"""Stage 2: Core Data Models and Types for Clinical Trial Monitoring."""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json


class FindingModel:
    def __init__(
        self,
        finding_id: str,
        finding_code: str,
        subject_id: str,
        site: str,
        severity: str,
        rationale: str,
        domain: str,
        sequence: int,
        source_evidence: Dict[str, Any],
        cut: int,
        classification: str = "PENDING",  # SAFETY ISSUE, DATA QUALITY ISSUE, COMPLIANCE ISSUE, MONITORING ONLY
        status: str = "OPEN"
    ):
        self.finding_id = finding_id
        self.finding_code = finding_code
        self.subject_id = subject_id
        self.site = site
        self.severity = severity
        self.rationale = rationale
        self.domain = domain
        self.sequence = sequence
        self.source_evidence = source_evidence
        self.cut = cut
        self.classification = classification
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "finding_code": self.finding_code,
            "subject_id": self.subject_id,
            "site": self.site,
            "severity": self.severity,
            "rationale": self.rationale,
            "domain": self.domain,
            "sequence": self.sequence,
            "source_evidence": self.source_evidence,
            "cut": self.cut,
            "classification": self.classification,
            "status": self.status
        }


class QueryModel:
    def __init__(
        self,
        query_id: str,
        subject: str,
        site: str,
        domain: str,
        sequence: int,
        cut: int,
        issue: str,
        requested_action: str,
        status: str,  # OPEN, ANSWERED, ON HOLD, RESOLVED
        evidence: Dict[str, Any],
        created_cycle: int,
        attempt_count: int = 1,
        last_response: Optional[str] = None,
        created_at: Optional[str] = None,
        external_sync_status: str = "LOCAL_ONLY",
        external_sync_error: Optional[str] = None
    ):
        self.query_id = query_id
        self.subject = subject
        self.site = site
        self.domain = domain
        self.sequence = sequence
        self.cut = cut
        self.issue = issue
        self.requested_action = requested_action
        self.status = status
        self.evidence = evidence
        self.created_cycle = created_cycle
        self.attempt_count = attempt_count
        self.last_response = last_response
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.external_sync_status = external_sync_status
        self.external_sync_error = external_sync_error

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_id": self.query_id,
            "subject": self.subject,
            "site": self.site,
            "domain": self.domain,
            "sequence": self.sequence,
            "cut": self.cut,
            "issue": self.issue,
            "requested_action": self.requested_action,
            "status": self.status,
            "evidence": self.evidence,
            "created_cycle": self.created_cycle,
            "attempt_count": self.attempt_count,
            "last_response": self.last_response,
            "created_at": self.created_at,
            "external_sync_status": self.external_sync_status,
            "external_sync_error": self.external_sync_error
        }


class EscalationModel:
    def __init__(
        self,
        escalation_id: str,
        finding_code: str,
        subject: str,
        site: str,
        severity: str,
        summary: str,
        evidence: Dict[str, Any],
        protocol_section: str,
        protocol_version: int,
        alternatives_considered: List[str],
        required_action: str,
        status: str = "PENDING",  # PENDING, APPROVED, REJECTED, CLARIFYING, EXECUTED
        rejection_reason: Optional[str] = None,
        clarification_history: Optional[List[Dict[str, Any]]] = None,
        created_cycle: int = 1,
        executed_at: Optional[str] = None,
        execution_details: Optional[str] = None
    ):
        self.escalation_id = escalation_id
        self.finding_code = finding_code
        self.subject = subject
        self.site = site
        self.severity = severity
        self.summary = summary
        self.evidence = evidence
        self.protocol_section = protocol_section
        self.protocol_version = protocol_version
        self.alternatives_considered = alternatives_considered or []
        self.required_action = required_action
        self.status = status
        self.rejection_reason = rejection_reason
        self.clarification_history = clarification_history or []
        self.created_cycle = created_cycle
        self.executed_at = executed_at
        self.execution_details = execution_details

    def to_dict(self) -> Dict[str, Any]:
        return {
            "escalation_id": self.escalation_id,
            "finding_code": self.finding_code,
            "subject": self.subject,
            "site": self.site,
            "severity": self.severity,
            "summary": self.summary,
            "evidence": self.evidence,
            "protocol_section": self.protocol_section,
            "protocol_version": self.protocol_version,
            "alternatives": self.alternatives_considered,
            "required_action": self.required_action,
            "status": self.status,
            "rejection_reason": self.rejection_reason,
            "clarification_history": self.clarification_history,
            "created_cycle": self.created_cycle,
            "executed_at": self.executed_at,
            "execution_details": self.execution_details
        }


