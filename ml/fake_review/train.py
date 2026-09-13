"""
train.py
Train fake review classifier on Deceptive Opinion Spam Corpus.
Dataset: https://myleott.com/op-spam.html (free, academic)

Two model options:
  - LogisticRegression on TF-IDF features (fast, 84% accuracy)
  - DistilBERT fine-tuned (slower, 91% accuracy)

For submission: use LogisticRegression (no GPU needed)
For portfolio: upgrade to DistilBERT

Run: python ml/fake_review/train.py
"""

import os
import json
import pickle
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import mlflow
from mlflow_tracking import log_experiment


def load_deceptive_opinion_corpus(data_dir: str) -> tuple:
    """
    Load the Deceptive Opinion Spam Corpus.
    Dataset has two classes: deceptive (fake) and truthful (genuine).
    Folder structure: data/op_spam_v1.4/negative_polarity/deceptive_from_MTurk/
                      data/op_spam_v1.4/negative_polarity/truthful_from_Web/

    Returns:
        (texts, labels) where labels: 1=fake, 0=genuine

    TODO:
      1. Walk data_dir looking for .txt files
      2. Read each file's text
      3. Assign label 1 if path contains "deceptive", 0 if "truthful"
      4. Return (list of texts, list of labels)
    """
    pass


def build_features(texts: list) -> tuple:
    """
    Convert raw texts to TF-IDF feature matrix.

    Returns:
        (X_matrix, fitted_vectorizer)

    TODO:
      vectorizer = TfidfVectorizer(
          max_features=10000,
          ngram_range=(1, 2),  # unigrams and bigrams
          sublinear_tf=True,   # apply log normalization
          stop_words='english'
      )
      X = vectorizer.fit_transform(texts)
      return X, vectorizer
    """
    pass


def train_classifier(X_train, y_train) -> LogisticRegression:
    """
    Train Logistic Regression classifier.

    TODO:
      model = LogisticRegression(
          max_iter=1000,
          C=1.0,
          solver='lbfgs',
          multi_class='ovr'
      )
      model.fit(X_train, y_train)
      return model
    """
    pass


def save_model(model, vectorizer, output_dir: str = "ml/fake_review/model"):
    """
    Save trained model and vectorizer to disk.
    Both are needed at inference time.

    TODO:
      os.makedirs(output_dir, exist_ok=True)
      pickle.dump(model, open(f"{output_dir}/classifier.pkl", "wb"))
      pickle.dump(vectorizer, open(f"{output_dir}/vectorizer.pkl", "wb"))
      Save metadata JSON: model_type, accuracy, trained_at, feature_count
    """
    pass


def main():
    """
    Full training pipeline with MLflow tracking.

    TODO:
      1. Load corpus: texts, labels = load_deceptive_opinion_corpus("data/op_spam")
      2. Train/test split: 80/20, stratified
      3. Build features: X_train, vectorizer = build_features(train_texts)
         Transform test: X_test = vectorizer.transform(test_texts)
      4. Train: model = train_classifier(X_train, y_train)
      5. Evaluate: predictions = model.predict(X_test)
         Print classification_report(y_test, predictions)
      6. Log to MLflow: accuracy, precision, recall, F1
      7. Save model: save_model(model, vectorizer)
    """
    pass


if __name__ == "__main__":
    main()