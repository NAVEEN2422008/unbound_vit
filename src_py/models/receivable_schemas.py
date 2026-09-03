"""
Pydantic v2 schemas for Trade Receivable Intelligence Engine.
Determines whether outstanding trade receivables can resolve liquidity distress
prior to considering additional borrowing.
Calculates:
- days_outstanding
- expected_payment_date
- collection_probability
- expected_7_day_cash
- expected_14_day_cash
- expected_30_day_cash
Classifies receivables into:
- HIGH_CONFIDENCE
- MODERATE_CONFIDENCE
- UNCERTAIN
- OVERDUE
Produces actionable recommendations for Credit Affordability Engine
(e.g., "Investigate receivable acceleration before taking additional debt").
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field, ConfigDict


class ReceivableConfidenceClassification(str, Enum):
    HIGH_CONFIDENCE = "HIGH_CONFIDENCE"        # Prompt buyer payment history (<5 days delay), collection prob >= 85%
    MODERATE_CONFIDENCE = "MODERATE_CONFIDENCE"  # Standard buyer payment history (5–15 days delay), collection prob 65–84%
    UNCERTAIN = "UNCERTAIN"                    # Volatile payment history or buyer dispute, collection prob < 65%
    OVERDUE = "OVERDUE"                        # Past agreed due date without settlement


class InvoiceAnalysisItem(BaseModel):
    invoice_number: str
    buyer_name: str
    invoice_amount: float
    invoice_date: date
    due_date: date
    days_outstanding: int
    expected_payment_date: date
    collection_probability: float = Field(ge=0.0, le=1.0)
    classification: ReceivableConfidenceClassification
    expected_cash_within_horizon: float
    is_accelerable_via_treds: bool = False
    notes: str


class ReceivablesAnalysisReport(BaseModel):
    """
    Standard output of Trade Receivable Intelligence Engine.
    Feeds directly into the Credit Affordability and Least-Harm Engines.
    """
    business_id: str
    as_of_date: date
    total_receivable_book_value: float
    total_invoices_analyzed: int
    
    # Expected Cash Horizon Aggregates (Probability-weighted)
    expected_7_day_cash: float
    expected_14_day_cash: float
    expected_30_day_cash: float
    
    # Breakdown by confidence classification
    high_confidence_amount: float
    moderate_confidence_amount: float
    uncertain_amount: float
    overdue_amount: float
    
    invoices: List[InvoiceAnalysisItem] = []
    
    # Decision Twin & Credit Affordability Feed
    can_receivables_cover_shortfall: bool
    projected_shortfall_amount: float
    receivable_coverage_ratio: float
    credit_affordability_recommendation: str
    
    model_config = ConfigDict(from_attributes=True)
