"""features

Feature-engineering utilities for the GigCredit ML Engine.

This module provides a simple, deterministic, and reusable feature
transformation that converts raw worker rows (the CSV produced by
`data_generator.generate_dataset`) into a feature matrix suitable for
training and prediction. Important constraints:
- `loan_repaid` is never used as an input feature (no leakage).
- Transformations are deterministic and handle missing values safely.
- The same transformations can be applied during training and at
  prediction time via the `FeatureEngineer` class.
"""

from typing import Iterable, List

import numpy as np
import pandas as pd


REQUIRED_COLUMNS = {
	"worker_id",
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
}


def _validate_columns(df: pd.DataFrame) -> None:
	missing = REQUIRED_COLUMNS - set(df.columns)
	if missing:
		raise ValueError(f"Missing required columns for feature engineering: {sorted(missing)}")


def _median_fill(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
	for c in cols:
		if df[c].isna().any():
			df[c] = df[c].fillna(df[c].median())
	return df


def _compute_income_trend(row_values: np.ndarray) -> float:
	# Fit a simple linear trend across the 6 months; return slope normalized
	# by mean income to keep scale stable across income levels.
	x = np.arange(len(row_values))
	# If all values are identical, polyfit can return NaN; handle gracefully.
	try:
		slope = np.polyfit(x, row_values, 1)[0]
	except Exception:
		slope = 0.0
	mean = np.mean(row_values) if np.mean(row_values) != 0 else 1.0
	return float(slope / mean)


class FeatureEngineer:
	"""Deterministic, reusable feature engineering pipeline.

	Usage:
	  fe = FeatureEngineer()
	  fe.fit(df)          # currently a no-op kept for compatibility
	  X = fe.transform(df)

	The pipeline validates inputs, fills missing values with medians,
	computes several explainable features (income stability, trend,
	obligation ratios, behavioral metrics), and returns a clean DataFrame
	without the `loan_repaid` column.
	"""

	def fit(self, df: pd.DataFrame) -> "FeatureEngineer":
		_validate_columns(df)
		return self

	def transform(self, df: pd.DataFrame) -> pd.DataFrame:
		_validate_columns(df)

		df = df.copy()

		# Fill numeric missing values with medians for determinism
		numeric_cols = [
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
		df = _median_fill(df, numeric_cols)

		# Income history matrix (6 months)
		income_cols = [f"income_month_{i}" for i in range(1, 7)]
		incomes = df[income_cols].astype(float).values

		monthly_mean = np.mean(incomes, axis=1)
		monthly_std = np.std(incomes, axis=1)
		income_cv = monthly_std / (monthly_mean + 1e-9)

		# Income stability: higher is better (bounded between 0 and 1)
		income_stability = 1.0 / (1.0 + income_cv)

		# Recent income: mean of the last 3 months
		recent_income_mean = np.mean(incomes[:, -3:], axis=1)

		# Income trend (normalized slope)
		income_trend = np.array([_compute_income_trend(row) for row in incomes])

		# Months with zero income (indicator of gaps)
		months_zero = np.sum(incomes <= 0.0, axis=1)

		# Obligation-to-income ratio
		obligation_to_income = (
			df["existing_monthly_obligations"].astype(float) / (df["average_monthly_income"].astype(float) + 1e-9)
		)

		# Income per working day
		income_per_workday = df["average_monthly_income"].astype(float) / (
			df["working_days_per_month"].astype(float) + 1e-9
		)

		# Build feature DataFrame. Keep worker_id for mapping but it should not
		# be used as an input to models unless explicitly desired.
		X = pd.DataFrame(
			{
				"worker_id": df["worker_id"].values,
				"average_monthly_income": df["average_monthly_income"].astype(float),
				"income_volatility": df["income_volatility"].astype(float),
				"income_stability": income_stability,
				"income_cv": income_cv,
				"income_trend": income_trend,
				"recent_income_mean": recent_income_mean,
				"months_zero_income": months_zero,
				"working_days_per_month": df["working_days_per_month"].astype(float),
				"gig_duration_months": df["gig_duration_months"].astype(float),
				"completion_rate": df["completion_rate"].astype(float),
				"cancellation_rate": df["cancellation_rate"].astype(float),
				"platform_rating": df["platform_rating"].astype(float),
				"existing_monthly_obligations": df["existing_monthly_obligations"].astype(float),
				"obligation_to_income": obligation_to_income.astype(float),
				"income_per_workday": income_per_workday.astype(float),
			}
		)

		# Final NaN handling: replace any remaining NaNs with 0 to ensure
		# downstream models do not break. This should be rare due to median
		# filling above.
		if X.isna().any().any():
			X = X.fillna(0.0)

		return X


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
	"""Convenience function: validate and transform a raw worker DataFrame.

	Returns a feature matrix DataFrame. Does not include `loan_repaid`.
	"""

	fe = FeatureEngineer()
	fe.fit(df)
	return fe.transform(df)


if __name__ == "__main__":
	# Quick verification when executed as a script. This will load the
	# generated CSV, run the feature pipeline, and print basic checks.
	import os

	csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "gig_workers.csv")
	csv_path = os.path.normpath(csv_path)

	print("Loading:", csv_path)
	df = pd.read_csv(csv_path)

	X = build_feature_matrix(df)

	print("Feature matrix shape:", X.shape)
	print("Feature columns:", list(X.columns))
	print("Is 'loan_repaid' present in X? ->", "loan_repaid" in X.columns)
	print("Any NaNs in feature matrix? ->", X.isna().any().any())

