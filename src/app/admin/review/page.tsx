"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Header } from "@/components/Header";
import {
  ShieldAlert, ShieldCheck, CheckCircle2, XCircle, AlertTriangle,
  RefreshCw, FileText, ArrowRight, ExternalLink, Eye, Play, History,
  Database, AlertOctagon, Check, ArrowLeftRight
} from "lucide-react";

interface CoverageData {
  total_schemes: number;
  total_versions: number;
  total_rules: number;
  verified_rules: number;
  unverified_bootstrap_rules: number;
  verification_coverage_pct: number;
  total_sources: number;
  stale_sources: number;
  pending_reviews: number;
}

interface ReviewQueueItem {
  id: string;
  scheme_id: string;
  scheme_name: string;
  source_title: string;
  source_url?: string;
  trust_level: string;
  status: string;
  summary: string;
  has_material_changes: boolean;
  quality_critical_count: number;
  quality_warning_count: number;
  rules_count: number;
  created_at: string;
}

interface ChangeSetDetail {
  id: string;
  scheme_name: string;
  source: {
    title: string;
    canonical_url: string;
    trust_level: string;
    publisher: string;
  };
  summary: string;
  structured_diff: {
    has_material_changes: boolean;
    summary: string;
    rule_diffs: Array<{
      fact_key: string;
      change_type: string;
      old_value: string | null;
      new_value: string | null;
      explanation: string;
      source_fragment?: string;
    }>;
    document_diffs: Array<{
      change_type: string;
      document_type: string;
      explanation: string;
      source_fragment?: string;
    }>;
  };
  quality_report: {
    is_valid_for_publication: boolean;
    critical_count: number;
    warning_count: number;
    violations: Array<{
      code: string;
      severity: string;
      message: string;
      field: string;
    }>;
  };
  rule_drafts: Array<any>;
}

