"""
Tests for Intervention Solvency Outcome Verification Engine.
Verifies:
1. BEFORE and AFTER metrics capture:
   - distress_score, resilience_score, cashflow, cash_buffer, debt, EMI, missed_payments
2. Metric comparison:
   - distress_change, resilience_change, cashflow_change, debt_change, repayment_change
3. Four classifications:
   - SUCCESS
   - PARTIAL_SUCCESS
   - NO_EFFECT
   - NEGATIVE_OUTCOME
4. REST APIs:
   - GET /api/v1/interventions/{id}/outcome
   - POST /api/v1/interventions/{id}/outcome
5. Epistemic constraint:
   - "associated improvement" instead of claiming causality.
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.outcome_verification_service import (
    InterventionOutcomeService, INTERVENTION_OUTCOMES_STORE
)
from src_py.models.outcome_schemas import (
    SolvencyMetricsSnapshot, OutcomeClassification, RecordInterventionOutcomeRequest
)

client = TestClient(app)


def test_classification_logic():
    # 1. SUCCESS: Distress 81 -> 31 (-50), Resilience 42 -> 75 (+33), Cashflow -85k -> +145k
    b1 = SolvencyMetricsSnapshot(
        distress_score=81.0, resilience_score=42.0, cashflow=-85000.0,
        cash_buffer=11.0, debt=4500000.0, EMI=120000.0, missed_payments=0
    )
    a1 = SolvencyMetricsSnapshot(
        distress_score=31.0, resilience_score=75.0, cashflow=145000.0,
        cash_buffer=46.0, debt=3800000.0, EMI=105000.0, missed_payments=0
    )
    d1 = InterventionOutcomeService.calculate_delta(b1, a1)
    assert d1.distress_change == -50.0
    assert d1.resilience_change == 33.0
    assert d1.cashflow_change == 230000.0
    assert d1.debt_change == -700000.0
    assert d1.repayment_change == 0
    assert InterventionOutcomeService.classify_outcome(d1) == OutcomeClassification.SUCCESS

    # 2. NEGATIVE_OUTCOME: Distress worsened (+12) or missed payments (+2)
    a_neg = SolvencyMetricsSnapshot(
        distress_score=93.0, resilience_score=30.0, cashflow=-120000.0,
        cash_buffer=4.0, debt=5200000.0, EMI=145000.0, missed_payments=2
    )
    d_neg = InterventionOutcomeService.calculate_delta(b1, a_neg)
    assert InterventionOutcomeService.classify_outcome(d_neg) == OutcomeClassification.NEGATIVE_OUTCOME

    # 3. NO_EFFECT: Metrics moved <= 3 points
    a_flat = SolvencyMetricsSnapshot(
        distress_score=80.0, resilience_score=43.0, cashflow=-84000.0,
        cash_buffer=11.5, debt=4500000.0, EMI=120000.0, missed_payments=0
    )
    d_flat = InterventionOutcomeService.calculate_delta(b1, a_flat)
    assert InterventionOutcomeService.classify_outcome(d_flat) == OutcomeClassification.NO_EFFECT

    # 4. PARTIAL_SUCCESS: Moderate improvement (e.g. distress -6, resilience +5)
    a_part = SolvencyMetricsSnapshot(
        distress_score=75.0, resilience_score=47.0, cashflow=-40000.0,
        cash_buffer=16.0, debt=4400000.0, EMI=120000.0, missed_payments=0
    )
    d_part = InterventionOutcomeService.calculate_delta(b1, a_part)
    assert InterventionOutcomeService.classify_outcome(d_part) == OutcomeClassification.PARTIAL_SUCCESS


def test_api_v1_intervention_outcome_endpoints():
    INTERVENTION_OUTCOMES_STORE.clear()

    # 1. POST /api/v1/interventions/{id}/outcome
    payload = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "intervention_name": "TReDS Receivable Acceleration & Machine Reallocation",
        "evaluation_month": 6,
        "before": {
            "distress_score": 81.0,
            "resilience_score": 42.0,
            "cashflow": -85000.0,
            "cash_buffer": 11.0,
            "debt": 4500000.0,
            "EMI": 120000.0,
            "missed_payments": 0
        },
        "after": {
            "distress_score": 47.0,
            "resilience_score": 62.0,
            "cashflow": 60000.0,
            "cash_buffer": 32.0,
            "debt": 4100000.0,
            "EMI": 115000.0,
            "missed_payments": 0
        },
        "causal_attribution_evidence": "associated improvement",
        "evaluator_notes": "Significant 6-month solvency stabilization observed"
    }

    res_post = client.post("/api/v1/interventions/INT_TREDS_001/outcome", json=payload)
    assert res_post.status_code == 200
    json_post = res_post.json()
    assert json_post["success"] is True
    data_post = json_post["data"]

    assert data_post["intervention_id"] == "INT_TREDS_001"
    assert data_post["classification"] == "SUCCESS"
    assert data_post["compare"]["distress_change"] == -34.0
    assert data_post["compare"]["resilience_change"] == 20.0
    assert "associated improvement" in data_post["attribution_statement"]

    # 2. GET /api/v1/interventions/{id}/outcome
    res_get = client.get("/api/v1/interventions/INT_TREDS_001/outcome")
    assert res_get.status_code == 200
    data_get = res_get.json()["data"]
    assert data_get["intervention_id"] == "INT_TREDS_001"
    assert data_get["classification"] == "SUCCESS"
    assert data_get["before"]["distress_score"] == 81.0
    assert data_get["after"]["distress_score"] == 47.0
