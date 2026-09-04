"""
Real-World Data Loader for FINRES ML Pipeline.
Loads and preprocesses 3 public credit risk datasets into a unified schema.
"""
import os
import pandas as pd
import numpy as np
from typing import Tuple, Optional


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_credit_risk() -> pd.DataFrame:
    """Kaggle Credit Risk Dataset - 32,581 loan records with default labels."""
    path = os.path.join(DATA_DIR, "credit_risk.csv")
    df = pd.read_csv(path)

    df = df.rename(columns={
        "person_age": "age",
        "person_income": "annual_income",
        "person_home_ownership": "home_ownership",
        "person_emp_length": "employment_years",
        "loan_intent": "loan_purpose",
        "loan_grade": "loan_grade",
        "loan_amnt": "loan_amount",
        "loan_int_rate": "interest_rate",
        "loan_status": "default",
        "loan_percent_income": "loan_to_income",
        "cb_person_default_on_file": "historical_default",
        "cb_person_cred_hist_length": "credit_history_years",
    })

    df["source"] = "credit_risk"
    df["archetype"] = df["loan_purpose"].apply(_map_archetype_from_purpose)
    return df


def load_loan_default() -> pd.DataFrame:
    """Kaggle Loan Default Dataset - 255,347 records with 18 features."""
    path = os.path.join(DATA_DIR, "loan_default.csv")
    df = pd.read_csv(path)

    df = df.rename(columns={
        "Loan_amount": "loan_amount",
        "Rate_of_interest": "interest_rate",
        "Term": "loan_term",
        "credit_scoring": "credit_score",
        "Age": "age",
        "LTV": "loan_to_value",
        "Region": "region",
        "Gender": "gender",
        "Status": "default",
        "loan_limit": "has_loan_limit",
        "Gender": "gender",
        "approv_in_adv": "advance_approved",
        "loan_purpose": "loan_purpose",
        "Credit_Worthiness": "credit_worthiness",
        "open_credit": "open_credit",
        "business_or_commercial": "business_type",
        "Neg_ammortization": "negative_amortization",
        "interest_only": "interest_only_payment",
        "lump_sum_payment": "lump_sum_payment",
        "revenue": "revenue",
        "property_value": "property_value",
        "construction_type": "construction_type",
        "occupancy_type": "occupancy_type",
        "Secured_by": "secured_by",
        "total_units": "total_units",
        "submission_of_application": "application_submission",
        "year_of_birth": "birth_year",
    })

    if "age" not in df.columns and "birth_year" in df.columns:
        df["age"] = 2026 - df["birth_year"]

    df["source"] = "loan_default"
    df["archetype"] = df.get("business_type", pd.Series(["MSME"] * len(df))).apply(
        lambda x: "MSME" if str(x).lower().startswith("yes") or str(x).lower() == "business" else "SALARIED"
    )
    return df


def load_german_credit() -> pd.DataFrame:
    """UCI German Credit Dataset - 1,000 records, classic benchmark."""
    path = os.path.join(DATA_DIR, "german_credit.csv")
    df = pd.read_csv(path)

    checking_map = {"A11": 0, "A12": 1, "A13": 2, "A14": 3}
    savings_map = {"A61": 0, "A62": 1, "A63": 2, "A64": 3, "A65": 4}
    employment_map = {"A71": 0, "A72": 1, "A73": 2, "A74": 3, "A75": 4}
    purpose_map = {"A40": "education", "A41": "goods", "A42": "car", "A43": "furniture",
                   "A44": "radio_tv", "A45": "appliances", "A46": "repairs", "A47": "education",
                   "A48": "retraining", "A49": "business", "A410": "other"}
    job_map = {"A171": 0, "A172": 1, "A173": 2, "A174": 3}
    housing_map = {"A151": 0, "A152": 1, "A153": 2}

    df["checking_account_status"] = df["checking_account"].map(checking_map).fillna(0)
    df["savings_account_status"] = df["savings"].map(savings_map).fillna(0)
    df["employment_status"] = df["employment"].map(employment_map).fillna(2)
    df["loan_purpose"] = df["purpose"].map(purpose_map).fillna("other")
    df["job_skill_level"] = df["job"].map(job_map).fillna(1)
    df["housing_status"] = df["housing"].map(housing_map).fillna(1)

    df["annual_income"] = df["credit_amount"] * 2
    df["loan_to_income"] = df["credit_amount"] / df["annual_income"].clip(lower=1)
    df["default"] = df["target"].apply(lambda x: 1 if x == 2 else 0)
    df["age"] = df["age"]
    df["interest_rate"] = 10.0
    df["loan_amount"] = df["credit_amount"]
    df["employment_years"] = df["employment_status"] * 3
    df["credit_history_years"] = df["existing_credits"] * 3
    df["loan_grade"] = "C"
    df["historical_default"] = "N"
    df["source"] = "german_credit"
    df["archetype"] = "MSME"

    return df


