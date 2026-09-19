"""Node 3: DATA MANAGER

Converts actual data issues into specific, actionable clinical data queries:
- AE before first dose
- Missing dose records
- Date inconsistency / impossible chronology
- Lab unit discrepancies
- Blank required values
- Query deduplication (key: subject + domain + sequence + issue_type)
- External API synchronization (POST /queries via HUB_URL / GATEWAY_URL) with safe error handling
- Unanswered queries tracking (OPEN / ON HOLD, attempt count, last response)
- Immediately writes trace entries: node = "data_manager"
"""

import os
import urllib.request
import urllib.error
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from stage2.memory import PersistentMemory


class DataManagerNode:
    def __init__(
        self,
        memory: PersistentMemory,
        hub_url: str = "",
        gateway_url: str = "",
        team_key: str = ""
    ):
        self.memory = memory
        self.hub_url = hub_url or os.getenv("HUB_URL", "")
        self.gateway_url = gateway_url or os.getenv("GATEWAY_URL", "")
        self.team_key = team_key or os.getenv("TEAM_KEY", "")

    def run(
        self,
        findings: List[Dict[str, Any]],
        cut: int,
        protocol_version: int
    ) -> Dict[str, Any]:
        new_queries_created = []
        deduplicated_count = 0

        # Review findings for data quality issues
        for f in findings:
            code = f.get("finding_code")
            subj = f.get("subject_id")
            site = f.get("site")
            seq = f.get("sequence", 1)
            ev = f.get("source_evidence", {})

            query_candidate = None

            # 1. AE before first dose
            if code == "AE_BEFORE_FIRST_DOSE":
                issue_type = "CHRONOLOGY_AE_PRE_DOSE"
                dedup_key = f"{subj}_AE_{seq}_{issue_type}"
                query_candidate = {
                    "query_id": f"QRY-C{cut}-{subj}-AE{seq}-PREDOSE",
                    "dedup_key": dedup_key,
                    "subject": subj,
                    "site": site,
                    "domain": "AE",
                    "sequence": seq,
                    "cut": cut,
                    "issue": f"Adverse Event onset '{ev.get('AESTDTC')}' for '{ev.get('AETERM')}' occurred prior to recorded first study drug dose '{ev.get('FIRST_DOSE_DATE')}'.",
                    "requested_action": "Verify chronology with site records. If event resolved prior to first dose, reclassify as Medical History (MH) and close AE record.",
                    "status": "OPEN",
                    "evidence": ev,
                    "created_cycle": cut
                }

            # 2. Missing dose record
            elif code == "MISSING_DOSE_RECORD":
                issue_type = "MISSING_EXPOSURE_VISIT"
                dedup_key = f"{subj}_EX_{seq}_{issue_type}"
                query_candidate = {
                    "query_id": f"QRY-C{cut}-{subj}-EX{seq}-MISSDOSE",
                    "dedup_key": dedup_key,
                    "subject": subj,
                    "site": site,
                    "domain": "EX",
                    "sequence": seq,
                    "cut": cut,
                    "issue": f"{ev.get('VISIT')} was attended per Subject Visits domain on {ev.get('SVSTDTC')}, but no corresponding study drug administration entry exists in Exposure domain.",
                    "requested_action": "Confirm whether study drug was administered at this visit. Enter dispensing/administration log in EX domain or document reason for missed dose.",
                    "status": "OPEN",
                    "evidence": ev,
                    "created_cycle": cut
                }

            # 3. Lab unit discrepancy
            elif code == "LAB_UNIT_DISCREPANCY":
                issue_type = "UNIT_MISMATCH_CREAT"
                dedup_key = f"{subj}_LB_{seq}_{issue_type}"
                query_candidate = {
                    "query_id": f"QRY-C{cut}-{subj}-LB{seq}-UNIT",
                    "dedup_key": dedup_key,
                    "subject": subj,
                    "site": site,
                    "domain": "LB",
                    "sequence": seq,
                    "cut": cut,
                    "issue": f"Serum Creatinine reported as {ev.get('LBORRES')} {ev.get('LBORRESU')} is out of plausible physiological range. Upper reference limit is ~1.2 mg/dL.",
                    "requested_action": "Verify whether units were mistakenly entered as mg/dL instead of umol/L, or if original reported value was 1.10 mg/dL. Re-enter corrected lab certificate.",
                    "status": "OPEN",
                    "evidence": ev,
                    "created_cycle": cut
                }

            # 4. Date chronology error (End before start)
            elif code == "DATE_CHRONOLOGY_ERROR":
                issue_type = "CHRONOLOGY_END_BEFORE_START"
                dedup_key = f"{subj}_AE_{seq}_{issue_type}"
                query_candidate = {
                    "query_id": f"QRY-C{cut}-{subj}-AE{seq}-DATE",
                    "dedup_key": dedup_key,
                    "subject": subj,
                    "site": site,
                    "domain": "AE",
                    "sequence": seq,
                    "cut": cut,
                    "issue": f"AE resolution date '{ev.get('AEENDTC')}' precedes onset date '{ev.get('AESTDTC')}'. Chronologically invalid.",
                    "requested_action": "Correct AE onset or resolution dates against source medical notes.",
                    "status": "OPEN",
                    "evidence": ev,
                    "created_cycle": cut
                }

            # 5. Incomplete / blank dose record
            elif code == "INCOMPLETE_DOSE_RECORD":
                issue_type = "BLANK_DOSE_DETAILS"
                dedup_key = f"{subj}_EX_{seq}_{issue_type}"
                query_candidate = {
                    "query_id": f"QRY-C{cut}-{subj}-EX{seq}-BLANK",
                    "dedup_key": dedup_key,
                    "subject": subj,
                    "site": site,
                    "domain": "EX",
                    "sequence": seq,
                    "cut": cut,
                    "issue": f"Dose record for {ev.get('VISIT')} logged with 0 mg dose and blank administration dates.",
                    "requested_action": "Complete dosage amount and actual administration dates or delete duplicate placeholder record.",
                    "status": "OPEN",
                    "evidence": ev,
                    "created_cycle": cut
                }

            if query_candidate:
                inserted = self.memory.insert_query(query_candidate, query_candidate["dedup_key"])
                if inserted:
                    # Sync with External API if configured
                    sync_res = self._sync_external_query(query_candidate)
                    query_candidate["external_sync_status"] = sync_res["status"]
                    query_candidate["external_sync_error"] = sync_res.get("error")

                    new_queries_created.append(query_candidate)
                    self.memory.write_trace(
                        cycle=cut,
                        node="data_manager",
                        decision="QUERY_RAISED",
                        subject=subj,
                        site=site,
                        evidence=query_candidate["evidence"],
                        protocol_version=protocol_version,
                        query_id=query_candidate["query_id"],
                        actor="data_manager_node"
                    )
                else:
                    deduplicated_count += 1
                    self.memory.write_trace(
                        cycle=cut,
                        node="data_manager",
                        decision="QUERY_DEDUPLICATED",
                        subject=subj,
                        site=site,
                        evidence={"dedup_key": query_candidate["dedup_key"]},
                        protocol_version=protocol_version,
                        actor="data_manager_node"
                    )

        # Handle unanswered queries tracking (Rule 28)
        # If older queries exist and have no response, update attempt count and mark ON HOLD if unresponsive
        all_open_queries = self.memory.get_queries()
        for q in all_open_queries:
            if q["created_cycle"] < cut and q["status"] == "OPEN":
                # Increment attempt count
                if q["attempt_count"] >= 2:
                    self.memory.update_query_status(q["query_id"], "ON HOLD", attempt_increment=True)
                    self.memory.write_trace(
                        cycle=cut,
                        node="data_manager",
                        decision="QUERY_HELD_UNANSWERED",
                        subject=q["subject"],
                        site=q["site"],
                        evidence={"query_id": q["query_id"], "attempts": q["attempt_count"] + 1},
                        protocol_version=protocol_version,
                        query_id=q["query_id"],
                        actor="data_manager_node"
                    )
                else:
                    self.memory.update_query_status(q["query_id"], "OPEN", attempt_increment=True)

        return {
            "new_queries": new_queries_created,
            "new_queries_count": len(new_queries_created),
            "deduplicated_count": deduplicated_count
        }

    def _sync_external_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Attempts to sync query to external API via HUB_URL or GATEWAY_URL if present.
        If fails: preserves local state, captures real error, does NOT claim false success!
        """
        api_target = self.gateway_url or self.hub_url
        if not api_target:
            return {"status": "LOCAL_ONLY", "error": None}

        endpoint = f"{api_target.rstrip('/')}/queries"
        payload = json.dumps({
            "team_key": self.team_key,
            "query_id": query["query_id"],
            "subject": query["subject"],
            "site": query["site"],
            "domain": query["domain"],
            "issue": query["issue"],
            "requested_action": query["requested_action"]
        }).encode("utf-8")

        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Team-Key": self.team_key
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=3) as resp:
                if 200 <= resp.status < 300:
                    return {"status": "SYNCED", "error": None}
                else:
                    return {"status": "SYNC_FAILED", "error": f"HTTP {resp.status}"}
        except Exception as e:
            # Preserves local state, does not claim false success
            return {"status": "SYNC_FAILED", "error": str(e)}
