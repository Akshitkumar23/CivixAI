"use client";

import React, { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import {
  ArrowLeft, ArrowRight, HelpCircle, ShieldCheck, CheckCircle2,
  Sparkles, RotateCcw, AlertCircle, Eye, RefreshCw, ChevronDown,
  User, Check, X, Lock
} from "lucide-react";

interface AllowedOption {
  value: string;
  label_en: string;
  label_hi: string;
}

interface QuestionMetadata {
  fact_key: string;
  component_type: "number" | "select" | "radio" | "boolean" | "text" | "range";
  label_en: string;
  label_hi: string;
  help_text_en?: string;
  help_text_hi?: string;
  why_asked_en: string;
  why_asked_hi: string;
  allowed_values?: AllowedOption[];
  unit?: string;
  min_value?: number;
  max_value?: number;
  sensitivity: "normal" | "financial" | "sensitive";
  scope?: string;
  can_skip: boolean;
  can_answer_unknown: boolean;
}

interface QuestionnaireProgressData {
  answered_count: number;
  unresolved_relevant_facts_count: number;
  estimated_remaining_questions: number;
  progress_pct: number;
  current_eligible_schemes_count: number;
  current_needs_info_schemes_count: number;
}

interface QuestionResponseData {
  session_id: string;
  fact_key: string;
  question: QuestionMetadata;
  why_asked: string;
  affected_schemes_count: number;
  progress: QuestionnaireProgressData;
  can_go_back: boolean;
  is_completed: boolean;
}

interface QuestionnaireStateData {
  session_id: string;
  is_completed: boolean;
  current_question?: QuestionResponseData;
  answered_facts: Record<string, any>;
  skipped_facts: string[];
  unknown_facts: string[];
  history: string[];
  progress: QuestionnaireProgressData;
}

interface AdaptiveQuestionnaireProps {
  onSwitchToClassic?: () => void;
}

export default function AdaptiveQuestionnaire({ onSwitchToClassic }: AdaptiveQuestionnaireProps) {
  const router = useRouter();
  const [sessionId, setSessionId] = useState<string>("");
  const [state, setState] = useState<QuestionnaireStateData | null>(null);
  const [currentValue, setCurrentValue] = useState<any>("");
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [showWhyAsked, setShowWhyAsked] = useState<boolean>(false);
  const [showHindi, setShowHindi] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string>("");
  const [previewOpen, setPreviewOpen] = useState<boolean>(false);
  const [previewData, setPreviewData] = useState<any>(null);

  // Initialize or restore session
  useEffect(() => {
    let sid = localStorage.getItem("civix_profile_session_id");
    if (!sid) {
      sid = "sess_" + Math.random().toString(36).substring(2, 11) + "_" + Date.now();
      localStorage.setItem("civix_profile_session_id", sid);
    }
    setSessionId(sid);
    loadState(sid);
  }, []);

  const loadState = useCallback(async (sid: string) => {
    try {
      setLoading(true);
      const res = await fetch(`/v1/profile-sessions/${sid}/questionnaire-state`);
      if (res.ok) {
        const data: QuestionnaireStateData = await res.json();
        setState(data);
        setCurrentValue("");
        setValidationError("");
        setShowWhyAsked(false);
      } else {
        // Fallback or retry creating session
        const createRes = await fetch("/v1/profile-sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_anonymous: true, facts: {} })
        });
        if (createRes.ok) {
          const createData = await createRes.json();
          localStorage.setItem("civix_profile_session_id", createData.session_id);
          setSessionId(createData.session_id);
          const stateRes = await fetch(`/v1/profile-sessions/${createData.session_id}/questionnaire-state`);
          if (stateRes.ok) {
            setState(await stateRes.json());
          }
        }
      }
    } catch (err) {
      console.error("Failed to load questionnaire state", err);
      setValidationError("Connecting to local CivixAI Intelligence Engine...");
    } finally {
      setLoading(false);
    }
  }, []);

  // Handle Answer
  const handleAnswer = async () => {
    if (!state?.current_question) return;
    const q = state.current_question.question;

    // Validate
    if (currentValue === "" || currentValue === undefined || currentValue === null) {
      setValidationError("Please select or enter an answer before continuing.");
      return;
    }

    if (q.component_type === "number") {
      const numVal = Number(currentValue);
      if (isNaN(numVal)) {
        setValidationError("Please enter a valid numeric value.");
        return;
      }
      if (q.min_value !== undefined && numVal < q.min_value) {
        setValidationError(`Value cannot be less than ${q.min_value}.`);
        return;
      }
      if (q.max_value !== undefined && numVal > q.max_value) {
        setValidationError(`Value cannot exceed ${q.max_value}.`);
        return;
      }
    }

    try {
      setSubmitting(true);
      setValidationError("");
      const res = await fetch(`/v1/profile-sessions/${sessionId}/answer`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          fact_key: q.fact_key,
          value: q.component_type === "number" ? Number(currentValue) : currentValue
        })
      });

      if (res.ok) {
        const newState = await res.json();
        setState(newState);
        setCurrentValue("");
      }
    } catch (err) {
      console.error("Error answering question:", err);
      setValidationError("Failed to record answer. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Skip
  const handleSkip = async () => {
    if (!state?.current_question) return;
    try {
      setSubmitting(true);
      const res = await fetch(`/v1/profile-sessions/${sessionId}/skip`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fact_key: state.current_question.fact_key })
      });
      if (res.ok) {
        const newState = await res.json();
        setState(newState);
        setCurrentValue("");
      }
    } catch (err) {
      console.error("Error skipping question:", err);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Unknown
  const handleUnknown = async () => {
    if (!state?.current_question) return;
    try {
      setSubmitting(true);
      const res = await fetch(`/v1/profile-sessions/${sessionId}/unknown`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ fact_key: state.current_question.fact_key })
      });
      if (res.ok) {
        const newState = await res.json();
        setState(newState);
        setCurrentValue("");
      }
    } catch (err) {
      console.error("Error marking unknown:", err);
    } finally {
      setSubmitting(false);
    }
  };

  // Handle Back
  const handleBack = async () => {
    try {
      setSubmitting(true);
      const res = await fetch(`/v1/profile-sessions/${sessionId}/back`, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      if (res.ok) {
        const newState = await res.json();
        setState(newState);
        setCurrentValue("");
      }
    } catch (err) {
      console.error("Error navigating back:", err);
    } finally {
      setSubmitting(false);
    }
  };

  // Load Preview
  const loadPreview = async () => {
    try {
      const res = await fetch(`/v1/profile-sessions/${sessionId}/recommendation-preview`);
      if (res.ok) {
        const data = await res.json();
        setPreviewData(data);
        setPreviewOpen(true);
      }
    } catch (err) {
      console.error("Failed to load recommendation preview", err);
    }
  };

  // Restart questionnaire session
  const handleStartAgain = async () => {
    if (window.confirm("Start again with a fresh session? Your previous answers will be cleared.")) {
      localStorage.removeItem("civix_profile_session_id");
      try {
        setLoading(true);
        const createRes = await fetch("/v1/profile-sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ is_anonymous: true, facts: {} })
        });
        if (createRes.ok) {
          const createData = await createRes.json();
          localStorage.setItem("civix_profile_session_id", createData.session_id);
          setSessionId(createData.session_id);
          const stateRes = await fetch(`/v1/profile-sessions/${createData.session_id}/questionnaire-state`);
          if (stateRes.ok) {
            setState(await stateRes.json());
          }
        }
      } catch (err) {
        console.error("Failed to reset questionnaire", err);
      } finally {
        setLoading(false);
      }
    }
  };

  // Navigate to full recommendations
  const handleViewResults = () => {
    router.push(`/recommendations?session_id=${sessionId}`);
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center p-16 space-y-4 text-center">
        <div className="p-4 rounded-2xl bg-blue-500/10 border border-blue-500/20 animate-pulse shadow-[0_0_30px_rgba(59,130,246,0.2)]">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-400" />
        </div>
        <p className="text-base font-semibold text-slate-300">
          {showHindi ? "नागरिक पात्रता प्रश्नावली लोड हो रही है..." : "Loading citizen eligibility assessment..."}
        </p>
        <p className="text-xs text-slate-500">
          Evaluating statutory policy rules across 135 welfare schemes
        </p>
      </div>
    );
  }

  const isCompleted = state?.is_completed || !state?.current_question;
  const currentQ = state?.current_question?.question;
  const progressPct = state?.progress?.progress_pct || 0;
  const eligibleCount = state?.progress?.current_eligible_schemes_count || 0;

  return (
    <div className="max-w-2xl mx-auto px-2 sm:px-4 py-4 sm:py-8 space-y-6">
      {/* Top Controls & Language Bar */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-1">
        <div className="flex items-center space-x-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold backdrop-blur-md shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-blue-400" />
            <span>{showHindi ? "स्मार्ट पात्रता मूल्यांकन" : "Adaptive Eligibility Engine"}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleStartAgain}
            className="text-xs text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 h-7 px-2.5 rounded-full transition-colors"
          >
            <RotateCcw className="h-3 w-3 mr-1" />
            {showHindi ? "पुनः शुरू करें" : "Start Again"}
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <div className="flex rounded-full bg-white/5 p-0.5 border border-white/10 backdrop-blur-md">
            <button
              type="button"
              onClick={() => setShowHindi(false)}
              className={`px-3 py-1 text-xs font-bold rounded-full transition-all ${
                !showHindi ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-white"
              }`}
            >
              English
            </button>
            <button
              type="button"
              onClick={() => setShowHindi(true)}
              className={`px-3 py-1 text-xs font-bold rounded-full transition-all ${
                showHindi ? "bg-blue-600 text-white shadow-md" : "text-slate-400 hover:text-white"
              }`}
            >
              हिंदी
            </button>
          </div>
        </div>
      </div>

      {/* Progress & Live Qualifying Counter Bar */}
      <div className="relative overflow-hidden rounded-2xl bg-slate-900/60 border border-white/10 p-5 backdrop-blur-xl shadow-xl space-y-3">
        <div className="flex justify-between items-center text-xs font-semibold">
          <span className="text-slate-300 flex items-center gap-1.5">
            <span className="flex h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
            {showHindi ? `प्रगति (${Math.round(progressPct)}%)` : `Assessment Progress (${Math.round(progressPct)}%)`}
          </span>
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-bold text-xs shadow-[0_0_15px_rgba(16,185,129,0.15)]">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
              {eligibleCount} {showHindi ? "पात्र योजनाएँ" : "Qualifying Schemes"}
            </span>
          </div>
        </div>

        {/* Custom Glowing Gradient Progress Bar */}
        <div className="h-2.5 w-full bg-white/10 rounded-full overflow-hidden p-[1px]">
          <div
            className="h-full bg-gradient-to-r from-blue-500 via-indigo-500 to-emerald-400 rounded-full transition-all duration-500 shadow-[0_0_12px_rgba(59,130,246,0.5)]"
            style={{ width: `${Math.max(progressPct, 5)}%` }}
          />
        </div>

        <div className="flex justify-between items-center text-[11px] text-slate-400 pt-0.5">
          <span>
            {state?.progress?.unresolved_relevant_facts_count || 0} {showHindi ? "मानदंड शेष हैं" : "criteria remaining to verify"}
          </span>
          {eligibleCount > 0 && (
            <button
              onClick={loadPreview}
              className="text-blue-400 font-bold hover:text-blue-300 flex items-center gap-1 underline underline-offset-2 transition-colors"
            >
              <Eye className="h-3 w-3" />
              {showHindi ? `पूर्वावलोकन (${eligibleCount})` : `Preview ${eligibleCount} Schemes`}
            </button>
          )}
        </div>
      </div>

      {/* Main Questionnaire Interactive Card */}
      {!isCompleted && currentQ ? (
        <div className="relative rounded-3xl bg-[#0B0F19]/90 border border-white/15 p-6 sm:p-8 backdrop-blur-2xl shadow-[0_20px_50px_rgba(0,0,0,0.7)] overflow-hidden space-y-6 transition-all duration-300">
          {/* Ambient Top Glow Line */}
          <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 via-indigo-500 to-purple-500" />
          <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />

          {/* Scope & Sensitivity Header */}
          <div className="flex items-center justify-between gap-2 border-b border-white/5 pb-4">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-slate-300 text-xs font-semibold">
              <User className="h-3.5 w-3.5 text-blue-400" />
              <span>
                {currentQ.scope === "landholding"
                  ? (showHindi ? "कृषि संपत्ति" : "Agricultural Asset")
                  : (currentQ.scope === "household"
                    ? (showHindi ? "पारिवारिक विवरण" : "Household Profile")
                    : (showHindi ? "व्यक्तिगत पात्रता" : "Individual Criteria"))}
              </span>
            </div>

            {currentQ.sensitivity !== "normal" && (
              <Badge variant="outline" className="text-[11px] bg-amber-500/10 text-amber-300 border-amber-500/20 font-medium px-2.5 py-0.5">
                <Lock className="h-3 w-3 mr-1 text-amber-400" />
                {currentQ.sensitivity === "financial"
                  ? (showHindi ? "वित्तीय रिकॉर्ड" : "Financial Info")
                  : (showHindi ? "जनसांख्यिकी" : "Demographic")}
              </Badge>
            )}
          </div>

          {/* Question Text */}
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight leading-snug drop-shadow-md">
              {showHindi ? currentQ.label_hi : currentQ.label_en}
            </h2>
            {(showHindi ? currentQ.help_text_hi : currentQ.help_text_en) && (
              <p className="text-sm sm:text-base text-slate-300 leading-relaxed font-normal">
                {showHindi ? currentQ.help_text_hi : currentQ.help_text_en}
              </p>
            )}
          </div>

          {/* Dynamic Component Tailoring */}
          <div className="space-y-4 pt-2">
            {/* Number Input */}
            {currentQ.component_type === "number" && (
              <div className="space-y-2">
                <div className="relative flex items-center">
                  <Input
                    type="number"
                    value={currentValue}
                    onChange={(e) => {
                      setCurrentValue(e.target.value);
                      setValidationError("");
                    }}
                    onKeyDown={(e) => e.key === "Enter" && handleAnswer()}
                    placeholder={showHindi ? "संख्या दर्ज करें..." : "Enter value..."}
                    className="text-xl sm:text-2xl py-6 px-5 font-bold text-white bg-black/40 border-white/15 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 rounded-2xl placeholder-slate-600 shadow-inner"
                    autoFocus
                  />
                  {currentQ.unit && (
                    <span className="absolute right-4 px-3 py-1.5 rounded-xl bg-white/10 text-xs font-bold text-blue-300 border border-white/10">
                      {currentQ.unit}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Select Dropdown */}
            {currentQ.component_type === "select" && (
              <div className="relative space-y-2">
                <select
                  value={currentValue}
                  onChange={(e) => {
                    setCurrentValue(e.target.value);
                    setValidationError("");
                  }}
                  className="w-full text-base font-semibold py-4 px-5 rounded-2xl border border-white/15 bg-[#0f172a] text-white focus:outline-none focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 appearance-none shadow-inner cursor-pointer"
                  autoFocus
                >
                  <option value="" className="bg-[#0f172a] text-slate-400">
                    {showHindi ? "-- एक विकल्प चुनें --" : "-- Select an option --"}
                  </option>
                  {currentQ.allowed_values?.map((opt) => (
                    <option key={opt.value} value={opt.value} className="bg-[#0f172a] text-white py-2">
                      {showHindi ? opt.label_hi : opt.label_en}
                    </option>
                  ))}
                </select>
                <div className="absolute right-5 top-4 pointer-events-none text-slate-400">
                  <ChevronDown className="h-5 w-5" />
                </div>
              </div>
            )}

            {/* Radio / Option Cards */}
            {currentQ.component_type === "radio" && (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {currentQ.allowed_values?.map((opt) => {
                  const isSelected = currentValue === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => {
                        setCurrentValue(opt.value);
                        setValidationError("");
                      }}
                      className={`group relative p-4 rounded-2xl text-left border transition-all duration-200 cursor-pointer flex items-center justify-between ${
                        isSelected
                          ? "border-blue-500 bg-blue-600/20 text-white shadow-[0_0_20px_rgba(59,130,246,0.3)] ring-1 ring-blue-500"
                          : "border-white/10 bg-white/[0.03] hover:bg-white/[0.07] hover:border-white/20 text-slate-200"
                      }`}
                    >
                      <span className="text-sm sm:text-base font-semibold pr-3 leading-snug">
                        {showHindi ? opt.label_hi : opt.label_en}
                      </span>
                      <div
                        className={`h-5 w-5 rounded-full border flex items-center justify-center flex-shrink-0 transition-all ${
                          isSelected
                            ? "border-blue-400 bg-blue-500 text-white"
                            : "border-white/30 bg-transparent group-hover:border-white/50"
                        }`}
                      >
                        {isSelected && <Check className="h-3 w-3 stroke-[3]" />}
                      </div>
                    </button>
                  );
                })}
              </div>
            )}

            {/* Boolean Yes / No Interactive Cards */}
            {currentQ.component_type === "boolean" && (
              <div className="grid grid-cols-2 gap-4">
                <button
                  type="button"
                  onClick={() => {
                    setCurrentValue(true);
                    setValidationError("");
                  }}
                  className={`py-6 px-4 rounded-2xl text-center font-bold text-lg border flex flex-col items-center justify-center gap-2 transition-all duration-200 cursor-pointer ${
                    currentValue === true
                      ? "border-emerald-500 bg-emerald-500/20 text-white shadow-[0_0_25px_rgba(16,185,129,0.35)] ring-2 ring-emerald-500 scale-[1.02]"
                      : "border-white/10 bg-white/[0.03] hover:bg-emerald-500/10 hover:border-emerald-500/30 text-slate-200 hover:text-white"
                  }`}
                >
                  <div className={`p-2.5 rounded-full ${currentValue === true ? "bg-emerald-500 text-white" : "bg-white/5 text-emerald-400"}`}>
                    <Check className="h-5 w-5 stroke-[3]" />
                  </div>
                  <span>{showHindi ? "हाँ (Yes)" : "Yes"}</span>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    setCurrentValue(false);
                    setValidationError("");
                  }}
                  className={`py-6 px-4 rounded-2xl text-center font-bold text-lg border flex flex-col items-center justify-center gap-2 transition-all duration-200 cursor-pointer ${
                    currentValue === false
                      ? "border-rose-500 bg-rose-500/20 text-white shadow-[0_0_25px_rgba(244,63,94,0.35)] ring-2 ring-rose-500 scale-[1.02]"
                      : "border-white/10 bg-white/[0.03] hover:bg-rose-500/10 hover:border-rose-500/30 text-slate-200 hover:text-white"
                  }`}
                >
                  <div className={`p-2.5 rounded-full ${currentValue === false ? "bg-rose-500 text-white" : "bg-white/5 text-rose-400"}`}>
                    <X className="h-5 w-5 stroke-[3]" />
                  </div>
                  <span>{showHindi ? "नहीं (No)" : "No"}</span>
                </button>
              </div>
            )}

            {/* Free Text Input */}
            {currentQ.component_type === "text" && (
              <div className="space-y-2">
                <Input
                  type="text"
                  value={currentValue}
                  onChange={(e) => {
                    setCurrentValue(e.target.value);
                    setValidationError("");
                  }}
                  onKeyDown={(e) => e.key === "Enter" && handleAnswer()}
                  placeholder={showHindi ? "विवरण दर्ज करें..." : "Enter details..."}
                  className="text-base sm:text-lg py-5 px-5 font-semibold text-white bg-black/40 border-white/15 focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 rounded-2xl placeholder-slate-600"
                  autoFocus
                />
              </div>
            )}

            {/* Validation Feedback */}
            {validationError && (
              <div className="flex items-center gap-2.5 text-rose-400 text-xs sm:text-sm font-semibold bg-rose-500/10 border border-rose-500/20 rounded-xl px-4 py-3 animate-fadeIn">
                <AlertCircle className="h-4 w-4 flex-shrink-0 text-rose-400" />
                <span>{validationError}</span>
              </div>
            )}

            {/* Transparent Rationale Accordion */}
            <div className="pt-3 border-t border-white/5">
              <button
                type="button"
                onClick={() => setShowWhyAsked(!showWhyAsked)}
                className="text-xs font-semibold text-slate-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors"
              >
                <HelpCircle className="h-3.5 w-3.5 text-blue-400" />
                <span>{showWhyAsked ? (showHindi ? "छिपाएं" : "Hide policy reasoning") : (showHindi ? "यह प्रश्न क्यों पूछा जा रहा है?" : "Why do we ask this question?")}</span>
              </button>
              {showWhyAsked && (
                <div className="mt-3 p-4 bg-white/[0.03] rounded-2xl text-xs text-slate-300 space-y-2 border border-white/10 leading-relaxed animate-fadeIn">
                  <p className="font-bold text-white flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-emerald-400" />
                    {showHindi ? currentQ.why_asked_hi : currentQ.why_asked_en}
                  </p>
                  <p className="text-[11px] text-slate-400">
                    {state?.current_question?.why_asked}
                  </p>
                  <p className="text-[10px] text-slate-500 pt-1 border-t border-white/5 flex items-center gap-1">
                    <Lock className="h-3 w-3" />
                    {showHindi ? "डीपीडीपी अधिनियम 2023 के तहत सुरक्षित। डेटा केवल पात्रता के लिए संसाधित होता है।" : "Protected under Digital Personal Data Protection (DPDP) Act 2023. Answer is processed exclusively to compute statutory benefits."}
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Action Footer */}
          <div className="pt-4 border-t border-white/10 flex flex-col sm:flex-row gap-3 items-center justify-between">
            <div className="flex flex-wrap items-center gap-2 w-full sm:w-auto">
              {state?.current_question?.can_go_back && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleBack}
                  disabled={submitting}
                  className="border-white/15 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl text-xs font-semibold h-11 px-4"
                >
                  <ArrowLeft className="h-3.5 w-3.5 mr-1.5" />
                  {showHindi ? "पीछे" : "Back"}
                </Button>
              )}
              {currentQ.can_answer_unknown && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleUnknown}
                  disabled={submitting}
                  className="text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded-xl text-xs font-medium h-11 px-3"
                >
                  {showHindi ? "मुझे नहीं पता" : "I don't know"}
                </Button>
              )}
              {currentQ.can_skip && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleSkip}
                  disabled={submitting}
                  className="text-slate-400 hover:text-slate-200 hover:bg-white/5 rounded-xl text-xs font-medium h-11 px-3"
                >
                  {showHindi ? "छोड़ें" : "Skip"}
                </Button>
              )}
            </div>

            <Button
              onClick={handleAnswer}
              disabled={submitting}
              className="w-full sm:w-auto h-12 px-8 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-500 hover:to-purple-500 text-white font-bold text-base rounded-2xl shadow-[0_0_25px_rgba(59,130,246,0.35)] transition-all transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {submitting ? (showHindi ? "जाँच हो रही है..." : "Checking...") : (showHindi ? "जारी रखें" : "Continue")}
              <ArrowRight className="h-4 w-4 ml-2" />
            </Button>
          </div>
        </div>
      ) : (
        /* Completion Celebration Card */
        <div className="relative rounded-3xl bg-[#0B0F19]/90 border border-emerald-500/30 p-8 sm:p-12 backdrop-blur-2xl shadow-[0_20px_60px_rgba(0,0,0,0.8)] text-center space-y-6 overflow-hidden animate-fadeIn">
          <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-emerald-400 to-teal-500" />
          <div className="absolute -top-32 left-1/2 -translate-x-1/2 w-64 h-64 bg-emerald-500/20 rounded-full blur-3xl pointer-events-none" />

          <div className="mx-auto bg-emerald-500/10 border border-emerald-500/30 rounded-full h-20 w-20 flex items-center justify-center shadow-[0_0_30px_rgba(16,185,129,0.3)]">
            <CheckCircle2 className="h-10 w-10 text-emerald-400" />
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">
              {showHindi ? "पात्रता मूल्यांकन पूर्ण हुआ!" : "Profile Assessment Complete!"}
            </h2>
            <p className="text-slate-300 text-sm sm:text-base max-w-lg mx-auto leading-relaxed">
              {showHindi
                ? "हमने आपके सत्यापित उत्तरों के आधार पर सभी सक्रिय सरकारी योजनाओं का मूल्यांकन कर लिया है। आपका व्यक्तिगत डैशबोर्ड तैयार है।"
                : "All active government schemes have been evaluated against your verified answers using deterministic statutory policy rules."}
            </p>
          </div>

          <div className="inline-block p-6 rounded-3xl bg-white/[0.04] border border-white/10 backdrop-blur-md shadow-inner">
            <span className="text-5xl sm:text-6xl font-black text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 drop-shadow-md">
              {eligibleCount}
            </span>
            <p className="text-xs sm:text-sm font-bold text-slate-300 uppercase tracking-wider mt-2">
              {showHindi ? "पात्र योजना लाभ मिले" : "Qualifying Schemes Found"}
            </p>
          </div>

          <div className="pt-4 flex justify-center">
            <Button
              onClick={handleViewResults}
              className="h-14 px-10 bg-gradient-to-r from-emerald-500 via-teal-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-black font-extrabold text-lg rounded-2xl shadow-[0_0_30px_rgba(16,185,129,0.4)] transition-all transform hover:scale-[1.02] active:scale-[0.98]"
            >
              {showHindi ? "मेरी योजनाएं और लाभ देखें" : "View My Schemes & Verified Benefits"}
              <ArrowRight className="h-5 w-5 ml-2.5 stroke-[3]" />
            </Button>
          </div>
        </div>
      )}

      {/* Real-time Eligible Schemes Preview Modal */}
      {previewOpen && previewData && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-[#0B0F19] border border-white/15 rounded-3xl max-w-lg w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="p-5 border-b border-white/10 flex items-center justify-between bg-white/[0.02]">
              <div>
                <h3 className="font-extrabold text-white text-lg flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-emerald-400" />
                  {showHindi ? "वर्तमान में पात्र योजनाएँ" : "Qualifying Schemes Preview"}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {previewData.total_eligible} {showHindi ? "योजनाएँ अब तक मेल खाती हैं" : "schemes currently matching your criteria"}
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setPreviewOpen(false)}
                className="rounded-full h-8 w-8 p-0 text-slate-400 hover:text-white hover:bg-white/10"
              >
                ✕
              </Button>
            </div>

            <div className="p-5 overflow-y-auto space-y-3 divide-y divide-white/5 flex-grow">
              {previewData.items?.length > 0 ? (
                previewData.items.map((item: any, idx: number) => (
                  <div key={idx} className="pt-3 first:pt-0 space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <h4 className="font-bold text-white text-sm leading-snug">
                        {item.scheme_name}
                      </h4>
                      <Badge variant="outline" className="text-[10px] bg-emerald-500/10 text-emerald-300 border-emerald-500/30 whitespace-nowrap">
                        {item.status || "ELIGIBLE"}
                      </Badge>
                    </div>
                    {item.benefit_summary && (
                      <p className="text-xs text-slate-400 line-clamp-2">
                        {item.benefit_summary}
                      </p>
                    )}
                  </div>
                ))
              ) : (
                <div className="text-center py-8 text-slate-400 text-sm">
                  {showHindi ? "उत्तर देना जारी रखें ताकि योजनाएँ मेल खा सकें।" : "Continue answering questions to unlock matching schemes."}
                </div>
              )}
            </div>

            <div className="p-4 border-t border-white/10 bg-white/[0.02] flex justify-end">
              <Button
                onClick={() => setPreviewOpen(false)}
                className="bg-white/10 hover:bg-white/20 text-white rounded-xl text-xs font-bold px-5"
              >
                {showHindi ? "वापस प्रश्न पर जाएँ" : "Back to Questions"}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
