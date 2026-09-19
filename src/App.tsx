import React, { useState, useEffect, useCallback } from "react";
import {
  ShieldAlert,
  Database,
  FileSpreadsheet,
  HelpCircle,
  FileCheck2,
  Radar,
  ListTree,
  Activity,
  AlertCircle
} from "lucide-react";

import {
  CycleReport,
  Escalation,
  QueryRecord,
  TraceEntry,
  RiskSignal,
  CytoscapeGraphData,
  Deviation
} from "./types";
import {
  fetchHealth,
  runCycle,
  fetchCycleReport,
  fetchEscalations,
  postEscalationDecision,
  fetchQueries,
  fetchTrace,
  fetchKnowledgeGraph,
  fetchRiskRadar,
  fetchProtocol
} from "./api";

import { Header } from "./components/Header";
import { WorkflowStepper } from "./components/WorkflowStepper";
import { HumanGateView } from "./components/HumanGateView";
import { KnowledgeGraphViewer } from "./components/KnowledgeGraphViewer";
import { CycleReportView } from "./components/CycleReportView";
import { QueriesView } from "./components/QueriesView";
import { ProtocolView } from "./components/ProtocolView";
import { RiskRadarView } from "./components/RiskRadarView";
import { TraceView } from "./components/TraceView";

