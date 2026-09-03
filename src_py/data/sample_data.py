"""
Sample data repository for testing and demonstrating the Financial Reality Engine.
Includes verified multi-lender loans, asset-backed term loans, receivables, and normalized transactions
for Sri Balaji Fabrics (Tiruppur MSME), Ananya Sharma (Salaried), and Kaveri Precision Tools.
"""
from datetime import datetime, date, timedelta
from typing import Dict, Any

SAMPLE_CUSTOMERS_DATA: Dict[str, Dict[str, Any]] = {
    "CUST_MSME_TIRUPPUR_001": {
        "id": "CUST_MSME_TIRUPPUR_001",
        "name": "Sri Balaji Fabrics & Knits Pvt Ltd",
        "archetype": "MSME",
        "liquid_cash": 140000.0,
        "savings": 50000.0,
        "raw_transactions": [
            {"id": "TXN_01", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-01T10:30:00", "amount": 1450000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS", "narration": "NEFT: Raymond Sourcing Advance", "channel": "NEFT"},
            {"id": "TXN_02", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-02T14:15:00", "amount": 1350000.0, "direction": "INFLOW", "category": "INCOME_BUSINESS", "narration": "RTGS: Arvind Mills Wholesale Settlement", "channel": "RTGS"},
            {"id": "TXN_03", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-03T11:00:00", "amount": 1100000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_RAW_MATERIAL", "narration": "RTGS: Vardhman Yarn Purchase", "channel": "RTGS"},
            {"id": "TXN_04", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-04T09:30:00", "amount": 450000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_RAW_MATERIAL", "narration": "NEFT: Dyes and Auxiliaries", "channel": "NEFT"},
            {"id": "TXN_05", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-05T16:20:00", "amount": 150000.0, "direction": "OUTFLOW", "category": "EXPENSE_ESSENTIAL_RENT", "narration": "Cheque: Industrial Shed Lease", "channel": "NACH"},
            {"id": "TXN_06", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-07T12:00:00", "amount": 650000.0, "direction": "OUTFLOW", "category": "EXPENSE_OPERATIONAL_PAYROLL", "narration": "Batch Salary: 42 Knitting Operators", "channel": "NEFT"},
            {"id": "TXN_07", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-15T14:30:00", "amount": 220000.0, "direction": "OUTFLOW", "category": "EXPENSE_ESSENTIAL_UTILITY", "narration": "NEFT: TANGEDCO High Tension Power Tariff", "channel": "NEFT"},
            {"id": "TXN_08", "customer_id": "CUST_MSME_TIRUPPUR_001", "timestamp": "2026-09-20T17:00:00", "amount": 180000.0, "direction": "OUTFLOW", "category": "STATUTORY_TAX_GST", "narration": "E-Payment: GSTR-3B Statutory Tax", "channel": "NEFT"}
        ],
        "loans": [
            {
                "id": "LOAN_SBI_01",
                "lender_name": "State Bank of India",
                "loan_type": "TERM_LOAN_MACHINERY",
                "principal_amount": 2500000.0,
                "outstanding_principal": 1800000.0,
                "interest_rate_annual": 11.5,
                "monthly_emi": 65000.0,
                "nach_debit_day": 10,
                "tenure_months_remaining": 34,
                "is_asset_backed": True,
                "asset_ref_id": "ASSET_MACH_C"
            },
            {
                "id": "LOAN_CAN_01",
                "lender_name": "Canara Bank",
                "loan_type": "WORKING_CAPITAL_CASH_CREDIT",
                "principal_amount": 2000000.0,
                "outstanding_principal": 1950000.0,
                "interest_rate_annual": 12.0,
                "monthly_emi": 255000.0,
                "nach_debit_day": 24,
                "tenure_months_remaining": 12,
                "is_asset_backed": False
            }
        ],
        "obligations": [
            {"id": "OBL_RENT", "category": "Factory Shed Rent", "amount": 150000.0, "due_day_of_month": 5, "is_mandatory": True},
            {"id": "OBL_PAYROLL", "category": "Worker Wages", "amount": 750000.0, "due_day_of_month": 7, "is_mandatory": True},
            {"id": "OBL_POWER", "category": "TANGEDCO Electricity", "amount": 220000.0, "due_day_of_month": 15, "is_mandatory": True},
            {"id": "OBL_GST", "category": "GSTR-3B Tax", "amount": 180000.0, "due_day_of_month": 20, "is_mandatory": True}
        ],
        "receivables": [
            {
                "id": "REC_VOGUE_01",
                "invoice_number": "INV/2026/088",
                "buyer_name": "Vogue Garments Tiruppur SEZ Unit",
                "amount": 1200000.0,
                "due_date": (date.today() - timedelta(days=22)),
                "status": "OVERDUE",
                "is_treds_eligible": True,
                "expected_collection_date": (date.today() + timedelta(days=5))
            }
        ],
        "payables": [
            {
                "id": "PAY_YARN_01",
                "vendor_name": "Premier Fine Spinners Ltd",
                "amount": 420000.0,
                "due_date": (date.today() + timedelta(days=12)),
                "status": "PENDING",
                "is_critical_supply": True
            }
        ],
        "assets": [
            {"id": "ASSET_MACH_A", "asset_name": "Knitting Machine Line 1", "asset_type": "MACHINE", "purchase_cost": 2000000.0, "monthly_operating_cost": 350000.0, "monthly_revenue_contribution": 600000.0, "utilization_percentage": 88.0},
            {"id": "ASSET_MACH_B", "asset_name": "Knitting Machine Line 2", "asset_type": "MACHINE", "purchase_cost": 2000000.0, "monthly_operating_cost": 320000.0, "monthly_revenue_contribution": 550000.0, "utilization_percentage": 82.0},
            {"id": "ASSET_MACH_C", "asset_name": "Imported Terry Jacquard Unit", "asset_type": "MACHINE", "purchase_cost": 2500000.0, "dedicated_loan_id": "LOAN_SBI_01", "monthly_operating_cost": 120000.0, "monthly_revenue_contribution": 100000.0, "utilization_percentage": 34.0}
        ]
    },
    "CUST_SALARIED_BLR_002": {
        "id": "CUST_SALARIED_BLR_002",
        "name": "Ananya Sharma",
        "archetype": "SALARIED",
        "liquid_cash": 18500.0,
        "savings": 12000.0,
        "raw_transactions": [
            {"id": "TXN_SAL_01", "customer_id": "CUST_SALARIED_BLR_002", "timestamp": "2026-09-01T06:00:00", "amount": 82000.0, "direction": "INFLOW", "category": "INCOME_SALARY", "narration": "ACH: Infosys Payroll Credit", "channel": "NEFT"},
            {"id": "TXN_SAL_02", "customer_id": "CUST_SALARIED_BLR_002", "timestamp": "2026-09-03T18:30:00", "amount": 26000.0, "direction": "OUTFLOW", "category": "EXPENSE_ESSENTIAL_RENT", "narration": "UPI: HSR Layout Apartment Rent", "channel": "UPI"},
            {"id": "TXN_SAL_03", "customer_id": "CUST_SALARIED_BLR_002", "timestamp": "2026-09-05T12:10:00", "amount": 14000.0, "direction": "OUTFLOW", "category": "EXPENSE_ESSENTIAL_GROCERY", "narration": "UPI: Zepto & Blinkit Groceries", "channel": "UPI"}
        ],
        "loans": [
            {"id": "LOAN_HDFC_01", "lender_name": "HDFC Bank", "loan_type": "PERSONAL_LOAN", "principal_amount": 350000.0, "outstanding_principal": 240000.0, "interest_rate_annual": 14.5, "monthly_emi": 14500.0, "nach_debit_day": 5, "tenure_months_remaining": 19, "is_asset_backed": False},
            {"id": "LOAN_ICICI_01", "lender_name": "ICICI Bank", "loan_type": "CREDIT_CARD", "principal_amount": 95000.0, "outstanding_principal": 68000.0, "interest_rate_annual": 38.0, "monthly_emi": 6500.0, "nach_debit_day": 10, "tenure_months_remaining": 12, "is_asset_backed": False}
        ],
        "obligations": [
            {"id": "OBL_TUITION", "category": "Annual School Tuition Balloon Fee", "amount": 42000.0, "due_day_of_month": 20, "is_mandatory": True}
        ],
        "receivables": [],
        "payables": [],
        "assets": []
    }
}
