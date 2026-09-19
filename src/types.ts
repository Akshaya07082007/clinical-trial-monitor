/**
 * TypeScript Type Definitions for Clinical Trial Review System
 */

export interface SourceEvidence {
  domain?: string;
  subject?: string;
  site?: string;
  sequence?: number;
  aeterm?: string;
  aestdtc?: string;
  aeendtc?: string;
  aeshosp?: string;
  aeser?: string;
  source_doc?: string;
  comment?: string;
  [key: string]: any;
}

export interface Finding {
  finding_id: string;
  cut: number;
  finding_code: string;
  subject_id: string;
  site: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  rationale: string;
  domain: string;
  sequence: number;
  source_evidence: SourceEvidence;
  classification: "SAFETY ISSUE" | "DATA QUALITY ISSUE" | "COMPLIANCE ISSUE" | "MONITORING ONLY" | "PENDING";
  status: "OPEN" | "RESOLVED" | "HELD";
  created_at?: string;
}

export interface ClarificationEntry {
  timestamp: string;
  question: string;
  actor: string;
  answer: string;
  evidence_found?: any[];
  search_log?: string[];
}

export interface Escalation {
  escalation_id: string;
  finding_code: string;
  subject: string;
  site: string;
  severity: "LOW" | "MEDIUM" | "HIGH";
  summary: string;
  evidence: SourceEvidence;
  protocol_section: string;
  protocol_version: number;
  alternatives: string[];
  required_action: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  rejection_reason?: string;
  execution_details?: string;
  executed_at?: string;
  clarification_history?: ClarificationEntry[];
  created_cycle: number;
  created_at?: string;
  updated_at?: string;
}

export interface QueryRecord {
  query_id: string;
  subject: string;
  site: string;
  domain: string;
  sequence: number;
  cut: number;
  issue: string;
  requested_action: string;
  status: "OPEN" | "ON HOLD" | "ANSWERED" | "CLOSED";
  evidence: SourceEvidence;
  created_cycle: number;
  attempt_count: number;
  last_response?: string;
  external_sync_status?: string;
  external_sync_error?: string;
  created_at?: string;
}

export interface Deviation {
  deviation_id: string;
  subject: string;
  site: string;
  deviation_type: string;
  protocol_version: number;
  cut: number;
  explanation: string;
  evidence: SourceEvidence;
  status: string;
  created_at?: string;
}

export interface TraceEntry {
  trace_id: number;
  timestamp: string;
  cycle: number;
  node: "detect" | "medical_review" | "data_manager" | "compliance" | "human_gate" | "execute" | string;
  decision: string;
  subject?: string | null;
  site?: string | null;
  evidence?: any;
  protocol_version: number;
  query_id?: string | null;
  escalation_id?: string | null;
  actor: string;
}

export interface RiskSignal {
  signal_id: string;
  site: string;
  issue_type: string;
  affected_subjects: string[];
  occurrences: number;
  first_occurrence: string;
  latest_occurrence: string;
  protocol_version: number;
  related_records: string[];
  related_queries: string[];
  related_escalations: string[];
  explanation: string;
  graph_evidence: any;
  status: "EARLY WARNING" | "MONITOR" | "REQUIRES REVIEW" | "RESOLVED";
}

export interface CycleReport {
  cut: number;
  protocol_version: number;
  cycle_status: string;
  timestamp: string;
  started_at?: string;
  nodes: {
    name: string;
    status: string;
    code: string;
  }[];
  metrics: {
    total_findings: number;
    safety_findings: number;
    data_findings: number;
    compliance_findings: number;
    monitoring_findings: number;
    pending_escalations: number;
    approved_escalations: number;
    rejected_escalations: number;
    open_queries: number;
    compliance_deviations: number;
    executed_actions: number;
    risk_signals: number;
  };
  findings_summary: Finding[];
  escalations: Escalation[];
  open_queries: QueryRecord[];
  deviations: Deviation[];
  executed_actions: any[];
  new_queries_created?: number;
  queries_deduplicated?: number;
  new_escalations_created?: number;
  risk_signals_detected?: number;
}

export interface GraphNode {
  data: {
    id: string;
    label: string;
    type: "SUBJECT" | "SITE" | "VISIT" | "LAB" | "AE" | "EXPOSURE" | "MED" | "MH" | "DS" | "DEVIATION" | "QUERY" | "ESCALATION" | "PROTOCOL";
    details?: any;
  };
}

export interface GraphEdge {
  data: {
    source: string;
    target: string;
    label: string;
  };
}

export interface CytoscapeGraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface ProtocolRule {
  version: number;
  amendment_date: string;
  title: string;
  visit_windows: Record<string, { target_day: number; window_days: number }>;
  prohibited_meds: string[];
  renal_egfr_min: number;
  sae_reporting_hours: number;
}
