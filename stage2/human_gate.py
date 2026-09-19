"""Node 5: HUMAN GATE

The Human Medical Monitor is the final decision-maker.
Evaluates pending escalations with EXACTLY THREE decisions:
1. APPROVED: Approves required action, triggers execution, records decision, writes trace.
2. REJECTED: Requires reason, downgrades to monitoring, stores rejection, writes trace, prevents re-escalation.
3. CLARIFY: NOT rejection! Accepts question, queries Knowledge Graph, returns actual evidence, writes trace, resubmits escalation.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph


class HumanGateNode:
    def __init__(self, memory: PersistentMemory, kg: ClinicalKnowledgeGraph):
        self.memory = memory
        self.kg = kg

    def get_pending_escalations(self) -> List[Dict[str, Any]]:
        """Returns all escalations awaiting medical monitor decision."""
        return self.memory.get_escalations(status="PENDING")

    def process_decision(
        self,
        escalation_id: str,
        decision: str,  # APPROVED, REJECTED, CLARIFY
        reason: Optional[str] = None,
        question: Optional[str] = None,
        actor: str = "Medical Monitor (Human)"
    ) -> Dict[str, Any]:
        esc = self.memory.get_escalation(escalation_id)
        if not esc:
            raise ValueError(f"Escalation {escalation_id} not found.")

        decision = decision.upper()
        if decision not in ["APPROVED", "REJECTED", "CLARIFY"]:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of: APPROVED, REJECTED, CLARIFY.")

        cut = esc.get("created_cycle", 1)
        pv = esc.get("protocol_version", 1)
        subj = esc.get("subject")
        site = esc.get("site")

        # 1. APPROVED
        if decision == "APPROVED":
            exec_details = f"Approved by {actor}. Action initiated: {esc.get('required_action')}."
            updated_esc = self.memory.update_escalation_decision(
                escalation_id=escalation_id,
                decision="APPROVED",
                execution_details=exec_details
            )

            # Mandatory real-time trace
            self.memory.write_trace(
                cycle=cut,
                node="human_gate",
                decision="ESCALATION_APPROVED",
                subject=subj,
                site=site,
                evidence={
                    "escalation_id": escalation_id,
                    "approved_action": esc.get("required_action"),
                    "protocol_section": esc.get("protocol_section")
                },
                protocol_version=pv,
                escalation_id=escalation_id,
                actor=actor
            )

            return {
                "decision": "APPROVED",
                "escalation": updated_esc,
                "message": f"Escalation {escalation_id} approved. Executing required action.",
                "clarification": None
            }

        # 2. REJECTED
        elif decision == "REJECTED":
            if not reason:
                raise ValueError("A reason is mandatory when REJECTING an escalation.")

            rejection_text = f"Rejected by {actor}: {reason}"
            updated_esc = self.memory.update_escalation_decision(
                escalation_id=escalation_id,
                decision="REJECTED",
                reason=rejection_text
            )

            # Mandatory trace: note downgrade to monitoring
            self.memory.write_trace(
                cycle=cut,
                node="human_gate",
                decision=f"ESCALATION_REJECTED_DOWNGRADED_TO_MONITORING: {reason}",
                subject=subj,
                site=site,
                evidence={"escalation_id": escalation_id, "rejection_reason": reason},
                protocol_version=pv,
                escalation_id=escalation_id,
                actor=actor
            )

            return {
                "decision": "REJECTED",
                "escalation": updated_esc,
                "message": f"Escalation {escalation_id} rejected and downgraded to monitoring.",
                "clarification": None
            }

        # 3. CLARIFY (NOT rejection!)
        elif decision == "CLARIFY":
            if not question:
                question = "Please clarify subject baseline clinical status and concurrent medications."

            # Query the Knowledge Graph for real evidence
            clarify_result = self.kg.answer_clarify(question=question, subject_id=subj)

            clarification_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "question": question,
                "actor": actor,
                "answer": clarify_result["answer"],
                "evidence_found": clarify_result["evidence"],
                "search_log": clarify_result["search_log"]
            }

            updated_esc = self.memory.update_escalation_decision(
                escalation_id=escalation_id,
                decision="CLARIFY",
                clarification_entry=clarification_entry
            )

            # Mandatory trace
            self.memory.write_trace(
                cycle=cut,
                node="human_gate",
                decision=f"CLARIFICATION_REQUESTED_AND_ANSWERED: {question}",
                subject=subj,
                site=site,
                evidence=clarify_result,
                protocol_version=pv,
                escalation_id=escalation_id,
                actor=actor
            )

            return {
                "decision": "CLARIFY",
                "escalation": updated_esc,
                "clarification": clarification_entry,
                "message": "Clarification completed from Knowledge Graph. Escalation resubmitted for Medical Monitor review."
            }
