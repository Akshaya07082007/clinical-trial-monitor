import React from "react";
import {
  Radar,
  AlertTriangle,
  Clock,
  ChevronRight,
  TrendingUp,
  Database,
  ShieldAlert,
  ArrowUpRight,
  CheckCircle2
} from "lucide-react";
import { RiskSignal } from "../types";

interface RiskRadarViewProps {
  signals: RiskSignal[];
  onOpenGraphFilter: (subject: string | null) => void;
  isLoading: boolean;
}

const STATUS_BADGES: Record<string, { bg: string; text: string; border: string }> = {
  "REQUIRES REVIEW": { bg: "bg-red-500/20", text: "text-red-300", border: "border-red-500/30" },
  "MONITOR": { bg: "bg-amber-500/20", text: "text-amber-300", border: "border-amber-500/30" },
  "EARLY WARNING": { bg: "bg-yellow-500/20", text: "text-yellow-300", border: "border-yellow-500/30" },
  "RESOLVED": { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/30" }
};

export const RiskRadarView: React.FC<RiskRadarViewProps> = ({
  signals,
  onOpenGraphFilter,
  isLoading
}) => {
  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-amber-500/10 border border-amber-500/20 rounded-lg text-amber-400">
              <Radar className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Protocol Drift & Ripple-Risk Radar
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  Operational Early Warning
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed max-w-3xl">
                Synthesizes Knowledge Graph topology across multi-cycle queries, protocol amendments, and site behavior.
                Detects recurring site training deficiencies, post-amendment protocol drift, and accumulating unanswered queries.
                <em> Does not replace the Medical Monitor or autonomously diagnose patients.</em>
              </p>
            </div>
          </div>

          <div className="bg-slate-800/80 px-4 py-2 rounded-lg border border-slate-700 text-center shrink-0">
            <span className="block text-xl font-bold text-amber-400">
              {signals.length}
            </span>
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Active Risk Signals
            </span>
          </div>
        </div>
      </div>

      {/* Signals List */}
      <div className="space-y-4">
        {signals.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-medium text-slate-300">No Operational Risk Signals Detected</p>
            <p className="text-xs text-slate-500 mt-1">
              Trial sites are adhering to protocol amendments without recurring chronology or query accumulation patterns.
            </p>
          </div>
        ) : (
          signals.map((sig) => {
            const badge = STATUS_BADGES[sig.status] || STATUS_BADGES["MONITOR"];

            return (
              <div
                key={sig.signal_id}
                className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs hover:border-slate-700 transition-all"
              >
                {/* Header */}
                <div className="bg-slate-800/60 px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2.5 py-0.5 rounded">
                      {sig.signal_id}
                    </span>
                    <span className="text-xs font-semibold text-slate-200">
                      {sig.issue_type.replace(/_/g, " ")}
                    </span>
                    <span className="text-xs text-slate-400">•</span>
                    <span className="text-xs font-mono text-slate-300">
                      Site: <strong>{sig.site}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold border ${badge.bg} ${badge.text} ${badge.border}`}
                    >
                      {sig.status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
                      Occurrences: {sig.occurrences}
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-5 space-y-3 text-xs">
                  {/* Detailed Explanation */}
                  <p className="text-slate-300 text-sm leading-relaxed bg-slate-800/30 p-3 rounded-lg border border-slate-800">
                    {sig.explanation}
                  </p>

                  {/* Metadata Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono text-[11px]">
                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase font-sans">
                        Affected Subjects
                      </span>
                      <span className="text-blue-300 font-semibold">
                        {sig.affected_subjects.join(", ") || "None specified"}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase font-sans">
                        Surveillance Interval
                      </span>
                      <span className="text-slate-300">
                        {sig.first_occurrence || "N/A"} → {sig.latest_occurrence || "N/A"}
                      </span>
                    </div>

                    <div className="bg-slate-950/60 p-2.5 rounded border border-slate-800">
                      <span className="text-slate-500 block text-[10px] uppercase font-sans">
                        Protocol Version in Effect
                      </span>
                      <span className="text-indigo-300 font-semibold">
                        Protocol v{sig.protocol_version}
                      </span>
                    </div>
                  </div>

                  {/* Bottom Bar with Link to Graph Evidence */}
                  <div className="pt-2 border-t border-slate-800 flex items-center justify-between">
                    <span className="text-slate-500 text-[11px]">
                      Graph Evidence: {sig.graph_evidence?.query_nodes?.length || 0} query nodes •{" "}
                      {sig.affected_subjects.length} subject nodes
                    </span>

                    <button
                      onClick={() => {
                        const firstSubj = sig.affected_subjects[0] || null;
                        onOpenGraphFilter(firstSubj);
                      }}
                      className="px-3 py-1.5 bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 rounded text-xs font-semibold flex items-center gap-1 cursor-pointer transition-colors"
                    >
                      <Database className="w-3 h-3" />
                      <span>View Graph Evidence</span>
                      <ArrowUpRight className="w-3 h-3 ml-0.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
