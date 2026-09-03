"""
Pydantic v2 schemas for Data Ingestion and Normalization Service.
Defines schemas for raw input payloads, normalized standard transactions,
ingestion batches, duplicate candidates, data quality reports, and validation errors.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class StandardDirection(str, Enum):
    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class StandardCategory(str, Enum):
    INCOME = "INCOME"
    SALARY = "SALARY"
    BUSINESS_REVENUE = "BUSINESS_REVENUE"
    GIG_INCOME = "GIG_INCOME"
    FOOD = "FOOD"
    RENT = "RENT"
    UTILITIES = "UTILITIES"
    FUEL = "FUEL"
    PAYROLL = "PAYROLL"
    SUPPLIER = "SUPPLIER"
    TAX = "TAX"
    EMI = "EMI"
    INSURANCE = "INSURANCE"
    TRANSFER = "TRANSFER"
    LOAN = "LOAN"
    INVESTMENT = "INVESTMENT"
    OTHER = "OTHER"


class IngestionDataStatus(str, Enum):
    ACTUAL = "ACTUAL"
    USER_ENTERED = "USER_ENTERED"
    PREDICTED = "PREDICTED"
    ESTIMATED = "ESTIMATED"
    DUPLICATE_REVIEW_REQUIRED = "DUPLICATE_REVIEW_REQUIRED"
    REJECTED = "REJECTED"


class NormalizedTransactionRecord(BaseModel):
    """Normalized standard transaction record consumable by every other module."""
    transaction_id: str
    customer_id: str
    transaction_date: datetime
    amount: float = Field(..., gt=0.0)
    currency: str = "INR"
    direction: StandardDirection
    category: StandardCategory
    subcategory: Optional[str] = None
    merchant_name: Optional[str] = None
    description: str
    source: str = "CSV_IMPORT"
    source_reference: Optional[str] = None
    data_status: IngestionDataStatus = IngestionDataStatus.ACTUAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


class IngestionErrorRecord(BaseModel):
    row_index: int
    raw_record: Dict[str, Any]
    error_type: str
    error_message: str
    field: Optional[str] = None


class DuplicateDetectionRecord(BaseModel):
    transaction_id: str
    customer_id: str
    duplicate_of_id: Optional[str] = None
    transaction_date: datetime
    amount: float
    merchant_name: Optional[str] = None
    description: str
    source_reference: Optional[str] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    resolution_status: str = "DUPLICATE_REVIEW_REQUIRED"


class DataQualityReport(BaseModel):
    customer_id: str
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    total_records_analyzed: int
    available_required_fields: int
    total_required_fields: int
    data_completeness_score: float = Field(ge=0.0, le=100.0)
    data_freshness_days: int
    field_breakdown: Dict[str, float] = {}
    missing_fields: List[str] = []
    reliability_verdict: str = "HIGH"  # HIGH, MODERATE, LOW_REQUIRES_HUMAN_REVIEW


class IngestionBatchOutput(BaseModel):
    batch_id: str
    customer_id: str
    records_processed: int
    records_accepted: int
    records_rejected: int
    duplicates_detected: int
    data_completeness_score: float
    data_freshness_days: int
    validation_errors: List[IngestionErrorRecord] = []
    duplicate_candidates: List[DuplicateDetectionRecord] = []
    normalized_transactions: List[NormalizedTransactionRecord] = []
