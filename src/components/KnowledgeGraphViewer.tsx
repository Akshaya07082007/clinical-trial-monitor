import React, { useState, useEffect, useMemo, useRef } from "react";
import {
  Database,
  Search,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Filter,
  Sparkles,
  ChevronRight,
  Info,
  ExternalLink,
  Layers,
  FileText
} from "lucide-react";
import { CytoscapeGraphData, GraphNode, GraphEdge } from "../types";
import { askKnowledgeGraphClarify } from "../api";

interface KnowledgeGraphViewerProps {
  graphData: CytoscapeGraphData | null;
  selectedSubjectFilter: string | null;
  onSelectSubjectFilter: (subj: string | null) => void;
  isLoading: boolean;
}

const TYPE_COLORS: Record<string, { bg: string; border: string; text: string; dot: string }> = {
  SUBJECT: { bg: "bg-blue-500/20", border: "border-blue-500", text: "text-blue-300", dot: "#3b82f6" },
  SITE: { bg: "bg-emerald-500/20", border: "border-emerald-500", text: "text-emerald-300", dot: "#10b981" },
  VISIT: { bg: "bg-slate-500/20", border: "border-slate-500", text: "text-slate-300", dot: "#64748b" },
  LAB: { bg: "bg-cyan-500/20", border: "border-cyan-500", text: "text-cyan-300", dot: "#06b6d4" },
  AE: { bg: "bg-rose-500/20", border: "border-rose-500", text: "text-rose-300", dot: "#f43f5e" },
  EXPOSURE: { bg: "bg-amber-500/20", border: "border-amber-500", text: "text-amber-300", dot: "#f59e0b" },
  MED: { bg: "bg-purple-500/20", border: "border-purple-500", text: "text-purple-300", dot: "#a855f7" },
  MH: { bg: "bg-pink-500/20", border: "border-pink-500", text: "text-pink-300", dot: "#ec4899" },
  DEVIATION: { bg: "bg-orange-500/20", border: "border-orange-500", text: "text-orange-300", dot: "#f97316" },
  QUERY: { bg: "bg-indigo-500/20", border: "border-indigo-500", text: "text-indigo-300", dot: "#6366f1" },
  ESCALATION: { bg: "bg-red-500/20", border: "border-red-500", text: "text-red-300", dot: "#ef4444" },
  PROTOCOL: { bg: "bg-teal-500/20", border: "border-teal-500", text: "text-teal-300", dot: "#14b8a6" }
};

