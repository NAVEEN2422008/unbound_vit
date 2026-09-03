"""
Unit and integration tests for Asset Decision Simulator Service.
Verifies:
1. Evaluation of all 7 strategic decision scenarios:
   - KEEP, RESTRUCTURE_FINANCING, REFINANCE, SELL, REPLACE, PAUSE, INCREASE_UTILIZATION
2. Output metrics for each scenario across 6, 12, and 24 months:
   - monthly_cashflow, monthly_profit, debt, EMI, financing_cost, liquidity, resilience_score, distress_score
3. Institutional safety rule:
   - This module only simulates and compares. It must never automatically sell an asset.
4. REST API:
   - POST /api/v1/assets/{id}/decision-simulation
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.asset_intelligence import AssetFinancialIntelligenceService
from src_py.models.asset_schemas import (
    AssetInput, AssetDecisionType, DataLabel
)

client = TestClient(app)


def test_simulate_all_7_scenarios_across_horizons():
    """
    Simulates underperforming/loss-making asset (35% utilization, high EMI)
    across KEEP, RESTRUCTURE_FINANCING, REFINANCE, SELL, REPLACE, PAUSE, INCREASE_UTILIZATION.
    Verifies that all 7 scenarios produce 6m, 12m, and 24m horizons with all 8 metrics.
    """
    asset = AssetInput(
        asset_id="AST_UNDERPERF_01",
        asset_name="Underutilized Loom",
        asset_type="machine",
        purchase_price=2500000.0,
        financing_amount=2000000.0,
        outstanding_loan=1500000.0,
        monthly_emi=45000.0,
        revenue_contribution=75000.0,
        operating_cost=60000.0,
        maintenance_cost=15000.0,
        utilization_percentage=35.0,
        age_years=3.0,
        remaining_useful_life_years=7.0,
        revenue_data_label=DataLabel.ACTUAL
    )

    report = AssetFinancialIntelligenceService.simulate_all_scenarios(asset, business_id="BIZ_TEX_001")

    # 1. Verify 7 Scenarios
    scenario_decisions = [s.decision for s in report.scenarios]
    assert AssetDecisionType.KEEP in scenario_decisions
    assert AssetDecisionType.RESTRUCTURE_FINANCING in scenario_decisions
    assert AssetDecisionType.REFINANCE in scenario_decisions
    assert AssetDecisionType.SELL in scenario_decisions
    assert AssetDecisionType.REPLACE in scenario_decisions
    assert AssetDecisionType.PAUSE in scenario_decisions
    assert AssetDecisionType.INCREASE_UTILIZATION in scenario_decisions
    assert len(report.scenarios) == 7

    # 2. Check Metrics on Each Scenario across 6m, 12m, 24m
    for s in report.scenarios:
        assert "6m" in s.projections
        assert "12m" in s.projections
        assert "24m" in s.projections
        for h_key in ["6m", "12m", "24m"]:
            proj = s.projections[h_key]
            # Required metrics:
            assert isinstance(proj.monthly_cashflow, float)
            assert isinstance(proj.monthly_profit, float)
            assert isinstance(proj.debt, float)
            assert isinstance(proj.EMI, float)
            assert isinstance(proj.financing_cost, float)
            assert isinstance(proj.liquidity, float)
            assert 0.0 <= proj.resilience_score <= 100.0
            assert 0.0 <= proj.distress_score <= 100.0

    # 3. Institutional Safety Guardrail
    # Must never automatically sell an asset
    assert "never automatically sell" in report.simulation_disclaimer.lower()


def test_api_v1_asset_decision_simulation_endpoint():
    res = client.post(
        "/api/v1/assets/AST_LOOM_99/decision-simulation?"
        "business_id=CUST_MSME_TIRUPPUR_001&purchase_value=2400000&monthly_emi=42000&"
        "revenue_contribution=70000&operating_cost=55000&maintenance_cost=12000&utilization=30"
    )
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["asset_id"] == "AST_LOOM_99"
    assert len(data["scenarios"]) == 7
    first_scen = data["scenarios"][0]
    assert "6m" in first_scen["projections"]
    proj_6m = first_scen["projections"]["6m"]
    assert "monthly_cashflow" in proj_6m
    assert "monthly_profit" in proj_6m
    assert "debt" in proj_6m
    assert "EMI" in proj_6m
    assert "financing_cost" in proj_6m
    assert "liquidity" in proj_6m
    assert "resilience_score" in proj_6m
    assert "distress_score" in proj_6m
    assert "simulation_disclaimer" in data
