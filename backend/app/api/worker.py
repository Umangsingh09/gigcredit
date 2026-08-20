import random
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException

from backend.app.schemas.worker import (
    WorkerProfileSchema,
    GigPlatformSchema,
    UpdateProfileRequest,
    ConsentItemSchema,
    ConsentToggleRequest,
    PlatformToggleRequest,
    GigCreditScoreSchema,
    ScoreFactorSchema,
    ApplyLoanRequest,
    LoanApplicationSchema,
    NotificationSchema,
)

router = APIRouter(prefix="/worker", tags=["Worker App Backend"])

# In-Memory Backend Data Store for Worker App
MOCK_WORKER_PROFILE = WorkerProfileSchema(
    id="wrk_8849",
    name="Raja Kumar",
    phone="+91 98765 43210",
    city="Bengaluru, KA",
    panNumber="ABCDE1234F",
    upiId="raja.kumar@okaxis",
    totalMonthsExperience=18,
    avgDailyHours=8.5,
    isOnboarded=True,
    platforms=[
        GigPlatformSchema(
            id="p_swiggy",
            name="Swiggy Food",
            logo="swiggy",
            monthlyEarnings=14200.0,
            rating=4.9,
            tripsCompleted=420,
            isConnected=True,
            workType="Food Delivery",
        ),
        GigPlatformSchema(
            id="p_zomato",
            name="Zomato",
            logo="zomato",
            monthlyEarnings=10500.0,
            rating=4.85,
            tripsCompleted=310,
            isConnected=True,
            workType="Food Delivery",
        ),
        GigPlatformSchema(
            id="p_uber",
            name="Uber India",
            logo="uber",
            monthlyEarnings=6200.0,
            rating=4.8,
            tripsCompleted=95,
            isConnected=True,
            workType="Rideshare Driver",
        ),
        GigPlatformSchema(
            id="p_urbancompany",
            name="Urban Company",
            logo="urban",
            monthlyEarnings=0.0,
            rating=0.0,
            tripsCompleted=0,
            isConnected=False,
            workType="Home Services",
        ),
    ],
)

MOCK_CONSENTS = {
    "c_bank_cashflow": ConsentItemSchema(
        id="c_bank_cashflow",
        title="Bank Account Cashflow Sync",
        subtitle="Read-only access to verify direct deposit payouts",
        description="Validates income stability and recurring earnings directly from linked bank account AA feeds.",
        category="Banking",
        dataPoints="Statement deposits, daily balance averages, recurring credits",
        isGranted=True,
        isMandatory=True,
        lastUpdated=datetime.now(),
    ),
    "c_gig_ratings": ConsentItemSchema(
        id="c_gig_ratings",
        title="Gig Platform Ratings & Trips",
        subtitle="Aggregates completed deliveries, customer stars, and work tenure",
        description="Proves work reliability and platform tenure to unlock lower interest rates.",
        category="Platform Work",
        dataPoints="Customer rating average, total trips completed, active work months",
        isGranted=True,
        isMandatory=True,
        lastUpdated=datetime.now(),
    ),
    "c_location_telematics": ConsentItemSchema(
        id="c_location_telematics",
        title="Work Location & Operating Zone",
        subtitle="Verifies regular active work areas in your registered city",
        description="Used by AI risk algorithms to detect consistent work shifts and active delivery hubs.",
        category="Logistics",
        dataPoints="Aggregated daily work hours, primary operating pin codes",
        isGranted=True,
        isMandatory=False,
        lastUpdated=datetime.now(),
    ),
    "c_utility_bills": ConsentItemSchema(
        id="c_utility_bills",
        title="Utility & Mobile Bill Timeliness",
        subtitle="Checks on-time payment history for electricity and phone bills",
        description="Demonstrates financial responsibility even without traditional CIBIL score history.",
        category="Alternative Credit",
        dataPoints="Bill payment timestamps, mobile recharge regularity",
        isGranted=True,
        isMandatory=False,
        lastUpdated=datetime.now(),
    ),
    "c_tax_returns": ConsentItemSchema(
        id="c_tax_returns",
        title="ITR / Form 26AS Tax Proofs",
        subtitle="Optional tax filing submission for higher loan limits",
        description="Unlocks maximum loan limits up to ₹1,50,000 for verified tax-paying gig workers.",
        category="Taxation",
        dataPoints="Gross taxable income, Form 26AS TDS receipts",
        isGranted=False,
        isMandatory=False,
        lastUpdated=datetime.now(),
    ),
}

