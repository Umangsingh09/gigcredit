"""service

Orchestrates the credit-scoring pipeline: fetch worker + credit_features
-> map DB fields to ML fields -> validate completeness -> predict ->
explain -> assemble a clean, backend-friendly result.

This is the only module in backend.app.services.ml that API routes
should import from directly; repository/feature_mapping/predictor stay
internal implementation details.
"""

from dataclasses import dataclass
from typing import Any, Dict, List

from . import repository
from .feature_mapping import map_worker_to_ml_input, validate_ml_input
from .predictor import explain, predict


@dataclass(frozen=True)
class CreditPredictionResult:
    worker_id: str
    repayment_probability: float
    default_probability: float
    predicted_class: int
    risk_score: float
    risk_category: str
    top_risk_factors: List[Dict[str, Any]]
    top_positive_factors: List[Dict[str, Any]]
    explanation: str
    out_of_distribution: bool
    out_of_distribution_fields: List[Dict[str, Any]]


def score_worker(user_id: str) -> CreditPredictionResult:
    """Run the full credit-scoring pipeline for the worker owned by user_id.

    Raises:
        WorkerNotFoundError: no worker profile exists for this user.
        CreditFeaturesNotFoundError: worker has no credit_features
            snapshot yet.
        MissingFeatureDataError: the snapshot exists but is incomplete.
        PredictionError: the ML pipeline itself failed.
    """
    worker = repository.get_worker_for_user(user_id)
    credit_features = repository.get_credit_features(worker["id"])

    ml_input = map_worker_to_ml_input(worker, credit_features)
    validate_ml_input(ml_input)

    prediction = predict(ml_input)
    explanation = explain(ml_input)

    return CreditPredictionResult(
        worker_id=worker["id"],
        repayment_probability=prediction["repayment_probability"],
        default_probability=prediction["default_probability"],
        predicted_class=prediction["predicted_class"],
        risk_score=prediction["risk_score"],
        risk_category=prediction["risk_category"],
        top_risk_factors=explanation["top_risk_factors"],
        top_positive_factors=explanation["top_positive_factors"],
        explanation=explanation["explanation"],
        # predict() and explain() compute this identically (same input
        # row, same training-distribution bounds) — sourced from
        # predict()'s result as the primary prediction.
        out_of_distribution=prediction["out_of_distribution"],
        out_of_distribution_fields=prediction["out_of_distribution_fields"],
    )
