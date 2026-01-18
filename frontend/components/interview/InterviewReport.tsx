"use client";

import { IoDownloadOutline } from "react-icons/io5";

interface InterviewReportProps {
    result: any;
}

export default function InterviewReport({ result }: InterviewReportProps) {
    if (!result) return <div>Loading results...</div>;

    const downloadReport = () => {
        let content = `AI INTERVIEW REPORT\n`;
        content += `================================\n`;
        content += `Session ID: ${result.session_id}\n`;
        content += `Date: ${new Date().toLocaleString()}\n\n`;

        content += `SCORES\n`;
        content += `------\n`;
        content += `Interview Score: ${result.interview_score}/100\n`;
        content += `Resume Match: ${result.resume_score}%\n`;
        content += `Final Weighted Score: ${result.final_score}%\n\n`;

        content += `TRANSCRIPT & FEEDBACK\n`;
        content += `================================\n\n`;

        result.transcript.forEach((t: any, i: number) => {
            content += `Q${i + 1}: ${t.q}\n\n`;
            content += `Answer: ${t.a}\n\n`;
            content += `Score: ${t.score}/10\n`;
            content += `Feedback: ${t.feedback}\n`;
            content += `------------------------------------------------\n\n`;
        });

        const blob = new Blob([content], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `Interview_Report_${new Date().toISOString().slice(0, 10)}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    return (
        <div className="mx-auto w-full max-w-[900px] p-6 text-center animate-in fade-in zoom-in duration-500">
            <div className="card border border-white/10 bg-slate-900/50 backdrop-blur-xl relative overflow-hidden">
                {/* Background Decor */}
                <div className="absolute top-0 left-0 w-full h-2 bg-gradient-to-r from-purple-500 via-pink-500 to-cyan-500"></div>

                <div className="mb-8 inline-flex items-center justify-center rounded-full bg-green-500/20 p-4 ring-1 ring-green-500/50 shadow-[0_0_20px_rgba(16,185,129,0.3)] animate-bounce-slow">
                    <IoDownloadOutline size={32} className="text-green-400" />
                </div>

                <h2 className="mb-2 text-4xl font-bold tracking-tight text-white">Interview Complete</h2>
                <p className="mb-10 font-light text-slate-400">&quot;Your session has been recorded and analyzed.&quot;</p>

                <div className="grid gap-8 md:grid-cols-2">
                    {/* Score Box */}
                    <div className="rounded-2xl border border-white/10 bg-white/5 p-8 relative overflow-hidden group hover:bg-white/10 transition-colors">
                        <div className="absolute -right-10 -top-10 w-32 h-32 bg-purple-500/20 rounded-full blur-3xl group-hover:bg-purple-500/30 transition-all"></div>
                        <div className="mb-4 text-xs font-bold uppercase tracking-widest text-slate-400">Performance Score</div>
                        <div className="text-[5rem] font-bold leading-none text-transparent bg-clip-text bg-gradient-to-br from-purple-400 to-cyan-400">
                            {result.interview_score}<span className="text-3xl text-slate-500">%</span>
                        </div>
                    </div>

                    {/* Scores Breakdown */}
                    <div className="flex flex-col justify-center space-y-4 text-left p-6 rounded-2xl border border-white/10 bg-white/5">
                        <div className="flex justify-between items-center border-b border-white/10 pb-3">
                            <span className="font-medium text-slate-400 uppercase text-xs tracking-wider">Resume Match</span>
                            <span className="font-bold text-2xl text-white">{result.resume_score}%</span>
                        </div>
                        <div className="flex justify-between items-center border-b border-white/10 pb-3">
                            <span className="font-medium text-slate-400 uppercase text-xs tracking-wider">Final Weighted</span>
                            <span className="font-bold text-2xl text-white">{result.final_score}%</span>
                        </div>
                        <div className={`mt-4 p-3 text-center rounded-xl font-bold uppercase tracking-widest text-sm shadow-lg ${result.final_score >= 70 ? "bg-green-500/20 text-green-300 border border-green-500/30" : "bg-yellow-500/20 text-yellow-300 border border-yellow-500/30"}`}>
                            {result.final_score >= 70 ? "Shortlisted" : "Review Needed"}
                        </div>
                    </div>
                </div>

                <div className="mt-12 text-left">
                    <h3 className="mb-6 flex items-center gap-4 text-xl font-bold text-white">
                        <span className="bg-gradient-to-r from-purple-500 to-blue-500 w-1 h-6 rounded-full"></span>
                        Detailed Feedback
                    </h3>
                    <div className="space-y-4">
                        {result.transcript?.map((item: any, idx: number) => (
                            <div key={idx} className="group rounded-2xl border border-white/5 bg-white/5 p-6 hover:bg-white/10 hover:border-white/20 transition-all">
                                <div className="mb-3 flex items-center justify-between">
                                    <span className="rounded px-2 py-1 text-[10px] font-bold text-slate-300 bg-white/10 uppercase tracking-wider">Question {idx + 1}</span>
                                    <span className="font-mono text-xs font-bold text-purple-400">Score: {item.score}/10</span>
                                </div>
                                <div className="mb-4 text-lg font-medium italic text-slate-300">&quot;{item.q}&quot;</div>
                                <div className="mb-4 rounded-xl border-l-2 border-purple-500 bg-black/20 p-4 font-light text-slate-400">
                                    &quot;{item.a}&quot;
                                </div>

                                <div className="grid gap-4 md:grid-cols-[auto_1fr] text-sm bg-blue-500/5 p-4 rounded-xl border border-blue-500/10">
                                    <div className="font-bold text-cyan-400 uppercase text-[10px] pt-1 tracking-widest">AI Feedback</div>
                                    <div className="text-slate-300 leading-relaxed">
                                        {item.feedback || "No specific feedback provided."}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="mt-12 sticky bottom-4">
                    <button onClick={downloadReport} className="btn btn-primary w-full md:w-auto px-12 py-4 text-lg shadow-lg shadow-purple-900/20">
                        Download Full Report <IoDownloadOutline className="ml-2 inline" size={20} />
                    </button>
                </div>

            </div>
        </div>
    );
}
