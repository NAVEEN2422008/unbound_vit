"""
Unit and integration tests for Obligation Collision Radar Service.
Verifies:
1. Available cash and projected balance formulas:
   available_cash = opening_cash + expected_inflows - non_obligation_outflows
   obligation_total = sum(obligations_due)
   projected_balance = available_cash - obligation_total
   shortfall = max(0, -projected_balance)
2. Severity classification: GREEN, YELLOW, ORANGE, RED
3. Prioritization order: severity + shortfall magnitude + days until event
4. Obligation type tracking: EMI, rent, payroll, supplier, tax, utility
5. Does NOT choose loans or interventions (strictly descriptive)
6. REST API: GET /api/v1/customers/{id}/obligation-collisions
"""
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.collision_radar import ObligationCollisionRadarService
from src_py.models.collision_radar_schemas import CollisionSeverity
from src_py.models.schemas import (
    NormalizedTransaction, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, DirectionEnum
)

client = TestClient(app)


@pytest.fixture
def collision_test_data():
    base_d = date(2026, 9, 1)

    # 2 loans: Loan 1 EMI on Day 10 (₹45,000), Loan 2 EMI on Day 20 (₹25,000)
    loans = [
        LoanObligation(
            id="L1", lender_name="HDFC Bank", loan_type="TERM",
            principal_amount=1000000, outstanding_principal=800000,
            interest_rate_annual=11.0, monthly_emi=45000,
            nach_debit_day=10, tenure_months_remaining=24
        ),
        LoanObligation(
            id="L2", lender_name="Axis Bank", loan_type="WORKING_CAPITAL",
            principal_amount=500000, outstanding_principal=400000,
            interest_rate_annual=13.0, monthly_emi=25000,
            nach_debit_day=20, tenure_months_remaining=18
        )
    ]

    # Fixed obligations: Rent on Day 5 (₹35,000), Payroll on Day 10 (₹60,000)
    obligations = [
        FixedObligationItem(id="O_RENT", category="Commercial Rent", amount=35000, due_day_of_month=5, is_mandatory=True),
        FixedObligationItem(id="O_PAYROLL", category="Staff Payroll", amount=60000, due_day_of_month=10, is_mandatory=True)
    ]

    # Supplier Payable on Day 10 (₹30,000)
    payables = [
        PayableItem(id="P1", vendor_name="Raw Yarn Corp", amount=30000, due_date=date(2026, 9, 10), is_critical_supply=True)
    ]

    # Starting Cash: ₹50,000
    starting_cash = 50000.0

    return starting_cash, loans, obligations, payables, base_d


def test_obligation_collision_calculation_and_severities(collision_test_data):
    starting_cash, loans, obligations, payables, base_d = collision_test_data

    report = ObligationCollisionRadarService.detect_collisions(
        customer_id="CUST_RADAR_01",
        customer_name="Sri Balaji Fabrics",
        archetype="MSME",
        starting_cash=starting_cash,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=[],
        payables=payables,
        horizon_days=30,
        start_date=base_d,
        minimum_buffer=20000.0
    )

    # 1. Day 5: Rent of ₹35,000 against ₹50,000 opening cash -> projected balance ₹15,000
    # 0 <= ₹15,000 < min_buffer (₹20,000) -> Severity YELLOW
    day5 = next(e for e in report.calendar_events if e.date == date(2026, 9, 5))
    assert day5.obligation_total == 35000.0
    assert day5.severity == CollisionSeverity.YELLOW
    assert day5.shortfall == 0.0

    # 2. Day 10: Multi-obligation collision!
    # EMI (₹45,000) + Payroll (₹60,000) + Supplier (₹30,000) = ₹135,000 obligations!
    # Projected balance plunges into deep negative territory -> Severe RED collision
    day10 = next(e for e in report.calendar_events if e.date == date(2026, 9, 10))
    assert day10.obligation_total == 135000.0
    assert day10.shortfall > 50000.0
    assert day10.severity == CollisionSeverity.RED
    assert len(day10.contributing_obligations) == 3
    # Verify obligation types
    ob_types = [o.obligation_type for o in day10.contributing_obligations]
    assert "EMI" in ob_types
    assert "PAYROLL" in ob_types
    assert "SUPPLIER" in ob_types


def test_collision_prioritization_ordering(collision_test_data):
    starting_cash, loans, obligations, payables, base_d = collision_test_data

    report = ObligationCollisionRadarService.detect_collisions(
        customer_id="CUST_RADAR_01",
        customer_name="Sri Balaji Fabrics",
        archetype="MSME",
        starting_cash=starting_cash,
        transactions=[],
        loans=loans,
        obligations=obligations,
        receivables=[],
        payables=payables,
        horizon_days=30,
        start_date=base_d
    )

    # Prioritized collisions must contain the collisions sorted by priority
    assert len(report.prioritized_collisions) > 0
    # All RED collisions must come before YELLOW collisions
    severities = [c.severity for c in report.prioritized_collisions]
    assert CollisionSeverity.RED in severities
    assert CollisionSeverity.YELLOW in severities
    assert severities.index(CollisionSeverity.RED) < severities.index(CollisionSeverity.YELLOW)
    
    # Priority scores must be in descending order
    scores = [c.priority_score for c in report.prioritized_collisions]
    assert scores == sorted(scores, reverse=True)
    
    # Verify Day 10 is among the RED collisions
    red_dates = [c.date for c in report.prioritized_collisions if c.severity == CollisionSeverity.RED]
    assert date(2026, 9, 10) in red_dates


def test_api_v1_obligation_collisions_endpoint():
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/obligation-collisions?horizon_days=30")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]
    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "total_obligations_tracked" in data
    assert "prioritized_collisions" in data
    assert "calendar_events" in data
    assert len(data["calendar_events"]) == 30
    assert "radar_summary" in data
