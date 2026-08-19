"""Unit tests for backend.app.services.ml.service (orchestration layer).

repository and predictor are mocked here so these tests exercise only
the orchestration logic (fetch -> map -> validate -> predict -> explain)
without touching Supabase or the real model — those are covered by
test_predictor.py (real model) and would need a live DB for repository.
"""

import pytest

from backend.app.services.ml import service
from backend.app.services.ml.exceptions import (
    CreditFeaturesNotFoundError,
    MissingFeatureDataError,
    PredictionError,
    WorkerNotFoundError,
)


def _worker_row():
    return {"id": "worker-uuid-123", "user_id": "user-uuid-456", "experience_months": 18}


def _credit_features_row():
    return {
        "worker_id": "worker-uuid-123",
        "average_monthly_income": 20000.0,
        "income_volatility": 0.3,
        "income_month_1": 19500.0,
        "income_month_2": 20500.0,
        "income_month_3": 19800.0,
        "income_month_4": 20200.0,
        "income_month_5": 19900.0,
        "income_month_6": 20100.0,
        "working_days_per_month": 22,
        "completion_rate": 90.0,
        "cancellation_rate": 5.0,
        "average_rating": 4.5,
        "existing_monthly_obligations": 3000.0,
    }


def _fake_prediction(out_of_distribution=False, out_of_distribution_fields=None):
    return {
        "repayment_probability": 0.82,
        "default_probability": 0.18,
        "predicted_class": 1,
        "risk_score": 0.18,
        "risk_category": "LOW",
        "out_of_distribution": out_of_distribution,
        "out_of_distribution_fields": out_of_distribution_fields or [],
    }


def _fake_explanation():
    return {
        "risk_score": 0.18,
        "risk_category": "LOW",
        "predicted_class": 1,
        "top_risk_factors": [{"feature": "income_volatility", "contribution": -0.1}],
        "top_positive_factors": [{"feature": "platform_rating", "contribution": 0.2}],
        "explanation": "mock explanation",
    }


class TestScoreWorkerSuccess:
    def test_returns_assembled_prediction_result(self, monkeypatch):
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )
        monkeypatch.setattr(service, "predict", lambda ml_input: _fake_prediction())
        monkeypatch.setattr(service, "explain", lambda ml_input: _fake_explanation())

        result = service.score_worker("user-uuid-456")

        assert result.worker_id == "worker-uuid-123"
        assert result.repayment_probability == 0.82
        assert result.risk_category == "LOW"
        assert result.top_positive_factors == [{"feature": "platform_rating", "contribution": 0.2}]
        assert result.out_of_distribution is False
        assert result.out_of_distribution_fields == []

    def test_predict_and_explain_receive_mapped_ml_fields_not_db_fields(self, monkeypatch):
        captured = {}

        def _capture_predict(ml_input):
            captured["predict_input"] = ml_input
            return _fake_prediction()

        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )
        monkeypatch.setattr(service, "predict", _capture_predict)
        monkeypatch.setattr(service, "explain", lambda ml_input: _fake_explanation())

        service.score_worker("user-uuid-456")

        ml_input = captured["predict_input"]
        assert ml_input["gig_duration_months"] == 18  # from experience_months
        assert ml_input["platform_rating"] == 4.5  # from average_rating
        assert ml_input["cancellation_rate"] == pytest.approx(0.05)  # 5.0 / 100
        assert "experience_months" not in ml_input
        assert "average_rating" not in ml_input


class TestOutOfDistributionPropagation:
    def test_normal_prediction_reports_not_out_of_distribution(self, monkeypatch):
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )
        monkeypatch.setattr(service, "predict", lambda ml_input: _fake_prediction())
        monkeypatch.setattr(service, "explain", lambda ml_input: _fake_explanation())

        result = service.score_worker("user-uuid-456")

        assert result.out_of_distribution is False
        assert result.out_of_distribution_fields == []

    def test_out_of_distribution_prediction_is_passed_through(self, monkeypatch):
        ood_fields = [
            {
                "field": "average_monthly_income",
                "value": 50000.0,
                "training_min": 150.0,
                "training_max": 9242.27,
            }
        ]
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )
        monkeypatch.setattr(
            service,
            "predict",
            lambda ml_input: _fake_prediction(
                out_of_distribution=True, out_of_distribution_fields=ood_fields
            ),
        )
        monkeypatch.setattr(service, "explain", lambda ml_input: _fake_explanation())

        result = service.score_worker("user-uuid-456")

        assert result.out_of_distribution is True
        assert result.out_of_distribution_fields == ood_fields


class TestScoreWorkerNotFound:
    def test_propagates_worker_not_found(self, monkeypatch):
        def _raise_not_found(user_id):
            raise WorkerNotFoundError(user_id)

        monkeypatch.setattr(service.repository, "get_worker_for_user", _raise_not_found)

        with pytest.raises(WorkerNotFoundError):
            service.score_worker("user-with-no-worker")


class TestScoreWorkerCreditFeaturesNotFound:
    def test_propagates_credit_features_not_found(self, monkeypatch):
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())

        def _raise_not_found(worker_id):
            raise CreditFeaturesNotFoundError(worker_id)

        monkeypatch.setattr(service.repository, "get_credit_features", _raise_not_found)

        with pytest.raises(CreditFeaturesNotFoundError):
            service.score_worker("user-uuid-456")


class TestMissingRequiredFeatureHandling:
    def test_raises_before_calling_the_model_when_data_incomplete(self, monkeypatch):
        incomplete_cf = _credit_features_row()
        incomplete_cf["average_monthly_income"] = None

        predict_called = []
        explain_called = []

        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(service.repository, "get_credit_features", lambda worker_id: incomplete_cf)
        monkeypatch.setattr(service, "predict", lambda ml_input: predict_called.append(1))
        monkeypatch.setattr(service, "explain", lambda ml_input: explain_called.append(1))

        with pytest.raises(MissingFeatureDataError) as exc_info:
            service.score_worker("user-uuid-456")

        assert "average_monthly_income" in exc_info.value.missing_fields
        # The model must never be called with incomplete data.
        assert predict_called == []
        assert explain_called == []


class TestPredictionFailureHandling:
    def test_propagates_prediction_error_from_predict_step(self, monkeypatch):
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )

        def _raise_prediction_error(ml_input):
            raise PredictionError("ML prediction failed: model unavailable")

        monkeypatch.setattr(service, "predict", _raise_prediction_error)

        with pytest.raises(PredictionError):
            service.score_worker("user-uuid-456")

    def test_propagates_prediction_error_from_explain_step(self, monkeypatch):
        monkeypatch.setattr(service.repository, "get_worker_for_user", lambda user_id: _worker_row())
        monkeypatch.setattr(
            service.repository, "get_credit_features", lambda worker_id: _credit_features_row()
        )
        monkeypatch.setattr(service, "predict", lambda ml_input: _fake_prediction())

        def _raise_prediction_error(ml_input):
            raise PredictionError("ML explanation failed: model unavailable")

        monkeypatch.setattr(service, "explain", _raise_prediction_error)

        with pytest.raises(PredictionError):
            service.score_worker("user-uuid-456")
