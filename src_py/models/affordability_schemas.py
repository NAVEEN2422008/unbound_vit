"""
Pydantic v2 schemas for the Credit Affordability Engine.
Answers the foundational question: "Can the customer repay safely?" (not merely "Can they qualify?").
Calculates pre-loan baseline vs post-loan projected metrics:
- debt, emi, free_cash_flow, debt_service_ratio, cash_buffer, resilience
Classifies affordability into:
- SAFE_TO_BORROW
- LIMITED_BORROWING
- NOT_SAFE_TO_BORROW
Outputs:
- maximum_recommended_amount
- safe_loan_range
- expected_emi
- affordability_status
- reason
- confidence
Integrates forward projected cash flows, seasonal forecasts, and receivable collections.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AffordabilityClassification(str, Enum):
    SAFE_TO_BORROW = "SAFE_TO_BORROW"          # Post-loan DSR <= 35%, FCF buffer comfortably positive, buffer days >= 21
    LIMITED_BORROWING = "LIMITED_BORROWING"    # Moderate leverage: Post-loan DSR 36-45%, reduced principal recommended
    NOT_SAFE_TO_BORROW = "NOT_SAFE_TO_BORROW"  # Post-loan DSR > 45%, negative FCF, cash buffer collapse imminent


class SafeLoanRange(BaseModel):
    minimum_viable_amount: float
    maximum_recommended_amount: float
    maximum_safe_monthly_emi: float
    recommended_tenure_months: int


class BaselineFinancialMetrics(BaseModel):
    current_debt: float
    current_emi: float
    current_free_cash_flow: float
    current_debt_service_ratio: float  # DSR %
    current_cash_buffer_days: int


class PostLoanProjectedMetrics(BaseModel):
    post_loan_debt: float
    post_loan_emi: float
    post_loan_free_cash_flow: float
    post_loan_debt_service_ratio: float  # DSR %
    post_loan_cash_buffer_days: int
    post_loan_resilience_score: float = Field(ge=0.0, le=100.0)


class ProposedLoanInput(BaseModel):
    customer_id: str
    proposed_principal: float = Field(gt=0.0, description="Requested loan amount")
    annual_interest_rate_pct: float = Field(default=12.0, ge=1.0, le=48.0)
    tenure_months: int = Field(default=24, ge=1, le=240)
    proposed_monthly_emi: Optional[float] = None
    expected_future_cash_flow: Optional[float] = None


class CreditAffordabilityReport(BaseModel):
    """
    Standard output of Credit Affordability Engine.
    Exposes baseline vs post-loan metrics, affordability verdict, maximum safe boundaries,
    and plain-language banking rationale.
    """
    customer_id: str
    proposed_principal: float
    expected_emi: float
    affordability_status: AffordabilityClassification
    maximum_recommended_amount: float
    safe_loan_range: SafeLoanRange
    baseline_metrics: BaselineFinancialMetrics
    post_loan_metrics: PostLoanProjectedMetrics
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    forward_projection_context: str
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class NoNewLoanVerdict(str, Enum):
    ALLOW = "ALLOW"
    LIMIT = "LIMIT"
    NOT_RECOMMENDED = "NOT_RECOMMENDED"


class NoNewLoanCheckReport(BaseModel):
    """
    Standard output of No-New-Loan Guardrail Engine.
    Evaluates 5 specific block triggers:
    1. Post-loan distress increases materially
    2. Post-loan free cash flow remains negative
    3. Post-loan EMI is not sustainable
    4. Loan does not address root cause
    5. Existing debt is already excessive
    Adheres to institutional safety mandate:
    "This is decision support. Do not implement automatic regulatory credit denial."
    """
    customer_id: str
    proposed_principal: float
    verdict: NoNewLoanVerdict
    reason: str
    evidence: List[str]
    confidence: float = Field(ge=0.0, le=1.0)
    decision_support_disclaimer: str = (
        "DECISION SUPPORT ADVISORY: This assessment provides human decision-support to prevent over-indebtedness. "
        "It does NOT constitute an automated regulatory credit denial."
    )
    current_distress_score: float
    projected_post_loan_distress_score: float
    current_free_cash_flow: float
    projected_post_loan_free_cash_flow: float
    current_debt_service_ratio: float
    projected_post_loan_debt_service_ratio: float
    root_cause_addressed: bool
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)

