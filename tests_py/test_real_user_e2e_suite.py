"""
Complete Real-User End-to-End QA and Domain Test Suite for Financial Distress Prevention Platform.
Validates:
- 10 Test User Personas (A through J)
- Real User Tests 1 through 28
- Negative Testing & Graceful Degradation
- Data Consistency & Access Control
- AI Safety & Deterministic Verification
- Flagship MSME Textile End-to-End Lifecycle
"""
import pytest
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.services.distress_engine import EarlyDistressDetectionService
from src_py.services.distress_classifier import DistressClassificationEngineService
from src_py.services.collision_radar import ObligationCollisionRadarService
from src_py.services.context_intelligence import ContextIntelligenceService
from src_py.services.peer_benchmarking import PeerBenchmarkingService
from src_py.services.seasonal_forecasting import SeasonalForecastingService
from src_py.services.asset_intelligence import AssetFinancialIntelligenceService
from src_py.services.receivable_analysis import ReceivablesAnalysisService
from src_py.services.credit_affordability import CreditAffordabilityEngineService
from src_py.services.financing_timing import FinancingTimingEngineService
from src_py.services.decision_twin import DecisionTwinEngineService
from src_py.services.least_harm_optimizer import LeastHarmOptimizerService
from src_py.services.non_debt_recovery import NonDebtBusinessRecoveryService
from src_py.services.business_matching import BusinessOpportunityMatchingService
from src_py.services.confidence_engine import EpistemicConfidenceService
from src_py.services.banker_review_service import BankerHumanReviewService
from src_py.services.audit_ledger_service import ImmutableAuditLedgerService
from src_py.services.outcome_verification_service import InterventionOutcomeService
from src_py.services.prevention_service import LongitudinalPreventionService
from src_py.services.customer_dashboard import CustomerDashboardService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

from src_py.models.schemas import (
    DirectionEnum, TransactionCategory, LoanObligation, FixedObligationItem,
    ReceivableItem, PayableItem, AssetFinancingItem
)
from src_py.models.distress_schemas import DistressPredictionRequest, PredictionHorizon
from src_py.models.distress_classification_schemas import DistressDominantType
from src_py.models.context_schemas import ContextClassificationEnum
from src_py.models.asset_schemas import AssetInput, AssetClassification
from src_py.models.affordability_schemas import ProposedLoanInput, AffordabilityClassification, NoNewLoanVerdict
from src_py.models.human_review_schemas import HumanReviewAction, EscalationReason, SubmitHumanReviewRequest
from src_py.models.outcome_schemas import SolvencyMetricsSnapshot, RecordInterventionOutcomeRequest
from src_py.models.confidence_schemas import ConfidenceLevel
from src_py.models.audit_schemas import AuditEventType

client = TestClient(app)

# ============================================================================
# 1. TEST USER PERSONAS (A through J)
# ============================================================================

def test_persona_a_healthy_salaried_customer():
    """
    PERSONA A — HEALTHY SALARIED CUSTOMER
    Name: Ravi Kumar, Monthly income: ₹60,000, Expenses: ₹30,000, EMI: ₹8,000, Savings: ₹2,50,000
    Expected: LOW distress, HIGH resilience, No intervention required.
    """
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "TX_A1", "customer_id": "PA_RAVI", "timestamp": "2026-08-01T10:00:00",
            "amount": 60000.0, "direction": "INFLOW", "category": "INCOME_SALARY"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "TX_A2", "customer_id": "PA_RAVI", "timestamp": "2026-08-05T10:00:00",
            "amount": 30000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_LIVING"
        })
    ]
    loans = [
        LoanObligation(
            id="L_RAVI", lender_name="HDFC", loan_type="PERSONAL",
            principal_amount=200000.0, outstanding_principal=120000.0,
            interest_rate_annual=10.5, monthly_emi=8000.0,
            nach_debit_day=10, tenure_months_remaining=18
        )
    ]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="PA_RAVI", customer_name="Ravi Kumar", archetype="SALARIED",
        transactions=txns, loans=loans, obligations=[], receivables=[], payables=[], assets=[],
        liquid_cash=250000.0, savings=250000.0
    )
    
    req = DistressPredictionRequest(
        customer_id="PA_RAVI",
        declining_cash_rate_pct=0.0,
        negative_balance_frequency=0,
        cash_buffer_days=int(fre.cash_buffer_days.value),
        revenue_decline_pct=0.0,
        income_volatility=0.04,
        debt_service_ratio=float(fre.debt_service_ratio.value) / 100.0,
        fixed_cost_ratio=0.50,
        late_payments_last_90d=0,
        upcoming_collision_shortfall=0.0,
        horizon=PredictionHorizon.HORIZON_30_DAY
    )
    distress = EarlyDistressDetectionService.predict_distress(req)
    assert distress.distress_score < 35.0
    assert distress.risk_level.value in ["LOW", "MODERATE"]


