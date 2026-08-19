# GigCredit Credit-Risk Model — Model Card

## Current version: 2.0.0

Trained by `ml-engine/src/train.py` (`python -m src.train` from `ml-engine/`).
Artifacts: `logreg_pipeline.joblib`, `feature_names.json`, `feature_distribution.json`.

## What this model is

A `StandardScaler` + `LogisticRegression` (liblinear, `class_weight="balanced"`)
pipeline predicting `loan_repaid` (binary) for a gig worker, trained on
**synthetic demo data** — see "Training data" below.

## Training data

- Source: `ml-engine/data/gig_workers.csv`, produced by
  `ml-engine/src/data_generator.py::generate_dataset(n_workers=2000, random_seed=42)`.
- **This is synthetic data, not real GigCredit worker data.** It exists to
  exercise the ML pipeline end-to-end during development.
- **Income/currency unit is undocumented and unvalidated.** Nothing in
  the codebase, comments, or READMEs states what currency or unit
  `average_monthly_income` / `income_month_1..6` / `existing_monthly_obligations`
  are denominated in. Do not assume INR, USD, or any other currency, and
  do not apply a conversion factor to make it "look like" one — there is
  no evidence base for any such conversion. Treat the income scale below
  as an arbitrary synthetic range until it is deliberately validated
  against real GigCredit production income figures.
- Training value ranges (from `feature_distribution.json`, computed at
  train time from the raw training CSV):

  | Field | min | max |
  |---|---|---|
  | `average_monthly_income` | 150.0 | 9,242.27 |
  | `income_month_1..6` | 0.0 | ~10,175–12,672 |
  | `existing_monthly_obligations` | 0.0 | 2,970.41 |
  | `working_days_per_month` | 5 | 30 |
  | `gig_duration_months` | 3 | 47 |
  | `completion_rate` (fraction) | 0.0 | 1.0 |
  | `cancellation_rate` (fraction) | 0.0 | 0.402 |
  | `platform_rating` | 2.23 | 5.0 |

  The fitted `StandardScaler` has no information about values outside
  these ranges; predictions on inputs far outside them are numerically
  extrapolated, not learned. See "Out-of-distribution detection" below.

## Feature set (15 features, in pipeline order)

```
average_monthly_income, income_volatility, income_stability, income_cv,
income_trend, recent_income_mean, months_zero_income,
working_days_per_month, gig_duration_months, completion_rate,
cancellation_rate, platform_rating, existing_monthly_obligations,
obligation_to_income, income_per_workday
```

This exact list, in this exact order, is saved in `feature_names.json`
alongside the model metadata. `explain.py` reindexes its feature matrix
to this list before computing contributions — the list and the fitted
pipeline must always be regenerated and shipped together.

## Why `worker_id` was removed (v1 → v2.0.0)

The original model (implicit "v1", 16 features, `worker_id` listed
first in `feature_names.json`) included `worker_id` — a plain
sequential row identifier (`data_generator.py`: `worker_id = np.arange(1, n+1)`)
— as a *scaled input to the classifier*. `worker_id` has no causal
relationship to `loan_repaid` by construction (it's assigned before any
risk-related random draw and never enters the `latent_risk` formula
that drives the synthetic label). Despite that, the fitted v1 model
gave it a non-trivial coefficient — empirically its logit contribution
ranged from about **+0.24** (`worker_id=0`) to **-0.24**
(`worker_id=2000`), enough to flip `risk_category` (e.g. MEDIUM↔HIGH,
LOW↔MEDIUM) for identical real financial/behavioral data, purely as a
function of an arbitrary placeholder.

This was a code defect, not a design choice: `features.py` already
carried a comment ("should not be used as an input to models unless
explicitly desired") that was never enforced in `train.py`. v2.0.0 fixes
this: `FeatureEngineer.transform()` no longer includes `worker_id` in
the feature matrix `X` used for scaling/fitting/predicting. `worker_id`
remains part of the raw input contract (`REQUIRED_COLUMNS` in
`features.py`) purely for row/worker identification by callers — it is
simply never passed to the classifier.

### Validation impact of removing `worker_id`

Evaluated with the identical `train_and_evaluate` methodology, same
`train_test_split(random_state=42, stratify=y)`, same 2000-row dataset —
only the presence/absence of `worker_id` in `X` differs:

| Metric | v1 (16 features, incl. worker_id) | v2.0.0 (15 features) | Δ |
|---|---|---|---|
| Accuracy | 0.6400 | 0.6450 | +0.0050 |
| Precision | 0.9056 | 0.9030 | -0.0026 |
| Recall | 0.6336 | 0.6426 | +0.0090 |
| F1 | 0.7456 | 0.7509 | +0.0053 |
| ROC-AUC | 0.7322 | 0.7292 | -0.0029 |
| Confusion matrix | `[[45,22],[122,211]]` | `[[44,23],[119,214]]` | ~1 sample shifted per cell |

**Removing `worker_id` did not materially change validation
performance** — every metric moved by well under 1 percentage point,
consistent with `worker_id` having contributed noise rather than signal.
No attempt was made to preserve v1's performance where that performance
depended on `worker_id`; the goal was correctness, not matching the old
numbers.

## Out-of-distribution detection

`distribution_check.py` records the `[min, max]` each raw numeric input
field spanned in the training data (`feature_distribution.json`,
regenerated every training run). `predict_worker()` and
`explain_worker()` (in `predict.py` / `explain.py`) check every request
against these bounds and add two fields to their output:

- `out_of_distribution` (bool) — true if any checked field fell outside
  its training range.
- `out_of_distribution_fields` — list of `{field, value, training_min,
  training_max}` for every field that triggered the flag.

**Values are never clamped, rescaled, or otherwise altered.** A
prediction is still returned even when flagged — the flag is metadata
for the caller to act on (e.g. surface a warning, require manual
review, or refuse to auto-decision), not a veto baked into the model
itself. A `risk_category` of `LOW` with `out_of_distribution: true`
means "the model is confident, but has never seen data anywhere near
this — that confidence is not earned." This is a known, current gap in
the backend integration: `backend/app/services/ml` does not yet read or
surface `out_of_distribution` in its API response (see integration
notes below) — the flag exists at the ML-engine level today.

## Retraining

```
cd ml-engine
python -m src.train
```

Regenerates all three artifacts (`logreg_pipeline.joblib`,
`feature_names.json`, `feature_distribution.json`) from
`data/gig_workers.csv`. All three must be regenerated together and
committed together — they are a matched set tied to the same feature
schema.

## Known limitations / follow-ups (not fixed by this version)

1. **Income scale is unvalidated against real GigCredit income.** Until
   real (or realistically calibrated) data is available, treat any
   prediction on income figures that plausibly reflect real-world
   worker earnings as **out-of-distribution by default** — check the
   `out_of_distribution` flag rather than trusting `risk_category` at
   face value.
2. **The backend adapter does not yet surface `out_of_distribution` in
   its API response.** `backend/app/services/ml/service.py` currently
   extracts only `repayment_probability`, `default_probability`,
   `predicted_class`, `risk_score`, `risk_category`,
   `top_risk_factors`, `top_positive_factors`, and `explanation` from
   the prediction/explanation dicts. The new OOD fields pass through
   `predictor.py` unused today. Wiring them into
   `CreditPredictionResult` / `CreditPredictionResponse` is a
   deliberately separate, future change to `backend/app`.
3. **This is still a synthetic-data model.** No amount of internal
   fixes (worker_id removal, OOD detection) makes v2.0.0 validated for
   real lending decisions — it demonstrates the pipeline, not
   production-grade risk assessment.
