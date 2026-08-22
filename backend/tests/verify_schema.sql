-- verify_schema.sql
-- GigCredit MVP
--
-- Read-only verification script for 002_ml_worker_features.sql (on top of
-- the already-applied 001_initial_schema.sql). Run against the target
-- database (e.g. via `psql` or the Supabase SQL editor) AFTER applying the
-- migration to confirm the live schema matches what the ML engine and its
-- backend adapter expect.
--
-- This script makes no changes; every check is a SELECT against
-- information_schema / pg_catalog. A check "fails" if it returns zero
-- rows (or the wrong row count, as noted).

-- =========================================================
-- 1. workers.experience_months is UNCHANGED (not renamed, not duplicated)
-- =========================================================
-- The ML engine's gig_duration_months is mapped from this column by the
-- backend adapter; no gig_duration_months column should exist in the DB.

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'workers'
AND column_name IN ('experience_months', 'gig_duration_months');
-- Expect: exactly 1 row -> experience_months (int, NOT NULL, default 0).
-- gig_duration_months must NOT appear.


-- =========================================================
-- 2. credit_features: pre-existing derived columns are preserved
-- =========================================================

SELECT column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'credit_features'
AND column_name IN (
    'average_monthly_income',
    'income_stability',
    'income_trend',
    'work_consistency',
    'completion_rate',
    'average_rating',
    'debt_burden',
    'repayment_capacity',
    'created_at',
    'updated_at'
)
ORDER BY column_name;
-- Expect: all 10 rows present, unchanged from 001.


-- =========================================================
-- 3. credit_features: newly added ML raw-input columns exist
-- =========================================================

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'credit_features'
AND column_name IN (
    'income_volatility',
    'income_month_1',
    'income_month_2',
    'income_month_3',
    'income_month_4',
    'income_month_5',
    'income_month_6',
    'working_days_per_month',
    'cancellation_rate',
    'existing_monthly_obligations'
)
ORDER BY column_name;
-- Expect: 10 rows, all nullable (NULL for every pre-existing worker row
-- until the scoring pipeline backfills them).


-- =========================================================
-- 4. credit_features: no duplicate/renamed columns were introduced
-- =========================================================
-- platform_rating must NOT exist as a separate column — the adapter maps
-- credit_features.average_rating -> ML input platform_rating instead.

SELECT column_name
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name = 'credit_features'
AND column_name = 'platform_rating';
-- Expect: 0 rows.


-- =========================================================
-- 5. Full ML input coverage check (existing column OR adapter mapping)
-- =========================================================
-- Every ML-engine raw input must resolve to a column on workers or
-- credit_features, either directly or via the adapter mapping noted in
-- the comment column.

SELECT *
FROM (VALUES
    ('worker_id',                    'credit_features.worker_id',        'direct'),
    ('gig_duration_months',          'workers.experience_months',        'adapter-mapped'),
    ('average_monthly_income',       'credit_features.average_monthly_income', 'direct'),
    ('income_volatility',            'credit_features.income_volatility','direct (new)'),
    ('income_month_1',               'credit_features.income_month_1',  'direct (new)'),
    ('income_month_2',               'credit_features.income_month_2',  'direct (new)'),
    ('income_month_3',               'credit_features.income_month_3',  'direct (new)'),
    ('income_month_4',               'credit_features.income_month_4',  'direct (new)'),
    ('income_month_5',               'credit_features.income_month_5',  'direct (new)'),
    ('income_month_6',               'credit_features.income_month_6',  'direct (new)'),
    ('working_days_per_month',       'credit_features.working_days_per_month', 'direct (new)'),
    ('completion_rate',              'credit_features.completion_rate', 'direct'),
    ('cancellation_rate',            'credit_features.cancellation_rate', 'direct (new)'),
    ('platform_rating',              'credit_features.average_rating',  'adapter-mapped'),
    ('existing_monthly_obligations', 'credit_features.existing_monthly_obligations', 'direct (new)')
) AS ml_input_map(ml_input, db_source, mapping_kind);
-- Reference table only (not a live query against the DB) — cross-check
-- each db_source column actually exists using checks 1-3 above.


-- =========================================================
-- 6. CHECK constraints on the newly added columns only
-- =========================================================

SELECT conname, pg_get_constraintdef(oid)
FROM pg_constraint
WHERE contype = 'c'
AND conrelid = 'public.credit_features'::regclass
AND (
    conname LIKE '%income_month%'
    OR conname LIKE '%income_volatility%'
    OR conname LIKE '%working_days_per_month%'
    OR conname LIKE '%cancellation_rate%'
    OR conname LIKE '%existing_monthly_obligations%'
)
ORDER BY conname;
-- Expect one CHECK per new numeric column (10 total), each bounding to a
-- sane range (>= 0, and <= 100/31 for rate/day fields). No CHECK is
-- expected on average_monthly_income or completion_rate — those are
-- pre-existing columns and were deliberately left unconstrained since
-- existing row data was not verified against those bounds.


-- =========================================================
-- 7. Index on credit_features.worker_id
-- =========================================================

SELECT indexname, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename = 'credit_features'
AND indexdef LIKE '%worker_id%';
-- Expect: idx_credit_features_worker_id.


-- =========================================================
-- 8. RLS still enabled, worker ownership isolation unchanged
-- =========================================================

SELECT relname, relrowsecurity
FROM pg_class
WHERE relname IN (
    'workers', 'earnings', 'work_history',
    'financial_obligations', 'credit_features'
)
AND relnamespace = 'public'::regnamespace;
-- Expect: relrowsecurity = true for all 5 rows (unchanged from 001).

SELECT policyname, cmd, qual
FROM pg_policies
WHERE schemaname = 'public'
AND tablename = 'credit_features';
-- Expect: credit_features_select_owner, cmd = SELECT, qual references
-- workers w ... w.user_id = auth.uid(). Identical to 001 — this
-- migration does not touch policies.


-- =========================================================
-- 9. Manual cross-worker isolation check (run as two different
--    authenticated users / JWTs, not as the service role)
-- =========================================================
-- As user A: have the backend/service role write a credit_features row
-- for A's worker_id (e.g. average_monthly_income = 50000).
-- As user B: SELECT * FROM public.credit_features; -- must return 0 rows
-- belonging to A's worker.
-- As user B: attempt SELECT ... WHERE worker_id = '<A''s worker id>';
-- -- must return 0 rows (RLS filters it out, not just an app-level check).
-- If the service-role key is used instead of a user JWT, RLS is bypassed
-- by design — only test isolation with anon/authenticated-role sessions.
