# Models

This directory stores trained model artifacts:

- `logreg_pipeline.joblib` — fitted `StandardScaler` + `LogisticRegression` pipeline.
- `feature_names.json` — the exact ordered feature list the pipeline expects, plus training/version metadata.
- `feature_distribution.json` — `[min, max]` each raw input field spanned in the training data, used for out-of-distribution detection at prediction time.

All three are regenerated together by `python -m src.train` (run from `ml-engine/`) and must be committed together.

**See [MODEL_CARD.md](MODEL_CARD.md)** for what the model is, what its
training data is (synthetic, unvalidated currency/unit), the feature
list, why `worker_id` was removed as a model input, before/after
validation metrics, and how out-of-distribution detection works.