MOCK_LOANS: list[LoanApplicationSchema] = [
    LoanApplicationSchema(
        id="app_1092",
        referenceId="GC-LOAN-8849-01",
        requestedAmount=35000.0,
        tenureMonths=6,
        interestRateMonthly=0.012,
        calculatedEmi=6100.0,
        status="underwriting",
        purpose="Vehicle Repair / Maintenance",
        appliedAt=datetime.now() - timedelta(hours=4),
        lenderName="GigCredit Lending NBFC",
    )
]

MOCK_NOTIFICATIONS: list[NotificationSchema] = [
    NotificationSchema(
        id="n_1",
        title="Application Under Review ⏳",
        message="Your loan application GC-LOAN-8849-01 is currently under AI underwriting.",
        timestamp=datetime.now() - timedelta(minutes=30),
        isRead=False,
        type="loan",
    ),
    NotificationSchema(
        id="n_2",
        title="GigCredit Score Up! ⚡",
        message="Your score increased to 742 after linking Uber driver account.",
        timestamp=datetime.now() - timedelta(hours=12),
        isRead=True,
        type="score",
    ),
]


def _calculate_score_internal() -> GigCreditScoreSchema:
    total_income = sum(p.monthlyEarnings for p in MOCK_WORKER_PROFILE.platforms if p.isConnected)
    connected_count = sum(1 for p in MOCK_WORKER_PROFILE.platforms if p.isConnected)
    granted_consents = sum(1 for c in MOCK_CONSENTS.values() if c.isGranted)

    base = 620.0 + (connected_count * 25) + (granted_consents * 20)
    if total_income > 25000:
        base += 45
    elif total_income > 15000:
        base += 25

    score_val = int(min(max(base, 300), 900))

    if score_val >= 740:
        tier = "Prime Gig Credit"
        max_loan = 80000.0
    elif score_val >= 680:
        tier = "Good Credit"
        max_loan = 50000.0
    elif score_val >= 600:
        tier = "Fair Credit"
        max_loan = 25000.0
    else:
        tier = "Developing Credit"
        max_loan = 10000.0

    return GigCreditScoreSchema(
        score=score_val,
        riskCategory=tier,
        incomeStabilityScore=min(95.0, round(total_income / 350.0, 1)),
        workConsistencyScore=88.0,
        debtBurdenRatio=18.5,
        maxRecommendedLoan=max_loan,
        factors=[
            ScoreFactorSchema(
                title="Platform Earnings Consistency",
                description="Based on last 4 months aggregated Swiggy & Zomato weekly payouts.",
                impact="+45 pts",
                isPositive=True,
                iconType="trending_up",
            ),
            ScoreFactorSchema(
                title="Customer Rating (4.88★)",
                description="Top 10% rated delivery partner in Bengaluru zone.",
                impact="+35 pts",
                isPositive=True,
                iconType="star",
            ),
            ScoreFactorSchema(
                title="Consents Granted",
                description=f"{granted_consents} out of {len(MOCK_CONSENTS)} consents active in vault.",
                impact="+60 pts",
                isPositive=granted_consents >= 3,
                iconType="shield",
            ),
        ],
        calculatedAt=datetime.now(),
    )


@router.get("/profile", response_model=WorkerProfileSchema)
def get_worker_profile():
    return MOCK_WORKER_PROFILE


