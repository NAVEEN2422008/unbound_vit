"""
Unit and integration tests for Prediction Reliability and Epistemic Confidence Engine Service.
Verifies:
1. Seven Core Dimensions:
   data completeness, data freshness, historical coverage, peer sample size,
   model confidence, prediction stability, actual/predicted/estimated proportions.
2. Output Contract:
   confidence_score (0.0 to 100.0), confidence_level (HIGH, MEDIUM, LOW).
3. Rule:
   LOW confidence -> human_review_required is strictly True.
4. Core Independence Principle:
   Confidence is independent from the actual risk score.
   Example from Specification:
   Distress: 90, Confidence: 45
   means "High estimated distress but low confidence", NOT "Customer definitely has high risk".
5. REST APIs:
   - POST /api/v1/confidence/evaluate
   - GET /api/v1/customers/{id}/confidence
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.confidence_engine import EpistemicConfidenceService
from src_py.models.confidence_schemas import ConfidenceLevel

client = TestClient(app)


def test_confidence_engine_specification_example_distress_90_confidence_low():
    """
    Specification Scenario:
    Distress = 90 (very high distress), but data is stale and history is sparse -> Confidence = ~45 (LOW).
    Meaning: "High estimated distress but low confidence."
    Rule: LOW confidence -> human review required MUST be True.
    """
    report = EpistemicConfidenceService.evaluate_confidence(
        target_entity_id="CUST_HIGH_DISTRESS_SPARSE_DATA",
        target_prediction_type="DISTRESS_SCORE",
        underlying_prediction_value=90.0,
        data_completeness_pct=40.0,
        data_freshness_days=65,             # Very stale data
        historical_coverage_months=3,        # Sparse history
        peer_sample_size=2,                 # Inadequate peer sample (< 5)
        model_raw_confidence=0.55,
        prediction_variance_pct=25.0,       # High variance
        actual_proportion_pct=20.0,
        user_entered_proportion_pct=20.0,
        estimated_proportion_pct=60.0       # Heavy estimation
    )

    # 1. Independent score check
    assert report.underlying_prediction_value == 90.0
    assert report.confidence_score <= 48.0
    assert report.confidence_level == ConfidenceLevel.LOW

    # 2. Rule: LOW confidence -> human review required
    assert report.human_review_required is True

    # 3. Epistemic Phrasing
    assert "high estimated distress but low confidence" in report.epistemic_interpretation.lower()
    assert "human review is mandated" in report.independence_disclaimer.lower()


def test_confidence_engine_high_reliability():
    """
    Healthy telemetry with deep history and high actual verification.
    """
    report = EpistemicConfidenceService.evaluate_confidence(
        target_entity_id="CUST_VERIFIED_ENTERPRISE",
        target_prediction_type="RESILIENCE_SCORE",
        underlying_prediction_value=85.0,
        data_completeness_pct=98.0,
        data_freshness_days=1,
        historical_coverage_months=48,
        peer_sample_size=35,
        model_raw_confidence=0.92,
        prediction_variance_pct=2.0,
        actual_proportion_pct=85.0,
        user_entered_proportion_pct=10.0,
        estimated_proportion_pct=5.0
    )

    assert report.confidence_score >= 85.0
    assert report.confidence_level == ConfidenceLevel.HIGH
    assert report.human_review_required is False


def test_api_v1_confidence_endpoints():
    # 1. POST /api/v1/confidence/evaluate
    payload = {
        "target_entity_id": "TEST_ENTITY_101",
        "target_prediction_type": "DISTRESS_SCORE",
        "underlying_prediction_value": 90.0,
        "data_completeness_pct": 35.0,
        "data_freshness_days": 80,
        "historical_coverage_months": 2,
        "peer_sample_size": 1,
        "estimated_proportion_pct": 75.0
    }
    res_post = client.post("/api/v1/confidence/evaluate", json=payload)
    assert res_post.status_code == 200
    post_json = res_post.json()
    assert post_json["success"] is True
    post_data = post_json["data"]
    assert post_data["confidence_level"] == "LOW"
    assert post_data["human_review_required"] is True

    # 2. GET /api/v1/customers/{id}/confidence
    res_get = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/confidence")
    assert res_get.status_code == 200
    get_json = res_get.json()
    assert get_json["success"] is True
    get_data = get_json["data"]
    assert get_data["target_entity_id"] == "CUST_MSME_TIRUPPUR_001"
    assert get_data["confidence_score"] >= 70.0
    assert get_data["confidence_level"] in ["MEDIUM", "HIGH"]
