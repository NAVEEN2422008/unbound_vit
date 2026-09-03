"""
Pydantic v2 schemas for Early Distress Detection Engine.
Enforces dual-component prediction (Explainable Rules Engine + Calibrated Logistic ML Model),
0-100 distress score, 4 risk tiers (LOW, MODERATE, HIGH, CRITICAL),
three prediction horizons (7_DAY, 30_DAY, 90_DAY), and top risk factor provenance.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DistressRiskLevel(str, Enum):
    LOW = "LOW"            # 0.0 - 29.9
    MODERATE = "MODERATE"  # 30.0 - 54.9
    HIGH = "HIGH"          # 55.0 - 79.9
    CRITICAL = "CRITICAL"  # 80.0 - 100.0


class PredictionHorizon(str, Enum):
    HORIZON_7_DAY = "7_DAY"
    HORIZON_30_DAY = "30_DAY"
    HORIZON_90_DAY = "90_DAY"


class RiskFactorContribution(BaseModel):
    feature_name: str
    category: str  # CASH_FLOW, INCOME, EXPENSES, DEBT, PAYMENTS, BUSINESS, OBLIGATIONS
    observed_value: float
    contribution_weight: float
    impact_direction: str  # INCREASES_DISTRESS, DECREASES_DISTRESS
    explanation: str


class DistressPredictionRequest(BaseModel):
    customer_id: str
    # Cash-flow signals
    declining_cash_rate_pct: float = 0.0
    negative_balance_frequency: int = 0
    cash_buffer_days: int = 30
    # Income signals
    revenue_decline_pct: float = 0.0
    income_volatility: float = 0.10
    income_shock_pct: float = 0.0
    # Expenses signals
    unexpected_expense_increase_pct: float = 0.0
    fixed_cost_ratio: float = 0.40
    # Debt signals
    debt_service_ratio: float = 0.20
    loan_count: int = 1
    emi_growth_rate_pct: float = 0.0
    # Payment signals
    late_payments_last_90d: int = 0
    missed_payments_last_180d: int = 0
    # Business signals
    declining_orders_pct: float = 0.0
    receivable_overdue_ratio: float = 0.0
    asset_underperformance_pct: float = 0.0
    # Obligations signals
    upcoming_collision_shortfall: float = 0.0
    horizon: PredictionHorizon = PredictionHorizon.HORIZON_30_DAY


class DistressPredictionResult(BaseModel):
    """
    Standard output of Early Distress Detection Engine.
    Exposes calibrated distress score (0-100), risk tier, multi-horizon trajectories,
    explainable rule score vs ML model score, and top contributing risk factors.
    """
    customer_id: str
    distress_score: float = Field(ge=0.0, le=100.0, description="Calibrated score 0-100")
    risk_level: DistressRiskLevel
    prediction_horizon: PredictionHorizon
    confidence_score: float = Field(ge=0.0, le=1.0)
    top_risk_factors: List[RiskFactorContribution]
    
    # Model Calibration & Component Transparency
    rules_engine_score: float
    ml_model_score: float
    model_type: str = "LogisticRegression+EnsembleRules (Calibrated Prototype)"
    training_data_label: str = "CALIBRATED_PROTOTYPE_DATA"
    is_early_preventable: bool
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)