@router.post("/profile/update", response_model=WorkerProfileSchema)
def update_worker_profile(data: UpdateProfileRequest):
    global MOCK_WORKER_PROFILE
    MOCK_WORKER_PROFILE.name = data.name
    MOCK_WORKER_PROFILE.phone = data.phone
    MOCK_WORKER_PROFILE.city = data.city
    MOCK_WORKER_PROFILE.panNumber = data.pan
    MOCK_WORKER_PROFILE.upiId = data.upi
    MOCK_WORKER_PROFILE.isOnboarded = True
    return MOCK_WORKER_PROFILE


@router.get("/consents", response_model=list[ConsentItemSchema])
def get_consents():
    return list(MOCK_CONSENTS.values())


@router.post("/consent/toggle")
def toggle_consent(data: ConsentToggleRequest):
    cid = data.consent_id
    if cid in MOCK_CONSENTS:
        curr = MOCK_CONSENTS[cid]
        MOCK_CONSENTS[cid] = ConsentItemSchema(
            id=curr.id,
            title=curr.title,
            subtitle=curr.subtitle,
            description=curr.description,
            category=curr.category,
            dataPoints=curr.dataPoints,
            isGranted=not curr.isGranted,
            isMandatory=curr.isMandatory,
            lastUpdated=datetime.now(),
        )

        state_str = "granted" if MOCK_CONSENTS[cid].isGranted else "revoked"
        MOCK_NOTIFICATIONS.insert(
            0,
            NotificationSchema(
                id=f"n_{len(MOCK_NOTIFICATIONS)+1}",
                title="Consent Updated",
                message=f"Privacy setting '{curr.title}' was {state_str}.",
                timestamp=datetime.now(),
                isRead=False,
                type="consent",
            ),
        )
        return {"status": "success", "is_granted": MOCK_CONSENTS[cid].isGranted}
    raise HTTPException(status_code=404, detail="Consent ID not found")


@router.post("/platform/toggle")
def toggle_platform(data: PlatformToggleRequest):
    pid = data.platform_id
    for platform in MOCK_WORKER_PROFILE.platforms:
        if platform.id == pid:
            platform.isConnected = not platform.isConnected
            return {"status": "success", "is_connected": platform.isConnected}
    raise HTTPException(status_code=404, detail="Platform ID not found")


@router.get("/score", response_model=GigCreditScoreSchema)
def get_credit_score():
    return _calculate_score_internal()


@router.post("/loans/apply", response_model=LoanApplicationSchema)
def apply_loan(data: ApplyLoanRequest):
    app_id = f"app_{random.randint(1000, 9999)}"
    ref_id = f"GC-LOAN-{random.randint(1000, 9999)}"

    new_app = LoanApplicationSchema(
        id=app_id,
        referenceId=ref_id,
        requestedAmount=data.amount,
        tenureMonths=data.tenureMonths,
        interestRateMonthly=data.interestRateMonthly,
        calculatedEmi=data.emi,
        status="submitted",
        purpose=data.purpose,
        appliedAt=datetime.now(),
        lenderName="GigCredit NBFC Engine",
    )
    MOCK_LOANS.insert(0, new_app)

    MOCK_NOTIFICATIONS.insert(
        0,
        NotificationSchema(
            id=f"n_{len(MOCK_NOTIFICATIONS)+1}",
            title="Loan Application Submitted 🚀",
            message=f"Request #{ref_id} for ₹{data.amount:.0f} sent to AI risk model.",
            timestamp=datetime.now(),
            isRead=False,
            type="loan",
        ),
    )

    return new_app


@router.get("/loans", response_model=list[LoanApplicationSchema])
def get_loans():
    return MOCK_LOANS


@router.get("/notifications", response_model=list[NotificationSchema])
def get_notifications():
    return MOCK_NOTIFICATIONS
