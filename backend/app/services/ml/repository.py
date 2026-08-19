"""repository

Supabase data access for the credit-scoring service, isolated from
feature mapping and ML inference so each concern can be tested/changed
independently (per-instructions: keep DB access, feature mapping, ML
inference, and API concerns separated).

Ownership is enforced explicitly here (filtering workers by user_id)
rather than assuming the configured Supabase key enforces RLS — the
shared `supabase` client in backend/app/core/supabase.py is used
project-wide for both anon and privileged operations, so this module
does not assume which key type is active and never trusts RLS alone
for this financial-data read path.
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


def get_credit_features(worker_id: str) -> Dict[str, Any]:
    """Fetch the most recent credit_features snapshot for a worker.

    credit_features has no uniqueness constraint on worker_id, so
    multiple snapshot rows are possible over time; the most recently
    updated one is used.

    Raises CreditFeaturesNotFoundError if no snapshot exists yet.
    """
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
