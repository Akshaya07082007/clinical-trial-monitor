import React from "react";
import { Play, ShieldAlert, GitBranch, Database, CheckCircle2, Activity } from "lucide-react";

interface HeaderProps {
  selectedCut: number;
  setSelectedCut: (cut: number) => void;
  selectedProtocolVersion: number;
  setSelectedProtocolVersion: (v: number) => void;
  onRunCycle: () => void;
  isRunning: boolean;
  activeCycleCut: number;
  isBackendOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({
  selectedCut,
  setSelectedCut,
  selectedProtocolVersion,
  setSelectedProtocolVersion,
  onRunCycle,
  isRunning,
  activeCycleCut,
  isBackendOnline
}) => {
  return (
    <header className="bg-slate-900 border-b border-slate-800 text-slate-100 px-6 py-4 shadow-sm">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Title & Badge */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <Activity className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight text-white">
                Clinical Trial Review System
              </h1>
              <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-slate-800 text-slate-300 border border-slate-700">
                CDISC SDTM Multi-Node
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Synthetic CDISC SDTM surveillance engine with 6-node deterministic workflow & Human Gate
            </p>
          </div>
        </div>

        {/* Controls & Actions */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Data Cut Selection */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 p-1 rounded-lg border border-slate-700 text-xs">
            <span className="text-slate-400 px-2 font-medium flex items-center gap-1">
              <Database className="w-3.5 h-3.5" /> Cut:
            </span>
            {[1, 2, 3].map((cut) => (
              <button
                key={cut}
                onClick={() => setSelectedCut(cut)}
                className={`px-2.5 py-1 rounded font-medium transition-all ${
                  selectedCut === cut
                    ? "bg-emerald-600 text-white shadow-xs"
                    : "text-slate-300 hover:bg-slate-700/60"
                }`}
              >
                Cut {cut}
              </button>
            ))}
          </div>

          {/* Protocol Version Selection */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 p-1 rounded-lg border border-slate-700 text-xs">
            <span className="text-slate-400 px-2 font-medium flex items-center gap-1">
              <GitBranch className="w-3.5 h-3.5" /> Protocol:
            </span>
            {[1, 2].map((v) => (
              <button
                key={v}
                onClick={() => setSelectedProtocolVersion(v)}
                className={`px-2.5 py-1 rounded font-medium transition-all ${
                  selectedProtocolVersion === v
                    ? "bg-indigo-600 text-white shadow-xs"
                    : "text-slate-300 hover:bg-slate-700/60"
                }`}
              >
                v{v}
              </button>
            ))}
          </div>

          {/* Run Cycle Button */}
          <button
            onClick={onRunCycle}
            disabled={isRunning}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold tracking-wide transition-all shadow-md ${
              isRunning
                ? "bg-slate-700 text-slate-400 cursor-not-allowed"
                : "bg-emerald-600 hover:bg-emerald-500 text-white active:scale-98"
            }`}
          >
            {isRunning ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>Running Node Pipeline...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Run 6-Node Cycle</span>
              </>
            )}
          </button>

          {/* Backend Status Pulse */}
          <div className="flex items-center gap-1.5 pl-2 border-l border-slate-800 text-[11px]">
            <span
              className={`w-2 h-2 rounded-full ${
                isBackendOnline ? "bg-emerald-400 animate-pulse" : "bg-red-500"
              }`}
            />
            <span className="text-slate-400 hidden sm:inline">
              {isBackendOnline ? "Engine Ready" : "Connecting..."}
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
