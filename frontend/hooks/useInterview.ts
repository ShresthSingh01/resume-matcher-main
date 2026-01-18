"use client";

import { useState } from "react";

export type Message = {
    role: "system" | "ai" | "user";
    content: string;
};

export type InterviewStatus = "idle" | "loading" | "active" | "finished" | "error";

export function useInterview() {
    const [status, setStatus] = useState<InterviewStatus>("idle");
    const [messages, setMessages] = useState<Message[]>([]);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [currentQuestion, setCurrentQuestion] = useState<string | null>(null);
    const [result, setResult] = useState<any>(null); // Store final result
    const [error, setError] = useState<string | null>(null);

    const addMessage = (role: Message["role"], content: string) => {
        setMessages((prev) => [...prev, { role, content }]);
    };

    const startInterview = async (candidateId: string) => {
        setStatus("loading");
        setError(null);
        setMessages([]);

        try {
            const res = await fetch("/api/interview/start", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ candidate_id: candidateId }),
            });

            const data = await res.json();

            if (!res.ok) {
                throw new Error(data.detail || "Failed to start interview");
            }

            setSessionId(data.session_id);

            if (data.question) {
                addMessage("ai", data.question);
                setCurrentQuestion(data.question);
                setStatus("active");
                return data.question; // Return for TTS to use immediately
            } else {
                setStatus("active"); // Or some intermediate state?
            }
        } catch (err: unknown) {
            console.error(err);
            if (err instanceof Error) {
                setError(err.message);
            } else {
                setError("An unknown error occurred");
            }
            setStatus("error");
        }
    };

    const submitAnswer = async (answer: string) => {
        if (!sessionId) return;

        // Optimistic Update
        addMessage("user", answer);

        try {
            const res = await fetch("/api/interview/answer", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    session_id: sessionId,
                    answer: answer,
                }),
            });

            const data = await res.json();

            if (!res.ok) throw new Error("Failed to submit answer");

            if (data.is_finished) {
                setStatus("finished");
                addMessage("ai", "Interview Finished! Generating report...");
                // Auto-fetch result after short delay
                setTimeout(() => fetchResult(sessionId), 1000);
                return { isFinished: true, text: "Interview Finished." };
            } else {
                addMessage("ai", data.next_question);
                setCurrentQuestion(data.next_question);
                return { isFinished: false, text: data.next_question };
            }

        } catch (err: unknown) {
            console.error(err);
            addMessage("system", "Error sending answer. Please try again.");
        }
    };

    const fetchResult = async (sid: string) => {
        try {
            const res = await fetch("/api/interview/result", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sid }),
            });
            const data = await res.json();
            setResult(data);
        } catch (e) {
            console.error("Failed to fetch result", e);
        }
    };

    const flagViolation = async (reason: string) => {
        if (!sessionId) return;
        try {
            await fetch("/api/interview/flag", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ session_id: sessionId, reason }),
            });
        } catch (e) {
            console.error("Flag error", e);
        }
    };

    return {
        status,
        messages,
        currentQuestion,
        result,
        error,
        startInterview,
        submitAnswer,
        flagViolation,
        sessionId // Exposed for advanced checks if needed
    };
}
