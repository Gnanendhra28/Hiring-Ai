"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

interface AssessmentItem {
  id: string;
  title: string;
  duration_minutes: number;
  passing_score: number;
}

export default function RecruiterAssessmentsPage() {
  const params = useParams();
  const jobId = params?.id as string;

  const [assessments, setAssessments] = useState<AssessmentItem[]>([
    {
      id: "ass-1",
      title: "Python Backend Systems Architecture Test",
      duration_minutes: 60,
      passing_score: 75,
    },
  ]);

  const [title, setTitle] = useState("");
  const [duration, setDuration] = useState(60);
  const [passingScore, setPassingScore] = useState(70);
  const [showCreateModal, setShowCreateModal] = useState(false);

  const handleCreateAssessment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    const newAss: AssessmentItem = {
      id: `ass-${Date.now()}`,
      title,
      duration_minutes: duration,
      passing_score: passingScore,
    };
    setAssessments([...assessments, newAss]);
    setTitle("");
    setShowCreateModal(false);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div>
            <Link href={`/recruiter/jobs/${jobId}`} className="text-xs text-blue-400 hover:underline">
              &larr; Back to Job Requisition
            </Link>
            <h1 className="text-2xl font-bold text-white mt-1">Job Assessment Management</h1>
            <p className="text-slate-400 text-xs">Configure technical assessments and assign tests to candidates.</p>
          </div>
          <button
            onClick={() => setShowCreateModal(true)}
            className="text-xs bg-blue-600 hover:bg-blue-500 text-white font-semibold px-4 py-2 rounded-lg transition-colors shadow-md shadow-blue-600/20"
          >
            + Create Assessment Template
          </button>
        </div>

        {/* Assessment Templates Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {assessments.map((a) => (
            <div key={a.id} className="bg-slate-900/40 border border-slate-800 rounded-xl p-6 space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/10 text-blue-400 border border-blue-500/20 uppercase tracking-wider">
                    Technical Assessment
                  </span>
                  <h3 className="text-lg font-bold text-white mt-2">{a.title}</h3>
                </div>
              </div>
              <div className="flex items-center gap-4 text-xs text-slate-400">
                <span>⏱️ {a.duration_minutes} Minutes</span>
                <span>🎯 Passing Score: {a.passing_score}%</span>
              </div>
              <div className="pt-2 border-t border-slate-800 flex justify-end">
                <span className="text-xs text-slate-400">Ready for Candidate Assignment</span>
              </div>
            </div>
          ))}
        </div>

        {/* Create Assessment Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4 z-50">
            <form onSubmit={handleCreateAssessment} className="bg-slate-900 border border-slate-800 rounded-xl p-6 max-w-md w-full space-y-4">
              <h3 className="text-lg font-bold text-white">Create Assessment Template</h3>
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Assessment Title</label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Senior Python Architecture Assessment"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Duration (Minutes)</label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Passing Score (%)</label>
                  <input
                    type="number"
                    value={passingScore}
                    onChange={(e) => setPassingScore(Number(e.target.value))}
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="px-4 py-2 bg-slate-800 text-slate-300 text-xs rounded-md"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white text-xs font-semibold rounded-md transition-all"
                >
                  Save Assessment
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
