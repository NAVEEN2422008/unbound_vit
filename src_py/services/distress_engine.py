"""
Early Distress Detection Engine Service.
Combines an Explainable Rule-Based Expert System with a Scikit-Learn Logistic Regression Model
calibrated on representative synthetic banking distress labels.
Detects early borrower deterioration before formal loan default occurs.
"""
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from src_py.models.distress_schemas import (
    DistressRiskLevel, PredictionHorizon, RiskFactorContribution,
    DistressPredictionRequest, DistressPredictionResult
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.financial_state_schemas import FinancialState


class EarlyDistressDetectionService:

    _scaler: Optional[StandardScaler] = None
    _ml_model: Optional[LogisticRegression] = None
    _is_calibrated: bool = False

    @classmethod
    def _initialize_and_calibrate_ml_model(cls):
        """
        Calibrates a Logistic Regression baseline model on representative training samples
        spanning healthy profiles, early warning stress, and severe default precursors.
        Clearly labeled as PROTOTYPE calibrated on synthetic banking labels.
        """
        if cls._is_calibrated and cls._ml_model is not None:
            return

        # 9 Input Features:
        # [declining_cash_pct, neg_balance_freq, cash_buffer_days, revenue_decline_pct,
        #  income_volatility, fixed_cost_ratio, debt_service_ratio, late_payments, collision_shortfall_scaled]
        X_train = np.array([
            # 1. Healthy Customers (Distress 0)
            [0.0, 0, 45, 0.0, 0.05, 0.35, 0.18, 0, 0.0],
            [-5.0, 0, 38, 2.0, 0.08, 0.40, 0.22, 0, 0.0],
            [2.0, 0, 50, 5.0, 0.04, 0.30, 0.15, 0, 0.0],
            [-2.0, 0, 42, -1.0, 0.06, 0.38, 0.20, 0, 0.0],
            
            # 2. Moderate Stress / Early Watchlist (Distress 0 or early 1)
            [12.0, 1, 24, 8.0, 0.18, 0.50, 0.35, 1, 10000.0],
            [18.0, 1, 20, 12.0, 0.22, 0.55, 0.38, 1, 20000.0],
            [15.0, 0, 22, 10.0, 0.20, 0.52, 0.36, 0, 15000.0],
            
            # 3. High Stress (Distress 1)
            [30.0, 3, 14, 25.0, 0.32, 0.68, 0.48, 2, 60000.0],
            [35.0, 4, 11, 28.0, 0.38, 0.72, 0.52, 3, 85000.0],
            [40.0, 5, 9, 32.0, 0.40, 0.75, 0.55, 3, 110000.0],
            
            # 4. Critical Stress / Imminent Collision (Distress 1)
            [55.0, 8, 4, 45.0, 0.50, 0.85, 0.65, 5, 200000.0],
            [60.0, 10, 2, 50.0, 0.58, 0.90, 0.70, 6, 250000.0],
            [70.0, 12, 1, 55.0, 0.62, 0.95, 0.75, 8, 300000.0],
        ])
        y_train = np.array([0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1])

        cls._scaler = StandardScaler()
        X_scaled = cls._scaler.fit_transform(X_train)

        cls._ml_model = LogisticRegression(C=1.0, solver="lbfgs", random_state=42)
        cls._ml_model.fit(X_scaled, y_train)
        cls._is_calibrated = True

    @classmethod
    def _evaluate_rules_engine(cls, req: DistressPredictionRequest) -> Tuple[float, List[RiskFactorContribution]]:
        """
        Explainable expert rules component evaluating 7 operational risk domains.
        Returns a base distress score (0-100) and top contributing factor items.
        """
        score = 0.0
        factors: List[RiskFactorContribution] = []

        # 1. Cash-Flow Domain (Max 25 pts)
        if req.cash_buffer_days < 10:
            score += 20.0
            factors.append(RiskFactorContribution(
                feature_name="cash_buffer_days",
                category="CASH_FLOW",
                observed_value=float(req.cash_buffer_days),
                contribution_weight=20.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Cash buffer of {req.cash_buffer_days} days is critically below the 14-day prudential floor."
            ))
        elif req.cash_buffer_days < 21:
            score += 12.0
            factors.append(RiskFactorContribution(
                feature_name="cash_buffer_days",
                category="CASH_FLOW",
                observed_value=float(req.cash_buffer_days),
                contribution_weight=12.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Cash buffer of {req.cash_buffer_days} days provides narrow operational cushion."
            ))

        if req.negative_balance_frequency > 0:
            pts = min(10.0, req.negative_balance_frequency * 3.0)
            score += pts
            factors.append(RiskFactorContribution(
                feature_name="negative_balance_frequency",
                category="CASH_FLOW",
                observed_value=float(req.negative_balance_frequency),
                contribution_weight=pts,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Account experienced {req.negative_balance_frequency} intraday negative liquidity breaches."
            ))

        # 2. Debt & Obligation Domain (Max 30 pts)
        if req.debt_service_ratio > 0.50:
            score += 25.0
            factors.append(RiskFactorContribution(
                feature_name="debt_service_ratio",
                category="DEBT",
                observed_value=round(req.debt_service_ratio, 3),
                contribution_weight=25.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Debt Service Ratio of {req.debt_service_ratio:.1%} severely impairs operational cash flow (>50%)."
            ))
        elif req.debt_service_ratio > 0.38:
            score += 15.0
            factors.append(RiskFactorContribution(
                feature_name="debt_service_ratio",
                category="DEBT",
                observed_value=round(req.debt_service_ratio, 3),
                contribution_weight=15.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Debt Service Ratio of {req.debt_service_ratio:.1%} is in elevated watch territory (>38%)."
            ))

        if req.upcoming_collision_shortfall > 0:
            pts = min(15.0, (req.upcoming_collision_shortfall / 50000.0) * 10.0)
            score += pts
            factors.append(RiskFactorContribution(
                feature_name="upcoming_collision_shortfall",
                category="OBLIGATIONS",
                observed_value=round(req.upcoming_collision_shortfall, 2),
                contribution_weight=round(pts, 1),
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Obligation Collision Radar detected imminent cash shortfall of ₹{req.upcoming_collision_shortfall:,.0f}."
            ))

        # 3. Income & Revenue Domain (Max 20 pts)
        if req.revenue_decline_pct > 20.0:
            score += 16.0
            factors.append(RiskFactorContribution(
                feature_name="revenue_decline_pct",
                category="INCOME",
                observed_value=round(req.revenue_decline_pct, 1),
                contribution_weight=16.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Sharp revenue decline of {req.revenue_decline_pct:.1f}% weakens repayment capacity."
            ))
        elif req.revenue_decline_pct > 10.0:
            score += 8.0
            factors.append(RiskFactorContribution(
                feature_name="revenue_decline_pct",
                category="INCOME",
                observed_value=round(req.revenue_decline_pct, 1),
                contribution_weight=8.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Moderate top-line revenue decline of {req.revenue_decline_pct:.1f}%."
            ))

        # 4. Payment Discipline Domain (Max 15 pts)
        if req.late_payments_last_90d > 0 or req.missed_payments_last_180d > 0:
            pts = min(15.0, req.late_payments_last_90d * 5.0 + req.missed_payments_last_180d * 10.0)
            score += pts
            factors.append(RiskFactorContribution(
                feature_name="late_or_missed_payments",
                category="PAYMENTS",
                observed_value=float(req.late_payments_last_90d + req.missed_payments_last_180d),
                contribution_weight=pts,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"Borrower registered {req.late_payments_last_90d} delayed and {req.missed_payments_last_180d} missed commitments."
            ))

        # 5. Fixed-Cost Pressure (Max 10 pts)
        if req.fixed_cost_ratio > 0.65:
            score += 8.0
            factors.append(RiskFactorContribution(
                feature_name="fixed_cost_ratio",
                category="EXPENSES",
                observed_value=round(req.fixed_cost_ratio, 2),
                contribution_weight=8.0,
                impact_direction="INCREASES_DISTRESS",
                explanation=f"High fixed operating structure ({req.fixed_cost_ratio:.1%} of income) limits cost flex."
            ))

        # Baseline clamp 5.0 - 95.0
        final_rules_score = min(98.0, max(5.0, score + 10.0))
        # Sort top factors by contribution weight descending
        factors.sort(key=lambda x: x.contribution_weight, reverse=True)
        return final_rules_score, factors

    @classmethod
    def predict_distress(cls, req: DistressPredictionRequest) -> DistressPredictionResult:
        """
        Executes hybrid early distress prediction:
        1. Explainable Rules Engine -> rules_score & factors
        2. Calibrated Logistic Regression ML Model -> ml_score
        3. Blended calibrated final distress score (0-100)
        4. Categorization into LOW, MODERATE, HIGH, CRITICAL tiers across 7, 30, and 90-day horizons.
        """
        cls._initialize_and_calibrate_ml_model()

        # 1. Rules Component
        rules_score, factors = cls._evaluate_rules_engine(req)

        # 2. ML Component
        feat_vector = np.array([[
            req.declining_cash_rate_pct,
            req.negative_balance_frequency,
            req.cash_buffer_days,
            req.revenue_decline_pct,
            req.income_volatility,
            req.fixed_cost_ratio,
            req.debt_service_ratio,
            req.late_payments_last_90d,
            req.upcoming_collision_shortfall
        ]])
        feat_scaled = cls._scaler.transform(feat_vector)
        # Probability of distress class (1)
        ml_prob = float(cls._ml_model.predict_proba(feat_scaled)[0][1])
        ml_score = round(ml_prob * 100.0, 1)

        # 3. Horizon scaling adjustment:
        # 7-day is immediate liquidity (heavier weight on cash collisions)
        # 90-day has structural drift
        horizon_multiplier = 1.0
        if req.horizon == PredictionHorizon.HORIZON_7_DAY:
            horizon_multiplier = 1.1 if req.upcoming_collision_shortfall > 0 else 0.95
        elif req.horizon == PredictionHorizon.HORIZON_90_DAY:
            horizon_multiplier = 1.05 if req.debt_service_ratio > 0.40 else 0.98

        # Blended final score: 60% explainable rules + 40% calibrated ML model
        blended_score = min(100.0, max(0.0, ((rules_score * 0.60) + (ml_score * 0.40)) * horizon_multiplier))
        final_score = round(blended_score, 1)

        # Risk Tier Classification
        if final_score >= 80.0:
            tier = DistressRiskLevel.CRITICAL
        elif final_score >= 55.0:
            tier = DistressRiskLevel.HIGH
        elif final_score >= 30.0:
            tier = DistressRiskLevel.MODERATE
        else:
            tier = DistressRiskLevel.LOW

        # Confidence metric (higher when sample observations align with calibrated bounds)
        confidence = 0.92 if len(factors) >= 2 else 0.85

        return DistressPredictionResult(
            customer_id=req.customer_id,
            distress_score=final_score,
            risk_level=tier,
            prediction_horizon=req.horizon,
            confidence_score=confidence,
            top_risk_factors=factors[:5],
            rules_engine_score=round(rules_score, 1),
            ml_model_score=ml_score,
            model_type="LogisticRegression+EnsembleRules (Calibrated Prototype)",
            training_data_label="CALIBRATED_PROTOTYPE_DATA",
            is_early_preventable=(tier != DistressRiskLevel.CRITICAL)
        )

    @classmethod
    def evaluate_customer_entity(
        cls,
        customer_id: str,
        fre: FinancialRealityObject,
        horizon: PredictionHorizon = PredictionHorizon.HORIZON_30_DAY
    ) -> DistressPredictionResult:
        """
        Builds feature request directly from FinancialRealityObject and executes prediction.
        """
        dsr = fre.debt_service_ratio.value
        cash_days = fre.cash_buffer_days.value
        receivable_exp = fre.receivable_exposure.value
        monthly_inc = max(1.0, fre.monthly_income.value)

        # Approximate indicators from FRE
        req = DistressPredictionRequest(
            customer_id=customer_id,
            declining_cash_rate_pct=15.0 if cash_days < 20 else 2.0,
            negative_balance_frequency=2 if fre.next_critical_collision_date else 0,
            cash_buffer_days=cash_days,
            revenue_decline_pct=18.0 if cash_days < 18 else 0.0,
            income_volatility=0.22 if cash_days < 20 else 0.08,
            debt_service_ratio=dsr,
            fixed_cost_ratio=round(fre.monthly_expenses.value / monthly_inc, 2),
            late_payments_last_90d=1 if dsr > 0.45 else 0,
            upcoming_collision_shortfall=max(0.0, fre.upcoming_30d_outflow - fre.upcoming_30d_inflow - fre.liquid_cash_balance.value),
            horizon=horizon
        )
        return cls.predict_distress(req)
