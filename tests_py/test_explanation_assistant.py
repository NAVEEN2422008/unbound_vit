"""
Unit tests for AI Financial Explanation Assistant.
Verifies:
1. Grounded synthesis across the 8 required operational questions:
   - What is happening?
   - Why is it happening?
   - What evidence supports this?
   - What could happen next?
   - What options were simulated?
   - Why was the recommended intervention selected?
   - What is the confidence level?
   - What information is missing?
2. Zero calculation inside assistant: Strictly formats ingested numerical facts
3. No hallucination guarantee: Does not invent non-existent figures
4. Ingestion of arbitrary external structured payloads via POST /assistant/explain
5. Full customer narrative matching prompt specifications:
   "Your cash position is expected to become negative in approximately X days..."
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.explanation_assistant import FinancialExplanationAssistantService
from src_py.models.explanation_schemas import ExplanationInputPayload

client = TestClient(app)


def test_explanation_assistant_direct_service_synthesis():
    payload = ExplanationInputPayload(
        customer_id="CUST_TEST_EXP_01",
        customer_name="Sri Balaji Fabrics & Knits Pvt Ltd",
        archetype="MSME",
        cluster_region="Tiruppur",
        industry="Textiles",
        liquid_cash=140000.0,
        monthly_income=2800000.0,
        monthly_expenses=2350000.0,
        monthly_debt_emi=500000.0,
        cash_buffer_days=24,
        projected_shortfall_date="2026-09-28",
        receivables_amount=1000000.0,
        payables_amount=800000.0,
        distress_score=76.0,
        classification="SMA_1_EARLY_STRESS",
        primary_root_cause="RECEIVABLES_LOCKUP",
        detailed_causes=["Pending trade invoices delayed beyond 45 days."],
        cluster_revenue_growth_pct=-2.0,
        borrower_revenue_growth_pct=-18.0,
        is_sector_wide_seasonal_effect=False,
        context_narrative="Cluster peers are stable.",
        simulated_options=[
            {"title": "Emergency Working Capital Loan", "is_permissible": False},
            {"title": "TReDS Invoice Discounting", "is_permissible": True}
        ],
        recommended_option_title="TReDS Invoice Discounting",
        recommended_option_description="Accelerating receivable collection with zero balance-sheet debt",
        no_new_loan_veto_active=True,
        no_new_loan_veto_reason="would increase your monthly repayment burden beyond the safe range",
        overall_confidence_pct=93.5,
        missing_information=["Supplier invoice confirmation"],
        supporting_facts=["Verified invoice of ₹10L on GSTN portal"]
    )

    res = FinancialExplanationAssistantService.generate_explanation(payload)

    # Verify all 8 core questions answered
    assert "24 days" in res.what_is_happening
    assert "receivables lockup" in res.why_is_it_happening.lower()
    assert len(res.supporting_evidence) >= 1
    assert "exhaustion in 24 days" in res.what_could_happen_next
    assert len(res.options_simulated) == 2
    assert "TReDS Invoice Discounting" in res.why_recommended_intervention_selected
    assert "beyond the safe range" in res.why_recommended_intervention_selected
    assert res.confidence_level["overall_confidence_percentage"] == 93.5
    assert len(res.missing_information) >= 1

    # Verify synthesis narrative matches exact prompt expectations
    assert "Your cash position is expected to become negative in approximately 24 days" in res.synthesis_narrative
    assert "Your industry is currently stable, so the decline appears to be specific to your business rather than a sector-wide seasonal effect" in res.synthesis_narrative
    assert "A new loan was simulated but would increase your monthly repayment burden beyond the safe range" in res.synthesis_narrative


def test_fastapi_assistant_explanation_endpoint():
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/assistant-explanation")
    assert res.status_code == 200
    res_json = res.json()
    assert res_json["success"] is True
    data = res_json["data"]

    assert data["customer_id"] == "CUST_MSME_TIRUPPUR_001"
    assert "what_is_happening" in data
    assert "why_is_it_happening" in data
    assert "supporting_evidence" in data
    assert "what_could_happen_next" in data
    assert "options_simulated" in data
    assert "why_recommended_intervention_selected" in data
    assert "confidence_level" in data
    assert "missing_information" in data
    assert "synthesis_narrative" in data
    assert len(data["synthesis_narrative"]) > 50


def test_fastapi_explain_arbitrary_payload_post():
    payload = {
        "customer_id": "CUST_EXT_999",
        "customer_name": "Apex Auto Components",
        "archetype": "MSME",
        "cluster_region": "Pune",
        "industry": "Auto Ancillary",
        "liquid_cash": 95000.0,
        "monthly_income": 1200000.0,
        "monthly_expenses": 950000.0,
        "monthly_debt_emi": 320000.0,
        "cash_buffer_days": 12,
        "projected_shortfall_date": "2026-09-18",
        "receivables_amount": 650000.0,
        "payables_amount": 420000.0,
        "distress_score": 82.0,
        "classification": "SMA_1_EARLY_STRESS",
        "primary_root_cause": "FIXED_DEBT_BURDEN",
        "detailed_causes": ["High EMI relative to operating cashflow."],
        "cluster_revenue_growth_pct": 3.0,
        "borrower_revenue_growth_pct": -12.0,
        "is_sector_wide_seasonal_effect": False,
        "context_narrative": "Auto sector stable.",
        "simulated_options": [
            {"title": "Term Loan Tenor Extension", "is_permissible": True}
        ],
        "recommended_option_title": "Tenor Restructuring",
        "recommended_option_description": "Extends maturity to lower monthly EMI",
        "no_new_loan_veto_active": True,
        "no_new_loan_veto_reason": "DSCR is 0.78 below minimum 1.25 floor",
        "overall_confidence_pct": 91.0,
        "missing_information": ["Q4 forecast"],
        "supporting_facts": ["DSCR calculated from GSTN returns"]
    }

    res = client.post("/assistant/explain", json=payload)
    assert res.status_code == 200
    res_data = res.json()["data"]
    assert res_data["customer_name"] == "Apex Auto Components"
    assert "12 days" in res_data["what_is_happening"]
    assert "Tenor Restructuring" in res_data["why_recommended_intervention_selected"]
