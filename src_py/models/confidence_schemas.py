"""
Pydantic v2 schemas for the Prediction Reliability and Epistemic Confidence Engine.
Calculates how reliable a model's prediction or recommendation is.

Inputs:
- data completeness
- data freshness
- historical coverage
- peer sample size
- model confidence
- prediction stability
- actual/predicted/estimated proportions

Outputs:
- confidence_score (0.0 to 100.0)
- confidence_level: HIGH, MEDIUM, LOW
- human_review_required: bool (Rule: LOW confidence -> human review required)

Core Mandate:
Confidence MUST be independent from the actual risk score.
Example:
Distress: 90, Confidence: 45
means: "High estimated distress but low confidence."
NOT: "Customer definitely has high risk."
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ConfidenceLevel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ProvenanceProportions(BaseModel):
    actual_pct: float = Field(ge=0.0, le=100.0, description="Proportion of verified actual bank/tax data")
    user_entered_pct: float = Field(ge=0.0, le=100.0, description="Proportion of self-reported customer data")
    predicted_pct: float = Field(ge=0.0, le=100.0, description="Proportion of model predicted projections")
    estimated_pct: float = Field(ge=0.0, le=100.0, description="Proportion of heuristic/industry proxy estimates")


class ConfidenceDimensionScores(BaseModel):
    data_completeness_score: float = Field(ge=0.0, le=100.0)
    data_freshness_score: float = Field(ge=0.0, le=100.0)
    historical_coverage_score: float = Field(ge=0.0, le=100.0)
    peer_sample_size_score: float = Field(ge=0.0, le=100.0)
    model_confidence_score: float = Field(ge=0.0, le=100.0)
    prediction_stability_score: float = Field(ge=0.0, le=100.0)
    provenance_integrity_score: float = Field(ge=0.0, le=100.0)


class ConfidenceEvaluationReport(BaseModel):
    """
    Standard output of Prediction Reliability and Epistemic Confidence Engine.
    Exposes confidence_score, confidence_level, human_review_required, breakdown, and epistemic notice.
    """
    target_entity_id: str
    target_prediction_type: str        # e.g., "DISTRESS_SCORE", "RECOVERY_RECOMMENDATION", "SEASONAL_FORECAST"
    underlying_prediction_value: float # The actual prediction value (e.g., Distress 90.0)
    confidence_score: float = Field(ge=0.0, le=100.0)
    confidence_level: ConfidenceLevel
    human_review_required: bool        # Rule: LOW confidence -> True
    dimension_scores: ConfidenceDimensionScores
    provenance_proportions: ProvenanceProportions
    epistemic_interpretation: str
    independence_disclaimer: str = (
        "INDEPENDENCE PRINCIPLE ENFORCED: Model confidence is strictly independent from the underlying risk/distress score. "
        "A distress score of 90 with a confidence score of 45 indicates 'High estimated distress but low confidence'—NOT "
        "that the customer definitely has high risk. Human review is mandated for low confidence decisions."
    )
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class ConfidenceEvaluationRequest(BaseModel):
    target_entity_id: str
    target_prediction_type: Optional[str] = "DISTRESS_SCORE"
    underlying_prediction_value: Optional[float] = 50.0
    data_completeness_pct: Optional[float] = None
    data_freshness_days: Optional[int] = None
    historical_coverage_months: Optional[int] = None
    peer_sample_size: Optional[int] = None
    model_raw_confidence: Optional[float] = None
    prediction_variance_pct: Optional[float] = None
    actual_proportion_pct: Optional[float] = None
    user_entered_proportion_pct: Optional[float] = None
    estimated_proportion_pct: Optional[float] = None
