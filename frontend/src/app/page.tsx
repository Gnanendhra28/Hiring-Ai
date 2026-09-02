"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import {
  Sparkles,
  CheckCircle2,
  ArrowRight,
  ChevronRight,
  ShieldCheck,
  Activity,
  BrainCircuit,
  X,
  Menu,
  Lock,
  BarChart3,
  Users,
  Zap,
  ExternalLink,
  Terminal,
  Eye,
  Sliders,
  Play,
  Layers,
  FileCheck,
  Database,
  Cpu,
  RefreshCw,
  Search,
  Check,
  Award
} from "lucide-react";

interface CandidateSim {
  id: string;
  name: string;
  initials: string;
  role: string;
  company: string;
  location: string;
  exp: number;
  reqSkillScore: number;
  prefSkillScore: number;
  semanticScore: number;
  color: string;
  tags: string[];
  rationale: string;
  evidence: string;
  commitHash: string;
  commitMsg: string;
}

const CANDIDATES: CandidateSim[] = [
  {
    id: "elena",
    name: "Elena Vance",
    initials: "EV",
    role: "Principal Distributed Systems Architect",
    company: "Ex-Stripe / AWS",
    location: "San Francisco, CA",
    exp: 12,
    reqSkillScore: 98,
    prefSkillScore: 94,
    semanticScore: 95,
    color: "from-sky-500 to-indigo-600",
    tags: ["Raft Consensus", "1.2M QPS", "Go/Rust", "Zero-Alloc Memory"],
    rationale: "Authored multi-region database failover spec at Stripe. GitHub commits demonstrate verified Raft consensus log compaction with 100% test coverage.",
    evidence: "github.com/stripe/raft-engine/commit/8f3a9d2 • Verified 100% test coverage",
    commitHash: "8f3a9d2",
    commitMsg: "impl RaftLogCompaction for HighThroughputStorage"
  },
  {
    id: "marcus",
    name: "Marcus Brody",
    initials: "MB",
    role: "Staff Backend Infrastructure Engineer",
    company: "Ex-Datadog",
    location: "New York, NY",
    exp: 9,
    reqSkillScore: 94,
    prefSkillScore: 91,
    semanticScore: 92,
    color: "from-emerald-500 to-teal-700",
    tags: ["Time-Series DB", "C++20", "eBPF Tracing", "400M Events/s"],
    rationale: "Built eBPF kernel tracing pipeline indexing 400M events/sec. Direct repository benchmarks confirm zero-allocation memory pool implementation.",
    evidence: "datadog-open/ebpf-tracer/pull/142 • Benchmark: 400M events/sec",
    commitHash: "e402b11",
    commitMsg: "feat: eBPF zero-copy ringbuffer aggregator"
  },
  {
    id: "sarah",
    name: "Sarah Lin",
    initials: "SL",
    role: "Director of Engineering (Platform)",
    company: "Ex-Airbnb",
    location: "Seattle, WA",
    exp: 14,
    reqSkillScore: 96,
    prefSkillScore: 95,
    semanticScore: 91,
    color: "from-purple-500 to-indigo-800",
    tags: ["Org Scale (40->180)", "Kubernetes", "Cost Optimization (-34%)"],
    rationale: "Led 45-person infrastructure organization. Managed $18M cloud budget migration saving 34% annual compute costs with zero downtime.",
    evidence: "Verified Case Study: Airbnb Compute Efficiency Migration (2024)",
    commitHash: "c18a994",
    commitMsg: "infra: multi-cluster k8s autoscaling controller"
  },
  {
    id: "devon",
    name: "Devon Reed",
    initials: "DR",
    role: "Senior AI Infrastructure Engineer",
    company: "Ex-Anthropic Contributor",
    location: "Austin, TX",
    exp: 8,
    reqSkillScore: 92,
    prefSkillScore: 90,
    semanticScore: 93,
    color: "from-amber-500 to-orange-700",
    tags: ["vLLM Tuning", "CUDA Kernels", "PyTorch C++", "PagedAttention"],
    rationale: "Optimized LLM KV-cache memory allocation reducing inference latency by 42%. Verified open-source PR merged into vLLM core repository.",
    evidence: "vllm-project/vllm/pull/3819 • KV-Cache PagedAttention Optimization",
    commitHash: "7b41e89",
    commitMsg: "cuda: custom flash-decoding kernel for 128k context"
  }
];

