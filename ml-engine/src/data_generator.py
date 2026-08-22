"""data_generator

Generate a reproducible synthetic demo dataset for training and testing an
alternative credit risk model for gig workers. This module provides a
single function `generate_dataset(n_workers, random_seed)` that returns a
`pandas.DataFrame` with worker features and a binary `loan_repaid` target.

The file is intentionally *only* responsible for dataset generation and
does not train models, call external services, or persist any secrets.
"""

from typing import Optional

import numpy as np
import pandas as pd


def generate_dataset(n_workers: int = 2000, random_seed: int = 42) -> pd.DataFrame:
	"""Generate a synthetic dataset of gig workers.

	Parameters
	----------
	n_workers : int
		Number of synthetic workers to generate (default 2000).
	random_seed : int
		RNG seed for reproducibility (default 42).

	Returns
	-------
	pandas.DataFrame
		DataFrame with the requested features and the `loan_repaid` target.

	Notes
	-----
	The target `loan_repaid` is generated from a hidden latent risk score
	(a combination of income, volatility, obligations, and behavioral
	signals). A small amount of noise is added and a logistic transform is
	used to convert risk into a repayment probability; the final label is
	sampled from that probability. The latent risk and repayment
	probability are not included in the returned DataFrame.
	"""

	rng = np.random.default_rng(random_seed)

	# 1) Identifiers
	worker_id = np.arange(1, n_workers + 1)

	# 2) Latent reliability (0..1). Higher = more reliable worker.
	reliability = rng.beta(a=2.0, b=2.0, size=n_workers)

	# 3) Platform rating correlated with reliability (range 1..5)
	platform_rating = np.clip(
		rng.normal(loc=3.0 + reliability * 1.5, scale=0.4, size=n_workers), 1.0, 5.0
	)

	# 4) Working days per month (int between 5 and 30), correlated with reliability
	working_days_per_month = np.clip(
		(rng.normal(loc=15 + reliability * 10, scale=4.0, size=n_workers)).round(), 5, 30
	).astype(int)

	# 5) Gig duration in months (positive integer), longer when reliability is higher
	gig_duration_months = np.maximum(1, rng.poisson(lam=6 + reliability * 30).astype(int))

	# 6) Completion & cancellation rates (0..1)
	completion_rate = np.clip(
		reliability + rng.normal(loc=0.0, scale=0.08, size=n_workers), 0.0, 1.0
	)
	# Cancellation tends to be higher when completion is lower
	cancellation_rate = np.clip(
		np.clip(0.25 * (1.0 - completion_rate) + rng.normal(0.02, 0.05, n_workers), 0.0, 1.0),
		0.0,
		1.0,
	)

	# 7) Average monthly income: base log-normal distribution, adjusted by
	# working intensity and reliability (keeps values realistic)
	base_income = rng.lognormal(mean=7.0, sigma=0.6, size=n_workers)
	# scale by working days and reliability
	average_monthly_income = (
		base_income * (0.5 + working_days_per_month / 30.0) * (0.8 + reliability * 0.6)
	)
	# enforce a sensible minimum
	average_monthly_income = np.clip(average_monthly_income, 150.0, None)

	# 8) Income volatility (coefficient of variation), lower for more
	# reliable workers
	income_volatility = np.clip(0.05 + (1.0 - reliability) * 0.6 + rng.normal(0.0, 0.03, n_workers), 0.01, 1.5)

	# 9) Existing monthly obligations (non-negative), correlated with income
	existing_monthly_obligations = np.maximum(
		0.0, rng.normal(loc=0.18 * average_monthly_income, scale=0.08 * average_monthly_income)
	)

	# 10) Generate six months of income history using average and volatility
	incomes = []
	for m in range(6):
		month_income = rng.normal(
			loc=average_monthly_income, scale=np.maximum(1.0, average_monthly_income * income_volatility)
		)
		# ensure non-negative and realistic rounding
		month_income = np.clip(month_income, 0.0, None)
		incomes.append(np.round(month_income, 2))

	income_month_1, income_month_2, income_month_3, income_month_4, income_month_5, income_month_6 = incomes

	# 11) Hidden latent risk score (higher = more risky). Combine meaningful
	# features; keep scale moderate and add small gaussian noise.
	# Note: do NOT store or return this score.
	# Components: lower income reduces risk, higher volatility increases risk,
	# high obligations relative to income increase risk, behavioral signals
	# (cancellation/completion/rating) affect risk, and stability (duration)
	# lowers risk.
	log_income = np.log1p(average_monthly_income)
	rel_obligations = existing_monthly_obligations / (average_monthly_income + 1e-6)

	latent_risk = (
		-0.6 * log_income
		+ 1.8 * income_volatility
		+ 1.6 * rel_obligations
		+ 1.2 * cancellation_rate
		- 1.4 * completion_rate
		- 0.02 * gig_duration_months
		- 0.25 * platform_rating
		+ rng.normal(loc=0.0, scale=0.25, size=n_workers)
	)

	# Convert latent risk to repayment probability via logistic transform
	def _sigmoid(x: np.ndarray) -> np.ndarray:
		return 1.0 / (1.0 + np.exp(-x))

	# We invert risk so higher latent_risk -> lower repayment probability
	logits = -latent_risk
	repay_prob = _sigmoid(logits)

	# Calibrate repayment probabilities to avoid severe class imbalance in
	# the synthetic demo dataset while preserving relative ordering from the
	# latent risk score. We adjust the logits by a small bias so the mean
	# repayment probability falls into a realistic range (~80% repaid).
	# This keeps probabilistic sampling and the relationships intact.
	desired_mean = 0.80  # target mean repayment probability (80%)
	# Compute current mean probability and transform to logit space
	current_mean = float(repay_prob.mean())
	# Avoid degenerate cases
	eps = 1e-6
	current_mean = np.clip(current_mean, eps, 1.0 - eps)
	desired_mean = np.clip(desired_mean, eps, 1.0 - eps)
	logit = lambda p: np.log(p / (1.0 - p))
	bias = logit(desired_mean) - logit(current_mean)

	# Apply bias to logits and recompute probabilities
	adjusted_logits = logits + bias
	repay_prob = _sigmoid(adjusted_logits)

	# Clamp probabilities to avoid exact 0/1 extreme values
	repay_prob = np.clip(repay_prob, 0.01, 0.99)

	# 12) Sample binary target (probabilistic)
	loan_repaid = rng.binomial(n=1, p=repay_prob, size=n_workers).astype(int)

	# Build DataFrame with required columns
	df = pd.DataFrame(
		{
			"worker_id": worker_id,
			"average_monthly_income": np.round(average_monthly_income, 2),
			"income_volatility": np.round(income_volatility, 3),
			"working_days_per_month": working_days_per_month,
			"gig_duration_months": gig_duration_months,
			"completion_rate": np.round(completion_rate, 3),
			"cancellation_rate": np.round(cancellation_rate, 3),
			"platform_rating": np.round(platform_rating, 2),
			"existing_monthly_obligations": np.round(existing_monthly_obligations, 2),
			"income_month_1": income_month_1,
			"income_month_2": income_month_2,
			"income_month_3": income_month_3,
			"income_month_4": income_month_4,
			"income_month_5": income_month_5,
			"income_month_6": income_month_6,
			"loan_repaid": loan_repaid,
		}
	)

	# Final sanity enforcement of types and bounds
	df["completion_rate"] = df["completion_rate"].clip(0.0, 1.0)
	df["cancellation_rate"] = df["cancellation_rate"].clip(0.0, 1.0)
	df["platform_rating"] = df["platform_rating"].clip(1.0, 5.0)
	df["existing_monthly_obligations"] = df["existing_monthly_obligations"].clip(0.0)

	return df


if __name__ == "__main__":
	# Generate dataset and save to CSV
	df = generate_dataset(n_workers=2000, random_seed=42)

	out_path = "data/gig_workers.csv"
	# Save using a relative path from this file's directory (ml-engine/src -> ml-engine/data)
	df.to_csv(out_path, index=False)

	# Print brief summaries
	print("Generated dataset saved to:", out_path)
	print("Shape:", df.shape)
	print("Columns:", list(df.columns))
	print("\nFirst 5 rows:")
	print(df.head().to_string(index=False))
	print("\nDescriptive statistics:")
	print(df.describe(include="all"))
	print("\nloan_repaid distribution:")
	print(df["loan_repaid"].value_counts(dropna=False))