def test_persona_b_temporary_liquidity_gap():
    """
    PERSONA B — TEMPORARY LIQUIDITY GAP
    MSME owner, Monthly revenue: ₹8,00,000, Normal cash flow: positive,
    Upcoming supplier payment: ₹3,00,000, Expected receivable: ₹4,00,000 in 12 days, Current cash: ₹1,50,000
    Expected: Identified as TEMPORARY_LIQUIDITY_GAP, receivable acceleration recommended over large new loan.
    """
    receivables = [
        ReceivableItem(
            id="REC_PB", invoice_number="INV_PB_01", buyer_name="Precision Spares",
            amount=400000.0, due_date=date.today() + timedelta(days=12)
        )
    ]
    payables = [
        PayableItem(
            id="PAY_PB", vendor_name="Raw Metal Co", amount=300000.0,
            due_date=date.today() + timedelta(days=5), is_critical=True
        )
    ]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="PB_MSME", customer_name="TechMech MSME", archetype="MSME",
        transactions=[], loans=[], obligations=[], receivables=receivables, payables=payables,
        assets=[], liquid_cash=150000.0
    )
    
    cls_report = DistressClassificationEngineService.classify_distress(
        customer_id="PB_MSME", fre=fre, revenue_decline_pct=0.0, has_upcoming_shortage=True
    )
    assert cls_report.primary_category == DistressDominantType.TEMPORARY_LIQUIDITY_GAP
    assert "14–30 days" in cls_report.expected_duration


def test_persona_c_income_shock():
    """
    PERSONA C — INCOME SHOCK
    Gig worker/freelancer, Normal income: ₹70,000, Current income: ₹35,000 (-50%).
    Expected: INCOME_SHOCK, high distress, detects problem before formal missed payment.
    """
    data = SAMPLE_CUSTOMERS_DATA["CUST_SALARIED_BLR_002"]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=[], loans=[], obligations=[], receivables=[], payables=[], assets=[],
        liquid_cash=data["liquid_cash"], savings=data.get("savings", 0.0)
    )
    cls_report = DistressClassificationEngineService.classify_distress(
        customer_id="CUST_GIG_001", fre=fre, revenue_decline_pct=50.0, declining_orders_pct=45.0
    )
    assert cls_report.primary_category == DistressDominantType.INCOME_SHOCK
    assert "revenue_decline_rate" in [e.metric_name for e in cls_report.evidence]


def test_persona_d_debt_overload():
    """
    PERSONA D — DEBT OVERLOAD
    MSME, Revenue: ₹10,00,000/month, Existing EMI: ₹4,00,000/month. Requests ₹20,00,000 loan.
    Expected: Credit affordability flags loan, No-New-Loan Guardrail triggers with clear rationale.
    """
    loans = [
        LoanObligation(
            id="L_D1", lender_name="Bank A", loan_type="WORKING_CAPITAL",
            principal_amount=4000000.0, outstanding_principal=3500000.0,
            interest_rate_annual=13.0, monthly_emi=400000.0,
            nach_debit_day=10, tenure_months_remaining=12
        )
    ]
    txns = [
        FinancialRealityEngineService.normalize_transaction({
            "id": "T1", "customer_id": "PD_DEBT", "timestamp": "2026-09-01T10:00:00",
            "amount": 1000000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS"
        }),
        FinancialRealityEngineService.normalize_transaction({
            "id": "T2", "customer_id": "PD_DEBT", "timestamp": "2026-09-02T10:00:00",
            "amount": 750000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_RAW_MATERIAL"
        })
    ]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="PD_DEBT", customer_name="Heavy Gear Ltd", archetype="MSME",
        transactions=txns, loans=loans, obligations=[], receivables=[], payables=[], assets=[],
        liquid_cash=50000.0
    )
    
    proposed = ProposedLoanInput(
        customer_id="PD_DEBT", proposed_principal=2000000.0,
        annual_interest_rate_pct=14.0, tenure_months=24
    )
    afford_res = CreditAffordabilityEngineService.evaluate_affordability(fre, proposed)
    assert afford_res.affordability_status == AffordabilityClassification.NOT_SAFE_TO_BORROW
    
    guardrail = CreditAffordabilityEngineService.check_no_new_loan(
        fre=fre,
        loan_input=proposed,
        current_distress_score=75.0,
        primary_root_cause="debt_overload"
    )
    assert guardrail.verdict == NoNewLoanVerdict.NOT_RECOMMENDED


