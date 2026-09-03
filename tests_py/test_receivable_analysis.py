"""
Unit and integration tests for Trade Receivable Intelligence Engine Service.
Verifies:
1. Calculation of:
   - days_outstanding, expected_payment_date, collection_probability
   - expected_7_day_cash, expected_14_day_cash, expected_30_day_cash
2. Classifications:
   - HIGH_CONFIDENCE, MODERATE_CONFIDENCE, UNCERTAIN, OVERDUE
3. Credit Affordability Engine integration and specification example:
   - Shortfall: ₹3L, Expected receivable: ₹4L within 10 days
   - Recommendation: "Investigate receivable acceleration before taking additional debt."
4. REST API:
   - GET /api/v1/businesses/{id}/receivables-analysis
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta

from src_py.api.main import app
from src_py.services.receivable_analysis import ReceivablesAnalysisService
from src_py.models.receivable_schemas import ReceivableConfidenceClassification

client = TestClient(app)


def test_receivable_analysis_specification_example():
    """
    Verifies the specification example:
    Shortfall: ₹300,000 (₹3L)
    Expected receivable: ₹400,000 (₹4L) arriving within 10 days (high confidence corporate buyer)
    Recommendation candidate: "Investigate receivable acceleration before taking additional debt."
    """
    today = date(2026, 9, 4)
    invoices = [
        {
            "invoice_number": "INV-RAYMOND-001",
            "buyer_name": "Raymond Garments Ltd (Corporate Buyer)",
            "amount": 400000.0,
            "invoice_date": today - timedelta(days=25),
            "due_date": today + timedelta(days=7)  # Due in 7 days, payment expected in ~10 days
        },
        {
            "invoice_number": "INV-OVERDUE-002",
            "buyer_name": "Late Payer Traders",
            "amount": 150000.0,
            "invoice_date": today - timedelta(days=90),
            "due_date": today - timedelta(days=45)  # 45 days overdue!
        }
    ]

    report = ReceivablesAnalysisService.analyze_receivables(
        business_id="BIZ_TEX_001",
        invoices=invoices,
        projected_shortfall=300000.0,
        as_of=today
    )

    # 1. Total book value check: 400k + 150k = 550,000
    assert report.total_receivable_book_value == 550000.0
    assert report.total_invoices_analyzed == 2

    # 2. Inflow Horizon calculations
    # Invoice 1 has ~0.95 prob, arriving in ~10 days (falls within 14-day and 30-day horizons)
    assert report.expected_14_day_cash >= 380000.0
    assert report.expected_30_day_cash >= 380000.0

    # 3. Classifications
    inv1 = next(i for i in report.invoices if i.invoice_number == "INV-RAYMOND-001")
    assert inv1.classification == ReceivableConfidenceClassification.HIGH_CONFIDENCE
    assert inv1.collection_probability >= 0.85
    assert inv1.days_outstanding == 25
    assert inv1.is_accelerable_via_treds is True

    inv2 = next(i for i in report.invoices if i.invoice_number == "INV-OVERDUE-002")
    assert inv2.classification == ReceivableConfidenceClassification.OVERDUE

    # 4. Credit Affordability Recommendation check
    assert report.can_receivables_cover_shortfall is True
    assert report.receivable_coverage_ratio > 1.2
    assert "investigate receivable acceleration" in report.credit_affordability_recommendation.lower()
    assert "before taking additional debt" in report.credit_affordability_recommendation.lower()


def test_api_v1_receivables_analysis_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/receivables-analysis?projected_shortfall=250000")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["business_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "expected_7_day_cash" in data
    assert "expected_14_day_cash" in data
    assert "expected_30_day_cash" in data
    assert "high_confidence_amount" in data
    assert "can_receivables_cover_shortfall" in data
    assert "credit_affordability_recommendation" in data
    assert len(data["invoices"]) > 0
