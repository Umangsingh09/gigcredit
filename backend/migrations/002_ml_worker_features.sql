-- 002_ml_worker_features.sql
-- GigCredit MVP
-- Supabase PostgreSQL migration
--
-- Adds the ML-engine raw input columns that are genuinely missing from
-- the live schema created by 001_initial_schema.sql (already applied —
-- not modified here, and not modified by this migration either).
--
-- Design:
--   - workers.experience_months is UNCHANGED. It is conceptually the same
--     field the ML engine calls gig_duration_months; the backend adapter
--     maps workers.experience_months -> ML input gig_duration_months at
--     read time. No schema change needed or made here.
--   - credit_features is the existing ML-ready, one-row-per-worker
--     feature snapshot table. Its existing derived columns
--     (income_stability, income_trend, work_consistency, average_rating,
--     debt_burden, repayment_capacity) are untouched and fully preserved.
--     average_monthly_income and completion_rate already exist under
--     those exact names and are left as-is (no duplicate added).
--     average_rating already exists and is semantically the ML engine's
--     platform_rating (same 0-5 scale); the backend adapter maps
--     credit_features.average_rating -> ML input platform_rating instead
--     of duplicating the column here.
--   - Only the ML inputs with no existing equivalent are added:
--     income_volatility, income_month_1..6, working_days_per_month,
--     cancellation_rate, existing_monthly_obligations.
--   - earnings / work_history / financial_obligations are not touched.
--
-- Idempotent: safe to run more than once (ADD COLUMN IF NOT EXISTS /
-- CREATE INDEX IF NOT EXISTS throughout).
--
-- No CHECK constraints are added to any pre-existing column
-- (average_monthly_income, completion_rate, average_rating, etc.)
-- because this migration cannot verify that every row already in the
-- live table satisfies them. Every column added below is brand new, so
-- existing rows simply get NULL there and CHECK constraints on them
-- cannot conflict with any existing data.

BEGIN;

-- =========================================================
-- CREDIT_FEATURES: add only the missing ML-engine raw inputs
-- =========================================================

ALTER TABLE public.credit_features
    ADD COLUMN IF NOT EXISTS income_volatility NUMERIC(8,4)
        CHECK (income_volatility >= 0),

    ADD COLUMN IF NOT EXISTS income_month_1 NUMERIC(12,2)
        CHECK (income_month_1 >= 0),
    ADD COLUMN IF NOT EXISTS income_month_2 NUMERIC(12,2)
        CHECK (income_month_2 >= 0),
    ADD COLUMN IF NOT EXISTS income_month_3 NUMERIC(12,2)
        CHECK (income_month_3 >= 0),
    ADD COLUMN IF NOT EXISTS income_month_4 NUMERIC(12,2)
        CHECK (income_month_4 >= 0),
    ADD COLUMN IF NOT EXISTS income_month_5 NUMERIC(12,2)
        CHECK (income_month_5 >= 0),
    ADD COLUMN IF NOT EXISTS income_month_6 NUMERIC(12,2)
        CHECK (income_month_6 >= 0),

    ADD COLUMN IF NOT EXISTS working_days_per_month SMALLINT
        CHECK (working_days_per_month >= 0 AND working_days_per_month <= 31),

    ADD COLUMN IF NOT EXISTS cancellation_rate NUMERIC(5,2)
        CHECK (cancellation_rate >= 0 AND cancellation_rate <= 100),

    ADD COLUMN IF NOT EXISTS existing_monthly_obligations NUMERIC(12,2)
        CHECK (existing_monthly_obligations >= 0);


-- =========================================================
-- INDEXES
-- =========================================================
-- idx_credit_features_worker_id already exists from 001; re-asserted
-- here defensively (no-op if present, harmless if not).

CREATE INDEX IF NOT EXISTS idx_credit_features_worker_id
    ON public.credit_features(worker_id);


-- No RLS changes: credit_features already has RLS enabled and the
-- credit_features_select_owner policy (worker can read only rows where
-- workers.user_id = auth.uid()) from 001. Adding nullable columns to an
-- already-covered table does not require any policy change — RLS is
-- row-level, and every column on the row is already gated by that policy.

COMMIT;
