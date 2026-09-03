"""
Pydantic v2 schemas for Intervention Solvency Outcome Verification.
Determines whether the chosen intervention actually improved the customer's financial health.

BEFORE metrics:
- distress_score
- resilience_score
- cashflow
- cash_buffer
- debt
- EMI
- missed_payments

AFTER metrics:
- Same metrics captured post-intervention.

COMPARE:
- distress_change (after - before)
- resilience_change (after - before)
- cashflow_change (after - before)
- debt_change (after - before)
- repayment_change (missed_payments_change: after - before)

CLASSIFICATION:
- SUCCESS
- PARTIAL_SUCCESS
- NO_EFFECT
- NEGATIVE_OUTCOME

API:
- GET /api/v1/interventions/{id}/outcome
- POST /api/v1/interventions/{id}/outcome
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class OutcomeClassification(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    NO_EFFECT = "NO_EFFECT"
    NEGATIVE_OUTCOME = "NEGATIVE_OUTCOME"


class SolvencyMetricsSnapshot(BaseModel):
    distress_score: float = Field(ge=0.0, le=100.0, description="Distress index (lower is healthier)")
    resilience_score: float = Field(ge=0.0, le=100.0, description="Resilience index (higher is healthier)")
    cashflow: float = Field(description="Net monthly operating cash flow in INR")
    cash_buffer: float = Field(ge=0.0, description="Cash buffer days")
    debt: float = Field(ge=0.0, description="Total outstanding debt principal in INR")
    EMI: float = Field(ge=0.0, description="Monthly aggregate debt servicing obligation in INR")
    missed_payments: int = Field(ge=0, description="Count of missed payments or DPD > 0")


class MetricsComparisonDelta(BaseModel):
    distress_change: float = Field(description="after.distress_score - before.distress_score (negative is good)")
    resilience_change: float = Field(description="after.resilience_score - before.resilience_score (positive is good)")
    cashflow_change: float = Field(description="after.cashflow - before.cashflow (positive is good)")
    debt_change: float = Field(description="after.debt - before.debt (negative is good)")
    repayment_change: int = Field(description="after.missed_payments - before.missed_payments (negative is good)")


class RecordInterventionOutcomeRequest(BaseModel):
    customer_id: str
    intervention_name: str
    evaluation_month: Optional[int] = Field(default=3, description="Evaluation horizon in months (e.g. 1, 3, 6, 12)")
    before: SolvencyMetricsSnapshot
    after: SolvencyMetricsSnapshot
    causal_attribution_evidence: Optional[str] = "associated improvement"
    evaluator_notes: Optional[str] = ""


class InterventionOutcomeReport(BaseModel):
    intervention_id: str
    customer_id: str
    intervention_name: str
    evaluation_month: int
    before: SolvencyMetricsSnapshot
    after: SolvencyMetricsSnapshot
    compare: MetricsComparisonDelta
    classification: OutcomeClassification
    attribution_statement: str
    evaluation_timestamp: datetime = Field(default_factory=datetime.utcnow)
    evaluator_notes: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True)
