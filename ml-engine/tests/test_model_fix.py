"""Tests proving the two ML correctness fixes (worker_id removal,
out-of-distribution detection) actually took effect on the shipped
model artifacts, not just in source code.

Run from ml-engine/: `python -m pytest tests -v`
(ml-engine/pytest.ini sets pythonpath so `import src...` resolves).
"""

import json
from pathlib import Path

import joblib
import pandas as pd
import pytest

from src.explain import explain_worker
from src.features import build_feature_matrix
from src.predict import predict_worker

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
DATA_CSV = Path(__file__).resolve().parent.parent / "data" / "gig_workers.csv"


def _sample_row(index: int = 0) -> dict:
    df = pd.read_csv(DATA_CSV)
    row = df.iloc[index].to_dict()
    row.pop("loan_repaid", None)
    return row


class TestWorkerIdRemovedFromFeatureSchema:
    """A. worker_id is absent from feature_names.json."""

    def test_feature_names_json_excludes_worker_id(self):
        with open(MODELS_DIR / "feature_names.json", encoding="utf-8") as f:
            meta = json.load(f)

        assert "worker_id" not in meta["feature_names"]
        assert meta["excludes_worker_id"] is True

    def test_build_feature_matrix_excludes_worker_id(self):
        df = pd.read_csv(DATA_CSV)
        X = build_feature_matrix(df)

        assert "worker_id" not in X.columns


class TestWorkerIdDoesNotAffectPredictions:
    """B. Changing worker_id while keeping all real worker features
    identical produces the same prediction.
    """

    @pytest.mark.parametrize("row_index", [0, 1, 999])
    def test_prediction_identical_across_worker_id_values(self, row_index):
        sample = _sample_row(row_index)

        results = []
        for wid in [0, 1, 500, 1000.5, 2000, 999999]:
            s = dict(sample)
            s["worker_id"] = wid
            results.append(predict_worker(s))

        first = results[0]
        for r in results[1:]:
            assert r["repayment_probability"] == first["repayment_probability"]
            assert r["default_probability"] == first["default_probability"]
            assert r["predicted_class"] == first["predicted_class"]
            assert r["risk_score"] == first["risk_score"]
            assert r["risk_category"] == first["risk_category"]

    def test_missing_worker_id_also_matches(self):
        # _safe_build_input defaults worker_id when absent; confirm that
        # default path agrees with an explicit value too, now that
        # worker_id carries no weight either way.
        sample = _sample_row(0)
        without_id = dict(sample)
        without_id.pop("worker_id", None)

        with_id = dict(sample)
        with_id["worker_id"] = 42

        assert predict_worker(without_id)["repayment_probability"] == pytest.approx(
            predict_worker(with_id)["repayment_probability"]
        )


class TestPipelineExpects15Features:
    """C. The trained pipeline expects 15 features."""

    def test_feature_names_json_has_15_entries(self):
        with open(MODELS_DIR / "feature_names.json", encoding="utf-8") as f:
            meta = json.load(f)

        assert meta["n_features"] == 15
        assert len(meta["feature_names"]) == 15

    def test_fitted_scaler_expects_15_input_features(self):
        pipeline = joblib.load(MODELS_DIR / "logreg_pipeline.joblib")
        scaler = dict(pipeline.steps)["scaler"]

        assert scaler.n_features_in_ == 15

    def test_fitted_logreg_has_15_coefficients(self):
        pipeline = joblib.load(MODELS_DIR / "logreg_pipeline.joblib")
        logreg = dict(pipeline.steps)["logreg"]

        assert logreg.coef_.shape[1] == 15


class TestExplanationWorksWithNewModel:
    """D. Explanation works with the new 15-feature model."""

    def test_explain_worker_returns_well_formed_output(self):
        sample = _sample_row(0)
        result = explain_worker(sample)

        assert result["predicted_class"] in (0, 1)
        assert result["risk_category"] in ("LOW", "MEDIUM", "HIGH")
        assert len(result["top_risk_factors"]) > 0
        assert len(result["top_positive_factors"]) > 0
        assert isinstance(result["explanation"], str) and result["explanation"]

    def test_explanation_never_cites_worker_id_as_a_factor(self):
        sample = _sample_row(0)
        result = explain_worker(sample)

        all_features = {f["feature"] for f in result["top_risk_factors"]} | {
            f["feature"] for f in result["top_positive_factors"]
        }
        assert "worker_id" not in all_features


class TestPredictionWithNormalValues:
    """E. Prediction works with normal training-distribution values."""

    @pytest.mark.parametrize("row_index", [0, 500, 1999])
    def test_predict_worker_on_real_training_rows(self, row_index):
        sample = _sample_row(row_index)
        result = predict_worker(sample)

        assert 0.0 <= result["repayment_probability"] <= 1.0
        assert result["predicted_class"] in (0, 1)
        assert result["risk_category"] in ("LOW", "MEDIUM", "HIGH")
        assert result["out_of_distribution"] is False
        assert result["out_of_distribution_fields"] == []


class TestOutOfDistributionDetection:
    """F. Out-of-distribution income is detected/warned about rather
    than silently treated as trustworthy.
    """

    def test_in_range_income_is_not_flagged(self):
        sample = _sample_row(0)
        result = predict_worker(sample)

        assert result["out_of_distribution"] is False

    @pytest.mark.parametrize("income", [15000, 20000, 30000, 50000])
    def test_far_above_range_income_is_flagged(self, income):
        sample = _sample_row(0)
        sample["average_monthly_income"] = income
        for m in range(1, 7):
            sample[f"income_month_{m}"] = income

        result = predict_worker(sample)

        assert result["out_of_distribution"] is True
        flagged_fields = {f["field"] for f in result["out_of_distribution_fields"]}
        assert "average_monthly_income" in flagged_fields
        # Still returns a usable prediction -- flagged, not refused.
        assert 0.0 <= result["repayment_probability"] <= 1.0

    def test_prediction_is_not_silently_treated_as_trustworthy(self):
        # The classic failure mode this guards against: a saturated,
        # falsely-confident LOW-risk prediction on an out-of-range
        # income, with nothing to signal it shouldn't be trusted.
        sample = _sample_row(0)
        sample["average_monthly_income"] = 50000
        for m in range(1, 7):
            sample[f"income_month_{m}"] = 50000

        result = predict_worker(sample)

        assert result["risk_category"] == "LOW"  # saturated, looks confident...
        assert result["out_of_distribution"] is True  # ...but is explicitly flagged.

    def test_explain_worker_also_flags_out_of_distribution(self):
        sample = _sample_row(0)
        sample["existing_monthly_obligations"] = 100000

        result = explain_worker(sample)

        assert result["out_of_distribution"] is True

    def test_value_is_never_altered_by_the_ood_check(self):
        sample = _sample_row(0)
        sample["average_monthly_income"] = 50000

        result = predict_worker(sample)
        reported_value = next(
            f["value"]
            for f in result["out_of_distribution_fields"]
            if f["field"] == "average_monthly_income"
        )
        assert reported_value == 50000.0
