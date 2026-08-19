"""feature_mapping

Pure, side-effect-free translation from GigCredit database rows
(workers + credit_features) to the raw feature dict the ml-engine
pipeline expects (ml-engine/src/features.py: REQUIRED_COLUMNS).

No database access and no ML inference happens here, so this module can
be unit tested without a database connection or a loaded model.

Field mapping summary
----------------------
Same name, same units, direct passthrough from credit_features:
    average_monthly_income, income_volatility, income_month_1..6,
    working_days_per_month, existing_monthly_obligations

Renamed (DB name -> ML name), same units:
    workers.experience_months        -> gig_duration_months
    credit_features.average_rating   -> platform_rating

Renamed AND unit-converted (DB name -> ML name):
    credit_features.completion_rate  -> completion_rate   (0-100 -> 0-1)
    credit_features.cancellation_rate -> cancellation_rate (0-100 -> 0-1)

    The ML pipeline was trained on 0-1 fractions
    (ml-engine/src/data_generator.py generates completion_rate /
    cancellation_rate as values in [0, 1]). The live database stores
    these as 0-100 percentages — see the
    credit_features_completion_rate_check /
    credit_features_cancellation_rate_check CHECK constraints in
    002_ml_worker_features.sql, which bound cancellation_rate to
    [0, 100]. Both fields are converted here so the model always sees
    the scale it was trained on.

worker_id is intentionally NOT included in the dict this module builds.
ml-engine's trained pipeline (v2.0.0+) no longer uses worker_id as a
model input at all — it was removed from the feature matrix after an
investigation found the original model had accidentally fit on it as a
scaled input, letting an arbitrary row identifier materially shift
predictions and risk categories (see ml-engine/models/MODEL_CARD.md).
worker_id remains part of ml-engine's raw REQUIRED_COLUMNS contract
purely so callers can still identify rows if they want to, but
predict.py's own input builder already defaults it to 0 when absent —
and since it is excluded from the scaled feature matrix, that default
is now provably inert (see ml-engine/tests/test_model_fix.py:
TestWorkerIdDoesNotAffectPredictions). There is no longer any reason
for this module to synthesize a placeholder value for it.
"""

from typing import Any, Dict, List, Optional

from .predictor import ML_REQUIRED_COLUMNS
from .exceptions import MissingFeatureDataError

_PERCENT_TO_FRACTION_FIELDS = ("completion_rate", "cancellation_rate")


def map_worker_to_ml_input(
    worker: Dict[str, Any], credit_features: Dict[str, Any]
) -> Dict[str, Optional[Any]]:
    """Build the raw ML input dict from a workers row and a
    credit_features row. Missing DB values are passed through as None
    (never invented) — callers must run validate_ml_input before using
    the result for a real prediction.
    """
    ml_input: Dict[str, Optional[Any]] = {
        "gig_duration_months": worker.get("experience_months"),
        "average_monthly_income": credit_features.get("average_monthly_income"),
        "income_volatility": credit_features.get("income_volatility"),
        "income_month_1": credit_features.get("income_month_1"),
        "income_month_2": credit_features.get("income_month_2"),
        "income_month_3": credit_features.get("income_month_3"),
        "income_month_4": credit_features.get("income_month_4"),
        "income_month_5": credit_features.get("income_month_5"),
        "income_month_6": credit_features.get("income_month_6"),
        "working_days_per_month": credit_features.get("working_days_per_month"),
        "completion_rate": credit_features.get("completion_rate"),
        "cancellation_rate": credit_features.get("cancellation_rate"),
        "platform_rating": credit_features.get("average_rating"),
        "existing_monthly_obligations": credit_features.get("existing_monthly_obligations"),
    }

    for field in _PERCENT_TO_FRACTION_FIELDS:
        value = ml_input.get(field)
        if value is not None:
            ml_input[field] = float(value) / 100.0

    return ml_input


def find_missing_fields(ml_input: Dict[str, Optional[Any]]) -> List[str]:
    """Return required ML fields that are still None after mapping.

    worker_id is excluded: this module never supplies it (see module
    docstring), and ml-engine's own raw-input defaulting fills it in
    harmlessly — it is not part of the model's feature matrix, so an
    absent value here is never "missing worker data".
    """
    return [
        field
        for field in ML_REQUIRED_COLUMNS
        if field != "worker_id" and ml_input.get(field) is None
    ]


def validate_ml_input(ml_input: Dict[str, Optional[Any]]) -> None:
    """Raise MissingFeatureDataError if any required field is missing.

    This is the explicit gate that prevents the service layer from ever
    relying on ml-engine/src/predict.py's own internal defaults (which
    silently fill things like average_monthly_income=0.0 or
    platform_rating=3.5) for a real worker's prediction.
    """
    missing = find_missing_fields(ml_input)
    if missing:
        raise MissingFeatureDataError(missing)