export default function Home() {
  // --- Interactive State ---
  const [selectedCandidate, setSelectedCandidate] = useState<CandidateSim>(CANDIDATES[0]);
  const [activeTab, setActiveTab] = useState<"scoring" | "evidence" | "code" | "audit">("scoring");

  // --- Weight Sliders ---
  const [wReq, setWReq] = useState(35);
  const [wPref, setWPref] = useState(25);
  const [wExp, setWExp] = useState(20);
  const [wSem, setWSem] = useState(20);

  // --- Dynamic Match Score Calculation ---
  const expScore = Math.min(100, (selectedCandidate.exp / 10) * 100);
  const totalWeight = wReq + wPref + wExp + wSem;
  const calculatedScore = totalWeight > 0
    ? Math.round(
        (selectedCandidate.reqSkillScore * wReq +
          selectedCandidate.prefSkillScore * wPref +
          expScore * wExp +
          selectedCandidate.semanticScore * wSem) /
          totalWeight
      )
    : 0;

  // --- Animated Score Counter Effect ---
  const [displayScore, setDisplayScore] = useState(calculatedScore);
  useEffect(() => {
    let start = displayScore;
    const end = calculatedScore;
    if (start === end) return;
    const duration = 400;
    const startTime = performance.now();

    const updateScore = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      const current = Math.round(start + (end - start) * progress);
      setDisplayScore(current);
      if (progress < 1) {
        requestAnimationFrame(updateScore);
      }
    };
    requestAnimationFrame(updateScore);
  }, [calculatedScore]);

  // --- Mouse Cursor Parallax & Dynamic Ambient Light ---
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [cursorScreen, setCursorScreen] = useState({ x: 500, y: 300 });
  const heroRef = useRef<HTMLDivElement>(null);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    setCursorScreen({ x: e.clientX, y: e.clientY });
    if (!heroRef.current) return;
    const rect = heroRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width - 0.5;
    const y = (e.clientY - rect.top) / rect.height - 0.5;
    setMousePos({ x, y });
  };

  // --- Interactive Constellation Selected Node ---
  const [activeNode, setActiveNode] = useState<string>("req_root");

  // --- Pipeline Animation Stage ---
  const [pipelineStage, setPipelineStage] = useState<number>(2);

  // --- Shortlist Filter & Modal Inspector ---
  const [searchQuery, setSearchQuery] = useState("");
  const [inspectedCandidate, setInspectedCandidate] = useState<CandidateSim | null>(null);

  // --- Mobile Menu ---
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  return (
    <div
      onMouseMove={handleMouseMove}
      className="min-h-screen bg-[#030712] text-slate-100 selection:bg-sky-500 selection:text-white relative overflow-hidden font-sans"
    >
      {/* Dynamic Cursor Light Beam */}
      <div
        className="pointer-events-none fixed -translate-x-1/2 -translate-y-1/2 rounded-full blur-[100px] opacity-40 transition-opacity duration-300 z-0"
        style={{
          left: `${cursorScreen.x}px`,
          top: `${cursorScreen.y}px`,
          width: "550px",
          height: "550px",
          background: "radial-gradient(circle, rgba(56, 189, 248, 0.25) 0%, rgba(99, 102, 241, 0.15) 50%, transparent 70%)"
        }}
      />

      {/* Background Animated Beams & Grid */}
      <div className="absolute inset-0 bg-hero-glow pointer-events-none z-0" />
      <div className="absolute inset-0 bg-grid-pattern opacity-25 pointer-events-none z-0" />

      {/* Floating Ambient Glowing Orbs */}
      <div className="absolute top-20 left-10 w-96 h-96 bg-sky-500/10 rounded-full blur-3xl pointer-events-none animate-pulse-glow" />
      <div className="absolute top-96 right-10 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-3xl pointer-events-none animate-pulse-glow" style={{ animationDelay: "2.5s" }} />

      {/* ---------------------------------------------------------------- NAVIGATION BAR ---------------------------------------------------------------- */}
      <header className="sticky top-0 z-50 glass-panel border-b border-slate-800/80 backdrop-blur-2xl transition-all duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group focus-visible:outline-none">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-sky-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-sky-500/25 group-hover:scale-105 transition-transform">
              <Sparkles className="w-5 h-5 text-white animate-pulse" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-black tracking-tight text-white flex items-center gap-1.5">
                AuraHire<span className="text-gradient-cyan">AI</span>
                <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/25 font-bold">
                  Enterprise
                </span>
              </span>
              <span className="text-[10px] text-slate-400 font-mono tracking-wider">DETERMINISTIC EVIDENCE ENGINE</span>
            </div>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden lg:flex items-center space-x-8 text-sm font-medium text-slate-300">
            <a href="#simulator" className="hover:text-sky-400 transition-colors">Engine Simulator</a>
            <a href="#pipeline" className="hover:text-sky-400 transition-colors">Visual Pipeline</a>
            <a href="#constellation" className="hover:text-sky-400 transition-colors">Skill Constellation</a>
            <a href="#shortlist" className="hover:text-sky-400 transition-colors">Live Shortlist</a>
            <a href="#governance" className="hover:text-sky-400 transition-colors">Zero-Mutation AI</a>
          </nav>

          {/* Action Portals */}
          <div className="flex items-center space-x-3">
            <Link
              href="/login"
              className="px-4 py-2 text-xs md:text-sm font-semibold rounded-lg glass-panel hover:bg-slate-800 text-slate-200 border border-slate-700 transition-all"
            >
              Sign In (All Roles)
            </Link>

            <Link
              href="/employee/login"
              className="px-4 py-2 text-xs md:text-sm font-bold rounded-lg btn-shimmer text-white shadow-lg shadow-sky-500/25 flex items-center gap-1.5"
            >
              <span>For Recruiters</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="lg:hidden p-2 rounded-lg border border-slate-800 text-slate-300 hover:bg-slate-800/60"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Navigation Menu */}
        {mobileMenuOpen && (
          <div className="lg:hidden px-4 py-6 bg-slate-950/95 border-b border-slate-800 backdrop-blur-2xl space-y-4">
            <nav className="flex flex-col space-y-3 font-medium text-sm">
              <a href="#simulator" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-sky-400">Engine Simulator</a>
              <a href="#pipeline" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-sky-400">Visual Pipeline</a>
              <a href="#constellation" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-sky-400">Skill Constellation</a>
              <a href="#shortlist" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-sky-400">Live Shortlist</a>
              <a href="#governance" onClick={() => setMobileMenuOpen(false)} className="text-slate-300 hover:text-sky-400">Zero-Mutation AI</a>
            </nav>
            <div className="pt-4 border-t border-slate-800 flex flex-col gap-2">
              <Link href="/login" onClick={() => setMobileMenuOpen(false)} className="w-full py-2.5 text-center text-xs font-semibold rounded-lg border border-slate-700 text-slate-200">
                Universal Sign In
              </Link>
              <Link href="/candidate/login" onClick={() => setMobileMenuOpen(false)} className="w-full py-2.5 text-center text-xs font-semibold rounded-lg border border-sky-500/40 text-sky-300">
                Candidate Portal (Login / Sign Up)
              </Link>
              <Link href="/employee/login" onClick={() => setMobileMenuOpen(false)} className="w-full py-2.5 text-center text-xs font-bold rounded-lg bg-sky-500 text-white">
                Recruiter Portal (Login / Sign Up)
              </Link>
            </div>
          </div>
        )}
      </header>

      {/* ---------------------------------------------------------------- HERO SECTION ---------------------------------------------------------------- */}
      <section
        ref={heroRef}
        className="relative z-10 pt-12 pb-20 md:pt-20 md:pb-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto"
      >
        <div className="text-center max-w-4xl mx-auto space-y-6">
          {/* Eyebrow Signal Pill */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-panel border border-sky-500/30 text-sky-300 text-xs font-mono font-semibold uppercase tracking-wider animate-pulse-slow">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            <span>NON-HALLUCINATED EVIDENCE & DETERMINISTIC RANKING</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-7xl font-black tracking-tight text-white leading-tight">
            Hire with AI.<br />
            <span className="text-gradient-cyan">Decide with verifiable evidence.</span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-slate-300 max-w-3xl mx-auto leading-relaxed">
            Explainable 8-dimensional candidate matching, automated repository code verification, and real-time recruitment calibration built on transparent, zero-bias AI governance.
          </p>

          {/* Quick Portal Jump Buttons */}
          <div className="flex flex-wrap items-center justify-center gap-4 pt-4">
            <Link
              href="/employee/login"
              className="px-8 py-4 text-base font-bold rounded-xl btn-shimmer text-white shadow-xl shadow-sky-500/25 flex items-center gap-2 group"
            >
              <span>For Recruiters (Login / Sign Up)</span>
              <ArrowRight className="w-5 h-5 transition-transform group-hover:translate-x-1" />
            </Link>

            <Link
              href="/candidate/login"
              className="px-8 py-4 text-base font-semibold rounded-xl glass-panel glass-panel-hover text-slate-200 border border-slate-700/80 flex items-center gap-2"
            >
              <Users className="w-5 h-5 text-sky-400" />
              <span>For Candidates (Login / Sign Up)</span>
            </Link>

            <Link
              href="/admin/login"
              className="px-6 py-4 text-sm font-mono text-slate-400 hover:text-white glass-panel rounded-xl border border-slate-800 transition-colors"
            >
              Platform Admin
            </Link>
          </div>
        </div>

        {/* ---------------------------------------------------------------- INTERACTIVE 3D PERSPECTIVE ENGINE SIMULATOR ---------------------------------------------------------------- */}
        <div id="simulator" className="mt-16 max-w-6xl mx-auto perspective-1000">
          <div
            className="glow-card rounded-2xl p-6 md:p-8 transition-transform duration-200 ease-out"
            style={{
              transform: `perspective(1000px) rotateX(${mousePos.y * 4}deg) rotateY(${-mousePos.x * 4}deg) translateY(${mousePos.y * 6}px)`
            }}
          >
            {/* Simulator Console Header */}
            <div className="flex flex-wrap items-center justify-between border-b border-slate-800 pb-5 mb-6 gap-4">
              <div className="flex items-center space-x-3">
                <div className="flex space-x-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                </div>
                <span className="text-xs font-mono text-slate-400 border-l border-slate-800 pl-3">
                  AuraHire Matching Simulator v4.2 • PostgreSQL pgvector HNSW
                </span>
              </div>

              {/* Candidate Quick Switcher */}
              <div className="flex items-center gap-1.5 p-1 rounded-xl bg-slate-900 border border-slate-800">
                {CANDIDATES.map((cand) => (
                  <button
                    key={cand.id}
                    onClick={() => setSelectedCandidate(cand)}
                    className={`px-3 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center gap-1.5 ${
                      selectedCandidate.id === cand.id
                        ? "bg-sky-500 text-white shadow-md shadow-sky-500/30"
                        : "text-slate-400 hover:text-white"
                    }`}
                  >
                    <span>{cand.name.split(" ")[0]}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Candidate Header & Real-Time Animated Score Gauge */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center pb-6 border-b border-slate-800">
              {/* Candidate Bio (7 cols) */}
              <div className="lg:col-span-7 flex items-start gap-4">
                <div className={`w-16 h-16 rounded-2xl bg-gradient-to-tr ${selectedCandidate.color} flex items-center justify-center text-white text-2xl font-black shadow-xl flex-shrink-0`}>
                  {selectedCandidate.initials}
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-white">{selectedCandidate.name}</h3>
                    <span className="px-2 py-0.5 text-[10px] font-mono font-bold uppercase rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      VERIFIED PROOF
                    </span>
                  </div>
                  <p className="text-xs text-slate-300 font-medium">{selectedCandidate.role} • {selectedCandidate.company}</p>
                  <p className="text-[11px] font-mono text-slate-400">{selectedCandidate.location} • {selectedCandidate.exp} Yrs Experience</p>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {selectedCandidate.tags.map((t, idx) => (
                      <span key={idx} className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-800/80 text-slate-300 border border-slate-700">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Real-time Dynamic Score Display (5 cols) */}
              <div className="lg:col-span-5 flex items-center justify-end gap-6 bg-slate-900/60 p-4 rounded-xl border border-slate-800">
                <div className="text-right">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-slate-400 block font-bold">
                    DETERMINISTIC MATCH SCORE
                  </span>
                  <div className="text-4xl font-black text-gradient-cyan font-mono flex items-baseline justify-end gap-1">
                    <span>{displayScore}</span>
                    <span className="text-xs text-slate-500 font-normal">/ 100</span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 font-bold">
                    P95 Latency &lt; 38ms • 0% Hallucination
                  </span>
                </div>

                <div className="relative w-16 h-16 flex-shrink-0">
                  <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
                    <path
                      className="text-slate-800"
                      strokeWidth="3.5"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                    <path
                      className="text-sky-400 transition-all duration-700"
                      strokeDasharray={`${displayScore}, 100`}
                      strokeWidth="3.5"
                      strokeLinecap="round"
                      stroke="currentColor"
                      fill="none"
                      d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center text-xs font-mono font-bold text-sky-300">
                    {displayScore}%
                  </div>
                </div>
              </div>
            </div>

            {/* Interactive Simulator Tabs */}
            <div className="flex flex-wrap items-center gap-2 my-6 p-1 rounded-xl bg-slate-900/80 border border-slate-800 text-xs font-semibold">
              <button
                onClick={() => setActiveTab("scoring")}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-2 ${
                  activeTab === "scoring" ? "bg-sky-500 text-white shadow-md shadow-sky-500/20 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                <Sliders className="w-4 h-4" />
                <span>Dynamic Weight Breakdown</span>
              </button>

              <button
                onClick={() => setActiveTab("evidence")}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-2 ${
                  activeTab === "evidence" ? "bg-sky-500 text-white shadow-md shadow-sky-500/20 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                <FileCheck className="w-4 h-4" />
                <span>Verified Evidence Citations</span>
              </button>

              <button
                onClick={() => setActiveTab("code")}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-2 ${
                  activeTab === "code" ? "bg-sky-500 text-white shadow-md shadow-sky-500/20 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                <Terminal className="w-4 h-4" />
                <span>Repository Commit Proof</span>
              </button>

              <button
                onClick={() => setActiveTab("audit")}
                className={`flex-1 py-2 rounded-lg transition-all flex items-center justify-center gap-2 ${
                  activeTab === "audit" ? "bg-sky-500 text-white shadow-md shadow-sky-500/20 font-bold" : "text-slate-400 hover:text-white"
                }`}
              >
                <ShieldCheck className="w-4 h-4" />
                <span>EEOC Governance Log</span>
              </button>
            </div>

            {/* Tab 1: Weight Sliders & Recalibration */}
            {activeTab === "scoring" && (
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center animate-in fade-in duration-300">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-300 uppercase font-mono">
                      Interactive Formula Weighting (Sum: {totalWeight}%)
                    </span>
                    <button
                      onClick={() => { setWReq(35); setWPref(25); setWExp(20); setWSem(20); }}
                      className="text-[11px] font-mono text-sky-400 hover:underline flex items-center gap-1"
                    >
                      <RefreshCw className="w-3 h-3" /> Reset Default
                    </button>
                  </div>

                  {/* Slider 1 */}
                  <div className="space-y-1 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-sky-300">1. Required Skills Alignment:</span>
                      <span className="font-bold text-white">{wReq}% weight ({selectedCandidate.reqSkillScore}%)</span>
                    </div>
                    <input
                      type="range" min="0" max="60" value={wReq}
                      onChange={(e) => setWReq(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-400"
                    />
                  </div>

                  {/* Slider 2 */}
                  <div className="space-y-1 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-emerald-300">2. Preferred Competency Breadth:</span>
                      <span className="font-bold text-white">{wPref}% weight ({selectedCandidate.prefSkillScore}%)</span>
                    </div>
                    <input
                      type="range" min="0" max="60" value={wPref}
                      onChange={(e) => setWPref(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-emerald-400"
                    />
                  </div>

                  {/* Slider 3 */}
                  <div className="space-y-1 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-amber-300">3. Seniority & Experience Threshold:</span>
                      <span className="font-bold text-white">{wExp}% weight ({selectedCandidate.exp} Yrs)</span>
                    </div>
                    <input
                      type="range" min="0" max="60" value={wExp}
                      onChange={(e) => setWExp(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-amber-400"
                    />
                  </div>

                  {/* Slider 4 */}
                  <div className="space-y-1 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-purple-300">4. pgvector HNSW Semantic Match:</span>
                      <span className="font-bold text-white">{wSem}% weight ({selectedCandidate.semanticScore}%)</span>
                    </div>
                    <input
                      type="range" min="0" max="60" value={wSem}
                      onChange={(e) => setWSem(Number(e.target.value))}
                      className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-purple-400"
                    />
                  </div>
                </div>

                {/* Animated Formula Preview Box */}
                <div className="space-y-4 bg-slate-900/80 p-6 rounded-2xl border border-slate-800 font-mono text-xs">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-800 text-sky-400 font-bold">
                    <span>Deterministic Mathematical Expression</span>
                    <Zap className="w-4 h-4" />
                  </div>
                  <div className="p-3.5 rounded-xl bg-black/50 border border-slate-800 text-slate-300 leading-relaxed overflow-x-auto text-[11px]">
                    <span className="text-slate-500"># Real-time dynamic weighted score equation:</span>
                    <p className="text-sky-300 mt-1 font-bold">
                      score = ({selectedCandidate.reqSkillScore} × {wReq}% + {selectedCandidate.prefSkillScore} × {wPref}% + {expScore.toFixed(0)} × {wExp}% + {selectedCandidate.semanticScore} × {wSem}%) / {totalWeight}%
                    </p>
                    <p className="text-emerald-400 mt-2 font-bold text-sm">
                      = {calculatedScore} / 100
                    </p>
                  </div>
                  <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs">
                    ✓ <strong>Mathematical Guarantee:</strong> Zero hallucinated LLM rating tokens. 100% reproducible score across all candidates.
                  </div>
                </div>
              </div>
            )}

            {/* Tab 2: Evidence Citations */}
            {activeTab === "evidence" && (
              <div className="space-y-4 animate-in fade-in duration-300 font-mono text-xs">
                <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
                  <span className="text-sky-400 font-bold uppercase tracking-wider block">
                    AI RATIONALE FOR CANDIDATE RELEVANCE:
                  </span>
                  <p className="text-slate-200 text-sm font-sans leading-relaxed">{selectedCandidate.rationale}</p>
                </div>
                <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 space-y-1">
                  <span className="font-bold text-emerald-400 block">Verified Production Proof Citation:</span>
                  <p className="text-white">{selectedCandidate.evidence}</p>
                </div>
              </div>
            )}

            {/* Tab 3: Code Commit Proof */}
            {activeTab === "code" && (
              <div className="space-y-4 animate-in fade-in duration-300 font-mono text-xs">
                <div className="p-4 rounded-xl bg-black/60 border border-slate-800 text-slate-300 space-y-2">
                  <div className="flex items-center justify-between text-slate-500 pb-2 border-b border-slate-800">
                    <span>Repository Commit Citation: #{selectedCandidate.commitHash}</span>
                    <span className="text-emerald-400 uppercase font-bold">100% Test Coverage</span>
                  </div>
                  <p className="text-white text-sm font-bold text-sky-400">
                    commit {selectedCandidate.commitHash}: {selectedCandidate.commitMsg}
                  </p>
                  <p className="text-slate-400 text-[11px]">
                    Verified zero-allocation memory pool implementation verified against 4,200 automated benchmark runs.
                  </p>
                </div>
              </div>
            )}

            {/* Tab 4: EEOC Audit */}
            {activeTab === "audit" && (
              <div className="space-y-4 animate-in fade-in duration-300 font-mono text-xs">
                <div className="p-4 rounded-xl bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-500/30 space-y-2">
                  <div className="flex items-center gap-2 text-emerald-400 font-bold">
                    <ShieldCheck className="w-5 h-5" />
                    <span>EEOC & AI Governance Audit Record Passed</span>
                  </div>
                  <p className="text-slate-300 leading-relaxed font-sans text-xs">
                    Audit Token <span className="underline font-mono">sec_audit_9941a8b2</span>. Protected attributes (race, age, gender) are masked at the database ingestion layer. Recruiter maintains 100% human hiring authority.
                  </p>
                </div>
              </div>
            )}

            {/* Simulator Footer CTA */}
            <div className="mt-8 pt-6 border-t border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-slate-400">
              <div className="flex items-center gap-2 text-emerald-400">
                <Activity className="w-4 h-4 animate-pulse" />
                <span>Live Calibration Active</span>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setInspectedCandidate(selectedCandidate)}
                  className="px-4 py-2 rounded-lg border border-sky-500/30 text-sky-300 hover:bg-sky-500/10 transition-all font-bold"
                >
                  Inspect Full Candidate Profile
                </button>
                <Link
                  href="/recruiter/dashboard"
                  className="px-4 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white font-bold transition-all shadow-md shadow-sky-500/20"
                >
                  Open Recruiter Console →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- SECTION 2: ANIMATED VISUAL PIPELINE ---------------------------------------------------------------- */}
      <section id="pipeline" className="py-24 border-y border-slate-800 bg-slate-950/70 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
            <span className="text-xs font-mono uppercase tracking-widest text-sky-400 font-bold">
              END-TO-END RECRUITMENT DATA STREAM
            </span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              From Raw Applications to <span className="text-gradient-cyan">Verified Shortlist</span>
            </h2>
            <p className="text-sm md:text-base text-slate-400">
              Click any pipeline phase to inspect how candidates flow through our multi-tenant verification engine in real time.
            </p>
          </div>

          {/* Pipeline Interactive Stages */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 relative">
            {[
              {
                step: 1,
                title: "1. Resume Parsing",
                badge: "Section Extraction",
                desc: "Parses original candidate PDF resumes without loss, extracting work history, projects, and skills.",
                icon: FileCheck,
                color: "text-sky-400"
              },
              {
                step: 2,
                title: "2. 8-D Intelligence",
                badge: "Skill Taxonomy",
                desc: "Extracts structured competency taxonomies and flags candidate buzzwords with zero bias markers.",
                icon: BrainCircuit,
                color: "text-emerald-400"
              },
              {
                step: 3,
                title: "3. HNSW Vector Match",
                badge: "pgvector Cosine",
                desc: "Computes sub-millisecond semantic distance against job requisitions using PostgreSQL vector indexing.",
                icon: Database,
                color: "text-purple-400"
              },
              {
                step: 4,
                title: "4. Recruiter Decision",
                badge: "Zero-Mutation",
                desc: "Recruiter inspects verified evidence and advances candidates with full EEOC audit tracking.",
                icon: Award,
                color: "text-amber-400"
              }
            ].map((p) => (
              <div
                key={p.step}
                onClick={() => setPipelineStage(p.step)}
                className={`p-6 rounded-2xl border cursor-pointer transition-all duration-300 relative overflow-hidden ${
                  pipelineStage === p.step
                    ? "bg-slate-900 border-sky-500 shadow-2xl shadow-sky-950/60 scale-[1.02]"
                    : "bg-slate-900/40 border-slate-800 opacity-70 hover:opacity-100 hover:border-slate-700"
                }`}
              >
                {pipelineStage === p.step && (
                  <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-sky-400 via-emerald-400 to-indigo-500" />
                )}
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center mb-4">
                  <p.icon className={`w-5 h-5 ${p.color}`} />
                </div>
                <span className="text-[10px] font-mono uppercase font-bold text-sky-400 block mb-1">
                  {p.badge}
                </span>
                <h3 className="text-base font-bold text-white mb-2">{p.title}</h3>
                <p className="text-xs text-slate-400 leading-relaxed font-sans">{p.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- SECTION 3: SKILL CONSTELLATION GRAPH ---------------------------------------------------------------- */}
      <section id="constellation" className="py-24 relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16 space-y-3">
          <span className="text-xs font-mono uppercase tracking-widest text-sky-400 font-bold">
            INTERACTIVE GRAPH TOPOLOGY
          </span>
          <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
            Animated <span className="text-gradient-cyan">Skill Constellation</span>
          </h2>
          <p className="text-sm md:text-base text-slate-400">
            Hover or click nodes to inspect multi-dimensional graph relationships between requisition skills and candidate evidence.
          </p>
        </div>

        <div className="glow-card rounded-3xl p-8 md:p-12 relative overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            {/* SVG Interactive Canvas (8 cols) */}
            <div className="lg:col-span-8 relative min-h-[380px] flex items-center justify-center">
              <svg className="absolute inset-0 w-full h-full pointer-events-none opacity-30" viewBox="0 0 600 400">
                <circle cx="300" cy="200" r="150" fill="none" stroke="#38bdf8" strokeWidth="1" strokeDasharray="6 6" className="animate-orbit-spin" />
                <circle cx="300" cy="200" r="100" fill="none" stroke="#6366f1" strokeWidth="1" />
                <line x1="300" y1="200" x2="140" y2="100" stroke="#38bdf8" strokeWidth="1.5" strokeDasharray="4 4" className="animate-dash-flow" />
                <line x1="300" y1="200" x2="460" y2="120" stroke="#10b981" strokeWidth="1.5" strokeDasharray="4 4" className="animate-dash-flow" />
                <line x1="300" y1="200" x2="440" y2="300" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="4 4" className="animate-dash-flow" />
                <line x1="300" y1="200" x2="160" y2="280" stroke="#a855f7" strokeWidth="1.5" strokeDasharray="4 4" className="animate-dash-flow" />
              </svg>

              {/* Central Requisition Node */}
              <div
                onClick={() => setActiveNode("req_root")}
                className={`absolute z-20 cursor-pointer p-4 rounded-2xl border transition-all text-center ${
                  activeNode === "req_root"
                    ? "bg-sky-500 text-white border-sky-300 scale-110 shadow-2xl shadow-sky-500/40"
                    : "bg-slate-900 border-sky-500/40 text-sky-300 hover:scale-105"
                }`}
                style={{ top: "40%", left: "40%" }}
              >
                <BrainCircuit className="w-6 h-6 mx-auto mb-1 animate-pulse" />
                <span className="text-xs font-bold font-mono block">Principal Architect</span>
                <span className="text-[9px] opacity-80 font-mono">Job Req #104</span>
              </div>

              {/* Surrounding Nodes */}
              {[
                { id: "node_elena", name: "Elena Vance (96%)", sub: "Raft Spec Verified", top: "12%", left: "15%", color: "border-emerald-500/50 bg-emerald-500/10 text-emerald-300" },
                { id: "node_raft", name: "Raft Consensus", sub: "Skill Taxonomy", top: "15%", left: "68%", color: "border-sky-500/50 bg-sky-500/10 text-sky-300" },
                { id: "node_marcus", name: "Marcus Brody (92%)", sub: "eBPF Benchmark", top: "68%", left: "68%", color: "border-amber-500/50 bg-amber-500/10 text-amber-300" },
                { id: "node_failover", name: "1.2M QPS Failover", sub: "Production Proof", top: "65%", left: "18%", color: "border-purple-500/50 bg-purple-500/10 text-purple-300" }
              ].map((node) => (
                <div
                  key={node.id}
                  onClick={() => setActiveNode(node.id)}
                  className={`absolute z-20 cursor-pointer p-3 rounded-xl border transition-all ${node.color} ${
                    activeNode === node.id ? "ring-2 ring-sky-400 scale-110 shadow-xl" : "opacity-80 hover:opacity-100"
                  }`}
                  style={{ top: node.top, left: node.left }}
                >
                  <span className="text-xs font-bold block">{node.name}</span>
                  <span className="text-[9px] font-mono opacity-70 block">{node.sub}</span>
                </div>
              ))}
            </div>

            {/* Node Detail Callout (4 cols) */}
            <div className="lg:col-span-4 space-y-4">
              <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 space-y-3 font-mono text-xs">
                <span className="text-sky-400 font-bold uppercase tracking-wider block">
                  SELECTED GRAPH ARTIFACT
                </span>
                {activeNode === "req_root" && (
                  <div className="space-y-2">
                    <h4 className="text-base font-bold text-white font-sans">Principal Distributed Architect</h4>
                    <p className="text-slate-300 font-sans leading-relaxed">
                      Requisition active with 42 total applicants. 4 top signal candidates isolated via pgvector cosine distance.
                    </p>
                  </div>
                )}
                {activeNode === "node_elena" && (
                  <div className="space-y-2">
                    <h4 className="text-base font-bold text-white font-sans">Elena Vance (96% Match)</h4>
                    <p className="text-slate-300 font-sans leading-relaxed">
                      Match score 96/100 anchored to verified multi-region database failover spec at Stripe.
                    </p>
                  </div>
                )}
                {activeNode === "node_raft" && (
                  <div className="space-y-2">
                    <h4 className="text-base font-bold text-white font-sans">Raft Consensus Taxonomy</h4>
                    <p className="text-slate-300 font-sans leading-relaxed">
                      Core competency required by Requisition #104. 2 candidates exhibit verified production repository commits.
                    </p>
                  </div>
                )}
                {activeNode === "node_marcus" && (
                  <div className="space-y-2">
                    <h4 className="text-base font-bold text-white font-sans">Marcus Brody (92% Match)</h4>
                    <p className="text-slate-300 font-sans leading-relaxed">
                      Match score 92/100 verified against Datadog eBPF kernel tracing benchmark (400M events/sec).
                    </p>
                  </div>
                )}
                {activeNode === "node_failover" && (
                  <div className="space-y-2">
                    <h4 className="text-base font-bold text-white font-sans">1.2M QPS Failover Spec</h4>
                    <p className="text-slate-300 font-sans leading-relaxed">
                      Production engineering artifact extracted directly from candidate resume work history.
                    </p>
                  </div>
                )}
                <Link
                  href="/recruiter/dashboard"
                  className="w-full py-2.5 text-xs font-bold rounded-lg bg-sky-500 hover:bg-sky-400 text-white transition-all shadow block text-center"
                >
                  Explore Requisition Graph →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- SECTION 4: LIVE SHORTLIST CONSOLE ---------------------------------------------------------------- */}
      <section id="shortlist" className="py-24 border-y border-slate-800 bg-slate-950/60 relative z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-sky-400 font-bold">
                RECRUITER SHORTLIST CONSOLE
              </span>
              <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight mt-2">
                Live Candidate Signal Table
              </h2>
            </div>

            {/* Live Search Box */}
            <div className="relative w-full md:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter candidate or skill..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2.5 text-xs rounded-xl bg-slate-900 border border-slate-800 text-white outline-none focus:border-sky-500 font-mono"
              />
            </div>
          </div>

          {/* Table Container */}
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 overflow-hidden shadow-2xl">
            <div className="divide-y divide-slate-800">
              {CANDIDATES.filter((c) =>
                searchQuery === "" ||
                c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                c.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()))
              ).map((cand) => (
                <div
                  key={cand.id}
                  className="p-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-6 hover:bg-slate-800/40 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${cand.color} flex items-center justify-center text-white font-black text-lg shadow-lg`}>
                      {cand.initials}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h4 className="text-base font-bold text-white">{cand.name}</h4>
                        <span className="px-2 py-0.5 text-[10px] font-mono font-bold rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/25">
                          {cand.reqSkillScore}% MATCH
                        </span>
                      </div>
                      <p className="text-xs text-slate-400 mt-0.5">{cand.role} • {cand.company}</p>
                      <div className="flex flex-wrap gap-1.5 mt-2">
                        {cand.tags.map((tag, idx) => (
                          <span key={idx} className="px-2 py-0.5 text-[10px] font-mono rounded bg-slate-800 text-slate-300 border border-slate-700">
                            {tag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3 w-full md:w-auto justify-end">
                    <button
                      onClick={() => setInspectedCandidate(cand)}
                      className="px-4 py-2 text-xs font-bold rounded-lg border border-sky-500/40 text-sky-300 hover:bg-sky-500/10 transition-all flex items-center gap-1.5"
                    >
                      <Eye className="w-3.5 h-3.5" />
                      <span>Inspect Signal</span>
                    </button>
                    <Link
                      href="/employee/login"
                      className="px-4 py-2 text-xs font-bold rounded-lg bg-sky-500 hover:bg-sky-400 text-white transition-all shadow"
                    >
                      For Recruiters →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- CANDIDATE DETAIL MODAL ---------------------------------------------------------------- */}
      {inspectedCandidate && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-300">
          <div className="w-full max-w-2xl rounded-2xl bg-slate-900 border border-slate-800 p-6 sm:p-8 space-y-6 max-h-[90vh] overflow-y-auto shadow-2xl">
            <div className="flex items-start justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center gap-4">
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-tr ${inspectedCandidate.color} flex items-center justify-center text-white text-xl font-bold shadow-lg`}>
                  {inspectedCandidate.initials}
                </div>
                <div>
                  <h3 className="text-xl font-bold text-white">{inspectedCandidate.name}</h3>
                  <p className="text-xs text-slate-400">{inspectedCandidate.role} • {inspectedCandidate.company}</p>
                  <p className="text-[11px] font-mono text-slate-500">{inspectedCandidate.location} • {inspectedCandidate.exp} Yrs Exp</p>
                </div>
              </div>
              <button onClick={() => setInspectedCandidate(null)} className="p-2 rounded-lg border border-slate-800 text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-4 rounded-xl bg-sky-500/10 border border-sky-500/20 space-y-2 font-mono text-xs">
              <span className="text-sky-400 font-bold block">AI MATCH RATIONALE & CITATION:</span>
              <p className="text-slate-200 font-sans leading-relaxed text-xs">{inspectedCandidate.rationale}</p>
            </div>

            <div className="p-4 rounded-xl bg-black/40 border border-slate-800 font-mono text-xs space-y-1">
              <span className="text-slate-500 block mb-1">Verified Evidence Artifact:</span>
              <span className="text-emerald-400">{inspectedCandidate.evidence}</span>
            </div>

            <div className="pt-4 border-t border-slate-800 flex justify-end gap-3 font-mono text-xs">
              <button onClick={() => setInspectedCandidate(null)} className="px-4 py-2 rounded-lg border border-slate-700 hover:bg-slate-800">
                Close
              </button>
              <Link href="/employee/login" className="px-5 py-2 rounded-lg bg-sky-500 hover:bg-sky-400 text-white font-bold shadow">
                Recruiter Login to Schedule →
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* ---------------------------------------------------------------- SECTION 5: ZERO-MUTATION AI GOVERNANCE ---------------------------------------------------------------- */}
      <section id="governance" className="py-24 relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="p-8 md:p-14 rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950/40 to-slate-900 border border-indigo-500/30 relative overflow-hidden">
          <div className="max-w-3xl space-y-4">
            <span className="px-3.5 py-1.5 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-mono font-bold uppercase tracking-widest border border-indigo-500/30">
              CORE GOVERNANCE PRINCIPLE
            </span>
            <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
              &quot;AI ASSISTS. <span className="text-gradient-cyan">RECRUITER DECIDES.&quot;</span>
            </h2>
            <p className="text-slate-300 text-sm md:text-base leading-relaxed">
              Our AI architecture provides explainable insights and evidence recommendations—with <strong>0% state mutation authority</strong>. Recruiters retain total human decision supremacy.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 text-xs font-medium text-slate-300">
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-emerald-400 font-extrabold text-lg">0</span>
                <span>AI Mutation Paths (Blocked by System Architecture)</span>
              </div>
              <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 flex items-center space-x-3">
                <span className="text-sky-400 font-extrabold text-lg">100%</span>
                <span>Human Recruiter Decision Authority</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- FINAL CALL TO ACTION ---------------------------------------------------------------- */}
      <section className="py-20 md:py-28 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto text-center relative z-10">
        <div className="p-12 rounded-3xl glow-card border border-slate-800 relative overflow-hidden space-y-6">
          <h2 className="text-3xl md:text-5xl font-black text-white tracking-tight">
            Ready to transform enterprise hiring?
          </h2>
          <p className="text-slate-300 text-base md:text-lg max-w-2xl mx-auto">
            Experience evidence-backed AI recruitment with complete governance and tenant isolation.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
            <Link
              href="/employee/login"
              className="px-8 py-4 text-base font-bold rounded-xl btn-shimmer text-white shadow-xl shadow-sky-500/25 flex items-center gap-2"
            >
              <span>For Recruiters (Login / Sign Up)</span>
              <ArrowRight className="w-5 h-5" />
            </Link>

            <Link
              href="/candidate/login"
              className="px-8 py-4 text-base font-semibold rounded-xl glass-panel text-slate-200 border border-slate-700 hover:bg-slate-800 flex items-center gap-2"
            >
              <Users className="w-5 h-5 text-sky-400" />
              <span>For Candidates (Login / Sign Up) →</span>
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------------------------------------------------------- FOOTER ---------------------------------------------------------------- */}
      <footer className="border-t border-slate-800 bg-slate-950 py-12 px-4 sm:px-6 lg:px-8 relative z-10 text-xs font-mono text-slate-400">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-lg bg-sky-500 flex items-center justify-center text-white font-bold text-sm">
              AH
            </div>
            <span className="text-sm font-bold text-slate-200 font-sans">AuraHire AI Enterprise SaaS</span>
            <span className="text-xs text-slate-500">v4.2</span>
          </div>

          <div className="flex items-center space-x-6">
            <Link href="/employee/login" className="hover:text-white transition-colors">For Recruiters</Link>
            <Link href="/candidate/login" className="hover:text-white transition-colors">For Candidates</Link>
            <Link href="/admin/login" className="hover:text-white transition-colors">Platform Admin</Link>
          </div>

          <div className="flex items-center space-x-2 text-emerald-400">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>ALL SYSTEMS OPERATIONAL</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
