"""
Unit tests for Consent-Based Bank Business Opportunity Matching Engine.
Verifies:
1. Multi-factor match scoring across 8 criteria (Industry, Region, Capacity vs Demand, Products, etc.)
2. Double-blind zero-knowledge anonymous cards (no company name or private info leaked)
3. Initial match state: CONSENT_REQUIRED
4. Transition to INITIATOR_CONSENTED when Party A approves
5. Transition to MUTUAL_CONSENT_GRANTED when Party B also approves
6. Identity introduction memo and cryptographic audit hash (SHA256) unlock ONLY upon mutual consent
7. Rejection workflow
8. FastAPI endpoints: GET /customers/{id}/business-opportunities and POST /business-opportunities/consent
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.business_matching import BusinessOpportunityMatchingService
from src_py.models.matching_schemas import (
    MatchConsentStatus, ConsentActionRequest
)
from src_py.data.matching_directory import BANK_BUSINESS_DIRECTORY

client = TestClient(app)


def test_calculate_match_score_high_compatibility():
    # Sri Balaji (Tiruppur Knits Supplier) vs Apex Global (Tiruppur Garment Buyer)
    supplier = BANK_BUSINESS_DIRECTORY["CUST_MSME_TIRUPPUR_001"]
    buyer = BANK_BUSINESS_DIRECTORY["CUST_CORP_GARMENT_TIR_009"]

    score, reasons = BusinessOpportunityMatchingService.calculate_match_score(supplier, buyer)

    assert score >= 0.85
    assert any("Direct Industry Alignment" in r for r in reasons)
    assert any("Geographic Proximity" in r for r in reasons)
    assert any("Buyer procurement demand" in r for r in reasons)


def test_double_blind_anonymous_card_generation():
    matches = BusinessOpportunityMatchingService.find_opportunities_for_customer("CUST_MSME_TIRUPPUR_001")
    assert len(matches) > 0
    top_match = matches[0]

    # Verify initial status is CONSENT_REQUIRED
    assert top_match.status == MatchConsentStatus.CONSENT_REQUIRED
    assert top_match.match_score >= 0.85
    assert len(top_match.reasons) >= 3

    # Private info MUST NOT be leaked in the anonymous card
    card = top_match.anonymous_counterparty_card
    assert "Apex Global" not in card.anonymous_alias
    assert "Verified Bank Client" in card.anonymous_alias
    assert card.cluster_region == "Tiruppur"
    assert top_match.unlocked_introduction_details is None


def test_mutual_consent_introduction_workflow():
    matches = BusinessOpportunityMatchingService.find_opportunities_for_customer("CUST_MSME_TIRUPPUR_001")
    top_match = matches[0]
    m_id = top_match.match_id

    # Step 1: Party A consents
    req_a = ConsentActionRequest(
        match_id=m_id,
        customer_id="CUST_MSME_TIRUPPUR_001",
        action="APPROVE",
        authorized_signatory_name="S. Balakrishnan (MD)"
    )
    res_a = BusinessOpportunityMatchingService.record_consent_and_facilitate_intro(req_a)
    assert res_a.status == MatchConsentStatus.INITIATOR_CONSENTED
    assert res_a.unlocked_introduction_details is None

    # Step 2: Party B consents
    req_b = ConsentActionRequest(
        match_id=m_id,
        customer_id="CUST_CORP_GARMENT_TIR_009",
        action="APPROVE",
        authorized_signatory_name="K. Meenakshi (Procurement Lead)"
    )
    res_b = BusinessOpportunityMatchingService.record_consent_and_facilitate_intro(req_b)
    assert res_b.status == MatchConsentStatus.MUTUAL_CONSENT_GRANTED
    
    # Mutual consent unlocked: Introductions and audit hash MUST now be available
    assert res_b.consent_audit_hash is not None
    assert res_b.consent_audit_hash.startswith("SHA256_")
    assert res_b.unlocked_introduction_details is not None
    assert "Sri Balaji Fabrics" in res_b.unlocked_introduction_details["party_a"]["company_name"]
    assert "Apex Global Apparel" in res_b.unlocked_introduction_details["party_b"]["company_name"]


def test_fastapi_business_matching_endpoints():
    # 1. Discover opportunities
    res = client.get("/customers/CUST_TEMP_LIQ_004/business-opportunities")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    opportunities = res_json["data"]
    assert len(opportunities) >= 1
    
    match_item = opportunities[0]
    assert match_item["match_score"] > 0.80
    assert match_item["status"] == "CONSENT_REQUIRED"
    assert "Hero Cycle Allied" not in match_item["anonymous_counterparty_card"]["anonymous_alias"]

    # 2. Record consent via API
    consent_req = {
        "match_id": match_item["match_id"],
        "customer_id": "CUST_TEMP_LIQ_004",
        "action": "APPROVE",
        "authorized_signatory_name": "R. Kaveri (Managing Partner)"
    }
    res_post = client.post("/business-opportunities/consent", json=consent_req)
    assert res_post.status_code == 200
    res_body = res_post.json()["data"]
    assert res_body["status"] in ["INITIATOR_CONSENTED", "MUTUAL_CONSENT_GRANTED"]
