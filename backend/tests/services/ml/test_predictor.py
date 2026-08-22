"""Unit tests for backend.app.services.ml.predictor.

test_predict_runs_the_real_trained_pipeline is a genuine local inference
test against the actual trained model artifact
(ml-engine/models/logreg_pipeline.joblib) — not mocked — to confirm the
adapter's sys.path wiring and the live model produce a real prediction.
Failure-handling tests mock the underlying ml-engine call to avoid
depending on being able to force the real model to error.
"""

import pytest

from backend.app.services.ml import predictor
from backend.app.services.ml.exceptions import PredictionError


def _valid_ml_input():
    """A well-formed input within the training data's value range
    (average_monthly_income training range is ~150-9,242 — see
    ml-engine/models/feature_distribution.json). worker_id is included
    only because ml-engine's REQUIRED_COLUMNS raw-input contract still
    lists it; its value is inert since ml-engine v2.0.0 (not part of the
    scaled feature matrix) — see feature_mapping.py's module docstring.
    """
    return {
        "worker_id": 0,
        "average_monthly_income": 1800.0,
        "income_volatility": 0.3,
        "working_days_per_month": 22,
        "gig_duration_months": 18,
        "completion_rate": 0.9,
        "cancellation_rate": 0.05,
        "platform_rating": 4.5,
        "existing_monthly_obligations": 300.0,
        "income_month_1": 1750.0,
        "income_month_2": 1850.0,
        "income_month_3": 1780.0,
        "income_month_4": 1820.0,
        "income_month_5": 1790.0,
        "income_month_6": 1810.0,
    }


def _out_of_distribution_ml_input():
    """Same shape as _valid_ml_input, but with an income far above the
    training range's max (~9,242), to exercise the OOD warning path.
    """
    ml_input = _valid_ml_input()
    ml_input["average_monthly_income"] = 50000.0
    for m in range(1, 7):
        ml_input[f"income_month_{m}"] = 50000.0
    return ml_input


class TestSuccessfulPrediction:
    def test_ml_required_columns_are_exposed_and_complete(self):
        assert set(_valid_ml_input().keys()) == set(predictor.ML_REQUIRED_COLUMNS)

    def test_predict_runs_the_real_trained_pipeline(self):
        result = predictor.predict(_valid_ml_input())

        # Required keys must be present; the ml-engine is free to add
        # further keys additively (e.g. out_of_distribution metadata)
        # without that being a breaking change here.
        assert {
            "repayment_probability",
            "default_probability",
            "predicted_class",
            "risk_score",
            "risk_category",
        } <= set(result.keys())
        assert 0.0 <= result["repayment_probability"] <= 1.0
        assert 0.0 <= result["default_probability"] <= 1.0
        assert result["predicted_class"] in (0, 1)
        assert result["risk_category"] in ("LOW", "MEDIUM", "HIGH")
        assert result["repayment_probability"] == pytest.approx(
            1.0 - result["default_probability"], abs=1e-6
        )

    def test_normal_prediction_is_not_flagged_out_of_distribution(self):
        result = predictor.predict(_valid_ml_input())

        assert result["out_of_distribution"] is False
        assert result["out_of_distribution_fields"] == []

    def test_explain_runs_the_real_trained_pipeline(self):
        result = predictor.explain(_valid_ml_input())

        assert "top_risk_factors" in result
        assert "top_positive_factors" in result
        assert isinstance(result["explanation"], str) and result["explanation"]
        assert result["risk_category"] in ("LOW", "MEDIUM", "HIGH")


class TestOutOfDistributionWarning:
    def test_predict_flags_out_of_range_income(self):
        result = predictor.predict(_out_of_distribution_ml_input())

        assert result["out_of_distribution"] is True
        flagged = {f["field"] for f in result["out_of_distribution_fields"]}
        assert "average_monthly_income" in flagged
        # Still returns a usable prediction alongside the warning.
        assert 0.0 <= result["repayment_probability"] <= 1.0

    def test_explain_also_flags_out_of_range_income(self):
        result = predictor.explain(_out_of_distribution_ml_input())

        assert result["out_of_distribution"] is True
        flagged = {f["field"] for f in result["out_of_distribution_fields"]}
        assert "average_monthly_income" in flagged

    def test_out_of_distribution_field_reports_value_unaltered(self):
        result = predictor.predict(_out_of_distribution_ml_input())

        entry = next(
            f for f in result["out_of_distribution_fields"] if f["field"] == "average_monthly_income"
        )
        assert entry["value"] == 50000.0


class TestPredictionFailureHandling:
    def test_predict_wraps_underlying_errors_in_prediction_error(self, monkeypatch):
        def _boom(_input_data, models_dir=None, pipeline=None):
            raise RuntimeError("pipeline exploded")

        monkeypatch.setattr(predictor, "_predict_worker", _boom)

        with pytest.raises(PredictionError):
            predictor.predict(_valid_ml_input())

    def test_explain_wraps_underlying_errors_in_prediction_error(self, monkeypatch):
        def _boom(_input_data, models_dir=None, top_k=5, pipeline=None):
            raise RuntimeError("explainer exploded")

        monkeypatch.setattr(predictor, "_explain_worker", _boom)

        with pytest.raises(PredictionError):
            predictor.explain(_valid_ml_input())

    def test_prediction_error_preserves_original_failure_message(self, monkeypatch):
        def _boom(_input_data, models_dir=None, pipeline=None):
            raise ValueError("bad feature shape")

        monkeypatch.setattr(predictor, "_predict_worker", _boom)

        with pytest.raises(PredictionError, match="bad feature shape"):
            predictor.predict(_valid_ml_input())
