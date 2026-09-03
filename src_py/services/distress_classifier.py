"""
Distress Classification Engine Service.
Identifies the dominant distress type following strict banking decision rules:
- TEMPORARY_LIQUIDITY_GAP: Short-term projected cash shortage + stable underlying income + recoverable receivables
- INCOME_SHOCK: Significant decline in primary income/revenue source (>20% decline or sudden loss)
- DEBT_OVERLOAD: Debt service ratio is consuming unsustainable cash flow (DSR > 45%)
- EXPENSE_SHOCK: Sudden or sustained increase in operating or household expenditure (>25% spike)
- MIXED_DISTRESS: More than one category contributes materially
Enforces at least two empirical evidence items per classification output.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from src_py.models.distress_classification_schemas import (
    DistressDominantType, ClassificationEvidenceItem, DistressClassificationReport
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.financial_state_schemas import FinancialState


class DistressClassificationEngineService:

    @classmethod
    def classify_distress(
        cls,
        customer_id: str,
        fre: FinancialRealityObject,
        revenue_decline_pct: float = 0.0,
        expense_increase_pct: float = 0.0,
        declining_orders_pct: float = 0.0,
        has_upcoming_shortage: bool = False
    ) -> DistressClassificationReport:
        """
        Evaluates signals from Financial Reality Engine and operational indicators
        to diagnose the dominant distress type and provide structured evidence items.
        """
        dsr = fre.debt_service_ratio.value
        cash_days = fre.cash_buffer_days.value
        monthly_inc = max(1.0, fre.monthly_income.value)
        receivable_exp = fre.receivable_exposure.value
        total_debt = fre.total_outstanding_debt.value
        monthly_emi = fre.monthly_debt_service.value
        shortfall_date = fre.next_critical_collision_date

        scores: Dict[DistressDominantType, float] = {
            DistressDominantType.TEMPORARY_LIQUIDITY_GAP: 0.0,
            DistressDominantType.INCOME_SHOCK: 0.0,
            DistressDominantType.DEBT_OVERLOAD: 0.0,
            DistressDominantType.EXPENSE_SHOCK: 0.0
        }
        evidence_pool: Dict[DistressDominantType, List[ClassificationEvidenceItem]] = {
            DistressDominantType.TEMPORARY_LIQUIDITY_GAP: [],
            DistressDominantType.INCOME_SHOCK: [],
            DistressDominantType.DEBT_OVERLOAD: [],
            DistressDominantType.EXPENSE_SHOCK: []
        }

        # 1. Evaluate TEMPORARY_LIQUIDITY_GAP
        # Condition: Short-term cash shortage + stable underlying income + recoverable receivables
        has_short_term_deficit = (cash_days < 25 or shortfall_date is not None or has_upcoming_shortage)
        has_stable_income = (revenue_decline_pct < 15.0 and declining_orders_pct < 15.0)
        has_recoverable_receivables = (receivable_exp >= monthly_emi * 0.8)

        if has_short_term_deficit and has_stable_income and has_recoverable_receivables:
            scores[DistressDominantType.TEMPORARY_LIQUIDITY_GAP] += 40.0
            evidence_pool[DistressDominantType.TEMPORARY_LIQUIDITY_GAP].append(ClassificationEvidenceItem(
                metric_name="receivable_coverage",
                observed_value=f"₹{receivable_exp:,.0f}",
                benchmark_or_threshold=f">= ₹{monthly_emi:,.0f} (Monthly EMI)",
                significance="HIGH",
                description=f"Recoverable trade receivables of ₹{receivable_exp:,.0f} comfortably exceed upcoming debt obligations."
            ))
            evidence_pool[DistressDominantType.TEMPORARY_LIQUIDITY_GAP].append(ClassificationEvidenceItem(
                metric_name="stable_baseline_income",
                observed_value=f"₹{monthly_inc:,.0f}/mo (Decline: {revenue_decline_pct:.1f}%)",
                benchmark_or_threshold="< 15.0% Decline",
                significance="HIGH",
                description=f"Underlying operational revenue remains fundamentally intact at ₹{monthly_inc:,.0f} per month."
            ))
            if shortfall_date:
                evidence_pool[DistressDominantType.TEMPORARY_LIQUIDITY_GAP].append(ClassificationEvidenceItem(
                    metric_name="isolated_collision_date",
                    observed_value=shortfall_date.isoformat(),
                    benchmark_or_threshold="Pre-default timing mismatch",
                    significance="MEDIUM",
                    description="Deficit is localized around fixed debit dates prior to expected invoice collections."
                ))

        # 2. Evaluate INCOME_SHOCK
        # Condition: Significant decline in primary income/revenue source (> 20% decline or sharp order cancellation)
        if revenue_decline_pct >= 20.0 or declining_orders_pct >= 25.0:
            weight = 50.0 if revenue_decline_pct >= 30.0 else 35.0
            scores[DistressDominantType.INCOME_SHOCK] += weight
            evidence_pool[DistressDominantType.INCOME_SHOCK].append(ClassificationEvidenceItem(
                metric_name="revenue_decline_rate",
                observed_value=f"-{revenue_decline_pct:.1f}%",
                benchmark_or_threshold=">= 20.0% Significant Decline",
                significance="CRITICAL",
                description=f"Severe top-line business contraction of {revenue_decline_pct:.1f}% recorded over the tracking window."
            ))
            evidence_pool[DistressDominantType.INCOME_SHOCK].append(ClassificationEvidenceItem(
                metric_name="order_volume_drop",
                observed_value=f"-{declining_orders_pct:.1f}%",
                benchmark_or_threshold=">= 25.0% Demand Collapse",
                significance="HIGH",
                description=f"Commercial purchase order bookings dropped by {declining_orders_pct:.1f}%, indicating demand destruction."
            ))

        # 3. Evaluate DEBT_OVERLOAD
        # Condition: Debt service is consuming unsustainable cash flow (DSR > 45% or EMI > Free Cash Flow)
        if dsr >= 0.45 or (monthly_emi > (monthly_inc * 0.40)):
            weight = 55.0 if dsr >= 0.55 else 40.0
            scores[DistressDominantType.DEBT_OVERLOAD] += weight
            evidence_pool[DistressDominantType.DEBT_OVERLOAD].append(ClassificationEvidenceItem(
                metric_name="debt_service_ratio",
                observed_value=f"{dsr:.1%}",
                benchmark_or_threshold="<= 40.0% Prudent Banking Ceiling",
                significance="CRITICAL",
                description=f"Borrower's Debt Service Ratio of {dsr:.1%} significantly exceeds the 40% sustainable threshold."
            ))
            evidence_pool[DistressDominantType.DEBT_OVERLOAD].append(ClassificationEvidenceItem(
                metric_name="monthly_emi_burden",
                observed_value=f"₹{monthly_emi:,.0f}/mo",
                benchmark_or_threshold=f"< ₹{monthly_inc * 0.40:,.0f} (40% of Income)",
                significance="HIGH",
                description=f"Total debt service commitments consume ₹{monthly_emi:,.0f} of ₹{monthly_inc:,.0f} gross monthly revenues."
            ))

        # 4. Evaluate EXPENSE_SHOCK
        # Condition: Sudden or sustained increase in operating or household expenditure (> 25% spike)
        if expense_increase_pct >= 25.0:
            scores[DistressDominantType.EXPENSE_SHOCK] += 40.0
            evidence_pool[DistressDominantType.EXPENSE_SHOCK].append(ClassificationEvidenceItem(
                metric_name="expense_inflation_pct",
                observed_value=f"+{expense_increase_pct:.1f}%",
                benchmark_or_threshold=">= 25.0% Cost Spike",
                significance="CRITICAL",
                description=f"Operating expenses experienced an abnormal surge of {expense_increase_pct:.1f}%."
            ))
            evidence_pool[DistressDominantType.EXPENSE_SHOCK].append(ClassificationEvidenceItem(
                metric_name="fixed_overhead_runway",
                observed_value=f"₹{fre.monthly_expenses.value:,.0f}",
                benchmark_or_threshold=f"< ₹{monthly_inc * 0.70:,.0f}",
                significance="HIGH",
                description=f"Monthly non-debt outlays have expanded to ₹{fre.monthly_expenses.value:,.0f}, eroding net margin."
            ))

        # Check for multiple material contributors -> MIXED_DISTRESS
        material_types = [t for t, sc in scores.items() if sc >= 30.0]
        all_gathered_evidence: List[ClassificationEvidenceItem] = []

        if len(material_types) >= 2:
            primary_cat = DistressDominantType.MIXED_DISTRESS
            sorted_material = sorted(material_types, key=lambda t: scores[t], reverse=True)
            secondary_cat = sorted_material[0]
            
            # Combine top evidence from both material contributors
            for t in sorted_material[:2]:
                all_gathered_evidence.extend(evidence_pool[t])
            expected_dur = "3–6 months (Compound Structural & Operating Stress)"
            summary = (
                f"Classified as MIXED DISTRESS: Multi-factor strain detected across {sorted_material[0].value} "
                f"and {sorted_material[1].value}. Requires coordinated dual intervention."
            )
            conf = 0.91
        elif len(material_types) == 1:
            primary_cat = material_types[0]
            secondary_cat = None
            all_gathered_evidence = evidence_pool[primary_cat]
            conf = 0.94

            if primary_cat == DistressDominantType.TEMPORARY_LIQUIDITY_GAP:
                expected_dur = "14–30 days (Resolvable via TReDS/Receivables Acceleration)"
                summary = "Classified as TEMPORARY LIQUIDITY GAP: Operating revenue remains sound; deficit is driven by collection timing."
            elif primary_cat == DistressDominantType.INCOME_SHOCK:
                expected_dur = "3–6 months (Requires Business Opportunity Matching / Demand Recovery)"
                summary = "Classified as INCOME SHOCK: Significant contraction in top-line commercial sales."
            elif primary_cat == DistressDominantType.DEBT_OVERLOAD:
                expected_dur = "Structural / Indefinite (> 6 months without Tenure Extension or Restructuring)"
                summary = "Classified as DEBT OVERLOAD: Fixed debt service exceeds safe cash flow capacity."
            else:
                expected_dur = "1–3 months (Requires Operating Cost Rationalization)"
                summary = "Classified as EXPENSE SHOCK: Sudden spike in variable or operating overhead."
        else:
            # Fallback based on closest leading factor
            if dsr > 0.35:
                primary_cat = DistressDominantType.DEBT_OVERLOAD
                secondary_cat = None
                expected_dur = "3–6 months"
                all_gathered_evidence = [
                    ClassificationEvidenceItem(
                        metric_name="debt_service_ratio",
                        observed_value=f"{dsr:.1%}",
                        benchmark_or_threshold="35.0%",
                        significance="MEDIUM",
                        description=f"Elevated debt service ratio of {dsr:.1%} restricts free cash flow."
                    ),
                    ClassificationEvidenceItem(
                        metric_name="cash_buffer_days",
                        observed_value=f"{cash_days} days",
                        benchmark_or_threshold="21 days",
                        significance="MEDIUM",
                        description=f"Cash buffer of {cash_days} days provides tight operational margin."
                    )
                ]
                summary = "Classified as DEBT OVERLOAD: Baseline debt service absorbs substantial liquidity."
            else:
                primary_cat = DistressDominantType.TEMPORARY_LIQUIDITY_GAP
                secondary_cat = None
                expected_dur = "14–30 days"
                all_gathered_evidence = [
                    ClassificationEvidenceItem(
                        metric_name="cash_buffer_days",
                        observed_value=f"{cash_days} days",
                        benchmark_or_threshold="21 days",
                        significance="MEDIUM",
                        description=f"Current liquid cash covers {cash_days} days of operational burn."
                    ),
                    ClassificationEvidenceItem(
                        metric_name="receivable_exposure",
                        observed_value=f"₹{receivable_exp:,.0f}",
                        benchmark_or_threshold="Working capital baseline",
                        significance="MEDIUM",
                        description=f"Receivables of ₹{receivable_exp:,.0f} represent short-term liquidity potential."
                    )
                ]
                summary = "Classified as TEMPORARY LIQUIDITY GAP: Standard working capital timing difference."
            conf = 0.86

        # Acceptance Criteria: Every classification must contain at least two evidence items
        if len(all_gathered_evidence) < 2:
            all_gathered_evidence.append(ClassificationEvidenceItem(
                metric_name="cash_buffer_runway",
                observed_value=f"{cash_days} days",
                benchmark_or_threshold="21 days",
                significance="MEDIUM",
                description=f"Cash buffer of {cash_days} days observed across recent account history."
            ))

        return DistressClassificationReport(
            customer_id=customer_id,
            primary_category=primary_cat,
            secondary_category=secondary_cat,
            confidence=conf,
            evidence=all_gathered_evidence,
            expected_duration=expected_dur,
            classification_summary=summary
        )
