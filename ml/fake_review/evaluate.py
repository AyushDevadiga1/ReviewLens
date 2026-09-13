"""
evaluate.py
Evaluation and metrics for the fake review classifier.
Produces a metrics report used for the model README and viva.

Run: python ml/fake_review/evaluate.py --model-dir ml/fake_review/model
"""

import json
import pickle
import os
import numpy as np
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)
from typing import Dict, List, Tuple


def evaluate_model(
    y_true: List[int],
    y_pred: List[int]
) -> Dict[str, float]:
    """
    Compute standard classification metrics for the fake detector.

    Args:
        y_true: ground truth labels (1 = fake, 0 = genuine)
        y_pred: predicted labels

    Returns:
        dict with accuracy, precision, recall, f1, and confusion matrix

    TODO:
      1. accuracy_score(y_true, y_pred)
      2. precision_score / recall_score / f1_score (binary)
      3. confusion_matrix for the report
      4. Return dict of all metrics
    """
    pass


def build_report(result: Dict[str, float]) -> str:
    """
    Format the evaluation result dict as a readable text report.

    TODO:
      Return formatted multi-line string for console / file output
    """
    pass


def main():
    """
    CLI entry point.
    TODO:
      1. Parse --model-dir argument
      2. Load hold-out dataset (from data/op_spam split earlier)
      3. Run evaluate_model()
      4. Print build_report() to console
      5. Optionally save report JSON to model dir
    """
    pass


if __name__ == "__main__":
    main()