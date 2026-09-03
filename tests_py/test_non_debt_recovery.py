"""
Unit and integration tests for Non-Debt Business Recovery Engine Service.
Verifies:
1. Core Epistemic Philosophy:
   - Evaluates: "Can the business problem be fixed without increasing debt?" BEFORE "How much more can we lend?"
2. All 8 Non-Debt Levers:
   - ADDITIONAL_CUSTOMERS
   - RECEIVABLE_COLLECTION
   - ASSET_UTILIZATION
   - COST_REDUCTION
   - SUPPLIER_NEGOTIATION
   - PRODUCT_MIX
   - SEASONAL_PLANNING
   - BUSINESS_MATCHING
3. Each opportunity card schema:
   - type, estimated_impact, time_to_benefit, risk, confidence, evidence
4. REST API:
   - GET /api/v1/businesses/{id}/non-debt-recovery
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.non_debt_recovery import NonDebtBusinessRecoveryService
from src_py.models.recovery_schemas import NonDebtRecoveryLeverType
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_non_debt_business_recovery_all_8_levers():
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

    report = NonDebtBusinessRecoveryService.evaluate_recovery_opportunities(
        fre=fre,
        industry="TEXTILES",
        region="TAMIL_NADU"
    )

    # 1. Check Core Philosophy
    assert "fixed without increasing debt" in report.core_epistemic_inquiry.lower()
    assert "how much more can we lend" in report.core_epistemic_inquiry.lower()

    # 2. Verify all 8 Non-Debt Levers
    lever_types = [o.type for o in report.recovery_opportunities]
    for expected_lever in [
        NonDebtRecoveryLeverType.ADDITIONAL_CUSTOMERS,
        NonDebtRecoveryLeverType.RECEIVABLE_COLLECTION,
        NonDebtRecoveryLeverType.ASSET_UTILIZATION,
        NonDebtRecoveryLeverType.COST_REDUCTION,
        NonDebtRecoveryLeverType.SUPPLIER_NEGOTIATION,
        NonDebtRecoveryLeverType.PRODUCT_MIX,
        NonDebtRecoveryLeverType.SEASONAL_PLANNING,
        NonDebtRecoveryLeverType.BUSINESS_MATCHING
    ]:
        assert expected_lever in lever_types

    assert len(report.recovery_opportunities) == 8

    # 3. Check Required Fields on every opportunity
    for opp in report.recovery_opportunities:
        assert isinstance(opp.type, NonDebtRecoveryLeverType)
        assert len(opp.estimated_impact) > 0
        assert opp.estimated_monthly_cash_benefit > 0.0
        assert len(opp.time_to_benefit) > 0
        assert opp.time_to_benefit_days > 0
        assert opp.risk in ["LOW", "MODERATE", "HIGH"]
        assert 0.0 <= opp.confidence <= 1.0
        assert len(opp.evidence) >= 1
        assert len(opp.implementation_steps) >= 1
        assert opp.is_non_debt is True

    # 4. Check Aggregate Unlock and Verdict
    assert report.total_potential_monthly_impact > 0.0
    assert report.total_immediate_liquidity_unlock >= 0.0
    assert "non-debt" in report.debt_avoidance_verdict.lower()


def test_api_v1_non_debt_recovery_endpoint():
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/non-debt-recovery")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert len(data["recovery_opportunities"]) == 8
    assert "total_potential_monthly_impact" in data
    assert "debt_avoidance_verdict" in data
