"""
Pydantic v2 schemas for Peer Benchmarking Engine.
Compares a business with a statistically matched peer group across 8 core financial metrics:
- revenue growth
- expense growth
- profit margin
- cash buffer
- debt burden
- receivable ageing
- payable pressure
- asset utilization
Enforces strict DPDP privacy (aggregated peer statistics only, no individual identifiers)
and minimum peer sample size rules (INSUFFICIENT_PEER_DATA).
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BenchmarkMetricStatus(str, Enum):
    BETTER = "BETTER"
    NORMAL = "NORMAL"
    WORSE = "WORSE"


class MetricComparisonItem(BaseModel):
    metric: str
    customer_value: float
    unit: str  # "%", "days", "ratio"
    peer_median: float
    peer_range: str  # e.g., "P25–P75: 12.0% to 24.0%"
    customer_percentile: float = Field(ge=0.0, le=100.0)
    status: BenchmarkMetricStatus
    interpretive_note: str


class PeerSelectionCriteria(BaseModel):
    industry: str
    region: str
    business_size: str
    revenue_range: str
    business_model: str
    asset_type: Optional[str] = None


class PeerBenchmarkReport(BaseModel):
    """
    Standard output of Peer Benchmarking Engine.
    Exposes customer comparison against matched cohort across 8 metrics,
    sample sizes, status, and DPDP privacy protections.
    """
    customer_id: str
    customer_name: str
    peer_selection: PeerSelectionCriteria
    peer_sample_size: int
    is_sufficient_peer_data: bool
    status: str = "BENCHMARK_COMPLETED"  # or "INSUFFICIENT_PEER_DATA"
    metrics_comparison: List[MetricComparisonItem] = []
    better_count: int = 0
    normal_count: int = 0
    worse_count: int = 0
    overall_cohort_ranking_percentile: float = Field(ge=0.0, le=100.0)
    
    privacy_compliance_note: str = (
        "Complies with DPDP Act & Institutional Privacy: All peer statistics are aggregated medians "
        "and interquartile ranges. No individual peer identities, transactions, balances, or debts are exposed."
    )
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
