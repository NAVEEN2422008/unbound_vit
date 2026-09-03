"""
Pydantic v2 schemas for DPDP-Compliant Granular Consent Management.
Controls customer permission for financial analysis and business opportunity matching.

Consent Types:
- FINANCIAL_DATA_ACCESS
- TRANSACTION_ANALYSIS
- PERSONALIZED_RECOMMENDATIONS
- PEER_ANALYSIS
- BUSINESS_MATCHING
- COMMUNICATION

Stored Attributes:
- id (consent_id)
- customer_id
- consent_type
- purpose
- status (ACTIVE, REVOKED, EXPIRED, PENDING)
- timestamp
- expiry
- revoked_at

Business Matching Rule:
- Both parties must consent before direct introduction.

Data Access Rule:
- Only authorized services should access sensitive financial fields.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field, ConfigDict


class ConsentType(str, Enum):
    FINANCIAL_DATA_ACCESS = "FINANCIAL_DATA_ACCESS"
    TRANSACTION_ANALYSIS = "TRANSACTION_ANALYSIS"
    PERSONALIZED_RECOMMENDATIONS = "PERSONALIZED_RECOMMENDATIONS"
    PEER_ANALYSIS = "PEER_ANALYSIS"
    BUSINESS_MATCHING = "BUSINESS_MATCHING"
    COMMUNICATION = "COMMUNICATION"


class ConsentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    PENDING = "PENDING"


class CreateConsentRequest(BaseModel):
    customer_id: str
    consent_type: ConsentType
    purpose: str = Field(..., min_length=5, description="Explicit purpose for data processing under DPDP Act")
    validity_days: Optional[int] = Field(default=365, ge=1, le=1095)


class ConsentRecord(BaseModel):
    id: str
    customer_id: str
    consent_type: ConsentType
    purpose: str
    status: ConsentStatus = ConsentStatus.ACTIVE
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    expiry: datetime
    revoked_at: Optional[datetime] = None
    dpdp_compliance_notice: str = (
        "PROTECTED UNDER DPDP ACT 2023: This consent authorizes processing strictly for the declared purpose. "
        "Consent may be freely withdrawn/revoked by the customer at any time without punitive consequences."
    )

    model_config = ConfigDict(from_attributes=True)


class ConsentQueryFilter(BaseModel):
    customer_id: Optional[str] = None
    consent_type: Optional[ConsentType] = None
    status: Optional[ConsentStatus] = None