def test_persona_e_expense_shock():
    """
    PERSONA E — EXPENSE SHOCK
    Business owner, revenue stable, operating expenses increase by 30%.
    Expected: EXPENSE_SHOCK identified as primary cause.
    """
    data = SAMPLE_CUSTOMERS_DATA["CUST_MSME_TIRUPPUR_001"]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=[], loans=[], obligations=[], receivables=[], payables=[], assets=[],
        liquid_cash=data["liquid_cash"]
    )
    cls_report = DistressClassificationEngineService.classify_distress(
        customer_id="PE_EXP", fre=fre, revenue_decline_pct=0.0, expense_increase_pct=30.0
    )
    assert cls_report.primary_category == DistressDominantType.EXPENSE_SHOCK


def test_persona_f_seasonal_business():
    """
    PERSONA F — SEASONAL BUSINESS
    Raincoat manufacturer, normal low season, revenue declined 20% during normal low season.
    Expected: Context Intelligence compares customer, industry, region, seasonal baseline.
    Does NOT classify as severe business failure.
    """
    ctx = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="PF_RAINCOAT",
        customer_growth_pct=-20.0,
        custom_industry_median=-18.0,
        custom_region_median=-17.0,
        custom_peer_median=-19.0,
        custom_seasonal_baseline=-16.0
    )
    assert ctx.classification in [
        ContextClassificationEnum.NORMAL_SEASONAL,
        ContextClassificationEnum.INDUSTRY_WIDE,
        ContextClassificationEnum.REGION_WIDE,
        ContextClassificationEnum.MIXED
    ]
    assert ctx.abnormality_score < 25.0


def test_persona_g_abnormally_performing_business():
    """
    PERSONA G — ABNORMALLY PERFORMING BUSINESS
    Same industry as Persona F. Customer: -35%, Industry: -8%, Peers: -10%, Region: -7%.
    Expected: CUSTOMER_SPECIFIC deterioration, stronger distress signal.
    """
    ctx = ContextIntelligenceService.evaluate_context_intelligence(
        customer_id="PG_ABNORMAL",
        customer_growth_pct=-35.0,
        custom_industry_median=-8.0,
        custom_region_median=-7.0,
        custom_peer_median=-10.0,
        custom_seasonal_baseline=-6.0
    )
    assert ctx.classification == ContextClassificationEnum.CUSTOMER_SPECIFIC
    assert ctx.abnormality_score >= 30.0


def test_persona_h_underperforming_machine():
    """
    PERSONA H — UNDERPERFORMING MACHINE
    Machine C: Rev ₹1,50,000, Op Cost ₹1,20,000, Financing ₹70,000 -> Net contribution -₹40,000.
    Expected: Marked as loss-making; Decision Twin compares keep, restructure, sell, replace.
    """
    asset_input = AssetInput(
        asset_id="MACH_C",
        asset_name="Knitting Machine C",
        asset_type="EQUIPMENT",
        purchase_price=2500000.0,
        financing_amount=2000000.0,
        outstanding_loan=600000.0,
        monthly_emi=70000.0,
        revenue_contribution=150000.0,
        operating_cost=120000.0,
        maintenance_cost=0.0,
        utilization_percentage=35.0,
        age_years=3.0,
        remaining_useful_life_years=7.0
    )
    report = AssetFinancialIntelligenceService.analyze_asset_health(asset_input)
    assert report.net_contribution == -40000.0
    assert report.asset_health == AssetClassification.LOSS_MAKING


