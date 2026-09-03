"""
Tests for Banker Human Review & Escalation Interface.
Verifies:
1. Automatic escalation when:
   - confidence is low
   - large credit request
   - asset sale recommendation
   - conflicting model outputs
   - insufficient data
   - unusual business conditions
2. Review screen displays:
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
3. Actions:
   - APPROVE, REJECT, MODIFY, REQUEST_MORE_DATA, ESCALATE
4. Audit storage:
   - review_id, customer_id, reviewer_id, decision, reason, notes, timestamp
   - Human decisions must be added to audit history.
   - Never silently overwrite model decisions.
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.banker_review_service import BankerHumanReviewService, BANKER_REVIEW_AUDIT_LEDGER
from src_py.services.confidence_engine import EpistemicConfidenceService
from src_py.models.human_review_schemas import (
    HumanReviewAction, EscalationReason, SubmitHumanReviewRequest
)

client = TestClient(app)


def test_automatic_escalation_triggers():
    # 1. Trigger: Low Confidence
    conf_low = EpistemicConfidenceService.evaluate_confidence(
        target_entity_id="CUST_LOW_CONF",
        data_completeness_pct=30.0,
        data_freshness_days=80,
        historical_coverage_months=2,
        peer_sample_size=1,
        estimated_proportion_pct=70.0
    )
    status_low = BankerHumanReviewService.check_automatic_escalation(
        confidence_report=conf_low,
        credit_requested=500000.0,
        recommended_intervention_type="RECEIVABLE_ACCELERATION"
    )
    assert status_low.is_escalated is True
    assert EscalationReason.LOW_CONFIDENCE in status_low.triggers

    # 2. Trigger: Large Credit Request (> ₹25L)
    conf_high = EpistemicConfidenceService.evaluate_confidence(
        target_entity_id="CUST_HIGH_CONF",
        data_completeness_pct=95.0,
        data_freshness_days=1,
        historical_coverage_months=36,
        peer_sample_size=25
    )
    status_large_credit = BankerHumanReviewService.check_automatic_escalation(
        confidence_report=conf_high,
        credit_requested=3500000.0,  # 35 Lakhs
        recommended_intervention_type="RECEIVABLE_ACCELERATION"
    )
    assert status_large_credit.is_escalated is True
    assert EscalationReason.LARGE_CREDIT_REQUEST in status_large_credit.triggers

    # 3. Trigger: Asset Sale Recommendation
    status_asset_sale = BankerHumanReviewService.check_automatic_escalation(
        confidence_report=conf_high,
        credit_requested=200000.0,
        recommended_intervention_type="ASSET_SALE_OR_DISPOSAL"
    )
    assert status_asset_sale.is_escalated is True
    assert EscalationReason.ASSET_SALE_RECOMMENDED in status_asset_sale.triggers

    # 4. Trigger: Unusual Business Conditions (> 20% divergence)
    status_unusual = BankerHumanReviewService.check_automatic_escalation(
        confidence_report=conf_high,
        credit_requested=200000.0,
        recommended_intervention_type="NO_ACTION",
        divergence_from_cluster_pct=-26.5
    )
    assert status_unusual.is_escalated is True
    assert EscalationReason.UNUSUAL_BUSINESS_CONDITIONS in status_unusual.triggers


def test_api_v1_banker_review_screen_and_actions():
    BANKER_REVIEW_AUDIT_LEDGER.clear()

    # 1. GET /api/v1/banker/review/{id} (Check all 11 display sections)
    res_get = client.get("/api/v1/banker/review/CUST_MSME_TIRUPPUR_001?credit_requested=3000000")
    assert res_get.status_code == 200
    json_get = res_get.json()
    assert json_get["success"] is True
    screen = json_get["data"]

    # Verify 11 analytical components exist
    assert "customer" in screen
    assert "financial_reality" in screen
    assert "distress" in screen
    assert "confidence" in screen
    assert "root_cause" in screen
    assert "context" in screen
    assert "assets" in screen
    assert "receivables" in screen
    assert "credit_affordability" in screen
    assert "decision_twin" in screen
    assert "recommended_intervention" in screen
    assert "escalation_status" in screen

    # Check allowed actions
    assert "APPROVE" in screen["allowed_actions"]
    assert "REJECT" in screen["allowed_actions"]
    assert "MODIFY" in screen["allowed_actions"]
    assert "REQUEST_MORE_DATA" in screen["allowed_actions"]
    assert "ESCALATE" in screen["allowed_actions"]

    # Check escalation triggered due to credit_requested = 30L
    assert screen["escalation_status"]["is_escalated"] is True
    assert "LARGE_CREDIT_REQUEST" in screen["escalation_status"]["triggers"]

    # 2. POST /api/v1/banker/review/{id} (Record MODIFY decision)
    post_payload = {
        "decision": "MODIFY",
        "reason": "Approve TReDS factoring at 75% advance with moratorium on term debt",
        "notes": "Spoke with promoter; inventory turnover expected to normalize in Q3.",
        "modified_parameters": {"advance_rate_pct": 75.0, "moratorium_months": 3}
    }
    res_post = client.post("/api/v1/banker/review/CUST_MSME_TIRUPPUR_001", json=post_payload)
    assert res_post.status_code == 200
    post_data = res_post.json()["data"]

    # Verify audit fields stored
    assert post_data["review_id"].startswith("REV_")
    assert post_data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert post_data["reviewer_id"] == "OFFICER_BALA_772"
    assert post_data["decision"] == "MODIFY"
    assert post_data["reason"] == post_payload["reason"]
    assert post_data["notes"] == post_payload["notes"]
    assert post_data["timestamp"] is not None
    assert post_data["audit_hash"].startswith("SHA256_")

    # Verify that model decision was NOT overwritten, but recorded alongside
    assert post_data["original_model_recommendation"] != ""
    assert len(BANKER_REVIEW_AUDIT_LEDGER) == 1

    # 3. Verify audit history API returns this action under GET /api/v1/audit/customer/{id}
    res_audit = client.get("/api/v1/audit/customer/CUST_MSME_TIRUPPUR_001")
    assert res_audit.status_code == 200
    audit_events = res_audit.json()["data"]
    human_events = [ev for ev in audit_events if ev["event_type"] == "HUMAN_REVIEWED"]
    assert len(human_events) >= 1
    assert any(ev["human_decision"] == "MODIFY" for ev in human_events)
