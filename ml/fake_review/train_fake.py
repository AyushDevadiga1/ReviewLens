"""
train_fake.py
Train a BINARY fake/genuine classifier on the Ott Deceptive Opinion Spam
corpus (1,600 hotel reviews, balanced fake/genuine across sentiments).
Source: https://myleott.com/op_spam_v1.4.tar.gz (Ott et al., Deceptive
Opinion Spam). Extract under data/op_spam/ — the folder is gitignored;
re-download to reproduce.

Why a second model: the v1 detector is a *sentiment* classifier plus a
length heuristic — structurally blind to long fakes and trigger-happy on
short genuine 5-stars. v2 learns fake-vs-genuine directly from labels.

Outputs (ml/fake_review/model/v2/ — v1 artifacts untouched):
  classifier.pkl       - LogisticRegression, classes [0 genuine, 1 fake]
  tfidf_vectorizer.pkl - fitted TF-IDF (word 1-2 grams)
  metadata.json        - metrics + provenance

Run: python -m ml.fake_review.train_fake
"""

import os
import re
import json
import pickle

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from ml.mlflow_tracking import log_experiment

CORPUS_ROOT = os.path.join("data", "op_spam", "op_spam_v1.4")
OUTPUT_DIR = os.path.join("ml", "fake_review", "model", "v2")


def load_ott_spam(root: str = CORPUS_ROOT):
    """Walk the corpus into (texts, labels). 1 = fake (deceptive)."""
    texts, labels = [], []
    for polarity in ("negative_polarity", "positive_polarity"):
        for source, label in (("deceptive_from_MTurk", 1),
                              ("truthful_from_Web", 0),
                              ("truthful_from_TripAdvisor", 0)):
            folder = os.path.join(root, polarity, source)
            if not os.path.isdir(folder):
                continue
            for dirpath, _, filenames in os.walk(folder):
                for fname in sorted(filenames):
                    if not fname.endswith(".txt"):
                        continue
                    with open(os.path.join(dirpath, fname), "r",
                              encoding="utf-8", errors="replace") as fh:
                        text = re.sub(r"\s+", " ", fh.read()).strip()
                    if len(text) >= 20:
                        texts.append(text)
                        labels.append(label)
    return texts, labels


def evaluate(model, X_test, y_test) -> dict:
    pred = model.predict(X_test)
    return {
        "accuracy": round(float(accuracy_score(y_test, pred)), 4),
        "precision_fake": round(float(precision_score(y_test, pred, zero_division=0)), 4),
        "recall_fake": round(float(recall_score(y_test, pred, zero_division=0)), 4),
        "f1_fake": round(float(f1_score(y_test, pred, zero_division=0)), 4),
    }


def main():
    texts, labels = load_ott_spam()
    print(f"Loaded {len(texts)} reviews "
          f"({sum(labels)} fake, {len(labels) - sum(labels)} genuine)")

    X_train_t, X_test_t, y_train, y_test = train_test_split(
        texts, labels, test_size=0.2, random_state=42, stratify=labels)

    vectorizer = TfidfVectorizer(
        max_features=15000, ngram_range=(1, 2),
        sublinear_tf=True, min_df=2)
    X_train = vectorizer.fit_transform(X_train_t)
    X_test = vectorizer.transform(X_test_t)

    model = LogisticRegression(max_iter=1000, C=1.0)
    model.fit(X_train, y_train)
    print("classes_:", list(model.classes_))

    metrics = evaluate(model, X_test, y_test)
    print("metrics:", metrics)

    # Save FIRST so a dead MLflow server can never lose the model.
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "classifier.pkl"), "wb") as fh:
        pickle.dump(model, fh)
    with open(os.path.join(OUTPUT_DIR, "tfidf_vectorizer.pkl"), "wb") as fh:
        pickle.dump(vectorizer, fh)
    metadata = {
        "model_type": "TF-IDF + LogisticRegression (binary fake)",
        "dataset": "Ott Deceptive Opinion Spam v1.4 (1600 hotel reviews)",
        "labels": {"0": "genuine", "1": "fake"},
        "classes_order": [int(c) for c in model.classes_],
        "trained_at": __import__("datetime").datetime.utcnow().isoformat(),
        **metrics,
    }
    with open(os.path.join(OUTPUT_DIR, "metadata.json"), "w") as fh:
        json.dump(metadata, fh, indent=2)
    print(f"Saved v2 artifacts to {OUTPUT_DIR}/")

    try:
        run_id = log_experiment(
            "fake_review_classifier_v2",
            {"model": "LR-binary", "max_features": 15000,
             "ngrams": "1-2", "corpus": "ott-v1.4"},
            metrics,
        )
        print(f"Logged to MLflow run {run_id}")
    except Exception as exc:
        print(f"MLflow logging skipped (server unreachable?): {exc}")


if __name__ == "__main__":
    main()
