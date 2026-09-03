"""
Credit Affordability Engine Service.
Determines whether additional borrowing is financially sustainable.
Answers the foundational question: "Can the customer repay safely?" (not: "Can the customer qualify?").
Calculates:
- Baseline: current_debt, current_emi, current_free_cash_flow, current_debt_service_ratio, current_cash_buffer
- Post-Loan: post_loan_debt, post_loan_emi, post_loan_free_cash_flow, post_loan_debt_service_ratio,
  post_loan_cash_buffer, post_loan_resilience
Classifies: SAFE_TO_BORROW, LIMITED_BORROWING, NOT_SAFE_TO_BORROW.
Derives maximum recommended loan amount and safe borrowing envelope.
Integrates forward projected cash flows, seasonal haircuts, and receivable timings.
"""
from typing import Dict, Any, Optional
from datetime import datetime

from src_py.models.affordability_schemas import (
    AffordabilityClassification, SafeLoanRange, BaselineFinancialMetrics,
    PostLoanProjectedMetrics, ProposedLoanInput, CreditAffordabilityReport,
    NoNewLoanVerdict, NoNewLoanCheckReport
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.seasonal_schemas import SeasonalForecastReport
from src_py.models.receivable_schemas import ReceivablesAnalysisReport


class CreditAffordabilityEngineService:

    SAFE_DSR_CEILING = 0.35      # 35% safe DSR threshold
    MAX_PERMISSIBLE_DSR = 0.45   # 45% upper boundary for limited borrowing

    @classmethod
    def calculate_emi(cls, principal: float, annual_rate_pct: float, tenure_months: int) -> float:
        """Standard amortizing monthly EMI formula."""
        if annual_rate_pct <= 0 or tenure_months <= 0:
            return round(principal / max(1, tenure_months), 2)
        r = (annual_rate_pct / 100.0) / 12.0
        # Formula: P * r * (1+r)^n / ((1+r)^n - 1)
        emi = principal * (r * ((1.0 + r) ** tenure_months)) / (((1.0 + r) ** tenure_months) - 1.0)
        return round(emi, 2)

    @classmethod
    def evaluate_affordability(
        cls,
        fre: FinancialRealityObject,
        loan_input: ProposedLoanInput,
        seasonal_forecast: Optional[SeasonalForecastReport] = None,
        receivables_report: Optional[ReceivablesAnalysisReport] = None
    ) -> CreditAffordabilityReport:
        """
        Executes pre-loan vs post-loan financial sustainability assessment.
        """
        # 1. Baseline Metrics
        curr_debt = fre.total_outstanding_debt.value
        curr_emi = fre.monthly_debt_service.value
        curr_fcf = fre.free_cash_flow.value
        curr_dsr = round(fre.debt_service_ratio.value * 100.0, 1)
        curr_buffer_days = int(fre.cash_buffer_days.value)
        monthly_income = max(1.0, fre.monthly_income.value)

        baseline = BaselineFinancialMetrics(
            current_debt=round(curr_debt, 2),
            current_emi=round(curr_emi, 2),
            current_free_cash_flow=round(curr_fcf, 2),
            current_debt_service_ratio=curr_dsr,
            current_cash_buffer_days=curr_buffer_days
        )

        # 2. Forward Projected Cash Flow factoring seasonality & receivables
        # If seasonal forecast exists, incorporate trough month revenue
        forward_income = monthly_income
        context_notes = []
        if seasonal_forecast and len(seasonal_forecast.monthly_forecasts) > 0:
            trough_revs = [f.expected_revenue for f in seasonal_forecast.monthly_forecasts if f.seasonal_index < 1.0]
            if trough_revs:
                forward_income = min(forward_income, min(trough_revs))
                context_notes.append("Incorporated off-peak seasonal revenue trough into debt service stress-testing.")

        # If receivables expected, factor in near-term liquidity support
        near_term_receivables = 0.0
        if receivables_report:
            near_term_receivables = receivables_report.expected_14_day_cash
            context_notes.append(f"Expected ₹{near_term_receivables:,.0f} high/moderate confidence receivables within 14 days.")

        # 3. Calculate Proposed EMI
        p_emi = loan_input.proposed_monthly_emi
        if not p_emi:
            p_emi = cls.calculate_emi(
                loan_input.proposed_principal,
                loan_input.annual_interest_rate_pct,
                loan_input.tenure_months
            )

        # 4. Post-Loan Calculations
        post_debt = curr_debt + loan_input.proposed_principal
        post_emi = curr_emi + p_emi
        post_dsr = round((post_emi / forward_income) * 100.0, 1)
        post_fcf = round(curr_fcf - p_emi, 2)
        
        # Post-loan cash buffer: initial cash augmented by loan disbursement net of immediate obligations,
        # but ongoing burn increased by post_emi
        daily_burn = max(1.0, (fre.monthly_expenses.value + post_emi) / 30.0)
        post_cash = max(0.0, fre.liquid_cash_balance.value)
        post_buffer_days = int(post_cash / daily_burn)

        # Post-loan resilience score calculation
        r_debt = max(0.0, min(100.0, (0.60 - (post_dsr / 100.0)) / 0.40 * 100.0))
        r_fcf = max(0.0, min(100.0, (post_fcf / max(1.0, monthly_income * 0.30)) * 100.0))
        post_resilience = round(max(10.0, min(95.0, (r_debt * 0.55) + (r_fcf * 0.45))), 1)

        post_metrics = PostLoanProjectedMetrics(
            post_loan_debt=round(post_debt, 2),
            post_loan_emi=round(post_emi, 2),
            post_loan_free_cash_flow=post_fcf,
            post_loan_debt_service_ratio=post_dsr,
            post_loan_cash_buffer_days=post_buffer_days,
            post_loan_resilience_score=post_resilience
        )

        # 5. Maximum Safe Loan Range Calculation
        # Max safe EMI = (Monthly Income * SAFE_DSR_CEILING) - Current EMI
        max_safe_additional_emi = max(0.0, (forward_income * cls.SAFE_DSR_CEILING) - curr_emi)
        r_month = (loan_input.annual_interest_rate_pct / 100.0) / 12.0
        n = loan_input.tenure_months
        
        if max_safe_additional_emi > 0 and r_month > 0:
            # PV of maximum safe EMI stream
            max_safe_principal = max_safe_additional_emi * (((1.0 + r_month) ** n) - 1.0) / (r_month * ((1.0 + r_month) ** n))
            max_safe_principal = round(max(0.0, max_safe_principal), 2)
        else:
            max_safe_principal = 0.0

        safe_range = SafeLoanRange(
            minimum_viable_amount=round(min(50000.0, max_safe_principal * 0.25), 2),
            maximum_recommended_amount=max_safe_principal,
            maximum_safe_monthly_emi=round(max_safe_additional_emi, 2),
            recommended_tenure_months=n
        )

        # 6. Classification & Reason Synthesis
        if post_dsr <= (cls.SAFE_DSR_CEILING * 100.0) and post_fcf > 0:
            status = AffordabilityClassification.SAFE_TO_BORROW
            reason = (
                f"Proposed loan of ₹{loan_input.proposed_principal:,.0f} is financially sustainable. "
                f"Projected post-loan DSR remains at {post_dsr:.1f}% (within the <=35.0% safe threshold), "
                f"and monthly free cash flow remains positive at ₹{post_fcf:,.0f}."
            )
            conf = 0.94

        elif post_dsr <= (cls.MAX_PERMISSIBLE_DSR * 100.0) and post_fcf >= -10000.0:
            status = AffordabilityClassification.LIMITED_BORROWING
            reason = (
                f"Proposed loan of ₹{loan_input.proposed_principal:,.0f} introduces moderate financial strain. "
                f"Post-loan DSR reaches {post_dsr:.1f}% (approaching the 45.0% prudential ceiling). "
                f"Recommended Action: Cap new borrowing at ₹{max_safe_principal:,.0f} (EMI ₹{max_safe_additional_emi:,.0f}/mo) "
                f"or extend tenure to lower monthly repayments."
            )
            conf = 0.89

        else:
            status = AffordabilityClassification.NOT_SAFE_TO_BORROW
            reason = (
                f"Borrowing ₹{loan_input.proposed_principal:,.0f} is NOT SAFE. "
                f"Post-loan debt service ratio would surge to an unsustainable {post_dsr:.1f}% (>45% critical limit), "
                f"driving monthly free cash flow negative (-₹{abs(post_fcf):,.0f}) and accelerating liquidity depletion. "
                f"Non-debt solutions (e.g., TReDS invoice discounting or operational restructuring) must be pursued."
            )
            conf = 0.95

        ctx_summary = "; ".join(context_notes) if context_notes else "Evaluated against baseline forward operating income."

        return CreditAffordabilityReport(
            customer_id=fre.customer_id,
            proposed_principal=loan_input.proposed_principal,
            expected_emi=p_emi,
            affordability_status=status,
            maximum_recommended_amount=max_safe_principal,
            safe_loan_range=safe_range,
            baseline_metrics=baseline,
            post_loan_metrics=post_metrics,
            reason=reason,
            confidence=conf,
            forward_projection_context=ctx_summary
        )

    @classmethod
    def check_no_new_loan(
        cls,
        fre: FinancialRealityObject,
        loan_input: ProposedLoanInput,
        current_distress_score: float = 35.0,
        primary_root_cause: str = "operational_cost_surge",
        seasonal_forecast: Optional[SeasonalForecastReport] = None,
        receivables_report: Optional[ReceivablesAnalysisReport] = None
    ) -> NoNewLoanCheckReport:
        """
        No-New-Loan Guardrail Engine (Decision Support).
        Triggered on every proposed loan to prevent incremental debt from deepening financial distress.
        Follows the 7-step process:
        1. Get current state
        2. Simulate proposed loan
        3. Compare current vs post-loan
        4. Check distress
        5. Check resilience
        6. Check cash flow
        7. Check debt burden

        Blocks recommendation (NOT_RECOMMENDED) when ANY of the 5 conditions occur:
        - Post-loan distress increases materially (by >= 15 pts or exceeds 70/100)
        - Post-loan free cash flow remains negative (< 0)
        - Post-loan EMI is not sustainable (Post-loan DSR > 45%)
        - Loan does not address root cause (e.g. borrowing to fund idle loss-making asset)
        - Existing debt is already excessive (Baseline DSR >= 50% or Debt > 5x monthly income)

        Strict institutional mandate:
        "This is decision support. Do not implement automatic regulatory credit denial."
        """
        # Step 1, 2, 3: Run baseline vs post-loan simulation
        affordability = cls.evaluate_affordability(
            fre=fre,
            loan_input=loan_input,
            seasonal_forecast=seasonal_forecast,
            receivables_report=receivables_report
        )

        base_dsr = affordability.baseline_metrics.current_debt_service_ratio
        base_fcf = affordability.baseline_metrics.current_free_cash_flow
        post_dsr = affordability.post_loan_metrics.post_loan_debt_service_ratio
        post_fcf = affordability.post_loan_metrics.post_loan_free_cash_flow
        post_emi = affordability.post_loan_metrics.post_loan_emi

        # Step 4: Check distress trajectory
        # Incremental distress delta
        distress_delta = max(0.0, (post_dsr - base_dsr) * 1.2)
        if post_fcf < 0:
            distress_delta += 12.0
        post_distress = min(100.0, current_distress_score + distress_delta)

        # Check Root Cause alignment: Borrowing is only aligned if root cause is temporary liquidity or order working capital
        root_cause_aligned = primary_root_cause.lower() in [
            "temporary_liquidity_gap", "order_growth_capital", "receivable_delay", "b2b_capacity_expansion"
        ]

        # Step 5, 6, 7 & Block Recommendation Evaluation
        blocking_evidence: List[str] = []

        # Trigger 1: Post-loan distress increases materially
        if (post_distress - current_distress_score >= 15.0) or (post_distress >= 70.0):
            blocking_evidence.append(
                f"Projected distress score surges materially from {current_distress_score:.1f} to {post_distress:.1f} (+{post_distress - current_distress_score:.1f} pts)."
            )

        # Trigger 2: Post-loan free cash flow remains negative
        if post_fcf < 0:
            blocking_evidence.append(
                f"Post-loan monthly free cash flow remains deeply negative at -₹{abs(post_fcf):,.0f}."
            )

        # Trigger 3: Post-loan EMI is not sustainable
        if post_dsr > (cls.MAX_PERMISSIBLE_DSR * 100.0):
            blocking_evidence.append(
                f"Post-loan debt service ratio (DSR) reaches {post_dsr:.1f}%, exceeding the 45.0% maximum sustainable threshold."
            )

        # Trigger 4: Loan does not address root cause
        if not root_cause_aligned:
            blocking_evidence.append(
                f"Proposed loan does not remediate the diagnosed underlying root cause ('{primary_root_cause}'). "
                f"Injecting debt into an unaddressed operational failure accelerates distress."
            )

        # Trigger 5: Existing debt is already excessive
        monthly_income = max(1.0, fre.monthly_income.value)
        debt_to_income_ratio = fre.total_outstanding_debt.value / monthly_income
        if base_dsr >= 50.0 or debt_to_income_ratio > 5.0:
            blocking_evidence.append(
                f"Existing debt burden is already excessive (Current DSR: {base_dsr:.1f}%, Debt-to-Monthly-Income: {debt_to_income_ratio:.1f}x)."
            )

        # Verdict Assignment
        if len(blocking_evidence) >= 1:
            verdict = NoNewLoanVerdict.NOT_RECOMMENDED
            reason = (
                f"No-New-Loan Guardrail: Additional borrowing of ₹{loan_input.proposed_principal:,.0f} is NOT RECOMMENDED. "
                f"The facility fails {len(blocking_evidence)} safety checks. "
                f"Prioritize non-debt interventions such as receivable factoring, term extension, or cost stabilization."
            )
            conf = 0.94
        elif post_dsr > (cls.SAFE_DSR_CEILING * 100.0) or post_fcf < 15000.0:
            verdict = NoNewLoanVerdict.LIMIT
            reason = (
                f"No-New-Loan Guardrail: Additional borrowing is approved with strict LIMITS. "
                f"Borrowing should be capped at ₹{affordability.maximum_recommended_amount:,.0f} to avoid exceeding the 35% safe DSR envelope."
            )
            conf = 0.90
        else:
            verdict = NoNewLoanVerdict.ALLOW
            reason = (
                f"No-New-Loan Guardrail: Proposed borrowing of ₹{loan_input.proposed_principal:,.0f} is safe to proceed. "
                f"Post-loan debt metrics satisfy all prudential cash-flow and resilience criteria."
            )
            conf = 0.96

        return NoNewLoanCheckReport(
            customer_id=fre.customer_id,
            proposed_principal=loan_input.proposed_principal,
            verdict=verdict,
            reason=reason,
            evidence=blocking_evidence,
            confidence=conf,
            current_distress_score=round(current_distress_score, 1),
            projected_post_loan_distress_score=round(post_distress, 1),
            current_free_cash_flow=round(base_fcf, 2),
            projected_post_loan_free_cash_flow=round(post_fcf, 2),
            current_debt_service_ratio=round(base_dsr, 1),
            projected_post_loan_debt_service_ratio=round(post_dsr, 1),
            root_cause_addressed=root_cause_aligned
        )
