"""
Tests for Evidence-Based Plain Language Explanation Engine.
Verifies:
1. Answers core questions:
   - What happened?
   - Why?
   - When?
   - What evidence supports it?
   - What alternatives were evaluated?
   - Why was this intervention selected?
   - What are the uncertainties?
2. Phrasing matches specification example:
   "Your cash balance is projected to fall below required obligations in 12 days
    because ₹3.5L of payments are due before ₹2L of expected receipts. Your industry is currently
    stable, so the decline appears more specific to your business."
3. Strict Restriction:
   The LLM/assistant may explain, but may NOT independently calculate financial numbers.
   All numbers must come from trusted upstream services.
4. Official APIs:
   - POST /api/v1/explain/risk
   - POST /api/v1/explain/intervention
"""
import pytest
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.explanation_assistant import FinancialExplanationAssistantService
from src_py.models.explanation_schemas import ExplanationInputPayload

client = TestClient(app)


def test_plain_language_risk_explanation_specification_example():
    payload = ExplanationInputPayload(
        customer_id="CUST_SPEC_EXAMPLE_001",
        customer_name="Raja Textiles",
        archetype="SEASONAL_ENTERPRISE",
        cluster_region="Tiruppur",
        industry="Textiles",
        liquid_cash=100000.0,
        monthly_income=250000.0,
        monthly_expenses=200000.0,       # 2.0L
        monthly_debt_emi=150000.0,       # 1.5L -> total scheduled payments = 3.5L
        cash_buffer_days=12,             # 12 days
        projected_shortfall_date="2026-09-16",
        receivables_amount=200000.0,     # 2.0L expected receipts
        payables_amount=180000.0,
        distress_score=78.0,
        classification="SMA-1",
        primary_root_cause="OBLIGATION_COLLISION",
        detailed_causes=["Liquidity deficit", "Delayed receivables"],
        cluster_revenue_growth_pct=1.5,
        borrower_revenue_growth_pct=-14.2,
        is_sector_wide_seasonal_effect=False,  # Industry is stable
        context_narrative="Cluster stable",
        simulated_options=[],
        recommended_option_title="RECEIVABLE_ACCELERATION",
        recommended_option_description="Mobilize invoices via TReDS factoring",
        no_new_loan_veto_active=True,
        no_new_loan_veto_reason="DSCR below threshold",
        overall_confidence_pct=92.0,
        missing_information=[],
        supporting_facts=[]
    )

    resp = FinancialExplanationAssistantService.explain_risk(payload)

    # Answers: What happened, Why, When, Evidence, Uncertainties
    assert resp.customer_id == "CUST_SPEC_EXAMPLE_001"
    assert "12 days" in resp.what_happened
    assert "3.5L" in resp.why
    assert "2.0L" in resp.why
    assert "2026-09-16" in resp.when
    assert len(resp.evidence) >= 3
    assert len(resp.uncertainties) >= 2

    # Verify exact specification narrative tone:
    text = resp.plain_language_explanation
    assert "fall below required obligations in 12 days" in text
    assert "₹3.5l of payments are due before ₹2.0l of expected receipts" in text.lower()
    assert "industry is currently stable" in text
    assert "decline appears more specific to your business" in text

    # Restriction check: No calculation disclaimer present
    assert "trusted upstream analytical engines" in resp.calculation_restriction_notice


def test_plain_language_intervention_explanation():
    payload = ExplanationInputPayload(
        customer_id="CUST_SPEC_EXAMPLE_001",
        customer_name="Raja Textiles",
        archetype="SEASONAL_ENTERPRISE",
        cluster_region="Tiruppur",
        industry="Textiles",
        liquid_cash=100000.0,
        monthly_income=250000.0,
        monthly_expenses=200000.0,
        monthly_debt_emi=150000.0,
        cash_buffer_days=12,
        receivables_amount=200000.0,
        payables_amount=180000.0,
        distress_score=78.0,
        classification="SMA-1",
        primary_root_cause="OBLIGATION_COLLISION",
        detailed_causes=[],
        cluster_revenue_growth_pct=1.5,
        borrower_revenue_growth_pct=-14.2,
        is_sector_wide_seasonal_effect=False,
        context_narrative="Cluster stable",
        simulated_options=[],
        recommended_option_title="RECEIVABLE_ACCELERATION",
        recommended_option_description="Mobilize invoices via TReDS factoring",
        no_new_loan_veto_active=True,
        no_new_loan_veto_reason="DSCR below threshold",
        overall_confidence_pct=92.0,
        missing_information=[],
        supporting_facts=[]
    )

    resp = FinancialExplanationAssistantService.explain_intervention(payload)

    # Answers: Alternatives evaluated, Why selected, Evidence, Uncertainties
    assert resp.selected_intervention == "RECEIVABLE_ACCELERATION"
    assert len(resp.alternatives_evaluated) >= 3
    assert "without adding multi-year interest" in resp.why_this_intervention_selected.lower()
    assert len(resp.evidence) >= 2
    assert len(resp.uncertainties) >= 1


def test_api_v1_explain_endpoints():
    # 1. POST /api/v1/explain/risk
    res_risk = client.post("/api/v1/explain/risk", json={"customer_id": "CUST_MSME_TIRUPPUR_001"})
    assert res_risk.status_code == 200
    json_risk = res_risk.json()
    assert json_risk["success"] is True
    data_risk = json_risk["data"]
    assert "what_happened" in data_risk
    assert "why" in data_risk
    assert "when" in data_risk
    assert "evidence" in data_risk
    assert "uncertainties" in data_risk
    assert "plain_language_explanation" in data_risk
    assert "trusted upstream" in data_risk["calculation_restriction_notice"]

    # 2. POST /api/v1/explain/intervention
    res_interv = client.post("/api/v1/explain/intervention", json={"customer_id": "CUST_MSME_TIRUPPUR_001"})
    assert res_interv.status_code == 200
    json_interv = res_interv.json()
    assert json_interv["success"] is True
    data_interv = json_interv["data"]
    assert "selected_intervention" in data_interv
    assert "alternatives_evaluated" in data_interv
    assert "why_this_intervention_selected" in data_interv
    assert "evidence" in data_interv
    assert "uncertainties" in data_interv
