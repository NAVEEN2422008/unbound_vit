"""
Pydantic schemas for the Customer-Facing Financial Resilience Dashboard.
Translates complex banking algorithms into plain-language, non-jargon metrics,
actionable recommendations with transparent "WHY" and "HOW CONFIDENT" backing,
and DPDP-compliant granular consent controls.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class DistressRiskLevel(str, Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"


class PlainLanguageRecommendation(BaseModel):
    id: str
    action_text: str                   # E.g. "Your receivables of ₹12L may reduce the need for additional borrowing."
    category: str                      # RECEIVABLES, LOAN_DECISION, CASH_RESERVES, ASSET_FIX, DEMAND
    why_explanation: str               # Plain-language non-jargon explanation of WHY
    confidence_level: str              # HIGH (95%), MODERATE (80%), ESTIMATED (65%)
    confidence_percentage: float = Field(ge=0.0, le=100.0)
    supporting_facts: List[str]        # Concrete numbers backing the statement
    priority: int = 1


class UpcomingObligation(BaseModel):
    title: str
    amount: float
    due_in_days: int
    due_date_formatted: str
    is_loan_emi: bool
    type_badge: str                    # "Loan EMI", "Payroll", "Factory Rent", "Electricity", "Taxes"


class AssetProfitabilitySummary(BaseModel):
    asset_name: str
    status_label: str                  # "Highly Profitable", "Making a Loss", "Break-Even"
    monthly_net_earnings: float        # Positive or negative
    utilization_percentage: float
    plain_tip: str                     # Plain actionable tip


class ClusterSeasonalBenchmark(BaseModel):
    region_cluster: str
    industry_label: str
    current_month_name: str
    business_revenue_vs_normal_pct: float  # E.g. -18% below normal
    is_normal_seasonal_dip: bool
    plain_explanation: str


class CustomerConsentState(BaseModel):
    financial_data_sharing: bool = True
    business_matching: bool = True
    personalized_recommendations: bool = True
    last_updated: str = "2026-09-04"
    dpdp_compliance_notice: str = "Protected under Digital Personal Data Protection (DPDP) Act 2023. You can revoke anytime."


class CustomerResilienceDashboardData(BaseModel):
    customer_id: str
    customer_name: str
    business_type: str
    cluster_region: str
    
    # 1. Resilience & Risk Dials
    financial_resilience_score: int = Field(ge=0, le=100) # e.g. 74/100
    distress_risk_level: DistressRiskLevel
    health_status_headline: str        # E.g. "Action Needed: Upcoming Payment Collision"
    
    # 2. Plain Numbers Summary (Cash, Income, Expenses, Buffers)
    cash_available_today: float
    expected_monthly_income: float
    expected_monthly_expenses: float
    upcoming_monthly_loan_emi: float
    total_upcoming_obligations: float
    savings_safety_buffer_days: int    # E.g. 19 days
    receivables_pending: float         # Money owed to you
    payables_due: float                # Bills you owe suppliers
    
    # 3. Simple Highlights / Warnings
    next_major_cash_requirement_headline: str # E.g. "Your next major cash requirement is in 6 days (₹3.2L for Wages & EMI)."
    
    # 4. Seasonal & Industry Context
    seasonal_context: ClusterSeasonalBenchmark
    
    # 5. Loan Affordability Verdict
    loan_affordability_verdict: str    # "NOT RECOMMENDED" or "SAFE TO BORROW"
    loan_affordability_plain_reason: str
    
    # 6. Asset Profitability Cards
    assets: List[AssetProfitabilitySummary]
    
    # 7. Upcoming Calendar Obligations (Next 30 Days)
    upcoming_obligations: List[UpcomingObligation]
    
    # 8. Plain Actionable Recommendations (With WHY? and HOW CONFIDENT?)
    recommendations: List[PlainLanguageRecommendation]
    
    # 9. Granular Consent Controls
    consent: CustomerConsentState

    model_config = ConfigDict(from_attributes=True)


class UpdateConsentRequest(BaseModel):
    financial_data_sharing: Optional[bool] = None
    business_matching: Optional[bool] = None
    personalized_recommendations: Optional[bool] = None
