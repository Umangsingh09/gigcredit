"""exceptions

Typed errors for the credit-scoring service layer. Kept free of any
FastAPI/HTTP dependency so the service can be unit tested in isolation;
the API layer (backend/app/api/credit.py) is responsible for translating
these into HTTP responses.
"""

from typing import List


class MLServiceError(Exception):
    """Base class for all credit-scoring service errors."""


class WorkerNotFoundError(MLServiceError):
    """No worker profile exists for the requesting user."""

    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"No worker profile found for user: {user_id}")


class CreditFeaturesNotFoundError(MLServiceError):
    """The worker exists but has no credit_features snapshot yet."""

    def __init__(self, worker_id: str):
        self.worker_id = worker_id
        super().__init__(f"No credit_features snapshot exists for worker: {worker_id}")


class MissingFeatureDataError(MLServiceError):
    """The credit_features snapshot exists but is missing required inputs.

    Raised instead of letting the ML pipeline silently default missing
    financial/behavioral data.
    """

    def __init__(self, missing_fields: List[str]):
        self.missing_fields = sorted(missing_fields)
        super().__init__(
            "Cannot score worker: required feature data is missing: "
            + ", ".join(self.missing_fields)
        )


class PredictionError(MLServiceError):
    """The underlying ML pipeline failed to produce a prediction."""
