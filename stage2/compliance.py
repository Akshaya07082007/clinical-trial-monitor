"""Node 4: COMPLIANCE

Checks EVERY subject against the active protocol version rules for the selected cut:
- Visit-window deviations
- Prohibited medications
- Eligibility & Renal function exclusion
- Preserves historical evaluations across protocol versions
- Immediately writes trace entries: node = "compliance"
"""

from typing import Dict, List, Any
from stage2.memory import PersistentMemory
from stage2.protocol import ProtocolEngine


class ComplianceNode:
    def __init__(self, memory: PersistentMemory, protocol_engine: ProtocolEngine):
        self.memory = memory
        self.protocol_engine = protocol_engine

    def run(
        self,
        raw_data: Dict[str, List[Dict[str, Any]]],
        cut: int,
        protocol_version: int
    ) -> Dict[str, Any]:
        evaluated_deviations = self.protocol_engine.evaluate_subject_compliance(
            raw_data=raw_data,
            protocol_version=protocol_version,
            cut=cut
        )

        new_deviations_persisted = []
        for dev in evaluated_deviations:
            inserted = self.memory.insert_deviation(dev)
            if inserted:
                new_deviations_persisted.append(dev)
                self.memory.write_trace(
                    cycle=cut,
                    node="compliance",
                    decision=f"DEVIATION_CONFIRMED_{dev['deviation_type']}",
                    subject=dev["subject"],
                    site=dev["site"],
                    evidence=dev["evidence"],
                    protocol_version=protocol_version,
                    actor="compliance_node"
                )

        # Summary trace
        self.memory.write_trace(
            cycle=cut,
            node="compliance",
            decision=f"COMPLETED_COMPLIANCE_EVALUATION_TOTAL_{len(evaluated_deviations)}_NEW_{len(new_deviations_persisted)}",
            subject=None,
            site=None,
            evidence={
                "protocol_version": protocol_version,
                "total_deviations": len(evaluated_deviations),
                "new_deviations": len(new_deviations_persisted)
            },
            protocol_version=protocol_version,
            actor="compliance_node"
        )

        return {
            "all_deviations_for_version": evaluated_deviations,
            "new_deviations": new_deviations_persisted,
            "count": len(evaluated_deviations)
        }
