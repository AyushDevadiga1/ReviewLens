"""
train.py
Train fake review sentiment classifier on Dataset-SA.csv.

Dataset : data/Dataset-SA.csv (205,052 labelled reviews)
          Columns: product_name, product_price, Rate, Review, Summary, Sentiment
          Labels : positive / negative / neutral

Model   : TF-IDF (unigrams + bigrams) + Logistic Regression
          Fast to train (< 2 min on CPU), ~80-85% accuracy on this task.
          DistilBERT fine-tuning is a Phase 2 upgrade — same save interface.

Features:
  - Primary text: Summary column (longer, more informative than Review title)
  - Fallback text: Review column if Summary is empty
  - Rating as numeric feature concatenated with TF-IDF matrix

Saved artifacts (ml/fake_review/model/):
  - tfidf_vectorizer.pkl  — fitted TF-IDF vectorizer
  - classifier.pkl        — fitted LogisticRegression model
  - label_encoder.pkl     — fitted LabelEncoder (positive/negative/neutral → int)
  - metadata.json         — model_type, accuracy, trained_at, feature_count

Fake detection logic (used in api/services/fake_detector.py):
  A review is flagged suspicious when:
    - Predicted positive with confidence > 0.85 AND review_length < 20 chars
    - OR rating == 5.0 AND review_length < 10 chars (pure heuristic)
  Genuine = not flagged by either rule.

Run:
  python -m ml.fake_review.train
  python -m ml.fake_review.train --file data/Dataset-SA.csv --limit 50000
"""

import typing_extensions
import os
import csv
import json
import pickle

import mlflow
from ml.mlflow_tracking import log_experiment

import argparse
from datetime import datetime
import typing_extensions

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.preprocessing import LabelEncoder
from sklearn.pipeline import Pipeline
import scipy.sparse as sp


# ── Data loading ───────────────────────────────────────────────────────────────

def load_dataset_sa(filepath: str, limit: int = None) -> tuple:
    """
    Load Dataset-SA.csv into parallel lists of texts, ratings and labels.

    Args:
        filepath : path to Dataset-SA.csv
        limit    : max rows to load (None = all 205K)

    Returns:
        (texts, ratings, labels)
        texts   : list of str — cleaned Summary or Review text
        ratings : list of float — 1.0–5.0, None where unparseable
        labels  : list of str — "positive", "negative", "neutral"

    TODO:
      1. Open filepath with csv.DictReader (comma-separated, utf-8 errors='replace')

      2. For each row:
         a. text = row.get("Summary") or row.get("Review", "")
            Strip whitespace. Skip row if len(text) < 20.

         b. Parse rating:
            try: rating = float(row.get("Rate", 0) or 0)
                 rating = max(1.0, min(5.0, rating))
            except (ValueError, TypeError): rating = None

         c. label = row.get("Sentiment", "").strip().lower()
            Skip row if label not in {"positive", "negative", "neutral"}

         d. Append to texts, ratings, labels

      3. Apply limit if provided: texts = texts[:limit] etc.

      4. Print summary:
         f"Loaded {len(texts)} samples — "
         f"pos: {labels.count('positive')}, "
         f"neg: {labels.count('negative')}, "
         f"neu: {labels.count('neutral')}"

      5. Return (texts, ratings, labels)
    """
    VALID_CLASSES = {"positive", "negative", "neutral"}

    texts, ratings, labels = [], [], []

    with open(filepath,mode="r",encoding="utf-8",errors='replace') as f:
        reader = csv.DictReader(f)
        for row in reader:

            text = (row.get("Summary") or row.get("Review", "")).strip()
            if len(text) < 20:
                continue  # Discard the row immediately and move to the next loop line

            try:
                rating = float(row.get("Rate", 0) or 0)
                rating = max(1.0, min(5.0, rating))
            except (ValueError,TypeError):
                rating = None

            label = row.get("Sentiment", "").strip().lower()
            if label not in VALID_CLASSES:
                continue

            texts.append(text)
            ratings.append(rating)
            labels.append(label)

            if limit is not None and len(texts) >= limit:
                break

    # Native frequency count structure
    pos_count = labels.count("positive")
    neg_count = labels.count("negative")
    neu_count = labels.count("neutral")

    print(f"Loaded {len(texts)} samples — pos: {pos_count}, neg: {neg_count}, neu: {neu_count}")

    return (texts, ratings, labels)
        
# ── Feature engineering ────────────────────────────────────────────────────────

