"""
Pydantic schemas and models for Asset-Level Financial Intelligence (ALE) and Asset Decision Simulator.
Defines asset attributes, data provenance (ACTUAL, USER_ENTERED, ESTIMATED), classification,
and 6, 12, 24-month forward projections across 6 strategic decision paths.
"""
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class DataLabel(str, Enum):
    ACTUAL = "ACTUAL"                  # Direct telemetry / IoT / job-card verified
    USER_ENTERED = "USER_ENTERED"      # Declared by MSME promoter in portal
    ESTIMATED = "ESTIMATED"            # Synthesized from cluster benchmarks & power bills


class AssetClassification(str, Enum):
    HIGHLY_PRODUCTIVE = "HIGHLY_PRODUCTIVE"  # Net contribution margin > 25%
    PRODUCTIVE = "PRODUCTIVE"                # Healthy positive net cash flow
    MARGINAL = "MARGINAL"                    # Barely covers operating & financing costs
    UNPRODUCTIVE = "UNPRODUCTIVE"            # Low utilization, near-zero or volatile return
    LOSS_MAKING = "LOSS_MAKING"              # Negative net cash contribution (cash drain)


class AssetDecisionType(str, Enum):
    KEEP = "KEEP"
    RESTRUCTURE_FINANCING = "RESTRUCTURE_FINANCING"
    REFINANCE = "REFINANCE"
    SELL = "SELL"
    REPLACE = "REPLACE"
    PAUSE = "PAUSE"
    INCREASE_UTILIZATION = "INCREASE_UTILIZATION"


class ProvenanceMetric(BaseModel):
    value: float
    label: DataLabel
    unit: str = "INR"
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class AssetInput(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str  # MACHINE, VEHICLE, EQUIPMENT, PRODUCTION_LINE
    purchase_price: float
    financing_amount: float
    outstanding_loan: float
    monthly_emi: float
    revenue_contribution: float
    operating_cost: float
    maintenance_cost: float
    utilization_percentage: float = Field(ge=0.0, le=100.0)
    age_years: float
    remaining_useful_life_years: float
    revenue_data_label: DataLabel = DataLabel.ACTUAL


class AssetType(str, Enum):
    MACHINE = "machine"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    PRODUCTION_LINE = "production_line"
    STORE = "store"
    OTHER_REVENUE_GENERATING_ASSET = "other_revenue_generating_asset"


class AssetHealthAnalysisReport(BaseModel):
    """
    Standard output of individual asset health and financial contribution analysis.
    Output: asset_health, net_contribution, financing_burden, utilization, trend, confidence.
    """
    asset_id: str
    asset_name: str
    asset_type: str
    asset_health: AssetClassification  # HIGHLY_PRODUCTIVE, PRODUCTIVE, MARGINAL, UNPRODUCTIVE, LOSS_MAKING
    gross_contribution: float
    net_contribution: float
    revenue_data_status: DataLabel  # ACTUAL, USER_ENTERED, ESTIMATED
    financing_burden: float  # monthly_emi / revenue_contribution
    utilization: float  # %
    trend: str  # STABLE, IMPROVING, DETERIORATING, MARGINAL
    confidence: float = Field(ge=0.0, le=1.0)
    monthly_emi: float
    monthly_revenue: float
    monthly_operating_cost: float
    monthly_maintenance_cost: float
    interpretive_rationale: str
    data_provenance_disclosure: str = (
        "Provenance transparency enforced: Estimated contributions are clearly marked as ESTIMATED "
        "and never represented as actual telemetry."
    )

    model_config = ConfigDict(from_attributes=True)


class AssetPerformanceProfile(BaseModel):
    asset_id: str
    asset_name: str
    asset_type: str
    classification: AssetClassification
    
    # Financial Contributions
    gross_contribution: ProvenanceMetric       # Revenue - Operating Cost
    net_cash_contribution: ProvenanceMetric   # Revenue - Operating - Maintenance - Financing EMI
    
    # Key Diagnostic Ratios
    profitability_margin_pct: float            # Net Contribution / Revenue
    financing_burden_ratio: float              # Monthly EMI / Revenue
    utilization_rate_pct: float
    efficiency_ratio: float                    # Revenue / Total Cost
    
    contribution_trend: str                    # STABLE, IMPROVING, DETERIORATING
    distress_impact_assessment: str            # Narrative of impact on borrower solvency
    actionable_recommendation: str             # Initial recommendation


class HorizonProjection(BaseModel):
    horizon_months: int  # 6, 12, 24
    monthly_cashflow: float
    monthly_profit: float
    debt: float
    EMI: float
    financing_cost: float
    liquidity: float
    resilience_score: float = Field(ge=0.0, le=100.0)
    distress_score: float = Field(ge=0.0, le=100.0)
    cumulative_net_cash_flow: float
    total_debt_paid: float
    remaining_loan_balance: float
    projected_solvency_impact: str


class DecisionSimulationResult(BaseModel):
    decision: AssetDecisionType
    title: str
    description: str
    projections: Dict[str, HorizonProjection]  # "6m", "12m", "24m"
    feasibility_score: float = Field(ge=0.0, le=1.0)
    primary_risk: str
    explainable_rationale: str


class MultiScenarioSimulationReport(BaseModel):
    """
    Standard output of Asset Decision Simulator.
    Simulates what may happen across KEEP, RESTRUCTURE_FINANCING, REFINANCE, SELL, REPLACE, PAUSE, INCREASE_UTILIZATION
    over 6, 12, and 24 month horizons.
    Adheres strictly to the institutional mandate: This module only simulates and compares;
    it must never automatically sell an asset.
    """
    asset_id: str
    asset_name: str
    business_id: str
    as_of_date: datetime = Field(default_factory=datetime.utcnow)
    scenarios: List[DecisionSimulationResult]
    recommended_scenario: AssetDecisionType
    simulation_disclaimer: str = (
        "Advisory Simulation Only: This platform generates forward scenario comparisons for human banking decision-support. "
        "It never automatically sells, liquidates, or repossesses an asset."
    )

    model_config = ConfigDict(from_attributes=True)


class AssetComprehensiveDiagnostic(BaseModel):
    customer_id: str
    asset_profile: AssetPerformanceProfile
    simulated_decisions: List[DecisionSimulationResult]
    recommended_decision: AssetDecisionType
    executive_recommendation_summary: str

    model_config = ConfigDict(from_attributes=True)
