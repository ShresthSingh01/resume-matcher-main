"use client";

import { Candidate } from "@/hooks/useDashboard";
import { IoClose, IoMailOutline, IoCallOutline, IoDownloadOutline } from "react-icons/io5";

interface CandidateModalProps {
    candidate: Candidate;
    onClose: () => void;
}

export default function CandidateModal({ candidate, onClose }: CandidateModalProps) {
    const c = candidate;

    // Helper to parse JSON fields safely
    const parseJson = (field: any) => {
        if (!field) return [];
        if (Array.isArray(field)) return field;
        try {
            return JSON.parse(field);
        } catch (e) {
            return [];
        }
    };

    const matchedSkills = parseJson(c.matched_skills);
    const missingSkills = parseJson(c.missing_skills);
    const evaluation = c.resume_evaluation_data ? (typeof c.resume_evaluation_data === "string" ? JSON.parse(c.resume_evaluation_data) : c.resume_evaluation_data) : null;
    const feedback = c.feedback_data ? (typeof c.feedback_data === "string" ? JSON.parse(c.feedback_data) : c.feedback_data) : null;
    const transcript = feedback?.transcript || (Array.isArray(feedback) ? feedback : []);

    const downloadReport = () => {
        // Basic text report generation
        let content = `VIREX AI REPORT: ${c.name}\n\n`;
        content += `Match Score: ${c.match_score}%\n`;
        content += `Interview Score: ${c.interview_score ?? 0}/100\n\n`;
        content += `TRANSCRIPT:\n`;
        transcript.forEach((t: any, i: number) => {
            content += `Q${i + 1}: ${t.q}\nAns: ${t.a}\nScore: ${t.score}\nFeedback: ${t.feedback}\n\n`;
        });
        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Report_${c.filename}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-300">
            {/* Overlay */}
            <div className="absolute inset-0 bg-slate-900/80" onClick={onClose}></div>

            <div className="relative h-[90vh] w-full max-w-6xl overflow-hidden rounded-lg bg-[var(--bg-secondary)] border border-[var(--border-color)] shadow-xl flex flex-col z-10">

                {/* Header */}
                <div className="relative flex items-center justify-between border-b border-[var(--border-color)] p-6 bg-[var(--bg-tertiary)]/20">
                    <div>
                        <h2 className="text-2xl font-bold text-[var(--text-main)] tracking-tight">{c.name || c.filename}</h2>
                        <div className="mt-1 flex gap-6 text-xs text-[var(--text-muted)] font-medium">
                            <span className="flex items-center gap-1.5"><IoMailOutline /> {c.email || "N/A"}</span>
                            <span className="flex items-center gap-1.5"><IoCallOutline /> {c.phone || "N/A"}</span>
                        </div>
                    </div>

                    <div className="flex gap-3 items-center">
                        {c.final_score > 75 && <span className="rounded bg-green-500/10 border border-green-500/20 px-2 py-1 text-xs font-semibold text-green-500">Top Pick</span>}
                        {(c.status === "completed" || c.status === "Interviewed") && <span className="rounded bg-blue-500/10 border border-blue-500/20 px-2 py-1 text-xs font-semibold text-blue-500">Interviewed</span>}
                        <button onClick={onClose} className="ml-6 rounded-md p-2 text-[var(--text-muted)] hover:bg-[var(--bg-tertiary)] hover:text-[var(--text-main)] transition-colors">
                            <IoClose size={20} />
                        </button>
                    </div>
                </div>

                {/* Content - Scrollable */}
                <div className="relative grid flex-1 overflow-hidden md:grid-cols-[280px_1fr]">

                    {/* Sidebar (Left) */}
                    <div className="overflow-y-auto border-r border-[var(--border-color)] bg-[var(--bg-primary)] p-6">
                        <h3 className="mb-6 text-xs font-bold uppercase tracking-wider text-[var(--text-muted)]">Analysis Engine</h3>

                        <div className="space-y-4">
                            <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                                <div className="text-xs font-medium text-[var(--text-muted)] mb-1">Resume Match</div>
                                <div className="text-3xl font-bold text-blue-500">{c.match_score.toFixed(0)}%</div>
                            </div>

                            <div className="p-4 rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)]">
                                <div className="text-xs font-medium text-[var(--text-muted)] mb-1">Interview Score</div>
                                <div className="flex items-baseline gap-2">
                                    <span className="text-3xl font-bold text-[var(--text-main)]">{c.interview_score ?? "-"}</span>
                                    <span className="text-xs text-[var(--text-muted)]">/ 100</span>
                                </div>
                            </div>
                        </div>

                        {evaluation && evaluation.decision && (
                            <div className="mt-8 rounded-lg border border-yellow-600/20 bg-yellow-500/5 p-4">
                                <div className="mb-2 text-xs font-bold uppercase text-yellow-500">AI Evaluation</div>
                                <div className="text-sm font-semibold text-yellow-200 mb-4 leading-relaxed">{evaluation.decision}</div>
                                <div className="grid grid-cols-2 gap-y-2 gap-x-2 text-xs text-[var(--text-muted)]">
                                    <div className="flex justify-between"><span>EXP</span> <b className="text-[var(--text-main)]">{evaluation.likert_scores?.experience}/5</b></div>
                                    <div className="flex justify-between"><span>SKILL</span> <b className="text-[var(--text-main)]">{evaluation.likert_scores?.skills}/5</b></div>
                                    <div className="flex justify-between"><span>EDU</span> <b className="text-[var(--text-main)]">{evaluation.likert_scores?.education}/5</b></div>
                                    <div className="flex justify-between"><span>PROJ</span> <b className="text-[var(--text-main)]">{evaluation.likert_scores?.projects}/5</b></div>
                                </div>
                            </div>
                        )}

                        <div className="mt-8">
                            <button onClick={downloadReport} className="btn btn-secondary w-full flex justify-center items-center gap-2 text-xs uppercase font-bold py-3">
                                <IoDownloadOutline size={16} /> Export Data
                            </button>
                        </div>
                    </div>

                    {/* Main Content (Right) */}
                    <div className="overflow-y-auto p-8 pb-32 bg-[var(--bg-secondary)]">
                        <div className="mb-10">
                            <h3 className="mb-4 text-lg font-bold text-[var(--text-main)] flex items-center gap-2">
                                Skills Matrix
                            </h3>

                            <div className="mb-2 text-xs font-bold text-emerald-500 uppercase tracking-wide">Verified Matches</div>
                            <div className="mb-6 flex flex-wrap gap-2">
                                {matchedSkills.length ? matchedSkills.map((s: string, i: number) => (
                                    <span key={i} className="rounded border border-emerald-500/20 bg-emerald-500/10 px-2 py-1 text-xs font-medium text-emerald-400">{s}</span>
                                )) : <span className="text-[var(--text-muted)] text-sm italic">No matches found</span>}
                            </div>

                            <div className="mb-2 text-xs font-bold text-red-500 uppercase tracking-wide">Identified Gaps</div>
                            <div className="flex flex-wrap gap-2">
                                {missingSkills.length ? missingSkills.map((s: string, i: number) => (
                                    <span key={i} className="rounded border border-red-500/20 bg-red-500/10 px-2 py-1 text-xs font-medium text-red-400 opacity-80">{s}</span>
                                )) : <span className="text-[var(--text-muted)] text-sm italic">No gaps identified</span>}
                            </div>
                        </div>

                        <div>
                            <h3 className="mb-6 text-lg font-bold text-[var(--text-main)]">
                                Neural Transcript
                            </h3>
                            <div className="space-y-4">
                                {transcript.length > 0 ? transcript.map((t: any, i: number) => (
                                    <div key={i} className="rounded-lg border border-[var(--border-color)] bg-[var(--bg-primary)] p-5 hover:border-blue-500/30 transition-colors">
                                        <div className="mb-3 flex justify-between items-center border-b border-[var(--border-color)] pb-2">
                                            <span className="text-xs font-bold text-[var(--text-muted)] uppercase">Sequence {i + 1}</span>
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs font-medium text-[var(--text-muted)]">Score</span>
                                                <span className={`text-sm font-bold ${t.score >= 8 ? "text-emerald-500" : t.score >= 5 ? "text-yellow-500" : "text-red-500"}`}>{t.score}/10</span>
                                            </div>
                                        </div>

                                        <div className="mb-3 text-sm font-medium text-[var(--text-main)] italic">"{t.q}"</div>

                                        <div className="bg-[var(--bg-secondary)] p-3 rounded border border-[var(--border-color)] text-sm text-[var(--text-secondary)] leading-relaxed">
                                            {t.a}
                                        </div>

                                        <div className="mt-3 text-xs leading-relaxed flex gap-2">
                                            <span className="font-bold text-blue-500 whitespace-nowrap">AI Feedback:</span>
                                            <span className="text-[var(--text-muted)]">{t.feedback}</span>
                                        </div>
                                    </div>
                                )) : (
                                    <div className="py-12 text-center text-[var(--text-muted)] border border-dashed border-[var(--border-color)] rounded-lg text-xs">
                                        No transcript data available
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
}
