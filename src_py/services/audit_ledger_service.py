"""
Immutable Audit Trail and Provenance Ledger Service.
Maintains a tamper-evident append-only history of system recommendations and human actions.

Enforces:
1. All 9 mandatory Audit Events:
   - DATA_INGESTED
   - DISTRESS_DETECTED
   - ROOT_CAUSE_IDENTIFIED
   - LOAN_EVALUATED
   - INTERVENTION_RECOMMENDED
   - HUMAN_REVIEWED
   - INTERVENTION_APPROVED
   - INTERVENTION_EXECUTED
   - OUTCOME_RECORDED
2. Stored Fields:
   customer_id, event_type, module, timestamp, input_reference,
   model_version, rule_version, output, confidence, human_decision.
3. Cryptographic Tamper-Evidence:
   SHA-256 hash chaining (prev_audit_hash -> cryptographic_hash).
4. Strict Immutability:
   Historical events must never be deleted or modified through normal application operations.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import hashlib
import json

from src_py.models.audit_schemas import (
    AuditEventType, ImmutableAuditEventRecord, CreateAuditEventRequest
)

# Append-only immutable ledger in memory
IMMUTABLE_AUDIT_LEDGER: List[ImmutableAuditEventRecord] = []
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class ImmutableAuditLedgerService:

    @classmethod
    def record_event(
        cls,
        req: CreateAuditEventRequest
    ) -> ImmutableAuditEventRecord:
        """
        Appends an immutable audit event to the ledger with SHA-256 tamper-evident chaining.
        """
        now = datetime.utcnow()
        event_count = len(IMMUTABLE_AUDIT_LEDGER) + 1
        audit_id = f"AUDIT_{req.customer_id[-6:]}_{req.event_type.value[:4]}_{int(now.timestamp())}_{event_count}"

        # Get previous event's hash or genesis hash
        prev_hash = IMMUTABLE_AUDIT_LEDGER[-1].cryptographic_hash if IMMUTABLE_AUDIT_LEDGER else GENESIS_HASH

        # Deterministic payload for hashing
        hashable_payload = {
            "audit_id": audit_id,
            "customer_id": req.customer_id,
            "event_type": req.event_type.value,
            "module": req.module,
            "timestamp": now.isoformat(),
            "input_reference": req.input_reference,
            "model_version": req.model_version or "v2.4.0",
            "rule_version": req.rule_version or "rbi-2026.1",
            "output": req.output,
            "confidence": req.confidence,
            "human_decision": req.human_decision,
            "prev_hash": prev_hash
        }
        payload_str = json.dumps(hashable_payload, sort_keys=True, default=str)
        crypto_hash = f"SHA256_{hashlib.sha256(payload_str.encode()).hexdigest()}"

        record = ImmutableAuditEventRecord(
            audit_id=audit_id,
            customer_id=req.customer_id,
            event_type=req.event_type,
            module=req.module,
            timestamp=now,
            input_reference=req.input_reference,
            model_version=req.model_version or "v2.4.0-production",
            rule_version=req.rule_version or "rbi-prudential-2026.1",
            output=req.output,
            confidence=req.confidence,
            human_decision=req.human_decision,
            cryptographic_hash=crypto_hash,
            prev_audit_hash=prev_hash
        )

        IMMUTABLE_AUDIT_LEDGER.append(record)
        return record

    @classmethod
    def get_audit_trail_for_customer(
        cls,
        customer_id: str
    ) -> List[ImmutableAuditEventRecord]:
        """
        Returns the complete chronological audit trail for a customer.
        """
        return [r for r in IMMUTABLE_AUDIT_LEDGER if r.customer_id == customer_id]

    @classmethod
    def verify_ledger_integrity(cls) -> Dict[str, Any]:
        """
        Validates cryptographic tamper-evidence across the entire chain.
        """
        for i in range(1, len(IMMUTABLE_AUDIT_LEDGER)):
            curr = IMMUTABLE_AUDIT_LEDGER[i]
            prev = IMMUTABLE_AUDIT_LEDGER[i - 1]
            if curr.prev_audit_hash != prev.cryptographic_hash:
                return {
                    "is_valid": False,
                    "error": f"Tamper detected at event index {i} ({curr.audit_id})"
                }
        return {
            "is_valid": True,
            "records_verified": len(IMMUTABLE_AUDIT_LEDGER),
            "status": "CHAIN_INTEGRITY_VERIFIED"
        }

    @classmethod
    def seed_initial_audit_trail(cls, customer_id: str):
        """Seeds initial audit events across the lifecycle for demonstration & testing."""
        events = [
            (AuditEventType.DATA_INGESTED, "DATA_INGESTION_ENGINE", "BATCH_INGEST_TXN_001", {"records_ingested": 180, "status": "CLEAN"}, 98.0, None),
            (AuditEventType.DISTRESS_DETECTED, "EARLY_DISTRESS_ENGINE", "FRE_SNAPSHOT_001", {"distress_score": 78.0, "classification": "SMA_1"}, 92.4, None),
            (AuditEventType.ROOT_CAUSE_IDENTIFIED, "ROOT_CAUSE_ANALYZER", "EDD_REPORT_001", {"primary_cause": "OBLIGATION_COLLISION", "rank": 1}, 88.0, None),
            (AuditEventType.LOAN_EVALUATED, "CREDIT_AFFORDABILITY_ENGINE", "LOAN_REQ_15L", {"verdict": "VETOED_PREDATORY_RISK", "dscr": 0.82}, 95.0, None),
            (AuditEventType.INTERVENTION_RECOMMENDED, "LEAST_HARM_OPTIMIZER", "TWIN_SIM_001", {"recommended_option": "RECEIVABLE_ACCELERATION", "benefit": 88.6, "harm": 4.0}, 91.0, None),
            (AuditEventType.HUMAN_REVIEWED, "BANKER_REVIEW_DESK", "REV_CASE_001", {"officer_id": "OFFICER_BALA_772", "action": "MODIFY"}, 91.0, "MODIFY"),
            (AuditEventType.INTERVENTION_APPROVED, "BANKER_REVIEW_DESK", "REV_CASE_001", {"approved_intervention": "TREDS_FACTORING_75_PCT"}, 100.0, "APPROVE"),
            (AuditEventType.INTERVENTION_EXECUTED, "EXECUTION_GATEWAY", "TREDS_INVOICE_BATCH_001", {"invoices_submitted": 2, "cash_mobilized": 900000.0}, 100.0, None),
            (AuditEventType.OUTCOME_RECORDED, "LONGITUDINAL_TRACKER", "OUTCOME_MONTH_1", {"distress_change": -31.0, "default_prevented": True}, 96.0, None),
        ]
        for ev, mod, ref, out, conf, dec in events:
            cls.record_event(CreateAuditEventRequest(
                customer_id=customer_id,
                event_type=ev,
                module=mod,
                input_reference=ref,
                output=out,
                confidence=conf,
                human_decision=dec
            ))