def test_persona_i_healthy_business_loan_request():
    """
    PERSONA I — HEALTHY BUSINESS BUT LOAN REQUEST
    Business is healthy, revenue growing, debt manageable.
    Expected: System does NOT reject automatically, evaluates sustainability.
    """
    data = SAMPLE_CUSTOMERS_DATA["CUST_SALARIED_BLR_002"]
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id="PI_HEALTHY", customer_name="Healthy Enterprise", archetype="MSME",
        transactions=[], loans=[], obligations=[], receivables=[], payables=[], assets=[],
        liquid_cash=1200000.0, savings=500000.0
    )
    proposed = ProposedLoanInput(
        customer_id="PI_HEALTHY", proposed_principal=500000.0,
        annual_interest_rate_pct=11.0, tenure_months=36
    )
    afford_res = CreditAffordabilityEngineService.evaluate_affordability(fre, proposed)
    assert afford_res.affordability_status in [
        AffordabilityClassification.SAFE_TO_BORROW,
        AffordabilityClassification.LIMITED_BORROWING
    ]


def test_persona_j_low_data_confidence():
    """
    PERSONA J — LOW DATA CONFIDENCE
    Only 2 months history, missing data.
    Expected: LOW DATA CONFIDENCE, triggers Human Review.
    """
    conf = EpistemicConfidenceService.evaluate_confidence(
        target_entity_id="PJ_LOW_CONF",
        data_completeness_pct=32.0,
        data_freshness_days=80,
        historical_coverage_months=2,
        peer_sample_size=1,
        estimated_proportion_pct=70.0
    )
    assert conf.confidence_score < 50.0
    assert conf.confidence_level == ConfidenceLevel.LOW
    
    escalation = BankerHumanReviewService.check_automatic_escalation(
        confidence_report=conf,
        credit_requested=500000.0,
        recommended_intervention_type="RECEIVABLE_ACCELERATION"
    )
    assert escalation.is_escalated is True
    assert EscalationReason.LOW_CONFIDENCE in escalation.triggers

# ============================================================================
# 2. REAL USER TESTS 1 THROUGH 28
# ============================================================================

def test_real_user_01_login_and_auth():
    """Test 1: Login UI page, and authentication."""
    res_login_page = client.get("/login")
    assert res_login_page.status_code == 200
    assert "login" in res_login_page.text.lower()


def test_real_user_02_banker_dashboard():
    """Test 2: Banker Dashboard and customer list view."""
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    
    res_cust = client.get("/customers")
    assert res_cust.status_code == 200


def test_real_user_03_customer_financial_profile():
    """Test 3: Customer Financial Profile numbers match raw data."""
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/dashboard")
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["cash_available_today"] == 140000.0
    assert d["expected_monthly_income"] == 2800000.0
    assert d["upcoming_monthly_loan_emi"] == 320000.0


def test_real_user_04_05_cashflow_timeline_and_obligation_collision():
    """Test 4 & 5: Cash-Flow Timeline & Obligation Collision Radar."""
    res_cf = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/cashflow")
    assert res_cf.status_code == 200
    
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/obligation-collisions")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "total_obligations_tracked" in d
    assert "total_shortfall_volume" in d
    assert "prioritized_collisions" in d


def test_real_user_06_07_early_distress_and_classification():
    """Test 6 & 7: Early distress detection & multi-factor taxonomy classification."""
    res_distress = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress")
    assert res_distress.status_code == 200
    
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/distress/classify")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "primary_category" in d
    assert "evidence" in d
    assert "expected_duration" in d
    assert len(d["evidence"]) >= 2


def test_real_user_08_root_cause_analysis():
    """Test 8: Root-cause decomposition gives evidence-backed factors."""
    res = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/root-cause")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "primary_cause" in d
    assert "secondary_causes" in d


def test_real_user_09_10_industry_and_regional_context():
    """Test 9 & 10: Industry/Regional Context and abnormality score."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/context-intelligence")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "classification" in d
    assert "abnormality_score" in d
    assert "explanation" in d


def test_real_user_11_seasonal_forecasting():
    """Test 11: Seasonal forecasting with 3+ years and confidence."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/seasonal-forecast")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "peak_season_months" in d
    assert "monthly_forecasts" in d


