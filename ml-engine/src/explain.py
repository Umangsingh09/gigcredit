"""explain

Explainability helpers for GigCredit predictions. For a given worker input
the module identifies the most influential features and explains which
increase risk and which reduce risk.

The explanation is based on the trained LogisticRegression pipeline saved
in `ml-engine/models/` and uses the same feature-engineering from
`features.py`.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

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
from .predict import _safe_build_input, MODEL_NAME


FEATURE_META = "feature_names.json"


def _load_pipeline(models_dir: str):
	model_path = os.path.join(models_dir, MODEL_NAME)
	if _use_joblib:
		return joblib.load(model_path)
	else:
		with open(model_path, "rb") as f:
			return pickle.load(f)


def _load_feature_names(models_dir: str) -> List[str]:
	meta_path = os.path.join(models_dir, FEATURE_META)
	if not os.path.exists(meta_path):
		raise FileNotFoundError(f"Feature metadata not found at {meta_path}")
	with open(meta_path, "r", encoding="utf-8") as f:
		data = json.load(f)
	return data.get("feature_names", [])


def _contributions_for_row(pipeline, X: pd.DataFrame) -> Tuple[np.ndarray, float]:
	"""Return per-feature contribution to the logit for repayment and intercept."""
	# Expect pipeline with scaler and logreg
	steps = pipeline.steps if hasattr(pipeline, "steps") else []
	scaler = None
	logreg = None
	for name, step in steps:
		if name == "scaler":
			scaler = step
		if name == "logreg":
			logreg = step

	if logreg is None:
		# fallback: try to access last estimator
		logreg = pipeline

	if scaler is not None:
		X_scaled = scaler.transform(X)
	else:
		X_scaled = X.values

	coef = getattr(logreg, "coef_")
	intercept = float(getattr(logreg, "intercept_")[0]) if hasattr(logreg, "intercept_") else 0.0
	coef = np.asarray(coef).reshape(-1)

	# contribution to logit for repayment = coef * X_scaled (elementwise)
	contribs = coef * X_scaled[0]
	return contribs, intercept


def explain_worker(
	input_data: Dict[str, Any],
	models_dir: str = None,
	top_k: int = 5,
	pipeline: Any = None,
) -> Dict[str, Any]:
	base_dir = Path(__file__).resolve().parent
	if models_dir is None:
		models_dir = (base_dir / ".." / "models").resolve()
	else:
		models_dir = Path(models_dir).resolve()

	if pipeline is None:
		pipeline = _load_pipeline(str(models_dir))
	feature_names = _load_feature_names(str(models_dir))

	# Prepare input and features
	raw_df = _safe_build_input(input_data)
	X = build_feature_matrix(raw_df)

	# Flag inputs outside the training data's value range (see
	# distribution_check.py and ml-engine/models/MODEL_CARD.md). Never
	# alters the input — only surfaces the warning alongside the
	# explanation.
	distribution_bounds = load_distribution(str(models_dir))
	ood_fields = check_out_of_distribution(raw_df.iloc[0].to_dict(), distribution_bounds)

	# Ensure feature ordering matches training
	if feature_names:
		X = X.reindex(columns=feature_names)

	# Get repayment probability and predicted class using pipeline
	try:
		proba = float(pipeline.predict_proba(X)[:, 1][0])
		pred = int(pipeline.predict(X)[0])
	except Exception:
		proba = 0.5
		pred = 1 if proba >= 0.5 else 0

	default_prob = 1.0 - proba

	# Compute contributions to repayment logit
	contribs, intercept = _contributions_for_row(pipeline, X)

	# Map contributions to feature names and sort
	feats = list(X.columns)
	contrib_pairs = list(zip(feats, contribs.tolist()))

	# Features that reduce repayment probability (negative contrib) increase risk
	contrib_pairs_sorted = sorted(contrib_pairs, key=lambda x: x[1])

	top_risk = contrib_pairs_sorted[:top_k]  # most negative
	top_positive = contrib_pairs_sorted[::-1][:top_k]

	def _format_list(pairs):
		return [{"feature": f, "contribution": float(round(v, 6))} for f, v in pairs]

	top_risk_fmt = _format_list(top_risk)
	top_positive_fmt = _format_list(top_positive)

	# Risk score and category consistent with predict.py
	risk_score = float(round(default_prob, 4))
	if risk_score < 0.25:
		risk_category = "LOW"
	elif risk_score < 0.5:
		risk_category = "MEDIUM"
	else:
		risk_category = "HIGH"

	# Human-readable explanation
	explanation_lines = []
	explanation_lines.append(f"Predicted repayment probability: {proba:.3f} (class={pred})")
	explanation_lines.append(f"Risk score (default probability): {risk_score:.3f} -> {risk_category}")
	explanation_lines.append("")
	explanation_lines.append("Top factors increasing risk (reduce repayment probability):")
	for f, v in top_risk:
		explanation_lines.append(f" - {f}: contribution {v:+.4f}")
	explanation_lines.append("")
	explanation_lines.append("Top factors reducing risk (increase repayment probability):")
	for f, v in top_positive:
		explanation_lines.append(f" - {f}: contribution {v:+.4f}")

	explanation_text = "\n".join(explanation_lines)

	result = {
		"risk_score": risk_score,
		"risk_category": risk_category,
		"predicted_class": pred,
		"top_risk_factors": top_risk_fmt,
		"top_positive_factors": top_positive_fmt,
		"explanation": explanation_text,
		"out_of_distribution": bool(ood_fields),
		"out_of_distribution_fields": ood_fields,
	}

	return result


if __name__ == "__main__":
	# Demo: explain first worker from CSV
	base_dir = Path(__file__).resolve().parent
	csv_path = (base_dir / ".." / "data" / "gig_workers.csv").resolve()
	print("Loading sample input from:", csv_path)
	df = pd.read_csv(csv_path)

	sample = df.iloc[0].to_dict()
	sample.pop("loan_repaid", None)

	out = explain_worker(sample)
	print("Explanation result:")
	print(json.dumps(out, indent=2))

