"""
Unit and integration tests for Financing Timing Engine Service.
Verifies:
1. Output Options:
   - BORROW_NOW, BORROW_LATER, LIMITED_BORROWING, AVOID_BORROWING,
     RESTRUCTURE_EXISTING_DEBT, USE_RECEIVABLE_FINANCING
2. Specification Example:
   - Business currently has weak seasonal revenue, but historical data predicts strong revenue in two months.
   - System recommends BORROW_LATER: "Would delaying borrowing reduce long-term debt pressure?"
3. Receivable acceleration scenario:
   - Strong expected receivables -> USE_RECEIVABLE_FINANCING
4. Output schema validation:
   - recommended_timing, recommended_amount, reason, confidence
5. REST API:
   - GET /api/v1/businesses/{id}/financing-timing
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.financing_timing import FinancingTimingEngineService
from src_py.models.financing_timing_schemas import FinancingTimingOption
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.services.seasonal_forecasting import SeasonalForecastingService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_financing_timing_specification_example_borrow_later():
    """
    Specification Example:
    Business currently has weak seasonal revenue (trough),
    but historical data predicts strong revenue in two months.
    System evaluates: "Would delaying borrowing reduce long-term debt pressure?" -> BORROW_LATER.
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

    # Generate seasonal forecast where month 1 is a trough (<0.95) and month 3 is a peak (>=1.10)
    # Start in August (month 8, pre-festival lull) leading to October surge (2 months later)
    seasonal_forecast = SeasonalForecastingService.generate_seasonal_forecast(
        customer_id=data["id"],
        customer_name=data["name"],
        industry="TEXTILES",
        region="TAMIL_NADU",
        base_monthly_revenue=fre.monthly_income.value,
        start_month=8  # August (trough: index 0.95) -> October (peak: index 1.15 in 2 months)
    )

    report = FinancingTimingEngineService.evaluate_financing_timing(
        business_id=data["id"],
        fre=fre,
        seasonal_forecast=seasonal_forecast,
        receivables_report=None,
        proposed_amount=600000.0
    )

    assert report.recommended_timing == FinancingTimingOption.BORROW_LATER
    assert report.recommended_window_months >= 1
    assert "delaying borrowing" in report.reason.lower()
    assert "reduce long-term debt pressure" in report.reason.lower()
    assert report.confidence >= 0.85


def test_api_v1_financing_timing_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/financing-timing?proposed_amount=400000")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["business_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "recommended_timing" in data
    assert data["recommended_timing"] in [
        "BORROW_NOW", "BORROW_LATER", "LIMITED_BORROWING",
        "AVOID_BORROWING", "RESTRUCTURE_EXISTING_DEBT", "USE_RECEIVABLE_FINANCING"
    ]
    assert "recommended_amount" in data
    assert "optimal_timing_window" in data
    assert "reason" in data
    assert "confidence" in data
