"""
Comprehensive unit & integration tests for Data Ingestion and Normalization Service.
Tests:
1. Valid CSV ingestion and standard normalization
2. Invalid date format quarantine
3. Missing customer_id quarantine
4. Missing amount quarantine
5. Duplicate record detection (marked DUPLICATE_REVIEW_REQUIRED without deletion)
6. Mixed currencies (rejecting unsupported currencies)
7. Empty dataset handling
8. Partially corrupted file / malformed amounts
9. Data completeness calculation
10. Conversion from normalized records to Financial Reality Engine (FRE) objects
11. FastAPI REST API endpoints (/api/v1/data/transactions/import, loans, assets, quality)
"""
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

from src_py.api.main import app
from src_py.services.data_ingestion import DataIngestionService
from src_py.models.ingestion_schemas import (
    StandardDirection, StandardCategory, IngestionDataStatus
)
from src_py.models.schemas import ValueProvenance, DirectionEnum

client = TestClient(app)


def test_valid_csv_ingestion():
    csv_data = """transaction_id,customer_id,transaction_date,amount,direction,category,description
TXN001,CUST_TEST_001,2026-09-01,150000,CREDIT,BUSINESS_REVENUE,Buyer Invoice Payment
TXN002,CUST_TEST_001,2026-09-02,45000,DEBIT,RENT,Factory Shed Lease Rent
TXN003,CUST_TEST_001,2026-09-03,28000,DEBIT,UTILITIES,TNEB Electricity Bill
"""
    records = DataIngestionService.parse_csv_content(csv_data)
    batch = DataIngestionService.ingest_transactions("CUST_TEST_001", records)

    assert batch.records_processed == 3
    assert batch.records_accepted == 3
    assert batch.records_rejected == 0
    assert batch.duplicates_detected == 0
    assert batch.data_completeness_score == 100.0
    assert batch.normalized_transactions[0].direction == StandardDirection.CREDIT
    assert batch.normalized_transactions[0].category == StandardCategory.BUSINESS_REVENUE
    assert batch.normalized_transactions[1].direction == StandardDirection.DEBIT
    assert batch.normalized_transactions[1].category == StandardCategory.RENT


def test_invalid_date_quarantined():
    raw_records = [
        {
            "customer_id": "CUST_TEST_002",
            "transaction_date": "INVALID_DATE_XYZ",
            "amount": "12000",
            "direction": "DEBIT",
            "category": "FUEL",
            "description": "Petrol pump fuel"
        },
        {
            "customer_id": "CUST_TEST_002",
            "transaction_date": "04/09/2026",
            "amount": "15000",
            "direction": "CREDIT",
            "category": "SALARY",
            "description": "Monthly Salary Credit"
        }
    ]
    batch = DataIngestionService.ingest_transactions("CUST_TEST_002", raw_records)
    assert batch.records_processed == 2
    assert batch.records_accepted == 1
    assert batch.records_rejected == 1
    assert batch.validation_errors[0].error_type == "INVALID_DATE"


def test_missing_customer_id_quarantined():
    raw_records = [
        {
            "customer_id": "",
            "transaction_date": "2026-09-01",
            "amount": "5000",
            "direction": "DEBIT",
            "category": "FOOD",
            "description": "Office pantry"
        }
    ]
    batch = DataIngestionService.ingest_transactions("", raw_records)
    assert batch.records_accepted == 0
    assert batch.records_rejected == 1
    assert batch.validation_errors[0].error_type == "MISSING_CUSTOMER_ID"


def test_missing_and_negative_amount_quarantined():
    raw_records = [
        {
            "customer_id": "CUST_TEST_003",
            "transaction_date": "2026-09-01",
            "amount": "",
            "direction": "DEBIT",
            "description": "Missing amount row"
        },
        {
            "customer_id": "CUST_TEST_003",
            "transaction_date": "2026-09-01",
            "amount": "-500",
            "direction": "DEBIT",
            "description": "Negative amount row"
        },
        {
            "customer_id": "CUST_TEST_003",
            "transaction_date": "2026-09-01",
            "amount": "ABC_NOT_A_NUMBER",
            "direction": "DEBIT",
            "description": "Corrupted amount string"
        }
    ]
    batch = DataIngestionService.ingest_transactions("CUST_TEST_003", raw_records)
    assert batch.records_accepted == 0
    assert batch.records_rejected == 3
    error_types = [e.error_type for e in batch.validation_errors]
    assert "MISSING_AMOUNT" in error_types
    assert "NON_POSITIVE_AMOUNT" in error_types
    assert "INVALID_AMOUNT_FORMAT" in error_types


