"""
Tests for Longitudinal Distress Prevention & Efficacy Measurement Service.
Verifies:
1. Evaluation horizons:
   - BASELINE
   - 6 MONTHS
   - 12 MONTHS
2. KPIs measured:
   - missed payments
   - default occurrence
   - repayment stability
   - interest burden
   - debt reduction
   - cashflow stability
   - savings growth
   - financial resilience
3. Outputs:
   - before_after_analysis
   - trend
   - intervention_effectiveness
4. Exact prompt example trajectory:
   - Distress: 81 -> 47 -> 31
   - Resilience: 42 -> 62 -> 75
5. Epistemic constraint:
   - "associated improvement" instead of claiming causality.
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.prevention_service import LongitudinalPreventionService
from src_py.models.prevention_schemas import LongitudinalHorizon

client = TestClient(app)


def test_longitudinal_prevention_service_logic():
    report = LongitudinalPreventionService.evaluate_customer_prevention(
        customer_id="CUST_MSME_TIRUPPUR_001",
        customer_name="Sri Balaji Modern Cotton Mills",
        baseline_distress=81.0,
        baseline_resilience=42.0
    )

    # 1. Verify 3 evaluation horizons
    assert len(report.evaluation_periods) == 3
    horizons = [p.horizon for p in report.evaluation_periods]
    assert LongitudinalHorizon.BASELINE in horizons
    assert LongitudinalHorizon.SIX_MONTHS in horizons
    assert LongitudinalHorizon.TWELVE_MONTHS in horizons

    # 2. Verify exact Distress trajectory: 81 -> 47 -> 31
    d_vals = [int(p.distress_score) for p in report.evaluation_periods]
    assert d_vals == [81, 47, 31]
    assert report.before_after_analysis.distress_trajectory == "81 → 47 → 31"

    # 3. Verify exact Resilience trajectory: 42 -> 62 -> 75
    r_vals = [int(p.financial_resilience) for p in report.evaluation_periods]
    assert r_vals == [42, 62, 75]
    assert report.before_after_analysis.resilience_trajectory == "42 → 62 → 75"

    # 4. Verify KPIs
    p12 = report.evaluation_periods[2]
    assert p12.missed_payments == 0
    assert p12.default_occurrence is False
    assert p12.repayment_stability_score > 90.0
    assert p12.debt_reduction_cumulative > 0
    assert p12.savings_growth_pct > 100.0

    # 5. Verify Trends list
    assert len(report.trend) >= 5
    distress_trend = next(t for t in report.trend if t.metric_name == "Distress Risk Score")
    assert distress_trend.net_12m_change == -50.0
    assert distress_trend.trend_direction == "IMPROVING"

    # 6. Verify Epistemic Mandate: 'associated improvement'
    assert "associated improvement" in report.intervention_effectiveness.associated_improvement_narrative
    assert "Do not claim causality unless experimental evidence exists" in report.intervention_effectiveness.causal_attribution_disclaimer


def test_api_v1_longitudinal_prevention_endpoint():
    res = client.get("/api/v1/prevention/CUST_MSME_TIRUPPUR_001")
    assert res.status_code == 200
    json_data = res.json()
    assert json_data["success"] is True
    data = json_data["data"]

    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "before_after_analysis" in data
    assert "trend" in data
    assert "intervention_effectiveness" in data
    assert data["before_after_analysis"]["distress_trajectory"] == "81 → 47 → 31"
    assert data["before_after_analysis"]["resilience_trajectory"] == "42 → 62 → 75"
    assert "associated improvement" in data["intervention_effectiveness"]["associated_improvement_narrative"]
