"""
Data Ingestion and Normalization Service.
Implements robust parsing, validation, format standardization, duplicate detection,
data completeness scoring, and conversion to Financial Reality Engine-compatible entities.
"""
import io
import csv
import json
import re
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple

from src_py.models.ingestion_schemas import (
    StandardDirection, StandardCategory, IngestionDataStatus,
    NormalizedTransactionRecord, IngestionErrorRecord, DuplicateDetectionRecord,
    DataQualityReport, IngestionBatchOutput
)
from src_py.models.schemas import (
    NormalizedTransaction, DirectionEnum, TransactionCategory, ValueProvenance
)


SUPPORTED_CURRENCIES = {"INR", "RS", "RUPEES", "INR "}

REQUIRED_TRANSACTION_FIELDS = [
    "customer_id", "transaction_date", "amount", "direction", "category", "description"
]


class DataIngestionService:
    """
    Ingests and normalizes raw customer transaction feeds from CSV, JSON, or bank statements.
    Detects duplicates without data loss and flags quality metrics.
    """

    # Categorization keywords dictionary
    KEYWORD_CATEGORY_MAP = [
        (re.compile(r"salary|payroll|ctc|stipend", re.IGNORECASE), StandardCategory.SALARY),
        (re.compile(r"customer|invoice|client|sales|buyer|collection|revenue|trf from", re.IGNORECASE), StandardCategory.BUSINESS_REVENUE),
        (re.compile(r"swiggy|zomato|uber|ola|dunzo|zepto|blinkit|shadowfax|rapido", re.IGNORECASE), StandardCategory.GIG_INCOME),
        (re.compile(r"swiggy|zomato|restaurant|cafe|food|hotel|mcdonald|domino", re.IGNORECASE), StandardCategory.FOOD),
        (re.compile(r"rent|lease|landlord|tenancy", re.IGNORECASE), StandardCategory.RENT),
        (re.compile(r"electricity|bescom|tneb|water|bescom|billdesk|broadband|wifi|airtel|jio", re.IGNORECASE), StandardCategory.UTILITIES),
        (re.compile(r"petrol|diesel|fuel|iocl|hpcl|bpcl|gas", re.IGNORECASE), StandardCategory.FUEL),
        (re.compile(r"wages|worker|payroll|staff salary", re.IGNORECASE), StandardCategory.PAYROLL),
        (re.compile(r"supplier|vendor|raw material|yarn|fabric|spares|trf to", re.IGNORECASE), StandardCategory.SUPPLIER),
        (re.compile(r"gst|gstr|tax|tds|challan|advance tax|cbic", re.IGNORECASE), StandardCategory.TAX),
        (re.compile(r"emi|loan|nach|bajaj|hdfc bank loan|sbi loan|muthoot", re.IGNORECASE), StandardCategory.EMI),
        (re.compile(r"lic|insurance|hdfc ergo|policy|premium", re.IGNORECASE), StandardCategory.INSURANCE),
        (re.compile(r"upi|transfer|neft|rtgs|imps", re.IGNORECASE), StandardCategory.TRANSFER),
    ]

    @classmethod
    def parse_flexible_date(cls, date_str: Any) -> Optional[datetime]:
        """Parses dates across multiple standard Indian and ISO formats."""
        if isinstance(date_str, datetime):
            return date_str
        if isinstance(date_str, date):
            return datetime.combine(date_str, datetime.min.time())
        if not date_str or not isinstance(date_str, str):
            return None

        clean_str = date_str.strip()
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%d/%m/%Y",
            "%d-%m-%Y",
            "%d/%m/%y",
            "%d-%m-%y",
            "%d %b %Y",
            "%d %B %Y",
            "%Y/%m/%d"
        ]
        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt)
            except ValueError:
                continue
        return None

    @classmethod
    def normalize_direction(cls, dir_val: Any) -> Optional[StandardDirection]:
        """Standardizes transaction direction into CREDIT or DEBIT."""
        if not dir_val:
            return None
        val_str = str(dir_val).strip().upper()
        if val_str in ("CR", "CREDIT", "INFLOW", "DEPOSIT", "IN", "RECEIVED", "+"):
            return StandardDirection.CREDIT
        if val_str in ("DR", "DEBIT", "OUTFLOW", "WITHDRAWAL", "OUT", "SPENT", "PAID", "-"):
            return StandardDirection.DEBIT
        return None

    @classmethod
    def infer_category(cls, raw_cat: Optional[str], description: str, direction: StandardDirection) -> StandardCategory:
        """Categorizes raw transactions based on explicit inputs or text mining."""
        if raw_cat:
            cat_upper = raw_cat.strip().upper()
            try:
                return StandardCategory(cat_upper)
            except ValueError:
                pass

        # Text matching on description
        for pattern, category in cls.KEYWORD_CATEGORY_MAP:
            if pattern.search(description):
                return category

        # Default by direction
        if direction == StandardDirection.CREDIT:
            return StandardCategory.INCOME
        return StandardCategory.OTHER

    @classmethod
    def parse_csv_content(cls, csv_text: str) -> List[Dict[str, Any]]:
        """Parses CSV content with automatic header mapping."""
        rows: List[Dict[str, Any]] = []
        reader = csv.DictReader(io.StringIO(csv_text))
        for row in reader:
            # Normalize column keys to lowercase and stripped
            clean_row = {k.strip().lower() if k else "": (v.strip() if v else "") for k, v in row.items()}
            rows.append(clean_row)
        return rows

    @classmethod
    def ingest_transactions(
        cls,
        customer_id: str,
        records: List[Dict[str, Any]],
        batch_id: Optional[str] = None,
        source: str = "CSV_IMPORT",
        existing_history: Optional[List[NormalizedTransactionRecord]] = None
    ) -> IngestionBatchOutput:
        """
        Master ingestion pipeline:
        1. Validate required fields
        2. Standardize formats (date, amount, currency, direction, category)
        3. Detect duplicates against batch and historical records
        4. Calculate data completeness and freshness
        5. Quarantine invalid rows with full diagnostics
        """
        actual_batch_id = batch_id or f"BATCH_{customer_id}_{int(datetime.utcnow().timestamp())}"
        history = existing_history or []

        accepted: List[NormalizedTransactionRecord] = []
        errors: List[IngestionErrorRecord] = []
        duplicates: List[DuplicateDetectionRecord] = []

        seen_signatures: Dict[str, str] = {}
        # Pre-fill signature map from existing history
        for past_txn in history:
            sig = f"{past_txn.customer_id}_{past_txn.transaction_date.date()}_{past_txn.amount}_{past_txn.description.strip().lower()}"
            seen_signatures[sig] = past_txn.transaction_id

        available_fields_count = 0
        total_fields_count = 0

        latest_transaction_date: Optional[datetime] = None

        for idx, raw in enumerate(records):
            # Count required fields for completeness calculation
            for field in REQUIRED_TRANSACTION_FIELDS:
                total_fields_count += 1
                val = raw.get(field) or raw.get(field.replace("_", "")) or raw.get(field.split("_")[-1])
                if val is not None and str(val).strip() != "":
                    available_fields_count += 1

            # 1. Validation: customer_id
            row_cust_id = raw.get("customer_id") or raw.get("customer") or customer_id
            if not row_cust_id or not str(row_cust_id).strip():
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="MISSING_CUSTOMER_ID",
                    error_message="Missing required customer_id field.",
                    field="customer_id"
                ))
                continue

            # 2. Validation: Amount
            raw_amt = raw.get("amount") or raw.get("txn_amount") or raw.get("value")
            if raw_amt is None or str(raw_amt).strip() == "":
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="MISSING_AMOUNT",
                    error_message="Missing required transaction amount.",
                    field="amount"
                ))
                continue

            try:
                clean_amt = float(str(raw_amt).replace(",", "").replace("₹", "").replace("$", "").strip())
                if clean_amt <= 0:
                    errors.append(IngestionErrorRecord(
                        row_index=idx,
                        raw_record=raw,
                        error_type="NON_POSITIVE_AMOUNT",
                        error_message="Transaction amount must be strictly greater than zero.",
                        field="amount"
                    ))
                    continue
            except ValueError:
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="INVALID_AMOUNT_FORMAT",
                    error_message=f"Cannot parse amount string '{raw_amt}' into a float.",
                    field="amount"
                ))
                continue

            # 3. Validation: Date
            raw_date = raw.get("transaction_date") or raw.get("date") or raw.get("txn_date") or raw.get("timestamp")
            parsed_date = cls.parse_flexible_date(raw_date)
            if not parsed_date:
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="INVALID_DATE",
                    error_message=f"Invalid or unparseable transaction date: '{raw_date}'.",
                    field="transaction_date"
                ))
                continue

            if not latest_transaction_date or parsed_date > latest_transaction_date:
                latest_transaction_date = parsed_date

            # 4. Validation: Direction
            raw_dir = raw.get("direction") or raw.get("type") or raw.get("cr_dr")
            direction = cls.normalize_direction(raw_dir)
            if not direction:
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="INVALID_DIRECTION",
                    error_message=f"Unrecognized transaction direction '{raw_dir}'. Expected CREDIT or DEBIT.",
                    field="direction"
                ))
                continue

            # 5. Validation: Currency
            curr = (raw.get("currency") or "INR").strip().upper()
            if curr not in SUPPORTED_CURRENCIES:
                errors.append(IngestionErrorRecord(
                    row_index=idx,
                    raw_record=raw,
                    error_type="UNSUPPORTED_CURRENCY",
                    error_message=f"Currency '{curr}' is not supported. Supported: INR.",
                    field="currency"
                ))
                continue

            # Description & Merchant extraction
            description = (raw.get("description") or raw.get("narration") or raw.get("particulars") or "Unspecified transaction").strip()
            merchant = (raw.get("merchant_name") or raw.get("merchant") or raw.get("party") or None)
            source_ref = (raw.get("source_reference") or raw.get("reference") or raw.get("ref_no") or None)

            # Categorization
            category = cls.infer_category(raw.get("category"), description, direction)

            # 6. Duplicate Detection
            txn_id = (raw.get("transaction_id") or raw.get("id") or f"TXN_{row_cust_id}_{parsed_date.strftime('%Y%m%d%H%M%S')}_{idx}").strip()
            sig = f"{row_cust_id}_{parsed_date.date()}_{clean_amt}_{description.lower()}"

            data_status = IngestionDataStatus.ACTUAL
            if sig in seen_signatures:
                # Flag duplicate candidate without deleting
                data_status = IngestionDataStatus.DUPLICATE_REVIEW_REQUIRED
                duplicates.append(DuplicateDetectionRecord(
                    transaction_id=txn_id,
                    customer_id=row_cust_id,
                    duplicate_of_id=seen_signatures[sig],
                    transaction_date=parsed_date,
                    amount=clean_amt,
                    merchant_name=merchant,
                    description=description,
                    source_reference=source_ref,
                    confidence_score=0.95
                ))
            else:
                seen_signatures[sig] = txn_id

            accepted_rec = NormalizedTransactionRecord(
                transaction_id=txn_id,
                customer_id=row_cust_id,
                transaction_date=parsed_date,
                amount=clean_amt,
                currency="INR",
                direction=direction,
                category=category,
                subcategory=raw.get("subcategory"),
                merchant_name=merchant,
                description=description,
                source=source,
                source_reference=source_ref,
                data_status=data_status,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            accepted.append(accepted_rec)

        # Completeness Score calculation
        completeness_pct = round((available_fields_count / total_fields_count * 100.0), 2) if total_fields_count > 0 else 0.0

        # Freshness calculation
        freshness_days = 0
        if latest_transaction_date:
            freshness_days = max(0, (datetime.utcnow().date() - latest_transaction_date.date()).days)

        return IngestionBatchOutput(
            batch_id=actual_batch_id,
            customer_id=customer_id,
            records_processed=len(records),
            records_accepted=len(accepted),
            records_rejected=len(errors),
            duplicates_detected=len(duplicates),
            data_completeness_score=completeness_pct,
            data_freshness_days=freshness_days,
            validation_errors=errors,
            duplicate_candidates=duplicates,
            normalized_transactions=accepted
        )

    @classmethod
    def convert_to_fre_transactions(cls, normalized_txns: List[NormalizedTransactionRecord]) -> List[NormalizedTransaction]:
        """
        Bridges Ingestion Service outputs directly into the Financial Reality Engine (FRE).
        Ensures seamless downstream consumption.
        """
        category_map = {
            StandardCategory.SALARY: TransactionCategory.INCOME_SALARY,
            StandardCategory.BUSINESS_REVENUE: TransactionCategory.INCOME_BUSINESS,
            StandardCategory.GIG_INCOME: TransactionCategory.INCOME_GIG_PLATFORM,
            StandardCategory.INCOME: TransactionCategory.INCOME_OTHER,
            StandardCategory.FOOD: TransactionCategory.EXPENSE_ESSENTIAL_GROCERY,
            StandardCategory.RENT: TransactionCategory.EXPENSE_ESSENTIAL_RENT,
            StandardCategory.UTILITIES: TransactionCategory.EXPENSE_ESSENTIAL_UTILITY,
            StandardCategory.FUEL: TransactionCategory.EXPENSE_OPERATIONAL_FUEL,
            StandardCategory.PAYROLL: TransactionCategory.EXPENSE_OPERATIONAL_PAYROLL,
            StandardCategory.SUPPLIER: TransactionCategory.EXPENSE_OPERATIONAL_RAW_MATERIAL,
            StandardCategory.TAX: TransactionCategory.STATUTORY_TAX_GST,
            StandardCategory.EMI: TransactionCategory.DEBT_EMI_LOAN,
            StandardCategory.INSURANCE: TransactionCategory.EXPENSE_DISCRETIONARY,
            StandardCategory.TRANSFER: TransactionCategory.INCOME_OTHER,
            StandardCategory.LOAN: TransactionCategory.DEBT_EMI_LOAN,
            StandardCategory.INVESTMENT: TransactionCategory.EXPENSE_DISCRETIONARY,
            StandardCategory.OTHER: TransactionCategory.EXPENSE_DISCRETIONARY,
        }

        fre_txns: List[NormalizedTransaction] = []
        for n in normalized_txns:
            # Skip records flagged for quarantine or duplicate review if desired, or include them with status
            direction = DirectionEnum.INFLOW if n.direction == StandardDirection.CREDIT else DirectionEnum.OUTFLOW
            cat = category_map.get(n.category, TransactionCategory.EXPENSE_DISCRETIONARY)

            fre_txns.append(NormalizedTransaction(
                id=n.transaction_id,
                customer_id=n.customer_id,
                timestamp=n.transaction_date,
                amount=n.amount,
                direction=direction,
                category=cat,
                narration=n.description,
                channel=n.source,
                is_recurring=(n.category in (StandardCategory.SALARY, StandardCategory.RENT, StandardCategory.EMI)),
                provenance=ValueProvenance.ACTUAL if n.data_status == IngestionDataStatus.ACTUAL else ValueProvenance.ESTIMATED
            ))
        return fre_txns

    @classmethod
    def compute_data_quality_report(
        cls,
        customer_id: str,
        transactions: List[NormalizedTransactionRecord]
    ) -> DataQualityReport:
        """Computes comprehensive data quality and completeness score report."""
        if not transactions:
            return DataQualityReport(
                customer_id=customer_id,
                total_records_analyzed=0,
                available_required_fields=0,
                total_required_fields=0,
                data_completeness_score=0.0,
                data_freshness_days=999,
                missing_fields=["transactions"],
                reliability_verdict="LOW_REQUIRES_HUMAN_REVIEW"
            )

        total_fields = len(transactions) * 6
        available_fields = 0
        missing = set()

        for t in transactions:
            if t.customer_id: available_fields += 1
            else: missing.add("customer_id")
            if t.transaction_date: available_fields += 1
            else: missing.add("transaction_date")
            if t.amount > 0: available_fields += 1
            else: missing.add("amount")
            if t.direction: available_fields += 1
            else: missing.add("direction")
            if t.category: available_fields += 1
            else: missing.add("category")
            if t.description: available_fields += 1
            else: missing.add("description")

        completeness = round((available_fields / total_fields) * 100.0, 2)
        latest_date = max(t.transaction_date for t in transactions)
        freshness_days = max(0, (datetime.utcnow().date() - latest_date.date()).days)

        verdict = "HIGH"
        if completeness < 70.0 or freshness_days > 45:
            verdict = "LOW_REQUIRES_HUMAN_REVIEW"
        elif completeness < 85.0 or freshness_days > 20:
            verdict = "MODERATE"

        return DataQualityReport(
            customer_id=customer_id,
            as_of_date=datetime.utcnow(),
            total_records_analyzed=len(transactions),
            available_required_fields=available_fields,
            total_required_fields=total_fields,
            data_completeness_score=completeness,
            data_freshness_days=freshness_days,
            field_breakdown={
                "customer_id": 100.0,
                "amount": 100.0,
                "transaction_date": 100.0,
                "direction": 100.0,
                "category": 100.0,
                "description": 100.0
            },
            missing_fields=list(missing),
            reliability_verdict=verdict
        )
