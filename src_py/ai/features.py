"""
Feature Engineering Pipeline for FINRES ML.
Transforms raw credit data into ML-ready features.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


# Feature definitions for the distress prediction model
FEATURE_NAMES = [
    "declining_cash_pct",
    "neg_balance_freq",
    "cash_buffer_days",
    "revenue_decline_pct",
    "income_volatility",
    "fixed_cost_ratio",
    "debt_service_ratio",
    "late_payments",
    "collision_shortfall_scaled",
]

NUMERIC_FEATURES = [
    "age", "annual_income", "loan_amount", "interest_rate",
    "employment_years", "credit_history_years", "loan_to_income",
    "credit_score", "property_value", "loan_to_value",
]

CATEGORICAL_FEATURES = [
    "loan_purpose", "archetype", "home_ownership",
    "historical_default", "loan_grade", "gender", "region",
]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Apply feature engineering to raw unified data."""
    feat = pd.DataFrame()

    feat["debt_service_ratio"] = (df["loan_amount"] * df["interest_rate"] / 100) / df["annual_income"].clip(lower=1)
    feat["debt_service_ratio"] = feat["debt_service_ratio"].clip(0, 2)

    feat["loan_burden"] = df["loan_amount"] / df["annual_income"].clip(lower=1)
    feat["loan_burden"] = feat["loan_burden"].clip(0, 5)

    feat["income_per_year_exp"] = df["annual_income"] / (df["employment_years"].clip(lower=1) + 1)

    feat["collateral_coverage"] = df["property_value"] / df["loan_amount"].clip(lower=1)
    feat["collateral_coverage"] = feat["collateral_coverage"].clip(0, 10)

    feat["credit_utilization"] = 1 - (df["credit_score"].clip(300, 850) - 300) / 550

    grade_map = {"A": 0.05, "B": 0.15, "C": 0.30, "D": 0.50, "E": 0.70, "F": 0.85, "G": 0.95}
    feat["grade_risk"] = df["loan_grade"].map(grade_map).fillna(0.3)

    default_map = {"Y": 1, "N": 0, "Yes": 1, "No": 0}
    feat["historical_default_flag"] = df["historical_default"].map(default_map).fillna(0)

    feat["cash_buffer_days"] = np.where(
        feat["debt_service_ratio"] < 0.2, 45,
        np.where(feat["debt_service_ratio"] < 0.4, 25,
        np.where(feat["debt_service_ratio"] < 0.6, 12,
        np.where(feat["debt_service_ratio"] < 0.8, 5, 2)))
    )

    feat["declining_cash_pct"] = np.where(
        feat["debt_service_ratio"] > 0.6, 50 + np.random.normal(0, 5, len(df)),
        np.where(feat["debt_service_ratio"] > 0.4, 25 + np.random.normal(0, 5, len(df)),
        np.where(feat["debt_service_ratio"] > 0.2, 10 + np.random.normal(0, 3, len(df)),
        2 + np.random.normal(0, 1, len(df))))
    ).clip(0, 100)

    feat["neg_balance_freq"] = np.where(
        feat["cash_buffer_days"] < 5, 8,
        np.where(feat["cash_buffer_days"] < 15, 3,
        np.where(feat["cash_buffer_days"] < 25, 1, 0))
    )

    feat["revenue_decline_pct"] = feat["declining_cash_pct"] * 0.8 + np.random.normal(0, 3, len(df))
    feat["revenue_decline_pct"] = feat["revenue_decline_pct"].clip(0, 80)

    feat["income_volatility"] = feat["credit_utilization"] * 0.5 + feat["debt_service_ratio"] * 0.3
    feat["income_volatility"] = feat["income_volatility"].clip(0, 1)

    feat["fixed_cost_ratio"] = 0.3 + feat["debt_service_ratio"] * 0.4 + feat["grade_risk"] * 0.2
    feat["fixed_cost_ratio"] = feat["fixed_cost_ratio"].clip(0.1, 0.95)

    feat["late_payments"] = np.where(
        feat["debt_service_ratio"] > 0.6, 5,
        np.where(feat["debt_service_ratio"] > 0.4, 2,
        np.where(feat["debt_service_ratio"] > 0.3, 1, 0))
    )

    feat["collision_shortfall_scaled"] = (
        feat["debt_service_ratio"] * df["loan_amount"] * feat["grade_risk"] / 1000
    ).clip(0, 500000)

    feat["age"] = df["age"]
    feat["employment_years"] = df["employment_years"]
    feat["credit_history_years"] = df["credit_history_years"]

    return feat


def build_real_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build the 9-feature vector matching the distress engine's input format."""
    feat = engineer_features(df)

    for col in FEATURE_NAMES:
        if col not in feat.columns:
            feat[col] = 0

    return feat[FEATURE_NAMES]


def build_enriched_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build expanded feature set for advanced models (XGBoost, RandomForest)."""
    base = engineer_features(df)

    base["log_income"] = np.log1p(df["annual_income"])
    base["log_loan"] = np.log1p(df["loan_amount"])
    base["log_property"] = np.log1p(df["property_value"].clip(lower=1))

    base["income_x_employment"] = base["log_income"] * df["employment_years"]
    base["loan_x_rate"] = df["loan_amount"] * df["interest_rate"] / 100
    base["ltv_x_grade"] = df["loan_to_value"] * base["grade_risk"]
    base["score_x_income"] = df["credit_score"] / 850 * base["log_income"]

    base["is_msME"] = (df["archetype"].str.upper() == "MSME").astype(int)
    base["has_property"] = (df["property_value"] > 0).astype(int)
    base["high_grade_risk"] = (base["grade_risk"] > 0.5).astype(int)

    return base


def get_distress_features(customer_data: dict) -> np.ndarray:
    """Convert a single customer dict to the 9-feature vector for the distress model."""
    income = float(customer_data.get("annual_income", 500000))
    loan = float(customer_data.get("loan_amount", 200000))
    rate = float(customer_data.get("interest_rate", 12))
    emp_years = float(customer_data.get("employment_years", 5))
    credit_score = float(customer_data.get("credit_score", 650))
    property_val = float(customer_data.get("property_value", 0))

    dsr = (loan * rate / 100) / max(income, 1)
    grade_risk = 0.3

    if dsr > 0.6:
        declining_cash = 50
        neg_bal_freq = 8
        cash_buffer = 2
        revenue_decline = 40
        income_vol = 0.5
        fixed_cost = 0.75
        late_pmts = 5
        collision = loan * dsr * grade_risk / 1000
    elif dsr > 0.4:
        declining_cash = 25
        neg_bal_freq = 3
        cash_buffer = 12
        revenue_decline = 20
        income_vol = 0.3
        fixed_cost = 0.55
        late_pmts = 2
        collision = loan * dsr * grade_risk / 1000
    elif dsr > 0.2:
        declining_cash = 10
        neg_bal_freq = 1
        cash_buffer = 25
        revenue_decline = 8
        income_vol = 0.15
        fixed_cost = 0.42
        late_pmts = 1
        collision = loan * dsr * grade_risk / 1000
    else:
        declining_cash = 2
        neg_bal_freq = 0
        cash_buffer = 45
        revenue_decline = 0
        income_vol = 0.05
        fixed_cost = 0.35
        late_pmts = 0
        collision = 0

    return np.array([[
        declining_cash, neg_bal_freq, cash_buffer, revenue_decline,
        income_vol, fixed_cost, dsr, late_pmts, collision
    ]])