export default function App() {
  // Navigation & View State
  const [activeTab, setActiveTab] = useState<string>("human_gate");
  const [selectedCut, setSelectedCut] = useState<number>(1);
  const [selectedProtocolVersion, setSelectedProtocolVersion] = useState<number>(1);
  const [isRunningCycle, setIsRunningCycle] = useState<boolean>(false);
  const [isBackendOnline, setIsBackendOnline] = useState<boolean>(false);

  // Core Clinical State
  const [currentReport, setCurrentReport] = useState<CycleReport | null>(null);
  const [escalations, setEscalations] = useState<Escalation[]>([]);
  const [queries, setQueries] = useState<QueryRecord[]>([]);
  const [graphData, setGraphData] = useState<CytoscapeGraphData | null>(null);
  const [riskSignals, setRiskSignals] = useState<RiskSignal[]>([]);
  const [traceEntries, setTraceEntries] = useState<TraceEntry[]>([]);
  const [deviations, setDeviations] = useState<Deviation[]>([]);

  // Focus & Filter State
  const [graphSubjectFilter, setGraphSubjectFilter] = useState<string | null>(null);
  const [selectedWorkflowNode, setSelectedWorkflowNode] = useState<string | null>("human_gate");

  // Load all current data from backend
  const loadAllData = useCallback(async () => {
    try {
      const [healthRes, escRes, qryRes, kgRes, rskRes, trcRes] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchEscalations().catch(() => []),
        fetchQueries().catch(() => []),
        fetchKnowledgeGraph().catch(() => null),
        fetchRiskRadar().catch(() => []),
        fetchTrace().catch(() => [])
      ]);

      setIsBackendOnline(Boolean(healthRes));
      setEscalations(escRes);
      setQueries(qryRes);
      if (kgRes) setGraphData(kgRes);
      setRiskSignals(rskRes);
      setTraceEntries(trcRes);

      // Attempt to load existing report for current cut
      const rep = await fetchCycleReport(selectedCut).catch(() => null);
      if (rep) {
        setCurrentReport(rep);
        setDeviations(rep.deviations || []);
      }
    } catch (err) {
      console.error("Error loading clinical data:", err);
    }
  }, [selectedCut]);

  // Initial mount load
  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // Trigger Run 6-Node Cycle
  const handleRunCycle = async () => {
    setIsRunningCycle(true);
    try {
      const report = await runCycle(selectedCut, selectedProtocolVersion);
      setCurrentReport(report);
      setDeviations(report.deviations || []);
      // Refresh related states
      await loadAllData();
    } catch (err: any) {
      alert(`Pipeline execution error: ${err.message}`);
    } finally {
      setIsRunningCycle(false);
    }
  };

  // Handle Human Gate Decision (Approve / Reject / Clarify)
  const handleHumanGateDecision = async (
    escalationId: string,
    decision: "APPROVED" | "REJECTED" | "CLARIFY",
    payload: { reason?: string; question?: string; actor?: string }
  ) => {
    try {
      const res = await postEscalationDecision(escalationId, decision, payload);
      // Reload updated escalations, trace, report
      await loadAllData();
      if (decision === "APPROVED") {
        setActiveTab("human_gate");
      }
    } catch (err: any) {
      alert(`Decision submission error: ${err.message}`);
    }
  };

  // Shortcut to open subject in Knowledge Graph viewer
  const handleOpenGraphSubject = (subjectId: string | null) => {
    setGraphSubjectFilter(subjectId);
    setActiveTab("knowledge_graph");
    setSelectedWorkflowNode("medical_review");
  };

  // Stepper Node Click Handler
  const handleSelectWorkflowNode = (nodeCode: string) => {
    setSelectedWorkflowNode(nodeCode);
    switch (nodeCode) {
      case "detect":
        setActiveTab("cycle_report");
        break;
      case "medical_review":
        setActiveTab("knowledge_graph");
        break;
      case "data_manager":
        setActiveTab("queries");
        break;
      case "compliance":
        setActiveTab("protocol");
        break;
      case "human_gate":
        setActiveTab("human_gate");
        break;
      case "execute":
        setActiveTab("cycle_report");
        break;
      default:
        break;
    }
  };

  const pendingEscalationsCount = escalations.filter((e) => e.status === "PENDING").length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans selection:bg-indigo-500 selection:text-white">
      {/* Top Header */}
      <Header
        selectedCut={selectedCut}
        setSelectedCut={(cut) => {
          setSelectedCut(cut);
          fetchCycleReport(cut)
            .then((r) => {
              setCurrentReport(r);
              setDeviations(r.deviations || []);
            })
            .catch(() => setCurrentReport(null));
        }}
        selectedProtocolVersion={selectedProtocolVersion}
        setSelectedProtocolVersion={setSelectedProtocolVersion}
        onRunCycle={handleRunCycle}
        isRunning={isRunningCycle}
        activeCycleCut={currentReport?.cut || selectedCut}
        isBackendOnline={isBackendOnline}
      />

      {/* Six-Node Workflow Stepper Bar */}
      <WorkflowStepper
        currentReport={currentReport}
        isRunning={isRunningCycle}
        selectedNode={selectedWorkflowNode}
        onSelectNode={handleSelectWorkflowNode}
        pendingEscalationsCount={pendingEscalationsCount}
      />

      {/* Main Navigation Tabs */}
      <nav className="bg-slate-900 border-b border-slate-800 px-6 overflow-x-auto">
        <div className="max-w-7xl mx-auto flex items-center space-x-1 py-2 text-xs font-medium">
          {/* Tab 1: Human Gate */}
          <button
            onClick={() => {
              setActiveTab("human_gate");
              setSelectedWorkflowNode("human_gate");
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "human_gate"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Human Gate</span>
            {pendingEscalationsCount > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-rose-500 text-white text-[10px] font-bold">
                {pendingEscalationsCount}
              </span>
            )}
          </button>

          {/* Tab 2: Knowledge Graph */}
          <button
            onClick={() => {
              setActiveTab("knowledge_graph");
              setSelectedWorkflowNode("medical_review");
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "knowledge_graph"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Database className="w-4 h-4 text-indigo-400" />
            <span>Knowledge Graph & Clarify</span>
          </button>

          {/* Tab 3: Cycle Report */}
          <button
            onClick={() => {
              setActiveTab("cycle_report");
              setSelectedWorkflowNode("execute");
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "cycle_report"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            <span>Cycle Report</span>
          </button>

          {/* Tab 4: Queries */}
          <button
            onClick={() => {
              setActiveTab("queries");
              setSelectedWorkflowNode("data_manager");
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "queries"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <HelpCircle className="w-4 h-4 text-purple-400" />
            <span>Data Queries</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400 text-[10px] font-mono">
              {queries.length}
            </span>
          </button>

          {/* Tab 5: Protocol Engine */}
          <button
            onClick={() => {
              setActiveTab("protocol");
              setSelectedWorkflowNode("compliance");
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "protocol"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <FileCheck2 className="w-4 h-4 text-cyan-400" />
            <span>Protocol & Amendments</span>
            {deviations.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-cyan-950 text-cyan-300 text-[10px] font-mono border border-cyan-800">
                {deviations.length}
              </span>
            )}
          </button>

          {/* Tab 6: Risk Radar */}
          <button
            onClick={() => {
              setActiveTab("risk_radar");
              setSelectedWorkflowNode(null);
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "risk_radar"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <Radar className="w-4 h-4 text-amber-400" />
            <span>Risk Radar</span>
            {riskSignals.length > 0 && (
              <span className="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/30">
                {riskSignals.length}
              </span>
            )}
          </button>

          {/* Tab 7: Trace Log */}
          <button
            onClick={() => {
              setActiveTab("trace");
              setSelectedWorkflowNode(null);
            }}
            className={`px-3.5 py-2 rounded-lg flex items-center gap-2 transition-colors cursor-pointer ${
              activeTab === "trace"
                ? "bg-slate-800 text-white font-semibold shadow-xs"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
            }`}
          >
            <ListTree className="w-4 h-4 text-slate-400" />
            <span>Audit Trace</span>
            <span className="px-1.5 py-0.2 rounded-full bg-slate-800 text-slate-400 text-[10px] font-mono">
              {traceEntries.length}
            </span>
          </button>
        </div>
      </nav>

      {/* Main Content Viewport */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6">
        {activeTab === "human_gate" && (
          <HumanGateView
            escalations={escalations}
            onDecision={handleHumanGateDecision}
            isLoading={isRunningCycle}
            onOpenGraphSubject={handleOpenGraphSubject}
          />
        )}

        {activeTab === "knowledge_graph" && (
          <KnowledgeGraphViewer
            graphData={graphData}
            selectedSubjectFilter={graphSubjectFilter}
            onSelectSubjectFilter={setGraphSubjectFilter}
            isLoading={isRunningCycle}
          />
        )}

        {activeTab === "cycle_report" && (
          <CycleReportView
            report={currentReport}
            onOpenGraphSubject={handleOpenGraphSubject}
            onSwitchTab={setActiveTab}
          />
        )}

        {activeTab === "queries" && (
          <QueriesView
            queries={queries}
            onOpenGraphSubject={handleOpenGraphSubject}
            isLoading={isRunningCycle}
          />
        )}

        {activeTab === "protocol" && (
          <ProtocolView
            currentCut={selectedCut}
            activeProtocolVersion={selectedProtocolVersion}
            deviations={deviations}
            onRefreshData={loadAllData}
            isLoading={isRunningCycle}
          />
        )}

        {activeTab === "risk_radar" && (
          <RiskRadarView
            signals={riskSignals}
            onOpenGraphFilter={handleOpenGraphSubject}
            isLoading={isRunningCycle}
          />
        )}

        {activeTab === "trace" && (
          <TraceView traceEntries={traceEntries} isLoading={isRunningCycle} />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 px-6 py-4 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>Clinical Trial Review System • CDISC SDTM Deterministic Surveillance Engine</span>
          <span className="font-mono text-[11px]">
            Node Order: Detect → Medical Review → Data Manager → Compliance → Human Gate → Execute
          </span>
        </div>
      </footer>
    </div>
  );
}
