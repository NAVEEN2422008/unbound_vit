"""
Pydantic v2 schemas for Financing Timing Engine.
Determines not only WHETHER credit is appropriate, but WHEN it is most appropriate.
Evaluates cyclical cash-flow trajectories, seasonal troughs vs peaks, receivable horizons,
and existing debt to decide whether delaying borrowing reduces long-term debt pressure.
Output Options:
- BORROW_NOW
- BORROW_LATER
- LIMITED_BORROWING
- AVOID_BORROWING
- RESTRUCTURE_EXISTING_DEBT
- USE_RECEIVABLE_FINANCING
Output:
- recommended_timing
- recommended_amount
- reason
- confidence
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class FinancingTimingOption(str, Enum):
    BORROW_NOW = "BORROW_NOW"
    BORROW_LATER = "BORROW_LATER"
    LIMITED_BORROWING = "LIMITED_BORROWING"
    AVOID_BORROWING = "AVOID_BORROWING"
    RESTRUCTURE_EXISTING_DEBT = "RESTRUCTURE_EXISTING_DEBT"
    USE_RECEIVABLE_FINANCING = "USE_RECEIVABLE_FINANCING"


class FinancingTimingReport(BaseModel):
    """
    Standard output of Financing Timing Engine.
    Exposes timing recommendation, optimal disbursement window, safe amount,
    and cyclical rationale.
    """
    business_id: str
    recommended_timing: FinancingTimingOption
    recommended_amount: float
    recommended_window_months: int = Field(default=0, description="Delay in months (0 = immediate, 2 = two months later)")
    optimal_timing_window: str = Field(..., description="E.g., 'Immediate', 'In 2 months (Post-Trough)', 'Next Quarter'")
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Contextual Telemetry
    current_season_status: str
    upcoming_recovery_month: Optional[str] = None
    expected_receivable_inflow_14d: float
    existing_debt_service_ratio: float
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
