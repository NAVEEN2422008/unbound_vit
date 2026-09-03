"""
Pydantic schemas and scoring models for Least-Harm Intervention Optimizer (LHO).
Evaluates 11 candidate interventions against multi-dimensional harm and benefit criteria,
enforces anti-predatory "No-New-Loan" guardrails, ranks options, and returns auditable evidence cards.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class CandidateIntervention(str, Enum):
    NO_ACTION = "NO_ACTION"
    SAVE_WAIT = "SAVE_WAIT"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    RECEIVABLE_COLLECTION = "RECEIVABLE_COLLECTION"
    EMI_RESTRUCTURING = "EMI_RESTRUCTURING"
    LOAN_TENURE_EXTENSION = "LOAN_TENURE_EXTENSION"
    REFINANCING = "REFINANCING"
    ASSET_SALE = "ASSET_SALE"
    ASSET_REPLACEMENT = "ASSET_REPLACEMENT"
    LIMITED_NEW_LOAN = "LIMITED_NEW_LOAN"
    BUSINESS_OPPORTUNITY = "BUSINESS_OPPORTUNITY"


class HarmDimensionBreakdown(BaseModel):
    debt_increase_penalty: float = Field(ge=0.0, le=100.0)
    interest_increase_penalty: float = Field(ge=0.0, le=100.0)
    repayment_burden_penalty: float = Field(ge=0.0, le=100.0)
    long_term_risk_penalty: float = Field(ge=0.0, le=100.0)
    total_harm_score: float = Field(ge=0.0, le=100.0)


class BenefitDimensionBreakdown(BaseModel):
    cashflow_improvement_score: float = Field(ge=0.0, le=100.0)
    resilience_improvement_score: float = Field(ge=0.0, le=100.0)
    distress_reduction_score: float = Field(ge=0.0, le=100.0)
    recovery_probability_score: float = Field(ge=0.0, le=100.0)
    total_benefit_score: float = Field(ge=0.0, le=100.0)


class ScoredIntervention(BaseModel):
    intervention: CandidateIntervention
    title: str
    description: str
    
    # 9 Quantitative Impact Indicators
    change_in_monthly_cashflow: float
    change_in_total_debt: float
    change_in_monthly_emi: float
    additional_interest_burden: float
    projected_distress_score: float = Field(ge=0.0, le=100.0)
    projected_financial_resilience: float = Field(ge=0.0, le=100.0)
    recovery_probability_pct: float = Field(ge=0.0, le=100.0)
    customer_burden_level: str  # LOW, MODERATE, HIGH, EXTREME
    long_term_sustainability_pct: float = Field(ge=0.0, le=100.0)
    
    # Scoring Breakdown
    harm_breakdown: HarmDimensionBreakdown
    benefit_breakdown: BenefitDimensionBreakdown
    net_least_harm_score: float  # Benefit Score - Harm Score (higher is safer/better)
    
    # Guardrail Compliance
    is_permissible_under_guardrail: bool
    guardrail_veto_reason: Optional[str] = None
    rank: int = 1


class LeastHarmOptimizationReport(BaseModel):
    customer_id: str
    customer_name: str
    archetype: str
    selected_intervention: ScoredIntervention
    ranked_interventions: List[ScoredIntervention]
    no_new_loan_guardrail_enforced: bool
    selection_rationale: List[str]
    confidence_percentage: float = Field(ge=0.0, le=100.0)
    supporting_evidence: List[str]
    transparent_scoring_formula: str

    model_config = ConfigDict(from_attributes=True)
