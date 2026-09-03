"""
Pydantic schemas and scoring models for Least-Harm Intervention Optimizer (LHO).
Evaluates 11 candidate interventions against multi-dimensional harm and benefit criteria,
enforces anti-predatory "No-New-Loan" guardrails, ranks options, and returns auditable evidence cards.
"""
from enum import Enum
from typing import List, Dict, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class CandidateIntervention(str, Enum):
    NO_ACTION = "NO_ACTION"
    SAVE_WAIT = "SAVE_WAIT"
    EXPENSE_REDUCTION = "EXPENSE_REDUCTION"
    RECEIVABLE_ACCELERATION = "RECEIVABLE_ACCELERATION"
    RECEIVABLE_COLLECTION = "RECEIVABLE_COLLECTION"      # Alias for backward compatibility
    EMI_RESTRUCTURE = "EMI_RESTRUCTURE"
    EMI_RESTRUCTURING = "EMI_RESTRUCTURING"              # Alias for backward compatibility
    TENURE_EXTENSION = "TENURE_EXTENSION"
    LOAN_TENURE_EXTENSION = "LOAN_TENURE_EXTENSION"      # Alias for backward compatibility
    REFINANCE = "REFINANCE"
    REFINANCING = "REFINANCING"                          # Alias for backward compatibility
    ASSET_ACTION = "ASSET_ACTION"
    ASSET_SALE = "ASSET_SALE"                            # Sub-variant
    ASSET_REPLACEMENT = "ASSET_REPLACEMENT"              # Sub-variant
    LIMITED_CREDIT = "LIMITED_CREDIT"
    LIMITED_NEW_LOAN = "LIMITED_NEW_LOAN"                # Alias for backward compatibility
    BUSINESS_RECOVERY = "BUSINESS_RECOVERY"
    BUSINESS_MATCHING = "BUSINESS_MATCHING"
    BUSINESS_OPPORTUNITY = "BUSINESS_OPPORTUNITY"        # Alias for backward compatibility


class InterventionBenefitMetrics(BaseModel):
    cashflow_improvement: float = Field(ge=0.0, le=100.0)
    distress_reduction: float = Field(ge=0.0, le=100.0)
    resilience_improvement: float = Field(ge=0.0, le=100.0)
    recovery_probability: float = Field(ge=0.0, le=100.0)
    total_benefit_score: float = Field(ge=0.0, le=100.0)


class InterventionHarmMetrics(BaseModel):
    new_debt: float = Field(ge=0.0, le=100.0)
    interest_increase: float = Field(ge=0.0, le=100.0)
    EMI_increase: float = Field(ge=0.0, le=100.0)
    cash_buffer_reduction: float = Field(ge=0.0, le=100.0)
    long_term_repayment_pressure: float = Field(ge=0.0, le=100.0)
    asset_loss: float = Field(ge=0.0, le=100.0)
    total_harm_score: float = Field(ge=0.0, le=100.0)


class LeastHarmInterventionScoredItem(BaseModel):
    intervention: CandidateIntervention
    title: str
    description: str
    benefit_metrics: InterventionBenefitMetrics
    harm_metrics: InterventionHarmMetrics
    intervention_score: float = Field(description="benefit_score / max(1.0, harm_score)")
    benefits: List[str]
    risks: List[str]
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    rank: int = 1


class LeastHarmOptimizeRequest(BaseModel):
    customer_id: str
    benefit_weights: Optional[Dict[str, float]] = None  # cashflow_improvement, distress_reduction, etc.
    harm_weights: Optional[Dict[str, float]] = None     # new_debt, interest_increase, EMI_increase, etc.


class LeastHarmOptimizeResponse(BaseModel):
    customer_id: str
    customer_name: str
    ranked_interventions: List[LeastHarmInterventionScoredItem]
    recommended_intervention: LeastHarmInterventionScoredItem
    benefits: List[str]
    risks: List[str]
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)
    transparent_scoring_formula: str = (
        "intervention_score = benefit_score / max(1.0, harm_score); "
        "Weights are configurable. The objective is sustainable financial recovery, never optimizing purely for bank revenue."
    )
    as_of_timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(from_attributes=True)


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
