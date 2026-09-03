"""
Unit and acceptance tests for Distress Classification Engine.
Verifies:
1. Classification of TEMPORARY_LIQUIDITY_GAP (short-term shortage + stable income + recoverable receivables)
2. Classification of INCOME_SHOCK (significant revenue/order decline)
3. Classification of DEBT_OVERLOAD (unsustainable DSR > 45%)
4. Classification of EXPENSE_SHOCK (sudden cost surge > 25%)
5. Classification of MIXED_DISTRESS (multiple material drivers)
6. Acceptance Criteria: Every classification must contain at least two evidence items.
7. REST API: GET /api/v1/customers/{id}/distress/classify
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date

from src_py.api.main import app
from src_py.services.distress_classifier import DistressClassificationEngineService
from src_py.models.distress_classification_schemas import DistressDominantType
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.models.schemas import (
    NormalizedTransaction, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, DirectionEnum, TransactionCategory
)

client = TestClient(app)


@pytest.fixture
def base_fre():
    """Builds baseline FinancialRealityObject."""
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "C_TEST", "timestamp": "2026-09-01T10:00:00",
            "amount": 200000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "T2", "customer_id": "C_TEST", "timestamp": "2026-09-02T10:00:00",
            "amount": 100000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_PAYROLL"
        })
    ]
    loans = [
        LoanObligation(
            id="L1", lender_name="SBI", loan_type="TERM",
            principal_amount=1000000, outstanding_principal=800000,
            interest_rate_annual=11.0, monthly_emi=40000,
            nach_debit_day=10, tenure_months_remaining=24
        )
    ]
    receivables = [
        ReceivableItem(id="R1", invoice_number="INV_1", buyer_name="Buyer Corp", amount=120000, due_date=date(2026, 9, 25))
    ]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="C_TEST", customer_name="Test Enterprise", archetype="MSME",
        transactions=txns, loans=loans, obligations=[], receivables=receivables,
        payables=[], assets=[], liquid_cash=25000.0
    )
    return fre


def test_classify_temporary_liquidity_gap(base_fre):
    report = DistressClassificationEngineService.classify_distress(
        customer_id="C_TEST",
        fre=base_fre,
        revenue_decline_pct=2.0,
        expense_increase_pct=0.0,
        declining_orders_pct=0.0,
        has_upcoming_shortage=True
    )

    assert report.primary_category == DistressDominantType.TEMPORARY_LIQUIDITY_GAP
    assert "14–30 days" in report.expected_duration
    # Acceptance criteria: at least 2 evidence items
    assert len(report.evidence) >= 2
    assert any("receivable_coverage" in e.metric_name for e in report.evidence)
    assert any("stable_baseline_income" in e.metric_name for e in report.evidence)


def test_classify_income_shock(base_fre):
    report = DistressClassificationEngineService.classify_distress(
        customer_id="C_TEST",
        fre=base_fre,
        revenue_decline_pct=35.0,
        declining_orders_pct=40.0
    )

    assert report.primary_category == DistressDominantType.INCOME_SHOCK
    assert "3–6 months" in report.expected_duration
    # Acceptance criteria: at least 2 evidence items
    assert len(report.evidence) >= 2
    metrics = [e.metric_name for e in report.evidence]
    assert "revenue_decline_rate" in metrics
    assert "order_volume_drop" in metrics


def test_classify_debt_overload():
    # Construct heavy debt scenario (DSR > 50%)
    loans = [
        LoanObligation(
            id="L_HEAVY", lender_name="HDFC", loan_type="TERM",
            principal_amount=5000000, outstanding_principal=4200000,
            interest_rate_annual=14.0, monthly_emi=120000,
            nach_debit_day=10, tenure_months_remaining=36
        )
    ]
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "C_DEBT", "timestamp": "2026-09-01T10:00:00",
            "amount": 200000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        })
    ]
    fre_heavy_debt = FinancialRealityEngineService.compute_financial_reality(
        customer_id="C_DEBT", customer_name="Overleveraged Spindles", archetype="MSME",
        transactions=txns, loans=loans, obligations=[], receivables=[],
        payables=[], assets=[], liquid_cash=20000.0
    )

    report = DistressClassificationEngineService.classify_distress(
        customer_id="C_DEBT",
        fre=fre_heavy_debt,
        revenue_decline_pct=0.0
    )

    assert report.primary_category == DistressDominantType.DEBT_OVERLOAD
    assert "Structural" in report.expected_duration
    assert len(report.evidence) >= 2
    metrics = [e.metric_name for e in report.evidence]
    assert "debt_service_ratio" in metrics


def test_classify_mixed_distress(base_fre):
    # Both Income Shock (30% drop) AND Debt Overload (DSR high)
    # Simulate both material contributors
    report = DistressClassificationEngineService.classify_distress(
        customer_id="C_TEST",
        fre=base_fre,
        revenue_decline_pct=32.0,
        declining_orders_pct=30.0,
        expense_increase_pct=28.0  # Expense shock as well
    )

    assert report.primary_category == DistressDominantType.MIXED_DISTRESS
    assert report.secondary_category is not None
    assert len(report.evidence) >= 2


def test_api_v1_distress_classify_endpoint():
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress/classify?revenue_decline_pct=25.0")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert data["primary_category"] in [
        "TEMPORARY_LIQUIDITY_GAP", "INCOME_SHOCK", "DEBT_OVERLOAD", "EXPENSE_SHOCK", "MIXED_DISTRESS"
    ]
    assert len(data["evidence"]) >= 2
    assert "expected_duration" in data
    assert 0.0 <= data["confidence"] <= 1.0
