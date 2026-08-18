-- 001_initial_schema.sql
-- GigCredit MVP
-- Supabase PostgreSQL migration

BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- =========================================================
-- WORKERS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.workers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    user_id UUID NOT NULL UNIQUE
        REFERENCES auth.users(id) ON DELETE CASCADE,

    full_name TEXT NOT NULL,
    phone TEXT,
    city TEXT,
    primary_platform TEXT,
    experience_months INTEGER NOT NULL DEFAULT 0
        CHECK (experience_months >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- CONSENTS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.consents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    data_type TEXT NOT NULL
        CHECK (
            data_type IN (
                'EARNINGS',
                'WORK_HISTORY',
                'FINANCIAL_DATA',
                'CREDIT_DATA'
            )
        ),

    granted BOOLEAN NOT NULL DEFAULT FALSE,

    granted_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    UNIQUE(worker_id, data_type)
);


-- =========================================================
-- EARNINGS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.earnings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    source TEXT NOT NULL,
    amount NUMERIC(12,2) NOT NULL
        CHECK (amount >= 0),

    earning_date DATE NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- WORK HISTORY
-- =========================================================

CREATE TABLE IF NOT EXISTS public.work_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    platform TEXT NOT NULL,

    active_from DATE,
    active_to DATE,

    jobs_completed INTEGER NOT NULL DEFAULT 0
        CHECK (jobs_completed >= 0),

    jobs_cancelled INTEGER NOT NULL DEFAULT 0
        CHECK (jobs_cancelled >= 0),

    average_rating NUMERIC(3,2)
        CHECK (
            average_rating >= 0
            AND average_rating <= 5
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- FINANCIAL OBLIGATIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.financial_obligations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    obligation_type TEXT NOT NULL,

    monthly_payment NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (monthly_payment >= 0),

    outstanding_amount NUMERIC(12,2) NOT NULL DEFAULT 0
        CHECK (outstanding_amount >= 0),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- CREDIT FEATURES
-- =========================================================

CREATE TABLE IF NOT EXISTS public.credit_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    average_monthly_income NUMERIC(12,2),
    income_stability NUMERIC(5,2),
    income_trend NUMERIC(8,4),

    work_consistency NUMERIC(5,2),
    completion_rate NUMERIC(5,2),
    average_rating NUMERIC(3,2),

    debt_burden NUMERIC(5,2),
    repayment_capacity NUMERIC(12,2),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- CREDIT SCORES
-- =========================================================

CREATE TABLE IF NOT EXISTS public.credit_scores (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    score INTEGER NOT NULL
        CHECK (score >= 0 AND score <= 100),

    risk_probability NUMERIC(6,5)
        CHECK (
            risk_probability >= 0
            AND risk_probability <= 1
        ),

    risk_level TEXT NOT NULL
        CHECK (
            risk_level IN (
                'LOW',
                'LOW_MODERATE',
                'MODERATE',
                'HIGH'
            )
        ),

    recommended_amount NUMERIC(12,2)
        CHECK (recommended_amount >= 0),

    model_version TEXT NOT NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- LOAN APPLICATIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.loan_applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID NOT NULL
        REFERENCES public.workers(id) ON DELETE CASCADE,

    requested_amount NUMERIC(12,2) NOT NULL
        CHECK (requested_amount > 0),

    tenure_months INTEGER NOT NULL
        CHECK (tenure_months > 0),

    status TEXT NOT NULL DEFAULT 'SUBMITTED'
        CHECK (
            status IN (
                'SUBMITTED',
                'UNDER_REVIEW',
                'APPROVED',
                'REJECTED'
            )
        ),

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- LOAN DECISIONS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.loan_decisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    application_id UUID NOT NULL
        REFERENCES public.loan_applications(id) ON DELETE CASCADE,

    recommended_amount NUMERIC(12,2)
        CHECK (recommended_amount >= 0),

    risk_level TEXT NOT NULL
        CHECK (
            risk_level IN (
                'LOW',
                'LOW_MODERATE',
                'MODERATE',
                'HIGH'
            )
        ),

    decision TEXT NOT NULL
        CHECK (
            decision IN (
                'APPROVE',
                'REVIEW',
                'REJECT'
            )
        ),

    reason TEXT,

    model_version TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- AUDIT LOGS
-- =========================================================

CREATE TABLE IF NOT EXISTS public.audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    worker_id UUID
        REFERENCES public.workers(id) ON DELETE SET NULL,

    user_id UUID
        REFERENCES auth.users(id) ON DELETE SET NULL,

    actor_type TEXT NOT NULL
        CHECK (
            actor_type IN (
                'WORKER',
                'LENDER',
                'SYSTEM'
            )
        ),

    action TEXT NOT NULL,
    resource_type TEXT,
    resource_id UUID,

    metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);


-- =========================================================
-- INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_consents_worker_id
    ON public.consents(worker_id);

CREATE INDEX IF NOT EXISTS idx_earnings_worker_id
    ON public.earnings(worker_id);

CREATE INDEX IF NOT EXISTS idx_earnings_date
    ON public.earnings(earning_date);

CREATE INDEX IF NOT EXISTS idx_work_history_worker_id
    ON public.work_history(worker_id);

CREATE INDEX IF NOT EXISTS idx_financial_obligations_worker_id
    ON public.financial_obligations(worker_id);

CREATE INDEX IF NOT EXISTS idx_credit_features_worker_id
    ON public.credit_features(worker_id);

CREATE INDEX IF NOT EXISTS idx_credit_scores_worker_id
    ON public.credit_scores(worker_id);

CREATE INDEX IF NOT EXISTS idx_loan_applications_worker_id
    ON public.loan_applications(worker_id);

CREATE INDEX IF NOT EXISTS idx_loan_decisions_application_id
    ON public.loan_decisions(application_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_worker_id
    ON public.audit_logs(worker_id);


-- =========================================================
-- ROW LEVEL SECURITY
-- =========================================================

ALTER TABLE public.workers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.consents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.earnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.work_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.financial_obligations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.credit_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.loan_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;


-- =========================================================
-- WORKER POLICIES
-- =========================================================

DROP POLICY IF EXISTS workers_owner ON public.workers;

CREATE POLICY workers_owner
ON public.workers
FOR ALL
USING (user_id = auth.uid())
WITH CHECK (user_id = auth.uid());


DROP POLICY IF EXISTS consents_owner ON public.consents;

CREATE POLICY consents_owner
ON public.consents
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = consents.worker_id
        AND w.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = consents.worker_id
        AND w.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS earnings_owner ON public.earnings;

CREATE POLICY earnings_owner
ON public.earnings
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = earnings.worker_id
        AND w.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = earnings.worker_id
        AND w.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS work_history_owner ON public.work_history;

CREATE POLICY work_history_owner
ON public.work_history
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = work_history.worker_id
        AND w.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = work_history.worker_id
        AND w.user_id = auth.uid()
    )
);


