"""
Pydantic v2 schemas for the Immutable Audit Trail & Provenance Ledger.
Maintains an immutable history of system recommendations and human actions.

Audit Events:
- DATA_INGESTED
- DISTRESS_DETECTED
- ROOT_CAUSE_IDENTIFIED
- LOAN_EVALUATED
- INTERVENTION_RECOMMENDED
- HUMAN_REVIEWED
- INTERVENTION_APPROVED
- INTERVENTION_EXECUTED
- OUTCOME_RECORDED

Store Attributes:
- audit_id
- customer_id
- event_type
- module
- timestamp
- input_reference
- model_version
- rule_version
- output
- confidence
- human_decision
- cryptographic_hash
- prev_audit_hash (tamper-evident hash chaining)

Requirement:
Historical events must never be deleted or modified through normal application operations.
"""
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AuditEventType(str, Enum):
    DATA_INGESTED = "DATA_INGESTED"
    DISTRESS_DETECTED = "DISTRESS_DETECTED"
    ROOT_CAUSE_IDENTIFIED = "ROOT_CAUSE_IDENTIFIED"
    LOAN_EVALUATED = "LOAN_EVALUATED"
    INTERVENTION_RECOMMENDED = "INTERVENTION_RECOMMENDED"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    INTERVENTION_APPROVED = "INTERVENTION_APPROVED"
    INTERVENTION_EXECUTED = "INTERVENTION_EXECUTED"
    OUTCOME_RECORDED = "OUTCOME_RECORDED"


class ImmutableAuditEventRecord(BaseModel):
    audit_id: str
    customer_id: str
    event_type: AuditEventType
    module: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    input_reference: str
    model_version: str
    rule_version: str
    output: Dict[str, Any]
    confidence: Optional[float] = None
    human_decision: Optional[str] = None
    cryptographic_hash: str
    prev_audit_hash: str
    regulatory_mandate: str = "RBI Digital Provenance & DPDP Act 2023 Non-Repudiation Framework"

    model_config = ConfigDict(from_attributes=True)


class CreateAuditEventRequest(BaseModel):
    customer_id: str
    event_type: AuditEventType
    module: str
    input_reference: str
    model_version: Optional[str] = "v2.4.0-production"
    rule_version: Optional[str] = "rbi-prudential-2026.1"
    output: Dict[str, Any]
    confidence: Optional[float] = None
    human_decision: Optional[str] = None