export const KnowledgeGraphViewer: React.FC<KnowledgeGraphViewerProps> = ({
  graphData,
  selectedSubjectFilter,
  onSelectSubjectFilter,
  isLoading
}) => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [typeFilter, setTypeFilter] = useState<string>("ALL");
  const [zoomLevel, setZoomLevel] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Clarify Question State
  const [clarifySubject, setClarifySubject] = useState("042-S01-002");
  const [clarifyQuestion, setClarifyQuestion] = useState(
    "What was the screening ALT and are they taking acetaminophen?"
  );
  const [clarifyResult, setClarifyResult] = useState<{
    answer: string;
    evidence: any[];
    search_log: string[];
  } | null>(null);
  const [isAskingClarify, setIsAskingClarify] = useState(false);

  // Extract all unique subjects from nodes
  const subjectList = useMemo(() => {
    if (!graphData) return [];
    return graphData.nodes
      .filter((n) => n.data.type === "SUBJECT")
      .map((n) => n.data.id.replace("SUBJ:", ""));
  }, [graphData]);

  // Compute node positions using deterministic circular layout grouped by subject/type
  const positionedNodes = useMemo(() => {
    if (!graphData) return [];

    let filteredNodes = graphData.nodes;

    // Filter by subject if selected
    if (selectedSubjectFilter) {
      const targetSubj = selectedSubjectFilter;
      filteredNodes = graphData.nodes.filter((n) => {
        const d = n.data;
        if (d.type === "SUBJECT" && d.id.includes(targetSubj)) return true;
        if (d.details && (d.details.subject === targetSubj || d.details.subject_id === targetSubj)) return true;
        if (d.id.includes(targetSubj)) return true;
        return false;
      });
    }

    // Filter by type
    if (typeFilter !== "ALL") {
      filteredNodes = filteredNodes.filter((n) => n.data.type === typeFilter);
    }

    // Filter by search
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase();
      filteredNodes = filteredNodes.filter(
        (n) => n.data.label.toLowerCase().includes(q) || n.data.id.toLowerCase().includes(q)
      );
    }

    // Calculate layout positions
    const width = 800;
    const height = 550;
    const centerX = width / 2;
    const centerY = height / 2;
    const total = filteredNodes.length;

    return filteredNodes.map((n, idx) => {
      // Golden ratio spiral / ring distribution
      const radius = total > 1 ? 70 + Math.sqrt(idx / total) * 180 : 0;
      const angle = idx * 2.399963; // golden angle in radians
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);

      return {
        ...n,
        x,
        y
      };
    });
  }, [graphData, selectedSubjectFilter, typeFilter, searchTerm]);

  // Edges connecting visible nodes
  const visibleEdges = useMemo(() => {
    if (!graphData) return [];
    const visibleNodeIds = new Set(positionedNodes.map((n) => n.data.id));

    return graphData.edges
      .filter((e) => visibleNodeIds.has(e.data.source) && visibleNodeIds.has(e.data.target))
      .map((e) => {
        const sourceNode = positionedNodes.find((n) => n.data.id === e.data.source);
        const targetNode = positionedNodes.find((n) => n.data.id === e.data.target);
        return {
          ...e,
          x1: sourceNode?.x || 0,
          y1: sourceNode?.y || 0,
          x2: targetNode?.x || 0,
          y2: targetNode?.y || 0
        };
      });
  }, [graphData, positionedNodes]);

  const handleAskClarify = async () => {
    if (!clarifySubject || !clarifyQuestion.trim()) return;
    setIsAskingClarify(true);
    try {
      const res = await askKnowledgeGraphClarify(clarifySubject, clarifyQuestion);
      setClarifyResult(res);
    } catch (err: any) {
      alert(`CLARIFY Search Error: ${err.message}`);
    } finally {
      setIsAskingClarify(false);
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  return (
    <div className="space-y-4">
      {/* Top Banner & CLARIFY Engine Search Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 mb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-indigo-500/10 border border-indigo-500/20 rounded-lg text-indigo-400">
              <Database className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                <span>Clinical Knowledge Graph & CLARIFY Engine</span>
                <span className="text-[11px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                  {graphData ? `${graphData.nodes.length} Nodes • ${graphData.edges.length} Edges` : "Loading..."}
                </span>
              </h2>
              <p className="text-xs text-slate-400">
                Multi-relational NetworkX graph mapping CDISC SDTM clinical records, protocol versions, queries, and escalations.
              </p>
            </div>
          </div>
        </div>

        {/* Interactive CLARIFY Bar */}
        <div className="bg-slate-950/80 border border-indigo-500/30 rounded-xl p-3.5 space-y-2.5">
          <div className="flex items-center gap-2 text-indigo-300 text-xs font-semibold">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <span>Interactive CLARIFY Query Engine (Evidence-Backed Graph Search)</span>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
            <div className="w-full sm:w-48 shrink-0">
              <select
                value={clarifySubject}
                onChange={(e) => setClarifySubject(e.target.value)}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              >
                {subjectList.map((s) => (
                  <option key={s} value={s}>
                    Subject: {s}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1 flex gap-2">
              <input
                type="text"
                value={clarifyQuestion}
                onChange={(e) => setClarifyQuestion(e.target.value)}
                placeholder="Ask CLARIFY engine (e.g. screening ALT values, concomitant medications)..."
                className="flex-1 bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
              <button
                onClick={handleAskClarify}
                disabled={isAskingClarify}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shrink-0 cursor-pointer disabled:opacity-50"
              >
                {isAskingClarify ? (
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                ) : (
                  <Search className="w-3.5 h-3.5" />
                )}
                <span>Run Clarify</span>
              </button>
            </div>
          </div>

          {/* Quick Presets */}
          <div className="flex flex-wrap items-center gap-2 text-[11px] text-slate-400">
            <span className="text-slate-500">Suggested queries:</span>
            <button
              onClick={() => {
                setClarifySubject("042-S01-002");
                setClarifyQuestion("What was the screening ALT and any concomitant medication?");
              }}
              className="text-indigo-400 hover:underline cursor-pointer"
            >
              042-S01-002 (Screening ALT & ConMeds)
            </button>
            <span>•</span>
            <button
              onClick={() => {
                setClarifySubject("042-S03-005");
                setClarifyQuestion("Check first dose date versus adverse event onset timing.");
              }}
              className="text-indigo-400 hover:underline cursor-pointer"
            >
              042-S03-005 (Dose vs AE Chronology)
            </button>
            <span>•</span>
            <button
              onClick={() => {
                setClarifySubject("042-S02-004");
                setClarifyQuestion("Verify hospitalization status and serious event classification.");
              }}
              className="text-indigo-400 hover:underline cursor-pointer"
            >
              042-S02-004 (Hospitalization & SAE Miscoding)
            </button>
          </div>

          {/* CLARIFY Result Card */}
          {clarifyResult && (
            <div className="bg-slate-900 border border-indigo-500/30 rounded-lg p-3.5 space-y-2 mt-2 animate-in fade-in duration-200">
              <div className="flex items-center justify-between text-xs font-semibold">
                <span className="text-indigo-300">Evidence Synthesized from Graph Records:</span>
                <button
                  onClick={() => setClarifyResult(null)}
                  className="text-slate-500 hover:text-slate-300 text-[11px]"
                >
                  Dismiss
                </button>
              </div>

              <p className="text-xs text-slate-200 leading-relaxed font-medium bg-slate-950/60 p-2.5 rounded border border-slate-800">
                {clarifyResult.answer}
              </p>

              {/* Traversed Records Citations */}
              {clarifyResult.evidence && clarifyResult.evidence.length > 0 && (
                <div className="space-y-1 pt-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400 tracking-wider">
                    Graph Records Citations:
                  </span>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-[11px] font-mono">
                    {clarifyResult.evidence.map((ev, i) => (
                      <div key={i} className="bg-slate-950/80 p-2 rounded border border-slate-800 flex flex-col">
                        <span className="text-indigo-400 font-semibold">{ev.category}</span>
                        <span className="text-slate-300">{ev.detail || ev.name}</span>
                        {ev.value && <span className="text-emerald-400">Value: {ev.value}</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Graph Visual Explorer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        {/* Main Canvas Area (3 cols) */}
        <div className="lg:col-span-3 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          {/* Controls Bar */}
          <div className="bg-slate-800/60 px-4 py-2.5 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
            {/* Filters */}
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex items-center gap-1 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1">
                <Filter className="w-3.5 h-3.5 text-slate-400" />
                <select
                  value={typeFilter}
                  onChange={(e) => setTypeFilter(e.target.value)}
                  className="bg-transparent text-slate-200 text-xs focus:outline-none"
                >
                  <option value="ALL">All Entity Types</option>
                  <option value="SUBJECT">Subjects</option>
                  <option value="SITE">Sites</option>
                  <option value="AE">Adverse Events</option>
                  <option value="LAB">Labs</option>
                  <option value="EXPOSURE">Doses</option>
                  <option value="MED">Medications</option>
                  <option value="DEVIATION">Deviations</option>
                  <option value="QUERY">Queries</option>
                  <option value="ESCALATION">Escalations</option>
                </select>
              </div>

              {/* Subject Isolation Filter */}
              <div className="flex items-center gap-1 bg-slate-900 border border-slate-700 rounded-lg px-2 py-1">
                <span className="text-slate-400">Subject:</span>
                <select
                  value={selectedSubjectFilter || "ALL"}
                  onChange={(e) => onSelectSubjectFilter(e.target.value === "ALL" ? null : e.target.value)}
                  className="bg-transparent text-slate-200 text-xs focus:outline-none"
                >
                  <option value="ALL">Entire Trial (All)</option>
                  {subjectList.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>

              {/* Search text */}
              <div className="relative">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Filter nodes..."
                  className="bg-slate-900 border border-slate-700 rounded-lg pl-7 pr-2 py-1 text-xs text-slate-200 focus:outline-none w-32 focus:w-44 transition-all"
                />
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2 top-2" />
              </div>
            </div>

            {/* Zoom Controls */}
            <div className="flex items-center gap-1">
              <button
                onClick={() => setZoomLevel((z) => Math.max(0.4, z - 0.15))}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-3.5 h-3.5" />
              </button>
              <span className="font-mono text-[11px] text-slate-400 px-1">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={() => setZoomLevel((z) => Math.min(2.5, z + 0.15))}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => {
                  setZoomLevel(1);
                  setPan({ x: 0, y: 0 });
                }}
                className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors ml-1"
                title="Reset View"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>

          {/* SVG Graph Viewport */}
          <div
            className="relative h-[480px] bg-slate-950/90 cursor-grab active:cursor-grabbing overflow-hidden select-none"
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
          >
            {/* Subtle Grid Pattern */}
            <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:16px_16px] pointer-events-none opacity-40" />

            <svg
              className="w-full h-full"
              viewBox="0 0 800 550"
              style={{
                transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoomLevel})`,
                transformOrigin: "center center",
                transition: isDragging ? "none" : "transform 0.1s ease-out"
              }}
            >
              {/* Edges */}
              <g className="edges opacity-40">
                {visibleEdges.map((e, idx) => (
                  <line
                    key={idx}
                    x1={e.x1}
                    y1={e.y1}
                    x2={e.x2}
                    y2={e.y2}
                    stroke="#475569"
                    strokeWidth="1.2"
                    strokeDasharray={e.data.label.includes("VIOLATES") || e.data.label.includes("ESCALATION") ? "3,3" : undefined}
                  />
                ))}
              </g>

              {/* Edge Labels for selected or prominent connections */}
              <g className="edge-labels">
                {visibleEdges.map((e, idx) => {
                  if (!e.data.label.includes("ESCALATION") && !e.data.label.includes("VIOLATES")) return null;
                  const mx = (e.x1 + e.x2) / 2;
                  const my = (e.y1 + e.y2) / 2;
                  return (
                    <text
                      key={idx}
                      x={mx}
                      y={my}
                      fill="#f43f5e"
                      fontSize="9"
                      fontFamily="monospace"
                      textAnchor="middle"
                      className="pointer-events-none"
                    >
                      {e.data.label}
                    </text>
                  );
                })}
              </g>

              {/* Nodes */}
              <g className="nodes">
                {positionedNodes.map((node) => {
                  const colorConfig = TYPE_COLORS[node.data.type] || TYPE_COLORS.SUBJECT;
                  const isSelected = selectedNode?.data.id === node.data.id;
                  const radius = node.data.type === "SUBJECT" ? 18 : node.data.type === "SITE" ? 16 : 13;

                  return (
                    <g
                      key={node.data.id}
                      transform={`translate(${node.x}, ${node.y})`}
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedNode(node);
                      }}
                      className="cursor-pointer group"
                    >
                      {/* Node Circle Halo on Select */}
                      {isSelected && (
                        <circle
                          r={radius + 6}
                          fill="none"
                          stroke="#10b981"
                          strokeWidth="2"
                          strokeDasharray="4,4"
                          className="animate-spin"
                        />
                      )}

                      {/* Main Node Circle */}
                      <circle
                        r={radius}
                        fill={colorConfig.dot}
                        fillOpacity="0.25"
                        stroke={colorConfig.dot}
                        strokeWidth={isSelected ? "2.5" : "1.5"}
                        className="transition-all group-hover:fill-opacity-50"
                      />

                      {/* Node Label Text */}
                      <text
                        y={radius + 12}
                        fill="#cbd5e1"
                        fontSize="10"
                        fontFamily="sans-serif"
                        fontWeight="500"
                        textAnchor="middle"
                        className="pointer-events-none"
                      >
                        {node.data.label}
                      </text>

                      {/* Small Type abbreviation inside node */}
                      <text
                        y="3.5"
                        fill="#ffffff"
                        fontSize="8"
                        fontFamily="monospace"
                        fontWeight="bold"
                        textAnchor="middle"
                        className="pointer-events-none"
                      >
                        {node.data.type.slice(0, 3)}
                      </text>
                    </g>
                  );
                })}
              </g>
            </svg>

            {/* Instruction tooltip */}
            <div className="absolute bottom-2 left-3 text-[10px] text-slate-500 pointer-events-none">
              Drag to pan • Click node to inspect details • Zoom in/out
            </div>
          </div>
        </div>

        {/* Node Inspector Drawer (1 col) */}
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col justify-between">
          <div>
            <h3 className="text-xs font-semibold text-slate-200 uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <Info className="w-3.5 h-3.5 text-indigo-400" />
              Node Inspector
            </h3>

            {selectedNode ? (
              <div className="space-y-3 text-xs">
                {/* Header */}
                <div className="bg-slate-950/60 p-3 rounded-lg border border-slate-800">
                  <span
                    className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold mb-1 ${
                      TYPE_COLORS[selectedNode.data.type]?.bg || "bg-slate-800"
                    } ${TYPE_COLORS[selectedNode.data.type]?.text || "text-slate-300"}`}
                  >
                    {selectedNode.data.type}
                  </span>
                  <div className="font-semibold text-sm text-slate-100 break-all">
                    {selectedNode.data.label}
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 break-all">
                    ID: {selectedNode.data.id}
                  </div>
                </div>

                {/* Properties list */}
                <div className="space-y-1.5 font-mono text-[11px]">
                  <span className="text-[10px] uppercase font-bold text-slate-400 font-sans block mb-1">
                    CDISC SDTM Attributes:
                  </span>
                  {selectedNode.data.details ? (
                    Object.entries(selectedNode.data.details).map(([k, v]) => {
                      if (typeof v === "object" && v !== null) return null;
                      return (
                        <div key={k} className="bg-slate-950/40 p-1.5 rounded border border-slate-800/80 flex justify-between gap-2">
                          <span className="text-slate-500">{k}:</span>
                          <span className="text-slate-200 text-right truncate">{String(v)}</span>
                        </div>
                      );
                    })
                  ) : (
                    <div className="text-slate-500 italic">No additional metadata properties</div>
                  )}
                </div>

                {/* Focus Subject Shortcut */}
                {selectedNode.data.type === "SUBJECT" && (
                  <button
                    onClick={() =>
                      onSelectSubjectFilter(selectedNode.data.id.replace("SUBJ:", ""))
                    }
                    className="w-full mt-2 py-1.5 bg-blue-600/20 hover:bg-blue-600/30 text-blue-300 border border-blue-500/30 rounded text-xs font-medium cursor-pointer transition-colors"
                  >
                    Isolate Subject Subgraph
                  </button>
                )}
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500 text-xs">
                <Layers className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p>Click any node in the graph viewport to inspect its CDISC SDTM properties.</p>
              </div>
            )}
          </div>

          {/* Graph Legend */}
          <div className="pt-3 border-t border-slate-800 mt-4">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">
              Entity Legend
            </span>
            <div className="grid grid-cols-2 gap-1.5 text-[10px] font-medium">
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-blue-500" />
                <span className="text-slate-400">Subject</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                <span className="text-slate-400">Site</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-rose-500" />
                <span className="text-slate-400">Adverse Event</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-cyan-500" />
                <span className="text-slate-400">Lab Test</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span className="text-slate-400">Dose (EX)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-indigo-500" />
                <span className="text-slate-400">Query (DM)</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-slate-400">Escalation</span>
              </div>
              <div className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-orange-500" />
                <span className="text-slate-400">Deviation</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
