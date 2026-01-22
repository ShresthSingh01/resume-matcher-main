"use client";

import { useState } from "react";
import { Candidate } from "@/hooks/useDashboard";
import { IoListOutline, IoTrashOutline, IoRefreshOutline, IoMailOutline } from "react-icons/io5";

interface LeaderboardSectionProps {
    candidates: Candidate[];
    onView: (c: Candidate) => void;
    onInvite: (id: string, action: "reject" | "shortlist" | "invite") => void;
    onClear: () => void;
    onRefresh: () => void; // Usually just sets view to upload or re-fetches
}

export default function LeaderboardSection({ candidates, onView, onInvite, onClear, onRefresh }: LeaderboardSectionProps) {


    const getStatusColor = (status: string) => {
        const s = (status || "").toLowerCase();
        if (s.includes("selected") || s.includes("hired")) return "text-emerald-700 font-extrabold";
        if (s.includes("completed") || s.includes("interviewed")) return "text-emerald-500 font-bold";
        if (s.includes("shortlist")) return "text-blue-600 font-semibold"; // Shortlisted -> Needs Interview
        if (s.includes("reject")) return "text-red-500";
        if (s.includes("waitlist")) return "text-orange-500";
        if (s.includes("invited")) return "text-purple-500";
        if (s.includes("terminated")) return "text-red-600 font-extrabold bg-red-100 px-2 py-0.5 rounded";
        return "text-gray-500";
    };

    const handleAction = (id: string) => {
        // Send 'invite' as generic action; backend decides based on status
        onInvite(id, "invite");
    };

    const getActionBtn = (c: Candidate) => {
        const s = (c.status || "").toLowerCase();

        // If action already taken (email sent), show disabled state
        // EXCEPTION: "Selected (Resume)" or "Rejected (Resume)" are pending manual confirmation
        const isResumeDecision = s.includes("(resume)");
        if ((s.includes("sent") || s.includes("invited") || s.includes("selected")) && !isResumeDecision) {
            let label = "Invited";
            if (s.includes("reject")) label = "Rejection Sent";
            else if (s.includes("selected") || s.includes("solicited") || s === "shortlist sent") label = "Next Round Sent";

            return (
                <div className="flex gap-2">
                    <button onClick={() => onView(c)} className="btn btn-secondary text-xs py-1 px-2">View</button>
                    <button disabled className="btn btn-secondary opacity-50 text-xs py-1 px-3 cursor-not-allowed">
                        {label}
                    </button>
                </div>
            );
        }

        // Available Actions for Pending/Reviewed/Decided but not sent
        let actionLabel = "Invite"; // Default for Shortlisted/Pending -> Invite to Interview
        let btnClass = "btn btn-primary text-xs py-1 px-4 flex items-center gap-2";

        if (s.includes("reject")) {
            actionLabel = "Send Rejection"; // Changed from Rejection
            btnClass = "btn bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-4 flex items-center gap-2 border border-red-500 shadow-sm";
        } else if (s.includes("interviewed")) {
            // Dual Buttons for Post-Interview Decision
            return (
                <div className="flex gap-2 items-center">
                    <button onClick={() => onView(c)} className="btn btn-secondary text-xs py-1 px-2" title="View Details">View</button>

                    <button
                        onClick={() => onInvite(c.id, "invite")}
                        className="btn bg-emerald-600 hover:bg-emerald-700 text-white text-xs py-1 px-3 shadow-sm flex items-center gap-1"
                        title="Send Invitation / Next Round"
                    >
                        <IoMailOutline /> Send Invite
                    </button>

                    <button
                        onClick={() => onInvite(c.id, "reject")}
                        className="btn bg-red-600 hover:bg-red-700 text-white text-xs py-1 px-3 shadow-sm flex items-center gap-1"
                        title="Reject Candidate"
                    >
                        Reject
                    </button>
                </div>
            );
        } else if (s.includes("selected")) {
            // Must be Selected (Resume) or similar pending
            actionLabel = "Send Next Round";
            btnClass = "btn bg-emerald-600 hover:bg-emerald-700 text-white text-xs py-1 px-4 shadow-sm";
        } else if (s.includes("shortlist")) {
            actionLabel = "Invite to Interview";
            // Keep primary blue/purple for invite
        } else if (s.includes("interviewing") || s.includes("active")) {
            actionLabel = "In Progress";
            btnClass = "btn bg-amber-500/10 text-amber-500 border border-amber-500/20 cursor-wait text-xs py-1 px-4";
        }

        return (
            <div className="flex gap-1 items-center">
                <button onClick={() => onView(c)} className="btn btn-secondary text-xs py-1 px-2" title="View Details">View</button>

                <button
                    onClick={() => handleAction(c.id)}
                    className={btnClass}
                    title={`Send email based on status: ${c.status}`}
                >
                    <IoMailOutline /> {actionLabel}
                </button>
            </div>
        );
    };

    const [showClearConfirmation, setShowClearConfirmation] = useState(false);

    return (
        <div className="mx-auto w-full max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Confirmation Modal */}
            {showClearConfirmation && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 backdrop-blur-sm animate-in fade-in duration-200">
                    <div className="absolute inset-0 bg-black/60" onClick={() => setShowClearConfirmation(false)}></div>
                    <div className="relative w-full max-w-md overflow-hidden rounded-xl border border-[var(--border-color)] bg-[var(--bg-secondary)] shadow-2xl p-6">
                        <h3 className="text-lg font-bold text-[var(--text-main)] mb-2">Clear Leaderboard?</h3>
                        <p className="text-sm text-[var(--text-secondary)] mb-6">
                            Are you sure you want to delete all candidates? This action cannot be undone.
                        </p>
                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setShowClearConfirmation(false)}
                                className="px-4 py-2 rounded-lg text-sm font-medium text-[var(--text-secondary)] hover:bg-[var(--bg-tertiary)] transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={() => {
                                    onClear();
                                    setShowClearConfirmation(false);
                                }}
                                className="px-4 py-2 rounded-lg text-sm font-bold bg-red-600 text-white hover:bg-red-700 transition-colors shadow-lg shadow-red-500/20"
                            >
                                Yes, Clear All
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="glass-card min-h-[500px] p-0 overflow-hidden">
                <div className="p-6 border-b border-[var(--border-color)] flex flex-col items-start justify-between gap-4 md:flex-row md:items-center bg-[var(--bg-secondary)]">
                    <div>
                        <h2 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-[var(--text-main)]">
                            <IoListOutline className="text-blue-500" /> Candidate Leaderboard
                        </h2>
                        <p className="mt-1 font-normal text-sm text-[var(--text-secondary)]">Ranked by Resume Match & Interview Performance</p>
                    </div>
                    <div className="flex gap-3">
                        <button onClick={() => setShowClearConfirmation(true)} className="btn bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 transition-all">
                            <IoTrashOutline className="mr-2 inline" /> Clear
                        </button>
                        <button onClick={onRefresh} className="btn btn-secondary">
                            <IoRefreshOutline className="mr-2 inline" /> Refresh
                        </button>
                    </div>
                </div>

                <div className="w-full overflow-x-auto">
                    <table className="w-full min-w-[800px] text-left">
                        <thead className="bg-slate-900/50 text-[var(--text-muted)] border-b border-[var(--border-color)]">
                            <tr>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Rank</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Name</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Match Rating</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Interview</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Final Score</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Status</th>
                                <th className="p-4 font-semibold uppercase tracking-wider text-xs">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[var(--border-color)] bg-[var(--bg-secondary)]">
                            {candidates.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="p-16 text-center text-[var(--text-secondary)] font-light">
                                        No candidates found.<br />Upload resumes to populate the leaderboard.
                                    </td>
                                </tr>
                            ) : candidates.map((c, i) => (
                                <tr key={c.id} className="group hover:bg-slate-800/80 transition-colors">
                                    <td className="p-4 font-mono font-bold text-lg text-[var(--text-muted)] group-hover:text-blue-500 transition-colors">#{i + 1}</td>
                                    <td className="p-4 font-medium text-[var(--text-main)]">{c.name || c.filename}</td>
                                    <td className="p-4">
                                        <div className="flex items-center gap-3">
                                            <div className="h-1.5 w-24 rounded-full bg-slate-700 overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-500"
                                                    style={{ width: `${c.match_score}%` }}
                                                />
                                            </div>
                                            <span className="font-mono text-sm text-[var(--text-secondary)]">{c.match_score.toFixed(0)}%</span>
                                        </div>
                                    </td>
                                    <td className="p-4 font-mono">
                                        {c.interview_score > 0 ? (
                                            <span className="font-bold text-emerald-500">{c.interview_score}/100</span>
                                        ) : (
                                            <span className="text-[var(--text-muted)]">-</span>
                                        )}
                                    </td>
                                    <td className="p-4 font-mono">
                                        {c.final_score > 0 ? (
                                            <span className="font-bold text-violet-400">{c.final_score}/100</span>
                                        ) : (
                                            <span className="text-[var(--text-muted)]">-</span>
                                        )}
                                    </td>
                                    <td className={`p-4 font-bold uppercase text-[10px] tracking-wider ${getStatusColor(c.status)}`}>
                                        {c.status || "PENDING"}
                                    </td>
                                    <td className="p-4">
                                        {getActionBtn(c)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
