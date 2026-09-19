"""Stage 2: ReviewCrew Six-Node Workflow Orchestrator

Executes the mandatory 6-node clinical trial monitoring pipeline in EXACT order:
1. DETECT
2. MEDICAL REVIEW
3. DATA MANAGER
4. COMPLIANCE
5. HUMAN GATE
6. EXECUTE
-> CYCLE REPORT
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os

from stage1.atlas import Atlas
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph
from stage2.protocol import ProtocolEngine
from stage2.detect import DetectNode
from stage2.medical_review import MedicalReviewNode
from stage2.data_manager import DataManagerNode
from stage2.compliance import ComplianceNode
from stage2.human_gate import HumanGateNode
from stage2.execute import ExecuteNode
from stage2.risk_radar import RiskRadar


class ReviewCrew:
    """The central clinical trial review orchestrator."""

    def __init__(
        self,
        hub_url: str = "",
        gateway_url: str = "",
        team_key: str = "",
        atlas: Optional[Atlas] = None,
        db_path: str = "clinical_monitor.db"
    ):
        self.hub_url = hub_url or os.getenv("HUB_URL", "")
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL", "")
        self.team_key = team_key or os.getenv("TEAM_KEY", "")
        self.memory = PersistentMemory(db_path=db_path)
        self.atlas = atlas if atlas is not None else Atlas()
        self.protocol_engine = ProtocolEngine(memory=self.memory)
        self.kg = ClinicalKnowledgeGraph()

        # Initialize six nodes in exact order
        self.detect_node = DetectNode(self.atlas, self.memory)
        self.medical_review_node = MedicalReviewNode(self.memory, self.kg)
        self.data_manager_node = DataManagerNode(
            self.memory,
            hub_url=self.hub_url,
            gateway_url=self.gateway_url,
            team_key=self.team_key
        )
        self.compliance_node = ComplianceNode(self.memory, self.protocol_engine)
        self.human_gate_node = HumanGateNode(self.memory, self.kg)
        self.execute_node = ExecuteNode(self.memory)
        self.risk_radar = RiskRadar(self.memory, self.kg)

    def run_cycle(self, cut: int, protocol_version: int) -> Dict[str, Any]:
        """Executes the full 6-node cycle in exact required order."""
        started_at = datetime.utcnow().isoformat()
        raw_data = self.atlas.get_raw_data(cut)

        # Baseline graph build from study data
        proto_data = self.protocol_engine.get_protocol(protocol_version)
        self.kg.build_from_study_data(raw_data=raw_data, protocol_data=proto_data)

        # --- NODE 1: DETECT ---
        findings = self.detect_node.run(cut=cut, protocol_version=protocol_version)

        # --- NODE 2: MEDICAL REVIEW ---
        med_rev_result = self.medical_review_node.run(
            findings=findings,
            cut=cut,
            protocol_version=protocol_version
        )

        # --- NODE 3: DATA MANAGER ---
        dm_result = self.data_manager_node.run(
            findings=med_rev_result["classified_findings"],
            cut=cut,
            protocol_version=protocol_version
        )

        # --- NODE 4: COMPLIANCE ---
        comp_result = self.compliance_node.run(
            raw_data=raw_data,
            cut=cut,
            protocol_version=protocol_version
        )

        # Update Knowledge Graph with newly derived findings, queries, escalations, deviations
        self.kg.build_from_study_data(
            raw_data=raw_data,
            protocol_data=proto_data,
            findings=med_rev_result["classified_findings"],
            queries=self.memory.get_queries(),
            escalations=self.memory.get_escalations(),
            deviations=comp_result["all_deviations_for_version"]
        )

        # Run Risk Radar operational surveillance
        risk_signals = self.risk_radar.analyze_signals(
            current_cut=cut,
            protocol_version=protocol_version
        )

        # Update Knowledge Graph with risk signals
        self.kg.build_from_study_data(
            raw_data=raw_data,
            protocol_data=proto_data,
            risk_signals=risk_signals
        )

        # --- NODE 5: HUMAN GATE ---
        pending_escalations = self.human_gate_node.get_pending_escalations()
        self.memory.write_trace(
            cycle=cut,
            node="human_gate",
            decision=f"GATE_CHECK_PENDING_ESCALATIONS_{len(pending_escalations)}",
            subject=None,
            site=None,
            evidence={"pending_count": len(pending_escalations)},
            protocol_version=protocol_version,
            actor="human_gate_node"
        )

        # --- NODE 6: EXECUTE ---
        cycle_report = self.execute_node.run(
            cut=cut,
            protocol_version=protocol_version
        )

        cycle_report["started_at"] = started_at
        cycle_report["new_queries_created"] = dm_result["new_queries_count"]
        cycle_report["queries_deduplicated"] = dm_result["deduplicated_count"]
        cycle_report["new_escalations_created"] = med_rev_result["new_escalations_count"]
        cycle_report["risk_signals_detected"] = len(risk_signals)

        return cycle_report
