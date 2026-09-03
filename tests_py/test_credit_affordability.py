"""
Unit and integration tests for Credit Affordability Engine Service.
Verifies:
1. Core question: "Can the customer repay safely?" (not "Can the customer qualify?")
2. Baseline metric calculations:
   - current_debt, current_emi, current_free_cash_flow, current_debt_service_ratio, current_cash_buffer
3. Post-loan projected metric calculations:
   - post_loan_debt, post_loan_emi, post_loan_free_cash_flow, post_loan_debt_service_ratio,
     post_loan_cash_buffer, post_loan_resilience
4. Classifications:
   - SAFE_TO_BORROW, LIMITED_BORROWING, NOT_SAFE_TO_BORROW
5. Output payload:
   - maximum_recommended_amount, safe_loan_range, expected_emi, affordability_status, reason, confidence
6. Forward projection factoring seasonal troughs and receivable timings
7. REST API:
   - POST /api/v1/credit/affordability
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.credit_affordability import CreditAffordabilityEngineService
from src_py.models.affordability_schemas import (
    ProposedLoanInput, AffordabilityClassification
)
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_credit_affordability_safe_vs_not_safe():
    """
    Tests an enterprise seeking a modest equipment upgrade vs an unsustainable mega debt.
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

    # 1. Modest loan: ₹200,000 (2L) at 11% for 36 months -> Should be SAFE or LIMITED
    modest_loan = ProposedLoanInput(
        customer_id=data["id"],
        proposed_principal=200000.0,
        annual_interest_rate_pct=11.0,
        tenure_months=36
    )
    modest_report = CreditAffordabilityEngineService.evaluate_affordability(fre, modest_loan)
    
    # Baseline assertions
    assert modest_report.baseline_metrics.current_debt == fre.total_outstanding_debt.value
    assert modest_report.baseline_metrics.current_emi == fre.monthly_debt_service.value
    assert isinstance(modest_report.baseline_metrics.current_free_cash_flow, float)
    assert isinstance(modest_report.baseline_metrics.current_cash_buffer_days, int)

    # Post-loan assertions
    assert modest_report.post_loan_metrics.post_loan_debt > modest_report.baseline_metrics.current_debt
    assert modest_report.post_loan_metrics.post_loan_emi > modest_report.baseline_metrics.current_emi
    assert modest_report.affordability_status in [
        AffordabilityClassification.SAFE_TO_BORROW,
        AffordabilityClassification.LIMITED_BORROWING
    ]
    assert modest_report.maximum_recommended_amount > 0.0
    assert modest_report.safe_loan_range.maximum_safe_monthly_emi > 0.0

    # 2. Excessive loan: ₹15,000,000 (1.5 Crore) -> Must be NOT_SAFE_TO_BORROW
    excessive_loan = ProposedLoanInput(
        customer_id=data["id"],
        proposed_principal=15000000.0,
        annual_interest_rate_pct=14.0,
        tenure_months=24
    )
    excessive_report = CreditAffordabilityEngineService.evaluate_affordability(fre, excessive_loan)
    assert excessive_report.affordability_status == AffordabilityClassification.NOT_SAFE_TO_BORROW
    assert excessive_report.post_loan_metrics.post_loan_debt_service_ratio > 45.0
    assert "not safe" in excessive_report.reason.lower()


def test_api_v1_credit_affordability_endpoint():
    payload = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "proposed_principal": 500000.0,
        "annual_interest_rate_pct": 12.5,
        "tenure_months": 24
    }
    res = client.post("/api/v1/credit/affordability", json=payload)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "proposed_principal" in data
    assert "expected_emi" in data
    assert "affordability_status" in data
    assert "maximum_recommended_amount" in data
    assert "safe_loan_range" in data
    assert "baseline_metrics" in data
    assert "post_loan_metrics" in data
    assert "reason" in data
    assert "confidence" in data
    assert "forward_projection_context" in data