def _map_archetype_from_purpose(purpose: str) -> str:
    purpose = str(purpose).lower()
    if purpose in ["venture", "business", "medical"]:
        return "MSME"
    return "SALARIED"


def load_all_datasets() -> pd.DataFrame:
    """Load and combine all 3 real-world datasets into unified schema."""
    dfs = []

    try:
        df1 = load_credit_risk()
        dfs.append(df1)
        print(f"  Credit Risk: {len(df1)} records")
    except Exception as e:
        print(f"  Credit Risk: FAILED - {e}")

    try:
        df2 = load_loan_default()
        dfs.append(df2)
        print(f"  Loan Default: {len(df2)} records")
    except Exception as e:
        print(f"  Loan Default: FAILED - {e}")

    try:
        df3 = load_german_credit()
        dfs.append(df3)
        print(f"  German Credit: {len(df3)} records")
    except Exception as e:
        print(f"  German Credit: FAILED - {e}")

    if not dfs:
        raise RuntimeError("No datasets could be loaded!")

    combined = pd.concat(dfs, ignore_index=True, sort=False)

    unified = _unify_schema(combined)
    print(f"\n  Total combined: {len(unified)} records, {len(unified.columns)} features")
    return unified


def _safe_numeric(df: pd.DataFrame, col: str, default, min_val=None, max_val=None) -> pd.Series:
    """Safely extract a numeric column, handling both existing columns and scalar defaults."""
    if col in df.columns:
        s = pd.to_numeric(df[col], errors="coerce").fillna(default)
    else:
        s = pd.Series([default] * len(df), index=df.index, dtype=float)
    if min_val is not None:
        s = s.clip(lower=min_val)
    if max_val is not None:
        s = s.clip(upper=max_val)
    return s


def _safe_string(df: pd.DataFrame, col: str, default: str) -> pd.Series:
    """Safely extract a string column."""
    if col in df.columns:
        return df[col].fillna(default).astype(str)
    return pd.Series([default] * len(df), index=df.index, dtype=str)


def _unify_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Map all datasets to a common feature schema for FINRES."""
    unified = pd.DataFrame()

    unified["age"] = _safe_numeric(df, "age", 35, 18, 80)
    unified["annual_income"] = _safe_numeric(df, "annual_income", 500000, 50000, 50000000)
    unified["loan_amount"] = _safe_numeric(df, "loan_amount", 200000, 10000, 50000000)
    unified["interest_rate"] = _safe_numeric(df, "interest_rate", 12.0, 1.0, 36.0)
    unified["employment_years"] = _safe_numeric(df, "employment_years", 5, 0, 40)
    unified["credit_history_years"] = _safe_numeric(df, "credit_history_years", 5, 0, 30)
    unified["loan_to_income"] = _safe_numeric(df, "loan_to_income", 0.3, 0.01, 2.0)

    unified["loan_purpose"] = _safe_string(df, "loan_purpose", "general")
    unified["archetype"] = _safe_string(df, "archetype", "SALARIED")
    unified["source"] = _safe_string(df, "source", "unknown")

    unified["default"] = _safe_numeric(df, "default", 0, 0, 1).astype(int)

    unified["home_ownership"] = _safe_string(df, "home_ownership", "RENT")
    unified["historical_default"] = _safe_string(df, "historical_default", "N")
    unified["loan_grade"] = _safe_string(df, "loan_grade", "C")

    unified["credit_score"] = _safe_numeric(df, "credit_score", 650, 300, 850)
    unified["property_value"] = _safe_numeric(df, "property_value", 0, 0, 50000000)
    unified["loan_to_value"] = _safe_numeric(df, "loan_to_value", 0.7, 0.01, 2.0)

    unified["gender"] = _safe_string(df, "gender", "Male")
    unified["region"] = _safe_string(df, "region", "Unknown")

    return unified


def get_feature_target_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Split into features (X) and target (y) for distress prediction."""
    feature_cols = [
        "age", "annual_income", "loan_amount", "interest_rate",
        "employment_years", "credit_history_years", "loan_to_income",
        "credit_score", "property_value", "loan_to_value",
    ]
    available = [c for c in feature_cols if c in df.columns]
    X = df[available].copy()
    y = df["default"].copy()
    return X, y


if __name__ == "__main__":
    print("Loading real-world datasets...")
    df = load_all_datasets()
    print(f"\nDataset shape: {df.shape}")
    print(f"Default rate: {df['default'].mean():.3f}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nArchetype distribution:")
    print(df["archetype"].value_counts())
    print(f"\nSource distribution:")
    print(df["source"].value_counts())