export default function AdminReviewDashboard() {
  const [coverage, setCoverage] = useState<CoverageData | null>(null);
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [activeTab, setActiveTab] = useState<"queue" | "sources" | "audit">("queue");
  const [selectedChangeSet, setSelectedChangeSet] = useState<ChangeSetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [reviewerNotes, setReviewerNotes] = useState("Verified against cited official government source.");
  const [promoteVerified, setPromoteVerified] = useState(true);
  const [notification, setNotification] = useState<{ type: "success" | "error"; message: string } | null>(null);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
    try {
      const [covRes, queueRes] = await Promise.all([
        fetch("http://127.0.0.1:8000/v1/admin/verification-coverage"),
        fetch("http://127.0.0.1:8000/v1/admin/review-queue")
      ]);

      if (covRes.ok) setCoverage(await covRes.json());
      if (queueRes.ok) setQueue(await queueRes.json());
    } catch (err) {
      console.error("Failed to load admin review data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const openReviewDetail = async (id: string) => {
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/admin/review-queue/${id}`);
      if (res.ok) {
        const detail = await res.json();
        setSelectedChangeSet(detail);
      }
    } catch (err) {
      setNotification({ type: "error", message: "Failed to load review details." });
    }
  };

  const handleApprove = async () => {
    if (!selectedChangeSet) return;
    setSubmitting(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/admin/review-queue/${selectedChangeSet.id}/approve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "human_verifier",
          review_notes: reviewerNotes,
          promote_to_source_verified: promoteVerified
        })
      });

      if (res.ok) {
        setNotification({ type: "success", message: `Published new SchemeVersion for ${selectedChangeSet.scheme_name}!` });
        setSelectedChangeSet(null);
        fetchDashboardData();
      } else {
        const errData = await res.json();
        setNotification({ type: "error", message: errData.detail || "Approval rejected by quality gate." });
      }
    } catch (err) {
      setNotification({ type: "error", message: "Network error during approval." });
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!selectedChangeSet) return;
    setSubmitting(true);
    try {
      const res = await fetch(`http://127.0.0.1:8000/v1/admin/review-queue/${selectedChangeSet.id}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          reviewer_id: "human_verifier",
          reason: "Evidence clause mismatch",
          review_notes: reviewerNotes
        })
      });

      if (res.ok) {
        setNotification({ type: "success", message: `Rejected changeset for ${selectedChangeSet.scheme_name}. Production remains safe.` });
        setSelectedChangeSet(null);
        fetchDashboardData();
      }
    } catch (err) {
      setNotification({ type: "error", message: "Failed to reject changeset." });
    } finally {
      setSubmitting(false);
    }
  };

  const triggerIngestion = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/v1/admin/ingestion-runs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      if (res.ok) {
        setNotification({ type: "success", message: "Ingestion run triggered successfully." });
        fetchDashboardData();
      }
    } catch (e) {
      setNotification({ type: "error", message: "Failed to trigger ingestion." });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      <Header />

      <main className="flex-1 container mx-auto px-4 py-8 max-w-7xl">
        {/* Top Header */}
        <div className="flex flex-col md:flex-row md:items-center justify-between pb-6 border-b border-white/10 gap-4">
          <div>
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="text-purple-400 border-purple-500/40 bg-purple-950/30">
                Phase 3 Governance
              </Badge>
              <span className="text-xs text-slate-400">Rule of Law & Source Provenance</span>
            </div>
            <h1 className="text-3xl font-extrabold tracking-tight mt-1 text-white">
              Scheme Ingestion & Human Review Hub
            </h1>
            <p className="text-sm text-slate-400 mt-0.5">
              Machine-extracted drafts require official evidence and human verification before production publication.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={fetchDashboardData}
              disabled={loading}
              className="border-white/10 text-slate-300 hover:text-white"
            >
              <RefreshCw className={`w-4 h-4 mr-1.5 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={triggerIngestion}
              className="bg-purple-600 hover:bg-purple-700 text-white font-medium"
            >
              <Play className="w-4 h-4 mr-1.5 fill-current" />
              Run Ingestion
            </Button>
          </div>
        </div>

        {/* Notifications */}
        {notification && (
          <div className={`mt-4 p-3 rounded-xl border text-sm flex items-center justify-between ${
            notification.type === "success"
              ? "bg-emerald-950/50 border-emerald-500/40 text-emerald-200"
              : "bg-rose-950/50 border-rose-500/40 text-rose-200"
          }`}>
            <span>{notification.message}</span>
            <button onClick={() => setNotification(null)} className="text-xs opacity-70 hover:opacity-100">Dismiss</button>
          </div>
        )}

        {/* Metric Cards */}
        {coverage && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6">
            <Card className="bg-white/[0.03] border-white/10">
              <CardContent className="pt-5 pb-4">
                <p className="text-xs text-slate-400 font-medium">Verification Coverage</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-purple-400">{coverage.verification_coverage_pct}%</span>
                  <span className="text-xs text-slate-500">of rules</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">{coverage.verified_rules} verified / {coverage.total_rules} total</p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/10">
              <CardContent className="pt-5 pb-4">
                <p className="text-xs text-slate-400 font-medium">Pending Review</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-amber-400">{coverage.pending_reviews}</span>
                  <span className="text-xs text-slate-500">changesets</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Awaiting human sign-off</p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/10">
              <CardContent className="pt-5 pb-4">
                <p className="text-xs text-slate-400 font-medium">Bootstrap Legacy Rules</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-slate-300">{coverage.unverified_bootstrap_rules}</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Unverified CSV baseline</p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/10">
              <CardContent className="pt-5 pb-4">
                <p className="text-xs text-slate-400 font-medium">Official Sources</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className="text-2xl font-bold text-blue-400">{coverage.total_sources}</span>
                  <span className="text-xs text-slate-500">registered</span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Gazette, Portals & PDFs</p>
              </CardContent>
            </Card>

            <Card className="bg-white/[0.03] border-white/10">
              <CardContent className="pt-5 pb-4">
                <p className="text-xs text-slate-400 font-medium">Stale Sources</p>
                <div className="flex items-baseline gap-2 mt-1">
                  <span className={`text-2xl font-bold ${coverage.stale_sources > 0 ? "text-rose-400" : "text-emerald-400"}`}>
                    {coverage.stale_sources}
                  </span>
                </div>
                <p className="text-[11px] text-slate-500 mt-1">Exceeding refresh policy</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabs */}
        <div className="flex items-center gap-3 mt-8 border-b border-white/10 pb-2">
          <button
            onClick={() => setActiveTab("queue")}
            className={`text-sm font-semibold pb-2 border-b-2 transition-colors ${
              activeTab === "queue" ? "border-purple-500 text-white" : "border-transparent text-slate-400 hover:text-slate-200"
            }`}
          >
            Review Queue ({queue.length})
          </button>
        </div>

        {/* Review Queue Table */}
        {activeTab === "queue" && (
          <div className="mt-6 space-y-4">
            {queue.length === 0 ? (
              <Card className="bg-white/[0.02] border-white/10 text-center py-12">
                <CardContent>
                  <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto mb-3" />
                  <h3 className="text-lg font-bold text-white">Review Queue is Clear</h3>
                  <p className="text-sm text-slate-400 mt-1 max-w-md mx-auto">
                    All ingested source drafts have been reviewed. Run a new ingestion cycle to fetch official guideline updates.
                  </p>
                  <Button onClick={triggerIngestion} className="mt-4 bg-purple-600 hover:bg-purple-700">
                    Run Ingestion Cycle
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <div className="grid gap-4">
                {queue.map((item) => (
                  <Card key={item.id} className="bg-white/[0.02] border-white/10 hover:border-purple-500/40 transition-all">
                    <CardHeader className="pb-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <Badge variant="secondary" className="bg-purple-950 text-purple-300 border-purple-800 text-[10px]">
                              Trust Level {item.trust_level}
                            </Badge>
                            <span className="text-xs text-slate-400">{item.source_title}</span>
                          </div>
                          <CardTitle className="text-lg font-bold text-white mt-1">
                            {item.scheme_name}
                          </CardTitle>
                        </div>
                        <Button
                          size="sm"
                          onClick={() => openReviewDetail(item.id)}
                          className="bg-purple-600 hover:bg-purple-700 text-white text-xs gap-1"
                        >
                          <Eye className="w-3.5 h-3.5" />
                          Inspect & Verify
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent className="pt-0 text-sm text-slate-300">
                      <p className="line-clamp-2 text-slate-400">{item.summary}</p>
                      <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                        <span>Rules extracted: <strong className="text-slate-300">{item.rules_count}</strong></span>
                        {item.quality_critical_count > 0 && (
                          <span className="text-rose-400 font-semibold flex items-center gap-1">
                            <AlertOctagon className="w-3 h-3" /> {item.quality_critical_count} critical quality issues
                          </span>
                        )}
                        {item.quality_warning_count > 0 && (
                          <span className="text-amber-400 flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3" /> {item.quality_warning_count} warnings
                          </span>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Side-by-Side Review Modal / Drawer */}
        {selectedChangeSet && (
          <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 overflow-y-auto">
            <Card className="w-full max-w-5xl bg-slate-900 border-white/20 shadow-2xl max-h-[90vh] flex flex-col">
              <CardHeader className="border-b border-white/10 pb-4">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-purple-400 border-purple-500/30">
                        Staging Draft
                      </Badge>
                      <span className="text-xs text-slate-400">ID: {selectedChangeSet.id}</span>
                    </div>
                    <CardTitle className="text-2xl font-black text-white mt-1">
                      Review Proposed Changes: {selectedChangeSet.scheme_name}
                    </CardTitle>
                    <p className="text-xs text-slate-400 mt-1">
                      Source: {selectedChangeSet.source.title} ({selectedChangeSet.source.publisher})
                    </p>
                  </div>
                  <button
                    onClick={() => setSelectedChangeSet(null)}
                    className="text-slate-400 hover:text-white p-2 text-sm"
                  >
                    ✕
                  </button>
                </div>
              </CardHeader>

              <CardContent className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Quality Gate Status */}
                {selectedChangeSet.quality_report && (
                  <div className={`p-4 rounded-xl border text-sm ${
                    selectedChangeSet.quality_report.is_valid_for_publication
                      ? "bg-emerald-950/40 border-emerald-500/30 text-emerald-200"
                      : "bg-rose-950/40 border-rose-500/40 text-rose-200"
                  }`}>
                    <div className="flex items-center gap-2 font-bold">
                      {selectedChangeSet.quality_report.is_valid_for_publication ? (
                        <>
                          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                          Data Quality Gate: Cleared for Publication
                        </>
                      ) : (
                        <>
                          <AlertOctagon className="w-4 h-4 text-rose-400" />
                          Data Quality Gate: Publication Blocked ({selectedChangeSet.quality_report.critical_count} Critical Issues)
                        </>
                      )}
                    </div>
                    {selectedChangeSet.quality_report.violations.length > 0 && (
                      <ul className="mt-2 space-y-1 text-xs list-disc list-inside">
                        {selectedChangeSet.quality_report.violations.map((v, idx) => (
                          <li key={idx}>
                            <strong>[{v.severity}]</strong> {v.message}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* Structured Diff View */}
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-purple-400 flex items-center gap-1.5">
                    <ArrowLeftRight className="w-4 h-4" /> Structured Semantic Difference
                  </h3>
                  <div className="mt-3 space-y-3">
                    {selectedChangeSet.structured_diff.rule_diffs.map((rd, i) => (
                      <div key={i} className="p-3 rounded-lg bg-black/40 border border-white/5 flex items-start justify-between gap-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-mono text-xs text-white font-semibold">{rd.fact_key}</span>
                            <Badge variant="outline" className={`text-[10px] ${
                              rd.change_type === "modified" ? "text-amber-400 border-amber-500/30" :
                              (rd.change_type === "added" ? "text-emerald-400 border-emerald-500/30" : "text-slate-400")
                            }`}>
                              {rd.change_type}
                            </Badge>
                          </div>
                          <p className="text-xs text-slate-300">{rd.explanation}</p>
                          {rd.source_fragment && (
                            <p className="text-[11px] text-purple-300/80 italic">
                              Evidence: &quot;{rd.source_fragment}&quot;
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Source Verification Evidence */}
                {selectedChangeSet.source.canonical_url && (
                  <div className="p-4 rounded-xl bg-white/[0.02] border border-white/10 flex items-center justify-between">
                    <div>
                      <p className="text-xs text-slate-400 font-medium">Original Government Source URL</p>
                      <a
                        href={selectedChangeSet.source.canonical_url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm text-blue-400 hover:underline flex items-center gap-1 mt-0.5"
                      >
                        {selectedChangeSet.source.canonical_url} <ExternalLink className="w-3 h-3" />
                      </a>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      Trust Tier: {selectedChangeSet.source.trust_level}
                    </Badge>
                  </div>
                )}

                {/* Human Review Inputs */}
                <div className="space-y-3 pt-2">
                  <label className="text-xs font-semibold text-slate-300">Reviewer Notes & Verification Rationales</label>
                  <Textarea
                    value={reviewerNotes}
                    onChange={(e) => setReviewerNotes(e.target.value)}
                    placeholder="Enter notes on why this update is approved or rejected..."
                    className="bg-black/50 border-white/10 text-white text-xs h-20"
                  />
                  {selectedChangeSet.source.trust_level in ["A", "B"] && (
                    <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={promoteVerified}
                        onChange={(e) => setPromoteVerified(e.target.checked)}
                        className="rounded border-white/20 text-purple-600 focus:ring-purple-500"
                      />
                      Promote to <strong>source_verified</strong> (authoritative statutory status)
                    </label>
                  )}
                </div>
              </CardContent>

              <CardFooter className="border-t border-white/10 pt-4 flex justify-end gap-3 bg-black/20">
                <Button
                  variant="outline"
                  onClick={handleReject}
                  disabled={submitting}
                  className="border-rose-500/40 text-rose-400 hover:bg-rose-950/30 text-xs"
                >
                  <XCircle className="w-3.5 h-3.5 mr-1" />
                  Reject Candidate
                </Button>
                <Button
                  onClick={handleApprove}
                  disabled={submitting || !selectedChangeSet.quality_report?.is_valid_for_publication}
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs"
                >
                  <Check className="w-3.5 h-3.5 mr-1" />
                  Approve & Publish Version
                </Button>
              </CardFooter>
            </Card>
          </div>
        )}
      </main>
    </div>
  );
}
