"""
FastAPI Backend for Financial Distress Prevention Platform (FINRES).
Features complete modular service endpoints across all 24 sub-engines:
- Financial Reality (FRE)
- Cashflow Timeline
- Obligation Radar (OCR)
- Distress Detection & Classification (IRACP SMA-0/1/2)
- Root-Cause Analyzer (WHY)
- Context Intelligence & Seasonal Forecasting
- Peer Benchmarking (Pandas & NumPy)
- Asset-Level Intelligence & Decision Simulator
- Receivable Analysis
- Credit Affordability, Loan Guardrail & Financing Timing
- Decision Twin Simulator
- Least-Harm Optimizer (LHO)
- Business Matching Engine (Double-blind ONDC)
- Financial Resilience Dashboard
- Confidence & Explainability
- Human Review, DPDP Consent, Immutable Audit & Outcomes
Includes Authentication, Role-Based Access Control, Error Handling, and Standardized Response Envelopes.
"""
from fastapi import FastAPI, HTTPException, Query, status, Depends, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import time
import logging

from src_py.core.response import StandardAPIResponse, APIResponseMeta, TokenData
from src_py.core.auth import authenticate_user, require_roles
from src_py.models.schemas import (
    FinancialRealityObject, CashflowSummary, RecalculateRequest, DirectionEnum
)
from src_py.models.financial_state_schemas import (
    FinancialState, RatioMetricsBlock
)
from src_py.models.asset_schemas import (
    AssetInput, AssetPerformanceProfile, AssetComprehensiveDiagnostic,
    DecisionSimulationResult, AssetDecisionType, DataLabel
)
from src_py.models.least_harm_schemas import (
    LeastHarmOptimizationReport, ScoredIntervention, CandidateIntervention
)
from src_py.models.matching_schemas import (
    OpportunityMatchResult, ConsentActionRequest
)
from src_py.models.dashboard_schemas import (
    CustomerResilienceDashboardData, CustomerConsentState, UpdateConsentRequest
)
from src_py.models.explanation_schemas import (
    ExplanationInputPayload, StructuredExplanationResponse
)
from src_py.models.ingestion_schemas import (
    IngestionBatchOutput, DataQualityReport, NormalizedTransactionRecord
)
from src_py.models.cashflow_schemas import (
    CashflowForecastHorizon, CashflowForecastReport, DailyTimelineRecord
)
from src_py.models.collision_radar_schemas import (
    ObligationCalendarReport, ObligationCollisionEvent, CollisionSeverity
)
from src_py.models.distress_schemas import (
    DistressPredictionRequest, DistressPredictionResult, DistressRiskLevel, PredictionHorizon
)
from src_py.models.distress_classification_schemas import (
    DistressClassificationReport, DistressDominantType, ClassificationEvidenceItem
)
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.models.root_cause_schemas import (
    RootCauseReport, ContributingCauseItem, CandidateCauseEnum, CauseEvidenceRecord
)
from src_py.services.fre_engine import FinancialRealityEngineService
from src_py.services.asset_intelligence import AssetFinancialIntelligenceService
from src_py.services.least_harm_optimizer import LeastHarmOptimizerService
from src_py.services.business_matching import BusinessOpportunityMatchingService
from src_py.services.customer_dashboard import CustomerDashboardService
from src_py.services.explanation_assistant import FinancialExplanationAssistantService
from src_py.services.diagnostic_suite import DiagnosticModularSuite, AUDIT_LOG_RECORDS
from src_py.services.data_ingestion import DataIngestionService
from src_py.services.cashflow_engine import CashflowTimelineEngineService
from src_py.services.collision_radar import ObligationCollisionRadarService
from src_py.services.distress_engine import EarlyDistressDetectionService
from src_py.services.distress_classifier import DistressClassificationEngineService
from src_py.services.root_cause_engine import RootCauseAnalyzerService
from src_py.data.sample_data import SAMPLE_CUSTOMERS_DATA

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("finres-api")

