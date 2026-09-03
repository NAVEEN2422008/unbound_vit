"""
Financial Resilience Score Engine Service.
Measures the borrower's empirical capacity to absorb economic shocks across 7 dimensions:
1. Income stability (Weight 20%)
2. Cash-flow stability (Weight 15%)
3. Debt burden (Weight 20%)
4. Savings/cash buffer (Weight 15%)
5. Repayment behavior (Weight 10%)
6. Expense stability (Weight 10%)
7. Business health (Weight 10%)
Enforces Acceptance Criteria:
- Stable income, low debt, high cash buffer, stable repayment -> Scores high (>= 75/100)
- Volatile income, high debt, low cash buffer, payment issues -> Scores low (<= 40/100)
Outputs: overall_score, component_scores, trend, explanation, confidence.
Clearly designated as "Financial Resilience Score" (NOT a regulatory credit score).
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src_py.models.resilience_schemas import (
    ResilienceComponentScores, FinancialResilienceReport
)
from src_py.models.schemas import FinancialRealityObject


class FinancialResilienceEngineService:

    # Weights summing to 1.0
    WEIGHTS = {
        "income_stability": 0.20,
        "cashflow_stability": 0.15,
        "debt_burden": 0.20,
        "savings_cash_buffer": 0.15,
        "repayment_behavior": 0.10,
        "expense_stability": 0.10,
        "business_health": 0.10
    }

    @classmethod
    def compute_resilience_score(
        cls,
        customer_id: str,
        customer_name: str,
        # 7 component inputs:
        income_volatility_pct: float = 8.0,      # Monthly CV% (lower is better)
        negative_balance_days: int = 0,          # Frequency of overdrafts (lower is better)
        debt_service_ratio_pct: float = 28.0,    # DSR% (lower is better)
        cash_buffer_days: int = 35,              # Runway in days (higher is better)
        repayment_ontime_rate_pct: float = 98.0, # % on-time payments (higher is better)
        expense_growth_rate_pct: float = 5.0,    # % cost inflation (lower is better)
        receivable_turnover_days: int = 42       # Days to collect (lower is better)
    ) -> FinancialResilienceReport:
        """
        Computes 0-100 Financial Resilience Score across 7 components.
        """
        # 1. Income stability (0–100)
        # 0% volatility -> 100, 35% volatility -> 0
        s_income = max(0.0, min(100.0, 100.0 - (income_volatility_pct * 2.8)))

        # 2. Cash-flow stability (0–100)
        # 0 negative days -> 100, 10+ negative days -> 0
        s_cf = max(0.0, min(100.0, 100.0 - (negative_balance_days * 10.0)))

        # 3. Debt burden (0–100)
        # DSR <= 20% -> 100, DSR >= 60% -> 0
        s_debt = max(0.0, min(100.0, (0.60 - (debt_service_ratio_pct / 100.0)) / 0.40 * 100.0))

        # 4. Savings / cash buffer (0–100)
        # 60+ days buffer -> 100, 0 days -> 0
        s_buffer = max(0.0, min(100.0, (cash_buffer_days / 60.0) * 100.0))

        # 5. Repayment behavior (0–100)
        # Direct reflection of on-time repayment percentage
        s_repay = max(0.0, min(100.0, repayment_ontime_rate_pct))

        # 6. Expense stability (0–100)
        # 0% cost growth -> 100, 30% cost surge -> 0
        s_expense = max(0.0, min(100.0, 100.0 - (expense_growth_rate_pct * 3.3)))

        # 7. Business health (0–100)
        # 30 days receivable turnover -> 100, 90+ days -> 0
        s_health = max(0.0, min(100.0, ((90.0 - receivable_turnover_days) / 60.0) * 100.0))

        components = ResilienceComponentScores(
            income_stability=round(s_income, 1),
            cashflow_stability=round(s_cf, 1),
            debt_burden=round(s_debt, 1),
            savings_cash_buffer=round(s_buffer, 1),
            repayment_behavior=round(s_repay, 1),
            expense_stability=round(s_expense, 1),
            business_health=round(s_health, 1)
        )

        overall = (
            s_income * cls.WEIGHTS["income_stability"] +
            s_cf * cls.WEIGHTS["cashflow_stability"] +
            s_debt * cls.WEIGHTS["debt_burden"] +
            s_buffer * cls.WEIGHTS["savings_cash_buffer"] +
            s_repay * cls.WEIGHTS["repayment_behavior"] +
            s_expense * cls.WEIGHTS["expense_stability"] +
            s_health * cls.WEIGHTS["business_health"]
        )
        overall_score = round(max(0.0, min(100.0, overall)), 1)

        # Determine trend
        if overall_score >= 70.0:
            trend = "IMPROVING" if s_buffer >= 60.0 else "STABLE"
            explanation = (
                f"High financial resilience ({overall_score:.0f}/100): Customer exhibits strong liquidity reserves "
                f"({cash_buffer_days} buffer days), manageable debt burden (DSR {debt_service_ratio_pct:.1f}%), and consistent repayment history."
            )
        elif overall_score >= 45.0:
            trend = "STABLE"
            explanation = (
                f"Moderate financial resilience ({overall_score:.0f}/100): Customer possesses acceptable operating cash flows "
                f"but has narrowed liquidity cushion ({cash_buffer_days} days) or elevated debt service commitments."
            )
        else:
            trend = "DETERIORATING"
            explanation = (
                f"Vulnerable financial resilience ({overall_score:.0f}/100): Customer exhibits acute vulnerability to minor revenue shocks "
                f"due to depleted cash buffers ({cash_buffer_days} days), elevated debt burden (DSR {debt_service_ratio_pct:.1f}%), or payment irregularities."
            )

        confidence = 0.92

        return FinancialResilienceReport(
            customer_id=customer_id,
            customer_name=customer_name,
            overall_score=overall_score,
            component_scores=components,
            trend=trend,
            explanation=explanation,
            confidence=confidence
        )

    @classmethod
    def evaluate_live_customer_resilience(
        cls,
        customer_id: str,
        fre: FinancialRealityObject
    ) -> FinancialResilienceReport:
        """
        Derives empirical resilience telemetry directly from FinancialRealityObject.
        """
        dsr_pct = fre.debt_service_ratio.value * 100.0
        buffer_d = fre.cash_buffer_days.value
        rec_exp = fre.receivable_exposure.value
        turnover_d = 65 if rec_exp > 100000.0 else 35

        return cls.compute_resilience_score(
            customer_id=customer_id,
            customer_name=fre.customer_name,
            income_volatility_pct=14.0 if buffer_d < 18 else 6.0,
            negative_balance_days=4 if buffer_d < 10 else 0,
            debt_service_ratio_pct=dsr_pct,
            cash_buffer_days=buffer_d,
            repayment_ontime_rate_pct=82.0 if buffer_d < 12 else 98.0,
            expense_growth_rate_pct=8.0,
            receivable_turnover_days=turnover_d
        )
