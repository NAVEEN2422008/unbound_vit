"""
Pydantic schemas for the AI Financial Explanation Assistant.
Strict boundary: This assistant NEVER calculates financial metrics itself.
It ingests structured outputs from FRE, EDD, CIE, Twin, and LHO,
and structures non-hallucinatory, grounded explanations across the 8 core dimensions.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class ExplanationInputPayload(BaseModel):
    """Structured inputs ingested from the deterministic numerical engines."""
    customer_id: str
    customer_name: str
    archetype: str
    cluster_region: str
    industry: str
    
    # Financial Reality Engine (FRE) outputs
    liquid_cash: float
    monthly_income: float
    monthly_expenses: float
    monthly_debt_emi: float
    cash_buffer_days: int
    projected_shortfall_date: Optional[str] = None
    receivables_amount: float
    payables_amount: float
    
    # Distress Detection & Root-Cause (EDD / WHY) outputs
    distress_score: float
    classification: str
    primary_root_cause: str
    detailed_causes: List[str]
    
    # Context Intelligence Engine (CIE) outputs
    cluster_revenue_growth_pct: float
    borrower_revenue_growth_pct: float
    is_sector_wide_seasonal_effect: bool
    context_narrative: str
    
    # Decision Twin & Least-Harm Optimizer (LHO) outputs
    simulated_options: List[Dict[str, Any]]
    recommended_option_title: str
    recommended_option_description: str
    no_new_loan_veto_active: bool
    no_new_loan_veto_reason: Optional[str] = None
    
    # Data Quality & Confidence metrics
    overall_confidence_pct: float
    missing_information: List[str]
    supporting_facts: List[str]


class StructuredExplanationResponse(BaseModel):
    customer_id: str
    customer_name: str
    
    # 8 Core Questions Answered Strictly from Underlying Numerical Outputs
    what_is_happening: str
    why_is_it_happening: str
    supporting_evidence: List[str]
    what_could_happen_next: str
    options_simulated: List[Dict[str, Any]]
    why_recommended_intervention_selected: str
    confidence_level: Dict[str, Any]
    missing_information: List[str]
    
    # Cohesive Synthesis Paragraph
    synthesis_narrative: str
    zero_hallucination_guarantee: str = "Strictly bounded to deterministic telemetry outputs. Zero fabricated metrics."

    model_config = ConfigDict(from_attributes=True)
