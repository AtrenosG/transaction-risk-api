from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID
from enum import Enum


class TransactionType(str, Enum):
    CREDIT = "credit"
    DEBIT = "debit"


class RiskCategory(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SpendingStability(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class User(BaseModel):
    id: Optional[UUID] = None
    name: str
    account_no: str
    ifsc_code: str


class Transaction(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    date: datetime
    description: str
    amount: float
    type: TransactionType
    category: str
    upi_app: Optional[str] = Field(None, alias="UPI_App")


class FinancialSummary(BaseModel):
    monthly_spendings: Dict[str, float]
    monthly_savings: Dict[str, float]
    total_savings: float
    income_volatility: float
    spending_volatility: float
    consistency_score: float
    transaction_frequency: int


class BehavioralPatterns(BaseModel):
    essential_spending_ratio: float
    high_risk_spending_ratio: float
    weekend_spending_ratio: float


class BehavioralAnalysis(BaseModel):
    spending_pattern_distribution: Dict[str, float]
    income_and_spending_analysis: Dict[str, Any]
    spending_stability: SpendingStability
    behavioral_patterns: BehavioralPatterns


class RiskAssessmentDetails(BaseModel):
    risk_essential_spending: float
    high_risk_spending: float
    weekend_spending: float
    loan_eligibility_factors: List[str]


class MLAnalysisResult(BaseModel):
    overall_risk_score: float
    risk_category: RiskCategory
    loan_eligibility: bool
    eligibility_reason: str
    financial_summary: FinancialSummary
    behavioral_analysis: BehavioralAnalysis
    risk_assessment_details: RiskAssessmentDetails
    created_at: Optional[datetime] = None


class MLResult(BaseModel):
    id: Optional[UUID] = None
    user_id: UUID
    risk_score: float
    risk_category: RiskCategory
    eligible: bool
    eligibility_reason: str
    metrics: Dict[str, Any]
    created_at: Optional[datetime] = None


class AnalyzeRequest(BaseModel):
    account_no: str
    ifsc_code: str


class WebhookPayload(BaseModel):
    user_id: UUID
    analysis_result: MLAnalysisResult
    timestamp: datetime


class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
