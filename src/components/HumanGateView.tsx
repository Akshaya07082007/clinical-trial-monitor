import React, { useState } from "react";
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  HelpCircle,
  AlertTriangle,
  FileText,
  Clock,
  Send,
  Search,
  Sparkles,
  ChevronRight,
  Database
} from "lucide-react";
import { Escalation, ClarificationEntry } from "../types";

interface HumanGateViewProps {
  escalations: Escalation[];
  onDecision: (
    escalationId: string,
    decision: "APPROVED" | "REJECTED" | "CLARIFY",
    payload: { reason?: string; question?: string; actor?: string }
  ) => Promise<void>;
  isLoading: boolean;
  onOpenGraphSubject?: (subjectId: string) => void;
}

export const HumanGateView: React.FC<HumanGateViewProps> = ({
  escalations,
  onDecision,
  isLoading,
  onOpenGraphSubject
}) => {
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectionReason, setRejectionReason] = useState("");
  const [clarifyingId, setClarifyingId] = useState<string | null>(null);
  const [clarifyQuestion, setClarifyQuestion] = useState(
    "What was the baseline screening ALT/AST and are there concurrent hepatotoxic medications?"
  );

  const pendingEscalations = escalations.filter((e) => e.status === "PENDING");
  const historyEscalations = escalations.filter((e) => e.status !== "PENDING");

  const handleApprove = async (id: string) => {
    await onDecision(id, "APPROVED", { actor: "Dr. Eleanor Vance, Lead Medical Monitor" });
  };

  const handleRejectSubmit = async (id: string) => {
    if (!rejectionReason.trim()) {
      alert("A clinical justification reason is required when rejecting an escalation.");
      return;
    }
    await onDecision(id, "REJECTED", {
      reason: rejectionReason,
      actor: "Dr. Eleanor Vance, Lead Medical Monitor"
    });
    setRejectingId(null);
    setRejectionReason("");
  };

  const handleClarifySubmit = async (id: string) => {
    if (!clarifyQuestion.trim()) {
      alert("Please enter a question to clarify with the Knowledge Graph.");
      return;
    }
    await onDecision(id, "CLARIFY", {
      question: clarifyQuestion,
      actor: "Dr. Eleanor Vance, Lead Medical Monitor"
    });
    setClarifyingId(null);
  };

  return (
    <div className="space-y-6">
      {/* Human Gate Banner / Purpose */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-rose-500/10 border border-rose-500/20 rounded-lg text-rose-400">
              <ShieldAlert className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Node 5: Human Gate (Medical Monitor Authority)
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-rose-500/20 text-rose-300 border border-rose-500/30">
                  Mandatory Human-in-the-Loop
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed max-w-3xl">
                The Medical Monitor possesses final decision authority. Evaluates critical clinical findings
                (such as hospital admission SAE miscodings), issues binding regulatory escalations, downgrades
                unsubstantiated events to monitoring with permanent deduplication, or interrogates the Knowledge
                Graph via <strong>CLARIFY</strong>.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="bg-slate-800/80 px-4 py-2 rounded-lg border border-slate-700 text-center">
              <span className="block text-xl font-bold text-white">
                {pendingEscalations.length}
              </span>
              <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
                Awaiting Gate Review
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Pending Escalations Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
            <span>Pending Medical Monitor Reviews</span>
            <span className="px-2 py-0.5 bg-rose-500/20 text-rose-300 text-xs rounded-full font-mono">
              {pendingEscalations.length}
            </span>
          </h3>
        </div>

        {pendingEscalations.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-medium text-slate-300">No Escalations Awaiting Review</p>
            <p className="text-xs text-slate-500 mt-1">
              All detected safety events have been reviewed, approved, or downgraded to monitoring.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {pendingEscalations.map((esc) => {
              const isRejecting = rejectingId === esc.escalation_id;
              const isClarifying = clarifyingId === esc.escalation_id;

              return (
                <div
                  key={esc.escalation_id}
                  className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-sm"
                >
                  {/* Escalation Header */}
                  <div className="bg-slate-800/60 px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2.5 py-0.5 rounded">
                        {esc.escalation_id}
                      </span>
                      <span className="text-xs font-semibold text-slate-200">
                        {esc.finding_code}
                      </span>
                      <span className="text-xs text-slate-400">•</span>
                      <span className="text-xs font-mono text-slate-300">
                        Subject: <strong>{esc.subject}</strong>
                      </span>
                      <span className="text-xs text-slate-400">•</span>
                      <span className="text-xs text-slate-300">
                        Site: <strong>{esc.site}</strong>
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-rose-900/40 text-rose-300 border border-rose-700/50">
                        SEVERITY: {esc.severity}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[11px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
                        Cut {esc.created_cycle}
                      </span>
                      {onOpenGraphSubject && (
                        <button
                          onClick={() => onOpenGraphSubject(esc.subject)}
                          className="px-2 py-0.5 text-[11px] rounded bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 flex items-center gap-1 cursor-pointer transition-colors"
                        >
                          <Database className="w-3 h-3" />
                          <span>Inspect in Graph</span>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Body Details */}
                  <div className="p-5 space-y-4 text-xs">
                    {/* Summary */}
                    <div>
                      <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px] block mb-1">
                        Clinical Finding Summary
                      </span>
                      <p className="text-slate-200 text-sm leading-relaxed bg-slate-800/30 p-3 rounded-lg border border-slate-800">
                        {esc.summary}
                      </p>
                    </div>

                    {/* Evidence & Protocol Rules */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Evidence Card */}
                      <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800">
                        <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px] block mb-2 flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-blue-400" />
                          Source SDTM Evidence
                        </span>
                        <div className="space-y-1.5 font-mono text-[11px]">
                          <div className="flex justify-between">
                            <span className="text-slate-500">Domain:</span>
                            <span className="text-slate-300">{esc.evidence.domain || "AE"}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Adverse Event (AETERM):</span>
                            <span className="text-rose-400 font-semibold">{esc.evidence.aeterm}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Hospitalized (AESHOSP):</span>
                            <span className="text-amber-300 font-bold bg-amber-500/20 px-1 rounded">
                              {esc.evidence.aeshosp} (Hospital Inpatient)
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Serious Flag (AESER):</span>
                            <span className="text-red-400 font-bold bg-red-500/20 px-1 rounded">
                              {esc.evidence.aeser} (Miscoded as 'N'!)
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-slate-500">Event Dates:</span>
                            <span className="text-slate-300">
                              {esc.evidence.aestdtc} to {esc.evidence.aeendtc || "Ongoing"}
                            </span>
                          </div>
                          <div className="flex justify-between border-t border-slate-800/80 pt-1 mt-1">
                            <span className="text-slate-500">Source Document:</span>
                            <span className="text-slate-400">{esc.evidence.source_doc}</span>
                          </div>
                        </div>
                      </div>

                      {/* Protocol & Required Action */}
                      <div className="bg-slate-950/60 p-3.5 rounded-lg border border-slate-800 space-y-2.5">
                        <div>
                          <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px] block mb-1">
                            Protocol Mandate Citation
                          </span>
                          <span className="text-indigo-300 font-medium block">
                            {esc.protocol_section}
                          </span>
                        </div>

                        <div>
                          <span className="font-semibold text-slate-300 uppercase tracking-wider text-[10px] block mb-1">
                            Required Action (Upon Approval)
                          </span>
                          <p className="text-slate-300 leading-normal">
                            {esc.required_action}
                          </p>
                        </div>

                        <div>
                          <span className="font-semibold text-slate-400 uppercase tracking-wider text-[10px] block mb-1">
                            Alternatives Considered & Weighed
                          </span>
                          <ul className="list-disc list-inside text-slate-400 space-y-0.5">
                            {esc.alternatives.map((alt, idx) => (
                              <li key={idx}>{alt}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>

                    {/* Clarification History Display (if CLARIFY was previously run) */}
                    {esc.clarification_history && esc.clarification_history.length > 0 && (
                      <div className="bg-indigo-950/30 border border-indigo-500/30 rounded-lg p-3.5 space-y-2">
                        <div className="flex items-center gap-1.5 text-indigo-300 font-semibold text-xs">
                          <Sparkles className="w-4 h-4 text-indigo-400" />
                          <span>Knowledge Graph CLARIFY Synthesized Response</span>
                        </div>
                        {esc.clarification_history.map((ch, idx) => (
                          <div key={idx} className="space-y-2 text-xs">
                            <div className="bg-slate-900/60 p-2.5 rounded border border-indigo-500/20">
                              <span className="text-indigo-400 font-medium block mb-1">
                                Q: "{ch.question}"
                              </span>
                              <p className="text-slate-200 font-medium leading-relaxed">
                                {ch.answer}
                              </p>
                            </div>

                            {/* Evidence details */}
                            {ch.evidence_found && ch.evidence_found.length > 0 && (
                              <div className="text-[11px] font-mono text-slate-400 pl-2 border-l-2 border-indigo-500/40 space-y-1">
                                <span className="text-slate-500 block uppercase font-bold text-[10px]">
                                  Graph Nodes Traversed & Verified:
                                </span>
                                {ch.evidence_found.map((ev, i) => (
                                  <div key={i} className="flex gap-2">
                                    <span className="text-indigo-300 font-semibold">{ev.category}:</span>
                                    <span className="text-slate-300">{ev.detail || ev.name}</span>
                                    {ev.value && <span className="text-emerald-300">({ev.value})</span>}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Action Decision Controls (APPROVE / REJECT / CLARIFY) */}
                    <div className="pt-2 border-t border-slate-800">
                      {!isRejecting && !isClarifying && (
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <span className="text-xs text-slate-400">
                            Select Human Monitor Decision:
                          </span>
                          <div className="flex items-center gap-2">
                            {/* APPROVE */}
                            <button
                              onClick={() => handleApprove(esc.escalation_id)}
                              disabled={isLoading}
                              className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer active:scale-98"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                              <span>APPROVE</span>
                            </button>

                            {/* REJECT */}
                            <button
                              onClick={() => {
                                setRejectingId(esc.escalation_id);
                                setClarifyingId(null);
                              }}
                              disabled={isLoading}
                              className="px-4 py-2 bg-rose-600/20 hover:bg-rose-600/30 text-rose-300 border border-rose-500/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all cursor-pointer"
                            >
                              <XCircle className="w-4 h-4" />
                              <span>REJECT</span>
                            </button>

                            {/* CLARIFY */}
                            <button
                              onClick={() => {
                                setClarifyingId(esc.escalation_id);
                                setRejectingId(null);
                              }}
                              disabled={isLoading}
                              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shadow-xs cursor-pointer"
                            >
                              <HelpCircle className="w-4 h-4" />
                              <span>CLARIFY (Ask Graph)</span>
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Reject Form Mode */}
                      {isRejecting && (
                        <div className="bg-rose-950/20 border border-rose-500/30 p-4 rounded-lg space-y-3 animate-in fade-in duration-200">
                          <div className="flex items-center gap-2 text-rose-300 text-xs font-semibold">
                            <AlertTriangle className="w-4 h-4" />
                            <span>Mandatory Rejection Justification (Downgrades to Monitoring)</span>
                          </div>
                          <textarea
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                            placeholder="Enter detailed clinical rationale (e.g. Outpatient observation only, subject not formally admitted, investigator confirmed non-serious)..."
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-rose-500"
                            rows={2}
                          />
                          <div className="flex justify-end gap-2">
                            <button
                              onClick={() => {
                                setRejectingId(null);
                                setRejectionReason("");
                              }}
                              className="px-3 py-1.5 rounded text-xs text-slate-400 hover:text-white"
                            >
                              Cancel
                            </button>
                            <button
                              onClick={() => handleRejectSubmit(esc.escalation_id)}
                              disabled={isLoading || !rejectionReason.trim()}
                              className="px-4 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold transition-all disabled:opacity-50"
                            >
                              Confirm Rejection & Downgrade
                            </button>
                          </div>
                        </div>
                      )}

                      {/* Clarify Form Mode */}
                      {isClarifying && (
                        <div className="bg-indigo-950/20 border border-indigo-500/30 p-4 rounded-lg space-y-3 animate-in fade-in duration-200">
                          <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold">
                            <HelpCircle className="w-4 h-4" />
                            <span>CLARIFY with Knowledge Graph (Query Study Baseline & Concomitants)</span>
                          </div>
                          <p className="text-[11px] text-slate-400">
                            CLARIFY does NOT reject the escalation. It executes a targeted graph query across labs,
                            medications, and medical history to provide immediate evidence for your decision.
                          </p>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={clarifyQuestion}
                              onChange={(e) => setClarifyQuestion(e.target.value)}
                              placeholder="Type query regarding subject labs, visits, medications..."
                              className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                            />
                            <button
                              onClick={() => handleClarifySubmit(esc.escalation_id)}
                              disabled={isLoading}
                              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 shrink-0"
                            >
                              <Search className="w-3.5 h-3.5" />
                              <span>Query Graph</span>
                            </button>
                          </div>
                          <div className="flex items-center gap-2 pt-1 text-[11px] text-slate-400">
                            <span>Quick presets:</span>
                            <button
                              onClick={() =>
                                setClarifyQuestion(
                                  "What was the baseline screening ALT/AST and are there concurrent hepatotoxic medications?"
                                )
                              }
                              className="text-indigo-400 hover:underline cursor-pointer"
                            >
                              Screening ALT & ConMeds
                            </button>
                            <span>•</span>
                            <button
                              onClick={() =>
                                setClarifyQuestion("What is the subject medical history and visit schedule?")
                              }
                              className="text-indigo-400 hover:underline cursor-pointer"
                            >
                              Medical History & Visits
                            </button>
                            <button
                              onClick={() => setClarifyingId(null)}
                              className="ml-auto text-slate-500 hover:text-slate-300"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Review History Section */}
      {historyEscalations.length > 0 && (
        <div className="pt-4 border-t border-slate-800">
          <h3 className="text-sm font-semibold text-slate-300 mb-3 flex items-center gap-2">
            <span>Decision History & Audit Outcomes</span>
            <span className="text-xs text-slate-500 font-mono">({historyEscalations.length})</span>
          </h3>

          <div className="space-y-3">
            {historyEscalations.map((esc) => {
              const isApproved = esc.status === "APPROVED";
              return (
                <div
                  key={esc.escalation_id}
                  className="bg-slate-900/60 border border-slate-800 rounded-lg p-4 flex flex-col md:flex-row md:items-center justify-between gap-4 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded font-bold text-[10px] ${
                          isApproved
                            ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
                            : "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                        }`}
                      >
                        {esc.status}
                      </span>
                      <span className="font-mono text-slate-400">{esc.escalation_id}</span>
                      <span className="text-slate-300 font-semibold">{esc.finding_code}</span>
                      <span className="text-slate-500">• Subject: {esc.subject}</span>
                    </div>

                    <p className="text-slate-300 text-xs">
                      {isApproved ? esc.execution_details : esc.rejection_reason}
                    </p>
                  </div>

                  <div className="text-right text-[11px] text-slate-500 font-mono shrink-0">
                    <div>Cycle {esc.created_cycle}</div>
                    <div>{esc.updated_at || esc.created_at || "Recorded"}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};
