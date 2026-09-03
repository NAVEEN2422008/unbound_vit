"""
Banker Human Review and Automatic Escalation Service.
Manages:
1. Automatic Escalation Detection:
   - confidence is low
   - large credit request (> ₹25L)
   - asset sale recommendation
   - conflicting model outputs (e.g. Distress says critical but credit engine allows loan)
   - insufficient data (history < 6m or missing key fields)
   - unusual business conditions (divergence from cluster > 20%)
2. Assembling Review Screen Display encompassing:
   - Customer
   - Financial Reality
   - Distress
   - Confidence
   - Root Cause
   - Context
   - Assets
   - Receivables
   - Credit Affordability
   - Decision Twin
   - Recommended Intervention
3. Recording Actions:
   - APPROVE, REJECT, MODIFY, REQUEST_MORE_DATA, ESCALATE
4. Storing Immutable Audit Records:
   - review_id, customer_id, reviewer_id, decision, reason, notes, timestamp
   - Never silently overwriting model decisions; records human override alongside model state.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

from src_py.models.human_review_schemas import (
    HumanReviewAction, EscalationReason, EscalationStatus,
    BankerReviewScreenData, SubmitHumanReviewRequest, StoredHumanReviewRecord
)
from src_py.models.schemas import FinancialRealityObject
from src_py.models.confidence_schemas import ConfidenceEvaluationReport, ConfidenceLevel
from src_py.models.least_harm_schemas import LeastHarmOptimizationReport

# In-memory persistent storage of reviews for audit logging
BANKER_REVIEW_AUDIT_LEDGER: List[StoredHumanReviewRecord] = []


class BankerHumanReviewService:

    @classmethod
    def check_automatic_escalation(
        cls,
        confidence_report: ConfidenceEvaluationReport,
        credit_requested: float = 0.0,
        recommended_intervention_type: str = "NO_ACTION",
        dscr_deficit_with_high_resilience: bool = False,
        historical_months: int = 24,
        divergence_from_cluster_pct: float = 0.0
    ) -> EscalationStatus:
        """
        Evaluates the 6 mandatory automatic escalation triggers.
        """
        triggers: List[EscalationReason] = []

        # 1. Confidence is low
        if confidence_report.confidence_level == ConfidenceLevel.LOW or confidence_report.confidence_score < 50.0:
            triggers.append(EscalationReason.LOW_CONFIDENCE)

        # 2. Large credit request (> ₹25,00,000)
        if credit_requested >= 2500000.0:
            triggers.append(EscalationReason.LARGE_CREDIT_REQUEST)

        # 3. Asset sale recommendation
        if "ASSET_SALE" in recommended_intervention_type.upper():
            triggers.append(EscalationReason.ASSET_SALE_RECOMMENDED)

        # 4. Conflicting model outputs
        if dscr_deficit_with_high_resilience:
            triggers.append(EscalationReason.CONFLICTING_MODEL_OUTPUTS)

        # 5. Insufficient data
        if historical_months < 6 or confidence_report.dimension_scores.data_completeness_score < 50.0:
            triggers.append(EscalationReason.INSUFFICIENT_DATA)

        # 6. Unusual business conditions
        if abs(divergence_from_cluster_pct) >= 20.0:
            triggers.append(EscalationReason.UNUSUAL_BUSINESS_CONDITIONS)

        is_escalated = len(triggers) > 0
        notes = (
            f"Escalated to human supervisor under {len(triggers)} trigger(s): {', '.join([t.value for t in triggers])}."
            if is_escalated else "Automated straight-through recommendation within normal operating parameters."
        )

        return EscalationStatus(
            is_escalated=is_escalated,
            triggers=triggers,
            escalation_notes=notes
        )

    @classmethod
    def assemble_review_screen(
        cls,
        customer_info: Dict[str, Any],
        fre: FinancialRealityObject,
        distress_dict: Dict[str, Any],
        confidence_rep: ConfidenceEvaluationReport,
        root_cause_dict: Dict[str, Any],
        context_dict: Dict[str, Any],
        assets_list: List[Dict[str, Any]],
        receivables_dict: Dict[str, Any],
        credit_dict: Dict[str, Any],
        decision_twin_dict: Dict[str, Any],
        least_harm_rep: LeastHarmOptimizationReport,
        credit_requested: float = 0.0
    ) -> BankerReviewScreenData:
        """
        Assembles all 11 required analytical sections into the single comprehensive review screen.
        """
        interv_val = getattr(least_harm_rep.selected_intervention, 'intervention', None) or getattr(least_harm_rep.selected_intervention, 'intervention_type', 'NO_ACTION')
        rec_type = interv_val.value if hasattr(interv_val, 'value') else str(interv_val)

        escalation = cls.check_automatic_escalation(
            confidence_report=confidence_rep,
            credit_requested=credit_requested,
            recommended_intervention_type=rec_type,
            dscr_deficit_with_high_resilience=distress_dict.get("classification") == "SMA-2" and fre.debt_service_ratio.value > 1.5,
            historical_months=int(confidence_rep.dimension_scores.historical_coverage_score / 4.0),
            divergence_from_cluster_pct=context_dict.get("divergence_from_cluster_trend_pct", 0.0)
        )

        review_case_id = f"REV_CASE_{fre.customer_id[-6:]}_{int(datetime.utcnow().timestamp())}"

        return BankerReviewScreenData(
            review_case_id=review_case_id,
            customer=customer_info,
            financial_reality={
                "liquid_cash": fre.liquid_cash_balance.value,
                "monthly_income": fre.monthly_income.value,
                "monthly_expenses": fre.monthly_expenses.value,
                "monthly_debt_emi": fre.monthly_debt_service.value,
                "cash_buffer_days": fre.cash_buffer_days.value,
                "projected_collision_date": fre.next_critical_collision_date.isoformat() if fre.next_critical_collision_date else None,
                "receivable_exposure": fre.receivable_exposure.value,
                "payable_exposure": fre.payable_exposure.value
            },
            distress=distress_dict,
            confidence=confidence_rep.model_dump(),
            root_cause=root_cause_dict,
            context=context_dict,
            assets=assets_list,
            receivables=receivables_dict,
            credit_affordability=credit_dict,
            decision_twin=decision_twin_dict,
            recommended_intervention={
                "title": least_harm_rep.selected_intervention.title,
                "intervention_type": rec_type,
                "description": least_harm_rep.selected_intervention.description,
                "benefit_score": least_harm_rep.selected_intervention.benefit_breakdown.total_benefit_score,
                "harm_score": least_harm_rep.selected_intervention.harm_breakdown.total_harm_score,
                "recovery_probability": least_harm_rep.selected_intervention.recovery_probability_pct,
                "no_new_loan_guardrail_enforced": least_harm_rep.no_new_loan_guardrail_enforced
            },
            escalation_status=escalation
        )

    @classmethod
    def record_human_decision(
        cls,
        customer_id: str,
        reviewer_id: str,
        req: SubmitHumanReviewRequest,
        original_recommendation: str
    ) -> StoredHumanReviewRecord:
        """
        Appends the human decision to the audit ledger.
        NEVER silently overwrites model decisions. Preserves original recommendation.
        """
        review_id = f"REV_{customer_id[-6:]}_{int(datetime.utcnow().timestamp())}"
        now = datetime.utcnow()

        audit_payload = f"{review_id}:{customer_id}:{reviewer_id}:{req.decision.value}:{now.isoformat()}"
        audit_hash = f"SHA256_{hashlib.sha256(audit_payload.encode()).hexdigest()[:24]}"

        record = StoredHumanReviewRecord(
            review_id=review_id,
            customer_id=customer_id,
            reviewer_id=reviewer_id,
            decision=req.decision,
            reason=req.reason,
            notes=req.notes or "",
            modified_parameters=req.modified_parameters,
            original_model_recommendation=original_recommendation,
            timestamp=now,
            audit_hash=audit_hash
        )

        BANKER_REVIEW_AUDIT_LEDGER.append(record)
        return record

    @classmethod
    def get_review_history_for_customer(cls, customer_id: str) -> List[StoredHumanReviewRecord]:
        return [r for r in BANKER_REVIEW_AUDIT_LEDGER if r.customer_id == customer_id]
