"""
Asset-Level Financial Intelligence Service & Decision Simulator.
Evaluates machine economics, calculates gross/net contributions with explicit provenance labeling,
classifies assets (HIGHLY_PRODUCTIVE to LOSS_MAKING), and projects 6, 12, 24-month impacts across 6 decision paths.
"""
from typing import List, Dict, Any, Optional
from src_py.models.asset_schemas import (
    AssetInput, AssetPerformanceProfile, AssetClassification,
    ProvenanceMetric, DataLabel, AssetDecisionType,
    DecisionSimulationResult, HorizonProjection, AssetComprehensiveDiagnostic,
    AssetHealthAnalysisReport, MultiScenarioSimulationReport
)


class AssetFinancialIntelligenceService:

    @classmethod
    def analyze_asset_health(cls, asset: AssetInput) -> AssetHealthAnalysisReport:
        """
        Analyzes individual business asset financial contribution:
        - gross_contribution = revenue_contribution - operating_cost
        - net_contribution = revenue_contribution - operating_cost - maintenance_cost - monthly_emi
        - classification into HIGHLY_PRODUCTIVE, PRODUCTIVE, MARGINAL, UNPRODUCTIVE, LOSS_MAKING
        - explicit data status (ACTUAL, USER_ENTERED, ESTIMATED)
        - financing_burden, utilization, trend, confidence.
        """
        profile = cls.evaluate_asset(asset)
        return AssetHealthAnalysisReport(
            asset_id=asset.asset_id,
            asset_name=asset.asset_name,
            asset_type=asset.asset_type,
            asset_health=profile.classification,
            gross_contribution=profile.gross_contribution.value,
            net_contribution=profile.net_cash_contribution.value,
            revenue_data_status=asset.revenue_data_label,
            financing_burden=profile.financing_burden_ratio,
            utilization=profile.utilization_rate_pct,
            trend=profile.contribution_trend,
            confidence=profile.net_cash_contribution.confidence,
            monthly_emi=asset.monthly_emi,
            monthly_revenue=asset.revenue_contribution,
            monthly_operating_cost=asset.operating_cost,
            monthly_maintenance_cost=asset.maintenance_cost,
            interpretive_rationale=profile.distress_impact_assessment
        )

    @classmethod
    def evaluate_asset(cls, asset: AssetInput) -> AssetPerformanceProfile:
        """
        Calculates Gross Contribution and Net Cash Contribution,
        evaluates financing burden, utilization, and classifies the asset.
        """
        # Gross Contribution = Revenue - Operating Cost
        gross_contrib = asset.revenue_contribution - asset.operating_cost
        
        # Net Cash Contribution = Revenue - Operating Cost - Maintenance Cost - Financing EMI
        total_costs = asset.operating_cost + asset.maintenance_cost + asset.monthly_emi
        net_contrib = asset.revenue_contribution - total_costs

        # Profitability & Burden Ratios
        profit_margin = (net_contrib / asset.revenue_contribution) if asset.revenue_contribution > 0 else -1.0
        financing_burden = (asset.monthly_emi / asset.revenue_contribution) if asset.revenue_contribution > 0 else 1.0
        efficiency_ratio = (asset.revenue_contribution / total_costs) if total_costs > 0 else 1.0

        # Classification Logic
        classification = AssetClassification.PRODUCTIVE
        distress_impact = "Neutral/Positive contributor to operating liquidity."
        recommendation = "Maintain current utilization and preventative maintenance schedule."
        trend = "STABLE"

        if net_contrib < 0:
            classification = AssetClassification.LOSS_MAKING
            distress_impact = (
                f"Negative net cash drain of -₹{abs(net_contrib):,.0f}/month directly depletes enterprise working capital "
                f"and precipitates obligation collision."
            )
            recommendation = "Immediate intervention required: Restructure debt, sublease idle capacity, or execute planned disposal."
            trend = "DETERIORATING"
        elif profit_margin < 0.08 or asset.utilization_percentage < 45.0:
            classification = AssetClassification.UNPRODUCTIVE if asset.utilization_percentage < 40.0 else AssetClassification.MARGINAL
            distress_impact = "Marginal economic yield creates vulnerability under minor energy or input cost inflation."
            recommendation = "Optimize batch scheduling or source incremental commercial orders to raise utilization above 70%."
            trend = "MARGINAL"
        elif profit_margin >= 0.25 and asset.utilization_percentage >= 75.0:
            classification = AssetClassification.HIGHLY_PRODUCTIVE
            distress_impact = "Core cash generator subsidizing debt service across enterprise balance sheet."
            recommendation = "Asset operates at benchmark efficiency. Protect production uptime."
            trend = "IMPROVING"

        confidence = 0.95 if asset.revenue_data_label == DataLabel.ACTUAL else (0.80 if asset.revenue_data_label == DataLabel.USER_ENTERED else 0.60)

        return AssetPerformanceProfile(
            asset_id=asset.asset_id,
            asset_name=asset.asset_name,
            asset_type=asset.asset_type,
            classification=classification,
            gross_contribution=ProvenanceMetric(
                value=round(gross_contrib, 2),
                label=asset.revenue_data_label,
                confidence=confidence
            ),
            net_cash_contribution=ProvenanceMetric(
                value=round(net_contrib, 2),
                label=asset.revenue_data_label,
                confidence=confidence
            ),
            profitability_margin_pct=round(profit_margin * 100.0, 2),
            financing_burden_ratio=round(financing_burden, 3),
            utilization_rate_pct=round(asset.utilization_percentage, 1),
            efficiency_ratio=round(efficiency_ratio, 2),
            contribution_trend=trend,
            distress_impact_assessment=distress_impact,
            actionable_recommendation=recommendation
        )

    @classmethod
    def simulate_decision_path(
        cls,
        asset: AssetInput,
        decision: AssetDecisionType
    ) -> DecisionSimulationResult:
        """
        Simulates 6, 12, and 24 month projections for a specific strategic decision path.
        """
        horizons = [6, 12, 24]
        projections: Dict[str, HorizonProjection] = {}
        feasibility = 0.85
        risk = "Standard operational risk."
        title = ""
        description = ""
        rationale = ""

        # Baseline monthly figures
        base_rev = asset.revenue_contribution
        base_op = asset.operating_cost
        base_maint = asset.maintenance_cost
        base_emi = asset.monthly_emi
        base_loan = asset.outstanding_loan

        if decision == AssetDecisionType.KEEP:
            title = "1. Maintain Current Status Quo (Keep Asset)"
            description = f"Continues operating at {asset.utilization_percentage:.0f}% utilization with existing EMI of ₹{base_emi:,.0f}/mo."
            risk = "Ongoing cash bleed if asset is loss-making; risks total working capital depletion."
            monthly_net = base_rev - (base_op + base_maint + base_emi)
            monthly_prof = base_rev - (base_op + base_maint)
            fin_cost = base_emi * 0.35
            rationale = (
                f"Status quo yields monthly net cash flow of ₹{monthly_net:,.0f}. "
                f"{'Creates severe liquidity strain over 24 months.' if monthly_net < 0 else 'Maintains positive operating buffer.'}"
            )
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(base_loan, (base_emi * 0.70) * h)
                rem_loan = max(0.0, base_loan - debt_paid)
                liq = max(10000.0, 50000.0 + (monthly_net * h * 0.5))
                resil = max(20.0, min(90.0, 60.0 + (monthly_net / 10000.0)))
                distress = min(95.0, max(15.0, 45.0 - (monthly_net / 8000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(base_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Cash-Bleed Accelerating" if cum_flow < 0 else "Solvent Operations"
                )

        elif decision == AssetDecisionType.RESTRUCTURE_FINANCING:
            title = "2. Term Loan Tenor Extension (RBI MSME Framework)"
            new_emi = base_emi * 0.65
            monthly_net = base_rev - (base_op + base_maint + new_emi)
            monthly_prof = base_rev - (base_op + base_maint)
            fin_cost = new_emi * 0.40
            description = f"Restructures debt over extended term, lowering monthly EMI from ₹{base_emi:,.0f} to ₹{new_emi:,.0f} (-35%)."
            risk = "Higher cumulative interest burden over extended amortization cycle."
            feasibility = 0.90
            rationale = f"Immediately restores ₹{base_emi - new_emi:,.0f}/month into operating cash flow without requiring asset disposal."
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(base_loan, (new_emi * 0.60) * h)
                rem_loan = max(0.0, base_loan - debt_paid)
                liq = max(20000.0, 50000.0 + (monthly_net * h * 0.6))
                resil = max(25.0, min(90.0, 68.0 + (monthly_net / 10000.0)))
                distress = min(85.0, max(15.0, 35.0 - (monthly_net / 10000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(new_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Cash Flow Stabilized"
                )

        elif decision == AssetDecisionType.REFINANCE:
            title = "3. Asset Refinancing at Lower Interest Margin"
            new_emi = base_emi * 0.82
            monthly_net = base_rev - (base_op + base_maint + new_emi)
            monthly_prof = base_rev - (base_op + base_maint)
            fin_cost = new_emi * 0.28
            description = f"Replaces high-cost NBFC debt with Scheduled Commercial Bank priority-sector MSME facility at reduced interest."
            risk = "Requires clear title, CIBIL verification, and 30-day processing window."
            feasibility = 0.78
            rationale = f"Reduces debt service burden by ₹{base_emi - new_emi:,.0f}/month with lower overall interest rate."
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(base_loan, (new_emi * 0.75) * h)
                rem_loan = max(0.0, base_loan - debt_paid)
                liq = max(25000.0, 50000.0 + (monthly_net * h * 0.65))
                resil = max(30.0, min(92.0, 72.0 + (monthly_net / 10000.0)))
                distress = min(80.0, max(12.0, 30.0 - (monthly_net / 12000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(new_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Interest Burden Optimized"
                )

        elif decision == AssetDecisionType.SELL:
            title = "4. Secondary Market Asset Disposal & Debt Payoff"
            depreciation_factor = max(0.30, 1.0 - (asset.age_years / max(1.0, (asset.age_years + asset.remaining_useful_life_years))))
            market_salvage_value = asset.purchase_price * depreciation_factor
            net_liquidity_realized = market_salvage_value - base_loan
            description = (
                f"Sells machinery on industrial exchange for ~₹{market_salvage_value:,.0f}, "
                f"clearing entire ₹{base_loan:,.0f} outstanding term loan and eliminating all dedicated monthly costs."
            )
            risk = "Irreversible loss of capacity; 60–90 day secondary market liquidation time."
            feasibility = 0.75 if net_liquidity_realized >= 0 else 0.45
            rationale = (
                f"Permanently eliminates operating bleed (-₹{base_op + base_maint + base_emi:,.0f}/mo) "
                f"and yields net cash surplus of ₹{max(0.0, net_liquidity_realized):,.0f}."
            )
            for h in horizons:
                cum_flow = max(0.0, net_liquidity_realized)
                liq = max(40000.0, 50000.0 + max(0.0, net_liquidity_realized))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=0.0,
                    monthly_profit=0.0,
                    debt=0.0,
                    EMI=0.0,
                    financing_cost=0.0,
                    liquidity=round(liq, 2),
                    resilience_score=65.0,
                    distress_score=25.0,
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(base_loan, 2),
                    remaining_loan_balance=0.0,
                    projected_solvency_impact="Debt Obligation Extinguished"
                )

        elif decision == AssetDecisionType.REPLACE:
            title = "5. Replacement with Energy-Efficient Modular Alternative"
            new_purchase_cost = asset.purchase_price * 0.85
            new_op = base_op * 0.55
            new_emi = (new_purchase_cost / 48) * 1.10
            monthly_net = base_rev - (new_op + (base_maint * 0.40) + new_emi)
            monthly_prof = base_rev - (new_op + (base_maint * 0.40))
            fin_cost = new_emi * 0.30
            description = "Trades in older unit for high-efficiency modern line with 45% lower operational power overhead."
            risk = "Requires capital outlay and installation downtime."
            feasibility = 0.65
            rationale = f"Operating cost drops by ₹{base_op - new_op:,.0f}/month, improving unit gross margin."
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(new_purchase_cost, (new_emi * 0.70) * h)
                rem_loan = max(0.0, new_purchase_cost - debt_paid)
                liq = max(20000.0, 50000.0 + (monthly_net * h * 0.5))
                resil = max(35.0, min(95.0, 75.0 + (monthly_net / 10000.0)))
                distress = min(75.0, max(10.0, 28.0 - (monthly_net / 12000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(new_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Operational Margin Re-engineered"
                )

        elif decision == AssetDecisionType.PAUSE:
            title = "6. Temporary Operational Layoff / Mothballing (Pause)"
            monthly_net = -(base_emi + (base_maint * 0.20))
            monthly_prof = -(base_maint * 0.20)
            fin_cost = base_emi * 0.35
            description = "Temporarily halts machine production to eliminate variable utility and raw material burn while preserving capital."
            risk = "Ongoing debt service persists while zero operating revenue is generated."
            feasibility = 0.82
            rationale = f"Stops active operating losses (-₹{base_op:,.0f}/mo), restricting outflow strictly to EMI of ₹{base_emi:,.0f}/mo."
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(base_loan, (base_emi * 0.70) * h)
                rem_loan = max(0.0, base_loan - debt_paid)
                liq = max(5000.0, 50000.0 + (monthly_net * h))
                resil = max(20.0, min(60.0, 40.0 + (monthly_net / 15000.0)))
                distress = min(90.0, max(30.0, 60.0 - (monthly_net / 10000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(base_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Variable Burn Arrested"
                )

        elif decision == AssetDecisionType.INCREASE_UTILIZATION:
            title = "7. B2B Capacity Subleasing & Incremental Order Channel"
            scaling = 80.0 / max(10.0, asset.utilization_percentage)
            new_rev = base_rev * scaling * 1.20
            new_op = base_op * (1.0 + ((scaling - 1.0) * 0.35))
            monthly_net = new_rev - (new_op + (base_maint * 1.10) + base_emi)
            monthly_prof = new_rev - (new_op + (base_maint * 1.10))
            fin_cost = base_emi * 0.30
            description = f"Secures off-peak corporate contract manufacturing (e.g. ONDC B2B network) raising utilization from {asset.utilization_percentage:.0f}% to 80%."
            risk = "Contract counterparty risk and strict SLA compliance."
            feasibility = 0.88
            rationale = f"Converts idle capacity into revenue, swinging net contribution to +₹{monthly_net:,.0f}/month without altering capital structure."
            for h in horizons:
                cum_flow = monthly_net * h
                debt_paid = min(base_loan, (base_emi * 0.70) * h)
                rem_loan = max(0.0, base_loan - debt_paid)
                liq = max(30000.0, 50000.0 + (monthly_net * h * 0.70))
                resil = max(40.0, min(95.0, 80.0 + (monthly_net / 10000.0)))
                distress = min(60.0, max(10.0, 20.0 - (monthly_net / 15000.0)))
                projections[f"{h}m"] = HorizonProjection(
                    horizon_months=h,
                    monthly_cashflow=round(monthly_net, 2),
                    monthly_profit=round(monthly_prof, 2),
                    debt=round(rem_loan, 2),
                    EMI=round(base_emi, 2),
                    financing_cost=round(fin_cost, 2),
                    liquidity=round(liq, 2),
                    resilience_score=round(resil, 1),
                    distress_score=round(distress, 1),
                    cumulative_net_cash_flow=round(cum_flow, 2),
                    total_debt_paid=round(debt_paid, 2),
                    remaining_loan_balance=round(rem_loan, 2),
                    projected_solvency_impact="Positive Cash Influx"
                )

        return DecisionSimulationResult(
            decision=decision,
            title=title,
            description=description,
            projections=projections,
            feasibility_score=feasibility,
            primary_risk=risk,
            explainable_rationale=rationale
        )

    @classmethod
    def diagnose_asset_holistic(
        cls,
        customer_id: str,
        asset: AssetInput
    ) -> AssetComprehensiveDiagnostic:
        """
        Runs comprehensive evaluation and all 6 decision path simulations,
        and selects the optimal Least-Harm decision.
        """
        perf = cls.evaluate_asset(asset)
        
        simulations = [
            cls.simulate_decision_path(asset, d)
            for d in [
                AssetDecisionType.KEEP,
                AssetDecisionType.RESTRUCTURE_FINANCING,
                AssetDecisionType.REFINANCE,
                AssetDecisionType.SELL,
                AssetDecisionType.REPLACE,
                AssetDecisionType.INCREASE_UTILIZATION
            ]
        ]

        # Determine Recommended Decision
        if perf.classification == AssetClassification.LOSS_MAKING:
            # If asset is severely underutilized (<40%), Recommend B2B capacity expansion or debt restructuring
            if asset.utilization_percentage < 40.0:
                recommended = AssetDecisionType.RESTRUCTURE_FINANCING
                summary = (
                    f"Asset '{asset.asset_name}' is currently LOSS_MAKING (-₹{abs(perf.net_cash_contribution.value):,.0f}/mo) "
                    f"due to low capacity utilization ({asset.utilization_percentage:.0f}%) coupled with heavy dedicated EMI (₹{asset.monthly_emi:,.0f}). "
                    f"Recommended Action: Restructure machinery term loan tenor to immediately save 35% on debt outflows, "
                    f"concurrent with B2B capacity job-working to lift revenue above break-even."
                )
            else:
                recommended = AssetDecisionType.RESTRUCTURE_FINANCING
                summary = (
                    f"Asset '{asset.asset_name}' suffers from elevated financing burden ({perf.financing_burden_ratio:.1%}). "
                    f"Recommended Action: Restructure debt amortization under RBI MSME Framework to restore positive cash yields."
                )
        elif perf.classification in [AssetClassification.MARGINAL, AssetClassification.UNPRODUCTIVE]:
            recommended = AssetDecisionType.INCREASE_UTILIZATION
            summary = (
                f"Asset '{asset.asset_name}' is viable but operating at suboptimal utilization ({asset.utilization_percentage:.0f}%). "
                f"Recommended Action: Scale production orders to 80% to maximize operating leverage."
            )
        else:
            recommended = AssetDecisionType.KEEP
            summary = (
                f"Asset '{asset.asset_name}' is PRODUCTIVE with net positive cash yield (+₹{perf.net_cash_contribution.value:,.0f}/mo). "
                f"Recommended Action: Maintain operational status quo."
            )

        return AssetComprehensiveDiagnostic(
            customer_id=customer_id,
            asset_profile=perf,
            simulated_decisions=simulations,
            recommended_decision=recommended,
            executive_recommendation_summary=summary
        )

    @classmethod
    def simulate_all_scenarios(
        cls,
        asset: AssetInput,
        business_id: str
    ) -> MultiScenarioSimulationReport:
        """
        Simulates all 7 forward strategic paths (KEEP, RESTRUCTURE_FINANCING, REFINANCE, SELL, REPLACE, PAUSE, INCREASE_UTILIZATION)
        across 6, 12, and 24 month horizons.
        Enforces rule: This module only simulates and compares. It never automatically sells an asset.
        """
        scenarios = [
            cls.simulate_decision_path(asset, d)
            for d in [
                AssetDecisionType.KEEP,
                AssetDecisionType.RESTRUCTURE_FINANCING,
                AssetDecisionType.REFINANCE,
                AssetDecisionType.SELL,
                AssetDecisionType.REPLACE,
                AssetDecisionType.PAUSE,
                AssetDecisionType.INCREASE_UTILIZATION
            ]
        ]
        perf = cls.evaluate_asset(asset)
        if perf.classification == AssetClassification.LOSS_MAKING:
            recommended = AssetDecisionType.RESTRUCTURE_FINANCING if asset.utilization_percentage < 40.0 else AssetDecisionType.REFINANCE
        elif perf.classification in [AssetClassification.MARGINAL, AssetClassification.UNPRODUCTIVE]:
            recommended = AssetDecisionType.INCREASE_UTILIZATION
        else:
            recommended = AssetDecisionType.KEEP

        return MultiScenarioSimulationReport(
            asset_id=asset.asset_id,
            asset_name=asset.asset_name,
            business_id=business_id,
            scenarios=scenarios,
            recommended_scenario=recommended
        )
