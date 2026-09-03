"""
Pytest unit tests for Financial Reality Engine.
Verifies:
1. Transaction normalization and timestamp preservation
2. Daily/weekly cash flow trajectory and collision date identification
3. Ratios calculation: Net income, FCF, DSR, expense ratio, savings rate, cash buffer
4. Value provenance distinction (ACTUAL vs PREDICTED vs ESTIMATED)
5. Missing data handling & data completeness metric degradation
6. FastAPI endpoints: GET /customers/{id}/financial-reality, GET /customers/{id}/cashflow, POST /financial-reality/recalculate
"""
import pytest
from datetime import datetime, date, timedelta
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.models.schemas import (
    DirectionEnum, TransactionCategory, ValueProvenance,
    LoanObligation, FixedObligationItem, ReceivableItem, PayableItem, AssetFinancingItem
)

client = TestClient(app)


def test_transaction_normalization():
    raw = {
        "id": "TXN_TEST_101",
        "customer_id": "CUST_TEST",
        "timestamp": "2026-09-04T11:20:00",
        "amount": 250000.0,
        "direction": "INFLOW",
        "category": "INCOME_BUSINESS",
        "narration": "NEFT: Cotton Export Settlement",
        "channel": "NEFT"
    }
    normalized = FinancialRealityEngineService.normalize_transaction(raw)
    assert normalized.id == "TXN_TEST_101"
    assert normalized.amount == 250000.0
    assert normalized.direction == DirectionEnum.INFLOW
    assert normalized.category == TransactionCategory.INCOME_BUSINESS
    assert normalized.timestamp.year == 2026
    assert normalized.provenance == ValueProvenance.ACTUAL


def test_cashflow_timeline_and_collision_detection():
    loans = [
        LoanObligation(
            id="L1", lender_name="SBI", loan_type="TERM",
            principal_amount=1000000, outstanding_principal=800000,
            interest_rate_annual=11.0, monthly_emi=50000,
            nach_debit_day=10, tenure_months_remaining=20
        )
    ]
    obligations = [
        FixedObligationItem(id="O1", category="Rent", amount=30000, due_day_of_month=5, is_mandatory=True)
    ]
    receivables = [
        ReceivableItem(
            id="R1", invoice_number="INV_1", buyer_name="Buyer Corp",
            amount=40000, due_date=date(2026, 9, 20)
        )
    ]
    
    start_d = date(2026, 9, 1)
    summary = FinancialRealityEngineService.calculate_cashflow_timeline(
        customer_id="CUST_TEST",
        starting_cash=60000.0,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=[],
        horizon_days=30,
        start_date=start_d
    )
    
    assert len(summary.daily_timeline) == 30
    assert summary.daily_timeline[0].opening_balance == 60000.0
    # Day 5: Rent -₹30,000 -> balance ₹30,000
    # Day 10: EMI -₹50,000 -> balance -₹20,000 (Collision occurs!)
    assert summary.projected_shortfall_date == date(2026, 9, 10)
    assert summary.projected_shortfall_amount >= 20000.0
    assert len(summary.weekly_net_flows) >= 4


def test_financial_reality_provenance_and_ratios():
    loans = [
        LoanObligation(
            id="L1", lender_name="HDFC", loan_type="WORKING_CAPITAL",
            principal_amount=2000000, outstanding_principal=1500000,
            interest_rate_annual=12.0, monthly_emi=45000,
            nach_debit_day=15, tenure_months_remaining=12
        )
    ]
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "CUST_1", "timestamp": "2026-09-01T10:00:00",
            "amount": 250000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "T2", "customer_id": "CUST_1", "timestamp": "2026-09-02T10:00:00",
            "amount": 120000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_PAYROLL"
        })
    ]

    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="CUST_1",
        customer_name="Precision Spares",
        archetype="MSME",
        transactions=txns,
        loans=loans,
        obligations=[],
        receivables=[],
        payables=[],
        assets=[],
        liquid_cash=90000.0
    )

    # 1. Income: ₹250,000 ACTUAL
    assert fre.monthly_income.value == 250000.0
    assert fre.monthly_income.provenance == ValueProvenance.ACTUAL

    # 2. Net Income: 250,000 - 120,000 - 45,000 = 85,000
    assert fre.net_income.value == 85000.0
    assert fre.free_cash_flow.value == 85000.0

    # 3. DSR: 45,000 / 250,000 = 0.18 (18%)
    assert fre.debt_service_ratio.value == 0.18
    assert fre.expense_ratio.value == 0.48

    # 4. Cash Buffer: 90,000 / (165,000 / 30) = 16 days
    assert fre.cash_buffer_days.value == 16


def test_missing_data_degradation():
    # If customer provides NO transactions (missing bank feed)
    fre_missing = FinancialRealityEngineService.compute_financial_reality(
        customer_id="CUST_MISSING",
        customer_name="Unbanked Trader",
        archetype="TRADER",
        transactions=[],  # Missing!
        loans=[],         # Missing!
        obligations=[],
        receivables=[],
        payables=[],
        assets=[],
        liquid_cash=10000.0
    )
    # Provenance must fall back to ESTIMATED
    assert fre_missing.monthly_income.provenance == ValueProvenance.ESTIMATED
    assert fre_missing.data_quality.completeness_percentage < 60.0
    assert "bank_transactions_feed" in fre_missing.data_quality.missing_fields
    assert fre_missing.data_quality.reliability_level in ["MODERATE", "LOW"]