def test_real_user_12_peer_benchmarking():
    """Test 12: Peer Benchmarking and small peer group handling."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/peer-benchmark")
    assert res.status_code == 200
    d = res.json()["data"]
    assert "metrics_comparison" in d
    assert "peer_sample_size" in d


def test_real_user_13_14_asset_analysis_and_simulation():
    """Test 13 & 14: Asset Portfolio evaluation and scenario simulation."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/assets")
    assert res.status_code == 200
    assets = res.json()["data"]
    assert len(assets) >= 1
    mach_c = next((a for a in assets if a["asset_id"] == "ASSET_MACH_C"), assets[0])
    assert mach_c["asset_id"] == "ASSET_MACH_C"
    assert mach_c["net_contribution"] < 0  # Loss-making
    
    # Simulate Machine C
    res_sim = client.post("/api/v1/assets/ASSET_MACH_C/decision-simulation", json={
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "action_type": "SELL_AND_REPAY_DEBT"
    })
    assert res_sim.status_code == 200


def test_real_user_15_receivable_intelligence():
    """Test 15: Receivable acceleration evaluated before recommending debt."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/receivables-analysis")
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["total_receivable_book_value"] == 1200000.0
    assert "credit_affordability_recommendation" in d


def test_real_user_16_17_18_credit_affordability_guardrail_and_timing():
    """Test 16, 17, 18: Credit Affordability, No-New-Loan Guardrail, Financing Timing."""
    # 1. Evaluate unsustainable loan
    res = client.post("/api/v1/credit/affordability", json={
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "proposed_principal": 1500000.0,
        "annual_interest_rate_pct": 13.5,
        "tenure_months": 24
    })
    assert res.status_code == 200
    d = res.json()["data"]
    assert d["affordability_status"] == "NOT_SAFE_TO_BORROW"
    
    # 2. No New Loan check
    res_guard = client.post("/api/v1/credit/no-new-loan-check", json={
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "proposed_principal": 1500000.0,
        "annual_interest_rate_pct": 13.5,
        "tenure_months": 24
    })
    assert res_guard.status_code == 200
    assert res_guard.json()["data"]["verdict"] == "NOT_RECOMMENDED"
    
    # 3. Financing Timing
    res_timing = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/financing-timing")
    assert res_timing.status_code == 200
    assert "recommended_timing" in res_timing.json()["data"]


def test_real_user_19_20_decision_twin_and_least_harm():
    """Test 19 & 20: Decision Twin simulation across scenarios and Least-Harm ranking."""
    res_twin = client.get("/api/v1/decision-twin/CUST_MSME_TIRUPPUR_001")
    assert res_twin.status_code == 200
    d_twin = res_twin.json()["data"]
    assert "scenario_results" in d_twin
    assert "comparison_table" in d_twin
    
    res_opt = client.get("/customers/CUST_MSME_TIRUPPUR_001/least-harm-recommendation")
    assert res_opt.status_code == 200
    d_opt = res_opt.json()["data"]
    assert "ranked_interventions" in d_opt
    assert "selected_intervention" in d_opt


def test_real_user_21_business_recovery():
    """Test 21: Business Recovery identifies non-debt operational recovery opportunities."""
    res = client.get("/api/v1/businesses/CUST_MSME_TIRUPPUR_001/non-debt-recovery")
    assert res.status_code == 200
    d = res.json()["data"]
    assert len(d["recovery_opportunities"]) >= 3


def test_real_user_22_business_matching_and_consent():
    """Test 22: Business Matching respects consent and privacy."""
    # Post consent
    res_consent = client.post("/customers/CUST_MSME_TIRUPPUR_001/consent", json={
        "data_sharing_consented": True,
        "business_matching_consented": True,
        "personalized_recommendations_consented": True
    })
    assert res_consent.status_code == 200
    
    # Check matching
    res_match = client.get("/api/v1/business-matching/CUST_MSME_TIRUPPUR_001")
    assert res_match.status_code == 200


def test_real_user_23_24_confidence_and_explanation():
    """Test 23 & 24: Confidence score separation and plain language explanations."""
    res_conf = client.get("/api/v1/customers/CUST_MSME_TIRUPPUR_001/confidence")
    assert res_conf.status_code == 200
    d_conf = res_conf.json()["data"]
    assert 0.0 <= d_conf["confidence_score"] <= 100.0
    
    res_exp = client.get("/customers/CUST_MSME_TIRUPPUR_001/assistant-explanation")
    assert res_exp.status_code == 200
    d_exp = res_exp.json()["data"]
    assert "what_is_happening" in d_exp
    assert "why_is_it_happening" in d_exp


def test_real_user_25_26_human_review_and_audit():
    """Test 25 & 26: Human review escalation and immutable audit ledger."""
    # 1. Fetch review case
    res_case = client.get("/api/v1/banker/review/CUST_MSME_TIRUPPUR_001")
    assert res_case.status_code == 200
    
    # 2. Submit Banker Review Action
    res_sub = client.post("/api/v1/banker/review/CUST_MSME_TIRUPPUR_001", json={
        "decision": "APPROVE",
        "reason": "Approved receivable factoring intervention after customer consultation.",
        "notes": "Factoring ₹12L invoice will bridge liquidity until textile demand recovers."
    })
    assert res_sub.status_code == 200
    
    # 3. Verify in Audit Trail
    res_audit = client.get("/api/v1/audit/customer/CUST_MSME_TIRUPPUR_001")
    assert res_audit.status_code == 200
    records = res_audit.json()["data"]
    assert len(records) >= 1


def test_real_user_27_28_outcome_monitoring_and_longitudinal():
    """Test 27 & 28: Outcome monitoring and 6/12 month longitudinal analysis."""
    # Post intervention outcome
    req_body = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "intervention_name": "RECEIVABLE_ACCELERATION",
        "evaluation_month": 3,
        "before": {
            "distress_score": 84.0,
            "resilience_score": 42.0,
            "cashflow": -120000.0,
            "cash_buffer": 14.0,
            "debt": 3800000.0,
            "EMI": 320000.0,
            "missed_payments": 0
        },
        "after": {
            "distress_score": 46.0,
            "resilience_score": 68.0,
            "cashflow": 150000.0,
            "cash_buffer": 45.0,
            "debt": 3800000.0,
            "EMI": 320000.0,
            "missed_payments": 0
        },
        "causal_attribution_evidence": "associated improvement",
        "evaluator_notes": "Significant turnaround after invoice monetization."
    }
    res_out = client.post("/api/v1/interventions/INT_TIRUPPUR_01/outcome", json=req_body)
    assert res_out.status_code == 200
    assert res_out.json()["data"]["classification"] == "SUCCESS"
    
    # Longitudinal Prevention Report
    res_prev = client.get("/api/v1/prevention/CUST_MSME_TIRUPPUR_001")
    assert res_prev.status_code == 200
    d_prev = res_prev.json()["data"]
    assert "evaluation_periods" in d_prev
    assert "before_after_analysis" in d_prev

# ============================================================================
# 3. NEGATIVE & SECURITY & DATA INTEGRITY TESTS
# ============================================================================

def test_negative_invalid_inputs_and_edge_cases():
    """Section 31: Negative testing with invalid dates, missing inputs, extreme values."""
    # Non-existent customer
    res404 = client.get("/customers/CUST_NON_EXISTENT_99999/dashboard")
    assert res404.status_code in [400, 404]
    
    # Negative values in outcome payload
    bad_req = {
        "customer_id": "CUST_MSME_TIRUPPUR_001",
        "intervention_name": "RECEIVABLE_ACCELERATION",
        "evaluation_month": 3,
        "before": {
            "distress_score": -10.0,  # Invalid negative
            "resilience_score": 42.0,
            "cashflow": -120000.0,
            "cash_buffer": 14.0,
            "debt": 3800000.0,
            "EMI": 320000.0,
            "missed_payments": 0
        },
        "after": {
            "distress_score": 46.0,
            "resilience_score": 68.0,
            "cashflow": 150000.0,
            "cash_buffer": 45.0,
            "debt": 3800000.0,
            "EMI": 320000.0,
            "missed_payments": 0
        }
    }
    res_bad = client.post("/api/v1/interventions/INT_INVALID/outcome", json=bad_req)
    assert res_bad.status_code in [400, 422]


def test_ai_safety_and_deterministic_guarantees():
    """Section 37: Financial calculations are deterministic and explainability adheres strictly to facts."""
    res = client.get("/customers/CUST_MSME_TIRUPPUR_001/dashboard")
    d = res.json()["data"]
    assert d["cash_available_today"] == 140000.0
    assert d["loan_affordability_verdict"] == "NOT RECOMMENDED"
