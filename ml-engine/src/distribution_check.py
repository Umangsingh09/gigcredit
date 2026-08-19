"""distribution_check

Tracks the value range each raw ML input field spanned in the training
data (ml-engine/data/gig_workers.csv), and flags predictions computed on
inputs that fall outside that range ("out-of-distribution").

This never clamps, rescales, or otherwise alters an input value — it
only adds an explicit, visible warning to the prediction/explanation
output so a result computed on data far outside anything the model was
ever trained on is never silently presented with the same confidence as
one computed well within its known operating range. See
ml-engine/models/MODEL_CARD.md for why this matters: the training
income scale is synthetic and has not been validated against real
GigCredit production income figures, and the fitted
StandardScaler+LogisticRegression pipeline saturates (loses all
discriminative power) for inputs far outside what it was fit on.

worker_id is deliberately excluded from these checks: it is not a real
predictive feature (see features.py) and is not meaningful to
range-check.
"""

import json
import os
from typing import Any, Dict, List

DISTRIBUTION_META = "feature_distribution.json"

CHECKED_FIELDS = [
    "average_monthly_income",
    "income_volatility",
    "working_days_per_month",
    "gig_duration_months",
    "completion_rate",
    "cancellation_rate",
    "platform_rating",
    "existing_monthly_obligations",
    "income_month_1",
    "income_month_2",
    "income_month_3",
    "income_month_4",
    "income_month_5",
    "income_month_6",
]


def compute_distribution(df) -> Dict[str, Dict[str, float]]:
    """Compute the [min, max] range each checked field spanned in the
    given training DataFrame.
    """
    bounds: Dict[str, Dict[str, float]] = {}
    for field in CHECKED_FIELDS:
        bounds[field] = {
            "min": float(df[field].min()),
            "max": float(df[field].max()),
        }
    return bounds


def save_distribution(bounds: Dict[str, Dict[str, float]], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, DISTRIBUTION_META)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(bounds, f, indent=2)
    return path


def load_distribution(models_dir: str) -> Dict[str, Dict[str, float]]:
    path = os.path.join(models_dir, DISTRIBUTION_META)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def check_out_of_distribution(
    input_data: Dict[str, Any], bounds: Dict[str, Dict[str, float]]
) -> List[Dict[str, Any]]:
    """Return one entry per checked field whose value falls outside the
    training range in `bounds`. An empty list means every checked field
    was within the range the model was actually trained on.
    """
    warnings: List[Dict[str, Any]] = []
    for field, rng in bounds.items():
        value = input_data.get(field)
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if value < rng["min"] or value > rng["max"]:
            warnings.append(
                {
                    "field": field,
                    "value": value,
                    "training_min": rng["min"],
                    "training_max": rng["max"],
                }
            )
    return warnings
