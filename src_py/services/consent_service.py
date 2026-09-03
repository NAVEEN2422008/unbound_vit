"""
Customer Consent Management and Data Access Governance Service.
Enforces DPDP Act 2023 compliance across all financial analysis and business matching operations.

Key Responsibilities:
1. Lifecycle of Consents:
   - Create, Query, and Revoke consents for all 6 types:
     FINANCIAL_DATA_ACCESS, TRANSACTION_ANALYSIS, PERSONALIZED_RECOMMENDATIONS,
     PEER_ANALYSIS, BUSINESS_MATCHING, COMMUNICATION.
2. Sensitive Data Access Authorization:
   - Evaluates whether a requesting service or actor is authorized to read sensitive financial fields
     (e.g., bank balances, loan details, ledger entries).
3. Bilateral Business Matching Consent Enforcement:
   - Guarantees both parties have granted active BUSINESS_MATCHING consent before direct introduction.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from src_py.models.consent_schemas import (
    ConsentType, ConsentStatus, CreateConsentRequest, ConsentRecord, ConsentQueryFilter
)

# In-memory mock database collection for consents
CONSENT_STORE: Dict[str, ConsentRecord] = {}


class CustomerConsentService:

    # Mapping of sensitive domains to required consent types
    SERVICE_PERMISSION_MAP = {
        "FINANCIAL_REALITY_ENGINE": ConsentType.FINANCIAL_DATA_ACCESS,
        "CASHFLOW_TIMELINE": ConsentType.TRANSACTION_ANALYSIS,
        "DISTRESS_DETECTION": ConsentType.FINANCIAL_DATA_ACCESS,
        "LEAST_HARM_OPTIMIZER": ConsentType.PERSONALIZED_RECOMMENDATIONS,
        "PEER_BENCHMARKING": ConsentType.PEER_ANALYSIS,
        "BUSINESS_MATCHING": ConsentType.BUSINESS_MATCHING,
        "COMMUNICATION_SERVICE": ConsentType.COMMUNICATION
    }

    @classmethod
    def create_consent(cls, req: CreateConsentRequest) -> ConsentRecord:
        """
        Registers a new explicit consent record with timestamp and expiry.
        """
        now = datetime.utcnow()
        expiry = now + timedelta(days=req.validity_days or 365)
        consent_id = f"CONSENT_{req.customer_id[-6:]}_{req.consent_type.value[:4]}_{int(now.timestamp())}"

        # If previous active consent of this type exists, supersede it
        for c in CONSENT_STORE.values():
            if c.customer_id == req.customer_id and c.consent_type == req.consent_type and c.status == ConsentStatus.ACTIVE:
                c.status = ConsentStatus.REVOKED
                c.revoked_at = now

        record = ConsentRecord(
            id=consent_id,
            customer_id=req.customer_id,
            consent_type=req.consent_type,
            purpose=req.purpose,
            status=ConsentStatus.ACTIVE,
            timestamp=now,
            expiry=expiry,
            revoked_at=None
        )
        CONSENT_STORE[consent_id] = record
        return record

    @classmethod
    def get_consents(
        cls,
        customer_id: Optional[str] = None,
        consent_type: Optional[ConsentType] = None,
        status: Optional[ConsentStatus] = None
    ) -> List[ConsentRecord]:
        """
        Queries consent records matching filter criteria.
        Auto-expires records whose expiry has lapsed.
        """
        now = datetime.utcnow()
        results: List[ConsentRecord] = []

        for record in CONSENT_STORE.values():
            # Check expiry
            if record.status == ConsentStatus.ACTIVE and record.expiry < now:
                record.status = ConsentStatus.EXPIRED

            if customer_id and record.customer_id != customer_id:
                continue
            if consent_type and record.consent_type != consent_type:
                continue
            if status and record.status != status:
                continue

            results.append(record)

        return sorted(results, key=lambda x: x.timestamp, reverse=True)

    @classmethod
    def revoke_consent(cls, consent_id: str) -> ConsentRecord:
        """
        Revokes an existing consent under DPDP right to withdraw consent.
        """
        record = CONSENT_STORE.get(consent_id)
        if not record:
            raise ValueError(f"Consent ID '{consent_id}' not found.")

        record.status = ConsentStatus.REVOKED
        record.revoked_at = datetime.utcnow()
        return record

    @classmethod
    def check_service_data_access(cls, customer_id: str, service_name: str) -> bool:
        """
        DATA ACCESS RULE:
        Verifies if an analytical service is authorized to access sensitive customer financials.
        """
        req_consent = cls.SERVICE_PERMISSION_MAP.get(service_name)
        if not req_consent:
            return True  # Public non-sensitive operations

        active_consents = cls.get_consents(
            customer_id=customer_id,
            consent_type=req_consent,
            status=ConsentStatus.ACTIVE
        )
        return len(active_consents) > 0

    @classmethod
    def check_bilateral_business_matching_consent(
        cls,
        customer_a_id: str,
        customer_b_id: str
    ) -> bool:
        """
        BUSINESS MATCHING RULE:
        Both parties must consent to BUSINESS_MATCHING before direct introduction.
        """
        a_consents = cls.get_consents(customer_id=customer_a_id, consent_type=ConsentType.BUSINESS_MATCHING, status=ConsentStatus.ACTIVE)
        b_consents = cls.get_consents(customer_id=customer_b_id, consent_type=ConsentType.BUSINESS_MATCHING, status=ConsentStatus.ACTIVE)
        return len(a_consents) > 0 and len(b_consents) > 0

    @classmethod
    def seed_initial_sample_consents(cls, customer_id: str):
        """Seeds standard active consents for test accounts."""
        purposes = {
            ConsentType.FINANCIAL_DATA_ACCESS: "Access bank account statements and Account Aggregator feeds for liquidity monitoring.",
            ConsentType.TRANSACTION_ANALYSIS: "Analyze bank credits, debits, and NACH obligations for collision detection.",
            ConsentType.PERSONALIZED_RECOMMENDATIONS: "Generate AI-driven least-harm financial recovery interventions.",
            ConsentType.PEER_ANALYSIS: "Compare enterprise operational performance against regional and industry peer benchmarks.",
            ConsentType.BUSINESS_MATCHING: "Participate in bank-assisted commercial buyer-supplier opportunity matching.",
            ConsentType.COMMUNICATION: "Receive early distress SMS, WhatsApp, and email alerts."
        }
        for ctype, purpose in purposes.items():
            cls.create_consent(CreateConsentRequest(
                customer_id=customer_id,
                consent_type=ctype,
                purpose=purpose,
                validity_days=365
            ))
