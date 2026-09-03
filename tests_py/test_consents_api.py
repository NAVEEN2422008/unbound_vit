"""
Unit and integration tests for DPDP Granular Consent Management Service & REST APIs.
Verifies:
1. Six Consent Types:
   - FINANCIAL_DATA_ACCESS
   - TRANSACTION_ANALYSIS
   - PERSONALIZED_RECOMMENDATIONS
   - PEER_ANALYSIS
   - BUSINESS_MATCHING
   - COMMUNICATION
2. Stored Fields:
   - id, customer_id, consent_type, purpose, status, timestamp, expiry, revoked_at
3. Business Matching Rule:
   - Both parties must consent before direct introduction.
4. Data Access Rule:
   - Only authorized services access sensitive financial fields.
5. REST Endpoints:
   - GET /api/v1/consents
   - POST /api/v1/consents
   - DELETE /api/v1/consents/{id}
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.consent_service import CustomerConsentService, CONSENT_STORE
from src_py.models.consent_schemas import ConsentType, ConsentStatus, CreateConsentRequest

client = TestClient(app)


def test_consent_lifecycle_and_rules():
    CONSENT_STORE.clear()

    # 1. Create Consent for Customer A
    req_a = CreateConsentRequest(
        customer_id="CUST_TIRUPPUR_A",
        consent_type=ConsentType.BUSINESS_MATCHING,
        purpose="Authorize bank matching for commercial fabric procurement",
        validity_days=180
    )
    c_a = CustomerConsentService.create_consent(req_a)
    assert c_a.status == ConsentStatus.ACTIVE
    assert c_a.customer_id == "CUST_TIRUPPUR_A"
    assert c_a.expiry > c_a.timestamp
    assert c_a.revoked_at is None

    # 2. Business Matching Bilateral Consent Check (A consented, B has NOT consented yet)
    is_intro_allowed = CustomerConsentService.check_bilateral_business_matching_consent(
        "CUST_TIRUPPUR_A", "CUST_GARMENT_B"
    )
    assert is_intro_allowed is False

    # 3. Customer B consents
    req_b = CreateConsentRequest(
        customer_id="CUST_GARMENT_B",
        consent_type=ConsentType.BUSINESS_MATCHING,
        purpose="Authorize bank buyer-supplier matching",
        validity_days=365
    )
    CustomerConsentService.create_consent(req_b)

    # Now both have consented -> introduction permitted
    assert CustomerConsentService.check_bilateral_business_matching_consent(
        "CUST_TIRUPPUR_A", "CUST_GARMENT_B"
    ) is True

    # 4. Sensitive Data Access Rule Check
    # Customer A has NOT granted FINANCIAL_DATA_ACCESS yet
    assert CustomerConsentService.check_service_data_access("CUST_TIRUPPUR_A", "FINANCIAL_REALITY_ENGINE") is False

    # Grant FINANCIAL_DATA_ACCESS
    CustomerConsentService.create_consent(CreateConsentRequest(
        customer_id="CUST_TIRUPPUR_A",
        consent_type=ConsentType.FINANCIAL_DATA_ACCESS,
        purpose="Analyze bank statements and credit obligations"
    ))
    assert CustomerConsentService.check_service_data_access("CUST_TIRUPPUR_A", "FINANCIAL_REALITY_ENGINE") is True

    # 5. Revoke Consent
    revoked = CustomerConsentService.revoke_consent(c_a.id)
    assert revoked.status == ConsentStatus.REVOKED
    assert revoked.revoked_at is not None

    # Bilateral check must now fail because A revoked
    assert CustomerConsentService.check_bilateral_business_matching_consent(
        "CUST_TIRUPPUR_A", "CUST_GARMENT_B"
    ) is False


def test_api_v1_consents_endpoints():
    CONSENT_STORE.clear()

    # 1. POST /api/v1/consents
    post_payload = {
        "customer_id": "CUST_TEST_API_001",
        "consent_type": "TRANSACTION_ANALYSIS",
        "purpose": "Analyze Account Aggregator transaction feeds for cash flow forecasting",
        "validity_days": 365
    }
    res_post = client.post("/api/v1/consents", json=post_payload)
    assert res_post.status_code == 200
    json_post = res_post.json()
    assert json_post["success"] is True
    consent_item = json_post["data"]
    consent_id = consent_item["id"]
    assert consent_item["customer_id"] == "CUST_TEST_API_001"
    assert consent_item["consent_type"] == "TRANSACTION_ANALYSIS"
    assert consent_item["status"] == "ACTIVE"

    # 2. GET /api/v1/consents (with filter)
    res_get = client.get(f"/api/v1/consents?customer_id=CUST_TEST_API_001&status=ACTIVE")
    assert res_get.status_code == 200
    get_items = res_get.json()["data"]
    assert len(get_items) == 1
    assert get_items[0]["id"] == consent_id

    # 3. DELETE /api/v1/consents/{id}
    res_del = client.delete(f"/api/v1/consents/{consent_id}")
    assert res_del.status_code == 200
    del_data = res_del.json()["data"]
    assert del_data["id"] == consent_id
    assert del_data["status"] == "REVOKED"
    assert del_data["revoked_at"] is not None

    # 4. Verify GET returns REVOKED
    res_get_rev = client.get(f"/api/v1/consents?customer_id=CUST_TEST_API_001&status=REVOKED")
    assert res_get_rev.status_code == 200
    assert len(res_get_rev.json()["data"]) == 1
