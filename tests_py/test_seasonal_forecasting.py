"""
Unit and integration tests for Seasonal Forecasting Engine Service.
Verifies:
1. Learning seasonal patterns from historical data using moving average decomposition
   and multiplicative seasonal indices.
2. Generating 12-month forward projection with:
   - expected_revenue, expected_expense, expected_cashflow
   - seasonal_index
   - confidence intervals (lower and upper bounds)
   - confidence score
3. Responsible probabilistic phrasing:
   - "Historical pattern indicates higher/subdued expected revenue"
   - Never says "Revenue will definitely increase"
4. Fallback behavior:
   - When customer history is insufficient (<24 months), falls back to peer/industry data
   - Calibrates confidence downwards
5. REST API: GET /api/v1/businesses/{id}/seasonal-forecast
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.seasonal_forecasting import SeasonalForecastingService
from src_py.models.seasonal_schemas import ForecastDataSource

client = TestClient(app)


def test_learned_seasonal_patterns_from_history():
    """
    Simulates 36 months of customer-level history for a business with high winter peak
    (e.g., Nov-Jan) and summer trough.
    Verifies that the engine LEARNS the seasonal patterns dynamically.
    """
    # 36 months of synthetic revenue (Base: 2,000,000)
    # Seasonal multipliers: Q1 ~ 1.1, Q2 ~ 0.85, Q3 ~ 0.90, Q4 ~ 1.25
    monthly_series = []
    multipliers = [1.15, 1.10, 1.05, 0.85, 0.80, 0.82, 0.85, 0.92, 1.02, 1.18, 1.28, 1.22]
    for year in range(3):
        for m in range(12):
            val = 2000000.0 * multipliers[m] * (1.0 + (year * 0.05))  # 5% annual growth
            monthly_series.append(val)

    report = SeasonalForecastingService.generate_seasonal_forecast(
        customer_id="CUST_SEASONAL_01",
        customer_name="Seasonal Apparels Ltd",
        industry="TEXTILES",
        region="TAMIL_NADU",
        customer_historical_revenue=monthly_series,
        start_month=1,
        start_year=2026
    )

    # 1. Verify Data Source: Learned from customer history
    assert report.data_source == ForecastDataSource.CUSTOMER_HISTORY
    assert report.months_of_history_analyzed == 36
    assert report.overall_confidence >= 0.88

    # 2. Verify 12-month projections
    assert len(report.monthly_forecasts) == 12

    # 3. Check Peak and Trough Identification
    # Nov (month 11) and Dec (month 12) must have high seasonal indices (> 1.15)
    nov_forecast = next(f for f in report.monthly_forecasts if f.month_index == 11)
    assert nov_forecast.seasonal_index > 1.15
    assert nov_forecast.expected_revenue > 2000000.0

    # May (month 5) must have low seasonal index (< 0.90)
    may_forecast = next(f for f in report.monthly_forecasts if f.month_index == 5)
    assert may_forecast.seasonal_index < 0.90

    # 4. Check Confidence Intervals
    for f in report.monthly_forecasts:
        assert f.revenue_lower_bound < f.expected_revenue < f.revenue_upper_bound
        assert f.cashflow_lower_bound < f.expected_cashflow < f.cashflow_upper_bound

    # 5. Check Phrasing: Strictly probabilistic language
    # Must NOT say "will definitely increase"
    assert "will definitely" not in report.executive_narrative.lower()
    for f in report.monthly_forecasts:
        assert "will definitely" not in f.interpretive_note.lower()
        assert "historical pattern indicates" in f.interpretive_note.lower()


def test_fallback_to_peer_industry_when_insufficient_history():
    """
    When customer history is under 24 months (or zero),
    the system must fallback to peer/industry data and reduce confidence.
    """
    short_history = [2200000.0, 2100000.0, 2300000.0]  # Only 3 months!

    report = SeasonalForecastingService.generate_seasonal_forecast(
        customer_id="CUST_NEW",
        customer_name="New Knitwear",
        industry="TEXTILES",
        customer_historical_revenue=short_history,
        base_monthly_revenue=2400000.0
    )

    # Must fall back to PEER_INDUSTRY_FALLBACK
    assert report.data_source == ForecastDataSource.PEER_INDUSTRY_FALLBACK
    # Confidence must be reduced
    assert report.overall_confidence < 0.85
    assert len(report.monthly_forecasts) == 12
    assert "PEER_INDUSTRY_FALLBACK" in report.executive_narrative


def test_api_v1_seasonal_forecast_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/seasonal-forecast?months_of_history=36")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert len(data["monthly_forecasts"]) == 12
    assert "overall_confidence" in data
    assert "peak_season_months" in data
    assert "trough_season_months" in data
    assert "probabilistic_disclaimer" in data
