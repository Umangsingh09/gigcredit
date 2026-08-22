from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class GigPlatformSchema(BaseModel):
    id: str
    name: str
    logo: str
    monthlyEarnings: float
    rating: float
    tripsCompleted: int
    isConnected: bool
    workType: str

class WorkerProfileSchema(BaseModel):
    id: str
    name: str
    phone: str
    city: str
    panNumber: str
    upiId: str
    totalMonthsExperience: int
    avgDailyHours: float
    isOnboarded: bool
    platforms: List[GigPlatformSchema]

class UpdateProfileRequest(BaseModel):
    name: str
    phone: str
    city: str
    pan: str
    upi: str

class ConsentItemSchema(BaseModel):
    id: str
    title: str
    subtitle: str
    description: str
    category: str
    dataPoints: str
    isGranted: bool
    isMandatory: bool
    lastUpdated: datetime

class ConsentToggleRequest(BaseModel):
    consent_id: str

class PlatformToggleRequest(BaseModel):
    platform_id: str

class ScoreFactorSchema(BaseModel):
    title: str
    description: str
    impact: str
    isPositive: bool
    iconType: str

class GigCreditScoreSchema(BaseModel):
    score: int
    riskCategory: str
    incomeStabilityScore: float
    workConsistencyScore: float
    debtBurdenRatio: float
    maxRecommendedLoan: float
    factors: List[ScoreFactorSchema]
    calculatedAt: datetime

class ApplyLoanRequest(BaseModel):
    amount: float
    tenureMonths: int
    interestRateMonthly: float
    emi: float
    purpose: str

class LoanApplicationSchema(BaseModel):
    id: str
    referenceId: Optional[str] = None
    requestedAmount: float
    tenureMonths: int
    interestRateMonthly: float
    calculatedEmi: float
    status: str
    purpose: str
    appliedAt: datetime
    lenderName: Optional[str] = None

class NotificationSchema(BaseModel):
    id: str
    title: str
    message: str
    timestamp: datetime
    isRead: bool
    type: str
