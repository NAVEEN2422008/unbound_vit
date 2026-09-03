"""
Unit and integration tests for Root-Cause Analyzer (WHY) Engine Service.
Verifies:
1. Diagnosis across candidate causes:
   - revenue decline, customer/order decline, seasonality, industry downturn,
   - regional downturn, receivable delay, expense increase, debt overload, high EMI,
   - asset underperformance, low asset utilization, supplier cost increase, inventory pressure
2. Epistemic humility rule:
   - Uses 'likely contributor' rather than asserting proven causation
3. Evidence gathering and ranking of primary and secondary contributing causes
4. Example verification from specification:
   - Primary cause: Reduced business orders / customer/order decline
   - Evidence: Revenue -31%, Peer industry -8%, Order volume -34%
5. REST API: GET /api/v1/customers/{id}/root-cause
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date

from src_py.api.main import app
from src_py.services.root_cause_engine import RootCauseAnalyzerService
from src_py.models.root_cause_schemas import CandidateCauseEnum
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.models.schemas import LoanObligation, ReceivableItem

client = TestClient(app)


@pytest.fixture
def sample_fre_textile():
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "C_TEX", "timestamp": "2026-09-01T10:00:00",
            "amount": 280000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "T2", "customer_id": "C_TEX", "timestamp": "2026-09-02T10:00:00",
            "amount": 160000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_PAYROLL"
        })
    ]
    loans = [
        LoanObligation(
            id="L1", lender_name="HDFC Bank", loan_type="TERM",
            principal_amount=2000000, outstanding_principal=1600000,
            interest_rate_annual=11.5, monthly_emi=42000,
            nach_debit_day=10, tenure_months_remaining=30
        )
    ]
    receivables = [
        ReceivableItem(id="R1", invoice_number="INV_90", buyer_name="Buyer Corp", amount=140000, due_date=date(2026, 9, 25))
    ]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="C_TEX", customer_name="Sri Balaji Fabrics", archetype="MSME",
        transactions=txns, loans=loans, obligations=[], receivables=receivables,
        payables=[], assets=[], liquid_cash=35000.0
    )
    return fre


def test_specification_example_order_decline(sample_fre_textile):
    """
    Verifies the specification example:
    Primary cause: Reduced business orders
    Evidence: Revenue -31%, Peer industry -8%, Order volume -34%, Confidence > 80%
    """
    report = RootCauseAnalyzerService.analyze_root_causes(
        customer_id="C_TEX",
        fre=sample_fre_textile,
        revenue_decline_pct=31.0,
        order_volume_decline_pct=34.0,
        peer_industry_growth_pct=-8.0
    )

    # 1. Primary cause identification
    assert report.primary_cause.cause == CandidateCauseEnum.CUSTOMER_ORDER_DECLINE

    # 2. Epistemic humility requirement: Uses 'likely contributor' rather than asserting proven causation
    assert report.primary_cause.causality_classification == "likely contributor"
    assert "likely contributor" in report.primary_cause.causality_classification.lower()
    assert "proven cause" not in report.primary_cause.causality_classification.lower()

    # 3. Evidence items
    metrics = [e.metric for e in report.primary_cause.evidence]
    assert "order_volume_drop" in metrics
    observed_vals = [e.observed for e in report.primary_cause.evidence]
    assert "-34.0%" in observed_vals

    # 4. Confidence rating
    assert report.primary_cause.confidence >= 0.80

    # 5. Secondary causes present
    assert len(report.secondary_causes) > 0
    assert report.total_causes_evaluated == 13


def test_receivable_delay_root_cause(sample_fre_textile):
    # Customer with stable demand, but heavy receivable lockup
    report = RootCauseAnalyzerService.analyze_root_causes(
        customer_id="C_TEX",
        fre=sample_fre_textile,
        revenue_decline_pct=2.0,
        order_volume_decline_pct=0.0
    )

    # With high receivables (₹140k against ₹280k revenue), receivable delay must be top ranked
    assert report.primary_cause.cause == CandidateCauseEnum.RECEIVABLE_DELAY
    assert report.primary_cause.causality_classification == "likely contributor"
    assert any("trade_receivable_exposure" in e.metric for e in report.primary_cause.evidence)


def test_api_v1_root_cause_endpoint():
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/root-cause")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "primary_cause" in data
    assert data["primary_cause"]["causality_classification"] == "likely contributor"
    assert len(data["primary_cause"]["evidence"]) > 0
    assert data["total_causes_evaluated"] == 13
    assert 0.0 <= data["causation_confidence_level"] <= 1.0
    assert "epistemic_disclaimer" in data
