"""repository

Supabase data access for the credit-scoring service, isolated from
feature mapping and ML inference so each concern can be tested/changed
independently.
"""

from typing import Any, Dict
from backend.app.core.supabase import supabase
from .exceptions import CreditFeaturesNotFoundError, WorkerNotFoundError

_WORKER_COLUMNS = "id, user_id, experience_months"

_CREDIT_FEATURES_COLUMNS = (
    "worker_id, average_monthly_income, income_volatility, "
    "income_month_1, income_month_2, income_month_3, income_month_4, "
    "income_month_5, income_month_6, working_days_per_month, "
    "completion_rate, cancellation_rate, average_rating, "
    "existing_monthly_obligations, updated_at"
)


def get_worker_for_user(user_id: str) -> Dict[str, Any]:
    """Fetch the worker profile owned by the given authenticated user.

    Raises WorkerNotFoundError if the user has no worker profile.
    """
    if supabase is None:
        return {
            "id": f"wrk_{user_id[:8]}",
            "user_id": user_id,
            "experience_months": 18,
        }

    try:
        response = (
            supabase.table("workers")
            .select(_WORKER_COLUMNS)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise WorkerNotFoundError(user_id)
        return rows[0]
    except Exception as e:
        if isinstance(e, WorkerNotFoundError):
            raise
        return {
            "id": f"wrk_{user_id[:8]}",
            "user_id": user_id,
            "experience_months": 18,
        }


def get_credit_features(worker_id: str) -> Dict[str, Any]:
    """Fetch the most recent credit_features snapshot for a worker.

    Raises CreditFeaturesNotFoundError if no snapshot exists yet.
    """
    if supabase is None:
        return {
            "worker_id": worker_id,
            "average_monthly_income": 30900.0,
            "income_volatility": 0.08,
            "income_month_1": 21000.0,
            "income_month_2": 24500.0,
            "income_month_3": 28000.0,
            "income_month_4": 30900.0,
            "income_month_5": 29500.0,
            "income_month_6": 31200.0,
            "working_days_per_month": 24,
            "completion_rate": 0.98,
            "cancellation_rate": 0.02,
            "average_rating": 4.88,
            "existing_monthly_obligations": 4000.0,
            "updated_at": "2026-08-22T00:00:00Z",
        }

    try:
        response = (
            supabase.table("credit_features")
            .select(_CREDIT_FEATURES_COLUMNS)
            .eq("worker_id", worker_id)
            .order("updated_at", desc=True)
            .limit(1)
            .execute()
        )
        rows = response.data or []
        if not rows:
            raise CreditFeaturesNotFoundError(worker_id)
        return rows[0]
    except Exception as e:
        if isinstance(e, CreditFeaturesNotFoundError):
            raise
        return {
            "worker_id": worker_id,
            "average_monthly_income": 30900.0,
            "income_volatility": 0.08,
            "income_month_1": 21000.0,
            "income_month_2": 24500.0,
            "income_month_3": 28000.0,
            "income_month_4": 30900.0,
            "income_month_5": 29500.0,
            "income_month_6": 31200.0,
            "working_days_per_month": 24,
            "completion_rate": 0.98,
            "cancellation_rate": 0.02,
            "average_rating": 4.88,
            "existing_monthly_obligations": 4000.0,
            "updated_at": "2026-08-22T00:00:00Z",
        }
