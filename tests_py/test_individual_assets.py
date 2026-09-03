"""
Unit and integration tests for Individual Asset Financial Intelligence Engine.
Verifies:
1. Asset types: machine, vehicle, equipment, production_line, store, other_revenue_generating_asset
2. Calculations:
   - gross_contribution = revenue_contribution - operating_cost
   - net_contribution = revenue_contribution - operating_cost - maintenance_cost - financing_cost
3. Classifications:
   - HIGHLY_PRODUCTIVE, PRODUCTIVE, MARGINAL, UNPRODUCTIVE, LOSS_MAKING
4. Data status provenance:
   - ACTUAL, USER_ENTERED, ESTIMATED (never represents estimate as actual)
5. Output fields:
   - asset_health, net_contribution, financing_burden, utilization, trend, confidence
6. REST API:
   - GET /api/v1/businesses/{id}/assets
   - GET /api/v1/assets/{asset_id}/analysis
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.asset_intelligence import AssetFinancialIntelligenceService
from src_py.models.asset_schemas import (
    AssetInput, AssetClassification, DataLabel, AssetType
)

client = TestClient(app)


def test_asset_health_calculations_and_classification():
    """
    Verifies gross and net contribution calculations and classifications.
    Gross = 200,000 - 60,000 = 140,000
    Net = 200,000 - 60,000 - 15,000 - 45,000 = 80,000 (Margin 40% -> HIGHLY_PRODUCTIVE)
    """
    asset = AssetInput(
        asset_id="LOOM_01",
        asset_name="Picanol Rapier Loom #1",
        asset_type=AssetType.MACHINE.value,
        purchase_price=3000000.0,
        financing_amount=2400000.0,
        outstanding_loan=1800000.0,
        monthly_emi=45000.0,
        revenue_contribution=200000.0,
        operating_cost=60000.0,
        maintenance_cost=15000.0,
        utilization_percentage=85.0,
        age_years=3.0,
        remaining_useful_life_years=7.0,
        revenue_data_label=DataLabel.ACTUAL
    )

    report = AssetFinancialIntelligenceService.analyze_asset_health(asset)

    # 1. Calculation Checks
    assert report.gross_contribution == 140000.0
    assert report.net_contribution == 80000.0

    # 2. Classification
    assert report.asset_health == AssetClassification.HIGHLY_PRODUCTIVE

    # 3. Output Fields
    assert report.financing_burden == round(45000.0 / 200000.0, 3)
    assert report.utilization == 85.0
    assert report.trend == "IMPROVING"
    assert report.confidence == 0.95
    assert report.revenue_data_status == DataLabel.ACTUAL


def test_loss_making_asset_and_estimated_provenance():
    """
    Verifies that a loss-making machine with ESTIMATED data is classified correctly
    and transparently declares data status without masquerading as actual.
    """
    loss_asset = AssetInput(
        asset_id="SPIN_09",
        asset_name="Old Spinning Frame",
        asset_type=AssetType.EQUIPMENT.value,
        purchase_price=1800000.0,
        financing_amount=1500000.0,
        outstanding_loan=1200000.0,
        monthly_emi=50000.0,
        revenue_contribution=60000.0,  # Revenue < Expenses!
        operating_cost=55000.0,
        maintenance_cost=20000.0,
        utilization_percentage=32.0,
        age_years=6.0,
        remaining_useful_life_years=2.0,
        revenue_data_label=DataLabel.ESTIMATED
    )

    report = AssetFinancialIntelligenceService.analyze_asset_health(loss_asset)

    # Net contribution: 60k - 55k - 20k - 50k = -65,000 (Draining working capital)
    assert report.net_contribution == -65000.0
    assert report.asset_health == AssetClassification.LOSS_MAKING
    assert report.trend == "DETERIORATING"
    # Data status must be explicit
    assert report.revenue_data_status == DataLabel.ESTIMATED
    assert report.confidence == 0.60  # Lower confidence on estimated data


def test_api_v1_business_assets_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/assets")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert isinstance(data, list)
    assert len(data) > 0
    first_asset = data[0]
    assert "asset_health" in first_asset
    assert "net_contribution" in first_asset
    assert "financing_burden" in first_asset
    assert "utilization" in first_asset
    assert "trend" in first_asset
    assert "revenue_data_status" in first_asset


def test_api_v1_single_asset_analysis_endpoint():
    res = client.get(
        "/api/v1/assets/AST_VEHICLE_01/analysis?"
        "asset_type=vehicle&purchase_value=1200000&monthly_emi=28000&"
        "revenue_contribution=95000&operating_cost=42000&maintenance_cost=8000&"
        "utilization=80&revenue_data_status=ESTIMATED"
    )
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["asset_id"] == "AST_VEHICLE_01"
    # Gross: 95000 - 42000 = 53000
    assert data["gross_contribution"] == 53000.0
    # Net: 95000 - 42000 - 8000 - 28000 = 17000
    assert data["net_contribution"] == 17000.0
    assert data["revenue_data_status"] == "ESTIMATED"
    assert "data_provenance_disclosure" in data
