"""Comprehensive Automated Test Suite for Problem 2 - Monitor Application

Validates all 25 mandatory behavioral specifications from Section 42:
1. SAE escalates in same cycle
2. AESHOSP=Y + AESER=N recognized as serious
3. Liver candidate with elevated screening value remains monitoring
4. Data issue creates specific query
5. Query references exact record
6. Duplicate query prevented
7. APPROVED executes
8. REJECTED downgrades to monitoring
9. Rejected item does not re-escalate
10. CLARIFY searches Knowledge Graph
11. CLARIFY returns actual evidence
12. CLARIFY resubmits escalation
13. Recurring subject detected
14. Recurring site detected
15. Unanswered query tracked
16. Rerunning same cut creates 0 new queries
17. Rerunning same cut creates 0 new escalations
18. Protocol amendment changes compliance
19. Historical protocol result preserved
20. Every node writes trace
21. Trace contains evidence
22. Risk Radar detects recurring pattern
23. Risk Radar links graph evidence
24. Memory survives restart
25. API failure does not create false success
"""

import unittest
import os
import shutil
from typing import Dict, Any

from stage1.atlas import Atlas
from stage2.crew import ReviewCrew
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph
from stage2.protocol import ProtocolEngine


class TestClinicalMonitor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_db = "test_clinical_monitor.db"
        if os.path.exists(cls.test_db):
            os.remove(cls.test_db)

    def setUp(self):
        # Fresh instance per test or clean DB if needed
        self.crew = ReviewCrew(db_path=self.test_db)

    # 1. SAE escalates in same cycle
    def test_01_sae_escalates_in_same_cycle(self):
        report = self.crew.run_cycle(cut=1, protocol_version=1)
        escalations = self.crew.memory.get_escalations(status="PENDING")
        self.assertGreater(len(escalations), 0, "SAE must escalate into a pending escalation in same cycle")
        # Check that 042-S02-004 is present
        target_esc = next((e for e in escalations if e["subject"] == "042-S02-004"), None)
        self.assertIsNotNone(target_esc, "Subject 042-S02-004 must have pending escalation")

    # 2. AESHOSP=Y + AESER=N recognized as serious
    def test_02_aeshosp_aeser_recognized_as_serious(self):
        findings = self.crew.atlas.detect_findings(cut=1)
        sae_finding = next((f for f in findings if f["subject_id"] == "042-S02-004"), None)
        self.assertIsNotNone(sae_finding)
        self.assertEqual(sae_finding["finding_code"], "SAE_MISCODED")
        self.assertEqual(sae_finding["source_evidence"]["AESHOSP"], "Y")
        self.assertEqual(sae_finding["source_evidence"]["AESER"], "N")
        # In medical review, classified as SAFETY ISSUE
        med_res = self.crew.medical_review_node.run([sae_finding], cut=1, protocol_version=1)
        self.assertEqual(med_res["classified_findings"][0]["classification"], "SAFETY ISSUE")

    # 3. Liver candidate with elevated screening value remains monitoring
    def test_03_liver_elevated_screening_remains_monitoring(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        findings = self.crew.memory.get_findings(subject="042-S01-002")
        liver_f = next((f for f in findings if "LIVER" in f["finding_code"]), None)
        self.assertIsNotNone(liver_f)
        self.assertEqual(liver_f["classification"], "MONITORING ONLY")
        self.assertIn("Screening value was already elevated", liver_f["rationale"])

    # 4. Data issue creates specific query
    def test_04_data_issue_creates_specific_query(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        queries = self.crew.memory.get_queries(subject="042-S03-005")
        predose_q = next((q for q in queries if "precedes" in q["issue"].lower() or "first dose" in q["issue"].lower() or "prior to" in q["issue"].lower()), None)
        self.assertIsNotNone(predose_q, "Must create specific query for AE before first dose")
        self.assertTrue(len(predose_q["requested_action"]) > 10)

    # 5. Query references exact record
    def test_05_query_references_exact_record(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        queries = self.crew.memory.get_queries(subject="042-S03-005")
        q = queries[0]
        self.assertIn("SOURCE_DOC", q["evidence"])
        self.assertEqual(q["evidence"]["SOURCE_DOC"], "CRF-AE-042-S03-005-Seq1")

    # 6. Duplicate query prevented
    def test_06_duplicate_query_prevented(self):
        # Run cut 1 twice
        rep1 = self.crew.run_cycle(cut=1, protocol_version=1)
        q_count_before = len(self.crew.memory.get_queries())
        rep2 = self.crew.run_cycle(cut=1, protocol_version=1)
        q_count_after = len(self.crew.memory.get_queries())
        self.assertEqual(q_count_before, q_count_after, "Duplicate query generation must be prevented")
        self.assertEqual(rep2["new_queries_created"], 0)

    # 7. APPROVED executes
    def test_07_approved_executes(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        escalations = self.crew.memory.get_escalations(status="PENDING")
        esc_id = escalations[0]["escalation_id"]
        res = self.crew.human_gate_node.process_decision(esc_id, "APPROVED")
        self.assertEqual(res["decision"], "APPROVED")
        self.assertEqual(res["escalation"]["status"], "APPROVED")
        # Run execute
        cycle_rep = self.crew.execute_node.run(cut=1, protocol_version=1)
        self.assertGreaterEqual(len(cycle_rep["executed_actions"]), 1)

    # 8. REJECTED downgrades to monitoring
    def test_08_rejected_downgrades_to_monitoring(self):
        # Insert a dummy escalation to test rejection
        dummy_key = "ESC_042-S01-999_TEST_REJECT"
        self.crew.memory.insert_escalation({
            "escalation_id": "ESC-TEST-REJECT-1",
            "finding_code": "SAE_TEST",
            "subject": "042-S01-999",
            "site": "S01",
            "severity": "HIGH",
            "summary": "Test summary",
            "evidence": {},
            "protocol_section": "7.3",
            "protocol_version": 1,
            "alternatives": [],
            "required_action": "Action",
            "status": "PENDING"
        }, dummy_key)

        res = self.crew.human_gate_node.process_decision(
            escalation_id="ESC-TEST-REJECT-1",
            decision="REJECTED",
            reason="Investigator confirmed outpatient clinic observation only."
        )
        self.assertEqual(res["decision"], "REJECTED")
        self.assertEqual(res["escalation"]["status"], "REJECTED")
        self.assertIn("Investigator confirmed", res["escalation"]["rejection_reason"])

    # 9. Rejected item does not re-escalate
    def test_09_rejected_item_does_not_reescalate(self):
        # Attempt to insert same rejected escalation again
        dummy_key = "ESC_042-S01-999_TEST_REJECT"
        inserted = self.crew.memory.insert_escalation({
            "escalation_id": "ESC-TEST-REJECT-2",
            "finding_code": "SAE_TEST",
            "subject": "042-S01-999",
            "site": "S01",
            "severity": "HIGH",
            "summary": "Test summary retry",
            "evidence": {},
            "protocol_section": "7.3",
            "protocol_version": 1,
            "alternatives": [],
            "required_action": "Action",
            "status": "PENDING"
        }, dummy_key)
        self.assertFalse(inserted, "Rejected escalation must not re-escalate or duplicate")

    # 10. CLARIFY searches Knowledge Graph
    def test_10_clarify_searches_knowledge_graph(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        clarify_res = self.crew.kg.answer_clarify("What was screening ALT and any medication?", "042-S01-002")
        self.assertIn("SEARCHING KNOWLEDGE GRAPH", clarify_res["search_log"])
        self.assertIn("SEARCHING LABS", clarify_res["search_log"][3])
        self.assertIn("SEARCHING MEDICATIONS", clarify_res["search_log"][4])

    # 11. CLARIFY returns actual evidence
    def test_11_clarify_returns_actual_evidence(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        clarify_res = self.crew.kg.answer_clarify("What was screening ALT and any medication?", "042-S01-002")
        self.assertGreater(len(clarify_res["evidence"]), 0)
        alt_ev = next((e for e in clarify_res["evidence"] if "ALT" in e.get("category", "")), None)
        self.assertIsNotNone(alt_ev)
        self.assertEqual(alt_ev["value"], "82.0 U/L")

    # 12. CLARIFY resubmits escalation
    def test_12_clarify_resubmits_escalation(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        # Create a pending escalation for 042-S01-002
        esc_id = "ESC-TEST-CLARIFY"
        self.crew.memory.insert_escalation({
            "escalation_id": esc_id,
            "finding_code": "LIVER_EVAL",
            "subject": "042-S01-002",
            "site": "S01",
            "severity": "MEDIUM",
            "summary": "Liver check",
            "evidence": {},
            "protocol_section": "5.2",
            "protocol_version": 1,
            "alternatives": [],
            "required_action": "Evaluate",
            "status": "PENDING"
        }, "ESC_042-S01-002_LIVER_EVAL")

        res = self.crew.human_gate_node.process_decision(
            escalation_id=esc_id,
            decision="CLARIFY",
            question="What was screening ALT and are they taking acetaminophen?"
        )
        self.assertEqual(res["decision"], "CLARIFY")
        self.assertEqual(res["escalation"]["status"], "PENDING", "Must resubmit as PENDING for Medical Monitor")
        self.assertGreater(len(res["escalation"]["clarification_history"]), 0)

    # 13. Recurring subject detected
    def test_13_recurring_subject_detected(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        self.crew.run_cycle(cut=2, protocol_version=1)
        # Subject 042-S03-005 has issues in Cut 1 (AE before dose) and Cut 2 (incomplete dose log)
        queries = self.crew.memory.get_queries(subject="042-S03-005")
        self.assertGreaterEqual(len(queries), 2, "Recurring subject must accumulate multi-cycle queries")

    # 14. Recurring site detected
    def test_14_recurring_site_detected(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        self.crew.run_cycle(cut=2, protocol_version=1)
        signals = self.crew.risk_radar.analyze_signals(2, 1)
        s03_sig = next((s for s in signals if s["site"] == "S03"), None)
        self.assertIsNotNone(s03_sig, "Recurring site pattern for S03 must be detected")
        self.assertIn("042-S03-005", s03_sig["affected_subjects"])

    # 15. Unanswered query tracked
    def test_15_unanswered_query_tracked(self):
        # Simulate an open query in cut 1
        q_id = "QRY-UNANSWERED-1"
        self.crew.memory.insert_query({
            "query_id": q_id,
            "subject": "042-S02-003",
            "site": "S02",
            "domain": "LB",
            "sequence": 1,
            "cut": 1,
            "issue": "Serum Creatinine mismatch",
            "requested_action": "Verify unit",
            "status": "OPEN",
            "evidence": {},
            "created_cycle": 1,
            "attempt_count": 2
        }, "042-S02-003_LB_1_UNIT_UNANSWERED")

        # Run cut 2
        self.crew.data_manager_node.run([], cut=2, protocol_version=1)
        updated_q = self.crew.memory.get_query(q_id)
        self.assertEqual(updated_q["status"], "ON HOLD")
        self.assertEqual(updated_q["attempt_count"], 3)

    # 16. Rerunning same cut creates 0 new queries
    def test_16_rerunning_same_cut_creates_0_new_queries(self):
        rep1 = self.crew.run_cycle(cut=1, protocol_version=1)
        rep2 = self.crew.run_cycle(cut=1, protocol_version=1)
        self.assertEqual(rep2["new_queries_created"], 0)

    # 17. Rerunning same cut creates 0 new escalations
    def test_17_rerunning_same_cut_creates_0_new_escalations(self):
        rep1 = self.crew.run_cycle(cut=1, protocol_version=1)
        rep2 = self.crew.run_cycle(cut=1, protocol_version=1)
        self.assertEqual(rep2["new_escalations_created"], 0)

    # 18. Protocol amendment changes compliance
    def test_18_protocol_amendment_changes_compliance(self):
        raw_data = self.crew.atlas.get_raw_data(cut=1)
        # Evaluate under v1
        devs_v1 = self.crew.protocol_engine.evaluate_subject_compliance(raw_data, 1, cut=1)
        # Evaluate under v2 (amended: renal threshold eGFR < 60, NSAIDs prohibited)
        devs_v2 = self.crew.protocol_engine.evaluate_subject_compliance(raw_data, 2, cut=1)
        # Under v2, 042-S01-003 (eGFR 52) and 042-S02-001 (Naproxen) become deviations
        self.assertGreater(len(devs_v2), len(devs_v1))
        diff = self.crew.protocol_engine.compute_protocol_diff(1, 2, raw_data, cut=1)
        self.assertIn("042-S01-003", diff["affected_subjects"])

    # 19. Historical protocol result preserved
    def test_19_historical_protocol_result_preserved(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        devs_v1 = self.crew.memory.get_deviations(protocol_version=1)
        self.crew.run_cycle(cut=1, protocol_version=2)
        devs_v1_after = self.crew.memory.get_deviations(protocol_version=1)
        devs_v2 = self.crew.memory.get_deviations(protocol_version=2)
        self.assertEqual(len(devs_v1), len(devs_v1_after), "Historical v1 deviations must be preserved")
        self.assertGreater(len(devs_v2), 0, "New v2 deviations must be recorded alongside v1")

    # 20. Every node writes trace
    def test_20_every_node_writes_trace(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        traces = self.crew.memory.get_trace(cycle=1)
        nodes_in_trace = {t["node"] for t in traces}
        for expected_node in ["detect", "medical_review", "data_manager", "compliance", "human_gate", "execute"]:
            self.assertIn(expected_node, nodes_in_trace, f"Node '{expected_node}' must have written trace")

    # 21. Trace contains evidence
    def test_21_trace_contains_evidence(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        traces = self.crew.memory.get_trace(cycle=1, node="detect")
        evidence_present = any(t["evidence"] is not None for t in traces)
        self.assertTrue(evidence_present, "Trace entries must contain source evidence")

    # 22. Risk Radar detects recurring pattern
    def test_22_risk_radar_detects_recurring_pattern(self):
        self.crew.run_cycle(cut=1, protocol_version=1)
        self.crew.run_cycle(cut=2, protocol_version=1)
        signals = self.crew.risk_radar.analyze_signals(2, 1)
        self.assertGreater(len(signals), 0, "Risk Radar must detect active risk signals")

    # 23. Risk Radar links graph evidence
    def test_23_risk_radar_links_graph_evidence(self):
        signals = self.crew.risk_radar.analyze_signals(2, 1)
        sig = signals[0]
        self.assertIn("graph_evidence", sig)
        self.assertTrue(bool(sig["graph_evidence"]))

    # 24. Memory survives restart
    def test_24_memory_survives_restart(self):
        # Insert known trace and query in one instance
        q_test_id = "QRY-PERSIST-TEST"
        self.crew.memory.insert_query({
            "query_id": q_test_id,
            "subject": "042-S01-001",
            "site": "S01",
            "domain": "EX",
            "sequence": 99,
            "cut": 1,
            "issue": "Persistence check",
            "requested_action": "None",
            "status": "OPEN",
            "evidence": {},
            "created_cycle": 1
        }, "042-S01-001_EX_99_PERSIST")

        # Create brand new instance with same DB path
        new_instance = PersistentMemory(db_path=self.test_db)
        retrieved = new_instance.get_query(q_test_id)
        self.assertIsNotNone(retrieved, "Query must persist and be retrievable from fresh memory instance")
        self.assertEqual(retrieved["query_id"], q_test_id)

    # 25. API failure does not create false success
    def test_25_api_failure_does_not_create_false_success(self):
        # Configure impossible target URL
        bad_dm = self.crew.data_manager_node
        bad_dm.hub_url = "http://127.0.0.1:59999/nonexistent"
        sync_res = bad_dm._sync_external_query({
            "query_id": "QRY-TEST-ERR",
            "subject": "042-S01-001",
            "site": "S01",
            "domain": "LB",
            "issue": "Test",
            "requested_action": "Test"
        })
        self.assertEqual(sync_res["status"], "SYNC_FAILED", "API failure must not report success")
        self.assertIsNotNone(sync_res["error"], "Real error message must be captured")


if __name__ == "__main__":
    unittest.main()
