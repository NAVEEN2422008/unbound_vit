"""
Unit tests for Customer-Facing Financial Resilience Dashboard.
Verifies:
1. Dashboard aggregation without financial jargon
2. Exact customer metrics (Resilience Score, Distress Risk, Cash, Income, Expenses, EMI, Buffers, Receivables)
3. Actionable plain-language recommendations matching specifications:
   - "Your next major cash requirement is in X days."
   - "Your business revenue is currently 18% below the normal seasonal range."
   - "Your receivables of ₹12L may reduce the need for additional borrowing."
   - "Taking the requested loan would significantly increase your repayment burden."
4. Every recommendation contains "WHY?" and "HOW CONFIDENT ARE WE?"
5. Consent section for data-sharing, business-matching, and personalized recommendations
6. FastAPI endpoints: GET /customers/{id}/dashboard and POST /customers/{id}/consent
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app

client = TestClient(app)


def test_customer_resilience_dashboard_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/dashboard")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    d = res_json["data"]

    # 1. Resilience & Plain Metrics
    assert "financial_resilience_score" in d
    assert 0 <= d["financial_resilience_score"] <= 100
    assert d["distress_risk_level"] in ["LOW", "MODERATE", "ELEVATED", "CRITICAL"]
    assert d["cash_available_today"] > 0
    assert d["expected_monthly_income"] > 0
    assert d["upcoming_monthly_loan_emi"] > 0
    assert d["savings_safety_buffer_days"] > 0
    assert d["receivables_pending"] > 0

    # 2. Key Headline Examples
    assert "next major cash requirement is in" in d["next_major_cash_requirement_headline"]
    assert "18% below the normal seasonal range" in d["seasonal_context"]["plain_explanation"]
    assert d["loan_affordability_verdict"] == "NOT RECOMMENDED"
    assert "significantly increase your" in d["loan_affordability_plain_reason"]

    # 3. Recommendations check (must contain WHY and HOW CONFIDENT)
    recs = d["recommendations"]
    assert len(recs) >= 3
    
    # Must have Receivables vs borrowing recommendation
    rec_receivables = next((r for r in recs if r["category"] == "RECEIVABLES"), None)
    assert rec_receivables is not None
    assert "reduce the need for additional borrowing" in rec_receivables["action_text"]
    assert len(rec_receivables["why_explanation"]) > 20
    assert rec_receivables["confidence_percentage"] >= 90.0
    assert "HIGH" in rec_receivables["confidence_level"]

    # Must have Loan Affordability recommendation
    rec_loan = next((r for r in recs if r["category"] == "LOAN_DECISION"), None)
    assert rec_loan is not None
    assert "repayment burden" in rec_loan["action_text"]
    assert len(rec_loan["why_explanation"]) > 20
    assert len(rec_loan["supporting_facts"]) >= 2

    # 4. Consent Section
    consent = d["consent"]
    assert consent["financial_data_sharing"] is True
    assert consent["business_matching"] is True
    assert consent["personalized_recommendations"] is True
    assert "Digital Personal Data Protection" in consent["dpdp_compliance_notice"]


def test_update_customer_consent_endpoint():
    # Update consent preferences (e.g. opt-out of business matching)
    update_payload = {
        "business_matching": False
    }
    res = client.post("/customers/CUST_MSME_TIRUPPUR_001/consent", json=update_payload)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    body = res_json["data"]
    assert body["business_matching"] is False
    assert body["financial_data_sharing"] is True

    # Re-check dashboard reflects updated consent state
    res_dash = client.get("/customers/CUST_MSME_TIRUPPUR_001/dashboard")
    assert res_dash.status_code == 200
    assert res_dash.json()["data"]["consent"]["business_matching"] is False
