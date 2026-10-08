"""
mlflow_tracking.py
Experiment logging helpers for ReviewLens model training.
Wraps MLflow client calls so training scripts stay clean.

Import from scripts that live next to this file:
  from mlflow_tracking import log_experiment
"""

import mlflow
from typing import Dict, Optional


def log_experiment(
    experiment_name: str,
    params: Dict[str, any],
    metrics: Dict[str, float],
    model=None,
    tags: Optional[Dict[str, str]] = None
) -> str:
    """
    Log one training run to MLflow under the given experiment.

    Args:
        experiment_name: MLflow experiment to run under
        params: hyperparameters to record
        metrics: evaluation metrics (accuracy, precision, recall, F1, ...)
        model: optional sklearn model to log as an artifact
        tags: optional metadata tags (e.g. model_type, dataset)

    Returns:
        run_id of the logged run

    TODO:
      1. mlflow.set_experiment(experiment_name)
      2. with mlflow.start_run():
         - log params, metrics, tags
         - if model is not None: mlflow.sklearn.log_model(model, "model")
      3. Return run.info.run_id
    """
    
    # 1. Set the active experiment name
    mlflow.set_experiment(experiment_name)
    
    # 2. Start a tracking run
    with mlflow.start_run() as run:
        # Log hyperparameters (dictionary)
        if params:
            mlflow.log_params(params)
            
        # Log evaluation metrics (dictionary)
        if metrics:
            mlflow.log_metrics(metrics)
            
        # Log metadata tags if provided
        if tags:
            mlflow.set_tags(tags)
            
        # If a model object is provided, save it as an MLflow artifact
        if model is not None:
            mlflow.sklearn.log_model(model, "model")
            
        # 3. Return the unique run identity string
        return run.info.run_id