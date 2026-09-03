"""
Pydantic schemas for the Consent-Based Bank Business Opportunity Matching Engine.
Designed as a financial distress recovery intervention leveraging the bank's enterprise client ecosystem.
Enforces double-blind anonymity until mutual consent is cryptographically recorded under DPDP.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class BusinessRole(str, Enum):
    SUPPLIER = "SUPPLIER"      # Excess capacity, distressed by low orders
    BUYER = "BUYER"            # Has active commercial procurement demand


class MatchConsentStatus(str, Enum):
    CONSENT_REQUIRED = "CONSENT_REQUIRED"              # Match found; neither party consented yet
    INITIATOR_CONSENTED = "INITIATOR_CONSENTED"        # Party A consented; awaiting Party B
    COUNTERPARTY_CONSENTED = "COUNTERPARTY_CONSENTED"  # Party B consented; awaiting Party A
    MUTUAL_CONSENT_GRANTED = "MUTUAL_CONSENT_GRANTED"  # Both parties consented -> Introduction unlocked
    REJECTED = "REJECTED"                              # Either party declined introduction
    EXPIRED = "EXPIRED"                                # 14-day consent SLA lapsed


class BusinessEntityProfile(BaseModel):
    customer_id: str
    company_name: str
    is_distressed: bool = False
    distress_reason: Optional[str] = None
    role: BusinessRole
    industry: str
    sub_sectors: List[str]
    products_services: List[str]
    cluster_region: str
    city: str
    state: str
    annual_turnover: float
    business_size: str  # MICRO, SMALL, MEDIUM, CORPORATE
    capacity_units_per_month: float
    demand_units_per_month: float
    target_partner_types: List[str]
    immediate_requirement_description: str


class AnonymousBusinessCard(BaseModel):
    """Zero-knowledge redacted preview card visible before mutual consent."""
    match_id: str
    anonymous_alias: str
    industry: str
    cluster_region: str
    business_size: str
    products_offered_or_needed: List[str]
    compatible_volume_monthly: float
    potential_monthly_revenue_impact: float


class OpportunityMatchResult(BaseModel):
    match_id: str
    distressed_customer_id: str
    counterparty_customer_id: str
    match_score: float = Field(ge=0.0, le=1.0)
    reasons: List[str]
    status: MatchConsentStatus
    anonymous_counterparty_card: AnonymousBusinessCard
    
    # Financial Distress Recovery Impact
    projected_monthly_revenue_gain: float
    projected_distress_reduction_points: float
    
    # Double-Blind Consent Records
    initiator_consent_timestamp: Optional[datetime] = None
    counterparty_consent_timestamp: Optional[datetime] = None
    consent_audit_hash: Optional[str] = None
    unlocked_introduction_details: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class ConsentActionRequest(BaseModel):
    match_id: str
    customer_id: str
    action: str = Field(..., description="APPROVE or REJECT")
    authorized_signatory_name: str
