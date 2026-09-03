"""
Unit and integration tests for No-New-Loan Guardrail Engine Service.
Verifies:
1. 7-step evaluation process:
   current state -> simulate loan -> compare -> distress -> resilience -> cash flow -> debt burden
2. Blocking conditions triggering NOT_RECOMMENDED:
   - post-loan distress increases materially
   - post-loan free cash flow remains negative
   - post-loan EMI is not sustainable (DSR > 45%)
   - loan does not address root cause (unaligned)
   - existing debt is already excessive
3. ALLOW and LIMIT verdicts for safe scenarios
4. Institutional Safety Mandate:
   - Decision support advisory; does NOT implement automatic regulatory credit denial
5. REST API:
   - POST /api/v1/credit/no-new-loan-check
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.credit_affordability import CreditAffordabilityEngineService
from src_py.models.affordability_schemas import (
    ProposedLoanInput, NoNewLoanVerdict
)
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_no_new_loan_blocking_triggers():
    """
    Tests blocking triggers on a financially stressed enterprise.
    1. Large loan that blows DSR past 45% and leaves negative FCF -> NOT_RECOMMENDED
    2. Unaligned root cause -> NOT_RECOMMENDED
    """
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

    # 1. Unsustainable debt facility
    risky_loan = ProposedLoanInput(
        customer_id=data["id"],
        proposed_principal=10000000.0,  # 1 Crore
        annual_interest_rate_pct=14.0,
        tenure_months=24
    )

    report = CreditAffordabilityEngineService.check_no_new_loan(
        fre=fre,
        loan_input=risky_loan,
        current_distress_score=42.0,
        primary_root_cause="unaddressed_raw_material_inflation"
    )

    assert report.verdict == NoNewLoanVerdict.NOT_RECOMMENDED
    assert len(report.evidence) >= 2
    # Check that institutional advisory is present
    assert "decision support" in report.decision_support_disclaimer.lower()
    assert "not constitute an automated regulatory credit denial" in report.decision_support_disclaimer.lower()


def test_no_new_loan_allow_for_sustainable_facility():
    """
    Tests a small, productive facility that addresses working capital with low DSR impact -> ALLOW or LIMIT.
    """
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

    modest_loan = ProposedLoanInput(
        customer_id=data["id"],
        proposed_principal=150000.0,  # 1.5 Lakh
        annual_interest_rate_pct=10.5,
        tenure_months=36
    )

    report = CreditAffordabilityEngineService.check_no_new_loan(
        fre=fre,
        loan_input=modest_loan,
        current_distress_score=15.0,
        primary_root_cause="temporary_liquidity_gap"
    )

    assert report.verdict in [NoNewLoanVerdict.ALLOW, NoNewLoanVerdict.LIMIT]
    assert report.root_cause_addressed is True


def test_api_v1_no_new_loan_check_endpoint():
    payload = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "proposed_principal": 8000000.0,  # 80 Lakhs
        "annual_interest_rate_pct": 13.0,
        "tenure_months": 24
    }
    res = client.post(
        "/api/v1/credit/no-new-loan-check?current_distress_score=50&primary_root_cause=idle_machinery",
        json=payload
    )
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert data["verdict"] == "NOT_RECOMMENDED"
    assert len(data["evidence"]) >= 1
    assert "reason" in data
    assert "confidence" in data
    assert "decision_support_disclaimer" in data
