"""
Unit and integration tests for Financial Decision Digital Twin Engine Service.
Verifies:
1. Virtual decoupled copy creation:
   - Real financial records are never modified; simulations stored separately in DECISION_SIMULATIONS and DECISION_SIMULATION_RESULTS
2. All 11 intervention scenarios:
   - NO_INTERVENTION, NEW_LOAN, LIMITED_LOAN, EMI_RESTRUCTURE, TENURE_EXTENSION,
     RECEIVABLE_ACCELERATION, EXPENSE_REDUCTION, ASSET_SALE, ASSET_REPLACEMENT,
     BUSINESS_RECOVERY, BUSINESS_MATCHING
3. Multi-period calculations across 3, 6, 12, and 24 months:
   - cash_balance, cashflow, debt_balance, EMI, interest_burden, cash_buffer,
     distress_score, resilience_score, recovery_status
4. Comparison table and best candidate rankings
5. REST APIs:
   - POST /api/v1/decision-twin/simulate
   - POST /api/v1/decision-twin/compare
   - GET /api/v1/decision-twin/{customer_id}
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.decision_twin import (
    DecisionTwinEngineService, DECISION_SIMULATIONS, DECISION_SIMULATION_RESULTS
)
from src_py.models.decision_twin_schemas import DigitalTwinScenarioType
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

client = TestClient(app)


def test_decision_twin_virtual_copy_and_11_scenarios():
    """
    Tests simulation of all 11 intervention scenarios across 3, 6, 12, and 24 months.
    Verifies that real records are untouched, all 9 metrics exist per horizon,
    and best candidates are selected.
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

    initial_liquid = fre.liquid_cash_balance.value
    initial_debt = fre.total_outstanding_debt.value

    # Run full Digital Twin simulation
    report = DecisionTwinEngineService.run_all_simulations(fre)

    # 1. Verify Real Records are Immutable
    assert fre.liquid_cash_balance.value == initial_liquid
    assert fre.total_outstanding_debt.value == initial_debt
    assert "isolated digital twin environment" in report.data_isolation_notice.lower()

    # 2. Verify all 11 Scenarios
    scenario_types = [r.scenario for r in report.scenario_results]
    for expected in [
        DigitalTwinScenarioType.NO_INTERVENTION,
        DigitalTwinScenarioType.NEW_LOAN,
        DigitalTwinScenarioType.LIMITED_LOAN,
        DigitalTwinScenarioType.EMI_RESTRUCTURE,
        DigitalTwinScenarioType.TENURE_EXTENSION,
        DigitalTwinScenarioType.RECEIVABLE_ACCELERATION,
        DigitalTwinScenarioType.EXPENSE_REDUCTION,
        DigitalTwinScenarioType.ASSET_SALE,
        DigitalTwinScenarioType.ASSET_REPLACEMENT,
        DigitalTwinScenarioType.BUSINESS_RECOVERY,
        DigitalTwinScenarioType.BUSINESS_MATCHING
    ]:
        assert expected in scenario_types

    assert len(report.scenario_results) == 11

    # 3. Check All 9 Metrics on Each Scenario across 3, 6, 12, 24 months
    for s in report.scenario_results:
        assert "3m" in s.projections
        assert "6m" in s.projections
        assert "12m" in s.projections
        assert "24m" in s.projections
        for h_key in ["3m", "6m", "12m", "24m"]:
            proj = s.projections[h_key]
            assert isinstance(proj.cash_balance, float)
            assert isinstance(proj.cashflow, float)
            assert isinstance(proj.debt_balance, float)
            assert isinstance(proj.EMI, float)
            assert isinstance(proj.interest_burden, float)
            assert isinstance(proj.cash_buffer_days, int)
            assert 0.0 <= proj.distress_score <= 100.0
            assert 0.0 <= proj.resilience_score <= 100.0
            assert proj.recovery_status in ["RECOVERED", "STABILIZING", "STAGNANT", "DETERIORATING"]

    # 4. Check Comparison Table and Rankings
    assert len(report.comparison_table) == 11
    assert len(report.best_candidates) >= 1

    # 5. Check isolated database storage
    assert report.simulation_id in DECISION_SIMULATIONS
    assert report.simulation_id in DECISION_SIMULATION_RESULTS


def test_api_v1_decision_twin_endpoints():
    # 1. Simulate POST
    sim_res = client.post(
        "/api/v1/decision-twin/simulate",
        json={"customer_id": "CUST_MSME_TIRUPPUR_001"}
    )
    assert sim_res.status_code == 200
    sim_data = sim_res.json()["data"]
    assert sim_data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert len(sim_data["scenario_results"]) == 11
    assert len(sim_data["comparison_table"]) == 11

    # 2. Compare POST
    comp_res = client.post(
        "/api/v1/decision-twin/compare",
        json={
            "customer_id": "CUST_MSME_TIRUPPUR_001",
            "candidate_scenarios": ["EMI_RESTRUCTURE", "RECEIVABLE_ACCELERATION", "EXPENSE_REDUCTION"]
        }
    )
    assert comp_res.status_code == 200
    comp_data = comp_res.json()["data"]
    assert len(comp_data["scenario_results"]) == 3

    # 3. Get GET
    get_res = client.get("/api/v1/decision-twin/CUST_MSME_TIRUPPUR_001")
    assert get_res.status_code == 200
    get_data = get_res.json()["data"]
    assert get_data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "best_candidates" in get_data
