"""End-to-end HTTP tests for POST /credit/predict.

Exercises the real FastAPI app, routing, and Pydantic response
validation via TestClient. The Supabase-backed auth dependency and the
ML service layer are substituted (via FastAPI dependency override and
monkeypatch respectively) since these tests run without a live Supabase
session or database — repository/predictor behavior itself is covered
by test_service.py and test_predictor.py.
"""

from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user_id
from backend.app.main import app
from backend.app.services.ml import service as ml_service
from backend.app.services.ml.exceptions import (
    CreditFeaturesNotFoundError,
    MissingFeatureDataError,
    WorkerNotFoundError,
)
from backend.app.services.ml.service import CreditPredictionResult

client = TestClient(app)


def _fake_result(out_of_distribution=False, out_of_distribution_fields=None):
    return CreditPredictionResult(
        worker_id="11111111-1111-1111-1111-111111111111",
        repayment_probability=0.82,
        default_probability=0.18,
        predicted_class=1,
        risk_score=0.18,
        risk_category="LOW",
        top_risk_factors=[{"feature": "income_volatility", "contribution": -0.12}],
        top_positive_factors=[{"feature": "platform_rating", "contribution": 0.21}],
        explanation="Predicted repayment probability: 0.820 (class=1)",
        out_of_distribution=out_of_distribution,
        out_of_distribution_fields=out_of_distribution_fields or [],
    )


def _override_auth():
    app.dependency_overrides[get_current_user_id] = lambda: "user-uuid-456"


def _clear_overrides():
    app.dependency_overrides.clear()


class TestCreditPredictEndpoint:
    def test_authenticated_request_returns_prediction(self, monkeypatch):
        _override_auth()
        monkeypatch.setattr(ml_service, "score_worker", lambda user_id: _fake_result())
        try:
            response = client.post("/credit/predict")
        finally:
            _clear_overrides()

        assert response.status_code == 200
        body = response.json()
        assert body["worker_id"] == "11111111-1111-1111-1111-111111111111"
        assert body["repayment_probability"] == 0.82
        assert body["risk_category"] == "LOW"
        assert body["top_positive_factors"] == [
            {"feature": "platform_rating", "contribution": 0.21}
        ]
        # Normal in-distribution prediction: OOD fields present and empty.
        assert body["out_of_distribution"] is False
        assert body["out_of_distribution_fields"] == []

    def test_out_of_distribution_prediction_surfaces_warning_fields(self, monkeypatch):
        ood_fields = [
            {
                "field": "average_monthly_income",
                "value": 50000.0,
                "training_min": 150.0,
                "training_max": 9242.27,
            }
        ]
        _override_auth()
        monkeypatch.setattr(
            ml_service,
            "score_worker",
            lambda user_id: _fake_result(
                out_of_distribution=True, out_of_distribution_fields=ood_fields
            ),
        )
        try:
            response = client.post("/credit/predict")
        finally:
            _clear_overrides()

        assert response.status_code == 200
        body = response.json()
        assert body["out_of_distribution"] is True
        assert body["out_of_distribution_fields"] == ood_fields
        # Existing fields are unaffected by the OOD flag being set.
        assert body["repayment_probability"] == 0.82
        assert body["risk_category"] == "LOW"

    def test_missing_authorization_header_is_rejected(self):
        response = client.post("/credit/predict")
        assert response.status_code == 401

    def test_worker_not_found_returns_404_without_internal_details(self, monkeypatch):
        _override_auth()

        def _raise(user_id):
            raise WorkerNotFoundError(user_id)

        monkeypatch.setattr(ml_service, "score_worker", _raise)
        try:
            response = client.post("/credit/predict")
        finally:
            _clear_overrides()

        assert response.status_code == 404
        assert "user-uuid-456" not in response.text

    def test_missing_credit_features_returns_409(self, monkeypatch):
        _override_auth()

        def _raise(user_id):
            raise CreditFeaturesNotFoundError("worker-uuid-123")

        monkeypatch.setattr(ml_service, "score_worker", _raise)
        try:
            response = client.post("/credit/predict")
        finally:
            _clear_overrides()

        assert response.status_code == 409

    def test_incomplete_feature_data_returns_422_with_missing_field_names(self, monkeypatch):
        _override_auth()

        def _raise(user_id):
            raise MissingFeatureDataError(["average_monthly_income", "platform_rating"])

        monkeypatch.setattr(ml_service, "score_worker", _raise)
        try:
            response = client.post("/credit/predict")
        finally:
            _clear_overrides()

        assert response.status_code == 422
        assert set(response.json()["detail"]["missing_fields"]) == {
            "average_monthly_income",
            "platform_rating",
        }