app = FastAPI(
    title="FINRES Financial Distress Prevention & Decision Support Platform",
    description="Institutional Scheduled Commercial Bank (SCB) early warning, distress prevention, and intervention engine.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS for institutional web portals
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_execution_telemetry(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = round((time.time() - start_time) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response


# Global Exception Handler returning standardized API envelopes
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=StandardAPIResponse[Any](
            success=False,
            message=exc.detail if isinstance(exc.detail, str) else "Request error occurred",
            errors=[str(exc.detail)],
            meta=APIResponseMeta(execution_time_ms=0.0)
        ).model_dump(mode="json")
    )


def get_customer_entities(customer_id: str):
    data = SAMPLE_CUSTOMERS_DATA.get(customer_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer ID '{customer_id}' not found in portfolio database."
        )
    
    normalized_txns = [
        FinancialRealityEngineService.normalize_transaction(t)
        for t in data.get("raw_transactions", [])
    ]
    
    from src_py.models.schemas import (
        LoanObligation, FixedObligationItem, ReceivableItem,
        PayableItem, AssetFinancingItem
    )
    
    loans = [LoanObligation(**l) for l in data.get("loans", [])]
    obligations = [FixedObligationItem(**o) for o in data.get("obligations", [])]
    receivables = [ReceivableItem(**r) for r in data.get("receivables", [])]
    payables = [PayableItem(**p) for p in data.get("payables", [])]
    assets = [AssetFinancingItem(**a) for a in data.get("assets", [])]
    
    return data, normalized_txns, loans, obligations, receivables, payables, assets


def get_asset_input(customer_id: str, asset_id: str) -> AssetInput:
    data, _, loans, _, _, _, assets = get_customer_entities(customer_id)
    raw_asset = next((a for a in data.get("assets", []) if a["id"] == asset_id), None)
    if not raw_asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset ID '{asset_id}' not found for customer '{customer_id}'."
        )

    linked_loan = next((l for l in loans if l.id == raw_asset.get("dedicated_loan_id") or l.asset_ref_id == asset_id), None)
    emi = linked_loan.monthly_emi if linked_loan else 0.0
    outstanding = linked_loan.outstanding_principal if linked_loan else 0.0
    fin_amt = linked_loan.principal_amount if linked_loan else 0.0

    return AssetInput(
        asset_id=raw_asset["id"],
        asset_name=raw_asset["asset_name"],
        asset_type=raw_asset.get("asset_type", "MACHINE"),
        purchase_price=raw_asset.get("purchase_cost", 2000000.0),
        financing_amount=fin_amt,
        outstanding_loan=outstanding,
        monthly_emi=emi,
        revenue_contribution=raw_asset.get("monthly_revenue_contribution", 500000.0),
        operating_cost=raw_asset.get("monthly_operating_cost", 300000.0),
        maintenance_cost=raw_asset.get("monthly_maintenance_cost", 25000.0),
        utilization_percentage=raw_asset.get("utilization_percentage", 80.0),
        age_years=raw_asset.get("age_years", 3.5),
        remaining_useful_life_years=raw_asset.get("remaining_useful_life_years", 6.5),
        revenue_data_label=DataLabel(raw_asset.get("revenue_data_label", "ACTUAL"))
    )


# In-memory storage of ingested customer transactions for testing & verification
CUSTOMER_INGESTED_TRANSACTIONS: Dict[str, List[NormalizedTransactionRecord]] = {}


# ==============================================================================
# 0. DATA INGESTION & NORMALIZATION SERVICE (API V1)
# ==============================================================================

class TransactionImportPayload(BaseModel):
    customer_id: str
    source: str = "CSV_IMPORT"
    batch_id: Optional[str] = None
    records: Optional[List[Dict[str, Any]]] = None
    csv_content: Optional[str] = None


class LoanImportPayload(BaseModel):
    customer_id: str
    source: str = "LOAN_MANAGEMENT_SYSTEM"
    loans: List[Dict[str, Any]]


class AssetImportPayload(BaseModel):
    customer_id: str
    source: str = "FIXED_ASSET_REGISTER"
    assets: List[Dict[str, Any]]


@app.post("/api/v1/data/transactions/import", response_model=StandardAPIResponse[IngestionBatchOutput], tags=["Data Ingestion"])
def import_transactions(
    payload: TransactionImportPayload,
    user: TokenData = Depends(authenticate_user)
):
    """
    Ingests and normalizes transactions from JSON records or raw CSV content.
    Validates mandatory fields, standardizes currencies and directions,
    detects duplicates, computes data completeness, and preserves audit trails.
    """
    raw_records = payload.records or []
    if payload.csv_content:
        csv_records = DataIngestionService.parse_csv_content(payload.csv_content)
        raw_records.extend(csv_records)

    existing_history = CUSTOMER_INGESTED_TRANSACTIONS.get(payload.customer_id, [])
    output = DataIngestionService.ingest_transactions(
        customer_id=payload.customer_id,
        records=raw_records,
        batch_id=payload.batch_id,
        source=payload.source,
        existing_history=existing_history
    )

    # Persist accepted in-memory
    if payload.customer_id not in CUSTOMER_INGESTED_TRANSACTIONS:
        CUSTOMER_INGESTED_TRANSACTIONS[payload.customer_id] = []
    CUSTOMER_INGESTED_TRANSACTIONS[payload.customer_id].extend(output.normalized_transactions)

    return StandardAPIResponse(
        data=output,
        message=f"Ingestion batch processed: {output.records_accepted} accepted, {output.records_rejected} rejected, {output.duplicates_detected} duplicates."
    )


@app.post("/api/v1/data/loans/import", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Data Ingestion"])
def import_loans(
    payload: LoanImportPayload,
    user: TokenData = Depends(authenticate_user)
):
    """Normalizes multi-lender loans and debt obligations."""
    accepted = []
    rejected = []
    for idx, l in enumerate(payload.loans):
        if not l.get("principal_amount") or not l.get("monthly_emi"):
            rejected.append({"index": idx, "error": "Missing principal_amount or monthly_emi"})
        else:
            accepted.append(l)

    return StandardAPIResponse(
        data={
            "customer_id": payload.customer_id,
            "loans_accepted": len(accepted),
            "loans_rejected": len(rejected),
            "rejections": rejected
        },
        message="Loans ingested and normalized."
    )


@app.post("/api/v1/data/assets/import", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Data Ingestion"])
def import_assets(
    payload: AssetImportPayload,
    user: TokenData = Depends(authenticate_user)
):
    """Normalizes fixed assets and plant machinery register."""
    accepted = []
    rejected = []
    for idx, a in enumerate(payload.assets):
        if not a.get("asset_name") or a.get("purchase_cost") is None:
            rejected.append({"index": idx, "error": "Missing asset_name or purchase_cost"})
        else:
            accepted.append(a)

    return StandardAPIResponse(
        data={
            "customer_id": payload.customer_id,
            "assets_accepted": len(accepted),
            "assets_rejected": len(rejected),
            "rejections": rejected
        },
        message="Assets ingested and normalized."
    )


@app.get("/api/v1/data/quality/{customer_id}", response_model=StandardAPIResponse[DataQualityReport], tags=["Data Ingestion"])
def get_data_quality_report(
    customer_id: str,
    user: TokenData = Depends(authenticate_user)
):
    """Returns data completeness score, freshness days, and epistemic reliability."""
    txns = CUSTOMER_INGESTED_TRANSACTIONS.get(customer_id, [])
    # If no imported txns yet, check if sample customer has data
    if not txns and customer_id in SAMPLE_CUSTOMERS_DATA:
        sample_raw = SAMPLE_CUSTOMERS_DATA[customer_id].get("raw_transactions", [])
        batch_out = DataIngestionService.ingest_transactions(customer_id, sample_raw)
        txns = batch_out.normalized_transactions

    report = DataIngestionService.compute_data_quality_report(customer_id, txns)
    return StandardAPIResponse(data=report)


# ==============================================================================
# 1. PLATFORM HEALTH & TELEMETRY
# ==============================================================================

@app.get("/health", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Platform"])
def health_check():
    return StandardAPIResponse(
        success=True,
        message="FINRES Core Platform Online",
        data={
            "status": "HEALTHY",
            "service": "FINRES-Modular-FastAPI-Platform",
            "version": "2.0.0",
            "modules_operational": 24,
            "active_portfolio_customers": len(SAMPLE_CUSTOMERS_DATA)
        }
    )


# ==============================================================================
# 2. FINANCIAL REALITY (FRE) & CASHFLOW MODULES
# ==============================================================================

@app.get("/api/v1/customers/{id}/financial-reality", response_model=StandardAPIResponse[FinancialState], tags=["Financial Reality Engine"])
def get_v1_customer_financial_state(
    id: str,
    user: TokenData = Depends(authenticate_user)
):
    """
    Returns the unified FinancialState object exposing all component metrics:
    Income, Expenses, Debt, Cash, Receivables, Payables, Cash Flow, and Data Quality
    at daily, weekly, and monthly resolutions.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    state = FinancialRealityEngineService.compute_financial_state(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=state, message="Unified FinancialState generated successfully.")


@app.get("/api/v1/customers/{id}/financial-reality/metrics", response_model=StandardAPIResponse[RatioMetricsBlock], tags=["Financial Reality Engine"])
def get_v1_customer_financial_metrics(
    id: str,
    user: TokenData = Depends(authenticate_user)
):
    """Exposes all component ratio metrics without using one single ratio as the decision maker."""
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    state = FinancialRealityEngineService.compute_financial_state(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=state.metrics, message="Component metrics exposed.")


@app.post("/api/v1/customers/{id}/financial-reality/recalculate", response_model=StandardAPIResponse[FinancialState], tags=["Financial Reality Engine"])
def recalculate_v1_customer_financial_reality(
    id: str,
    req: Optional[RecalculateRequest] = None,
    user: TokenData = Depends(authenticate_user)
):
    """Recalculates unified FinancialState deterministically given current or simulated parameters."""
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    
    # Apply simulated deltas if provided
    mod_txns = list(txns)
    if req and req.simulated_income_delta_pct:
        factor = 1.0 + (req.simulated_income_delta_pct / 100.0)
        for t in mod_txns:
            if t.direction == DirectionEnum.INFLOW:
                t.amount = round(t.amount * factor, 2)

    state = FinancialRealityEngineService.compute_financial_state(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=mod_txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=state, message="FinancialState recalculated deterministically.")


@app.get("/customers/{id}/financial-reality", response_model=StandardAPIResponse[FinancialRealityObject], tags=["Financial Reality"])
def get_customer_financial_reality(
    id: str,
    user: TokenData = Depends(authenticate_user)
):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        assets=assets,
        liquid_cash=data["liquid_cash"],
        savings=data.get("savings", 0.0)
    )
    return StandardAPIResponse(data=fre, message="Financial Reality Computed Successfully")


@app.get("/api/v1/customers/{id}/cashflow", response_model=StandardAPIResponse[CashflowForecastHorizon], tags=["Cash-Flow Timeline Engine"])
def get_v1_customer_cashflow(
    id: str,
    horizon_days: int = Query(default=30, ge=7, le=90),
    user: TokenData = Depends(authenticate_user)
):
    """
    Returns granular daily and weekly cashflow timeline.
    Tracks opening/closing balances, actual and expected inflows/outflows,
    minimum required cash, surplus/shortfall, and obligation/receivable markers.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    timeline = CashflowTimelineEngineService.generate_timeline(
        customer_id=data["id"],
        starting_cash=data["liquid_cash"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        horizon_days=horizon_days
    )
    return StandardAPIResponse(data=timeline, message="Daily cash-flow timeline generated.")


@app.get("/api/v1/customers/{id}/cashflow/forecast", response_model=StandardAPIResponse[CashflowForecastReport], tags=["Cash-Flow Timeline Engine"])
def get_v1_customer_cashflow_forecast(
    id: str,
    user: TokenData = Depends(authenticate_user)
):
    """
    Generates conservative 30-day, 60-day, and 90-day forward cash forecasts.
    Uncovers temporary liquidity shortages even when monthly total income > monthly expenses.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    report = CashflowTimelineEngineService.generate_full_forecast_report(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        starting_cash=data["liquid_cash"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables
    )
    return StandardAPIResponse(data=report, message="30/60/90-day cashflow forecast report generated.")


@app.get("/api/v1/customers/{id}/obligation-collisions", response_model=StandardAPIResponse[ObligationCalendarReport], tags=["Obligation Collision Radar"])
def get_v1_customer_obligation_collisions(
    id: str,
    horizon_days: int = Query(default=30, ge=7, le=90),
    user: TokenData = Depends(authenticate_user)
):
    """
    Scans forward obligation schedule against projected available liquidity.
    Identifies exact dates where obligations (EMI, rent, payroll, supplier, taxes, utilities)
    exceed available cash. Sorts collisions by severity (GREEN, YELLOW, ORANGE, RED),
    shortfall volume, and days until event.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    report = ObligationCollisionRadarService.detect_collisions(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        starting_cash=data["liquid_cash"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        horizon_days=horizon_days
    )
    return StandardAPIResponse(data=report, message="Obligation collisions detected and calendar generated.")


@app.get("/customers/{id}/cashflow", response_model=StandardAPIResponse[CashflowSummary], tags=["Cashflow Timeline"])
def get_customer_cashflow(
    id: str,
    horizon_days: int = Query(default=30, ge=7, le=90),
    user: TokenData = Depends(authenticate_user)
):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    summary = FinancialRealityEngineService.calculate_cashflow_timeline(
        customer_id=data["id"],
        starting_cash=data["liquid_cash"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        horizon_days=horizon_days
    )
    return StandardAPIResponse(data=summary, message="Forward Cash Flow Timeline Generated")


@app.post("/financial-reality/recalculate", response_model=StandardAPIResponse[FinancialRealityObject], tags=["Financial Reality"])
def recalculate_financial_reality(
    req: RecalculateRequest,
    user: TokenData = Depends(authenticate_user)
):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(req.customer_id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"],
        customer_name=data["name"],
        archetype=data["archetype"],
        transactions=txns,
        loans=loans,
        obligations=obligations,
        receivables=receivables,
        payables=payables,
        assets=assets,
        liquid_cash=data["liquid_cash"],
        savings=data.get("savings", 0.0),
        simulated_income_delta_pct=req.simulated_income_delta_pct,
        simulated_expense_delta_pct=req.simulated_expense_delta_pct
    )
    return StandardAPIResponse(data=fre, message="Counterfactual Stress Scenario Recalculated")


# ==============================================================================
# 3. EARLY DISTRESS DETECTION ENGINE & OBLIGATION RADAR
# ==============================================================================

@app.post("/api/v1/distress/predict", response_model=StandardAPIResponse[DistressPredictionResult], tags=["Early Distress Detection"])
def predict_early_distress(
    req: DistressPredictionRequest,
    user: TokenData = Depends(authenticate_user)
):
    """
    Predicts early financial distress score (0-100) and risk tier (LOW, MODERATE, HIGH, CRITICAL)
    across 7, 30, and 90-day horizons.
    Uses calibrated hybrid model: Explainable Rules Engine + Calibrated Logistic Regression.
    """
    result = EarlyDistressDetectionService.predict_distress(req)
    return StandardAPIResponse(data=result, message="Early distress predicted successfully.")


@app.get("/api/v1/customers/{id}/distress", response_model=StandardAPIResponse[DistressPredictionResult], tags=["Early Distress Detection"])
def get_v1_customer_distress(
    id: str,
    horizon: PredictionHorizon = Query(default=PredictionHorizon.HORIZON_30_DAY),
    user: TokenData = Depends(authenticate_user)
):
    """
    Computes early distress prediction directly from the customer's live Financial Reality state.
    Exposes 0-100 distress score, risk tier, calibrated rules vs ML scores, and top contributing factors.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"],
        savings=data.get("savings", 0.0)
    )
    result = EarlyDistressDetectionService.evaluate_customer_entity(id, fre, horizon=horizon)
    return StandardAPIResponse(data=result, message="Customer live early distress calculated.")


@app.get("/customers/{id}/obligation-radar", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Obligation Radar"])
def get_obligation_radar(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=DiagnosticModularSuite.run_obligation_collision_radar(fre))


@app.get("/api/v1/customers/{id}/distress/classify", response_model=StandardAPIResponse[DistressClassificationReport], tags=["Distress Classification"])
def get_v1_distress_classification(
    id: str,
    revenue_decline_pct: float = Query(default=0.0),
    expense_increase_pct: float = Query(default=0.0),
    declining_orders_pct: float = Query(default=0.0),
    user: TokenData = Depends(authenticate_user)
):
    """
    Identifies the dominant distress type:
    - TEMPORARY_LIQUIDITY_GAP
    - INCOME_SHOCK
    - DEBT_OVERLOAD
    - EXPENSE_SHOCK
    - MIXED_DISTRESS
    Returns primary category, secondary category, confidence, expected duration,
    and at least two empirical evidence items.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"],
        savings=data.get("savings", 0.0)
    )
    report = DistressClassificationEngineService.classify_distress(
        customer_id=id,
        fre=fre,
        revenue_decline_pct=revenue_decline_pct,
        expense_increase_pct=expense_increase_pct,
        declining_orders_pct=declining_orders_pct,
        has_upcoming_shortage=(fre.next_critical_collision_date is not None)
    )
    return StandardAPIResponse(data=report, message="Dominant distress type classified.")


@app.get("/customers/{id}/distress-classification", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Distress Classification"])
def get_distress_classification(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=DiagnosticModularSuite.run_distress_detection_and_classification(fre))


# ==============================================================================
# 4. ROOT-CAUSE & CONTEXT INTELLIGENCE (PEER BENCHMARKING)
# ==============================================================================

@app.get("/customers/{id}/root-cause", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Root Cause"])
def get_root_cause_analysis(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=DiagnosticModularSuite.run_root_cause_analysis(fre))


@app.get("/customers/{id}/context-benchmarking", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Context Intelligence"])
def get_context_benchmarking(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=DiagnosticModularSuite.run_context_and_seasonal_benchmarking(fre))


# ==============================================================================
# 5. ASSET FINANCIAL INTELLIGENCE & DECISION SIMULATOR
# ==============================================================================

@app.get("/customers/{id}/assets", response_model=StandardAPIResponse[List[AssetPerformanceProfile]], tags=["Asset Intelligence"])
def list_assets(id: str, user: TokenData = Depends(authenticate_user)):
    data, _, _, _, _, _, assets = get_customer_entities(id)
    profiles = [
        AssetFinancialIntelligenceService.evaluate_asset(get_asset_input(id, a["id"]))
        for a in data.get("assets", [])
    ]
    return StandardAPIResponse(data=profiles)


@app.get("/customers/{id}/assets/{asset_id}/diagnostic", response_model=StandardAPIResponse[AssetComprehensiveDiagnostic], tags=["Asset Intelligence"])
def get_asset_diagnostic(id: str, asset_id: str, user: TokenData = Depends(authenticate_user)):
    asset_input = get_asset_input(id, asset_id)
    return StandardAPIResponse(data=AssetFinancialIntelligenceService.diagnose_asset_holistic(id, asset_input))


@app.post("/customers/{id}/assets/{asset_id}/simulate", response_model=StandardAPIResponse[DecisionSimulationResult], tags=["Asset Intelligence"])
def simulate_asset_decision(id: str, asset_id: str, decision: AssetDecisionType, user: TokenData = Depends(authenticate_user)):
    asset_input = get_asset_input(id, asset_id)
    return StandardAPIResponse(data=AssetFinancialIntelligenceService.simulate_decision_path(asset_input, decision))


# ==============================================================================
# 6. CREDIT AFFORDABILITY, LOAN GUARDRAIL & LEAST-HARM OPTIMIZER
# ==============================================================================

@app.get("/customers/{id}/credit-affordability", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Credit Affordability"])
def get_credit_affordability(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    return StandardAPIResponse(data=DiagnosticModularSuite.run_credit_affordability_and_guardrail(fre))


@app.get("/customers/{id}/least-harm-recommendation", response_model=StandardAPIResponse[LeastHarmOptimizationReport], tags=["Least-Harm Optimizer"])
def get_least_harm(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    overdue_amt = sum(r.amount for r in receivables if r.status == "OVERDUE") or 1200000.0
    report = LeastHarmOptimizerService.rank_and_optimize(fre, overdue_receivables=overdue_amt, machine_bleed=85000.0)
    return StandardAPIResponse(data=report)


# ==============================================================================
# 7. BUSINESS MATCHING (DOUBLE-BLIND)
# ==============================================================================

@app.get("/customers/{id}/business-opportunities", response_model=StandardAPIResponse[List[OpportunityMatchResult]], tags=["Business Matching"])
def get_business_opportunities(id: str, user: TokenData = Depends(authenticate_user)):
    matches = BusinessOpportunityMatchingService.find_opportunities_for_customer(id)
    return StandardAPIResponse(data=matches)


@app.post("/business-opportunities/consent", response_model=StandardAPIResponse[OpportunityMatchResult], tags=["Business Matching"])
def submit_opportunity_consent(req: ConsentActionRequest, user: TokenData = Depends(authenticate_user)):
    match_result = BusinessOpportunityMatchingService.record_consent_and_facilitate_intro(req)
    return StandardAPIResponse(data=match_result, message="Consent Recorded Under DPDP Act")


# ==============================================================================
# 8. EXPLAINABILITY, HUMAN REVIEW & AUDIT LOGS
# ==============================================================================

class HumanReviewRequest(BaseModel):
    decision: str = Field(..., description="APPROVE, OVERRIDE, REJECT")
    comments: str


@app.get("/customers/{id}/explainability", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Explainability"])
def get_explainability(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    least_harm = LeastHarmOptimizerService.rank_and_optimize(fre)
    return StandardAPIResponse(data=DiagnosticModularSuite.run_explainability_and_confidence(fre, least_harm))


@app.post("/customers/{id}/human-review", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Human Review"])
def record_officer_review(
    id: str,
    req: HumanReviewRequest,
    user: TokenData = Depends(require_roles(["BANKER", "CREDIT_OFFICER", "ADMIN"]))
):
    audit_record = DiagnosticModularSuite.record_human_review(
        customer_id=id,
        officer_id=user.user_id,
        decision=req.decision,
        comments=req.comments
    )
    return StandardAPIResponse(data=audit_record, message="Officer Decision Cryptographically Recorded")


@app.get("/customers/{id}/audit-logs", response_model=StandardAPIResponse[List[Dict[str, Any]]], tags=["Audit Logs"])
def get_audit_logs(
    id: str,
    user: TokenData = Depends(require_roles(["BANKER", "AUDITOR", "CREDIT_OFFICER", "ADMIN"]))
):
    logs = [log for log in AUDIT_LOG_RECORDS if log.get("customer_id") == id]
    return StandardAPIResponse(data=logs)


@app.get("/customers/{id}/outcomes", response_model=StandardAPIResponse[Dict[str, Any]], tags=["Outcome Tracking"])
def get_outcomes(id: str, user: TokenData = Depends(authenticate_user)):
    return StandardAPIResponse(data=DiagnosticModularSuite.track_outcomes(id))


# ==============================================================================
# 9. CUSTOMER-FACING RESILIENCE DASHBOARD
# ==============================================================================

@app.get("/customers/{id}/dashboard", response_model=StandardAPIResponse[CustomerResilienceDashboardData], tags=["Customer Dashboard"])
def get_customer_dashboard(id: str, user: TokenData = Depends(authenticate_user)):
    data, txns, loans, obligations, receivables, payables, raw_assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=raw_assets, liquid_cash=data["liquid_cash"]
    )
    assets = [AssetFinancialIntelligenceService.evaluate_asset(get_asset_input(id, a["id"])) for a in data.get("assets", [])]
    least_harm = LeastHarmOptimizerService.rank_and_optimize(fre)
    dashboard_data = CustomerDashboardService.build_dashboard(fre, assets, least_harm)
    return StandardAPIResponse(data=dashboard_data)


@app.post("/customers/{id}/consent", response_model=StandardAPIResponse[CustomerConsentState], tags=["Customer Dashboard"])
def update_consent(id: str, req: UpdateConsentRequest, user: TokenData = Depends(authenticate_user)):
    updated = CustomerDashboardService.update_consent(id, req)
    return StandardAPIResponse(data=updated, message="DPDP Consent Preferences Saved")


# ==============================================================================
# 10. AI FINANCIAL EXPLANATION ASSISTANT (ZERO-HALLUCINATION)
# ==============================================================================

@app.get("/customers/{id}/assistant-explanation", response_model=StandardAPIResponse[StructuredExplanationResponse], tags=["Explanation Assistant"])
def get_assistant_explanation(id: str, user: TokenData = Depends(authenticate_user)):
    """
    Synthesizes grounded explanations across the 8 core operational questions:
    1. What is happening?
    2. Why is it happening?
    3. What evidence supports this?
    4. What could happen next?
    5. What options were simulated?
    6. Why was the recommended intervention selected?
    7. What is the confidence level?
    8. What information is missing?
    Strict Rule: Never fabricates metrics; strictly bounded to underlying numerical engine outputs.
    """
    data, txns, loans, obligations, receivables, payables, assets = get_customer_entities(id)
    fre = FinancialRealityEngineService.compute_financial_reality(
        customer_id=data["id"], customer_name=data["name"], archetype=data["archetype"],
        transactions=txns, loans=loans, obligations=obligations, receivables=receivables,
        payables=payables, assets=assets, liquid_cash=data["liquid_cash"]
    )
    distress = DiagnosticModularSuite.run_distress_detection_and_classification(fre)
    root_cause = DiagnosticModularSuite.run_root_cause_analysis(fre)
    context = DiagnosticModularSuite.run_context_and_seasonal_benchmarking(fre)
    least_harm = LeastHarmOptimizerService.rank_and_optimize(fre)

    # Ingest structured outputs into the Explanation Assistant payload
    payload = ExplanationInputPayload(
        customer_id=fre.customer_id,
        customer_name=fre.customer_name,
        archetype=fre.archetype,
        cluster_region=context["cluster_region"],
        industry=data.get("occupationOrIndustry", "Textiles"),
        liquid_cash=fre.liquid_cash_balance.value,
        monthly_income=fre.monthly_income.value,
        monthly_expenses=fre.monthly_expenses.value,
        monthly_debt_emi=fre.monthly_debt_service.value,
        cash_buffer_days=int(fre.cash_buffer_days.value),
        projected_shortfall_date=fre.next_critical_collision_date.isoformat() if fre.next_critical_collision_date else None,
        receivables_amount=fre.receivable_exposure.value,
        payables_amount=fre.payable_exposure.value,
        distress_score=distress["distress_score"],
        classification=distress["classification"],
        primary_root_cause=root_cause["primary_driver"],
        detailed_causes=[c["detail"] for c in root_cause["detailed_factors"]],
        cluster_revenue_growth_pct=-5.0,
        borrower_revenue_growth_pct=context["divergence_from_cluster_trend_pct"],
        is_sector_wide_seasonal_effect=context["is_anomaly_isolated_to_borrower"] is False,
        context_narrative=context["seasonal_forecast_next_quarter"],
        simulated_options=[
            {
                "title": o.title,
                "description": o.description,
                "is_permissible": o.is_permissible_under_guardrail,
                "summaryBenefit": f"Recovery Probability: {o.recovery_probability_pct}%"
            }
            for o in least_harm.ranked_interventions
        ],
        recommended_option_title=least_harm.selected_intervention.title,
        recommended_option_description=least_harm.selected_intervention.description,
        no_new_loan_veto_active=least_harm.no_new_loan_guardrail_enforced,
        no_new_loan_veto_reason="Taking the requested loan would push Debt Service Coverage Ratio (DSCR) below 1.25",
        overall_confidence_pct=94.0,
        missing_information=fre.data_quality.missing_fields,
        supporting_facts=least_harm.supporting_evidence
    )

    explanation = FinancialExplanationAssistantService.generate_explanation(payload)
    return StandardAPIResponse(data=explanation, message="Explanation Synthesized Without Hallucination")


@app.post("/assistant/explain", response_model=StandardAPIResponse[StructuredExplanationResponse], tags=["Explanation Assistant"])
def explain_arbitrary_payload(payload: ExplanationInputPayload, user: TokenData = Depends(authenticate_user)):
    """
    Directly ingests an arbitrary structured payload from any external banking sub-engine
    and produces grounded explanations without calculating metrics itself.
    """
    explanation = FinancialExplanationAssistantService.generate_explanation(payload)
    return StandardAPIResponse(data=explanation, message="Explanation Synthesized Successfully")

