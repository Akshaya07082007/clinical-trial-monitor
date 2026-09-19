import React, { useState } from "react";
import {
  FileCheck2,
  GitCompare,
  GitBranch,
  ShieldCheck,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  CheckCircle2
} from "lucide-react";
import { Deviation } from "../types";
import { amendProtocol } from "../api";

interface ProtocolViewProps {
  currentCut: number;
  activeProtocolVersion: number;
  deviations: Deviation[];
  onRefreshData: () => Promise<void>;
  isLoading: boolean;
}

export const ProtocolView: React.FC<ProtocolViewProps> = ({
  currentCut,
  activeProtocolVersion,
  deviations,
  onRefreshData,
  isLoading
}) => {
  const [isAmending, setIsAmending] = useState(false);
  const [amendResult, setAmendResult] = useState<any | null>(null);

  const handleSimulateAmendment = async () => {
    setIsAmending(true);
    try {
      const res = await amendProtocol(currentCut, 2);
      setAmendResult(res);
      await onRefreshData();
    } catch (err: any) {
      alert(`Amendment simulation failed: ${err.message}`);
    } finally {
      setIsAmending(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Banner */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg text-cyan-400">
              <FileCheck2 className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Node 4: Protocol Engine & Versioning Rules
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                  Dual-Version Compliance
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed max-w-3xl">
                The protocol engine enforces version-specific criteria without overwriting historical evaluations.
                Enables instantaneous differential comparison between Protocol v1 (Baseline) and Protocol v2 (Safety Amendment).
              </p>
            </div>
          </div>

          <button
            onClick={handleSimulateAmendment}
            disabled={isAmending}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-2 transition-all shadow-md shrink-0 cursor-pointer disabled:opacity-50"
          >
            {isAmending ? (
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Sparkles className="w-4 h-4 text-indigo-200" />
            )}
            <span>Enact Protocol v2 Amendment</span>
          </button>
        </div>
      </div>

      {/* Protocol v1 vs v2 Side-by-Side Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Protocol v1 Card */}
        <div
          className={`bg-slate-900 rounded-xl p-5 border transition-all ${
            activeProtocolVersion === 1
              ? "border-cyan-500/80 ring-1 ring-cyan-500/30 shadow-md"
              : "border-slate-800"
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-cyan-500/20 text-cyan-300 border border-cyan-500/30">
                Protocol v1.0
              </span>
              <span className="text-xs text-slate-400">Baseline Protocol</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Effective: 2026-01-01</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                Renal Function Exclusion
              </span>
              <div className="text-slate-200 font-semibold">
                eGFR &lt; 30 mL/min/1.73m² (Severe Impairment)
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Mild and moderate renal decline permitted in baseline cohort.
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                Prohibited Concomitant Medications
              </span>
              <div className="text-slate-200 font-semibold">
                Investigational drugs only
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Standard NSAIDs (Naproxen, Ibuprofen) permitted for chronic arthritic pain.
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                Visit Windows
              </span>
              <div className="text-slate-300 font-mono text-[11px]">
                Visit 2 (Day 14 ±3d) • Visit 3 (Day 28 ±3d) • Visit 4 (Day 42 ±5d)
              </div>
            </div>
          </div>
        </div>

        {/* Protocol v2 Card */}
        <div
          className={`bg-slate-900 rounded-xl p-5 border transition-all ${
            activeProtocolVersion === 2
              ? "border-indigo-500/80 ring-1 ring-indigo-500/30 shadow-md"
              : "border-slate-800"
          }`}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded text-xs font-bold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                Protocol v2.0
              </span>
              <span className="text-xs text-indigo-300 font-medium">Safety Amendment #1</span>
            </div>
            <span className="text-[11px] font-mono text-slate-500">Effective: 2026-02-01</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="bg-slate-950/60 p-3 rounded-lg border border-indigo-900/40">
              <span className="text-[10px] uppercase font-bold text-amber-400 block mb-1">
                Renal Function Exclusion (Tightened)
              </span>
              <div className="text-amber-300 font-semibold">
                eGFR &lt; 60 mL/min/1.73m² (Moderate + Severe Impairment)
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Flags Subject 042-S01-003 (eGFR 52) as active exclusion violation!
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-indigo-900/40">
              <span className="text-[10px] uppercase font-bold text-amber-400 block mb-1">
                Prohibited Concomitant Medications (Expanded)
              </span>
              <div className="text-amber-300 font-semibold">
                Investigational drugs + High-dose NSAIDs (Naproxen, Ibuprofen)
              </div>
              <p className="text-[11px] text-slate-400 mt-0.5">
                Flags Subject 042-S02-001 (Naproxen) as prohibited medication deviation!
              </p>
            </div>

            <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-500 block mb-1">
                Tightened Visit Windows
              </span>
              <div className="text-slate-300 font-mono text-[11px]">
                Visit 2 (Day 14 ±2d) • Visit 3 (Day 28 ±2d) • Visit 4 (Day 42 ±3d)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Amendment Result Diff Banner */}
      {amendResult && (
        <div className="bg-indigo-950/30 border border-indigo-500/40 rounded-xl p-4 space-y-3 animate-in fade-in duration-200">
          <div className="flex items-center justify-between text-xs font-semibold">
            <span className="text-indigo-300 flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-indigo-400" />
              <span>Protocol v2.0 Amendment Enacted: Differential Compliance Impact</span>
            </span>
            <button
              onClick={() => setAmendResult(null)}
              className="text-slate-500 hover:text-slate-300 text-[11px]"
            >
              Dismiss
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                Newly Affected Subjects:
              </span>
              <div className="flex items-center gap-2 font-mono text-amber-300 font-semibold">
                {amendResult.diff.affected_subjects.join(", ") || "None"}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                These subjects were compliant under v1, but triggered new deviations under v2 rules.
              </p>
            </div>

            <div className="bg-slate-900/80 p-3 rounded-lg border border-slate-800">
              <span className="text-[10px] uppercase font-bold text-slate-400 block mb-1">
                Historical Record Preservation:
              </span>
              <div className="text-emerald-400 font-medium">
                ✓ Preserved all {amendResult.diff.v1_deviations_count} baseline v1 deviation records.
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Added {amendResult.new_deviations_persisted?.length || 0} v2 deviations without overwriting history.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Active Deviations List */}
      <div>
        <h3 className="text-sm font-semibold text-slate-200 mb-3 flex items-center gap-2">
          <span>Active Protocol Deviations (Under Active Protocol v{activeProtocolVersion})</span>
          <span className="px-2 py-0.5 bg-cyan-500/20 text-cyan-300 text-xs rounded-full font-mono">
            {deviations.length}
          </span>
        </h3>

        <div className="space-y-2.5">
          {deviations.length === 0 ? (
            <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 text-center text-slate-400 text-xs">
              <CheckCircle2 className="w-6 h-6 text-emerald-400 mx-auto mb-1.5 opacity-80" />
              <p>No protocol deviations recorded under v{activeProtocolVersion}.</p>
            </div>
          ) : (
            deviations.map((d) => (
              <div
                key={d.deviation_id}
                className="bg-slate-900 border border-slate-800 rounded-lg p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-cyan-400 font-bold">{d.deviation_id}</span>
                    <span className="font-semibold text-slate-200">{d.deviation_type}</span>
                    <span className="text-slate-500">• Subject: {d.subject}</span>
                    <span className="text-slate-500">• Site: {d.site}</span>
                  </div>
                  <p className="text-slate-300 text-xs">{d.explanation}</p>
                </div>

                <div className="shrink-0 text-right font-mono text-[11px] text-slate-400">
                  <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700">
                    Protocol v{d.protocol_version}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