def build_tfidf_features(train_texts: list, test_texts: list) -> tuple:
    """
    Fit TF-IDF on train_texts, transform both splits.

    Args:
        train_texts : list of str (training split)
        test_texts  : list of str (test split)

    Returns:
        (X_train_tfidf, X_test_tfidf, fitted_vectorizer)

    TODO:
      vectorizer = TfidfVectorizer(
          max_features=15000,
          ngram_range=(1, 2),   — unigrams + bigrams: "battery life" as one feature
          sublinear_tf=True,    — log(1+tf) dampens effect of very frequent terms
          strip_accents='unicode',
          analyzer='word',
          min_df=3,             — ignore terms appearing in < 3 docs (reduces noise)
      )
      X_train = vectorizer.fit_transform(train_texts)
      X_test  = vectorizer.transform(test_texts)
      return X_train, X_test, vectorizer
    """
    
    vectorizer = TfidfVectorizer(
        max_features = 15000,
        ngram_range=(1,2),
        sublinear_tf=True,
        strip_accents="unicode",
        analyzer='word',
        min_df=3
    )
    vectorizer.fit(train_texts)

    X_train = vectorizer.transform(train_texts)
    X_test  = vectorizer.transform(test_texts)

    return X_train, X_test, vectorizer    


def append_rating_feature(X_tfidf, ratings: list):
    """
    Append normalised rating as one extra column to the TF-IDF matrix.
    Rating adds a strong signal — 1-star reviews are almost never positive.

    Args:
        X_tfidf : sparse matrix from TF-IDF
        ratings : list of float or None — same length as X_tfidf rows

    Returns:
        Combined sparse matrix with one extra column

    TODO:
      1. Replace None ratings with the mean of available ratings
      2. Normalise: (rating - 1) / 4.0  → maps [1, 5] to [0.0, 1.0]
      3. rating_col = sp.csr_matrix(np.array(normalised).reshape(-1, 1))
      4. return sp.hstack([X_tfidf, rating_col])
         Why sp.hstack: TF-IDF returns a sparse matrix — converting to dense
         first would use ~10GB RAM for 150K × 15000. Stay sparse throughout.
    """
    
    # 1. Replace None ratings with the mean of available ratings

    # First, calculate the mean of only the valid numbers
    valid_ratings = [r for r in ratings if r is not None]
    mean_rating = sum(valid_ratings) / len(valid_ratings) if valid_ratings else 3.0 # Fallback if empty
    
    # Replace None values with that mean
    cleaned_ratings = [r if r is not None else mean_rating for r in ratings]
    
    # 2. Normalise: (rating - 1) / 4.0  → maps [1, 5] to [0.0, 1.0]
    # We use a NumPy array here to perform the vector math cleanly
    normalised = (np.array(cleaned_ratings) - 1.0) / 4.0
    
    # 3. rating_col = sp.csr_matrix(np.array(normalised).reshape(-1, 1))
    rating_col = sp.csr_matrix(normalised.reshape(-1, 1))
    
    # 4. return sp.hstack([X_tfidf, rating_col])
    return sp.hstack([X_tfidf, rating_col])


# ── Training ───────────────────────────────────────────────────────────────────

def train_classifier(X_train, y_train) -> LogisticRegression:
    """
    Fit Logistic Regression with balanced class weights.

    Args:
        X_train : sparse feature matrix
        y_train : encoded integer labels

    Returns:
        Fitted LogisticRegression

    TODO:
      model = LogisticRegression(
          max_iter=1000,
          C=1.0,              — regularisation strength (1.0 is a safe default)
          solver='lbfgs',     — efficient for multiclass, works on sparse input
          class_weight='balanced',  — weights classes inversely to frequency
                                      pos:166K neg:28K neu:10K → neu gets 16x weight
          multi_class='multinomial',
          n_jobs=-1           — use all CPU cores
      )
      model.fit(X_train, y_train)
      return model
    """
    
    model = LogisticRegression(
          max_iter=1000,
          C=1.0,             
          solver='lbfgs', 
          class_weight='balanced',
          multi_class='multinomial',
          n_jobs=-1      
    )
    
    model.fit(X_train, y_train)
    
    return model

# ── Evaluation ─────────────────────────────────────────────────────────────────

def evaluate(model, X_test, y_test, label_encoder: LabelEncoder) -> dict:
    """
    Evaluate model and return metrics dict.

    Args:
        model         : fitted LogisticRegression
        X_test        : sparse feature matrix
        y_test        : encoded integer labels
        label_encoder : to decode integer predictions back to string labels

    Returns:
        metrics dict: accuracy, precision, recall, f1 (weighted)

    TODO:
      1. y_pred = model.predict(X_test)
      2. report = classification_report(y_test, y_pred,
                      target_names=label_encoder.classes_, output_dict=True)
      3. Print classification_report(y_test, y_pred,
                      target_names=label_encoder.classes_)
      4. Return {
             "accuracy":  accuracy_score(y_test, y_pred),
             "precision": report["weighted avg"]["precision"],
             "recall":    report["weighted avg"]["recall"],
             "f1":        report["weighted avg"]["f1-score"],
         }
    """
    y_pred = model.predict(X_test)

    report = classification_report(
        y_test,y_pred,
        target_names=label_encoder.classes_,
        output_dict=True
    )

    return {
             "accuracy":  accuracy_score(y_test, y_pred),
             "precision": report["weighted avg"]["precision"],
             "recall":    report["weighted avg"]["recall"],
             "f1":        report["weighted avg"]["f1-score"],
        }


# ── Persistence ────────────────────────────────────────────────────────────────

