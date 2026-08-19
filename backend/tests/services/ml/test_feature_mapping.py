"""Unit tests for backend.app.services.ml.feature_mapping.

Pure mapping logic — no database, no ML model, no HTTP. These tests are
the source of truth for the DB-field -> ML-field contract described in
the module docstring.
"""

import pytest

from backend.app.services.ml.exceptions import MissingFeatureDataError
from backend.app.services.ml.feature_mapping import (
    find_missing_fields,
    map_worker_to_ml_input,
    validate_ml_input,
)


def _complete_worker():
    return {"id": "11111111-1111-1111-1111-111111111111", "experience_months": 18}


def _complete_credit_features():
    return {
        "average_monthly_income": 20000.0,
        "income_volatility": 0.35,
        "income_month_1": 19000.0,
        "income_month_2": 21000.0,
        "income_month_3": 18500.0,
        "income_month_4": 20500.0,
        "income_month_5": 19800.0,
        "income_month_6": 20200.0,
        "working_days_per_month": 22,
        "completion_rate": 95.0,        # stored as a 0-100 percentage
        "cancellation_rate": 4.0,       # stored as a 0-100 percentage
        "average_rating": 4.6,
        "existing_monthly_obligations": 3000.0,
    }


class TestSuccessfulFeatureMapping:
    def test_maps_all_required_fields(self):
        ml_input = map_worker_to_ml_input(_complete_worker(), _complete_credit_features())

        assert set(ml_input.keys()) == {
            "gig_duration_months",
            "average_monthly_income",
            "income_volatility",
            "income_month_1",
            "income_month_2",
            "income_month_3",
            "income_month_4",
            "income_month_5",
            "income_month_6",
            "working_days_per_month",
            "completion_rate",
            "cancellation_rate",
            "platform_rating",
            "existing_monthly_obligations",
        }
        # Direct passthrough fields keep their DB values untouched.
        assert ml_input["average_monthly_income"] == 20000.0
        assert ml_input["income_volatility"] == 0.35
        assert ml_input["income_month_3"] == 18500.0
        assert ml_input["working_days_per_month"] == 22
        assert ml_input["existing_monthly_obligations"] == 3000.0

    def test_mapped_input_passes_validation(self):
        ml_input = map_worker_to_ml_input(_complete_worker(), _complete_credit_features())
        validate_ml_input(ml_input)  # must not raise
        assert find_missing_fields(ml_input) == []


class TestExperienceMonthsMapping:
    def test_experience_months_becomes_gig_duration_months(self):
        worker = _complete_worker()
        worker["experience_months"] = 27

        ml_input = map_worker_to_ml_input(worker, _complete_credit_features())

        assert ml_input["gig_duration_months"] == 27
        assert "experience_months" not in ml_input

    def test_missing_experience_months_is_reported_as_missing(self):
        worker = _complete_worker()
        worker["experience_months"] = None

        ml_input = map_worker_to_ml_input(worker, _complete_credit_features())

        assert "gig_duration_months" in find_missing_fields(ml_input)


class TestAverageRatingMapping:
    def test_average_rating_becomes_platform_rating(self):
        cf = _complete_credit_features()
        cf["average_rating"] = 4.2

        ml_input = map_worker_to_ml_input(_complete_worker(), cf)

        assert ml_input["platform_rating"] == 4.2
        assert "average_rating" not in ml_input

    def test_missing_average_rating_is_reported_as_missing(self):
        cf = _complete_credit_features()
        cf["average_rating"] = None

        ml_input = map_worker_to_ml_input(_complete_worker(), cf)

        assert "platform_rating" in find_missing_fields(ml_input)


class TestRatePercentToFractionConversion:
    def test_completion_and_cancellation_rate_are_divided_by_100(self):
        cf = _complete_credit_features()
        cf["completion_rate"] = 95.0
        cf["cancellation_rate"] = 4.0

        ml_input = map_worker_to_ml_input(_complete_worker(), cf)

        assert ml_input["completion_rate"] == pytest.approx(0.95)
        assert ml_input["cancellation_rate"] == pytest.approx(0.04)


class TestWorkerIdOmitted:
    def test_worker_id_is_not_included_in_the_ml_input(self):
        # ml-engine v2.0.0+ no longer uses worker_id as a model feature
        # (see ml-engine/models/MODEL_CARD.md), so this module has no
        # reason to synthesize a value for it, and never does.
        worker = _complete_worker()
        ml_input = map_worker_to_ml_input(worker, _complete_credit_features())

        assert "worker_id" not in ml_input


class TestMissingRequiredFeatureHandling:
    def test_find_missing_fields_lists_every_none_field(self):
        cf = _complete_credit_features()
        cf["average_monthly_income"] = None
        cf["income_month_2"] = None

        ml_input = map_worker_to_ml_input(_complete_worker(), cf)
        missing = find_missing_fields(ml_input)

        assert "average_monthly_income" in missing
        assert "income_month_2" in missing
        assert len(missing) == 2

    def test_validate_ml_input_raises_missing_feature_data_error(self):
        cf = _complete_credit_features()
        cf["existing_monthly_obligations"] = None

        ml_input = map_worker_to_ml_input(_complete_worker(), cf)

        with pytest.raises(MissingFeatureDataError) as exc_info:
            validate_ml_input(ml_input)

        assert "existing_monthly_obligations" in exc_info.value.missing_fields

    def test_worker_id_is_never_reported_as_missing(self):
        # worker_id is never included in the mapped output at all (see
        # TestWorkerIdOmitted), so it must never appear in the
        # missing-fields list even though ml-engine's raw contract lists
        # it as a required column.
        ml_input = map_worker_to_ml_input(_complete_worker(), _complete_credit_features())
        assert "worker_id" not in find_missing_fields(ml_input)

    def test_missing_credit_features_snapshot_reports_all_its_fields_missing(self):
        # Simulates a worker who has a profile but an empty/partial
        # credit_features row.
        ml_input = map_worker_to_ml_input(_complete_worker(), {})
        missing = find_missing_fields(ml_input)

        assert "average_monthly_income" in missing
        assert "platform_rating" in missing
        assert "income_month_6" in missing