class DeviationModel:
    def __init__(
        self,
        deviation_id: str,
        subject: str,
        site: str,
        deviation_type: str,
        protocol_version: int,
        evidence: Dict[str, Any],
        explanation: str,
        status: str = "CONFIRMED",
        created_cycle: int = 1
    ):
        self.deviation_id = deviation_id
        self.subject = subject
        self.site = site
        self.deviation_type = deviation_type
        self.protocol_version = protocol_version
        self.evidence = evidence
        self.explanation = explanation
        self.status = status
        self.created_cycle = created_cycle

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deviation_id": self.deviation_id,
            "subject": self.subject,
            "site": self.site,
            "deviation_type": self.deviation_type,
            "protocol_version": self.protocol_version,
            "evidence": self.evidence,
            "explanation": self.explanation,
            "status": self.status,
            "created_cycle": self.created_cycle
        }


class TraceEntryModel:
    def __init__(
        self,
        trace_id: str,
        timestamp: str,
        cycle: int,
        node: str,  # detect, medical_review, data_manager, compliance, human_gate, execute
        decision: str,
        subject: Optional[str],
        site: Optional[str],
        evidence: Any,
        protocol_version: int,
        query_id: Optional[str] = None,
        escalation_id: Optional[str] = None,
        actor: str = "automated"
    ):
        self.trace_id = trace_id
        self.timestamp = timestamp
        self.cycle = cycle
        self.node = node
        self.decision = decision
        self.subject = subject
        self.site = site
        self.evidence = evidence
        self.protocol_version = protocol_version
        self.query_id = query_id
        self.escalation_id = escalation_id
        self.actor = actor

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "timestamp": self.timestamp,
            "cycle": self.cycle,
            "node": self.node,
            "decision": self.decision,
            "subject": self.subject,
            "site": self.site,
            "evidence": self.evidence,
            "protocol_version": self.protocol_version,
            "query_id": self.query_id,
            "escalation_id": self.escalation_id,
            "actor": self.actor
        }


class RiskSignalModel:
    def __init__(
        self,
        signal_id: str,
        site: str,
        issue_type: str,
        affected_subjects: List[str],
        occurrences: int,
        first_occurrence: str,
        latest_occurrence: str,
        protocol_version: int,
        related_records: List[str],
        related_queries: List[str],
        related_escalations: List[str],
        explanation: str,
        graph_evidence: Dict[str, Any],
        status: str = "EARLY WARNING"  # EARLY WARNING, MONITOR, REQUIRES REVIEW, RESOLVED
    ):
        self.signal_id = signal_id
        self.site = site
        self.issue_type = issue_type
        self.affected_subjects = affected_subjects
        self.occurrences = occurrences
        self.first_occurrence = first_occurrence
        self.latest_occurrence = latest_occurrence
        self.protocol_version = protocol_version
        self.related_records = related_records
        self.related_queries = related_queries
        self.related_escalations = related_escalations
        self.explanation = explanation
        self.graph_evidence = graph_evidence
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "site": self.site,
            "issue_type": self.issue_type,
            "affected_subjects": self.affected_subjects,
            "occurrences": self.occurrences,
            "first_occurrence": self.first_occurrence,
            "latest_occurrence": self.latest_occurrence,
            "protocol_version": self.protocol_version,
            "related_records": self.related_records,
            "related_queries": self.related_queries,
            "related_escalations": self.related_escalations,
            "explanation": self.explanation,
            "graph_evidence": self.graph_evidence,
            "status": self.status
        }
