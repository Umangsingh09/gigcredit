"""predictor

Thin wrapper around the existing, untouched ml-engine trained pipeline
(ml-engine/src/predict.py, ml-engine/src/explain.py).

ml-engine/ is a sibling directory of backend/, not an installable
package, and its directory name contains a hyphen so it cannot be
imported as a normal dotted Python package (`import ml-engine` is not
valid syntax). Rather than modify anything under ml-engine/ to make it
"pip installable", this module adds the ml-engine/ directory itself to
sys.path so its existing `src` package (ml-engine/src/__init__.py) can be
imported directly — the same mechanism ml-engine's own `python -m
src.train` entry point relies on.

Everything else in the service layer only depends on the plain
dict-in/dict-out functions exposed here, never on ml-engine's internals
directly.
"""

import sys
from pathlib import Path
from typing import Any, Dict

# backend/app/services/ml/predictor.py -> parents[4] is the repo root
# (mirrors the fixed-depth BASE_DIR pattern already used in
# backend/app/core/config.py).
_REPO_ROOT = Path(__file__).resolve().parents[4]
_ML_ENGINE_DIR = _REPO_ROOT / "ml-engine"

if not _ML_ENGINE_DIR.is_dir():
    raise ImportError(f"ml-engine directory not found at expected path: {_ML_ENGINE_DIR}")

if str(_ML_ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(_ML_ENGINE_DIR))

from src.features import REQUIRED_COLUMNS as ML_REQUIRED_COLUMNS  # type: ignore  # noqa: E402
from src.predict import predict_worker as _predict_worker  # type: ignore  # noqa: E402
from src.explain import explain_worker as _explain_worker  # type: ignore  # noqa: E402

from .exceptions import PredictionError


def predict(ml_input: Dict[str, Any]) -> Dict[str, Any]:
    """Run the trained pipeline's prediction step.

    ml_input must already be complete and validated (see
    feature_mapping.validate_ml_input) — this function does not fill in
    any missing values itself.
    """
    try:
        return _predict_worker(ml_input)
    except Exception as exc:
        raise PredictionError(f"ML prediction failed: {exc}") from exc


def explain(ml_input: Dict[str, Any]) -> Dict[str, Any]:
    """Run the trained pipeline's explanation step."""
    try:
        return _explain_worker(ml_input)
    except Exception as exc:
        raise PredictionError(f"ML explanation failed: {exc}") from exc
