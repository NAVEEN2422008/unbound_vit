"""
Core Business Logic for Least-Harm Intervention Optimizer (LHO).
Evaluates all 11 candidate interventions using multi-dimensional harm and benefit criteria,
enforces anti-predatory "No-New-Loan" guardrails (DSCR >= 1.25, FOIR <= 60%),
ranks options transparently, and outputs auditable evidence cards.
"""
from typing import List, Dict, Any, Tuple, Optional
from src_py.models.schemas import FinancialRealityObject
from src_py.models.least_harm_schemas import (
    CandidateIntervention, HarmDimensionBreakdown, BenefitDimensionBreakdown,
    ScoredIntervention, LeastHarmOptimizationReport,
    InterventionBenefitMetrics, InterventionHarmMetrics,
    LeastHarmInterventionScoredItem, LeastHarmOptimizeResponse
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
        candidate_list = [
            CandidateIntervention.NO_ACTION,
            CandidateIntervention.SAVE_WAIT,
            CandidateIntervention.EXPENSE_REDUCTION,
            CandidateIntervention.RECEIVABLE_COLLECTION,
            CandidateIntervention.EMI_RESTRUCTURING,
            CandidateIntervention.LOAN_TENURE_EXTENSION,
            CandidateIntervention.REFINANCING,
            CandidateIntervention.ASSET_SALE,
            CandidateIntervention.ASSET_REPLACEMENT,
            CandidateIntervention.LIMITED_NEW_LOAN,
            CandidateIntervention.BUSINESS_OPPORTUNITY
        ]
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

    @classmethod
    def optimize_interventions(
        cls,
        fre: FinancialRealityObject,
        benefit_weights: Optional[Dict[str, float]] = None,
        harm_weights: Optional[Dict[str, float]] = None
    ) -> LeastHarmOptimizeResponse:
        """
        Selects the intervention providing meaningful distress reduction with lowest long-term customer harm.
        Evaluates all 11 specified interventions:
        NO_ACTION, SAVE_WAIT, EXPENSE_REDUCTION, RECEIVABLE_ACCELERATION, EMI_RESTRUCTURE,
        TENURE_EXTENSION, REFINANCE, ASSET_ACTION, LIMITED_CREDIT, BUSINESS_RECOVERY, BUSINESS_MATCHING.

        Benefit Metrics:
        - cashflow_improvement, distress_reduction, resilience_improvement, recovery_probability
        Harm Metrics:
        - new_debt, interest_increase, EMI_increase, cash_buffer_reduction,
          long_term_repayment_pressure, asset_loss

        Transparent weighted scoring model:
        intervention_score = benefit_score / max(1.0, harm_score)
        Weights are configurable.
        Guiding Mandate: Never optimize purely for bank revenue; objective is sustainable financial recovery.
        """
        # Default configurable weights
        b_weights = {
            "cashflow_improvement": 0.30,
            "distress_reduction": 0.25,
            "resilience_improvement": 0.25,
            "recovery_probability": 0.20
        }
        if benefit_weights:
            b_weights.update(benefit_weights)

        h_weights = {
            "new_debt": 0.25,
            "interest_increase": 0.15,
            "EMI_increase": 0.20,
            "cash_buffer_reduction": 0.15,
            "long_term_repayment_pressure": 0.15,
            "asset_loss": 0.10
        }
        if harm_weights:
            h_weights.update(harm_weights)

        interventions_to_evaluate = [
            (CandidateIntervention.NO_ACTION, "1. Maintain Status Quo (No Action)", "No operational or debt changes.",
             {"cf": 0.0, "dist": 5.0, "resil": 15.0, "rec": 15.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 45.0, "press": 60.0, "loss": 0.0},
             ["Avoids new debt commitments."], ["Ongoing cash drain risks working capital depletion."],
             "Status quo provides zero corrective relief.", 0.95),

            (CandidateIntervention.SAVE_WAIT, "2. Defensive Liquidity Preservation (Save & Wait)", "Conserve discretionary cash while monitoring collections.",
             {"cf": 15.0, "dist": 20.0, "resil": 30.0, "rec": 25.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 10.0, "press": 40.0, "loss": 0.0},
             ["Zero debt accumulation."], ["Does not solve structural shortfall."],
             "Viable only for micro gaps with stable baseline.", 0.90),

            (CandidateIntervention.EXPENSE_REDUCTION, "3. Operating Overhead Rationalization (-15%)", "Cuts administrative, non-critical vendor, and energy overhead.",
             {"cf": 55.0, "dist": 50.0, "resil": 55.0, "rec": 60.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 0.0, "press": 10.0, "loss": 0.0},
             ["Restores +₹45,000/mo operating margin without borrowing."], ["Requires strict expense discipline."],
             "Immediately expands free cash flow buffer.", 0.92),

            (CandidateIntervention.RECEIVABLE_ACCELERATION, "4. TReDS Digital Invoice Acceleration", "Discounts vetted enterprise receivables for immediate non-debt cash influx.",
             {"cf": 85.0, "dist": 75.0, "resil": 80.0, "rec": 88.0},
             {"debt": 0.0, "int": 5.0, "emi": 0.0, "buf_red": 0.0, "press": 5.0, "loss": 0.0},
             ["Converts ₹12L receivables into immediate liquidity.", "Zero long-term EMI or debt balance growth."],
             ["Small 1.5% factoring fee on invoice face value."],
             "Solves immediate liquidity gap without creating loan repayment drag.", 0.96),

            (CandidateIntervention.EMI_RESTRUCTURE, "5. RBI MSME Debt Restructuring (-35% EMI)", "Re-schedules term loan amortization under regulatory MSME framework.",
             {"cf": 75.0, "dist": 70.0, "resil": 72.0, "rec": 82.0},
             {"debt": 5.0, "int": 25.0, "emi": 0.0, "buf_red": 0.0, "press": 20.0, "loss": 0.0},
             ["Immediately saves ₹65,000/mo on debt service outflows."], ["Extended cumulative interest over loan lifetime."],
             "Relieves acute debt service pressure.", 0.94),

            (CandidateIntervention.TENURE_EXTENSION, "6. Loan Tenor Amortization Extension", "Extends repayment horizon from 36 to 60 months to lower monthly installments.",
             {"cf": 68.0, "dist": 65.0, "resil": 68.0, "rec": 78.0},
             {"debt": 5.0, "int": 35.0, "emi": 0.0, "buf_red": 0.0, "press": 30.0, "loss": 0.0},
             ["Reduces monthly EMI by 28%."], ["Higher total interest over 5 years."],
             "Lowers monthly commitment to sustainable level.", 0.91),

            (CandidateIntervention.REFINANCE, "7. SCB Priority Sector Debt Refinancing", "Refinances high-cost NBFC debt with Scheduled Commercial Bank priority MSME credit.",
             {"cf": 62.0, "dist": 60.0, "resil": 65.0, "rec": 74.0},
             {"debt": 0.0, "int": 10.0, "emi": 0.0, "buf_red": 5.0, "press": 15.0, "loss": 0.0},
             ["Lowers interest margin by 250 bps."], ["Requires underwriting verification."],
             "Reduces systemic cost of capital.", 0.89),

            (CandidateIntervention.ASSET_ACTION, "8. Asset Restructuring / Secondary Disposal", "Disposes of loss-making machinery or restructures financing.",
             {"cf": 70.0, "dist": 62.0, "resil": 66.0, "rec": 75.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 0.0, "press": 10.0, "loss": 35.0},
             ["Permanently eliminates dedicated machine operating bleed."], ["Permanent loss of machinery asset capacity."],
             "Releases working capital trapped in unproductive assets.", 0.88),

            (CandidateIntervention.LIMITED_CREDIT, "9. Micro-Working Capital Emergency Line", "Injects strictly capped short-term liquidity line (within 35% safe DSR).",
             {"cf": 65.0, "dist": 50.0, "resil": 55.0, "rec": 68.0},
             {"debt": 45.0, "int": 40.0, "emi": 35.0, "buf_red": 0.0, "press": 45.0, "loss": 0.0},
             ["Provides immediate cash buffer."], ["Increases monthly debt service and long-term interest pressure."],
             "Must be capped strictly to avoid tipping DSR into distress.", 0.87),

            (CandidateIntervention.BUSINESS_RECOVERY, "10. Core Order Book Expansion & Marketing", "Restores customer demand and order volumes to pre-distress baseline.",
             {"cf": 80.0, "dist": 72.0, "resil": 78.0, "rec": 84.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 0.0, "press": 5.0, "loss": 0.0},
             ["Sustainable organic revenue growth."], ["Requires 60–90 days lead time to materialize."],
             "Addresses the fundamental commercial root cause.", 0.85),

            (CandidateIntervention.BUSINESS_MATCHING, "11. Double-Blind B2B Capacity Consortium", "Subleases off-peak machinery capacity and pools raw material procurement.",
             {"cf": 78.0, "dist": 70.0, "resil": 75.0, "rec": 82.0},
             {"debt": 0.0, "int": 0.0, "emi": 0.0, "buf_red": 0.0, "press": 5.0, "loss": 0.0},
             ["Generates incremental off-peak operating income without capital outlay."], ["Depends on peer contract fulfillment."],
             "Restores capacity utilization without additional borrowing.", 0.90)
        ]

        scored_items: List[LeastHarmInterventionScoredItem] = []

        for code, title, desc, b_raw, h_raw, ben_list, risk_list, reason_txt, conf in interventions_to_evaluate:
            # Weighted Benefit Score
            b_score = (
                b_raw["cf"] * b_weights["cashflow_improvement"] +
                b_raw["dist"] * b_weights["distress_reduction"] +
                b_raw["resil"] * b_weights["resilience_improvement"] +
                b_raw["rec"] * b_weights["recovery_probability"]
            )
            # Weighted Harm Score
            h_score = (
                h_raw["debt"] * h_weights["new_debt"] +
                h_raw["int"] * h_weights["interest_increase"] +
                h_raw["emi"] * h_weights["EMI_increase"] +
                h_raw["buf_red"] * h_weights["cash_buffer_reduction"] +
                h_raw["press"] * h_weights["long_term_repayment_pressure"] +
                h_raw["loss"] * h_weights["asset_loss"]
            )

            b_rounded = round(b_score, 1)
            h_rounded = round(h_score, 1)
            score = round(b_rounded / max(1.0, h_rounded), 2)

            scored_items.append(LeastHarmInterventionScoredItem(
                intervention=code,
                title=title,
                description=desc,
                benefit_metrics=InterventionBenefitMetrics(
                    cashflow_improvement=round(b_raw["cf"], 1),
                    distress_reduction=round(b_raw["dist"], 1),
                    resilience_improvement=round(b_raw["resil"], 1),
                    recovery_probability=round(b_raw["rec"], 1),
                    total_benefit_score=b_rounded
                ),
                harm_metrics=InterventionHarmMetrics(
                    new_debt=round(h_raw["debt"], 1),
                    interest_increase=round(h_raw["int"], 1),
                    EMI_increase=round(h_raw["emi"], 1),
                    cash_buffer_reduction=round(h_raw["buf_red"], 1),
                    long_term_repayment_pressure=round(h_raw["press"], 1),
                    asset_loss=round(h_raw["loss"], 1),
                    total_harm_score=h_rounded
                ),
                intervention_score=score,
                benefits=ben_list,
                risks=risk_list,
                reason=reason_txt,
                confidence=conf,
                rank=1
            ))

        # Sort descending by intervention_score
        scored_items.sort(key=lambda x: x.intervention_score, reverse=True)
        for idx, item in enumerate(scored_items, start=1):
            item.rank = idx

        recommended = scored_items[0]

        return LeastHarmOptimizeResponse(
            customer_id=fre.customer_id,
            customer_name=fre.customer_name,
            ranked_interventions=scored_items,
            recommended_intervention=recommended,
            benefits=recommended.benefits,
            risks=recommended.risks,
            reason=(
                f"Selected '{recommended.title}' as the Least-Harm Intervention (Score: {recommended.intervention_score:.2f}). "
                f"It delivers high recovery benefit ({recommended.benefit_metrics.total_benefit_score:.1f}/100) with "
                f"negligible long-term debt drag ({recommended.harm_metrics.total_harm_score:.1f}/100 harm), "
                f"preserving credit solvency and preventing balance sheet distress."
            ),
            confidence=recommended.confidence
        )

