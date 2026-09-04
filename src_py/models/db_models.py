"""
PostgreSQL Database Schemas using SQLAlchemy for Financial Reality Engine.
Stores raw normalized transactions, multi-lender loans, obligations, receivables, payables, and asset financing.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Date,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from src_py.db.engine import Base


class CustomerDB(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    archetype = Column(String(64), nullable=False)  # MSME, SALARIED, GIG_WORKER, etc.
    pan_masked = Column(String(16), nullable=False)
    cluster_region = Column(String(128), nullable=False)
    occupation_or_industry = Column(String(128), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    transactions = relationship("TransactionDB", back_populates="customer", cascade="all, delete-orphan")
    loans = relationship("LoanDB", back_populates="customer", cascade="all, delete-orphan")
    obligations = relationship("FixedObligationDB", back_populates="customer", cascade="all, delete-orphan")
    receivables = relationship("ReceivableDB", back_populates="customer", cascade="all, delete-orphan")
    payables = relationship("PayableDB", back_populates="customer", cascade="all, delete-orphan")
    assets = relationship("AssetFinancingDB", back_populates="customer", cascade="all, delete-orphan")
    financial_realities = relationship("FinancialRealityDB", back_populates="customer", cascade="all, delete-orphan")


class TransactionDB(Base):
    __tablename__ = "bank_transactions"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    amount = Column(Float, nullable=False)
    direction = Column(String(16), nullable=False)  # INFLOW, OUTFLOW
    category = Column(String(64), nullable=False)   # INCOME_BUSINESS, EXPENSE_PAYROLL, etc.
    narration = Column(Text, nullable=False)
    channel = Column(String(32), nullable=False)     # UPI, NACH, NEFT, RTGS, CARD, CASH
    is_recurring = Column(Boolean, default=False)
    
    customer = relationship("CustomerDB", back_populates="transactions")


class LoanDB(Base):
    __tablename__ = "loans"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    lender_name = Column(String(128), nullable=False)
    loan_type = Column(String(64), nullable=False)  # TERM_LOAN, WORKING_CAPITAL, PERSONAL_LOAN
    principal_amount = Column(Float, nullable=False)
    outstanding_principal = Column(Float, nullable=False)
    interest_rate_annual = Column(Float, nullable=False)
    monthly_emi = Column(Float, nullable=False)
    nach_debit_day = Column(Integer, nullable=False)
    tenure_months_remaining = Column(Integer, nullable=False)
    is_asset_backed = Column(Boolean, default=False)
    asset_ref_id = Column(String(64), nullable=True)

    customer = relationship("CustomerDB", back_populates="loans")


class FixedObligationDB(Base):
    __tablename__ = "fixed_obligations"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    category = Column(String(64), nullable=False)  # RENT, PAYROLL, ELECTRICITY, GST_TAX, SCHOOL_FEE
    amount = Column(Float, nullable=False)
    due_day_of_month = Column(Integer, nullable=False)
    is_mandatory = Column(Boolean, default=True)

    customer = relationship("CustomerDB", back_populates="obligations")


class ReceivableDB(Base):
    __tablename__ = "receivables"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    invoice_number = Column(String(64), nullable=False)
    buyer_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(32), default="CURRENT")  # CURRENT, OVERDUE, PAID
    is_treds_eligible = Column(Boolean, default=False)
    expected_collection_date = Column(Date, nullable=True)

    customer = relationship("CustomerDB", back_populates="receivables")


class PayableDB(Base):
    __tablename__ = "payables"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(32), default="PENDING")  # PENDING, PAID, OVERDUE
    is_critical_supply = Column(Boolean, default=True)

    customer = relationship("CustomerDB", back_populates="payables")


class AssetFinancingDB(Base):
    __tablename__ = "asset_financings"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    asset_name = Column(String(255), nullable=False)
    asset_type = Column(String(64), nullable=False)  # MACHINE, VEHICLE, EQUIPMENT
    purchase_cost = Column(Float, nullable=False)
    dedicated_loan_id = Column(String(64), nullable=True)
    monthly_operating_cost = Column(Float, default=0.0)
    monthly_revenue_contribution = Column(Float, default=0.0)
    utilization_percentage = Column(Float, default=100.0)

    customer = relationship("CustomerDB", back_populates="assets")


class FinancialRealityDB(Base):
    __tablename__ = "financial_realities"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Financial Aggregates
    monthly_income_actual = Column(Float, nullable=False)
    monthly_expenses_actual = Column(Float, nullable=False)
    monthly_debt_service = Column(Float, nullable=False)
    liquid_cash_balance = Column(Float, nullable=False)
    savings_balance = Column(Float, nullable=False)
    free_cash_flow = Column(Float, nullable=False)
    
    # Ratios
    debt_service_ratio = Column(Float, nullable=False)
    expense_ratio = Column(Float, nullable=False)
    savings_rate = Column(Float, nullable=False)
    cash_buffer_days = Column(Integer, nullable=False)
    receivable_exposure = Column(Float, nullable=False)
    payable_exposure = Column(Float, nullable=False)
    
    # Data Quality
    data_completeness_percentage = Column(Float, nullable=False)
    is_missing_external_debt = Column(Boolean, default=False)
    is_missing_receivables = Column(Boolean, default=False)
    
    customer = relationship("CustomerDB", back_populates="financial_realities")


class AuditEntryDB(Base):
    """
    Immutable System-Wide Audit Log.
    Historical audit records must never be overwritten or deleted.
    """
    __tablename__ = "audit_log_entries"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    module_name = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    model_version = Column(String(32), default="v2.1-prod", nullable=False)
    rule_version = Column(String(32), default="RBI-IRACP-2026-R04", nullable=False)
    input_reference = Column(Text, nullable=False)
    output_summary = Column(Text, nullable=False)
    confidence_score = Column(Float, nullable=False)
    recommendation = Column(String(255), nullable=False)
    human_decision = Column(String(64), nullable=True)  # APPROVED, REJECTED, MODIFIED, REQUESTED_MORE_DATA
    final_action = Column(String(255), nullable=True)
    cryptographic_hash = Column(String(128), nullable=False)


class OutcomeRecordDB(Base):
    """
    Longitudinal Outcome Monitoring.
    Tracks whether interventions actually work over 30/60/90/180-day horizons.
    """
    __tablename__ = "outcome_monitoring_records"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    audit_ref_id = Column(String(64), ForeignKey("audit_log_entries.id"), nullable=True)
    intervention_type = Column(String(128), nullable=False)
    start_date = Column(Date, nullable=False)
    evaluation_date = Column(Date, nullable=False)
    baseline_distress_score = Column(Float, nullable=False)
    current_distress_score = Column(Float, nullable=False)
    default_averted = Column(Boolean, default=True)
    interest_cost_saved = Column(Float, default=0.0)
    current_dpd = Column(Integer, default=0)
    customer_resilience_trend = Column(String(32), default="IMPROVING")


class IngestionBatchDB(Base):
    """
    Ingestion Batches table tracking file uploads, batch IDs, accepted/rejected counts.
    """
    __tablename__ = "ingestion_batches"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    source = Column(String(64), nullable=False)  # CSV_IMPORT, BANK_AA_API, ACCOUNTING_SYSTEM
    file_name = Column(String(255), nullable=True)
    records_processed = Column(Integer, default=0)
    records_accepted = Column(Integer, default=0)
    records_rejected = Column(Integer, default=0)
    duplicates_detected = Column(Integer, default=0)
    data_completeness_score = Column(Float, default=0.0)
    data_freshness_days = Column(Integer, default=0)
    status = Column(String(32), default="COMPLETED")  # PROCESSING, COMPLETED, FAILED
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class IngestionErrorDB(Base):
    """
    Ingestion Errors table recording quarantined or rejected rows with root-cause details.
    """
    __tablename__ = "ingestion_errors"

    id = Column(String(64), primary_key=True, index=True)
    batch_id = Column(String(64), ForeignKey("ingestion_batches.id"), nullable=False, index=True)
    customer_id = Column(String(64), nullable=False, index=True)
    row_index = Column(Integer, nullable=False)
    raw_record = Column(Text, nullable=False)
    error_type = Column(String(64), nullable=False)  # MISSING_AMOUNT, INVALID_DATE, UNSUPPORTED_CURRENCY, etc.
    error_message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class DataQualityReportDB(Base):
    """
    Data Quality Reports table tracking completeness, freshness, and epistemic reliability.
    """
    __tablename__ = "data_quality_reports"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False, index=True)
    batch_id = Column(String(64), ForeignKey("ingestion_batches.id"), nullable=True)
    as_of_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    total_records_analyzed = Column(Integer, default=0)
    data_completeness_score = Column(Float, nullable=False)
    data_freshness_days = Column(Integer, default=0)
    reliability_verdict = Column(String(32), default="HIGH")  # HIGH, MODERATE, LOW_REQUIRES_HUMAN_REVIEW
    details_json = Column(Text, nullable=True)


