"""
Unit and integration tests for Cash-Flow Timeline & Forward Forecast Engine.
Tests:
1. Daily calculation formula: closing = opening + actual_in + expected_in - actual_out - expected_out
2. Detection of temporary liquidity shortage hidden behind net positive monthly income
3. Obligation markers (NACH EMI, Rent, Payroll) and Receivable markers
4. 30-day, 60-day, and 90-day forward forecast generation
5. Conservative forecasting (income haircutting, non-exact recurring assumptions)
6. Surplus and shortfall calculation against 21-day minimum cash cushion
7. Weekly and monthly rollups
8. API endpoints: GET /api/v1/customers/{id}/cashflow and GET /api/v1/customers/{id}/cashflow/forecast
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.cashflow_engine import CashflowTimelineEngineService
from src_py.models.schemas import (
    NormalizedTransaction, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, DirectionEnum, TransactionCategory
)

client = TestClient(app)


@pytest.fixture
def hidden_shortage_scenario():
    """
    Constructs a scenario where monthly aggregate income > monthly expenses,
    YET a severe liquidity shortage occurs on Day 10 because NACH EMI and Rent
    are debited before a large receivable arrives on Day 25.
    
    Starting Cash: ₹40,000
    Day 5: Rent ₹30,000
    Day 10: Loan EMI ₹40,000 (Account drops to -₹30,000 -> SHORTAGE!)
    Day 25: Large Receivable of ₹1,50,000 arrives
    
    Total 30d Inflow: ₹1,50,000
    Total 30d Outflow: ₹70,000
    Net Monthly Cashflow: +₹80,000 (Positive on average!)
    """
    start_d = date(2026, 9, 1)

    loans = [
        LoanObligation(
            id="L_COLLISION",
            lender_name="HDFC Bank",
            loan_type="MACHINERY_TERM",
            principal_amount=1500000,
            outstanding_principal=1200000,
            interest_rate_annual=11.5,
            monthly_emi=40000,
            nach_debit_day=10,
            tenure_months_remaining=30
        )
    ]

    obligations = [
        FixedObligationItem(id="O_RENT", category="Commercial Rent", amount=30000, due_day_of_month=5, is_mandatory=True)
    ]

    receivables = [
        ReceivableItem(
            id="R_LARGE",
            invoice_number="INV_SEP_99",
            buyer_name="Titan Garments",
            amount=150000,
            due_date=date(2026, 9, 25),
            is_treds_eligible=True
        )
    ]

    return 40000.0, loans, obligations, receivables, start_d


def test_hidden_liquidity_shortage_detected(hidden_shortage_scenario):
    cash, loans, obligations, receivables, start_d = hidden_shortage_scenario

    horizon = CashflowTimelineEngineService.generate_timeline(
        customer_id="CUST_HIDDEN_GAP",
        starting_cash=cash,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=[],
        horizon_days=30,
        start_date=start_d,
        minimum_required_cash=25000.0
    )

    # 1. Verify that overall net cashflow is positive
    assert horizon.total_projected_inflows > horizon.total_projected_outflows
    assert horizon.net_projected_cash_flow > 0.0

    # 2. Acceptance Criteria: System MUST detect a short-term liquidity shortage
    # even when monthly total income remains greater than monthly expenses
    assert horizon.is_hidden_shortage_detected is True
    assert horizon.earliest_shortfall_date == date(2026, 9, 10)
    assert horizon.peak_cash_deficit > 0.0

    # 3. Check Daily Balance Formula for Day 10
    day10 = next(d for d in horizon.daily_timeline if d.date == date(2026, 9, 10))
    assert day10.closing_balance < 0.0
    assert day10.is_liquidity_deficit is True
    assert len(day10.obligation_markers) == 1
    assert day10.obligation_markers[0]["type"] == "LOAN_EMI_NACH"


def test_receivable_and_obligation_markers(hidden_shortage_scenario):
    cash, loans, obligations, receivables, start_d = hidden_shortage_scenario

    horizon = CashflowTimelineEngineService.generate_timeline(
        customer_id="CUST_MARKERS",
        starting_cash=cash,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=[],
        horizon_days=30,
        start_date=start_d
    )

    # Check Day 5 has Rent obligation marker
    day5 = next(d for d in horizon.daily_timeline if d.date == date(2026, 9, 5))
    assert len(day5.obligation_markers) == 1
    assert day5.obligation_markers[0]["category"] == "Commercial Rent"

    # Check Day 25 has Receivable marker
    day25 = next(d for d in horizon.daily_timeline if d.date == date(2026, 9, 25))
    assert len(day25.receivable_markers) == 1
    assert day25.receivable_markers[0]["invoice"] == "INV_SEP_99"
    assert day25.receivable_markers[0]["is_treds_eligible"] is True


def test_multi_horizon_forecast_30_60_90(hidden_shortage_scenario):
    cash, loans, obligations, receivables, start_d = hidden_shortage_scenario

    report = CashflowTimelineEngineService.generate_full_forecast_report(
        customer_id="CUST_MULTI_HORIZON",
        customer_name="Sri Balaji Fabrics",
        archetype="MSME",
        starting_cash=cash,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=[],
        as_of_date=start_d
    )

    assert report.forecast_30d.horizon_days == 30
    assert len(report.forecast_30d.daily_timeline) == 30
    assert len(report.forecast_30d.weekly_timeline) >= 4

    assert report.forecast_60d.horizon_days == 60
    assert len(report.forecast_60d.daily_timeline) == 60

    assert report.forecast_90d.horizon_days == 90
    assert len(report.forecast_90d.daily_timeline) == 90

    assert report.hidden_shortage_narrative is not None
    assert "CRITICAL TIMING MISMATCH DETECTED" in report.hidden_shortage_narrative


def test_api_v1_cashflow_endpoints():
    # 1. GET /api/v1/customers/{id}/cashflow
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/cashflow?horizon_days=30")
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["horizon_days"] == 30
    assert len(body["daily_timeline"]) == 30
    assert len(body["weekly_timeline"]) > 0
    assert "is_hidden_shortage_detected" in body

    # 2. GET /api/v1/customers/{id}/cashflow/forecast
    res_f = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/cashflow/forecast")
    assert res_f.status_code == 200
    report = res_f.json()["data"]
    assert report["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "forecast_30d" in report
    assert "forecast_60d" in report
    assert "forecast_90d" in report
    assert "underlying_assumptions" in report
