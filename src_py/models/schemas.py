"""
Pydantic v2 schemas for Financial Reality Engine.
Defines input payloads, normalized transactions, cashflow timelines,
value provenance (ACTUAL, PREDICTED, ESTIMATED), and final Financial Reality objects.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class ValueProvenance(str, Enum):
    ACTUAL = "ACTUAL"                  # Real verified bank/AA transaction or GST return
    USER_ENTERED = "USER_ENTERED"      # Declared by customer/business owner
    PREDICTED = "PREDICTED"            # Machine learning or recurring rule prediction
    ESTIMATED = "ESTIMATED"            # Benchmark/cluster heuristic when data is missing


class CustomerCategoryEnum(str, Enum):
    INDIVIDUAL = "INDIVIDUAL"
    GIG_OR_INFORMAL_WORKER = "GIG_OR_INFORMAL_WORKER"
    MSME_BUSINESS = "MSME_BUSINESS"


class UserRoleEnum(str, Enum):
    CUSTOMER = "CUSTOMER"
    BANKER = "BANKER"
    ADMIN = "ADMIN"


class DirectionEnum(str, Enum):
    INFLOW = "INFLOW"
    OUTFLOW = "OUTFLOW"


class TransactionCategory(str, Enum):
    INCOME_SALARY = "INCOME_SALARY"
    INCOME_BUSINESS = "INCOME_BUSINESS"
    INCOME_GIG_PLATFORM = "INCOME_GIG_PLATFORM"
    INCOME_RECEIVABLE = "INCOME_RECEIVABLE"
    INCOME_OTHER = "INCOME_OTHER"
    
    EXPENSE_ESSENTIAL_RENT = "EXPENSE_ESSENTIAL_RENT"
    EXPENSE_ESSENTIAL_GROCERY = "EXPENSE_ESSENTIAL_GROCERY"
    EXPENSE_ESSENTIAL_UTILITY = "EXPENSE_ESSENTIAL_UTILITY"
    EXPENSE_OPERATIONAL_RAW_MATERIAL = "EXPENSE_OPERATIONAL_RAW_MATERIAL"
    EXPENSE_OPERATIONAL_PAYROLL = "EXPENSE_OPERATIONAL_PAYROLL"
    EXPENSE_OPERATIONAL_FUEL = "EXPENSE_OPERATIONAL_FUEL"
    EXPENSE_DISCRETIONARY = "EXPENSE_DISCRETIONARY"
    
    DEBT_EMI_LOAN = "DEBT_EMI_LOAN"
    DEBT_CREDIT_CARD = "DEBT_CREDIT_CARD"
    STATUTORY_TAX_GST = "STATUTORY_TAX_GST"
    STATUTORY_TDS_EPF = "STATUTORY_TDS_EPF"


class ProvenanceValue(BaseModel):
    """Encapsulates any monetary or numeric value along with its provenance and confidence."""
    value: float
    provenance: ValueProvenance
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source: str = "Bank Account Aggregator"


class NormalizedTransaction(BaseModel):
    id: str
    customer_id: str
    timestamp: datetime
    amount: float
    direction: DirectionEnum
    category: TransactionCategory
    narration: str
    channel: str
    is_recurring: bool = False
    provenance: ValueProvenance = ValueProvenance.ACTUAL


class LoanObligation(BaseModel):
    id: str
    lender_name: str
    loan_type: str
    principal_amount: float
    outstanding_principal: float
    interest_rate_annual: float
    monthly_emi: float
    nach_debit_day: int
    tenure_months_remaining: int
    is_asset_backed: bool = False
    asset_ref_id: Optional[str] = None


class FixedObligationItem(BaseModel):
    id: str
    category: str
    amount: float
    due_day_of_month: int
    is_mandatory: bool = True


class ReceivableItem(BaseModel):
    id: str
    invoice_number: str
    buyer_name: str
    amount: float
    due_date: date
    status: str = "CURRENT"
    is_treds_eligible: bool = False
    expected_collection_date: Optional[date] = None


class PayableItem(BaseModel):
    id: str
    vendor_name: str
    amount: float
    due_date: date
    status: str = "PENDING"
    is_critical_supply: bool = True


class AssetFinancingItem(BaseModel):
    id: str
    asset_name: str
    asset_type: str
    purchase_cost: float
    dedicated_loan_id: Optional[str] = None
    monthly_operating_cost: float = 0.0
    monthly_revenue_contribution: float = 0.0
    utilization_percentage: float = 100.0


class DataQualityMetrics(BaseModel):
    completeness_percentage: float = Field(ge=0.0, le=100.0)
    has_bank_feed: bool = True
    has_gstn_feed: bool = False
    has_multi_lender_loans: bool = True
    has_receivables_data: bool = True
    missing_fields: List[str] = []
    reliability_level: str = "HIGH"  # HIGH, MODERATE, LOW (requires human review)


class DailyCashflowEntry(BaseModel):
    date: date
    opening_balance: float
    actual_inflow: float = 0.0
    actual_outflow: float = 0.0
    projected_inflow: float = 0.0
    projected_outflow: float = 0.0
    net_flow: float
    closing_balance: float
    events: List[str] = []
    is_negative: bool = False


class CashflowSummary(BaseModel):
    customer_id: str
    start_date: date
    end_date: date
    daily_timeline: List[DailyCashflowEntry]
    weekly_net_flows: Dict[str, float]
    monthly_inflow: float
    monthly_outflow: float
    projected_shortfall_date: Optional[date] = None
    projected_shortfall_amount: float = 0.0


class FinancialRealityObject(BaseModel):
    """
    The master unified customer financial reality schema.
    Can be consumed directly by Decision Twin, Early Distress Detection, and Least-Harm Optimizer.
    """
    customer_id: str
    customer_name: str
    archetype: str
    as_of_date: datetime = Field(default_factory=datetime.utcnow)

    # 1. Income & Cash Flow
    monthly_income: ProvenanceValue
    monthly_expenses: ProvenanceValue
    net_income: ProvenanceValue
    free_cash_flow: ProvenanceValue

    # 2. Debt & Obligation Metrics
    total_outstanding_debt: ProvenanceValue
    monthly_debt_service: ProvenanceValue
    debt_service_ratio: ProvenanceValue  # DSR = Debt Service / Income
    expense_ratio: ProvenanceValue       # Total Expenses / Income
    savings_rate: ProvenanceValue        # (Income - Expenses - Debt) / Income

    # 3. Liquidity & Buffers
    liquid_cash_balance: ProvenanceValue
    savings_balance: ProvenanceValue
    cash_buffer_days: ProvenanceValue    # Liquid Cash / Daily Essential Burn

    # 4. Working Capital Exposures (MSMEs & Traders)
    receivable_exposure: ProvenanceValue
    payable_exposure: ProvenanceValue
    net_working_capital: ProvenanceValue

    # 5. Asset Level Economics
    total_financed_assets: int
    asset_operating_burn: ProvenanceValue

    # 6. Expected Inflows/Outflows (Next 30 Days)
    upcoming_30d_inflow: float
    upcoming_30d_outflow: float
    next_critical_collision_date: Optional[date] = None

    # 7. Data Quality & Epistemic Uncertainty
    data_quality: DataQualityMetrics

    # 8. Human Explainable Narrative
    explanation_summary: str
    key_vulnerabilities: List[str]

    model_config = ConfigDict(from_attributes=True)


class RecalculateRequest(BaseModel):
    customer_id: str
    simulated_income_delta_pct: Optional[float] = None
    simulated_expense_delta_pct: Optional[float] = None
    include_projected_loans: bool = False
