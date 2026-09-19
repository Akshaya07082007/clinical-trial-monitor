import React, { useState } from "react";
import {
  ListTree,
  Filter,
  Search,
  CheckCircle2,
  Clock,
  User,
  Cpu,
  ChevronDown,
  ChevronUp,
  FileCode
} from "lucide-react";
import { TraceEntry } from "../types";

interface TraceViewProps {
  traceEntries: TraceEntry[];
  isLoading: boolean;
}

const NODE_COLORS: Record<string, { text: string; bg: string }> = {
  detect: { text: "text-blue-400", bg: "bg-blue-500/10" },
  medical_review: { text: "text-amber-400", bg: "bg-amber-500/10" },
  data_manager: { text: "text-purple-400", bg: "bg-purple-500/10" },
  compliance: { text: "text-cyan-400", bg: "bg-cyan-500/10" },
  human_gate: { text: "text-rose-400", bg: "bg-rose-500/10" },
  execute: { text: "text-emerald-400", bg: "bg-emerald-500/10" }
};

export const TraceView: React.FC<TraceViewProps> = ({ traceEntries, isLoading }) => {
  const [nodeFilter, setNodeFilter] = useState("ALL");
  const [cycleFilter, setCycleFilter] = useState("ALL");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedTraceId, setExpandedTraceId] = useState<number | null>(null);

  const filtered = traceEntries.filter((t) => {
    if (nodeFilter !== "ALL" && t.node !== nodeFilter) return false;
    if (cycleFilter !== "ALL" && String(t.cycle) !== cycleFilter) return false;
    if (searchTerm.trim()) {
      const s = searchTerm.toLowerCase();
      return (
        t.decision.toLowerCase().includes(s) ||
        (t.subject && t.subject.toLowerCase().includes(s)) ||
        (t.site && t.site.toLowerCase().includes(s)) ||
        t.actor.toLowerCase().includes(s)
      );
    }
    return true;
  });

  return (
    <div className="space-y-4">
      {/* Header Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-slate-800 border border-slate-700 rounded-lg text-slate-300">
              <ListTree className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Real-Time Audit Trace Log
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                  Mandatory Surveillance Log
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed max-w-3xl">
                Immutable, chronological ledger recording every surveillance detection, classification, query generation,
                compliance validation, human decision, and action execution with associated source evidence payloads.
              </p>
            </div>
          </div>

          <div className="bg-slate-800/80 px-4 py-2 rounded-lg border border-slate-700 text-center shrink-0">
            <span className="block text-xl font-bold text-slate-200">{traceEntries.length}</span>
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Total Trace Events
            </span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {/* Node Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg">
            <span className="text-slate-400">Node:</span>
            <select
              value={nodeFilter}
              onChange={(e) => setNodeFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Nodes</option>
              <option value="detect">Detect (Node 1)</option>
              <option value="medical_review">Medical Review (Node 2)</option>
              <option value="data_manager">Data Manager (Node 3)</option>
              <option value="compliance">Compliance (Node 4)</option>
              <option value="human_gate">Human Gate (Node 5)</option>
              <option value="execute">Execute (Node 6)</option>
            </select>
          </div>

          {/* Cycle Filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg">
            <span className="text-slate-400">Cycle:</span>
            <select
              value={cycleFilter}
              onChange={(e) => setCycleFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Cycles</option>
              <option value="1">Cycle Cut 1</option>
              <option value="2">Cycle Cut 2</option>
              <option value="3">Cycle Cut 3</option>
            </select>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search decisions, actors..."
            className="bg-slate-800/80 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none w-48"
          />
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
        </div>
      </div>

      {/* Trace Log Entries Table / Feed */}
      <div className="space-y-2">
        {filtered.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-6 h-6 text-slate-500 mx-auto mb-1.5" />
            <p>No trace records match the selected filter.</p>
          </div>
        ) : (
          filtered.map((t) => {
            const isExpanded = expandedTraceId === t.trace_id;
            const nodeConfig = NODE_COLORS[t.node] || { text: "text-slate-400", bg: "bg-slate-800" };
            const isHuman = t.actor.toLowerCase().includes("human") || t.actor.toLowerCase().includes("monitor");

            return (
              <div
                key={t.trace_id}
                className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden text-xs transition-all hover:border-slate-700"
              >
                <div
                  onClick={() => setExpandedTraceId(isExpanded ? null : t.trace_id)}
                  className="px-4 py-2.5 flex flex-wrap items-center justify-between gap-2 cursor-pointer select-none bg-slate-900/90"
                >
                  <div className="flex items-center gap-3">
                    <span className="font-mono text-[11px] text-slate-500 w-10">
                      #{t.trace_id}
                    </span>

                    <span
                      className={`px-2 py-0.5 rounded font-mono font-semibold text-[10px] uppercase ${nodeConfig.bg} ${nodeConfig.text}`}
                    >
                      {t.node}
                    </span>

                    <span className="font-semibold text-slate-200">{t.decision}</span>

                    {t.subject && (
                      <span className="font-mono text-[11px] text-slate-400">
                        Subj: <strong>{t.subject}</strong>
                      </span>
                    )}
                    {t.site && (
                      <span className="font-mono text-[11px] text-slate-400">
                        Site: <strong>{t.site}</strong>
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 font-mono text-[11px] text-slate-500">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-400">
                      Cut {t.cycle} • v{t.protocol_version}
                    </span>
                    <span className="flex items-center gap-1">
                      {isHuman ? (
                        <User className="w-3 h-3 text-rose-400" />
                      ) : (
                        <Cpu className="w-3 h-3 text-slate-400" />
                      )}
                      <span className={isHuman ? "text-rose-300 font-semibold" : "text-slate-400"}>
                        {t.actor}
                      </span>
                    </span>
                    <span className="text-[10px]">{t.timestamp.slice(11, 19)}</span>
                    {isExpanded ? (
                      <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
                    )}
                  </div>
                </div>

                {/* Expanded Evidence JSON Viewer */}
                {isExpanded && (
                  <div className="px-4 py-3 bg-slate-950 border-t border-slate-800/80 space-y-2 text-xs">
                    <div className="flex items-center justify-between text-[10px] font-mono text-slate-400">
                      <span>Source Evidence Payload</span>
                      <span>Recorded at {t.timestamp}</span>
                    </div>
                    <pre className="bg-slate-900/80 p-3 rounded-lg border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto">
                      {JSON.stringify(t.evidence, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
