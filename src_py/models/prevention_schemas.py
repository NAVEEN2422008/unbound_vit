"""
Pydantic v2 schemas for Longitudinal Distress Prevention & Efficacy Measurement.
Measures whether the system actually prevented financial distress over:
- BASELINE
- 6 MONTHS
- 12 MONTHS

KPIs tracked:
- missed payments
- default occurrence
- repayment stability
- interest burden
- debt reduction
- cashflow stability
- savings growth
- financial resilience

Output structure:
- before_after_analysis
- trend
- intervention_effectiveness

Specification Example:
Distress: 81 -> 47 -> 31
Resilience: 42 -> 62 -> 75

Important Rule:
Do not claim causality unless experimental evidence exists.
Use: "associated improvement" when causal attribution is not established.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class LongitudinalHorizon(str, Enum):
    BASELINE = "BASELINE"
    SIX_MONTHS = "6_MONTHS"
    TWELVE_MONTHS = "12_MONTHS"


class HorizonKPISnapshot(BaseModel):
    horizon: LongitudinalHorizon
    month_offset: int
    distress_score: float = Field(ge=0.0, le=100.0)
    financial_resilience: float = Field(ge=0.0, le=100.0)
    missed_payments: int = Field(ge=0, description="Cumulative count of missed payments/mandates")
    default_occurrence: bool = Field(description="Whether a 90+ DPD default or NPA occurred")
    repayment_stability_score: float = Field(ge=0.0, le=100.0, description="Ratio of on-time debt service repayments")
    interest_burden_monthly: float = Field(ge=0.0, description="Monthly interest component in INR")
    total_debt: float = Field(ge=0.0, description="Aggregate outstanding debt in INR")
    debt_reduction_cumulative: float = Field(description="Cumulative reduction in debt principal since baseline")
    cashflow_stability_index: float = Field(ge=0.0, le=100.0, description="Consistency score of operational cashflow")
    savings_balance: float = Field(ge=0.0, description="Accumulated reserve/savings balance in INR")
    savings_growth_pct: float = Field(description="Percentage growth in savings compared to baseline")


class MetricTrendProgression(BaseModel):
    metric_name: str
    baseline_value: float
    six_month_value: float
    twelve_month_value: float
    net_12m_change: float
    trend_direction: str  # IMPROVING, STABLE, DETERIORATING
    trajectory_display: str  # e.g., "81 -> 47 -> 31"


class BeforeAfterAnalysis(BaseModel):
    baseline_summary: HorizonKPISnapshot
    twelve_month_summary: HorizonKPISnapshot
    distress_trajectory: str = "81 -> 47 -> 31"
    resilience_trajectory: str = "42 -> 62 -> 75"
    default_prevented: bool = True
    total_debt_reduced: float
    interest_burden_lowered_pct: float
    savings_growth_pct: float


class InterventionEffectivenessSummary(BaseModel):
    effectiveness_rating: str  # HIGHLY_EFFECTIVE, MODERATELY_EFFECTIVE, INEFFECTIVE
    prevented_default_count: int
    associated_improvement_narrative: str
    causal_attribution_disclaimer: str = (
        "IMPORTANT: Do not claim causality unless experimental evidence exists. "
        "Observed outcomes represent an 'associated improvement' occurring alongside early intervention."
    )


class LongitudinalPreventionReport(BaseModel):
    report_id: str
    customer_id: str
    customer_name: str
    evaluation_periods: List[HorizonKPISnapshot]
    before_after_analysis: BeforeAfterAnalysis
    trend: List[MetricTrendProgression]
    intervention_effectiveness: InterventionEffectivenessSummary
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
