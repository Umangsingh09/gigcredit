"""train

Train an explainable binary classification model for gig-worker loan
repayment. This script loads the synthetic dataset, applies the shared
feature-engineering pipeline from `features.py`, trains a Logistic
Regression model with a simple scaler, evaluates common metrics, and
saves the trained pipeline and feature metadata to `ml-engine/models/`.

Run from the `ml-engine` directory as:

	python -m src.train

Only `ml-engine/src/train.py` is modified by this step.
"""

import json
import os
from pathlib import Path
from typing import Tuple

try:
	import joblib
	_use_joblib = True
except Exception:
	import pickle
	_use_joblib = False
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
	accuracy_score,
	precision_score,
	recall_score,
	f1_score,
	roc_auc_score,
	confusion_matrix,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .features import build_feature_matrix


def load_data(csv_path: str) -> pd.DataFrame:
	df = pd.read_csv(csv_path)
	return df


def prepare_xy(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
	# Build features using shared feature-engineering code (no duplication)
	X = build_feature_matrix(df)
	# Ensure target exists
	if "loan_repaid" not in df.columns:
		raise ValueError("Expected 'loan_repaid' column in input data")
	y = df["loan_repaid"].astype(int)
	# Remove target if present in X (defensive)
	if "loan_repaid" in X.columns:
		X = X.drop(columns=["loan_repaid"])
	return X, y


def train_and_evaluate(
	X: pd.DataFrame, y: pd.Series, random_state: int = 42
) -> Tuple[Pipeline, dict]:
	# Split with stratification to preserve class distribution
	X_train, X_test, y_train, y_test = train_test_split(
		X, y, test_size=0.2, stratify=y, random_state=random_state
	)

	# Build a simple, explainable pipeline: StandardScaler + LogisticRegression
	clf = Pipeline(
		[
			("scaler", StandardScaler()),
			(
				"logreg",
				LogisticRegression(
					solver="liblinear",
					class_weight="balanced",
					random_state=random_state,
					max_iter=1000,
				),
			),
		]
	)

	clf.fit(X_train, y_train)

	# Predictions and probabilities
	y_pred = clf.predict(X_test)
	try:
		y_prob = clf.predict_proba(X_test)[:, 1]
	except Exception:
		# In rare cases of pipeline misconfiguration
		y_prob = np.zeros_like(y_pred, dtype=float)

	# Evaluation metrics
	metrics = {
		"n_train": int(X_train.shape[0]),
		"n_test": int(X_test.shape[0]),
		"n_features": int(X.shape[1]),
		"accuracy": float(accuracy_score(y_test, y_pred)),
		"precision": float(precision_score(y_test, y_pred, zero_division=0)),
		"recall": float(recall_score(y_test, y_pred, zero_division=0)),
		"f1": float(f1_score(y_test, y_pred, zero_division=0)),
		"roc_auc": float(roc_auc_score(y_test, y_prob)),
		"confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
	}

	return clf, metrics


def save_model(pipeline: Pipeline, feature_names: list, out_dir: str) -> str:
	os.makedirs(out_dir, exist_ok=True)
	model_path = os.path.join(out_dir, "logreg_pipeline.joblib")
	meta_path = os.path.join(out_dir, "feature_names.json")

	if _use_joblib:
		joblib.dump(pipeline, model_path)
	else:
		# Fallback: use pickle when joblib is not available
		with open(model_path, "wb") as f:
			pickle.dump(pipeline, f)
	with open(meta_path, "w", encoding="utf-8") as f:
		json.dump({"feature_names": feature_names}, f, indent=2)

	return model_path


def main():
	# Paths relative to this file (ml-engine/src)
	base_dir = Path(__file__).resolve().parent
	csv_path = (base_dir / ".." / "data" / "gig_workers.csv").resolve()
	models_dir = (base_dir / ".." / "models").resolve()

	print("Loading data from:", csv_path)
	df = load_data(str(csv_path))

	X, y = prepare_xy(df)

	pipeline, metrics = train_and_evaluate(X, y, random_state=42)

	# Save model and feature metadata
	model_path = save_model(pipeline, list(X.columns), str(models_dir))

	# Print evaluation summary
	print("\nTraining completed")
	print("Model saved to:", model_path)
	print("Number of training samples:", metrics["n_train"])
	print("Number of test samples:", metrics["n_test"])
	print("Feature count:", metrics["n_features"])
	print("Model: LogisticRegression (liblinear, class_weight=balanced)")
	print(f"Accuracy: {metrics['accuracy']:.4f}")
	print(f"Precision: {metrics['precision']:.4f}")
	print(f"Recall: {metrics['recall']:.4f}")
	print(f"F1-score: {metrics['f1']:.4f}")
	print(f"ROC-AUC: {metrics['roc_auc']:.4f}")
	print("Confusion matrix:", metrics["confusion_matrix"])


if __name__ == "__main__":
	main()

