"""Node 1: DETECT

Executes Stage 1 ATLAS surveillance on the selected study data cut.
Detects safety findings, data-quality findings, compliance findings, monitoring findings,
and site-level patterns.
Immediately writes a trace entry: node = "detect".
"""

from typing import Dict, List, Any
from stage1.atlas import Atlas
from stage2.memory import PersistentMemory


class DetectNode:
    def __init__(self, atlas: Atlas, memory: PersistentMemory):
        self.atlas = atlas
        self.memory = memory

    def run(self, cut: int, protocol_version: int) -> List[Dict[str, Any]]:
        raw_findings = self.atlas.detect_findings(cut)

        processed_findings = []
        for f in raw_findings:
            f_id = f"FND-C{cut}-{f['subject_id']}-{f['finding_code']}-{f['sequence']}"
            finding_record = {
                "finding_id": f_id,
                "cut": cut,
                "finding_code": f["finding_code"],
                "subject_id": f["subject_id"],
                "site": f["site"],
                "severity": f["severity"],
                "rationale": f["rationale"],
                "domain": f["domain"],
                "sequence": f["sequence"],
                "source_evidence": f["source_evidence"],
                "classification": "PENDING",
                "status": "OPEN"
            }
            # Persist to database
            self.memory.insert_finding(finding_record)
            processed_findings.append(finding_record)

            # Mandatory real-time trace logging per finding
            self.memory.write_trace(
                cycle=cut,
                node="detect",
                decision=f"DETECTED_{f['finding_code']}",
                subject=f["subject_id"],
                site=f["site"],
                evidence=f["source_evidence"],
                protocol_version=protocol_version,
                actor="detect_node"
            )

        # Trace summary for Node 1
        self.memory.write_trace(
            cycle=cut,
            node="detect",
            decision=f"COMPLETED_DETECTION_COUNT_{len(processed_findings)}",
            subject=None,
            site=None,
            evidence={"total_detected": len(processed_findings), "cut": cut},
            protocol_version=protocol_version,
            actor="detect_node"
        )

        return processed_findings
