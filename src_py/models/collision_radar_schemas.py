"""
Pydantic v2 schemas for the Obligation Collision Radar module.
Enforces severity levels (GREEN, YELLOW, ORANGE, RED), mathematical shortfall calculations,
and prioritized sorting by severity, shortfall amount, and days until event.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class CollisionSeverity(str, Enum):
    GREEN = "GREEN"    # Healthy liquidity buffer (> minimum buffer)
    YELLOW = "YELLOW"  # Low buffer (between 0 and minimum buffer)
    ORANGE = "ORANGE"  # Projected shortage (shortfall > 0 up to threshold)
    RED = "RED"        # Severe shortage (shortfall exceeds 2x daily burn or significant deficit)


class ObligationDueItem(BaseModel):
    id: str
    obligation_type: str  # EMI, RENT, PAYROLL, SUPPLIER, TAX, INSURANCE, LOAN_MATURITY, UTILITY, OTHER
    title: str
    counterparty: Optional[str] = None
    amount: float
    is_mandatory: bool = True
    penalty_on_default: Optional[str] = None


class ObligationCollisionEvent(BaseModel):
    """
    Individual collision event where obligations intersect with cash availability.
    """
    date: date
    days_until_event: int
    obligation_total: float
    expected_cash: float
    projected_balance: float
    shortfall: float = 0.0
    severity: CollisionSeverity
    priority_score: float = Field(..., description="Computed sorting weight: severity + shortfall + days urgency")
    contributing_obligations: List[ObligationDueItem] = []

    model_config = ConfigDict(from_attributes=True)


class ObligationCalendarReport(BaseModel):
    """
    Complete report containing prioritized collisions and full obligation calendar.
    """
    customer_id: str
    customer_name: str
    archetype: str
    as_of_date: date
    horizon_days: int = 30
    total_obligations_tracked: float
    total_shortfall_volume: float
    critical_collision_count: int
    first_severe_shortfall_date: Optional[date] = None
    prioritized_collisions: List[ObligationCollisionEvent]
    calendar_events: List[ObligationCollisionEvent]
    radar_summary: str
