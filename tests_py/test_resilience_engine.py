"""
Unit and acceptance tests for Financial Resilience Score Engine Service.
Verifies:
1. 0-100 Financial Resilience Score calculation across 7 dimensions:
   - income stability, cash-flow stability, debt burden, savings/cash buffer,
   - repayment behavior, expense stability, business health
2. Mandatory Acceptance Criteria:
   - A customer with: stable income, low debt, high cash buffer, stable repayment
     MUST score higher than a customer with: volatile income, high debt, low cash buffer, repeated payment issues.
3. Institutional Demarcation:
   - Explicit naming as "Financial Resilience Score" (NOT a regulatory credit score).
4. Output payload integrity:
   - overall_score, component_scores, trend, explanation, confidence
5. REST API:
   - GET /api/v1/customers/{id}/financial-resilience
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.resilience_engine import FinancialResilienceEngineService

client = TestClient(app)


def test_financial_resilience_acceptance_criteria():
    """
    Verifies acceptance criteria:
    A customer with:
    - stable income (volatility 4%)
    - low debt (DSR 18%)
    - high cash buffer (55 days)
    - stable repayment (100% on-time)
    MUST score higher than a customer with:
    - volatile income (volatility 32%)
    - high debt (DSR 58%)
    - low cash buffer (6 days)
    - repeated payment issues (70% on-time).
    """
    # 1. Resilient Customer
    healthy_report = FinancialResilienceEngineService.compute_resilience_score(
        customer_id="CUST_HEALTHY",
        customer_name="Stable Textiles Pvt Ltd",
        income_volatility_pct=4.0,
        negative_balance_days=0,
        debt_service_ratio_pct=18.0,
        cash_buffer_days=55,
        repayment_ontime_rate_pct=100.0,
        expense_growth_rate_pct=3.0,
        receivable_turnover_days=32
    )

    # 2. Vulnerable Customer
    vulnerable_report = FinancialResilienceEngineService.compute_resilience_score(
        customer_id="CUST_VULNERABLE",
        customer_name="Struggling Looms",
        income_volatility_pct=32.0,
        negative_balance_days=8,
        debt_service_ratio_pct=58.0,
        cash_buffer_days=6,
        repayment_ontime_rate_pct=70.0,
        expense_growth_rate_pct=24.0,
        receivable_turnover_days=85
    )

    # Acceptance check: healthy must score significantly higher than vulnerable
    assert healthy_report.overall_score > vulnerable_report.overall_score
    assert healthy_report.overall_score >= 75.0
    assert vulnerable_report.overall_score <= 40.0

    # Trend checks
    assert healthy_report.trend in ["STABLE", "IMPROVING"]
    assert vulnerable_report.trend == "DETERIORATING"

    # Regulatory demarcation check
    assert "Financial Resilience Score" in healthy_report.metric_naming_notice
    assert "NOT a regulatory or bureau credit score" in healthy_report.metric_naming_notice


def test_component_scores_populated():
    report = FinancialResilienceEngineService.compute_resilience_score(
        customer_id="CUST_COMPONENTS",
        customer_name="Precision Spares",
        income_volatility_pct=8.0,
        debt_service_ratio_pct=30.0,
        cash_buffer_days=28
    )

    comps = report.component_scores
    assert 0.0 <= comps.income_stability <= 100.0
    assert 0.0 <= comps.cashflow_stability <= 100.0
    assert 0.0 <= comps.debt_burden <= 100.0
    assert 0.0 <= comps.savings_cash_buffer <= 100.0
    assert 0.0 <= comps.repayment_behavior <= 100.0
    assert 0.0 <= comps.expense_stability <= 100.0
    assert 0.0 <= comps.business_health <= 100.0


def test_api_v1_financial_resilience_endpoint():
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/financial-resilience")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "overall_score" in data
    assert 0.0 <= data["overall_score"] <= 100.0
    assert "component_scores" in data
    assert "trend" in data
    assert "explanation" in data
    assert "metric_naming_notice" in data