def test_fastapi_health_endpoint():
    res = client.get("/health")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    assert res_json["data"]["status"] == "HEALTHY"


def test_fastapi_get_financial_reality():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/financial-reality")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    body = res_json["data"]
    assert body["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert body["monthly_income"]["value"] == 2800000.0
    assert body["monthly_debt_service"]["value"] == 320000.0
    assert body["debt_service_ratio"]["value"] > 0
    assert "explanation_summary" in body
    assert len(body["key_vulnerabilities"]) > 0


def test_fastapi_get_cashflow():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/cashflow?horizon_days=30")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    body = res_json["data"]
    assert len(body["daily_timeline"]) == 30
    assert "projected_shortfall_date" in body
    assert body["monthly_inflow"] > 0


def test_fastapi_recalculate_what_if():
    # Simulate a 25% revenue collapse
    req = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "simulated_income_delta_pct": -25.0
    }
    res = client.post("/financial-reality/recalculate", json=req)
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    body = res_json["data"]
    # Baseline was 2,800,000 -> -25% is 2,100,000
    assert body["monthly_income"]["value"] == 2100000.0
    assert body["monthly_income"]["provenance"] == "PREDICTED"


@pytest.fixture
def sample_entities():
    loans = [
        LoanObligation(
            id="L1", lender_name="HDFC", loan_type="WORKING_CAPITAL",
            principal_amount=2000000, outstanding_principal=1500000,
            interest_rate_annual=12.0, monthly_emi=45000,
            nach_debit_day=15, tenure_months_remaining=12
        )
    ]
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "CUST_DET_01", "timestamp": "2026-09-01T10:00:00",
            "amount": 250000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "T2", "customer_id": "CUST_DET_01", "timestamp": "2026-09-02T10:00:00",
            "amount": 120000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_PAYROLL"
        })
    ]
    obligations = [FixedObligationItem(id="O1", category="Rent", amount=15000, due_day_of_month=5, is_mandatory=True)]
    receivables = [ReceivableItem(id="R1", invoice_number="INV_10", buyer_name="Buyer X", amount=150000, due_date=date(2026, 9, 25))]
    payables = [PayableItem(id="P1", vendor_name="Vendor Y", amount=60000, due_date=date(2026, 9, 28))]
    assets = [AssetFinancingItem(id="A1", asset_name="Machine 1", asset_type="MACHINE", purchase_cost=800000)]
    return txns, loans, obligations, receivables, payables, assets


def test_compute_financial_state_deterministic(sample_entities):
    txns, loans, obligations, receivables, payables, assets = sample_entities
    
    # First computation
    state1 = FinancialRealityEngineService.compute_financial_state(
        customer_id="CUST_DET_01",
        customer_name="Precision Spindles",
        archetype="MSME",
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        liquid_cash=90000.0
    )

    # Second computation with identical input
    state2 = FinancialRealityEngineService.compute_financial_state(
        customer_id="CUST_DET_01",
        customer_name="Precision Spindles",
        archetype="MSME",
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        liquid_cash=90000.0
    )

    # Acceptance Criteria: Given the same normalized data, the engine must produce deterministic results
    assert state1.income.total_income == state2.income.total_income
    assert state1.expenses.total_expenses == state2.expenses.total_expenses
    assert state1.debt.total_debt == state2.debt.total_debt
    assert state1.debt.monthly_debt_service == 45000.0
    assert state1.cashflow.net_cash_flow == state2.cashflow.net_cash_flow
    assert state1.cashflow.free_cash_flow == state2.cashflow.free_cash_flow
    assert state1.metrics.debt_service_ratio == state2.metrics.debt_service_ratio
    assert state1.current_cash == 90000.0
    assert state1.receivables.total_receivables == 150000.0
    assert state1.payables.total_payables == 60000.0
    # Multi-resolution time series checks
    assert len(state1.cashflow.time_series.daily) == 30
    assert len(state1.cashflow.time_series.weekly) > 0
    assert len(state1.cashflow.time_series.monthly) == 1


def test_api_v1_financial_reality_endpoints():
    # 1. GET /api/v1/customers/{id}/financial-reality
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-reality")
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "income" in data
    assert "expenses" in data
    assert "debt" in data
    assert "current_cash" in data
    assert "receivables" in data
    assert "payables" in data
    assert "cashflow" in data
    assert "metrics" in data
    assert "data_quality" in data
    assert "daily" in data["cashflow"]["time_series"]
    assert "weekly" in data["cashflow"]["time_series"]
    assert "monthly" in data["cashflow"]["time_series"]

    # 2. GET /api/v1/customers/{id}/financial-reality/metrics
    res_m = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-reality/metrics")
    assert res_m.status_code == 200
    metrics = res_m.json()["data"]
    assert "debt_service_ratio" in metrics
    assert "expense_ratio" in metrics
    assert "savings_rate" in metrics
    assert "dscr" in metrics
    assert "foir" in metrics

    # 3. POST /api/v1/customers/{id}/financial-reality/recalculate
    res_r = client.post("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-reality/recalculate", json={
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "simulated_income_delta_pct": -20.0
    })
    assert res_r.status_code == 200
    rec_data = res_r.json()["data"]
    assert rec_data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert rec_data["income"]["total_income"] > 0

