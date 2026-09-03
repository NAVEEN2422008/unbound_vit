"""
Unit tests for Asset-Level Financial Intelligence (ALE) and Asset Decision Simulator.
Verifies:
1. Gross Contribution & Net Cash Contribution calculations
2. Provenance Labeling (ACTUAL, USER_ENTERED, ESTIMATED)
3. Asset Classifications (HIGHLY_PRODUCTIVE, PRODUCTIVE, MARGINAL, UNPRODUCTIVE, LOSS_MAKING)
4. Financing burden and profitability margins
5. Asset Decision Simulator across all 6 decision paths (Keep, Restructure, Refinance, Sell, Replace, Scale Utilization)
6. 6, 12, 24-month horizon projections
7. FastAPI endpoints (/customers/{id}/assets, /customers/{id}/assets/{asset_id}/diagnostic, /simulate)
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.asset_intelligence import AssetFinancialIntelligenceService
from src_py.models.asset_schemas import (
    AssetInput, AssetClassification, AssetDecisionType, DataLabel
)

client = TestClient(app)


def test_asset_gross_and_net_contribution_calculation():
    # Asset with healthy economics
    asset = AssetInput(
        asset_id="ASSET_TEST_1",
        asset_name="Weaving Loom Unit A",
        asset_type="MACHINE",
        purchase_price=2000000.0,
        financing_amount=1500000.0,
        outstanding_loan=1200000.0,
        monthly_emi=45000.0,
        revenue_contribution=500000.0,
        operating_cost=300000.0,
        maintenance_cost=20000.0,
        utilization_percentage=85.0,
        age_years=2.0,
        remaining_useful_life_years=8.0,
        revenue_data_label=DataLabel.ACTUAL
    )

    profile = AssetFinancialIntelligenceService.evaluate_asset(asset)

    # Gross Contribution = 500,000 - 300,000 = 200,000
    assert profile.gross_contribution.value == 200000.0
    assert profile.gross_contribution.label == DataLabel.ACTUAL

    # Net Cash Contribution = 500,000 - 300,000 - 20,000 - 45,000 = 135,000
    assert profile.net_cash_contribution.value == 135000.0
    assert profile.profitability_margin_pct == 27.0
    assert profile.classification == AssetClassification.HIGHLY_PRODUCTIVE
    assert profile.financing_burden_ratio == 0.09


def test_loss_making_asset_classification():
    # Machine C: Burning cash due to low utilization and high EMI
    loss_asset = AssetInput(
        asset_id="ASSET_MACH_C",
        asset_name="Terry Jacquard Unit C",
        asset_type="MACHINE",
        purchase_price=2500000.0,
        financing_amount=2000000.0,
        outstanding_loan=1800000.0,
        monthly_emi=65000.0,
        revenue_contribution=100000.0,
        operating_cost=120000.0,
        maintenance_cost=15000.0,
        utilization_percentage=32.0,
        age_years=4.0,
        remaining_useful_life_years=6.0,
        revenue_data_label=DataLabel.ESTIMATED
    )

    profile = AssetFinancialIntelligenceService.evaluate_asset(loss_asset)

    # Net Contribution = 100,000 - (120,000 + 15,000 + 65,000) = -100,000
    assert profile.net_cash_contribution.value == -100000.0
    assert profile.net_cash_contribution.label == DataLabel.ESTIMATED
    assert profile.classification == AssetClassification.LOSS_MAKING
    assert "Negative net cash drain" in profile.distress_impact_assessment


def test_asset_decision_simulator_projections():
    loss_asset = AssetInput(
        asset_id="ASSET_MACH_C",
        asset_name="Terry Jacquard Unit C",
        asset_type="MACHINE",
        purchase_price=2500000.0,
        financing_amount=2000000.0,
        outstanding_loan=1800000.0,
        monthly_emi=65000.0,
        revenue_contribution=100000.0,
        operating_cost=120000.0,
        maintenance_cost=15000.0,
        utilization_percentage=32.0,
        age_years=4.0,
        remaining_useful_life_years=6.0
    )

    # 1. Simulate KEEP (Status Quo)
    sim_keep = AssetFinancialIntelligenceService.simulate_decision_path(loss_asset, AssetDecisionType.KEEP)
    assert sim_keep.projections["6m"].cumulative_net_cash_flow < 0
    assert sim_keep.projections["24m"].cumulative_net_cash_flow < sim_keep.projections["12m"].cumulative_net_cash_flow

    # 2. Simulate RESTRUCTURE_FINANCING
    sim_restruct = AssetFinancialIntelligenceService.simulate_decision_path(loss_asset, AssetDecisionType.RESTRUCTURE_FINANCING)
    assert sim_restruct.feasibility_score >= 0.85
    assert "extended" in sim_restruct.description

    # 3. Simulate SELL
    sim_sell = AssetFinancialIntelligenceService.simulate_decision_path(loss_asset, AssetDecisionType.SELL)
    assert sim_sell.projections["24m"].remaining_loan_balance == 0.0

    # 4. Simulate INCREASE_UTILIZATION
    sim_util = AssetFinancialIntelligenceService.simulate_decision_path(loss_asset, AssetDecisionType.INCREASE_UTILIZATION)
    assert sim_util.projections["6m"].cumulative_net_cash_flow > 0


def test_asset_holistic_diagnostic():
    loss_asset = AssetInput(
        asset_id="ASSET_MACH_C",
        asset_name="Terry Jacquard Unit C",
        asset_type="MACHINE",
        purchase_price=2500000.0,
        financing_amount=2000000.0,
        outstanding_loan=1800000.0,
        monthly_emi=65000.0,
        revenue_contribution=100000.0,
        operating_cost=120000.0,
        maintenance_cost=15000.0,
        utilization_percentage=32.0,
        age_years=4.0,
        remaining_useful_life_years=6.0
    )

    diagnostic = AssetFinancialIntelligenceService.diagnose_asset_holistic("CUST_MSME_TIRUPPUR_001", loss_asset)
    assert len(diagnostic.simulated_decisions) == 6
    assert diagnostic.recommended_decision in [AssetDecisionType.RESTRUCTURE_FINANCING, AssetDecisionType.INCREASE_UTILIZATION]
    assert "LOSS_MAKING" in diagnostic.executive_recommendation_summary


def test_fastapi_asset_endpoints():
    # 1. List assets for MSME
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/assets")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    assets = res_json["data"]
    assert len(assets) == 3
    
    # Check Machine C is classified as LOSS_MAKING
    mach_c = next((a for a in assets if a["asset_id"] == "ASSET_MACH_C"), None)
    assert mach_c is not None
    assert mach_c["classification"] == "LOSS_MAKING"

    # 2. Get holistic diagnostic
    res_diag = client.get("/customers/CUST_MSME_TIRUPPUR_001/assets/ASSET_MACH_C/diagnostic")
    assert res_diag.status_code == 200
    diag_data = res_diag.json()["data"]
    assert len(diag_data["simulated_decisions"]) == 6
    assert "executive_recommendation_summary" in diag_data

    # 3. Simulate decision path endpoint
    res_sim = client.post("/customers/CUST_MSME_TIRUPPUR_001/assets/ASSET_MACH_C/simulate?decision=RESTRUCTURE_FINANCING")
    assert res_sim.status_code == 200
    sim_data = res_sim.json()["data"]
    assert "6m" in sim_data["projections"]
    assert "12m" in sim_data["projections"]
    assert "24m" in sim_data["projections"]
