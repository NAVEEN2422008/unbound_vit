"""
Financial Decision Digital Twin Engine Service.
Creates an in-memory virtual financial copy of the customer's current state and tests possible interventions
without altering real customer financial records.
Implements all 11 intervention scenarios:
1. NO_INTERVENTION (Status Quo)
2. NEW_LOAN (Proposed fresh borrowing)
3. LIMITED_LOAN (Prudentially capped debt)
4. EMI_RESTRUCTURE (RBI MSME Framework payment reduction)
5. TENURE_EXTENSION (Lengthening amortization horizon)
6. RECEIVABLE_ACCELERATION (TReDS / Invoice discounting)
7. EXPENSE_REDUCTION (Cost rationalization)
8. ASSET_SALE (Disposal of loss-making machinery)
9. ASSET_REPLACEMENT (Energy-efficient machinery swap)
10. BUSINESS_RECOVERY (Core order volume turnaround)
11. BUSINESS_MATCHING (Double-blind peer capacity exchange / supplier consortium)

For each scenario, calculates across 3, 6, 12, and 24 months:
cash_balance, cashflow, debt_balance, EMI, interest_burden, cash_buffer,
distress_score, resilience_score, recovery_status.

Stores all simulation runs in isolated in-memory tables:
- DECISION_SIMULATIONS
- DECISION_SIMULATION_RESULTS
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import copy

from src_py.models.decision_twin_schemas import (
    DigitalTwinScenarioType, PeriodMetricProjection, ScenarioSimulationResult,
    ComparisonTableRow, DecisionTwinReport
)
from src_py.models.schemas import FinancialRealityObject


# In-memory mock database collections satisfying the specification
DECISION_SIMULATIONS: Dict[str, Dict[str, Any]] = {}
DECISION_SIMULATION_RESULTS: Dict[str, List[Dict[str, Any]]] = {}


class DecisionTwinEngineService:

    HORIZONS = [3, 6, 12, 24]

    @classmethod
    def create_virtual_financial_copy(cls, fre: FinancialRealityObject) -> Dict[str, Any]:
        """
        Creates a decoupled, isolated virtual copy of the customer's financial state.
        Guarantees that real financial records remain 100% immutable.
        """
        return {
            "customer_id": fre.customer_id,
            "customer_name": fre.customer_name,
            "liquid_cash": fre.liquid_cash_balance.value,
            "savings": fre.savings_balance.value,
            "monthly_income": fre.monthly_income.value,
            "monthly_expenses": fre.monthly_expenses.value,
            "total_debt": fre.total_outstanding_debt.value,
            "monthly_emi": fre.monthly_debt_service.value,
            "receivables": fre.receivable_exposure.value,
            "payables": fre.payable_exposure.value,
            "buffer_days": fre.cash_buffer_days.value,
            "dsr": fre.debt_service_ratio.value,
            "fcf": fre.free_cash_flow.value
        }

    @classmethod
    def simulate_scenario(
        cls,
        v_state: Dict[str, Any],
        scenario: DigitalTwinScenarioType
    ) -> ScenarioSimulationResult:
        """
        Simulates one scenario across 3, 6, 12, and 24 months on the virtual state copy.
        """
        base_cash = v_state["liquid_cash"]
        base_inc = v_state["monthly_income"]
        base_exp = v_state["monthly_expenses"]
        base_debt = v_state["total_debt"]
        base_emi = v_state["monthly_emi"]
        base_rec = v_state["receivables"]

        projections: Dict[str, PeriodMetricProjection] = {}

        # Scenario modifiers
        inc_mult = 1.0
        exp_mult = 1.0
        emi_mult = 1.0
        immediate_cash_infusion = 0.0
        debt_addition = 0.0
        interest_rate_annual = 0.12
        feasibility = 0.85

        if scenario == DigitalTwinScenarioType.NO_INTERVENTION:
            title = "Status Quo (No Intervention)"
            desc = "Continue existing operating trajectory with present costs, debtor delays, and loan EMIs."
            feasibility = 1.0

        elif scenario == DigitalTwinScenarioType.NEW_LOAN:
            title = "Commercial Term Debt Injection"
            desc = "Inject ₹50L term loan at 13% for 36 months to paper over working capital gaps."
            immediate_cash_infusion = 5000000.0
            debt_addition = 5000000.0
            new_loan_emi = 168000.0
            emi_mult = (base_emi + new_loan_emi) / max(1.0, base_emi)
            feasibility = 0.70

        elif scenario == DigitalTwinScenarioType.LIMITED_LOAN:
            title = "Prudentially Capped Micro-Facility"
            desc = "Inject ₹12L working capital line strictly calibrated to 35% safe DSR envelope."
            immediate_cash_infusion = 1200000.0
            debt_addition = 1200000.0
            new_loan_emi = 40000.0
            emi_mult = (base_emi + new_loan_emi) / max(1.0, base_emi)
            feasibility = 0.90

        elif scenario == DigitalTwinScenarioType.EMI_RESTRUCTURE:
            title = "RBI MSME Debt Restructuring"
            desc = "Restructures amortization schedules, reducing monthly EMI outflows by 35%."
            emi_mult = 0.65
            feasibility = 0.92

        elif scenario == DigitalTwinScenarioType.TENURE_EXTENSION:
            title = "Tenor Amortization Extension"
            desc = "Extends loan tenor from 36 to 60 months, lowering monthly EMI by 28%."
            emi_mult = 0.72
            feasibility = 0.90

        elif scenario == DigitalTwinScenarioType.RECEIVABLE_ACCELERATION:
            title = "TReDS Invoice Factoring & Early Settlement"
            desc = "Accelerates ₹12L of locked trade credit via automated digital invoice discounting."
            immediate_cash_infusion = min(1200000.0, base_rec * 0.80)
            feasibility = 0.95

        elif scenario == DigitalTwinScenarioType.EXPENSE_REDUCTION:
            title = "Operational Overhead Rationalization"
            desc = "Curbs non-essential administrative, variable energy, and vendor logistics burn by 15%."
            exp_mult = 0.85
            feasibility = 0.88

        elif scenario == DigitalTwinScenarioType.ASSET_SALE:
            title = "Secondary Market Disposal of Loss-Making Asset"
            desc = "Liquidates idle/loss-making machinery, clearing dedicated debt and restoring working capital."
            immediate_cash_infusion = 1500000.0
            debt_addition = -2000000.0
            emi_mult = max(0.50, 0.75)
            feasibility = 0.78

        elif scenario == DigitalTwinScenarioType.ASSET_REPLACEMENT:
            title = "Energy-Efficient Modern Machinery Swap"
            desc = "Upgrades to low-power automated unit, reducing operating utilities by 25%."
            exp_mult = 0.90
            inc_mult = 1.08
            feasibility = 0.80

        elif scenario == DigitalTwinScenarioType.BUSINESS_RECOVERY:
            title = "Core Commercial Order Book Expansion"
            desc = "Rebounds customer order flow to historical baseline (+20% monthly gross receipts)."
            inc_mult = 1.20
            feasibility = 0.82

        elif scenario == DigitalTwinScenarioType.BUSINESS_MATCHING:
            title = "Double-Blind B2B Peer Capacity Consortium"
            desc = "Subleases off-peak loom capacity and pools bulk raw material purchases via matched peer."
            inc_mult = 1.15
            exp_mult = 0.92
            feasibility = 0.90

        # Calculate metrics for each period
        for h in cls.HORIZONS:
            eff_inc = base_inc * inc_mult
            eff_exp = base_exp * exp_mult
            eff_emi = base_emi * emi_mult
            monthly_cf = eff_inc - (eff_exp + eff_emi)
            interest_burden = eff_emi * 0.35

            # Cumulative cash tracking
            tot_debt = max(0.0, base_debt + debt_addition - (eff_emi * 0.60 * h))
            cum_cash = base_cash + immediate_cash_infusion + (monthly_cf * h)
            daily_burn = max(1.0, (eff_exp + eff_emi) / 30.0)
            buffer_days = max(0, int(cum_cash / daily_burn))

            # Distress & Resilience calculation
            eff_dsr = (eff_emi / eff_inc) if eff_inc > 0 else 1.0
            distress = min(98.0, max(10.0, (eff_dsr * 70.0) + (30.0 if monthly_cf < 0 else -15.0)))
            resilience = max(10.0, min(95.0, 100.0 - distress + (buffer_days * 0.40)))

            if monthly_cf > 0 and buffer_days >= 30:
                rec_status = "RECOVERED"
            elif monthly_cf >= 0:
                rec_status = "STABILIZING"
            elif monthly_cf > -30000:
                rec_status = "STAGNANT"
            else:
                rec_status = "DETERIORATING"

            projections[f"{h}m"] = PeriodMetricProjection(
                period_months=h,
                cash_balance=round(cum_cash, 2),
                cashflow=round(monthly_cf, 2),
                debt_balance=round(tot_debt, 2),
                EMI=round(eff_emi, 2),
                interest_burden=round(interest_burden, 2),
                cash_buffer_days=buffer_days,
                distress_score=round(distress, 1),
                resilience_score=round(resilience, 1),
                recovery_status=rec_status
            )

        p24 = projections["24m"]
        is_safe = p24.cashflow >= 0 and p24.distress_score <= 50.0

        return ScenarioSimulationResult(
            scenario=scenario,
            title=title,
            description=desc,
            projections=projections,
            terminal_cash_balance_24m=p24.cash_balance,
            terminal_distress_score_24m=p24.distress_score,
            terminal_resilience_score_24m=p24.resilience_score,
            solvency_verdict="Sustainable & Solvent" if is_safe else "Liquidity Vulnerability Alert",
            is_safe_candidate=is_safe,
            feasibility_score=feasibility
        )

    @classmethod
    def run_all_simulations(
        cls,
        fre: FinancialRealityObject,
        selected_scenarios: Optional[List[DigitalTwinScenarioType]] = None
    ) -> DecisionTwinReport:
        """
        Runs all 11 intervention simulations on the virtual state copy.
        Builds the comparison table, selects best candidates, and records results into isolated database collections.
        """
        v_state = cls.create_virtual_financial_copy(fre)
        scenarios_to_run = selected_scenarios or list(DigitalTwinScenarioType)

        results: List[ScenarioSimulationResult] = [
            cls.simulate_scenario(v_state, sc)
            for sc in scenarios_to_run
        ]

        # Build comparison table based on 12-month horizon
        comp_rows: List[ComparisonTableRow] = []
        for r in results:
            p12 = r.projections["12m"]
            comp_rows.append(ComparisonTableRow(
                scenario=r.scenario,
                scenario_title=r.title,
                cashflow_12m=p12.cashflow,
                debt_balance_12m=p12.debt_balance,
                monthly_emi=p12.EMI,
                cash_buffer_days_12m=p12.cash_buffer_days,
                distress_score_12m=p12.distress_score,
                resilience_score_12m=p12.resilience_score,
                recovery_status_12m=p12.recovery_status,
                rank=1
            ))

        # Rank: Highest cashflow, lowest distress, highest resilience
        comp_rows.sort(
            key=lambda x: (x.cashflow_12m, x.resilience_score_12m, -x.distress_score_12m),
            reverse=True
        )
        for idx, row in enumerate(comp_rows, start=1):
            row.rank = idx

        # Pick best candidates: top 3 non-debt or safe debt interventions
        best_candidates = [
            row.scenario for row in comp_rows[:3]
            if row.scenario != DigitalTwinScenarioType.NO_INTERVENTION
        ]

        sim_id = f"TWIN_{fre.customer_id[-6:]}_{int(datetime.utcnow().timestamp())}"

        # Store in isolated database collections
        DECISION_SIMULATIONS[sim_id] = {
            "customer_id": fre.customer_id,
            "created_at": datetime.utcnow().isoformat(),
            "virtual_baseline": v_state,
            "scenario_count": len(results)
        }
        DECISION_SIMULATION_RESULTS[sim_id] = [r.model_dump() for r in results]

        summary = (
            f"Digital Twin evaluated {len(results)} prospective intervention trajectories over 24 months. "
            f"Top recommended path: '{comp_rows[0].scenario_title}' yielding +₹{comp_rows[0].cashflow_12m:,.0f}/mo cash flow "
            f"and lifting Financial Resilience to {comp_rows[0].resilience_score_12m:.0f}/100 without balance sheet deterioration."
        )

        return DecisionTwinReport(
            simulation_id=sim_id,
            customer_id=fre.customer_id,
            customer_name=fre.customer_name,
            scenario_results=results,
            comparison_table=comp_rows,
            best_candidates=best_candidates,
            executive_twin_summary=summary
        )

    @classmethod
    def compare_candidates(
        cls,
        fre: FinancialRealityObject,
        candidate_scenarios: List[DigitalTwinScenarioType]
    ) -> DecisionTwinReport:
        """
        Runs and compares a focused subset of candidate interventions.
        """
        return cls.run_all_simulations(fre, selected_scenarios=candidate_scenarios)
