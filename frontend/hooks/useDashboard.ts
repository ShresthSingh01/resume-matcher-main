"use client";

import { useState, useEffect, useCallback } from "react";

export type Candidate = {
    id: string;
    name: string;
    email: string | null;
    phone: string | null;
    filename: string;
    match_score: number;
    interview_score: number;
    final_score: number;
    status: string;
    matched_skills: string | string[]; // JSON string or array
    missing_skills: string | string[];
    resume_evaluation_data: any;
    feedback_data: any;
};

export function useDashboard() {
    const [candidates, setCandidates] = useState<Candidate[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [view, setView] = useState<"upload" | "leaderboard">("upload");
    const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
    const [isVerifying, setIsVerifying] = useState(true);

    // Verify Session on Mount
    useEffect(() => {
        const verifySession = async () => {
            try {
                // If we are on the client and have a cookie, we check if it's valid
                // But since we can't easily check document.cookie perfectly for HTTPOnly, 
                // we just hit the verify endpoint.
                const res = await fetch("/api/verify");
                if (res.status === 401) {
                    // Stale cookie -> Redirect
                    window.location.href = "/login";
                } else {
                    // Valid or other error (let main fetch handle other errors)
                    setIsVerifying(false);
                }
            } catch (e) {
                console.error("Verification failed", e);
                setIsVerifying(false); // Let it fail naturally later or show UI
            }
        };
        verifySession();
    }, []);

    const fetchCandidates = useCallback(async () => {
        try {
            setLoading(true);
            const res = await fetch("/api/leaderboard"); // Proxy to /leaderboard
            if (res.status === 401) {
                window.location.href = "/login";
                return;
            }
            if (!res.ok) throw new Error("Failed to fetch leaderboard");

            const data = await res.json();
            setCandidates(data);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const uploadResumes = async (files: FileList, jdText: string, templateMode: string, enableInterview: boolean) => {
        try {
            setLoading(true);
            const formData = new FormData();
            for (let i = 0; i < files.length; i++) {
                formData.append("resumes", files[i]);
            }
            formData.append("job_description", jdText);
            formData.append("template_mode", templateMode);
            formData.append("enable_interview", String(enableInterview));

            const res = await fetch("/api/upload", {
                method: "POST",
                body: formData,
            });

            if (res.status === 401) {
                window.location.href = "/login";
                return;
            }


            let data;
            const contentType = res.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                data = await res.json();
            } else {
                // Fallback for 500s that return HTML/Text
                const text = await res.text();
                throw new Error(`Server Error (${res.status}): ${text.slice(0, 100)}...`);
            }

            if (!res.ok) throw new Error(data.detail || "Upload failed");

            if (!res.ok) throw new Error(data.detail || "Upload failed");

            // Async Queue: Return Job ID
            if (data.job_id) {
                return data.job_id;
            }

            // Fallback for non-async (shouldn't happen with new logic, but safe)
            await fetchCandidates();
            setView("leaderboard");
            return null;
        } catch (err: any) {
            console.error("Upload Error:", err);
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    };

    const inviteCandidate = async (candidateId: string, action?: "reject" | "shortlist" | "invite") => {
        try {
            // Optimistic? No, wait for result.
            let url = `/api/invite/candidate/${candidateId}`;
            if (action) url += `?action=${action}`;

            const res = await fetch(url, {
                method: "POST",
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Action failed");

            // Update local state to reflect status change?
            // Ideally backend returns updated candidate, but if not we can just refresh
            await fetchCandidates();
            return data.message;
        } catch (err: any) {
            throw new Error(err.message);
        }
    };

    const clearLeaderboard = async () => {
        if (!confirm("Clear all candidates?")) return;
        try {
            const res = await fetch("/api/candidates", { method: "DELETE" });
            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Failed to clear: ${res.status} ${text}`);
            }
            setCandidates([]);
            setView("upload");
            // Optional: alert check?
        } catch (e: any) {
            console.error(e);
            alert("Error clearing leaderboard: " + e.message);
        }
    };

    const logout = async () => {
        try {
            await fetch("/api/logout", { method: "POST" });
            window.location.href = "/login";
        } catch (e) {
            console.error(e);
        }
    };

    return {
        candidates,
        loading,
        error,
        view,
        setView,
        selectedCandidate,
        setSelectedCandidate,
        fetchCandidates,
        uploadResumes,
        inviteCandidate,
        clearLeaderboard,
        logout,
        isVerifying
    };
}
