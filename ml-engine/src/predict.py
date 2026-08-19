"""predict

Load a trained pipeline and produce prediction outputs for a single gig
worker. This script uses the same feature-engineering in `features.py`
so predictions match training preprocessing.

Outputs (JSON-serializable):
  - repayment_probability
  - default_probability
  - predicted_class (0/1)
  - risk_score (0..1, higher means more risky)
  - risk_category: LOW / MEDIUM / HIGH

Includes a small demo when run as `python -m src.predict` which uses the
first row of `ml-engine/data/gig_workers.csv` as input.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

try:
	import joblib
	_use_joblib = True
except Exception:
	import pickle
	_use_joblib = False

from .distribution_check import check_out_of_distribution, load_distribution
from .features import build_feature_matrix, REQUIRED_COLUMNS


MODEL_NAME = "logreg_pipeline.joblib"
FEATURE_META = "feature_names.json"


def _load_pipeline(models_dir: str):
	model_path = os.path.join(models_dir, MODEL_NAME)
	if not os.path.exists(model_path):
		# try pickle fallback name as saved by train when joblib missing
		model_path = model_path
	if _use_joblib:
		return joblib.load(model_path)
	else:
		with open(model_path, "rb") as f:
			return pickle.load(f)


def _safe_build_input(data: Dict[str, Any]) -> pd.DataFrame:
	"""Create a single-row DataFrame with required columns, filling
	sensible defaults for missing values so the pipeline can run.
	"""
	# Start with provided keys
	row = {k: data.get(k, None) for k in REQUIRED_COLUMNS}

	# Sensible defaults for missing values
	defaults = {
		"worker_id": 0,
		"average_monthly_income": 0.0,
		"income_volatility": 0.5,
		"working_days_per_month": 15,
		"gig_duration_months": 6,
		"completion_rate": 0.5,
		"cancellation_rate": 0.1,
		"platform_rating": 3.5,
		"existing_monthly_obligations": 0.0,
		"income_month_1": 0.0,
		"income_month_2": 0.0,
		"income_month_3": 0.0,
		"income_month_4": 0.0,
		"income_month_5": 0.0,
		"income_month_6": 0.0,
	}

	for k, dv in defaults.items():
		if row.get(k) is None or (isinstance(row.get(k), float) and np.isnan(row.get(k))):
			row[k] = dv

	df = pd.DataFrame([row])
	# Ensure correct dtypes where possible
	numeric_cols = [c for c in REQUIRED_COLUMNS if c != "worker_id"]
	df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
	return df


def predict_worker(
	input_data: Dict[str, Any], models_dir: str = None, pipeline: Any = None
) -> Dict[str, Any]:
	"""Predict repayment for a single worker input (dict of features).

	Returns a JSON-serializable dict with probabilities, class, risk
	score and category.
	"""
	base_dir = Path(__file__).resolve().parent
	if models_dir is None:
		models_dir = (base_dir / ".." / "models").resolve()
	else:
		models_dir = Path(models_dir).resolve()

	if pipeline is None:
		pipeline = _load_pipeline(str(models_dir))

	# Build a clean input DataFrame using shared feature logic
	raw_df = _safe_build_input(input_data)
	X = build_feature_matrix(raw_df)

	# Flag inputs outside the training data's value range. This never
	# alters the input or the prediction — it only surfaces, explicitly,
	# that the model has no real basis for judging a value it never saw
	# anything close to during training (see distribution_check.py and
	# ml-engine/models/MODEL_CARD.md).
	distribution_bounds = load_distribution(str(models_dir))
	ood_fields = check_out_of_distribution(raw_df.iloc[0].to_dict(), distribution_bounds)

	# Align columns to what the model expects (pipeline was saved with a set)
	# If model metadata exists, we could reorder; otherwise assume matching
	try:
		proba = pipeline.predict_proba(X)[:, 1][0]
		pred = int(pipeline.predict(X)[0])
	except Exception:
		# In case model can't predict, return safe defaults
		proba = 0.5
		pred = 1 if proba >= 0.5 else 0

	repayment_probability = float(np.clip(proba, 0.0, 1.0))
	default_probability = float(1.0 - repayment_probability)

	# Risk score: map default probability to 0..1 where higher=more risky
	risk_score = default_probability

	# Risk category thresholds (explainable and simple)
	if risk_score < 0.25:
		risk_category = "LOW"
	elif risk_score < 0.5:
		risk_category = "MEDIUM"
	else:
		risk_category = "HIGH"

	result = {
		"repayment_probability": round(repayment_probability, 4),
		"default_probability": round(default_probability, 4),
		"predicted_class": int(pred),
		"risk_score": round(float(risk_score), 4),
		"risk_category": risk_category,
		"out_of_distribution": bool(ood_fields),
		"out_of_distribution_fields": ood_fields,
	}

	return result


if __name__ == "__main__":
	# Demo: use the first worker from the generated CSV as a test input
	base_dir = Path(__file__).resolve().parent
	csv_path = (base_dir / ".." / "data" / "gig_workers.csv").resolve()
	print("Loading sample input from:", csv_path)
	df = pd.read_csv(csv_path)

	# Use first row, drop target if present
	sample = df.iloc[0].to_dict()
	sample.pop("loan_repaid", None)

	print("Running demo prediction for worker_id:", sample.get("worker_id"))
	out = predict_worker(sample)
	print("Prediction result:")
	print(json.dumps(out, indent=2))

