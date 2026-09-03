"""
Pydantic v2 schemas for Context-Aware Distress Intelligence Engine.
Evaluates customer trajectory against:
- normal seasonal behavior
- industry-wide deterioration
- regional deterioration
- peer-group deterioration
- customer-specific abnormal deterioration
Enforces strict DPDP privacy (aggregated metrics only; no peer IDs, balances, or debt exposed)
and minimum sample size thresholds (INSUFFICIENT_PEER_DATA).
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ContextClassificationEnum(str, Enum):
    NORMAL_SEASONAL = "NORMAL_SEASONAL"
    INDUSTRY_WIDE = "INDUSTRY_WIDE"
    REGION_WIDE = "REGION_WIDE"
    CUSTOMER_SPECIFIC = "CUSTOMER_SPECIFIC"
    MIXED = "MIXED"
    INSUFFICIENT_PEER_DATA = "INSUFFICIENT_PEER_DATA"


class AggregatedCohortBenchmark(BaseModel):
    cohort_name: str
    sample_size: int = Field(..., description="Number of anonymized peer enterprises aggregated")
    median_growth_pct: float
    interquartile_range_pct: float
    is_statistically_significant: bool


class ContextIntelligenceReport(BaseModel):
    """
    Standard output of Context-Aware Distress Intelligence Engine.
    Exposes classification, abnormality score, multi-layer deviations, aggregated peer metrics,
    and plain-English supervisory explanations.
    """
    customer_id: str
    customer_growth_pct: float
    classification: ContextClassificationEnum
    abnormality_score: float = Field(ge=0.0, le=100.0, description="Degree of idiosyncratic customer deviation from context")
    customer_vs_industry_deviation: float
    customer_vs_region_deviation: float
    customer_vs_peer_deviation: float
    customer_vs_seasonal_baseline: float
    
    # Aggregated contextual benchmarks (strictly privacy-preserving)
    industry_benchmark: AggregatedCohortBenchmark
    regional_benchmark: AggregatedCohortBenchmark
    peer_cohort_benchmark: AggregatedCohortBenchmark
    seasonal_baseline_pct: float
    
    peer_sample_size: int
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    privacy_compliance_note: str = (
        "Complies with DPDP Act & Institutional Privacy: All peer metrics are anonymized medians. "
        "No individual enterprise balances, transactions, debt, or identities are exposed."
    )
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
