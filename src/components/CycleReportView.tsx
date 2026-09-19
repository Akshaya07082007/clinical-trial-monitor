import React from "react";
import {
  FileCheck,
  CheckCircle2,
  Clock,
  ShieldAlert,
  HelpCircle,
  AlertTriangle,
  Database,
  Terminal,
  FileSpreadsheet,
  Download
} from "lucide-react";
import { CycleReport } from "../types";

interface CycleReportViewProps {
  report: CycleReport | null;
  onOpenGraphSubject?: (subjectId: string) => void;
  onSwitchTab?: (tab: string) => void;
}

export const CycleReportView: React.FC<CycleReportViewProps> = ({
  report,
  onOpenGraphSubject,
  onSwitchTab
}) => {
  if (!report) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-12 text-center text-slate-400">
        <FileSpreadsheet className="w-12 h-12 text-slate-600 mx-auto mb-3" />
        <h3 className="text-base font-semibold text-slate-200">No Cycle Report Available</h3>
        <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
          Click <strong>"Run 6-Node Cycle"</strong> in the top header to execute detection,
          medical review, query generation, compliance, human gate, and action execution.
        </p>
      </div>
    );
  }

  const exportReportJson = () => {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
    const downloadAnchor = document.createElement("a");
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `clinical_cycle_cut_${report.cut}_report.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
  };

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-emerald-400">
              <FileCheck className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Cycle Cut {report.cut} Formal Review Report
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                  {report.cycle_status}
                </span>
                <span className="px-2 py-0.5 rounded text-[11px] font-mono text-slate-300 bg-slate-800 border border-slate-700">
                  Protocol v{report.protocol_version}
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 font-mono">
                Generated: {report.timestamp}
              </p>
            </div>
          </div>

          <button
            onClick={exportReportJson}
            className="px-3.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer shrink-0"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Report JSON</span>
          </button>
        </div>
      </div>

      {/* 6 Nodes Execution Checklist */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider block mb-3">
          Required 6-Node Architecture Status Checklist
        </span>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2 text-xs">
          {report.nodes.map((node, i) => (
            <div
              key={node.code}
              className="bg-slate-950/60 border border-slate-800/80 rounded-lg p-3 flex flex-col justify-between"
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[10px] font-mono font-bold text-slate-500">
                  Node 0{i + 1}
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              </div>
              <span className="font-semibold text-slate-200 text-xs">{node.name}</span>
              <span className="text-[10px] text-emerald-400 font-mono mt-0.5">{node.status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-blue-400 block">{report.metrics.total_findings}</span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Total Findings
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-rose-400 block">
            {report.metrics.safety_findings}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Safety Issues
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-purple-400 block">
            {report.metrics.data_findings}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Data Issues
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-cyan-400 block">
            {report.metrics.compliance_findings}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Deviations
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-amber-400 block">
            {report.metrics.pending_escalations}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Pending Human Gate
          </span>
        </div>

        <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 text-center">
          <span className="text-2xl font-bold text-emerald-400 block">
            {report.metrics.executed_actions}
          </span>
          <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
            Executed Actions
          </span>
        </div>
      </div>

      {/* Executed Actions List (Node 6) */}
      {report.executed_actions && report.executed_actions.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
          <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <span>Node 6: Executed Clinical Regulatory Actions</span>
          </h3>

          <div className="space-y-2">
            {report.executed_actions.map((act, idx) => (
              <div
                key={idx}
                className="bg-slate-950/60 border border-emerald-900/30 rounded-lg p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                      EXECUTED
                    </span>
                    <span className="font-mono text-slate-300">{act.escalation_id}</span>
                    <span className="text-slate-500">• Subject: {act.subject}</span>
                    <span className="text-slate-500">• Site: {act.site}</span>
                  </div>
                  <p className="text-slate-200">{act.details}</p>
                </div>

                <div className="shrink-0 text-right font-mono text-[11px] text-slate-400">
                  {act.executed_at?.slice(0, 19) || "Recorded"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Findings Breakdown Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
        <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center justify-between">
          <span>Complete Surveillance Findings (Cut {report.cut})</span>
          <span className="text-slate-400 font-mono font-normal">
            {report.findings_summary?.length || 0} findings evaluated
          </span>
        </h3>

        <div className="space-y-2">
          {report.findings_summary &&
            report.findings_summary.map((f) => {
              const isSafety = f.classification === "SAFETY ISSUE";
              const isData = f.classification === "DATA QUALITY ISSUE";
              const isCompliance = f.classification === "COMPLIANCE ISSUE";

              return (
                <div
                  key={f.finding_id}
                  className="bg-slate-950/50 border border-slate-800 rounded-lg p-3 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          isSafety
                            ? "bg-rose-500/20 text-rose-300 border border-rose-500/30"
                            : isData
                            ? "bg-purple-500/20 text-purple-300 border border-purple-500/30"
                            : isCompliance
                            ? "bg-cyan-500/20 text-cyan-300 border border-cyan-500/30"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {f.classification}
                      </span>
                      <span className="font-semibold text-slate-200">{f.finding_code}</span>
                      <span className="text-slate-500">•</span>
                      <span className="font-mono text-slate-300">Subj: {f.subject_id}</span>
                      <span className="text-slate-500">•</span>
                      <span className="font-mono text-slate-400">Site: {f.site}</span>
                    </div>
                    <p className="text-slate-300 text-xs">{f.rationale}</p>
                  </div>

                  <div className="shrink-0 text-right font-mono text-[11px] text-slate-500">
                    <div>Domain: {f.domain}</div>
                    <div>Source: {f.source_evidence?.SOURCE_DOC || "CRF Entry"}</div>
                  </div>
                </div>
              );
            })}
        </div>
      </div>
    </div>
  );
};
