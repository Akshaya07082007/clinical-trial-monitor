"""Stage 2: Trace Management & Audit Log

Provides real-time chronological audit logging and query capabilities:
Filters by:
- Cycle
- Node (detect, medical_review, data_manager, compliance, human_gate, execute)
- Subject
- Site
- Query
- Escalation
- Protocol Version
"""

from typing import Dict, List, Any, Optional
from stage2.memory import PersistentMemory


class TraceManager:
    def __init__(self, memory: PersistentMemory):
        self.memory = memory

    def log(
        self,
        cycle: int,
        node: str,
        decision: str,
        subject: Optional[str] = None,
        site: Optional[str] = None,
        evidence: Any = None,
        protocol_version: int = 1,
        query_id: Optional[str] = None,
        escalation_id: Optional[str] = None,
        actor: str = "automated"
    ) -> Dict[str, Any]:
        return self.memory.write_trace(
            cycle=cycle,
            node=node,
            decision=decision,
            subject=subject,
            site=site,
            evidence=evidence,
            protocol_version=protocol_version,
            query_id=query_id,
            escalation_id=escalation_id,
            actor=actor
        )

    def get_entries(
        self,
        cycle: Optional[int] = None,
        node: Optional[str] = None,
        subject: Optional[str] = None,
        site: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        return self.memory.get_trace(
            cycle=cycle,
            node=node,
            subject=subject,
            site=site
        )