def save_model(
    model,
    vectorizer,
    label_encoder,
    metrics: dict,
    output_dir: str = "ml/fake_review/model"
) -> None:
    """
    Save all artifacts needed for inference to ml/fake_review/model/.

    Args:
        model         : fitted LogisticRegression
        vectorizer    : fitted TfidfVectorizer
        label_encoder : fitted LabelEncoder
        metrics       : dict from evaluate()
        output_dir    : save path

    TODO:
      1. os.makedirs(output_dir, exist_ok=True)

      2. pickle.dump(model,         open(f"{output_dir}/classifier.pkl",      "wb"))
         pickle.dump(vectorizer,    open(f"{output_dir}/tfidf_vectorizer.pkl", "wb"))
         pickle.dump(label_encoder, open(f"{output_dir}/label_encoder.pkl",    "wb"))

      3. Save metadata JSON:
         metadata = {
             "model_type":    "TF-IDF + LogisticRegression",
             "dataset":       "Dataset-SA.csv",
             "labels":        list(label_encoder.classes_),
             "accuracy":      round(metrics["accuracy"], 4),
             "f1_weighted":   round(metrics["f1"], 4),
             "feature_count": vectorizer.get_feature_names_out().shape[0] + 1,
             "trained_at":    datetime.utcnow().isoformat(),
         }
         json.dump(metadata, open(f"{output_dir}/metadata.json", "w"), indent=2)

      4. Print: f"Model saved to {output_dir}/"
         Print: f"  accuracy={metadata['accuracy']}, f1={metadata['f1_weighted']}"
    """
    
    os.makedirs(output_dir,exist_ok=True)

    pickle.dump(model,         open(f"{output_dir}/classifier.pkl",      "wb"))
    pickle.dump(vectorizer,    open(f"{output_dir}/tfidf_vectorizer.pkl", "wb"))
    pickle.dump(label_encoder, open(f"{output_dir}/label_encoder.pkl",    "wb"))

    metadata = {
             "model_type":    "TF-IDF + LogisticRegression",
             "dataset":       "Dataset-SA.csv",
             "labels":        list(label_encoder.classes_),
             "accuracy":      round(metrics["accuracy"], 4),
             "f1_weighted":   round(metrics["f1"], 4),
             "feature_count": vectorizer.get_feature_names_out().shape[0] + 1,
             "trained_at":    datetime.utcnow().isoformat(),
        }

    json.dump(metadata, open(f"{output_dir}/metadata.json", "w"), indent=2)

    print(f"Model saved to {output_dir}")
    print(f"accuracy={metadata['accuracy']}, f1={metadata['f1_weighted']}")
    


# ── Main ───────────────────────────────────────────────────────────────────────

def main(filepath: str = "data/Dataset-SA.csv", limit: int = None):
    """
    Full training pipeline.

    TODO:
      1. Load data:
         texts, ratings, labels = load_dataset_sa(filepath, limit)

      2. Encode labels:
         le = LabelEncoder()
         y = le.fit_transform(labels)   — negative=0, neutral=1, positive=2

      3. Train/test split (80/20, stratified so class ratios are preserved):
         texts_train, texts_test, ratings_train, ratings_test, y_train, y_test =
             train_test_split(texts, ratings, y,
                              test_size=0.2, random_state=42, stratify=y)

      4. Build TF-IDF features:
         X_train_tfidf, X_test_tfidf, vectorizer = build_tfidf_features(
             texts_train, texts_test)

      5. Append rating feature:
         X_train = append_rating_feature(X_train_tfidf, ratings_train)
         X_test  = append_rating_feature(X_test_tfidf,  ratings_test)

      6. Train:
         model = train_classifier(X_train, y_train)

      7. Evaluate:
         metrics = evaluate(model, X_test, y_test, le)

      8. Log to MLflow (import from ml.mlflow_tracking):
         log_experiment("fake_review_classifier", metrics,
                        params={"model": "LR", "max_features": 15000})

      9. Save:
         save_model(model, vectorizer, le, metrics)
    """
    texts, ratings, labels = load_dataset_sa(filepath, limit)

    le = LabelEncoder()
    le.fit(labels)

    y = le.transform(labels)

    texts_train, texts_test, ratings_train, ratings_test, y_train, y_test = train_test_split(
                            texts, ratings, y,
                            test_size=0.2, random_state=42, stratify=y
                        )
    
    X_train_tfidf, X_test_tfidf, vectorizer = build_tfidf_features(
            texts_train, texts_test 
            )

    X_train = append_rating_feature(X_train_tfidf, ratings_train)
    X_test  = append_rating_feature(X_test_tfidf,  ratings_test)

    model = train_classifier(X_train, y_train)

    metrics = evaluate(model, X_test, y_test, le)

    log_experiment(
                    "fake_review_classifier", 
                    {"model": "LR", "max_features": 15000},
                    metrics                                  
                )
    
    save_model(model, vectorizer, le, metrics)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file",  default="data/Dataset-SA.csv")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    main(args.file, args.limit)
