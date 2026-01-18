"use client";

import { useState, useEffect } from "react";
import { IoCloudUploadOutline, IoDocumentTextOutline, IoBriefcaseOutline, IoArrowForwardOutline, IoOptionsOutline, IoCheckmarkCircleOutline } from "react-icons/io5";

interface UploadSectionProps {
    onUpload: (files: FileList, jd: string, template: string) => Promise<string | null>; // Returns Job ID
    loading: boolean; // Initial submit loading
}

export default function UploadSection({ onUpload, loading }: UploadSectionProps) {
    const [files, setFiles] = useState<FileList | null>(null);
    const [jd, setJd] = useState("");
    const [template, setTemplate] = useState("auto");

    // Async Job State
    const [jobId, setJobId] = useState<string | null>(null);
    const [processed, setProcessed] = useState(0);
    const [total, setTotal] = useState(0);
    const [status, setStatus] = useState("idle"); // idle, processing, completed, failed

    // Polling Effect
    useEffect(() => {
        if (!jobId || status === "completed" || status === "failed") return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/jobs/${jobId}`);
                const data = await res.json();

                if (data.status) {
                    setStatus(data.status);
                    setProcessed(data.processed || 0);
                    setTotal(data.total || 0);

                    if (data.status === "completed") {
                        clearInterval(interval);
                        // Trigger refresh? passed as prop or handled by parent?
                        // For now just show completion state
                        window.location.reload(); // Simple refresh to show leaderboard
                    }
                }
            } catch (e) {
                console.error("Polling error", e);
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [jobId, status]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!files || files.length === 0 || !jd) {
            alert("Please provide at least one resume and a Job Description.");
            return;
        }
        const id = await onUpload(files, jd, template);
        if (id) {
            setJobId(id);
            setTotal(files.length);
            setStatus("queued");
        }
    };

    if (jobId) {
        // Progress UI
        const percent = total > 0 ? Math.round((processed / total) * 100) : 0;

        return (
            <div className="mx-auto w-full max-w-2xl animate-in fade-in zoom-in duration-300">
                <div className="glass-card text-center py-12">
                    <div className="mb-6 flex justify-center">
                        {status === "completed" ? (
                            <div className="h-20 w-20 rounded-full bg-emerald-500/20 text-emerald-500 flex items-center justify-center text-4xl animate-bounce">
                                <IoCheckmarkCircleOutline />
                            </div>
                        ) : (
                            <div className="relative h-20 w-20">
                                <div className="absolute inset-0 rounded-full border-4 border-[var(--bg-tertiary)]"></div>
                                <div className="absolute inset-0 rounded-full border-4 border-blue-500 border-t-transparent animate-spin"></div>
                                <div className="absolute inset-0 flex items-center justify-center text-xs font-bold">{percent}%</div>
                            </div>
                        )}
                    </div>

                    <h2 className="text-xl font-bold mb-2">
                        {status === "queued" && "Queued for Processing..."}
                        {status === "processing" && `Analyzing Resumes (${processed}/${total})...`}
                        {status === "completed" && "Analysis Complete!"}
                    </h2>

                    <p className="text-[var(--text-secondary)] mb-8">
                        {status === "completed" ? "Redirecting to rankings..." : "Please wait while our AI agents evaluate each candidate."}
                    </p>

                    {/* Progress Bar */}
                    <div className="mx-auto max-w-md h-2 bg-[var(--bg-tertiary)] rounded-full overflow-hidden">
                        <div
                            className="h-full bg-blue-500 transition-all duration-500 ease-out"
                            style={{ width: `${percent}%` }}
                        ></div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <div className="mx-auto w-full max-w-5xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            <form onSubmit={handleSubmit} className="grid gap-6 md:grid-cols-2">
                {/* Resume Card */}
                <div className="glass-card group relative overflow-hidden p-0">
                    <div className="p-6">
                        <h2 className="mb-6 flex items-center gap-3 text-xl font-bold tracking-tight text-[var(--text-main)]">
                            <span className="p-2 rounded-lg bg-blue-500/10 text-blue-500"><IoDocumentTextOutline /></span> Resume Upload
                        </h2>
                        <input
                            type="file"
                            id="resume-file"
                            multiple
                            accept=".pdf,.txt"
                            className="hidden"
                            onChange={(e) => setFiles(e.target.files)}
                        />
                        <label
                            htmlFor="resume-file"
                            className={`
                        flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed border-[var(--border-color)] bg-[var(--bg-primary)]/50 py-16 transition-all 
                        hover:border-blue-400/50 hover:bg-slate-800
                        ${files ? "border-emerald-500/50 bg-emerald-500/5" : ""}
                    `}
                        >
                            <IoCloudUploadOutline className={`mb-4 text-5xl transition-all ${files ? "text-emerald-500 scale-110" : "text-[var(--text-secondary)] group-hover:text-blue-400"}`} />
                            <span className="font-semibold text-lg text-[var(--text-main)]">
                                {files ? `${files.length} file(s) selected` : "Drop PDF here"}
                            </span>
                            <span className="mt-2 text-xs text-[var(--text-secondary)]">or click to browse</span>
                        </label>
                    </div>
                </div>

                {/* JD Card */}
                <div className="glass-card group relative overflow-hidden p-0">
                    <div className="p-6">
                        <h2 className="mb-6 flex items-center gap-3 text-xl font-bold tracking-tight text-[var(--text-main)]">
                            <span className="p-2 rounded-lg bg-indigo-500/10 text-indigo-500"><IoBriefcaseOutline /></span> Job Description
                        </h2>
                        <textarea
                            value={jd}
                            onChange={(e) => setJd(e.target.value)}
                            placeholder="Paste the full job description here..."
                            className="h-40 w-full rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)]/50 p-4 font-normal text-sm text-[var(--text-main)] focus:border-blue-500 focus:bg-[var(--bg-primary)] focus:outline-none resize-none transition-all placeholder:text-[var(--text-secondary)]"
                        />

                        <div className="mt-6 pt-4 border-t border-[var(--border-color)]">
                            <label className="mb-3 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-[var(--text-secondary)]">
                                <IoOptionsOutline /> Evaluation Template
                            </label>
                            <div className="relative">
                                <select
                                    value={template}
                                    onChange={(e) => setTemplate(e.target.value)}
                                    className="w-full appearance-none rounded-xl border border-[var(--border-color)] bg-[var(--bg-primary)]/50 p-3 pr-10 font-medium text-[var(--text-main)] focus:border-blue-500 focus:outline-none"
                                >
                                    <option value="auto">✨ Auto-Detect (AI)</option>
                                    <option value="intern">🎓 Intern / Fresher</option>
                                    <option value="junior">👨‍💻 Junior / Mid Level</option>
                                    <option value="senior">🚀 Senior / Lead</option>
                                </select>
                                <div className="pointer-events-none absolute right-4 top-3.5 text-[var(--text-secondary)]">▼</div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Action Button */}
                <div className="col-span-full text-center mt-6">
                    <button
                        type="submit"
                        disabled={loading || (jobId !== null)}
                        className="btn btn-primary px-16 py-4 text-lg w-full md:w-auto tracking-wide group"
                    >
                        {loading ? (
                            <>Starting Upload <span className="animate-pulse">...</span></>
                        ) : (
                            <>Batch Analyze <IoArrowForwardOutline className="ml-2 inline group-hover:translate-x-1 transition-transform" /></>
                        )}
                    </button>
                    <p className="mt-4 text-xs font-mono text-[var(--text-secondary)] opacity-60">Powered by Gemini Pro Vision</p>
                </div>
            </form>
        </div>
    );
}
