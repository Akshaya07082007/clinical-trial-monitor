import React from "react";
import {
  Search,
  Stethoscope,
  Database,
  FileCheck2,
  ShieldAlert,
  Terminal,
  CheckCircle2,
  Clock,
  ArrowRight
} from "lucide-react";
import { CycleReport } from "../types";

interface WorkflowStepperProps {
  currentReport: CycleReport | null;
  isRunning: boolean;
  selectedNode: string | null;
  onSelectNode: (nodeCode: string) => void;
  pendingEscalationsCount: number;
}

const NODES = [
  {
    code: "detect",
    number: 1,
    name: "Detect",
    role: "ATLAS Surveillance",
    desc: "Stage 1 rule evaluation across SDTM domains",
    icon: Search,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    border: "border-blue-500/30"
  },
  {
    code: "medical_review",
    number: 2,
    name: "Medical Review",
    role: "Clinical Evaluation",
    desc: "SAE hospital rule & liver screening baseline check",
    icon: Stethoscope,
    color: "text-amber-400",
    bg: "bg-amber-500/10",
    border: "border-amber-500/30"
  },
  {
    code: "data_manager",
    number: 3,
    name: "Data Manager",
    role: "Query Generation",
    desc: "Specific site queries with 4-key deduplication",
    icon: Database,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    border: "border-purple-500/30"
  },
  {
    code: "compliance",
    number: 4,
    name: "Compliance",
    role: "Protocol Checking",
    desc: "Multi-version rules: visit windows, eGFR, NSAIDs",
    icon: FileCheck2,
    color: "text-cyan-400",
    bg: "bg-cyan-500/10",
    border: "border-cyan-500/30"
  },
  {
    code: "human_gate",
    number: 5,
    name: "Human Gate",
    role: "Medical Monitor",
    desc: "Human authority: Approve, Reject, or Clarify",
    icon: ShieldAlert,
    color: "text-rose-400",
    bg: "bg-rose-500/10",
    border: "border-rose-500/30"
  },
  {
    code: "execute",
    number: 6,
    name: "Execute",
    role: "Action Dispatch",
    desc: "Dispatches approved regulatory notices & reports",
    icon: Terminal,
    color: "text-emerald-400",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/30"
  }
];

export const WorkflowStepper: React.FC<WorkflowStepperProps> = ({
  currentReport,
  isRunning,
  selectedNode,
  onSelectNode,
  pendingEscalationsCount
}) => {
  return (
    <div className="bg-slate-900 border-b border-slate-800 p-4">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
              Required 6-Node Architecture Pipeline
            </span>
            {currentReport && (
              <span className="text-[11px] text-slate-400 font-mono">
                [Cycle Cut {currentReport.cut} • Protocol v{currentReport.protocol_version}]
              </span>
            )}
          </div>
          <span className="text-xs text-slate-400">Click node to inspect stage outputs</span>
        </div>

        {/* 6 Nodes Stepper Grid */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-2">
          {NODES.map((node, index) => {
            const Icon = node.icon;
            const isSelected = selectedNode === node.code;
            const hasRun = Boolean(currentReport);
            const isHumanGate = node.code === "human_gate";

            return (
              <button
                key={node.code}
                onClick={() => onSelectNode(node.code)}
                className={`relative flex flex-col p-3 rounded-lg border text-left transition-all cursor-pointer ${
                  isSelected
                    ? "bg-slate-800 border-emerald-500 shadow-md ring-1 ring-emerald-500/50"
                    : "bg-slate-900/80 border-slate-800 hover:bg-slate-800/60 hover:border-slate-700"
                }`}
              >
                {/* Top Row: Number & Status */}
                <div className="flex items-center justify-between mb-2">
                  <span className="w-5 h-5 rounded-full bg-slate-800 border border-slate-700 text-[10px] font-bold text-slate-300 flex items-center justify-center">
                    0{node.number}
                  </span>
                  {isRunning ? (
                    <Clock className="w-3.5 h-3.5 text-amber-400 animate-spin" />
                  ) : hasRun ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <div className="w-2 h-2 rounded-full bg-slate-700" />
                  )}
                </div>

                {/* Node Icon & Name */}
                <div className="flex items-center gap-2 mb-1">
                  <div className={`p-1.5 rounded-md ${node.bg} ${node.border} ${node.color}`}>
                    <Icon className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-xs font-semibold text-slate-200">{node.name}</span>
                </div>

                {/* Role and description */}
                <span className="text-[11px] font-medium text-slate-400 truncate">{node.role}</span>
                <span className="text-[10px] text-slate-500 leading-tight mt-0.5 line-clamp-2">
                  {node.desc}
                </span>

                {/* Alert Badge for Human Gate */}
                {isHumanGate && pendingEscalationsCount > 0 && (
                  <div className="mt-2 flex items-center gap-1 bg-rose-500/20 text-rose-300 border border-rose-500/30 px-1.5 py-0.5 rounded text-[10px] font-semibold animate-pulse">
                    <ShieldAlert className="w-3 h-3" />
                    <span>{pendingEscalationsCount} Pending Review</span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};
