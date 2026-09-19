/**
 * API Client for Clinical Trial Review System
 */

import {
  CycleReport,
  Escalation,
  QueryRecord,
  TraceEntry,
  RiskSignal,
  CytoscapeGraphData,
  Finding,
  Deviation
} from "./types";

const BASE_URL = ""; // Relative proxy routes through Express port 3000

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${BASE_URL}/health`);
  if (!res.ok) throw new Error("Health check failed");
  return res.json();
}

export async function runCycle(cut: number, protocolVersion: number): Promise<CycleReport> {
  const res = await fetch(`${BASE_URL}/cycles/run`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cut, protocol_version: protocolVersion })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Failed to run cycle" }));
    throw new Error(err.error || "Failed to run cycle");
  }
  return res.json();
}

export async function fetchCycleReport(cut: number): Promise<CycleReport> {
  const res = await fetch(`${BASE_URL}/cycles/${cut}/report`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Cycle report not found" }));
    throw new Error(err.error || "Cycle report not found");
  }
  return res.json();
}

export async function fetchEscalations(status?: string): Promise<Escalation[]> {
  const url = status ? `${BASE_URL}/escalations?status=${encodeURIComponent(status)}` : `${BASE_URL}/escalations`;
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch escalations");
  const data = await res.json();
  return data.escalations || [];
}

export async function postEscalationDecision(
  escalationId: string,
  decision: "APPROVED" | "REJECTED" | "CLARIFY",
  payload: { reason?: string; question?: string; actor?: string }
): Promise<{ decision: string; escalation: Escalation; message: string; clarification?: any }> {
  const res = await fetch(`${BASE_URL}/escalations/${escalationId}/decision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ decision, ...payload })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Decision failed" }));
    throw new Error(err.error || "Decision failed");
  }
  return res.json();
}

export async function fetchQueries(subject?: string, site?: string): Promise<QueryRecord[]> {
  let url = `${BASE_URL}/queries`;
  const params: string[] = [];
  if (subject) params.push(`subject=${encodeURIComponent(subject)}`);
  if (site) params.push(`site=${encodeURIComponent(site)}`);
  if (params.length > 0) url += `?${params.join("&")}`;

  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch queries");
  const data = await res.json();
  return data.queries || [];
}

export async function fetchTrace(filters?: {
  cycle?: number;
  node?: string;
  subject?: string;
  site?: string;
}): Promise<TraceEntry[]> {
  let url = `${BASE_URL}/trace`;
  if (filters) {
    const params: string[] = [];
    if (filters.cycle !== undefined) params.push(`cycle=${filters.cycle}`);
    if (filters.node) params.push(`node=${encodeURIComponent(filters.node)}`);
    if (filters.subject) params.push(`subject=${encodeURIComponent(filters.subject)}`);
    if (filters.site) params.push(`site=${encodeURIComponent(filters.site)}`);
    if (params.length > 0) url += `?${params.join("&")}`;
  }
  const res = await fetch(url);
  if (!res.ok) throw new Error("Failed to fetch trace log");
  const data = await res.json();
  return data.trace || [];
}

export async function fetchKnowledgeGraph(): Promise<CytoscapeGraphData> {
  const res = await fetch(`${BASE_URL}/knowledge-graph`);
  if (!res.ok) throw new Error("Failed to fetch Knowledge Graph");
  return res.json();
}

export async function fetchSubjectGraph(subjectId: string): Promise<any> {
  const res = await fetch(`${BASE_URL}/knowledge-graph/subject/${encodeURIComponent(subjectId)}`);
  if (!res.ok) throw new Error(`Subject ${subjectId} not found`);
  return res.json();
}

export async function askKnowledgeGraphClarify(
  subjectId: string,
  question: string
): Promise<{ answer: string; evidence: any[]; search_log: string[] }> {
  const res = await fetch(`${BASE_URL}/knowledge-graph/clarify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject_id: subjectId, question })
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "CLARIFY search failed" }));
    throw new Error(err.error || "CLARIFY search failed");
  }
  return res.json();
}

export async function fetchRiskRadar(): Promise<RiskSignal[]> {
  const res = await fetch(`${BASE_URL}/risk-radar`);
  if (!res.ok) throw new Error("Failed to fetch Risk Radar");
  const data = await res.json();
  return data.risk_signals || [];
}

export async function fetchProtocol(version: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/protocol/${version}`);
  if (!res.ok) throw new Error(`Protocol v${version} not found`);
  return res.json();
}

export async function fetchProtocolDiff(v1: number, v2: number, cut: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/protocol/diff?v1=${v1}&v2=${v2}&cut=${cut}`);
  if (!res.ok) throw new Error("Failed to fetch protocol diff");
  return res.json();
}

export async function amendProtocol(cut: number, newVersion: number): Promise<any> {
  const res = await fetch(`${BASE_URL}/protocol/amend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cut, new_version: newVersion })
  });
  if (!res.ok) throw new Error("Failed to amend protocol");
  return res.json();
}
