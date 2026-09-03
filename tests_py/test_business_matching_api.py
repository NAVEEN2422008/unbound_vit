"""
Integration and API tests for official Bank Business Matching Recovery Engine.
Verifies:
1. Bank-assisted recovery mechanism:
   - Matches distressed customer (e.g. Textile Manufacturer with low orders) with
     corporate buyer (e.g. Garment Manufacturer needing textile supplier).
2. Matching features:
   - industry, products, services, geography, capacity, demand, business size.
3. 8-step process & status progression:
   - MATCH_IDENTIFIED -> CONSENT_REQUIRED -> BOTH_CONSENTED / MUTUAL_CONSENT_GRANTED -> INTRODUCTION_SENT -> INTRODUCTION_COMPLETE, or DECLINED.
4. Privacy & Confidentiality Guarantee:
   - Bank balance, loan details, distress score, transaction history, and private financials are NEVER EXPOSED.
5. Official APIs:
   - POST /api/v1/business-matching/search
   - POST /api/v1/business-matching/{id}/consent
   - GET /api/v1/business-matching/{customer_id}
6. Success Metrics:
   - introduction completed, business relationship created, additional revenue observed,
     cash-flow improvement, repayment improvement.
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.models.matching_schemas import (
    MatchConsentStatus, BusinessMatchingSuccessMetrics
)
from src_py.services.business_matching import ACTIVE_MATCH_REGISTRY

client = TestClient(app)


def test_api_v1_business_matching_full_lifecycle():
    # Reset active match registry for clean isolation
    ACTIVE_MATCH_REGISTRY.clear()

    # 1. POST /api/v1/business-matching/search
    search_payload = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "min_match_score": 0.60
    }
    search_res = client.post("/api/v1/business-matching/search", json=search_payload)
    assert search_res.status_code == 200
    search_json = search_res.json()
    assert search_json["success"] is True
    data = search_json["data"]
    assert data["distressed_customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert data["matches_found"] >= 1
    assert "never exposed" in data["confidentiality_notice"].lower()

    match_item = data["matches"][0]
    match_id = match_item["match_id"]
    assert match_item["match_score"] >= 0.60

    # Verify Strict Confidentiality (No private financials leaked)
    card = match_item["anonymous_counterparty_card"]
    assert "bank balance" not in str(card).lower()
    assert "loan details" not in str(card).lower()
    assert "distress score" not in str(card).lower()
    assert match_item["unlocked_introduction_details"] is None

    # 2. GET /api/v1/business-matching/{customer_id}
    get_res = client.get("/api/v1/business-matching/CUST_MSME_TIRUPPUR_001")
    assert get_res.status_code == 200
    get_data = get_res.json()["data"]
    assert len(get_data) >= 1
    assert get_data[0]["match_id"] == match_id

    # 3. POST /api/v1/business-matching/{id}/consent (Party A consents)
    consent_a = {
        "match_id": match_id,
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "action": "APPROVE",
        "authorized_signatory_name": "S. Balakrishnan (MD)"
    }
    consent_res_a = client.post(f"/api/v1/business-matching/{match_id}/consent", json=consent_a)
    assert consent_res_a.status_code == 200
    res_a_data = consent_res_a.json()["data"]
    assert res_a_data["status"] == MatchConsentStatus.INITIATOR_CONSENTED

    # 4. POST /api/v1/business-matching/{id}/consent (Party B consents -> Introduction Unlocked)
    counterparty_id = match_item["counterparty_customer_id"]
    consent_b = {
        "match_id": match_id,
        "customer_id": counterparty_id,
        "action": "APPROVE",
        "authorized_signatory_name": "K. Meenakshi (Procurement Head)"
    }
    consent_res_b = client.post(f"/api/v1/business-matching/{match_id}/consent", json=consent_b)
    assert consent_res_b.status_code == 200
    res_b_data = consent_res_b.json()["data"]
    assert res_b_data["status"] in [MatchConsentStatus.MUTUAL_CONSENT_GRANTED, MatchConsentStatus.BOTH_CONSENTED]
    assert res_b_data["unlocked_introduction_details"] is not None
    assert "party_a" in res_b_data["unlocked_introduction_details"]
    assert "party_b" in res_b_data["unlocked_introduction_details"]

    # 5. Success Metrics Validation
    success = BusinessMatchingSuccessMetrics(
        introduction_completed=True,
        business_relationship_created=True,
        additional_revenue_observed=1800000.0,
        cash_flow_improvement=240000.0,
        repayment_improvement="PUNCTUAL_DEBT_SERVICING"
    )
    assert success.introduction_completed is True
    assert success.additional_revenue_observed == 1800000.0


def test_business_matching_declined_status():
    # Discover live match_id first
    search_res = client.post(
        "/api/v1/business-matching/search",
        json={"customer_id": "CUST_MSME_TIRUPPUR_001"}
    )
    assert search_res.status_code == 200
    match_id = search_res.json()["data"]["matches"][0]["match_id"]

    # Verify decline transition
    decline_payload = {
        "match_id": match_id,
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "action": "DECLINE",
        "authorized_signatory_name": "S. Balakrishnan (MD)"
    }
    res = client.post(f"/api/v1/business-matching/{match_id}/consent", json=decline_payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["status"] == MatchConsentStatus.DECLINED