def test_duplicate_records_detected_without_data_loss():
    raw_records = [
        {
            "transaction_id": "TXN_ORIG_01",
            "customer_id": "CUST_TEST_DUP",
            "transaction_date": "2026-09-01",
            "amount": "25000",
            "direction": "DEBIT",
            "description": "Supplier Yarn Payment"
        },
        {
            "transaction_id": "TXN_DUP_02",
            "customer_id": "CUST_TEST_DUP",
            "transaction_date": "2026-09-01",
            "amount": "25000",
            "direction": "DEBIT",
            "description": "Supplier Yarn Payment"
        }
    ]
    batch = DataIngestionService.ingest_transactions("CUST_TEST_DUP", raw_records)
    assert batch.records_processed == 2
    assert batch.records_accepted == 2
    assert batch.duplicates_detected == 1
    # Check that second transaction is flagged DUPLICATE_REVIEW_REQUIRED
    assert batch.normalized_transactions[0].data_status == IngestionDataStatus.ACTUAL
    assert batch.normalized_transactions[1].data_status == IngestionDataStatus.DUPLICATE_REVIEW_REQUIRED
    assert batch.duplicate_candidates[0].duplicate_of_id == "TXN_ORIG_01"


def test_mixed_currencies_unsupported_quarantined():
    raw_records = [
        {
            "customer_id": "CUST_TEST_CURR",
            "transaction_date": "2026-09-01",
            "amount": "1000",
            "currency": "INR",
            "direction": "DEBIT",
            "description": "Valid INR debit"
        },
        {
            "customer_id": "CUST_TEST_CURR",
            "transaction_date": "2026-09-01",
            "amount": "500",
            "currency": "USD",
            "direction": "DEBIT",
            "description": "Unsupported USD payment"
        }
    ]
    batch = DataIngestionService.ingest_transactions("CUST_TEST_CURR", raw_records)
    assert batch.records_accepted == 1
    assert batch.records_rejected == 1
    assert batch.validation_errors[0].error_type == "UNSUPPORTED_CURRENCY"


def test_empty_dataset_handling():
    batch = DataIngestionService.ingest_transactions("CUST_EMPTY", [])
    assert batch.records_processed == 0
    assert batch.records_accepted == 0
    assert batch.records_rejected == 0
    assert batch.data_completeness_score == 0.0

    report = DataIngestionService.compute_data_quality_report("CUST_EMPTY", [])
    assert report.reliability_verdict == "LOW_REQUIRES_HUMAN_REVIEW"
    assert "transactions" in report.missing_fields


def test_fre_bridge_conversion():
    csv_data = """transaction_id,customer_id,transaction_date,amount,direction,category,description
TXN10,CUST_FRE_01,2026-09-01,200000,CREDIT,BUSINESS_REVENUE,Garment Export Payment
TXN11,CUST_FRE_01,2026-09-02,50000,DEBIT,EMI,Machinery Term Loan EMI
"""
    records = DataIngestionService.parse_csv_content(csv_data)
    batch = DataIngestionService.ingest_transactions("CUST_FRE_01", records)
    fre_txns = DataIngestionService.convert_to_fre_transactions(batch.normalized_transactions)

    assert len(fre_txns) == 2
    assert fre_txns[0].direction == DirectionEnum.INFLOW
    assert fre_txns[0].provenance == ValueProvenance.ACTUAL
    assert fre_txns[1].direction == DirectionEnum.OUTFLOW
    assert fre_txns[1].is_recurring is True


def test_api_v1_endpoints():
    # 1. Import transactions API
    res = client.post("/api/v1/data/transactions/import", json={
        "customer_id": "CUST_API_TEST",
        "records": [
            {
                "transaction_date": "2026-09-01",
                "amount": 75000,
                "direction": "CREDIT",
                "category": "BUSINESS_REVENUE",
                "description": "Client payment"
            },
            {
                "transaction_date": "2026-09-02",
                "amount": 25000,
                "direction": "DEBIT",
                "category": "RENT",
                "description": "Office rent"
            }
        ]
    }, headers={"X-API-KEY": "FINRES_BANKER_KEY_2026"})
    assert res.status_code == 200
    body = res.json()["data"]
    assert body["records_accepted"] == 2

    # 2. Quality report API
    q_res = client.get("/api/v1/data/quality/CUST_API_TEST", headers={"X-API-KEY": "FINRES_BANKER_KEY_2026"})
    assert q_res.status_code == 200
    q_data = q_res.json()["data"]
    assert q_data["total_records_analyzed"] == 2
    assert q_data["data_completeness_score"] > 0

    # 3. Loans import API
    l_res = client.post("/api/v1/data/loans/import", json={
        "customer_id": "CUST_API_TEST",
        "loans": [{"id": "L1", "principal_amount": 500000, "monthly_emi": 15000}]
    }, headers={"X-API-KEY": "FINRES_BANKER_KEY_2026"})
    assert l_res.status_code == 200
    assert l_res.json()["data"]["loans_accepted"] == 1

    # 4. Assets import API
    a_res = client.post("/api/v1/data/assets/import", json={
        "customer_id": "CUST_API_TEST",
        "assets": [{"id": "A1", "asset_name": "Loom 01", "purchase_cost": 1200000}]
    }, headers={"X-API-KEY": "FINRES_BANKER_KEY_2026"})
    assert a_res.status_code == 200
    assert a_res.json()["data"]["assets_accepted"] == 1
