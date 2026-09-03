"""
Pydantic v2 schemas for the Non-Debt Business Recovery Engine.
Identifies operational, commercial, and structural non-debt levers to improve the customer's financial condition.
Core Philosophy:
Ask: "Can the business problem be fixed without increasing debt?"
Before: "How much more can we lend?"

Recovery Levers:
- additional_customers
- receivable_collection
- asset_utilization
- cost_reduction
- supplier_negotiation
- product_mix
- seasonal_planning
- business_matching
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class NonDebtRecoveryLeverType(str, Enum):
    ADDITIONAL_CUSTOMERS = "ADDITIONAL_CUSTOMERS"
    RECEIVABLE_COLLECTION = "RECEIVABLE_COLLECTION"
    ASSET_UTILIZATION = "ASSET_UTILIZATION"
    COST_REDUCTION = "COST_REDUCTION"
    SUPPLIER_NEGOTIATION = "SUPPLIER_NEGOTIATION"
    PRODUCT_MIX = "PRODUCT_MIX"
    SEASONAL_PLANNING = "SEASONAL_PLANNING"
    BUSINESS_MATCHING = "BUSINESS_MATCHING"


class RecoveryOpportunityItem(BaseModel):
    """
    Detailed non-debt recovery opportunity card.
    Contains: type, estimated_impact, time_to_benefit, risk, confidence, evidence.
    """
    type: NonDebtRecoveryLeverType
    title: str
    description: str
    estimated_impact: str                      # e.g., "+₹1,80,000/mo margin" or "₹12,00,000 immediate liquidity"
    estimated_monthly_cash_benefit: float      # Standardized in INR
    time_to_benefit: str                       # e.g., "7 to 14 days", "30 days", "60 to 90 days"
    time_to_benefit_days: int
    risk: str                                  # "LOW", "MODERATE", "HIGH"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[str]
    implementation_steps: List[str]
    is_non_debt: bool = True


class NonDebtBusinessRecoveryReport(BaseModel):
    customer_id: str
    customer_name: str
    industry: str
    region: str
    core_epistemic_inquiry: str = (
        "MANDATORY INQUIRY: 'Can the business problem be fixed without increasing debt?' "
        "Evaluated BEFORE: 'How much more can we lend?'"
    )
    total_potential_monthly_impact: float
    total_immediate_liquidity_unlock: float
    recovery_opportunities: List[RecoveryOpportunityItem]
    debt_avoidance_verdict: str
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
