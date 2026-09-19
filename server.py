"""Problem 2: Clinical Trial Monitor Backend REST API Server

Implements all required Section 39 endpoints:
- GET /health
- POST /cycles/run
- GET /cycles/{cut}
- GET /cycles/{cut}/report
- GET /escalations
- GET /escalations/{id}
- POST /escalations/{id}/decision
- GET /queries
- GET /queries/{id}
- GET /trace
- GET /knowledge-graph
- GET /knowledge-graph/subject/{subject_id}
- GET /risk-radar
- GET /protocol/{version}
- POST /protocol/amend
- GET /protocol/diff
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import urllib.parse
import sys
import os
from typing import Dict, Any

from stage1.atlas import Atlas
from stage2.crew import ReviewCrew
from stage2.memory import PersistentMemory
from stage2.knowledge_graph import ClinicalKnowledgeGraph

# Global persistent instances
DB_PATH = "clinical_monitor.db"
crew = ReviewCrew(db_path=DB_PATH)


class MonitorAPIHandler(BaseHTTPRequestHandler):
    def _send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Team-Key")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Team-Key")
        self.end_headers()

    def _parse_body(self) -> Dict[str, Any]:
        content_len = int(self.headers.get("Content-Length", 0))
        if content_len > 0:
            raw = self.rfile.read(content_len).decode("utf-8")
            try:
                return json.loads(raw)
            except Exception:
                return {}
        return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Health
        if path in ["/health", "/api/health"]:
            self._send_json({"status": "ok", "service": "Clinical Trial Monitor API", "version": "2.0"})
            return

        # 2. Trace
        if path in ["/trace", "/api/trace"]:
            cycle = int(query["cycle"][0]) if "cycle" in query else None
            node = query.get("node", [None])[0]
            subj = query.get("subject", [None])[0]
            site = query.get("site", [None])[0]
            traces = crew.memory.get_trace(cycle=cycle, node=node, subject=subj, site=site)
            self._send_json({"trace": traces, "count": len(traces)})
            return

        # 3. Queries List
        if path in ["/queries", "/api/queries"]:
            subj = query.get("subject", [None])[0]
            site = query.get("site", [None])[0]
            queries = crew.memory.get_queries(subject=subj, site=site)
            self._send_json({"queries": queries, "count": len(queries)})
            return

        # 4. Query Detail: /queries/{id}
        if path.startswith("/queries/") or path.startswith("/api/queries/"):
            parts = path.split("/")
            qid = parts[-1]
            q = crew.memory.get_query(qid)
            if q:
                self._send_json({"query": q})
            else:
                self._send_json({"error": f"Query {qid} not found"}, status=404)
            return

        # 5. Escalations List
        if path in ["/escalations", "/api/escalations"]:
            status = query.get("status", [None])[0]
            subj = query.get("subject", [None])[0]
            escalations = crew.memory.get_escalations(status=status, subject=subj)
            self._send_json({"escalations": escalations, "count": len(escalations)})
            return

        # 6. Escalation Detail: /escalations/{id}
        if (path.startswith("/escalations/") or path.startswith("/api/escalations/")) and not path.endswith("/decision"):
            parts = path.split("/")
            esc_id = parts[-1]
            esc = crew.memory.get_escalation(esc_id)
            if esc:
                self._send_json({"escalation": esc})
            else:
                self._send_json({"error": f"Escalation {esc_id} not found"}, status=404)
            return

        # 7. Cycle Report: /cycles/{cut}/report or /cycles/{cut}
        if "/cycles/" in path:
            parts = path.split("/")
            # e.g. ["", "cycles", "1", "report"] or ["", "api", "cycles", "1"]
            cut_idx = 2 if parts[1] == "cycles" else 3
            try:
                cut_num = int(parts[cut_idx])
                rep = crew.memory.get_cycle_report(cut_num)
                if rep:
                    self._send_json(rep)
                else:
                    self._send_json({"error": f"No cycle run report found for cut {cut_num}. Run cycle first."}, status=404)
                return
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
                return

        # 8. All Cycles List
        if path in ["/cycles", "/api/cycles"]:
            reps = crew.memory.get_all_cycle_reports()
            self._send_json({"cycle_reports": reps, "count": len(reps)})
            return

        # 9. Knowledge Graph: full or subject-specific
        if path in ["/knowledge-graph", "/api/knowledge-graph"]:
            data = crew.kg.to_cytoscape_json()
            self._send_json(data)
            return

        if "/knowledge-graph/subject/" in path:
            subj_id = path.split("/")[-1]
            subj_node = crew.kg.get_subject(subj_id)
            if subj_node:
                labs = crew.kg.get_subject_labs(subj_id)
                aes = crew.kg.get_subject_adverse_events(subj_id)
                doses = crew.kg.get_subject_doses(subj_id)
                meds = crew.kg.get_subject_medications(subj_id)
                devs = crew.kg.get_subject_deviations(subj_id)
                queries = crew.kg.get_subject_queries(subj_id)
                escs = crew.kg.get_subject_escalations(subj_id)
                self._send_json({
                    "subject": subj_node,
                    "labs": labs,
                    "adverse_events": aes,
                    "doses": doses,
                    "medications": meds,
                    "deviations": devs,
                    "queries": queries,
                    "escalations": escs
                })
            else:
                self._send_json({"error": f"Subject {subj_id} not found in Knowledge Graph"}, status=404)
            return

        # 10. Risk Radar
        if path in ["/risk-radar", "/api/risk-radar"]:
            signals = crew.memory.get_risk_signals()
            self._send_json({"risk_signals": signals, "count": len(signals)})
            return

        # 11. Protocol Version: /protocol/{version}
        if path.startswith("/protocol/") or path.startswith("/api/protocol/"):
            parts = path.split("/")
            if parts[-1] == "diff":
                v1 = int(query.get("v1", [1])[0])
                v2 = int(query.get("v2", [2])[0])
                cut = int(query.get("cut", [1])[0])
                raw_data = crew.atlas.get_raw_data(cut)
                diff = crew.protocol_engine.compute_protocol_diff(v1, v2, raw_data, cut)
                self._send_json(diff)
                return
            try:
                v = int(parts[-1])
                proto = crew.protocol_engine.get_protocol(v)
                self._send_json(proto)
                return
            except Exception:
                all_protos = crew.memory.get_all_protocol_versions()
                self._send_json({"protocol_versions": all_protos})
                return

        # 12. Deviations
        if path in ["/deviations", "/api/deviations"]:
            pv = int(query["protocol_version"][0]) if "protocol_version" in query else None
            devs = crew.memory.get_deviations(protocol_version=pv)
            self._send_json({"deviations": devs, "count": len(devs)})
            return

        # 13. Findings
        if path in ["/findings", "/api/findings"]:
            cut = int(query["cut"][0]) if "cut" in query else None
            findings = crew.memory.get_findings(cut=cut)
            self._send_json({"findings": findings, "count": len(findings)})
            return

        self._send_json({"error": f"Path '{path}' not found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        body = self._parse_body()

        # 1. Run Cycle: POST /cycles/run
        if path in ["/cycles/run", "/api/cycles/run"]:
            cut = int(body.get("cut", 1))
            pv = int(body.get("protocol_version", 1))
            try:
                report = crew.run_cycle(cut=cut, protocol_version=pv)
                self._send_json(report)
            except Exception as e:
                self._send_json({"error": str(e)}, status=500)
            return

        # 2. Escalation Decision: POST /escalations/{id}/decision
        if "/decision" in path:
            # Extract id
            parts = path.split("/")
            # e.g. ["", "escalations", "ESC-1", "decision"]
            esc_id = parts[-2]
            decision = body.get("decision", "")
            reason = body.get("reason")
            question = body.get("question")
            actor = body.get("actor", "Medical Monitor (Human)")
            try:
                res = crew.human_gate_node.process_decision(
                    escalation_id=esc_id,
                    decision=decision,
                    reason=reason,
                    question=question,
                    actor=actor
                )
                self._send_json(res)
            except Exception as e:
                self._send_json({"error": str(e)}, status=400)
            return

        # 3. Knowledge Graph Clarify Search: POST /knowledge-graph/clarify
        if path in ["/knowledge-graph/clarify", "/api/knowledge-graph/clarify"]:
            subject_id = body.get("subject_id", "")
            question = body.get("question", "")
            if not subject_id or not question:
                self._send_json({"error": "subject_id and question are required"}, status=400)
                return
            ans = crew.kg.answer_clarify(question=question, subject_id=subject_id)
            self._send_json(ans)
            return

        # 4. Protocol Amendment: POST /protocol/amend
        if path in ["/protocol/amend", "/api/protocol/amend"]:
            cut = int(body.get("cut", 2))
            new_version = int(body.get("new_version", 2))
            # Run compliance re-evaluation
            raw_data = crew.atlas.get_raw_data(cut)
            diff = crew.protocol_engine.compute_protocol_diff(1, new_version, raw_data, cut)
            # Re-evaluate and persist new deviations under v2
            comp_res = crew.compliance_node.run(raw_data=raw_data, cut=cut, protocol_version=new_version)
            crew.memory.write_trace(
                cycle=cut,
                node="compliance",
                decision=f"PROTOCOL_AMENDMENT_V{new_version}_APPLIED",
                subject=None,
                site=None,
                evidence=diff,
                protocol_version=new_version,
                actor="protocol_amendment_system"
            )
            self._send_json({
                "message": f"Protocol amended to v{new_version}. Compliance evaluated.",
                "diff": diff,
                "new_deviations_persisted": comp_res["new_deviations"]
            })
            return

        self._send_json({"error": f"POST endpoint '{path}' not found"}, status=404)


def run(port: int = 8000):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, MonitorAPIHandler)
    print(f"Clinical Trial Monitor API server listening on port {port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()


if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])
    elif "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = int(sys.argv[idx + 1])
    run(port)
