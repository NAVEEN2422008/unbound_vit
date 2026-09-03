"""
Pydantic v2 schemas for Cash-Flow Timeline & Forward Forecast Engine.
Defines daily cashflow entries with opening, inflows (actual/expected), outflows (actual/expected),
closing balances, minimum required cash, surplus/shortfall, markers for obligations and receivables,
and 30/60/90-day multi-horizon forecast structures.
"""
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict

from src_py.models.schemas import ValueProvenance


class DailyTimelineRecord(BaseModel):
    """
    Granular daily timeline record capturing cash movements and pre-default collision signals.
    """
    date: date
    opening_balance: float
    actual_inflow: float = 0.0
    expected_inflow: float = 0.0
    actual_outflow: float = 0.0
    expected_outflow: float = 0.0
    closing_balance: float
    minimum_required_cash: float
    surplus: float = 0.0
    shortfall: float = 0.0
    data_status: ValueProvenance = ValueProvenance.ACTUAL
    obligation_markers: List[Dict[str, Any]] = []
    receivable_markers: List[Dict[str, Any]] = []
    is_liquidity_deficit: bool = False

    model_config = ConfigDict(from_attributes=True)


class WeeklySummaryRecord(BaseModel):
    week_number: int
    week_start_date: date
    week_end_date: date
    total_inflows: float
    total_outflows: float
    net_cash_flow: float
    ending_cash_balance: float
    has_deficit: bool = False


class CashflowForecastHorizon(BaseModel):
    """Forecast breakdown for a specific horizon (30-day, 60-day, 90-day)."""
    horizon_days: int
    start_date: date
    end_date: date
    starting_cash: float
    projected_closing_cash: float
    total_projected_inflows: float
    total_projected_outflows: float
    net_projected_cash_flow: float
    is_hidden_shortage_detected: bool
    earliest_shortfall_date: Optional[date] = None
    peak_cash_deficit: float = 0.0
    daily_timeline: List[DailyTimelineRecord]
    weekly_timeline: List[WeeklySummaryRecord]


class CashflowForecastReport(BaseModel):
    """Multi-horizon cash-flow forecast container (30, 60, 90 days)."""
    customer_id: str
    customer_name: str
    archetype: str
    as_of_date: date
    current_cash: float
    minimum_required_cash: float
    forecast_30d: CashflowForecastHorizon
    forecast_60d: CashflowForecastHorizon
    forecast_90d: CashflowForecastHorizon
    underlying_assumptions: Dict[str, Any]
    hidden_shortage_narrative: Optional[str] = None
