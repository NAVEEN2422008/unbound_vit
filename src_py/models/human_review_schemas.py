"""
Pydantic v2 schemas for the Banker Human Review & Escalation Interface.
Allows a qualified banker to review uncertain or high-impact recommendations.

Automatic Escalation Triggers:
- confidence is low
- large credit request
- asset sale recommendation
- conflicting model outputs
- insufficient data
- unusual business conditions

Review Screen Displays:
- Customer
- Financial Reality
- Distress
- Confidence
- Root Cause
- Context
- Assets
- Receivables
- Credit Affordability
- Decision Twin
- Recommended Intervention

Actions:
- APPROVE
- REJECT
- MODIFY
- REQUEST_MORE_DATA
- ESCALATE

Audit Storage:
- review_id, customer_id, reviewer_id, decision, reason, notes, timestamp
Strict Principle:
- Human decisions must be added to audit history.
- Never silently overwrite model decisions.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class HumanReviewAction(str, Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    MODIFY = "MODIFY"
    REQUEST_MORE_DATA = "REQUEST_MORE_DATA"
    ESCALATE = "ESCALATE"


class EscalationReason(str, Enum):
    LOW_CONFIDENCE = "LOW_CONFIDENCE"
    LARGE_CREDIT_REQUEST = "LARGE_CREDIT_REQUEST"
    ASSET_SALE_RECOMMENDED = "ASSET_SALE_RECOMMENDED"
    CONFLICTING_MODEL_OUTPUTS = "CONFLICTING_MODEL_OUTPUTS"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNUSUAL_BUSINESS_CONDITIONS = "UNUSUAL_BUSINESS_CONDITIONS"


class EscalationStatus(BaseModel):
    is_escalated: bool
    triggers: List[EscalationReason]
    escalation_notes: str


class BankerReviewScreenData(BaseModel):
    """
    Comprehensive aggregated review screen presenting all 11 analytical layers.
    """
    review_case_id: str
    customer: Dict[str, Any]
    financial_reality: Dict[str, Any]
    distress: Dict[str, Any]
    confidence: Dict[str, Any]
    root_cause: Dict[str, Any]
    context: Dict[str, Any]
    assets: List[Dict[str, Any]]
    receivables: Dict[str, Any]
    credit_affordability: Dict[str, Any]
    decision_twin: Dict[str, Any]
    recommended_intervention: Dict[str, Any]
    escalation_status: EscalationStatus
    allowed_actions: List[HumanReviewAction] = [
        HumanReviewAction.APPROVE,
        HumanReviewAction.REJECT,
        HumanReviewAction.MODIFY,
        HumanReviewAction.REQUEST_MORE_DATA,
        HumanReviewAction.ESCALATE
    ]

    model_config = ConfigDict(from_attributes=True)


class SubmitHumanReviewRequest(BaseModel):
    decision: HumanReviewAction
    reason: str = Field(..., min_length=3, description="Formal justification for the supervisory decision")
    notes: Optional[str] = ""
    modified_parameters: Optional[Dict[str, Any]] = None


class StoredHumanReviewRecord(BaseModel):
    review_id: str
    customer_id: str
    reviewer_id: str
    decision: HumanReviewAction
    reason: str
    notes: Optional[str] = ""
    modified_parameters: Optional[Dict[str, Any]] = None
    original_model_recommendation: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audit_hash: str
    regulatory_framework: str = "RBI Stressed MSME Resolution & Supervisory Oversight"

    model_config = ConfigDict(from_attributes=True)
