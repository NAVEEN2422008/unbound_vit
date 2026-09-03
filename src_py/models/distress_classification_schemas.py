"""
Pydantic v2 schemas for Distress Classification Engine.
Classifies the dominant distress type into:
- TEMPORARY_LIQUIDITY_GAP
- INCOME_SHOCK
- DEBT_OVERLOAD
- EXPENSE_SHOCK
- MIXED_DISTRESS
Provides primary_category, secondary_category, confidence, evidence (>= 2 items), and expected_duration.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DistressDominantType(str, Enum):
    TEMPORARY_LIQUIDITY_GAP = "TEMPORARY_LIQUIDITY_GAP"
    INCOME_SHOCK = "INCOME_SHOCK"
    DEBT_OVERLOAD = "DEBT_OVERLOAD"
    EXPENSE_SHOCK = "EXPENSE_SHOCK"
    MIXED_DISTRESS = "MIXED_DISTRESS"


class ClassificationEvidenceItem(BaseModel):
    metric_name: str
    observed_value: Any
    benchmark_or_threshold: str
    significance: str  # HIGH, MEDIUM, CRITICAL
    description: str


class DistressClassificationReport(BaseModel):
    """
    Standard output of Distress Classification Engine.
    Exposes primary, secondary categories, confidence score, duration estimate,
    and a strictly validated list of at least 2 evidence items.
    """
    customer_id: str
    primary_category: DistressDominantType
    secondary_category: Optional[DistressDominantType] = None
    confidence: float = Field(ge=0.0, le=1.0, description="Epistemic confidence in dominant classification")
    evidence: List[ClassificationEvidenceItem] = Field(..., min_length=2, description="At least two empirical evidence items required")
    expected_duration: str  # e.g., "14-30 days", "3-6 months", "Structural / Indefinite (>6 months)"
    classification_summary: str
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
