"""
Pydantic v2 schemas for the Root-Cause Analyzer (WHY) Engine.
Enforces careful epistemic phrasing ("likely contributor", "primary contributing factor"
rather than "proven cause" unless deterministically confirmed),
empirical evidence itemization, percentage contribution weighting, and ranking across 13 candidate causes.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CandidateCauseEnum(str, Enum):
    REVENUE_DECLINE = "revenue decline"
    CUSTOMER_ORDER_DECLINE = "customer/order decline"
    SEASONALITY = "seasonality"
    INDUSTRY_DOWNTURN = "industry downturn"
    REGIONAL_DOWNTURN = "regional downturn"
    RECEIVABLE_DELAY = "receivable delay"
    EXPENSE_INCREASE = "expense increase"
    DEBT_OVERLOAD = "debt overload"
    HIGH_EMI = "high EMI"
    ASSET_UNDERPERFORMANCE = "asset underperformance"
    LOW_ASSET_UTILIZATION = "low asset utilization"
    SUPPLIER_COST_INCREASE = "supplier cost increase"
    INVENTORY_PRESSURE = "inventory pressure"


class CauseEvidenceRecord(BaseModel):
    metric: str
    observed: str
    benchmark_or_peer: Optional[str] = None
    finding: str


class ContributingCauseItem(BaseModel):
    cause: CandidateCauseEnum
    causality_classification: str = Field(
        default="likely contributor",
        description="Phrased as 'likely contributor' or 'contributing factor' to avoid confusing correlation with proven causation"
    )
    estimated_contribution_pct: float = Field(ge=0.0, le=100.0, description="Estimated percentage contribution to distress")
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: List[CauseEvidenceRecord]
    narrative_rationale: str


class RootCauseReport(BaseModel):
    """
    Standard output of Root-Cause Analyzer (WHY) Engine.
    Exposes ranked primary and secondary causes, empirical evidence, contribution scores,
    and confidence ratings.
    """
    customer_id: str
    customer_name: str
    archetype: str
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    primary_cause: ContributingCauseItem
    secondary_causes: List[ContributingCauseItem] = []
    total_causes_evaluated: int = 13
    causation_confidence_level: float = Field(ge=0.0, le=1.0)
    epistemic_disclaimer: str = (
        "Statistical findings represent likely contributors based on multi-source diagnostic telemetry; "
        "they are not asserted as absolute proven causation."
    )
    human_summary: str

    model_config = ConfigDict(from_attributes=True)
