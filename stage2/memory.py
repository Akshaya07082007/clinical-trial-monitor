"""Stage 2: Persistent Database Memory (SQLite)

Ensures all clinical trial monitor state survives application restart:
- Findings & Medical Reviews
- Queries (with deduplication & status tracking)
- Escalations (with deduplication, human decisions, rejections, clarifications)
- Protocol versions, amendments, and historical compliance evaluations
- Trace log entries (with immediate chronological persistence)
- Risk Radar signals
- Cycle executions
"""

import sqlite3
import json
import os
from typing import Dict, List, Any, Optional
from datetime import datetime


class PersistentMemory:
    def __init__(self, db_path: str = "clinical_monitor.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            cursor = conn.cursor()

            # Cycle Runs
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cycle_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cut INTEGER NOT NULL,
                protocol_version INTEGER NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                summary_json TEXT
            )
            """)

            # Findings
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                finding_id TEXT PRIMARY KEY,
                cut INTEGER NOT NULL,
                finding_code TEXT NOT NULL,
                subject_id TEXT NOT NULL,
                site TEXT NOT NULL,
                severity TEXT NOT NULL,
                rationale TEXT NOT NULL,
                domain TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                source_evidence_json TEXT NOT NULL,
                classification TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """)

            # Queries
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_id TEXT PRIMARY KEY,
                dedup_key TEXT UNIQUE NOT NULL,
                subject TEXT NOT NULL,
                site TEXT NOT NULL,
                domain TEXT NOT NULL,
                sequence INTEGER NOT NULL,
                cut INTEGER NOT NULL,
                issue TEXT NOT NULL,
                requested_action TEXT NOT NULL,
                status TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                created_cycle INTEGER NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 1,
                last_response TEXT,
                created_at TEXT NOT NULL,
                external_sync_status TEXT DEFAULT 'LOCAL_ONLY',
                external_sync_error TEXT
            )
            """)

            # Escalations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                escalation_id TEXT PRIMARY KEY,
                dedup_key TEXT UNIQUE NOT NULL,
                finding_code TEXT NOT NULL,
                subject TEXT NOT NULL,
                site TEXT NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                protocol_section TEXT NOT NULL,
                protocol_version INTEGER NOT NULL,
                alternatives_json TEXT NOT NULL,
                required_action TEXT NOT NULL,
                status TEXT NOT NULL,
                rejection_reason TEXT,
                clarification_history_json TEXT,
                created_cycle INTEGER NOT NULL,
                executed_at TEXT,
                execution_details TEXT,
                created_at TEXT NOT NULL
            )
            """)

            # Compliance Deviations
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS deviations (
                deviation_id TEXT PRIMARY KEY,
                subject TEXT NOT NULL,
                site TEXT NOT NULL,
                deviation_type TEXT NOT NULL,
                protocol_version INTEGER NOT NULL,
                evidence_json TEXT NOT NULL,
                explanation TEXT NOT NULL,
                status TEXT NOT NULL,
                created_cycle INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """)

            # Trace
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS trace (
                trace_id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                cycle INTEGER NOT NULL,
                node TEXT NOT NULL,
                decision TEXT NOT NULL,
                subject TEXT,
                site TEXT,
                evidence_json TEXT,
                protocol_version INTEGER NOT NULL,
                query_id TEXT,
                escalation_id TEXT,
                actor TEXT NOT NULL
            )
            """)

            # Protocol Versions & Amendments
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS protocol_versions (
                version INTEGER PRIMARY KEY,
                effective_cut INTEGER NOT NULL,
                title TEXT NOT NULL,
                rules_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                amendment_summary TEXT
            )
            """)

            # Risk Signals
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS risk_signals (
                signal_id TEXT PRIMARY KEY,
                site TEXT NOT NULL,
                issue_type TEXT NOT NULL,
                affected_subjects_json TEXT NOT NULL,
                occurrences INTEGER NOT NULL,
                first_occurrence TEXT NOT NULL,
                latest_occurrence TEXT NOT NULL,
                protocol_version INTEGER NOT NULL,
                related_records_json TEXT NOT NULL,
                related_queries_json TEXT NOT NULL,
                related_escalations_json TEXT NOT NULL,
                explanation TEXT NOT NULL,
                graph_evidence_json TEXT NOT NULL,
                status TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """)

            conn.commit()

    # --- Query Operations with Deduplication ---
    def has_query_dedup(self, dedup_key: str) -> bool:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM queries WHERE dedup_key = ?", (dedup_key,))
            return c.fetchone() is not None

    def get_query_by_dedup(self, dedup_key: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM queries WHERE dedup_key = ?", (dedup_key,))
            row = c.fetchone()
            return self._row_to_query(row) if row else None

    def insert_query(self, query: Dict[str, Any], dedup_key: str) -> bool:
        if self.has_query_dedup(dedup_key):
            return False
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO queries (
                query_id, dedup_key, subject, site, domain, sequence, cut, issue,
                requested_action, status, evidence_json, created_cycle,
                attempt_count, last_response, created_at, external_sync_status, external_sync_error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                query["query_id"],
                dedup_key,
                query["subject"],
                query["site"],
                query["domain"],
                query["sequence"],
                query["cut"],
                query["issue"],
                query["requested_action"],
                query["status"],
                json.dumps(query["evidence"]),
                query["created_cycle"],
                query.get("attempt_count", 1),
                query.get("last_response"),
                query.get("created_at", datetime.utcnow().isoformat()),
                query.get("external_sync_status", "LOCAL_ONLY"),
                query.get("external_sync_error")
            ))
            conn.commit()
            return True

    def get_queries(self, subject: Optional[str] = None, site: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            query_sql = "SELECT * FROM queries WHERE 1=1"
            params = []
            if subject:
                query_sql += " AND subject = ?"
                params.append(subject)
            if site:
                query_sql += " AND site = ?"
                params.append(site)
            query_sql += " ORDER BY created_at ASC"
            c.execute(query_sql, params)
            return [self._row_to_query(row) for row in c.fetchall()]

    def get_query(self, query_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM queries WHERE query_id = ?", (query_id,))
            row = c.fetchone()
            return self._row_to_query(row) if row else None

    def update_query_status(self, query_id: str, status: str, response: Optional[str] = None, attempt_increment: bool = False):
        with self._get_conn() as conn:
            c = conn.cursor()
            if attempt_increment:
                c.execute("""
                UPDATE queries
                SET status = ?, last_response = COALESCE(?, last_response), attempt_count = attempt_count + 1
                WHERE query_id = ?
                """, (status, response, query_id))
            else:
                c.execute("""
                UPDATE queries
                SET status = ?, last_response = COALESCE(?, last_response)
                WHERE query_id = ?
                """, (status, response, query_id))
            conn.commit()

    def _row_to_query(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "query_id": row["query_id"],
            "subject": row["subject"],
            "site": row["site"],
            "domain": row["domain"],
            "sequence": row["sequence"],
            "cut": row["cut"],
            "issue": row["issue"],
            "requested_action": row["requested_action"],
            "status": row["status"],
            "evidence": json.loads(row["evidence_json"]) if row["evidence_json"] else {},
            "created_cycle": row["created_cycle"],
            "attempt_count": row["attempt_count"],
            "last_response": row["last_response"],
            "created_at": row["created_at"],
            "external_sync_status": row["external_sync_status"],
            "external_sync_error": row["external_sync_error"]
        }

    # --- Escalation Operations with Deduplication & Rejection Downgrade ---
    def has_escalation_dedup(self, dedup_key: str) -> bool:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM escalations WHERE dedup_key = ?", (dedup_key,))
            return c.fetchone() is not None

    def get_escalation_by_dedup(self, dedup_key: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM escalations WHERE dedup_key = ?", (dedup_key,))
            row = c.fetchone()
            return self._row_to_escalation(row) if row else None

    def insert_escalation(self, esc: Dict[str, Any], dedup_key: str) -> bool:
        # Check if already exists or was previously rejected
        existing = self.get_escalation_by_dedup(dedup_key)
        if existing:
            # Rule 21: Never recreate automatically if rejected or already processed
            return False

        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO escalations (
                escalation_id, dedup_key, finding_code, subject, site, severity,
                summary, evidence_json, protocol_section, protocol_version,
                alternatives_json, required_action, status, rejection_reason,
                clarification_history_json, created_cycle, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                esc["escalation_id"],
                dedup_key,
                esc["finding_code"],
                esc["subject"],
                esc["site"],
                esc["severity"],
                esc["summary"],
                json.dumps(esc["evidence"]),
                esc["protocol_section"],
                esc["protocol_version"],
                json.dumps(esc.get("alternatives", [])),
                esc["required_action"],
                esc.get("status", "PENDING"),
                esc.get("rejection_reason"),
                json.dumps(esc.get("clarification_history", [])),
                esc.get("created_cycle", 1),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            return True

    def get_escalations(self, status: Optional[str] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            sql = "SELECT * FROM escalations WHERE 1=1"
            params = []
            if status:
                sql += " AND status = ?"
                params.append(status)
            if subject:
                sql += " AND subject = ?"
                params.append(subject)
            sql += " ORDER BY created_at ASC"
            c.execute(sql, params)
            return [self._row_to_escalation(row) for row in c.fetchall()]

    def get_escalation(self, escalation_id: str) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM escalations WHERE escalation_id = ?", (escalation_id,))
            row = c.fetchone()
            return self._row_to_escalation(row) if row else None

    def update_escalation_decision(
        self,
        escalation_id: str,
        decision: str,  # APPROVED, REJECTED, CLARIFY
        reason: Optional[str] = None,
        clarification_entry: Optional[Dict[str, Any]] = None,
        execution_details: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM escalations WHERE escalation_id = ?", (escalation_id,))
            row = c.fetchone()
            if not row:
                return None

            current = self._row_to_escalation(row)
            clarifications = current.get("clarification_history", [])

            if decision == "APPROVED":
                new_status = "APPROVED"
                exec_at = datetime.utcnow().isoformat()
                c.execute("""
                UPDATE escalations
                SET status = ?, executed_at = ?, execution_details = ?
                WHERE escalation_id = ?
                """, (new_status, exec_at, execution_details or "Approved by Medical Monitor. Expedited notification executed.", escalation_id))

            elif decision == "REJECTED":
                # Rule 21: Downgrade to monitoring, record rejection reason, prevent re-escalation
                new_status = "REJECTED"
                c.execute("""
                UPDATE escalations
                SET status = ?, rejection_reason = ?
                WHERE escalation_id = ?
                """, (new_status, reason or "Rejected by Medical Monitor. Downgraded to monitoring.", escalation_id))

            elif decision == "CLARIFY":
                # Rule 22: CLARIFY is not rejection! Accept question, add to history, resubmit
                if clarification_entry:
                    clarifications.append(clarification_entry)
                new_status = "PENDING"  # resubmitted
                c.execute("""
                UPDATE escalations
                SET status = ?, clarification_history_json = ?
                WHERE escalation_id = ?
                """, (new_status, json.dumps(clarifications), escalation_id))

            conn.commit()

        return self.get_escalation(escalation_id)

    def _row_to_escalation(self, row: sqlite3.Row) -> Dict[str, Any]:
        return {
            "escalation_id": row["escalation_id"],
            "finding_code": row["finding_code"],
            "subject": row["subject"],
            "site": row["site"],
            "severity": row["severity"],
            "summary": row["summary"],
            "evidence": json.loads(row["evidence_json"]) if row["evidence_json"] else {},
            "protocol_section": row["protocol_section"],
            "protocol_version": row["protocol_version"],
            "alternatives": json.loads(row["alternatives_json"]) if row["alternatives_json"] else [],
            "required_action": row["required_action"],
            "status": row["status"],
            "rejection_reason": row["rejection_reason"],
            "clarification_history": json.loads(row["clarification_history_json"]) if row["clarification_history_json"] else [],
            "created_cycle": row["created_cycle"],
            "executed_at": row["executed_at"],
            "execution_details": row["execution_details"]
        }

    # --- Compliance Deviations ---
    def insert_deviation(self, dev: Dict[str, Any]) -> bool:
        with self._get_conn() as conn:
            c = conn.cursor()
            # Check duplicate
            c.execute("""
            SELECT 1 FROM deviations
            WHERE subject = ? AND deviation_type = ? AND protocol_version = ?
            """, (dev["subject"], dev["deviation_type"], dev["protocol_version"]))
            if c.fetchone():
                return False
            c.execute("""
            INSERT INTO deviations (
                deviation_id, subject, site, deviation_type, protocol_version,
                evidence_json, explanation, status, created_cycle, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dev["deviation_id"],
                dev["subject"],
                dev["site"],
                dev["deviation_type"],
                dev["protocol_version"],
                json.dumps(dev["evidence"]),
                dev["explanation"],
                dev.get("status", "CONFIRMED"),
                dev.get("created_cycle", 1),
                datetime.utcnow().isoformat()
            ))
            conn.commit()
            return True

    def get_deviations(self, protocol_version: Optional[int] = None, subject: Optional[str] = None, site: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            sql = "SELECT * FROM deviations WHERE 1=1"
            params = []
            if protocol_version is not None:
                sql += " AND protocol_version = ?"
                params.append(protocol_version)
            if subject:
                sql += " AND subject = ?"
                params.append(subject)
            if site:
                sql += " AND site = ?"
                params.append(site)
            sql += " ORDER BY created_at ASC"
            c.execute(sql, params)
            return [
                {
                    "deviation_id": row["deviation_id"],
                    "subject": row["subject"],
                    "site": row["site"],
                    "deviation_type": row["deviation_type"],
                    "protocol_version": row["protocol_version"],
                    "evidence": json.loads(row["evidence_json"]) if row["evidence_json"] else {},
                    "explanation": row["explanation"],
                    "status": row["status"],
                    "created_cycle": row["created_cycle"]
                }
                for row in c.fetchall()
            ]

    # --- Findings Persistence ---
    def insert_finding(self, finding: Dict[str, Any]):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT OR REPLACE INTO findings (
                finding_id, cut, finding_code, subject_id, site, severity,
                rationale, domain, sequence, source_evidence_json,
                classification, status, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                finding["finding_id"],
                finding["cut"],
                finding["finding_code"],
                finding["subject_id"],
                finding["site"],
                finding["severity"],
                finding["rationale"],
                finding["domain"],
                finding["sequence"],
                json.dumps(finding["source_evidence"]),
                finding.get("classification", "PENDING"),
                finding.get("status", "OPEN"),
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_findings(self, cut: Optional[int] = None, subject: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            sql = "SELECT * FROM findings WHERE 1=1"
            params = []
            if cut is not None:
                sql += " AND cut = ?"
                params.append(cut)
            if subject:
                sql += " AND subject_id = ?"
                params.append(subject)
            sql += " ORDER BY created_at ASC"
            c.execute(sql, params)
            return [
                {
                    "finding_id": row["finding_id"],
                    "cut": row["cut"],
                    "finding_code": row["finding_code"],
                    "subject_id": row["subject_id"],
                    "site": row["site"],
                    "severity": row["severity"],
                    "rationale": row["rationale"],
                    "domain": row["domain"],
                    "sequence": row["sequence"],
                    "source_evidence": json.loads(row["source_evidence_json"]) if row["source_evidence_json"] else {},
                    "classification": row["classification"],
                    "status": row["status"]
                }
                for row in c.fetchall()
            ]

    # --- Trace Logging (Mandatory Real-Time Logging) ---
    def write_trace(
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
        trace_id = f"TRC-{cycle}-{node[:3].upper()}-{datetime.utcnow().strftime('%H%M%S%f')[:10]}"
        timestamp = datetime.utcnow().isoformat()
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO trace (
                trace_id, timestamp, cycle, node, decision, subject, site,
                evidence_json, protocol_version, query_id, escalation_id, actor
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trace_id,
                timestamp,
                cycle,
                node,
                decision,
                subject,
                site,
                json.dumps(evidence) if evidence is not None else None,
                protocol_version,
                query_id,
                escalation_id,
                actor
            ))
            conn.commit()

        return {
            "trace_id": trace_id,
            "timestamp": timestamp,
            "cycle": cycle,
            "node": node,
            "decision": decision,
            "subject": subject,
            "site": site,
            "evidence": evidence,
            "protocol_version": protocol_version,
            "query_id": query_id,
            "escalation_id": escalation_id,
            "actor": actor
        }

    def get_trace(
        self,
        cycle: Optional[int] = None,
        node: Optional[str] = None,
        subject: Optional[str] = None,
        site: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            sql = "SELECT * FROM trace WHERE 1=1"
            params = []
            if cycle is not None:
                sql += " AND cycle = ?"
                params.append(cycle)
            if node:
                sql += " AND node = ?"
                params.append(node)
            if subject:
                sql += " AND subject = ?"
                params.append(subject)
            if site:
                sql += " AND site = ?"
                params.append(site)
            sql += " ORDER BY timestamp ASC"
            c.execute(sql, params)
            return [
                {
                    "trace_id": row["trace_id"],
                    "timestamp": row["timestamp"],
                    "cycle": row["cycle"],
                    "node": row["node"],
                    "decision": row["decision"],
                    "subject": row["subject"],
                    "site": row["site"],
                    "evidence": json.loads(row["evidence_json"]) if row["evidence_json"] else None,
                    "protocol_version": row["protocol_version"],
                    "query_id": row["query_id"],
                    "escalation_id": row["escalation_id"],
                    "actor": row["actor"]
                }
                for row in c.fetchall()
            ]

    # --- Risk Signals ---
    def upsert_risk_signal(self, sig: Dict[str, Any]):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT OR REPLACE INTO risk_signals (
                signal_id, site, issue_type, affected_subjects_json, occurrences,
                first_occurrence, latest_occurrence, protocol_version,
                related_records_json, related_queries_json, related_escalations_json,
                explanation, graph_evidence_json, status, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sig["signal_id"],
                sig["site"],
                sig["issue_type"],
                json.dumps(sig["affected_subjects"]),
                sig["occurrences"],
                sig["first_occurrence"],
                sig["latest_occurrence"],
                sig["protocol_version"],
                json.dumps(sig.get("related_records", [])),
                json.dumps(sig.get("related_queries", [])),
                json.dumps(sig.get("related_escalations", [])),
                sig["explanation"],
                json.dumps(sig.get("graph_evidence", {})),
                sig.get("status", "EARLY WARNING"),
                datetime.utcnow().isoformat()
            ))
            conn.commit()

    def get_risk_signals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            sql = "SELECT * FROM risk_signals WHERE 1=1"
            params = []
            if status:
                sql += " AND status = ?"
                params.append(status)
            sql += " ORDER BY occurrences DESC"
            c.execute(sql, params)
            return [
                {
                    "signal_id": row["signal_id"],
                    "site": row["site"],
                    "issue_type": row["issue_type"],
                    "affected_subjects": json.loads(row["affected_subjects_json"]),
                    "occurrences": row["occurrences"],
                    "first_occurrence": row["first_occurrence"],
                    "latest_occurrence": row["latest_occurrence"],
                    "protocol_version": row["protocol_version"],
                    "related_records": json.loads(row["related_records_json"]),
                    "related_queries": json.loads(row["related_queries_json"]),
                    "related_escalations": json.loads(row["related_escalations_json"]),
                    "explanation": row["explanation"],
                    "graph_evidence": json.loads(row["graph_evidence_json"]),
                    "status": row["status"]
                }
                for row in c.fetchall()
            ]

    # --- Protocol Versions ---
    def upsert_protocol_version(self, version: int, effective_cut: int, title: str, rules: Dict[str, Any], amendment_summary: Optional[str] = None):
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT OR REPLACE INTO protocol_versions (
                version, effective_cut, title, rules_json, created_at, amendment_summary
            ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                version,
                effective_cut,
                title,
                json.dumps(rules),
                datetime.utcnow().isoformat(),
                amendment_summary
            ))
            conn.commit()

    def get_protocol_version(self, version: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM protocol_versions WHERE version = ?", (version,))
            row = c.fetchone()
            if not row:
                return None
            return {
                "version": row["version"],
                "effective_cut": row["effective_cut"],
                "title": row["title"],
                "rules": json.loads(row["rules_json"]),
                "created_at": row["created_at"],
                "amendment_summary": row["amendment_summary"]
            }

    def get_all_protocol_versions(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM protocol_versions ORDER BY version ASC")
            return [
                {
                    "version": row["version"],
                    "effective_cut": row["effective_cut"],
                    "title": row["title"],
                    "rules": json.loads(row["rules_json"]),
                    "created_at": row["created_at"],
                    "amendment_summary": row["amendment_summary"]
                }
                for row in c.fetchall()
            ]

    # --- Cycle Summary Persistence ---
    def record_cycle_run(self, cut: int, protocol_version: int, summary: Dict[str, Any]) -> int:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("""
            INSERT INTO cycle_runs (cut, protocol_version, started_at, completed_at, status, summary_json)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (
                cut,
                protocol_version,
                summary.get("started_at", datetime.utcnow().isoformat()),
                datetime.utcnow().isoformat(),
                "COMPLETED",
                json.dumps(summary)
            ))
            conn.commit()
            return c.lastrowid

    def get_cycle_report(self, cut: int) -> Optional[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM cycle_runs WHERE cut = ? ORDER BY id DESC LIMIT 1", (cut,))
            row = c.fetchone()
            if not row:
                return None
            return json.loads(row["summary_json"])

    def get_all_cycle_reports(self) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM cycle_runs ORDER BY id ASC")
            return [json.loads(row["summary_json"]) for row in c.fetchall()]
