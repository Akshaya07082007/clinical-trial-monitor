"""Node 2: MEDICAL REVIEW

Performs medical monitoring evaluation on each detected finding:
- Seriousness & clinical relevance
- Critical SAE Rule: IF AESHOSP = Y AND AESER = N -> MUST escalate as serious event!
- Liver Signal Rule: Check screening ALT/AST; if already elevated at screening -> MONITORING ONLY
  with reason: "Screening value was already elevated."
- Classifications: SAFETY ISSUE, DATA QUALITY ISSUE, COMPLIANCE ISSUE, MONITORING ONLY
- Immediately writes trace entries: node = "medical_review"
"""

from typing import Dict, List, Any, Optional
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph


class MedicalReviewNode:
    def __init__(self, memory: PersistentMemory, kg: ClinicalKnowledgeGraph):
        self.memory = memory
        self.kg = kg

    def run(
        self,
        findings: List[Dict[str, Any]],
        cut: int,
        protocol_version: int
    ) -> Dict[str, Any]:
        classified_findings = []
        new_escalations_created = []

        for f in findings:
            code = f["finding_code"]
            subj = f["subject_id"]
            site = f["site"]
            evidence = f["source_evidence"]

            classification = "MONITORING ONLY"
            monitoring_reason = None
            escalation_candidate = None

            # --- Rule 5: Critical SAE Rule ---
            # IF AESHOSP = Y AND AESER = N -> MUST recognize as serious!
            if code == "SAE_MISCODED" or (evidence.get("AESHOSP") == "Y" and evidence.get("AESER") == "N"):
                classification = "SAFETY ISSUE"
                dedup_key = f"ESC_{subj}_{site}_SAE_MISCODED_{f.get('sequence', 1)}"

                # Build full required escalation record
                escalation_candidate = {
                    "escalation_id": f"ESC-C{cut}-{subj}-{f.get('sequence', 1)}",
                    "dedup_key": dedup_key,
                    "finding_code": "SAE_MISCODED",
                    "subject": subj,
                    "site": site,
                    "severity": "HIGH",
                    "summary": f"Subject {subj} at Site {site} was admitted to hospital (AESHOSP=Y) for '{evidence.get('AETERM')}', but serious adverse event flag is miscoded as 'N' (AESER=N).",
                    "evidence": {
                        "domain": "AE",
                        "subject": subj,
                        "site": site,
                        "sequence": f.get("sequence", 1),
                        "aeterm": evidence.get("AETERM"),
                        "aestdtc": evidence.get("AESTDTC"),
                        "aeendtc": evidence.get("AEENDTC"),
                        "aeshosp": evidence.get("AESHOSP"),
                        "aeser": evidence.get("AESER"),
                        "source_doc": evidence.get("SOURCE_DOC"),
                        "comment": evidence.get("COMMENT", "")
                    },
                    "protocol_section": "Section 7.3: Expedited Serious Adverse Event Reporting (Within 24h)",
                    "protocol_version": protocol_version,
                    "alternatives": [
                        "Downgrade to routine site clarification query",
                        "Defer decision to next scheduled monitor visit",
                        "Immediate Expedited SAE Escalation with 24-hour Sponsor/IRB alert"
                    ],
                    "required_action": "Issue immediate expedited SAE regulatory notification and require Site PI to formally correct CRF AESER flag to 'Y'.",
                    "created_cycle": cut
                }

            # --- Rule 6: Liver Signal Rule ---
            elif code in ["LIVER_SIGNAL_CANDIDATE", "LIVER_SIGNAL_ELEVATION"]:
                screening_labs = self.kg.get_screening_labs(subj)
                scr_alt = next((l for l in screening_labs if l.get("test_code") == "ALT"), None)
                scr_ast = next((l for l in screening_labs if l.get("test_code") == "AST"), None)

                screening_elevated = False
                if scr_alt and scr_alt.get("ref_high") and scr_alt.get("value", 0) > scr_alt.get("ref_high"):
                    screening_elevated = True
                if scr_ast and scr_ast.get("ref_high") and scr_ast.get("value", 0) > scr_ast.get("ref_high"):
                    screening_elevated = True

                if screening_elevated:
                    classification = "MONITORING ONLY"
                    monitoring_reason = "Screening value was already elevated."
                else:
                    classification = "SAFETY ISSUE"

            elif code in ["AE_BEFORE_FIRST_DOSE", "MISSING_DOSE_RECORD", "LAB_UNIT_DISCREPANCY", "DATE_CHRONOLOGY_ERROR", "INCOMPLETE_DOSE_RECORD"]:
                classification = "DATA QUALITY ISSUE"

            elif code in ["VISIT_WINDOW_EXCEEDED", "RENAL_EXCLUSION_VIOLATION", "PROHIBITED_MEDICATION_VIOLATION"]:
                classification = "COMPLIANCE ISSUE"

            # Update finding in DB
            if not f.get("finding_id"):
                f["finding_id"] = f"FND-C{cut}-{subj}-{code}-{f.get('sequence', 1)}"
            f["classification"] = classification
            if monitoring_reason:
                f["rationale"] = f"{f['rationale']} [Medical Review: {monitoring_reason}]"
            self.memory.insert_finding(f)
            classified_findings.append(f)

            # Persist escalation if needed (with deduplication & rejection checks)
            if escalation_candidate:
                inserted = self.memory.insert_escalation(escalation_candidate, escalation_candidate["dedup_key"])
                if inserted:
                    new_escalations_created.append(escalation_candidate)
                    self.memory.write_trace(
                        cycle=cut,
                        node="medical_review",
                        decision="ESCALATION_CREATED",
                        subject=subj,
                        site=site,
                        evidence=escalation_candidate["evidence"],
                        protocol_version=protocol_version,
                        escalation_id=escalation_candidate["escalation_id"],
                        actor="medical_review_node"
                    )
                else:
                    self.memory.write_trace(
                        cycle=cut,
                        node="medical_review",
                        decision="ESCALATION_DEDUPLICATED_OR_PREVIOUSLY_REJECTED",
                        subject=subj,
                        site=site,
                        evidence={"dedup_key": escalation_candidate["dedup_key"]},
                        protocol_version=protocol_version,
                        actor="medical_review_node"
                    )

            # Mandatory real-time trace for medical review decision
            self.memory.write_trace(
                cycle=cut,
                node="medical_review",
                decision=f"CLASSIFIED_{classification}" + (f"_REASON_{monitoring_reason}" if monitoring_reason else ""),
                subject=subj,
                site=site,
                evidence={
                    "finding_code": code,
                    "classification": classification,
                    "monitoring_reason": monitoring_reason,
                    "source_evidence": evidence
                },
                protocol_version=protocol_version,
                actor="medical_review_node"
            )

        return {
            "classified_findings": classified_findings,
            "new_escalations": new_escalations_created,
            "new_escalations_count": len(new_escalations_created)
        }
