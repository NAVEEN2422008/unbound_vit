"""
Unit tests for the new Diagnostic Modular Suite (Obligation Radar, IRACP classification,
Root Cause, Context & Seasonal Benchmarking, Credit Affordability, Explainability, Human Review & Outcomes).
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.diagnostic_suite import DiagnosticModularSuite

client = TestClient(app)


def test_obligation_radar_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/obligation-radar")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert "radar_status" in data
    assert "days_to_liquidity_exhaustion" in data
    assert len(data["critical_milestones"]) >= 3


def test_distress_classification_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/distress-classification")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["classification"] in ["SMA_0_WATCHLIST", "SMA_1_EARLY_STRESS", "NON_DISTRESSED"]
    assert "rbi_iracp_bucket" in data
    assert data["distress_score"] > 0


def test_root_cause_analysis_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/root-cause")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "primary_driver" in data
    assert len(data["detailed_factors"]) >= 1
    assert data["is_temporary_or_structural"] in ["TEMPORARY_LIQUIDITY_GAP", "STRUCTURAL_DEFICIT"]


def test_context_benchmarking_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/context-benchmarking")
    assert res.status_code == 200
    data = res.json()["data"]
    assert "Tiruppur" in data["cluster_region"]
    assert data["cluster_median_revenue"] > 0
    assert "seasonal_forecast_next_quarter" in data


def test_credit_affordability_and_guardrail_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/credit-affordability")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["statutory_dscr_floor"] == 1.25
    assert data["statutory_foir_ceiling"] == 0.60
    assert data["loan_guardrail_verdict"] in ["PERMITTED", "VETOED_PREDATORY_RISK"]
    assert "optimal_financing_timing" in data


def test_explainability_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/explainability")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["overall_confidence_score_pct"] >= 90.0
    assert len(data["explainable_decision_tree"]) >= 4


def test_human_review_and_audit_log_endpoint():
    review_req = {
        "decision": "APPROVE",
        "comments": "Approved TReDS invoice discounting of ₹12L; rejected new term loan due to DSCR constraint."
    }
    # Test recording review as credit officer
    res = client.post(
        "/customers/CUST_MSME_TIRUPPUR_001/human-review",
        json=review_req,
        headers={"X-API-KEY": "FINRES_CREDIT_OFFICER_KEY_2026"}
    )
    assert res.status_code == 200
    res_data = res.json()["data"]
    assert res_data["action"] == "APPROVE"
    assert res_data["cryptographic_hash"].startswith("SHA256_")

    # Verify audit log retrieval
    res_logs = client.get(
        "/customers/CUST_MSME_TIRUPPUR_001/audit-logs",
        headers={"X-API-KEY": "FINRES_AUDITOR_DPDP_KEY_2026"}
    )
    assert res_logs.status_code == 200
    logs = res_logs.json()["data"]
    assert len(logs) >= 1
    assert logs[-1]["customer_id"] == "CUST_MSME_TIRUPPUR_001"


def test_outcome_tracking_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/outcomes")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["monitoring_active"] is True
    assert data["cumulative_default_prevented"] is True
    assert data["interest_saved_by_avoiding_predatory_credit"] > 0
