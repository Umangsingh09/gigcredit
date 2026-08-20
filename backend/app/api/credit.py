"""credit

Credit-scoring API routes. Thin FastAPI layer only — data access,
feature mapping, and ML inference all live in backend.app.services.ml.
No internal details (DB structure, ML pipeline internals, stack traces)
are exposed in responses.
"""

from fastapi import APIRouter, Depends, HTTPException

from backend.app.api.deps import get_current_user_id
from backend.app.schemas.ml import (
    CreditPredictionResponse,
    FeatureContribution,
    OutOfDistributionField,
)
from backend.app.services.ml import service as ml_service
from backend.app.services.ml.exceptions import (
    CreditFeaturesNotFoundError,
    MissingFeatureDataError,
    PredictionError,
    WorkerNotFoundError,
)

router = APIRouter(
    prefix="/credit",
    tags=["Credit Scoring"],
)


@router.post("/predict", response_model=CreditPredictionResponse)
def predict_credit_score(user_id: str = Depends(get_current_user_id)):
    """Score the calling worker's own creditworthiness.

    The worker is derived from the authenticated caller's token, never
    from a client-supplied id — a worker can only ever request their own
    score through this endpoint.
    """
    try:
        result = ml_service.score_worker(user_id)
    except WorkerNotFoundError:
        raise HTTPException(status_code=404, detail="No worker profile found for this account")
    except CreditFeaturesNotFoundError:
        raise HTTPException(
            status_code=409,
            detail="Credit feature data has not been generated for this worker yet",
        )
    except MissingFeatureDataError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Worker's feature data is incomplete for scoring",
                "missing_fields": exc.missing_fields,
            },
        )
    except PredictionError:
        raise HTTPException(status_code=503, detail="Credit scoring is temporarily unavailable")

    return CreditPredictionResponse(
        worker_id=result.worker_id,
        repayment_probability=result.repayment_probability,
        default_probability=result.default_probability,
        predicted_class=result.predicted_class,
        risk_score=result.risk_score,
        risk_category=result.risk_category,
        top_risk_factors=[FeatureContribution(**f) for f in result.top_risk_factors],
        top_positive_factors=[FeatureContribution(**f) for f in result.top_positive_factors],
        explanation=result.explanation,
        out_of_distribution=result.out_of_distribution,
        out_of_distribution_fields=[
            OutOfDistributionField(**f) for f in result.out_of_distribution_fields
        ],
    )