DROP POLICY IF EXISTS financial_obligations_owner
ON public.financial_obligations;

CREATE POLICY financial_obligations_owner
ON public.financial_obligations
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = financial_obligations.worker_id
        AND w.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = financial_obligations.worker_id
        AND w.user_id = auth.uid()
    )
);


-- =========================================================
-- CREDIT FEATURES
-- Workers can read their features.
-- Backend/service role will generate them.
-- =========================================================

DROP POLICY IF EXISTS credit_features_select_owner
ON public.credit_features;

CREATE POLICY credit_features_select_owner
ON public.credit_features
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = credit_features.worker_id
        AND w.user_id = auth.uid()
    )
);


-- =========================================================
-- CREDIT SCORES
-- Workers can READ their score.
-- They cannot modify it directly.
-- =========================================================

DROP POLICY IF EXISTS credit_scores_select_owner
ON public.credit_scores;

CREATE POLICY credit_scores_select_owner
ON public.credit_scores
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = credit_scores.worker_id
        AND w.user_id = auth.uid()
    )
);


-- =========================================================
-- LOAN APPLICATIONS
-- =========================================================

DROP POLICY IF EXISTS loan_applications_owner
ON public.loan_applications;

CREATE POLICY loan_applications_owner
ON public.loan_applications
FOR ALL
USING (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = loan_applications.worker_id
        AND w.user_id = auth.uid()
    )
)
WITH CHECK (
    EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = loan_applications.worker_id
        AND w.user_id = auth.uid()
    )
);


-- =========================================================
-- LOAN DECISIONS
-- Worker can read decisions for their applications.
-- Backend creates decisions.
-- =========================================================

DROP POLICY IF EXISTS loan_decisions_select_owner
ON public.loan_decisions;

CREATE POLICY loan_decisions_select_owner
ON public.loan_decisions
FOR SELECT
USING (
    EXISTS (
        SELECT 1
        FROM public.loan_applications la
        JOIN public.workers w
            ON w.id = la.worker_id
        WHERE la.id = loan_decisions.application_id
        AND w.user_id = auth.uid()
    )
);


-- =========================================================
-- AUDIT LOGS
-- =========================================================

DROP POLICY IF EXISTS audit_logs_select_owner
ON public.audit_logs;

CREATE POLICY audit_logs_select_owner
ON public.audit_logs
FOR SELECT
USING (
    user_id = auth.uid()
    OR EXISTS (
        SELECT 1
        FROM public.workers w
        WHERE w.id = audit_logs.worker_id
        AND w.user_id = auth.uid()
    )
);


COMMIT;