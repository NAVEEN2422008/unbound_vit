"""
Unit and integration tests for Least-Harm Intervention Optimizer Service.
Verifies:
1. Evaluation of all 11 interventions:
   NO_ACTION, SAVE_WAIT, EXPENSE_REDUCTION, RECEIVABLE_ACCELERATION, EMI_RESTRUCTURE,
   TENURE_EXTENSION, REFINANCE, ASSET_ACTION, LIMITED_CREDIT, BUSINESS_RECOVERY, BUSINESS_MATCHING.
2. Benefit metrics:
   cashflow_improvement, distress_reduction, resilience_improvement, recovery_probability.
3. Harm metrics:
   new_debt, interest_increase, EMI_increase, cash_buffer_reduction,
   long_term_repayment_pressure, asset_loss.
4. Transparent weighted scoring formula:
   intervention_score = benefit_score / max(1.0, harm_score)
5. Core Institutional Mandate:
   Never optimize purely for bank revenue; objective is sustainable financial recovery.
   (e.g., Non-debt solutions like RECEIVABLE_ACCELERATION outscore debt-heavy facilities).
6. REST API:
   POST /api/v1/interventions/optimize
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.least_harm_optimizer import LeastHarmOptimizerService
from src_py.models.least_harm_schemas import CandidateIntervention
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_least_harm_optimizer_all_11_interventions_and_scoring():
    data = SAMPLE_CUSTOMERS_DATA["CUST_MSME_TIRUPPUR_001"]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=[],
        loans=[],
        obligations=[],
        receivables=[],
        payables=[],
        assets=[],
        liquid_cash=data["liquid_cash"],
        savings=data.get("savings", 0.0)
    )

    report = LeastHarmOptimizerService.optimize_interventions(fre)

    # 1. Verify 11 Interventions
    interventions_evaluated = [i.intervention for i in report.ranked_interventions]
    for expected in [
        CandidateIntervention.NO_ACTION,
        CandidateIntervention.SAVE_WAIT,
        CandidateIntervention.EXPENSE_REDUCTION,
        CandidateIntervention.RECEIVABLE_ACCELERATION,
        CandidateIntervention.EMI_RESTRUCTURE,
        CandidateIntervention.TENURE_EXTENSION,
        CandidateIntervention.REFINANCE,
        CandidateIntervention.ASSET_ACTION,
        CandidateIntervention.LIMITED_CREDIT,
        CandidateIntervention.BUSINESS_RECOVERY,
        CandidateIntervention.BUSINESS_MATCHING
    ]:
        assert expected in interventions_evaluated

    assert len(report.ranked_interventions) == 11

    # 2. Check Benefit and Harm metrics populated
    for item in report.ranked_interventions:
        # Benefits
        b = item.benefit_metrics
        assert 0.0 <= b.cashflow_improvement <= 100.0
        assert 0.0 <= b.distress_reduction <= 100.0
        assert 0.0 <= b.resilience_improvement <= 100.0
        assert 0.0 <= b.recovery_probability <= 100.0
        assert 0.0 <= b.total_benefit_score <= 100.0

        # Harms
        h = item.harm_metrics
        assert 0.0 <= h.new_debt <= 100.0
        assert 0.0 <= h.interest_increase <= 100.0
        assert 0.0 <= h.EMI_increase <= 100.0
        assert 0.0 <= h.cash_buffer_reduction <= 100.0
        assert 0.0 <= h.long_term_repayment_pressure <= 100.0
        assert 0.0 <= h.asset_loss <= 100.0
        assert 0.0 <= h.total_harm_score <= 100.0

        # Score formula check
        expected_score = round(b.total_benefit_score / max(1.0, h.total_harm_score), 2)
        assert item.intervention_score == expected_score

    # 3. Sustainable recovery over bank revenue check:
    # Non-debt solutions like RECEIVABLE_ACCELERATION must have lower harm than LIMITED_CREDIT
    rec_accel = next(i for i in report.ranked_interventions if i.intervention == CandidateIntervention.RECEIVABLE_ACCELERATION)
    lim_credit = next(i for i in report.ranked_interventions if i.intervention == CandidateIntervention.LIMITED_CREDIT)
    assert rec_accel.harm_metrics.new_debt == 0.0
    assert lim_credit.harm_metrics.new_debt > 0.0
    assert rec_accel.intervention_score > lim_credit.intervention_score


def test_api_v1_interventions_optimize_endpoint():
    payload = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "benefit_weights": {
            "cashflow_improvement": 0.35,
            "distress_reduction": 0.30
        },
        "harm_weights": {
            "new_debt": 0.30,
            "long_term_repayment_pressure": 0.20
        }
    }
    res = client.post("/api/v1/interventions/optimize", json=payload)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert len(data["ranked_interventions"]) == 11
    assert "recommended_intervention" in data
    assert "benefits" in data
    assert "risks" in data
    assert "reason" in data
    assert "confidence" in data
    assert "transparent_scoring_formula" in data
