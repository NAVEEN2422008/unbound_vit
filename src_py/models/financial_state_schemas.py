"""
Pydantic v2 schemas defining the complete FinancialState object for the Financial Reality Engine.
Encapsulates granular, multi-resolution breakdown of Income, Expenses, Debt, Cash, Receivables,
Payables, Cash Flow, Financial Health Metrics, and Data Quality.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from src_py.models.schemas import ProvenanceValue, ValueProvenance, DataQualityMetrics


class IncomeFinancialBlock(BaseModel):
    total_income: float
    average_daily_income: float
    average_weekly_income: float
    average_monthly_income: float
    income_volatility: float = Field(..., description="Coefficient of variation (std_dev / mean) of weekly/monthly income")
    income_growth_rate: float = Field(..., description="Month-over-month growth rate percentage")
    breakdown_by_category: Dict[str, float] = {}


class ExpenseFinancialBlock(BaseModel):
    total_expenses: float
    fixed_expenses: float
    variable_expenses: float
    essential_expenses: float
    discretionary_expenses: float
    expense_growth_rate: float = Field(..., description="Month-over-month expense growth rate percentage")
    breakdown_by_category: Dict[str, float] = {}


class DebtFinancialBlock(BaseModel):
    total_debt: float
    monthly_debt_service: float
    loan_count: int
    average_interest_rate: float
    remaining_tenure_months: int
    multi_lender_breakdown: List[Dict[str, Any]] = []


class CashFinancialBlock(BaseModel):
    current_cash: float
    cash_buffer: float
    cash_buffer_days: int
    minimum_cash_requirement: float


class ReceivablesFinancialBlock(BaseModel):
    total_receivables: float
    overdue_receivables: float
    near_term_receivables: float  # Due in next 30 days
    treds_eligible_amount: float = 0.0


class PayablesFinancialBlock(BaseModel):
    total_payables: float
    overdue_payables: float
    near_term_payables: float  # Due in next 30 days
    critical_supplier_amount: float = 0.0


class TimeResolutionCashflow(BaseModel):
    daily: List[Dict[str, Any]] = []    # [{date, inflow, outflow, net_flow, closing_balance}]
    weekly: List[Dict[str, Any]] = []   # [{week_str, inflow, outflow, net_flow}]
    monthly: List[Dict[str, Any]] = []  # [{month_str, inflow, outflow, net_flow}]


class CashFlowFinancialBlock(BaseModel):
    total_inflows: float
    total_outflows: float
    net_cash_flow: float = Field(..., description="total_inflows - total_outflows")
    operating_cash_inflow: float
    operating_cash_outflow: float
    debt_service: float
    free_cash_flow: float = Field(..., description="operating_cash_inflow - operating_cash_outflow - debt_service")
    time_series: TimeResolutionCashflow


class RatioMetricsBlock(BaseModel):
    debt_service_ratio: float = Field(..., description="monthly_debt_service / monthly_income")
    expense_ratio: float = Field(..., description="total_expenses / monthly_income")
    savings_rate: float = Field(..., description="(monthly_income - total_expenses - monthly_debt_service) / monthly_income")
    dscr: float = Field(..., description="Operating Cash / Debt Service")
    foir: float = Field(..., description="Debt Service / Gross Income")
    net_working_capital: float


class FinancialState(BaseModel):
    """
    Unified, complete, and continuously updated representation of customer financial condition.
    Exposes all component metrics at daily, weekly, and monthly resolutions.
    """
    customer_id: str
    customer_name: str
    customer_archetype: str
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    current_cash: float
    income: IncomeFinancialBlock
    expenses: ExpenseFinancialBlock
    debt: DebtFinancialBlock
    receivables: ReceivablesFinancialBlock
    payables: PayablesFinancialBlock
    cashflow: CashFlowFinancialBlock
    metrics: RatioMetricsBlock
    data_quality: DataQualityMetrics

    model_config = ConfigDict(from_attributes=True)
