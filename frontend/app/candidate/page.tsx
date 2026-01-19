"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useState, Suspense } from "react";
import CandidateLanding from "@/components/interview/CandidateLanding";
import InterviewInterface from "@/components/interview/InterviewInterface";
import InterviewReport from "@/components/interview/InterviewReport";
import { useInterview } from "@/hooks/useInterview";

function CandidateFlow() {
    const searchParams = useSearchParams();
    const [candidateId, setCandidateId] = useState<string | null>(null);
    const { status, messages, currentQuestion, result, startInterview, submitAnswer, error, flagViolation } = useInterview();

    useEffect(() => {
        const cid = searchParams.get("candidate_id");
        if (cid) setCandidateId(cid);
    }, [searchParams]);

    const handleStart = async () => {
        if (!candidateId) return;
        try {
            await document.documentElement.requestFullscreen();
        } catch (err) {
            console.error("Fullscreen blocked or failed:", err);
            // We continue anyway, as the blocker in InterviewInterface will catch it
        }
        startInterview(candidateId);
    };

    // View Routing
    if (status === "finished" && result) {
        return <InterviewReport result={result} />;
    }

    if (status === "active" || status === "loading") {
        return (
            <div className="p-4">
                <InterviewInterface
                    messages={messages}
                    onSendMessage={submitAnswer}
                    currentQuestion={currentQuestion}
                    status={status}
                    onFlagViolation={flagViolation}
                />
            </div>
        );
    }

    // Default: Landing
    return (
        <div className="container mx-auto">
            <header className="mb-8 mt-4 text-center">
                <h1 className="text-4xl font-bold uppercase text-[var(--text-main)] drop-shadow-sm">
                    Virex AI Interview
                </h1>
                <p className="font-mono text-[var(--text-muted)]">
                    {candidateId ? `Candidate ID: ${candidateId.slice(0, 8)}...` : "Invalid Link"}
                </p>
            </header>

            {error && (
                <div className="mx-auto mb-4 max-w-lg rounded border-2 border-black bg-[var(--error)] p-4 font-bold text-white shadow-lg">
                    Error: {error}
                </div>
            )}

            <CandidateLanding
                onStart={handleStart}
                loading={(status as any) === "loading"}
            />

            {!candidateId && (
                <div className="text-center font-bold text-red-500">
                    Missing candidate_id in URL. Please check your invite link.
                </div>
            )}
        </div>
    );
}

export default function CandidatePage() {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <CandidateFlow />
        </Suspense>
    );
}
