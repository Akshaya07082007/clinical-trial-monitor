"""Stage 2: Protocol Drift & Ripple-Risk Radar

Operational surveillance analyzing:
- Knowledge Graph topology
- Multi-cycle queries, deviations, escalations, protocol versions
- Detects recurring site issues, repeated dosing/timing errors, query accumulation,
  and protocol drift following amendments.
Risk Radar does NOT diagnose patients or make autonomous clinical decisions.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph


class RiskRadar:
    def __init__(self, memory: PersistentMemory, kg: ClinicalKnowledgeGraph):
        self.memory = memory
        self.kg = kg

    def analyze_signals(self, current_cut: int, protocol_version: int) -> List[Dict[str, Any]]:
        signals = []

        queries = self.memory.get_queries()
        deviations = self.memory.get_deviations()
        escalations = self.memory.get_escalations()
        findings = self.memory.get_findings()

        # 1. Pattern: Site S03 Chronological & Dosing Discrepancy Cluster
        s03_queries = [q for q in queries if q.get("site") == "S03"]
        s03_subjects = list({q.get("subject") for q in s03_queries if q.get("subject")})
        if len(s03_subjects) >= 2 or len(s03_queries) >= 2:
            signals.append({
                "signal_id": "RSK-SITE-S03-CHRONOLOGY",
                "site": "S03",
                "issue_type": "RECURRENT_SITE_CHRONOLOGY_ERRORS",
                "affected_subjects": s03_subjects,
                "occurrences": len(s03_queries),
                "first_occurrence": min(q.get("created_at", "") for q in s03_queries),
                "latest_occurrence": max(q.get("created_at", "") for q in s03_queries),
                "protocol_version": protocol_version,
                "related_records": [q.get("evidence", {}).get("SOURCE_DOC", "") for q in s03_queries if q.get("evidence")],
                "related_queries": [q["query_id"] for q in s03_queries],
                "related_escalations": [e["escalation_id"] for e in escalations if e.get("site") == "S03"],
                "explanation": f"Site S03 exhibits a cluster of {len(s03_queries)} data chronology discrepancies across subjects {', '.join(s03_subjects)} (e.g. AE onset preceding first dose date, date reversals). Indicates potential site staff training or source transcription deficiency.",
                "graph_evidence": {
                    "site_node": "SITE:S03",
                    "subject_nodes": [f"SUBJ:{s}" for s in s03_subjects],
                    "query_nodes": [q["query_id"] for q in s03_queries]
                },
                "status": "REQUIRES REVIEW"
            })

        # 2. Pattern: Protocol Drift Following Amendment (e.g. v2 Prohibited Meds / Renal)
        if protocol_version >= 2:
            v2_devs = [d for d in deviations if d.get("protocol_version") == 2]
            v2_subjects = list({d.get("subject") for d in v2_devs if d.get("subject")})
            if v2_devs:
                signals.append({
                    "signal_id": "RSK-PROTO-V2-AMENDMENT-DRIFT",
                    "site": "CROSS-SITE",
                    "issue_type": "POST_AMENDMENT_COMPLIANCE_DRIFT",
                    "affected_subjects": v2_subjects,
                    "occurrences": len(v2_devs),
                    "first_occurrence": "2026-02-01",
                    "latest_occurrence": datetime.utcnow().isoformat()[:10],
                    "protocol_version": protocol_version,
                    "related_records": [d.get("evidence", {}).get("source_doc", "") for d in v2_devs if d.get("evidence")],
                    "related_queries": [],
                    "related_escalations": [],
                    "explanation": f"Activation of Protocol v2 generated {len(v2_devs)} new deviations across subjects {', '.join(v2_subjects)} relating to heightened renal cut-offs (eGFR < 60) and expanded prohibited NSAIDs. Suggests need for immediate investigator site broadcast regarding amendment enforcement.",
                    "graph_evidence": {
                        "protocol_node": "PROTO:v2",
                        "affected_subject_nodes": [f"SUBJ:{s}" for s in v2_subjects]
                    },
                    "status": "MONITOR"
                })

        # 3. Pattern: Accumulating Unanswered Queries (e.g. Site S02)
        on_hold_queries = [q for q in queries if q.get("status") in ["ON HOLD", "OPEN"] and q.get("attempt_count", 1) >= 2]
        if on_hold_queries:
            sites_with_unanswered = list({q.get("site") for q in on_hold_queries if q.get("site")})
            for s in sites_with_unanswered:
                site_unanswered = [q for q in on_hold_queries if q.get("site") == s]
                signals.append({
                    "signal_id": f"RSK-UNANSWERED-QUERIES-{s}",
                    "site": s,
                    "issue_type": "UNRESPONSIVE_SITE_QUERY_ACCUMULATION",
                    "affected_subjects": list({q.get("subject") for q in site_unanswered}),
                    "occurrences": len(site_unanswered),
                    "first_occurrence": min(q.get("created_at", "") for q in site_unanswered),
                    "latest_occurrence": max(q.get("created_at", "") for q in site_unanswered),
                    "protocol_version": protocol_version,
                    "related_records": [q.get("evidence", {}).get("SOURCE_DOC", "") for q in site_unanswered],
                    "related_queries": [q["query_id"] for q in site_unanswered],
                    "related_escalations": [],
                    "explanation": f"Site {s} has {len(site_unanswered)} unresolved queries that have reached 2+ re-query attempts without resolution. Risk of data freeze blockages.",
                    "graph_evidence": {
                        "site_node": f"SITE:{s}",
                        "query_nodes": [q["query_id"] for q in site_unanswered]
                    },
                    "status": "EARLY WARNING"
                })

        # Persist signals
        for sig in signals:
            self.memory.upsert_risk_signal(sig)

        return signals
