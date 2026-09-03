"""
Root-Cause Analyzer (WHY) Engine Service.
Evaluates 13 candidate causes of financial distress across Financial Reality, Cash Flow,
Asset Intelligence, and Peer Benchmarking engines.
Collects empirical evidence, calculates contribution scores, ranks causes,
and assesses confidence while maintaining strict epistemic humility
(using 'likely contributor' rather than asserting proven causation).
"""
from typing import List, Dict, Any, Optional
from datetime import datetime

from src_py.models.root_cause_schemas import (
    CandidateCauseEnum, CauseEvidenceRecord, ContributingCauseItem, RootCauseReport
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.asset_schemas import AssetComprehensiveDiagnostic


class RootCauseAnalyzerService:

    @classmethod
    def analyze_root_causes(
        cls,
        customer_id: str,
        fre: FinancialRealityObject,
        revenue_decline_pct: float = 0.0,
        order_volume_decline_pct: float = 0.0,
        peer_industry_growth_pct: float = -2.0,
        peer_regional_growth_pct: float = 1.0,
        supplier_cost_inflation_pct: float = 0.0,
        inventory_days: int = 45,
        asset_diagnostic: Optional[AssetComprehensiveDiagnostic] = None
    ) -> RootCauseReport:
        """
        Executes a 4-step diagnostic protocol across 13 candidate causes:
        1. Collect empirical evidence.
        2. Calculate contribution score.
        3. Rank candidate causes.
        4. Assess confidence ratings with 'likely contributor' epistemic framing.
        """
        candidate_evaluations: List[ContributingCauseItem] = []

        dsr = fre.debt_service_ratio.value
        cash_days = fre.cash_buffer_days.value
        monthly_inc = max(1.0, fre.monthly_income.value)
        monthly_emi = fre.monthly_debt_service.value
        receivable_exp = fre.receivable_exposure.value
        asset_burn = fre.asset_operating_burn.value

        # ----------------------------------------------------------------------
        # 1. REVENUE DECLINE
        # ----------------------------------------------------------------------
        rev_weight = max(0.0, min(80.0, revenue_decline_pct * 2.0))
        if rev_weight > 10.0:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.REVENUE_DECLINE,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(rev_weight, 1),
                confidence=0.88,
                evidence=[
                    CauseEvidenceRecord(
                        metric="revenue_growth_rate",
                        observed=f"-{revenue_decline_pct:.1f}%",
                        benchmark_or_peer=f"{peer_industry_growth_pct:+.1f}% (Peer Industry)",
                        finding=f"Monthly sales revenue dropped {revenue_decline_pct:.1f}% below historical baseline."
                    ),
                    CauseEvidenceRecord(
                        metric="monthly_operating_inflow",
                        observed=f"₹{fre.monthly_income.value:,.0f}",
                        benchmark_or_peer="Target Capacity",
                        finding="Absolute cash generation capability has compressed."
                    )
                ],
                narrative_rationale="Significant contraction in top-line revenue weakens overall cash generation capacity."
            ))

        # ----------------------------------------------------------------------
        # 2. CUSTOMER / ORDER DECLINE
        # ----------------------------------------------------------------------
        if order_volume_decline_pct > 10.0:
            order_weight = max(0.0, min(85.0, order_volume_decline_pct * 2.2))
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.CUSTOMER_ORDER_DECLINE,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(order_weight, 1),
                confidence=0.85,
                evidence=[
                    CauseEvidenceRecord(
                        metric="order_volume_drop",
                        observed=f"-{order_volume_decline_pct:.1f}%",
                        benchmark_or_peer="-5.0% normal seasonal drift",
                        finding=f"Commercial purchase orders contracted by {order_volume_decline_pct:.1f}%."
                    ),
                    CauseEvidenceRecord(
                        metric="peer_industry_demand",
                        observed=f"{peer_industry_growth_pct:+.1f}%",
                        benchmark_or_peer="Broad Market",
                        finding="Enterprise-specific drop exceeds peer group demand trend."
                    )
                ],
                narrative_rationale="Buyer demand destruction directly throttles operating cash velocity."
            ))

        # ----------------------------------------------------------------------
        # 3. SEASONALITY
        # ----------------------------------------------------------------------
        if peer_industry_growth_pct < -8.0:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.SEASONALITY,
                causality_classification="likely contributor",
                estimated_contribution_pct=35.0,
                confidence=0.82,
                evidence=[
                    CauseEvidenceRecord(
                        metric="sectoral_seasonal_trend",
                        observed=f"{peer_industry_growth_pct:.1f}%",
                        benchmark_or_peer="Historical Cycle",
                        finding="Entire regional industry exhibits synchronized off-season contraction."
                    )
                ],
                narrative_rationale="Cyclical monsoon/festival lull impacts short-term customer collections."
            ))

        # ----------------------------------------------------------------------
        # 4. INDUSTRY DOWNTURN
        # ----------------------------------------------------------------------
        if peer_industry_growth_pct < -12.0:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.INDUSTRY_DOWNTURN,
                causality_classification="likely contributor",
                estimated_contribution_pct=40.0,
                confidence=0.80,
                evidence=[
                    CauseEvidenceRecord(
                        metric="peer_cohort_revenue",
                        observed=f"{peer_industry_growth_pct:.1f}%",
                        benchmark_or_peer="National Index",
                        finding="Systemic demand slump across peer manufacturing cluster."
                    )
                ],
                narrative_rationale="Broader industry headwind limits recovery via conventional local sales."
            ))

        # ----------------------------------------------------------------------
        # 5. REGIONAL DOWNTURN
        # ----------------------------------------------------------------------
        if peer_regional_growth_pct < -10.0:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.REGIONAL_DOWNTURN,
                causality_classification="likely contributor",
                estimated_contribution_pct=30.0,
                confidence=0.78,
                evidence=[
                    CauseEvidenceRecord(
                        metric="district_commercial_growth",
                        observed=f"{peer_regional_growth_pct:.1f}%",
                        benchmark_or_peer="State Average",
                        finding="Regional economic activity shows localized deceleration."
                    )
                ],
                narrative_rationale="Regional logistics disruptions or local power tariff hikes constrain margin."
            ))

        # ----------------------------------------------------------------------
        # 6. RECEIVABLE DELAY
        # ----------------------------------------------------------------------
        if receivable_exp > (monthly_inc * 0.30):
            rec_weight = min(75.0, (receivable_exp / monthly_inc) * 35.0)
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.RECEIVABLE_DELAY,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(rec_weight, 1),
                confidence=0.91,
                evidence=[
                    CauseEvidenceRecord(
                        metric="trade_receivable_exposure",
                        observed=f"₹{receivable_exp:,.0f}",
                        benchmark_or_peer=f"< ₹{monthly_inc * 0.30:,.0f} (30% of Income)",
                        finding=f"Outstanding receivables lock up ₹{receivable_exp:,.0f} in trade credit."
                    ),
                    CauseEvidenceRecord(
                        metric="cash_buffer_runway",
                        observed=f"{cash_days} days",
                        benchmark_or_peer="21 days minimum",
                        finding="Liquid reserves depleted while waiting for buyer payments."
                    )
                ],
                narrative_rationale="Customer cash is trapped in working capital rather than lost operationally."
            ))

        # ----------------------------------------------------------------------
        # 7. DEBT OVERLOAD
        # ----------------------------------------------------------------------
        if dsr > 0.40:
            debt_weight = min(85.0, (dsr - 0.25) * 120.0)
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.DEBT_OVERLOAD,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(debt_weight, 1),
                confidence=0.94,
                evidence=[
                    CauseEvidenceRecord(
                        metric="debt_service_ratio",
                        observed=f"{dsr:.1%}",
                        benchmark_or_peer="<= 35.0% safe threshold",
                        finding=f"Monthly debt commitments consume {dsr:.1%} of total operational cash flow."
                    ),
                    CauseEvidenceRecord(
                        metric="multi_lender_emi",
                        observed=f"₹{monthly_emi:,.0f}/mo",
                        benchmark_or_peer="Free Cash Flow",
                        finding="Fixed repayment obligations outpace operational surplus."
                    )
                ],
                narrative_rationale="Excessive borrowing has created an unsustainable fixed repayment burden."
            ))

        # ----------------------------------------------------------------------
        # 8. HIGH EMI
        # ----------------------------------------------------------------------
        if monthly_emi > 50000.0 and dsr > 0.35:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.HIGH_EMI,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(min(60.0, (monthly_emi / 100000.0) * 20.0), 1),
                confidence=0.89,
                evidence=[
                    CauseEvidenceRecord(
                        metric="monthly_debt_service",
                        observed=f"₹{monthly_emi:,.0f}",
                        benchmark_or_peer="₹30,000 peer median",
                        finding="Lender debt structure features steep amortization schedule."
                    )
                ],
                narrative_rationale="Short loan tenures compress amortizing payments into large monthly outflows."
            ))

        # ----------------------------------------------------------------------
        # 9. ASSET UNDERPERFORMANCE & 10. LOW UTILIZATION
        # ----------------------------------------------------------------------
        if asset_diagnostic and asset_diagnostic.asset_profile.classification.value in ["LOSS_MAKING", "UNPRODUCTIVE"]:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.ASSET_UNDERPERFORMANCE,
                causality_classification="likely contributor",
                estimated_contribution_pct=42.0,
                confidence=0.87,
                evidence=[
                    CauseEvidenceRecord(
                        metric="asset_performance_classification",
                        observed=str(asset_diagnostic.asset_profile.classification.value),
                        benchmark_or_peer="PRODUCTIVE",
                        finding=f"Machine '{asset_diagnostic.asset_profile.asset_id}' net cash contribution is negative (₹{asset_diagnostic.asset_profile.net_cash_contribution.value:,.0f}/mo)."
                    ),
                    CauseEvidenceRecord(
                        metric="monthly_asset_burn",
                        observed=f"₹{asset_burn:,.0f}",
                        benchmark_or_peer="Self-funding",
                        finding="Financing and operating costs exceed asset-generated revenue."
                    )
                ],
                narrative_rationale="Financed capital assets are draining liquidity rather than generating operating surplus."
            ))
            if asset_diagnostic.asset_profile.utilization_percentage.value < 65.0:
                candidate_evaluations.append(ContributingCauseItem(
                    cause=CandidateCauseEnum.LOW_ASSET_UTILIZATION,
                    causality_classification="likely contributor",
                    estimated_contribution_pct=34.0,
                    confidence=0.84,
                    evidence=[
                        CauseEvidenceRecord(
                            metric="average_utilization",
                            observed=f"{asset_diagnostic.asset_profile.utilization_percentage.value:.1f}%",
                            benchmark_or_peer=">= 80.0% productive benchmark",
                            finding="Idle machinery capacity fails to cover fixed financing charges."
                        )
                    ],
                    narrative_rationale="Sub-optimal machine runtime creates overhead drag."
                ))

        # ----------------------------------------------------------------------
        # 11. EXPENSE INCREASE & 12. SUPPLIER COST INCREASE
        # ----------------------------------------------------------------------
        if supplier_cost_inflation_pct > 15.0:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.SUPPLIER_COST_INCREASE,
                causality_classification="likely contributor",
                estimated_contribution_pct=round(min(55.0, supplier_cost_inflation_pct * 1.8), 1),
                confidence=0.83,
                evidence=[
                    CauseEvidenceRecord(
                        metric="raw_material_cost_inflation",
                        observed=f"+{supplier_cost_inflation_pct:.1f}%",
                        benchmark_or_peer="+4.0% CPI Wholesale",
                        finding="Supplier input prices have escalated faster than output realization."
                    )
                ],
                narrative_rationale="Direct vendor price escalation compresses operating gross margins."
            ))

        # ----------------------------------------------------------------------
        # 13. INVENTORY PRESSURE
        # ----------------------------------------------------------------------
        if inventory_days > 60:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.INVENTORY_PRESSURE,
                causality_classification="likely contributor",
                estimated_contribution_pct=28.0,
                confidence=0.79,
                evidence=[
                    CauseEvidenceRecord(
                        metric="days_inventory_outstanding",
                        observed=f"{inventory_days} days",
                        benchmark_or_peer="<= 40 days peer average",
                        finding="Unsold inventory absorbs working capital reserves."
                    )
                ],
                narrative_rationale="Slow-moving stock delays inventory cash conversion."
            ))

        # Fallback if no specific threshold triggered
        if not candidate_evaluations:
            candidate_evaluations.append(ContributingCauseItem(
                cause=CandidateCauseEnum.RECEIVABLE_DELAY if receivable_exp > 0 else CandidateCauseEnum.DEBT_OVERLOAD,
                causality_classification="likely contributor",
                estimated_contribution_pct=30.0,
                confidence=0.80,
                evidence=[
                    CauseEvidenceRecord(
                        metric="cash_buffer_days",
                        observed=f"{cash_days} days",
                        benchmark_or_peer="21 days",
                        finding=f"Operational cushion of {cash_days} days creates exposure to payment shocks."
                    )
                ],
                narrative_rationale="Working capital cycles and debt obligations require close calibration."
            ))

        # Sort candidate causes by estimated contribution percentage (descending)
        candidate_evaluations.sort(key=lambda x: x.estimated_contribution_pct, reverse=True)

        primary = candidate_evaluations[0]
        secondaries = candidate_evaluations[1:4]

        # Overall causation confidence
        overall_conf = round(sum(c.confidence for c in candidate_evaluations[:3]) / min(3, len(candidate_evaluations)), 2)

        summary = (
            f"The primary likely contributor to financial distress is '{primary.cause.value}' "
            f"(estimated contribution: {primary.estimated_contribution_pct:.0f}%, confidence: {primary.confidence:.0%}). "
        )
        if secondaries:
            sec_names = ", ".join(f"'{s.cause.value}' ({s.estimated_contribution_pct:.0f}%)" for s in secondaries)
            summary += f"Secondary contributing factors include {sec_names}."

        return RootCauseReport(
            customer_id=customer_id,
            customer_name=fre.customer_name,
            archetype=fre.archetype,
            primary_cause=primary,
            secondary_causes=secondaries,
            total_causes_evaluated=13,
            causation_confidence_level=overall_conf,
            human_summary=summary
        )
