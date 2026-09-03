"""
Pydantic v2 schemas for the Seasonal Forecasting Engine.
Encapsulates monthly forward forecasts with:
- expected_revenue, expected_expense, expected_cashflow
- seasonal_index
- confidence intervals (lower_bound, upper_bound)
- confidence score
- fallback status (CUSTOMER_HISTORY vs PEER_INDUSTRY_FALLBACK)
- responsible probabilistic communication phrasing ("Historical pattern indicates higher expected revenue").
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ForecastDataSource(str, Enum):
    CUSTOMER_HISTORY = "CUSTOMER_HISTORY"
    PEER_INDUSTRY_FALLBACK = "PEER_INDUSTRY_FALLBACK"


class MonthlyForecastRecord(BaseModel):
    month_index: int  # 1 to 12
    month_label: str  # "Jan", "Feb", etc.
    year: int
    expected_revenue: float
    expected_expense: float
    expected_cashflow: float
    seasonal_index: float = Field(..., description="Multiplicative seasonal index (1.0 = average month)")
    
    # Confidence Interval (Prudential range, e.g. 80% CI)
    revenue_lower_bound: float
    revenue_upper_bound: float
    cashflow_lower_bound: float
    cashflow_upper_bound: float
    
    confidence: float = Field(ge=0.0, le=1.0)
    interpretive_note: str


class SeasonalForecastReport(BaseModel):
    """
    Standard output of Seasonal Forecasting Engine.
    Exposes 12-month forward projection, methodology used, historical coverage,
    and responsible probabilistic advisory notes.
    """
    customer_id: str
    customer_name: str
    industry: str
    region: str
    data_source: ForecastDataSource
    months_of_history_analyzed: int
    forecasting_method: str = "Decomposed Multiplicative Seasonal Index + Holt-Winters Exponential Smoothing"
    overall_confidence: float = Field(ge=0.0, le=1.0)
    peak_season_months: List[str]
    trough_season_months: List[str]
    monthly_forecasts: List[MonthlyForecastRecord]
    
    probabilistic_disclaimer: str = (
        "Historical pattern indicates expected revenue distributions with confidence intervals; "
        "projections do not guarantee definitive future realization."
    )
    executive_narrative: str

    model_config = ConfigDict(from_attributes=True)
