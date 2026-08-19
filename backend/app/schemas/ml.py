from typing import List

from pydantic import BaseModel, Field


class FeatureContribution(BaseModel):
    feature: str
    contribution: float


class OutOfDistributionField(BaseModel):
    """One raw input field whose value fell outside the range the model
    was trained on (see ml-engine/src/distribution_check.py and
    ml-engine/models/MODEL_CARD.md). Reports the value as given — never
    clamped or altered — alongside the training range it exceeded.
    """

    field: str
    value: float
    training_min: float
    training_max: float


class CreditPredictionResponse(BaseModel):
    worker_id: str
    repayment_probability: float = Field(..., ge=0.0, le=1.0)
    default_probability: float = Field(..., ge=0.0, le=1.0)
    predicted_class: int
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_category: str
    top_risk_factors: List[FeatureContribution]
    top_positive_factors: List[FeatureContribution]
    explanation: str
    out_of_distribution: bool
    out_of_distribution_fields: List[OutOfDistributionField]
