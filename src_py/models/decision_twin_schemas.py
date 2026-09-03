"""
Pydantic v2 schemas for the Financial Decision Digital Twin Engine.
Creates an in-memory virtual financial copy of the customer's current state and tests possible interventions
without altering real customer financial records.
Scenarios:
- NO_INTERVENTION
- NEW_LOAN
- LIMITED_LOAN
- EMI_RESTRUCTURE
- TENURE_EXTENSION
- RECEIVABLE_ACCELERATION
- EXPENSE_REDUCTION
- ASSET_SALE
- ASSET_REPLACEMENT
- BUSINESS_RECOVERY
- BUSINESS_MATCHING
Simulation Horizons: 3 months, 6 months, 12 months, 24 months.
Metrics for each scenario & period:
- cash_balance
- cashflow
- debt_balance
- EMI
- interest_burden
- cash_buffer
- distress_score
- resilience_score
- recovery_status
Outputs:
- scenario_results[]
- comparison_table
- best_candidates[]
All simulations stored in isolated collections (decision_simulations, decision_simulation_results).
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DigitalTwinScenarioType(str, Enum):
    NO_INTERVENTION = "NO_INTERVENTION"
    NEW_LOAN = "NEW_LOAN"
    LIMITED_LOAN = "LIMITED_LOAN"
    EMI_RESTRUCTURE = "EMI_RESTRUCTURE"
    TENURE_EXTENSION = "TENURE_EXTENSION"
    RECEIVABLE_ACCELERATION = "RECEIVABLE_ACCELERATION"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    ASSET_SALE = "ASSET_SALE"
    ASSET_REPLACEMENT = "ASSET_REPLACEMENT"
    BUSINESS_RECOVERY = "BUSINESS_RECOVERY"
    BUSINESS_MATCHING = "BUSINESS_MATCHING"


class PeriodMetricProjection(BaseModel):
    period_months: int                 # 3, 6, 12, or 24
    cash_balance: float
    cashflow: float                    # Monthly net cash flow
    debt_balance: float
    EMI: float
    interest_burden: float
    cash_buffer_days: int
    distress_score: float = Field(ge=0.0, le=100.0)
    resilience_score: float = Field(ge=0.0, le=100.0)
    recovery_status: str               # "RECOVERED", "STABILIZING", "STAGNANT", "DETERIORATING"


class ScenarioSimulationResult(BaseModel):
    scenario: DigitalTwinScenarioType
    title: str
    description: str
    projections: Dict[str, PeriodMetricProjection]  # "3m", "6m", "12m", "24m"
    terminal_cash_balance_24m: float
    terminal_distress_score_24m: float
    terminal_resilience_score_24m: float
    solvency_verdict: str
    is_safe_candidate: bool
    feasibility_score: float = Field(ge=0.0, le=1.0)


class ComparisonTableRow(BaseModel):
    scenario: DigitalTwinScenarioType
    scenario_title: str
    cashflow_12m: float
    debt_balance_12m: float
    monthly_emi: float
    cash_buffer_days_12m: int
    distress_score_12m: float
    resilience_score_12m: float
    recovery_status_12m: str
    rank: int


class DecisionTwinReport(BaseModel):
    """
    Standard output of Financial Decision Digital Twin Engine.
    Exposes all 11 scenarios across 4 horizons, ranked comparison table, and best candidates.
    """
    simulation_id: str
    customer_id: str
    customer_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scenario_results: List[ScenarioSimulationResult]
    comparison_table: List[ComparisonTableRow]
    best_candidates: List[DigitalTwinScenarioType]
    executive_twin_summary: str
    data_isolation_notice: str = (
        "ISOLATED DIGITAL TWIN ENVIRONMENT: All scenarios were simulated on an ephemeral virtual copy. "
        "Real customer accounts, CIBIL/bureau ledgers, and live loan balances have NOT been modified."
    )

    model_config = ConfigDict(from_attributes=True)


class DecisionTwinSimulateRequest(BaseModel):
    customer_id: str
    selected_scenarios: Optional[List[DigitalTwinScenarioType]] = None
    override_loan_amount: Optional[float] = None
    override_expense_cut_pct: Optional[float] = None


class DecisionTwinCompareRequest(BaseModel):
    customer_id: str
    candidate_scenarios: List[DigitalTwinScenarioType]
