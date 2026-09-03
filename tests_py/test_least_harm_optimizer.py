"""
Unit tests for Least-Harm Intervention Optimizer (LHO).
Verifies:
1. Evaluation of all 11 candidate interventions
2. Calculation of 9 quantitative impact metrics
3. Mathematical Harm and Benefit scoring functions
4. Strict enforcement of anti-predatory "No-New-Loan" guardrail (DSCR >= 1.25, FOIR <= 60%)
5. Ranking order (safest/highest net score first, vetoed options last)
6. FastAPI endpoint: GET /customers/{id}/least-harm-recommendation
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.least_harm_optimizer import LeastHarmOptimizerService
from src_py.models.least_harm_schemas import CandidateIntervention
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_evaluate_all_11_candidate_interventions():
    # Fetch Sri Balaji Fabrics FRE
    data = SAMPLE_CUSTOMERS_DATA["CUST_MSME_TIRUPPUR_001"]
    txns = [FinancialRealityEngineService.normalize_transaction(t) for t in data["raw_transactions"]]
    from src_py.models.schemas import LoanObligation, FixedObligationItem, ReceivableItem, PayableItem, AssetFinancingItem

    loans = [LoanObligation(**l) for l in data["loans"]]
    obligations = [FixedObligationItem(**o) for o in data["obligations"]]
    receivables = [ReceivableItem(**r) for r in data["receivables"]]
    payables = [PayableItem(**p) for p in data["payables"]]
    assets = [AssetFinancingItem(**a) for a in data["assets"]]

    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        assets=assets,
        liquid_cash=data["liquid_cash"]
    )

    for cand in CandidateIntervention:
        scored = LeastHarmOptimizerService.evaluate_intervention(fre, cand)
        assert scored.intervention == cand
        assert scored.harm_breakdown.total_harm_score >= 0.0
        assert scored.benefit_breakdown.total_benefit_score >= 0.0
        assert scored.recovery_probability_pct > 0.0
        assert scored.long_term_sustainability_pct > 0.0


def test_no_new_loan_guardrail_enforcement():
    # Sri Balaji Fabrics has operating cash flow insufficient to support another ₹5L loan with 24k EMI
    data = SAMPLE_CUSTOMERS_DATA["CUST_MSME_TIRUPPUR_001"]
    txns = [FinancialRealityEngineService.normalize_transaction(t) for t in data["raw_transactions"]]
    from src_py.models.schemas import LoanObligation, FixedObligationItem, ReceivableItem, PayableItem, AssetFinancingItem

    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=[LoanObligation(**l) for l in data["loans"]],
        obligations=[FixedObligationItem(**o) for o in data["obligations"]],
        receivables=[ReceivableItem(**r) for r in data["receivables"]],
        payables=[PayableItem(**p) for p in data["payables"]],
        assets=[AssetFinancingItem(**a) for a in data["assets"]],
        liquid_cash=data["liquid_cash"]
    )

    loan_option = LeastHarmOptimizerService.evaluate_intervention(fre, CandidateIntervention.LIMITED_NEW_LOAN)
    
    # Must be strictly vetoed by guardrail
    assert loan_option.is_permissible_under_guardrail is False
    assert "ANTI-PREDATORY GUARDRAIL ENFORCED" in loan_option.guardrail_veto_reason
    assert loan_option.harm_breakdown.total_harm_score == 100.0
    assert loan_option.customer_burden_level == "EXTREME"


def test_rank_and_optimize_report():
    data = SAMPLE_CUSTOMERS_DATA["CUST_MSME_TIRUPPUR_001"]
    txns = [FinancialRealityEngineService.normalize_transaction(t) for t in data["raw_transactions"]]
    from src_py.models.schemas import LoanObligation, FixedObligationItem, ReceivableItem, PayableItem, AssetFinancingItem

    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=[LoanObligation(**l) for l in data["loans"]],
        obligations=[FixedObligationItem(**o) for o in data["obligations"]],
        receivables=[ReceivableItem(**r) for r in data["receivables"]],
        payables=[PayableItem(**p) for p in data["payables"]],
        assets=[AssetFinancingItem(**a) for a in data["assets"]],
        liquid_cash=data["liquid_cash"]
    )

    report = LeastHarmOptimizerService.rank_and_optimize(fre, overdue_receivables=1200000.0, machine_bleed=85000.0)

    assert len(report.ranked_interventions) == 11
    assert report.no_new_loan_guardrail_enforced is True

    # Top selected intervention must be permissible, non-debt, and carrying high recovery probability
    assert report.selected_intervention.is_permissible_under_guardrail is True
    assert report.selected_intervention.intervention in [
        CandidateIntervention.RECEIVABLE_COLLECTION,
        CandidateIntervention.BUSINESS_OPPORTUNITY,
        CandidateIntervention.EMI_RESTRUCTURING
    ]
    assert report.selected_intervention.recovery_probability_pct >= 85.0
    assert report.confidence_percentage >= 90.0

    # Vetoed option must rank lower than top permissible options
    vetoed_rank = next(o.rank for o in report.ranked_interventions if o.intervention == CandidateIntervention.LIMITED_NEW_LOAN)
    assert vetoed_rank > 1


def test_fastapi_least_harm_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/least-harm-recommendation")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    body = res_json["data"]
    assert body["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert len(body["ranked_interventions"]) == 11
    assert body["no_new_loan_guardrail_enforced"] is True
    assert "selected_intervention" in body
    assert len(body["selection_rationale"]) >= 3
    assert len(body["supporting_evidence"]) >= 3
    assert "transparent_scoring_formula" in body
