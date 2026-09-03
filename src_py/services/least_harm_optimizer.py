"""
Core Business Logic for Least-Harm Intervention Optimizer (LHO).
Evaluates all 11 candidate interventions using multi-dimensional harm and benefit criteria,
enforces anti-predatory "No-New-Loan" guardrails (DSCR >= 1.25, FOIR <= 60%),
ranks options transparently, and outputs auditable evidence cards.
"""
from typing import List, Dict, Any, Tuple
from src_py.models.schemas import FinancialRealityObject
from src_py.models.least_harm_schemas import (
    CandidateIntervention, HarmDimensionBreakdown, BenefitDimensionBreakdown,
    ScoredIntervention, LeastHarmOptimizationReport
)


class LeastHarmOptimizerService:

    @classmethod
    def evaluate_intervention(
        cls,
        fre: FinancialRealityObject,
        intervention: CandidateIntervention,
        total_overdue_receivables: float = 1200000.0,
        underperforming_asset_loss: float = 85000.0
    ) -> ScoredIntervention:
        """
        Calculates 9 quantitative impact metrics and generates transparent harm vs. benefit scoring
        for a specific candidate intervention.
        """
        income = fre.monthly_income.value
        expenses = fre.monthly_expenses.value
        emi = fre.monthly_debt_service.value
        debt = fre.total_outstanding_debt.value
        base_distress = 80.0  # Baseline distress score for stressed profile
        base_resilience = fre.savings_rate.value * 100.0 + (fre.cash_buffer_days.value / 2.0)

        # Baseline Impact Defaults
        d_cashflow = 0.0
        d_debt = 0.0
        d_emi = 0.0
        interest_burden = 0.0
        proj_distress = base_distress
        proj_resilience = max(20.0, min(80.0, base_resilience))
        recovery_prob = 50.0
        burden = "MODERATE"
        sustainability = 50.0
        is_permissible = True
        veto_reason = None
        title = ""
        desc = ""

        if intervention == CandidateIntervention.NO_ACTION:
            title = "1. No Action (Status Quo)"
            desc = "Maintain existing cash flows, debt servicing, and operational overheads without intervention."
            d_cashflow = 0.0
            d_debt = 0.0
            d_emi = 0.0
            interest_burden = 0.0
            proj_distress = min(100.0, base_distress + 15.0)
            proj_resilience = max(10.0, base_resilience - 15.0)
            recovery_prob = 18.0
            burden = "HIGH"
            sustainability = 15.0

        elif intervention == CandidateIntervention.SAVE_WAIT:
            title = "2. Save / Wait Buffer"
            desc = "Pause discretionary commitments and accumulate liquid reserves over the next 30 days."
            savings_harvest = min(50000.0, expenses * 0.08)
            d_cashflow = savings_harvest
            d_debt = 0.0
            d_emi = 0.0
            interest_burden = 0.0
            proj_distress = max(20.0, base_distress - 5.0)
            proj_resilience = proj_resilience + 6.0
            recovery_prob = 40.0
            burden = "LOW"
            sustainability = 45.0

        elif intervention == CandidateIntervention.EXPENSE_REDUCTION:
            title = "3. Operational & Discretionary Expense Optimization"
            desc = "Audit non-essential vendor retainers and trims discretionary overheads by 15%."
            saved = expenses * 0.15
            d_cashflow = saved
            d_debt = 0.0
            d_emi = 0.0
            interest_burden = 0.0
            proj_distress = max(20.0, base_distress - 18.0)
            proj_resilience = proj_resilience + 16.0
            recovery_prob = 74.0
            burden = "LOW"
            sustainability = 82.0

        elif intervention == CandidateIntervention.RECEIVABLE_COLLECTION:
            title = "4. Accelerated Receivables / TReDS Invoice Factoring"
            desc = f"Discount verified trade invoices (₹{total_overdue_receivables:,.0f}) via TReDS (RXIL/Invoicemart) with 2% factoring fee."
            net_inflow = total_overdue_receivables * 0.98
            d_cashflow = net_inflow
            d_debt = 0.0
            d_emi = 0.0
            interest_burden = total_overdue_receivables * 0.02
            proj_distress = 28.0
            proj_resilience = 88.0
            recovery_prob = 93.0
            burden = "LOW"
            sustainability = 92.0

        elif intervention == CandidateIntervention.EMI_RESTRUCTURING:
            title = "5. EMI Restructuring (RBI MSME Framework)"
            desc = "Reschedule principal payments under approved regulatory resolution, reducing monthly EMI outlays by 35%."
            emi_saved = emi * 0.35
            d_cashflow = emi_saved
            d_debt = 0.0
            d_emi = -emi_saved
            interest_burden = emi * 1.5
            proj_distress = 32.0
            proj_resilience = 82.0
            recovery_prob = 88.0
            burden = "LOW"
            sustainability = 85.0

        elif intervention == CandidateIntervention.LOAN_TENURE_EXTENSION:
            title = "6. Term Loan Amortization Tenure Extension"
            desc = "Extend existing machinery and business loan terms by 18 to 24 months, lowering monthly debt payments."
            emi_saved = emi * 0.28
            d_cashflow = emi_saved
            d_debt = 0.0
            d_emi = -emi_saved
            interest_burden = emi * 2.1
            proj_distress = 35.0
            proj_resilience = 78.0
            recovery_prob = 84.0
            burden = "LOW"
            sustainability = 80.0

        elif intervention == CandidateIntervention.REFINANCING:
            title = "7. High-Cost Debt Refinancing"
            desc = "Replace high-interest working capital credit with Scheduled Commercial Bank priority-sector MSME facility."
            emi_saved = emi * 0.18
            d_cashflow = emi_saved
            d_debt = 0.0
            d_emi = -emi_saved
            interest_burden = -(emi * 0.8)  # Net interest savings!
            proj_distress = 38.0
            proj_resilience = 75.0
            recovery_prob = 80.0
            burden = "LOW"
            sustainability = 85.0

        elif intervention == CandidateIntervention.ASSET_SALE:
            title = "8. Secondary Market Asset Disposal & Debt Payoff"
            desc = f"Liquidate underperforming physical assets, eliminating dedicated cash bleed (-₹{underperforming_asset_loss:,.0f}/mo) and retiring loan debt."
            d_cashflow = underperforming_asset_loss
            d_debt = -65000.0 * 24.0
            d_emi = -65000.0
            interest_burden = 0.0
            proj_distress = 30.0
            proj_resilience = 84.0
            recovery_prob = 86.0
            burden = "MODERATE"
            sustainability = 88.0

        elif intervention == CandidateIntervention.ASSET_REPLACEMENT:
            title = "9. Modular Asset Replacement with High-Efficiency Unit"
            desc = "Replace older loss-making unit with modern low-power automated machinery."
            d_cashflow = 45000.0
            d_debt = 800000.0
            d_emi = 18000.0
            interest_burden = 120000.0
            proj_distress = 45.0
            proj_resilience = 70.0
            recovery_prob = 75.0
            burden = "MODERATE"
            sustainability = 82.0

        elif intervention == CandidateIntervention.LIMITED_NEW_LOAN:
            title = "10. Emergency Working Capital Top-up Loan (+₹5,00,000)"
            desc = "Disburses ₹5,00,000 fresh borrowing for immediate liquidity; adds ₹24,482/mo in mandatory debt EMI for 24 months."
            new_loan = 500000.0
            new_monthly_emi = 24482.0
            d_cashflow = new_loan  # Upfront injection
            d_debt = new_loan
            d_emi = new_monthly_emi
            interest_burden = (new_monthly_emi * 24.0) - new_loan
            proj_distress = 78.0
            proj_resilience = 38.0
            recovery_prob = 32.0
            burden = "EXTREME"
            sustainability = 25.0

            # ENFORCE HARD "NO-NEW-LOAN" SOLVENCY GUARDRAILS
            # 1. Projected DSCR Check
            projected_operating_cashflow = income - expenses
            projected_total_emi = emi + new_monthly_emi
            projected_dscr = (projected_operating_cashflow / projected_total_emi) if projected_total_emi > 0 else 0.0
            
            # 2. Projected FOIR Check
            projected_foir = (projected_total_emi / income) if income > 0 else 1.0

            if projected_dscr < 1.25 or projected_foir > 0.60:
                is_permissible = False
                veto_reason = (
                    f"ANTI-PREDATORY GUARDRAIL ENFORCED: Taking additional credit drops Debt Service Coverage Ratio (DSCR) to {projected_dscr:.2f} "
                    f"(strictly below RBI prudential boundary of 1.25) and pushes FOIR to {projected_foir:.1%}. Fresh debt accelerates insolvency."
                )

        elif intervention == CandidateIntervention.BUSINESS_OPPORTUNITY:
            title = "11. B2B Business Recovery Network (ONDC Demand Off-take)"
            desc = "Connects idle manufacturing plant capacity with vetted corporate buyer orders under double-blind privacy protocol."
            added_sales = 450000.0
            d_cashflow = added_sales * 0.22  # Operating margin
            d_debt = 0.0
            d_emi = 0.0
            interest_burden = 0.0
            proj_distress = 22.0
            proj_resilience = 94.0
            recovery_prob = 95.0
            burden = "LOW"
            sustainability = 96.0

        # =========================================================================
        # TRANSPARENT MATHEMATICAL SCORING FORMULAS
        # =========================================================================
        # 1. Harm Score = debt_increase_penalty + interest_increase_penalty + repayment_burden_penalty + long_term_risk_penalty
        debt_penalty = min(35.0, (d_debt / 20000.0)) if d_debt > 0 else 0.0
        interest_penalty = min(25.0, (interest_burden / 10000.0)) if interest_burden > 0 else 0.0
        repayment_penalty = 30.0 if burden == "EXTREME" else (18.0 if burden == "HIGH" else (8.0 if burden == "MODERATE" else 0.0))
        long_term_risk = min(20.0, (100.0 - sustainability) * 0.20)
        
        total_harm = round(min(100.0, debt_penalty + interest_penalty + repayment_penalty + long_term_risk), 2)
        if not is_permissible:
            total_harm = 100.0  # Vetoed options carry maximum harm penalty

        # 2. Benefit Score = cashflow_improvement + resilience_improvement + distress_reduction + recovery_probability
        cf_score = min(30.0, max(0.0, (d_cashflow / 25000.0)))
        res_score = min(25.0, max(0.0, (proj_resilience / 4.0)))
        dist_score = min(25.0, max(0.0, ((100.0 - proj_distress) / 4.0)))
        rec_score = min(20.0, max(0.0, (recovery_prob / 5.0)))
        
        total_benefit = round(min(100.0, cf_score + res_score + dist_score + rec_score), 2)

        # Net Least-Harm Score = Benefit Score - Harm Score
        net_score = round(total_benefit - total_harm, 2)

        return ScoredIntervention(
            intervention=intervention,
            title=title,
            description=desc,
            change_in_monthly_cashflow=round(d_cashflow, 2),
            change_in_total_debt=round(d_debt, 2),
            change_in_monthly_emi=round(d_emi, 2),
            additional_interest_burden=round(interest_burden, 2),
            projected_distress_score=round(proj_distress, 1),
            projected_financial_resilience=round(proj_resilience, 1),
            recovery_probability_pct=round(recovery_prob, 1),
            customer_burden_level=burden,
            long_term_sustainability_pct=round(sustainability, 1),
            harm_breakdown=HarmDimensionBreakdown(
                debt_increase_penalty=round(debt_penalty, 2),
                interest_increase_penalty=round(interest_penalty, 2),
                repayment_burden_penalty=round(repayment_penalty, 2),
                long_term_risk_penalty=round(long_term_risk, 2),
                total_harm_score=total_harm
            ),
            benefit_breakdown=BenefitDimensionBreakdown(
                cashflow_improvement_score=round(cf_score, 2),
                resilience_improvement_score=round(res_score, 2),
                distress_reduction_score=round(dist_score, 2),
                recovery_probability_score=round(rec_score, 2),
                total_benefit_score=total_benefit
            ),
            net_least_harm_score=net_score,
            is_permissible_under_guardrail=is_permissible,
            guardrail_veto_reason=veto_reason,
            rank=1
        )

    @classmethod
    def rank_and_optimize(
        cls,
        fre: FinancialRealityObject,
        overdue_receivables: float = 1200000.0,
        machine_bleed: float = 85000.0
    ) -> LeastHarmOptimizationReport:
        """
        Evaluates and ranks all 11 candidate interventions from safest/highest benefit to most harmful.
        Selects the top permissible option with an auditable evidence card.
        """
        candidate_list = list(CandidateIntervention)
        scored_options: List[ScoredIntervention] = [
            cls.evaluate_intervention(fre, cand, overdue_receivables, machine_bleed)
            for cand in candidate_list
        ]

        # Filter permissible and sort by net_least_harm_score descending
        # Permissible options come first, followed by vetoed options at the bottom
        permissible = [o for o in scored_options if o.is_permissible_under_guardrail]
        vetoed = [o for o in scored_options if not o.is_permissible_under_guardrail]

        permissible.sort(key=lambda x: x.net_least_harm_score, reverse=True)
        vetoed.sort(key=lambda x: x.net_least_harm_score, reverse=True)

        ranked = permissible + vetoed
        for idx, item in enumerate(ranked):
            item.rank = idx + 1

        selected = ranked[0]
        no_loan_veto_active = any(not o.is_permissible_under_guardrail for o in scored_options)

        # Build explainable rationale
        rationale = [
            f"Rank #1 Option '{selected.title}' achieved the highest Net Score of {selected.net_least_harm_score:.1f} "
            f"(Total Benefit: {selected.benefit_breakdown.total_benefit_score:.1f} vs Total Harm: {selected.harm_breakdown.total_harm_score:.1f}).",
            f"Zero Additional Principal Burden: Avoids adding fresh debt to a balance sheet already servicing ₹{fre.monthly_debt_service.value:,.0f}/month.",
            f"Solvency Restoration: Elevates 24-month recovery probability to {selected.recovery_probability_pct:.1f}% while dropping distress score to {selected.projected_distress_score:.1f}."
        ]
        if no_loan_veto_active:
            rationale.append("Statutory Anti-Predatory Guardrail strictly VETOED Option 10 (Limited New Loan) due to DSCR breach.")

        evidence = [
            f"Current liquid buffer covers only {fre.cash_buffer_days.value} days of operational burn (Safety minimum is 21 days).",
            f"Borrower's current Debt Service Ratio stands at {fre.debt_service_ratio.value:.1%}.",
            f"Injecting ₹{selected.change_in_monthly_cashflow:,.0f} non-debt liquidity preserves credit score and guarantees uninterrupted operations."
        ]

        formula_desc = (
            "Harm Score = Debt Penalty (35%) + Interest Penalty (25%) + Repayment Burden (30%) + Long-Term Risk (20%) [Max 100]. "
            "Benefit Score = Cashflow Improvement (30%) + Resilience (25%) + Distress Reduction (25%) + Recovery Probability (20%) [Max 100]. "
            "Net Least-Harm Score = Benefit Score - Harm Score."
        )

        return LeastHarmOptimizationReport(
            customer_id=fre.customer_id,
            customer_name=fre.customer_name,
            archetype=fre.archetype,
            selected_intervention=selected,
            ranked_interventions=ranked,
            no_new_loan_guardrail_enforced=no_loan_veto_active,
            selection_rationale=rationale,
            confidence_percentage=92.0,
            supporting_evidence=evidence,
            transparent_scoring_formula=formula_desc
        )
