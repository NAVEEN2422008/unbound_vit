"""
Unit and integration tests for Early Distress Detection Engine.
Verifies:
1. Dual-component prediction: Explainable Rules Engine + Calibrated Logistic Regression model
2. Calibrated 0-100 distress score and risk levels (LOW, MODERATE, HIGH, CRITICAL)
3. Prediction horizons: 7_DAY, 30_DAY, 90_DAY
4. Top risk factors breakdown
5. Acceptance Criteria:
   Given a synthetic customer with rapidly declining cash, rising obligations, and increasing
   debt burden, the system MUST generate a higher distress score than a healthy baseline customer.
6. API Endpoints: POST /api/v1/distress/predict and GET /api/v1/customers/{id}/distress
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.distress_engine import EarlyDistressDetectionService
from src_py.models.distress_schemas import (
    DistressPredictionRequest, DistressRiskLevel, PredictionHorizon
)

client = TestClient(app)


def test_acceptance_criteria_distressed_vs_healthy():
    # 1. Healthy Baseline Customer
    healthy_req = DistressPredictionRequest(
        customer_id="CUST_HEALTHY",
        declining_cash_rate_pct=0.0,
        negative_balance_frequency=0,
        cash_buffer_days=45,
        revenue_decline_pct=0.0,
        income_volatility=0.05,
        debt_service_ratio=0.18,
        fixed_cost_ratio=0.35,
        late_payments_last_90d=0,
        upcoming_collision_shortfall=0.0,
        horizon=PredictionHorizon.HORIZON_30_DAY
    )
    healthy_res = EarlyDistressDetectionService.predict_distress(healthy_req)

    # 2. Deteriorating / Distressed Customer:
    # Rapidly declining cash, rising obligations, increasing debt burden, negative balances
    distressed_req = DistressPredictionRequest(
        customer_id="CUST_DETERIORATING",
        declining_cash_rate_pct=38.0,
        negative_balance_frequency=4,
        cash_buffer_days=8,
        revenue_decline_pct=28.0,
        income_volatility=0.38,
        debt_service_ratio=0.52,
        fixed_cost_ratio=0.75,
        late_payments_last_90d=3,
        upcoming_collision_shortfall=85000.0,
        horizon=PredictionHorizon.HORIZON_30_DAY
    )
    distressed_res = EarlyDistressDetectionService.predict_distress(distressed_req)

    # Acceptance Criteria Check:
    # System MUST generate a higher distress score than a healthy baseline customer
    assert distressed_res.distress_score > healthy_res.distress_score
    assert healthy_res.distress_score < 35.0
    assert healthy_res.risk_level in [DistressRiskLevel.LOW, DistressRiskLevel.MODERATE]

    assert distressed_res.distress_score >= 60.0
    assert distressed_res.risk_level in [DistressRiskLevel.HIGH, DistressRiskLevel.CRITICAL]

    # Check model provenance and components
    assert "LogisticRegression" in distressed_res.model_type
    assert distressed_res.training_data_label == "CALIBRATED_PROTOTYPE_DATA"
    assert distressed_res.rules_engine_score > 0
    assert distressed_res.ml_model_score > 0
    assert len(distressed_res.top_risk_factors) >= 3


def test_prediction_horizons_scaling():
    req_30d = DistressPredictionRequest(
        customer_id="CUST_HORIZONS",
        cash_buffer_days=10,
        debt_service_ratio=0.48,
        upcoming_collision_shortfall=50000.0,
        horizon=PredictionHorizon.HORIZON_30_DAY
    )
    res_30d = EarlyDistressDetectionService.predict_distress(req_30d)

    # 7-Day horizon with upcoming collision gets higher urgency weighting
    req_7d = req_30d.model_copy(update={"horizon": PredictionHorizon.HORIZON_7_DAY})
    res_7d = EarlyDistressDetectionService.predict_distress(req_7d)

    assert res_7d.prediction_horizon == PredictionHorizon.HORIZON_7_DAY
    assert res_7d.distress_score >= res_30d.distress_score


def test_api_v1_distress_predict_endpoint():
    payload = {
        "customer_id": "CUST_API_TEST",
        "cash_buffer_days": 12,
        "debt_service_ratio": 0.44,
        "revenue_decline_pct": 15.0,
        "upcoming_collision_shortfall": 30000.0,
        "horizon": "30_DAY"
    }
    res = client.post("/api/v1/distress/predict", json=payload)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["customer_id"] == "CUST_API_TEST"
    assert "distress_score" in data
    assert data["distress_score"] > 0
    assert "risk_level" in data
    assert len(data["top_risk_factors"]) > 0


def test_api_v1_get_customer_distress_endpoint():
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress?horizon=30_DAY")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert 0.0 <= data["distress_score"] <= 100.0
    assert data["risk_level"] in ["LOW", "MODERATE", "HIGH", "CRITICAL"]
    assert "confidence_score" in data
