"""
Pydantic v2 schemas for the Financial Resilience Score Engine.
Measures the customer's capacity to absorb financial shocks across 7 core dimensions:
1. Income stability
2. Cash-flow stability
3. Debt burden
4. Savings/cash buffer
5. Repayment behavior
6. Expense stability
7. Business health
Score range: 0–100.
Enforces institutional clarity: "This is NOT a regulatory credit score. Name clearly: Financial Resilience Score."
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ResilienceComponentScores(BaseModel):
    income_stability: float = Field(ge=0.0, le=100.0, description="Predictability and recurrence of primary revenue stream")
    cashflow_stability: float = Field(ge=0.0, le=100.0, description="Consistency of net cash flows avoiding negative dips")
    debt_burden: float = Field(ge=0.0, le=100.0, description="Manageability of monthly debt service / DSR")
    savings_cash_buffer: float = Field(ge=0.0, le=100.0, description="Available liquidity runway in days")
    repayment_behavior: float = Field(ge=0.0, le=100.0, description="Historical track record of on-time debt and vendor settlement")
    expense_stability: float = Field(ge=0.0, le=100.0, description="Control over operational cost spikes and fixed overhead")
    business_health: float = Field(ge=0.0, le=100.0, description="Receivable turnover, asset productivity, and commercial demand")


class FinancialResilienceReport(BaseModel):
    """
    Standard output of the Financial Resilience Engine.
    Score: 0–100.
    Output: overall_score, component_scores, trend, explanation, confidence.
    """
    customer_id: str
    customer_name: str
    overall_score: float = Field(ge=0.0, le=100.0, description="Financial Resilience Score (0–100)")
    component_scores: ResilienceComponentScores
    trend: str = Field(..., description="STABLE, IMPROVING, DETERIORATING")
    explanation: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Explicit Institutional Regulatory Demarcation
    metric_naming_notice: str = (
        "IMPORTANT NOTICE: This metric is the 'Financial Resilience Score'. "
        "It is NOT a regulatory or bureau credit score (such as CIBIL or Experian). "
        "It measures operational shock absorption capacity and cash-flow resilience."
    )
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
