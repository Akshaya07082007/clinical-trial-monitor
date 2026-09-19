import React, { useState } from "react";
import {
  HelpCircle,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  AlertCircle,
  FileText,
  ExternalLink,
  ChevronDown
} from "lucide-react";
import { QueryRecord } from "../types";

interface QueriesViewProps {
  queries: QueryRecord[];
  onOpenGraphSubject?: (subjectId: string) => void;
  isLoading: boolean;
}

const STATUS_CONFIG: Record<string, { bg: string; text: string; border: string }> = {
  OPEN: { bg: "bg-blue-500/20", text: "text-blue-300", border: "border-blue-500/30" },
  "ON HOLD": { bg: "bg-amber-500/20", text: "text-amber-300", border: "border-amber-500/30" },
  ANSWERED: { bg: "bg-purple-500/20", text: "text-purple-300", border: "border-purple-500/30" },
  CLOSED: { bg: "bg-emerald-500/20", text: "text-emerald-300", border: "border-emerald-500/30" }
};

export const QueriesView: React.FC<QueriesViewProps> = ({
  queries,
  onOpenGraphSubject,
  isLoading
}) => {
  const [searchTerm, setSearchTerm] = useState("");
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [domainFilter, setDomainFilter] = useState("ALL");
  const [siteFilter, setSiteFilter] = useState("ALL");

  const sites = Array.from(new Set(queries.map((q) => q.site))).sort();
  const domains = Array.from(new Set(queries.map((q) => q.domain))).sort();

  const filteredQueries = queries.filter((q) => {
    if (statusFilter !== "ALL" && q.status !== statusFilter) return false;
    if (domainFilter !== "ALL" && q.domain !== domainFilter) return false;
    if (siteFilter !== "ALL" && q.site !== siteFilter) return false;
    if (searchTerm.trim()) {
      const s = searchTerm.toLowerCase();
      return (
        q.query_id.toLowerCase().includes(s) ||
        q.subject.toLowerCase().includes(s) ||
        q.issue.toLowerCase().includes(s) ||
        q.requested_action.toLowerCase().includes(s)
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
            <div className="p-2.5 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-400">
              <HelpCircle className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-base font-semibold text-white">
                  Node 3: Data Manager Clinical Queries
                </h2>
                <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-purple-500/20 text-purple-300 border border-purple-500/30">
                  Deduplicated 4-Key Architecture
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5 leading-relaxed max-w-3xl">
                Actionable site queries derived from raw study data discrepancies (e.g. AE onset before first dose,
                missing exposure doses, lab unit mismatches). Deduplicated by <em>subject + domain + sequence + issue_type</em>.
                Tracks attempt counts and flags unresponsive sites as ON HOLD.
              </p>
            </div>
          </div>

          <div className="bg-slate-800/80 px-4 py-2 rounded-lg border border-slate-700 text-center shrink-0">
            <span className="block text-xl font-bold text-purple-400">{queries.length}</span>
            <span className="text-[10px] uppercase font-semibold text-slate-400 tracking-wider">
              Total Queries Raised
            </span>
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-3.5 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-2">
          {/* Status filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg">
            <span className="text-slate-400">Status:</span>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">OPEN</option>
              <option value="ON HOLD">ON HOLD</option>
              <option value="ANSWERED">ANSWERED</option>
              <option value="CLOSED">CLOSED</option>
            </select>
          </div>

          {/* Domain filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg">
            <span className="text-slate-400">Domain:</span>
            <select
              value={domainFilter}
              onChange={(e) => setDomainFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Domains</option>
              {domains.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </div>

          {/* Site filter */}
          <div className="flex items-center gap-1.5 bg-slate-800/80 border border-slate-700 px-2.5 py-1 rounded-lg">
            <span className="text-slate-400">Site:</span>
            <select
              value={siteFilter}
              onChange={(e) => setSiteFilter(e.target.value)}
              className="bg-transparent text-slate-200 focus:outline-none"
            >
              <option value="ALL">All Sites</option>
              {sites.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search */}
        <div className="relative">
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search queries..."
            className="bg-slate-800/80 border border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-purple-500 w-48"
          />
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
        </div>
      </div>

      {/* Queries List */}
      <div className="space-y-3">
        {filteredQueries.length === 0 ? (
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-8 text-center text-slate-400">
            <CheckCircle2 className="w-8 h-8 text-emerald-400 mx-auto mb-2 opacity-80" />
            <p className="text-sm font-medium text-slate-300">No Queries Match Filters</p>
            <p className="text-xs text-slate-500 mt-1">Run cycle or adjust search parameters.</p>
          </div>
        ) : (
          filteredQueries.map((q) => {
            const statusConfig = STATUS_CONFIG[q.status] || STATUS_CONFIG.OPEN;

            return (
              <div
                key={q.query_id}
                className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden shadow-xs hover:border-slate-700 transition-all text-xs"
              >
                {/* Header */}
                <div className="bg-slate-800/60 px-5 py-3 border-b border-slate-800 flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs font-bold text-purple-400 bg-purple-500/10 border border-purple-500/20 px-2.5 py-0.5 rounded">
                      {q.query_id}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                      Domain: {q.domain} (Seq {q.sequence})
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-300 font-mono">
                      Subject: <strong>{q.subject}</strong>
                    </span>
                    <span className="text-slate-400">•</span>
                    <span className="text-slate-300 font-mono">
                      Site: <strong>{q.site}</strong>
                    </span>
                  </div>

                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-bold border ${statusConfig.bg} ${statusConfig.text} ${statusConfig.border}`}
                    >
                      {q.status}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[11px] font-mono text-slate-400 bg-slate-800 border border-slate-700">
                      Attempts: {q.attempt_count}
                    </span>
                    {q.external_sync_status && (
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-mono ${
                          q.external_sync_status === "SYNCED"
                            ? "bg-emerald-950 text-emerald-300 border border-emerald-800"
                            : "bg-slate-800 text-slate-400 border border-slate-700"
                        }`}
                      >
                        {q.external_sync_status}
                      </span>
                    )}
                  </div>
                </div>

                {/* Body */}
                <div className="p-5 space-y-3">
                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Data Issue Description
                    </span>
                    <p className="text-slate-200 text-sm leading-relaxed bg-slate-800/30 p-3 rounded-lg border border-slate-800">
                      {q.issue}
                    </p>
                  </div>

                  <div>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block mb-1">
                      Requested Action for Site Investigator
                    </span>
                    <p className="text-slate-300 leading-normal bg-slate-950/40 p-2.5 rounded-lg border border-slate-800/80">
                      {q.requested_action}
                    </p>
                  </div>

                  {/* Evidence Citation */}
                  {q.evidence && (
                    <div className="pt-2 border-t border-slate-800 flex flex-wrap items-center justify-between gap-2 text-[11px] font-mono text-slate-400">
                      <div className="flex items-center gap-2">
                        <FileText className="w-3.5 h-3.5 text-slate-500" />
                        <span>Source Document: {q.evidence.SOURCE_DOC || "CRF Entry"}</span>
                      </div>
                      {onOpenGraphSubject && (
                        <button
                          onClick={() => onOpenGraphSubject(q.subject)}
                          className="text-indigo-400 hover:text-indigo-300 hover:underline cursor-pointer"
                        >
                          View Subject Records in Graph →
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
