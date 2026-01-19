"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { IoMicOutline, IoMicOffOutline, IoSend, IoWarningOutline } from "react-icons/io5";
import { useMedia } from "@/hooks/useMedia";
import { useSpeech } from "@/hooks/useSpeech";
import { Message } from "@/hooks/useInterview";

interface InterviewInterfaceProps {
    messages: Message[];
    onSendMessage: (text: string) => void;
    currentQuestion: string | null;
    status: string;
    onFlagViolation: (reason: string) => Promise<any>;
}

export default function InterviewInterface({ messages, onSendMessage, currentQuestion, status, onFlagViolation }: InterviewInterfaceProps) {
    const [inputValue, setInputValue] = useState("");
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputValueRef = useRef(inputValue);

    useEffect(() => {
        inputValueRef.current = inputValue;
    }, [inputValue]);

    // Media & Speech Hooks
    const { videoRef, initWebcam, initAudioContext, audioContextRef, analyserRef, getAudioLevel } = useMedia();

    const handleTranscript = useCallback((text: string) => {
        setInputValue(text);
    }, []);

    const handleSilence = useCallback(() => {
        console.log("Silence detected - stopping recording logic handled in hook");
    }, []);

    const { isListening, isSpeaking, startListening, stopListening, speak, stopSpeaking, error: speechError } = useSpeech(handleTranscript, handleSilence);

    // Effect to sync silence to stop
    useEffect(() => {
    }, []);

    // Init Webcam on mount
    useEffect(() => {
        initWebcam();
        initAudioContext();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    // Auto-Scroll chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    // TTS when AI message arrives
    useEffect(() => {
        if (currentQuestion && audioContextRef.current && analyserRef.current) {
            speak(currentQuestion, audioContextRef.current, analyserRef.current);
        } else if (currentQuestion) {
            speak(currentQuestion, null, null);
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [currentQuestion]);

    const handleSubmit = (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!inputValue.trim()) return;
        onSendMessage(inputValue);
        setInputValue("");
        stopListening(); // Ensure mic off
        stopSpeaking(); // Cut off AI if interrupting
    };

    // Timer Logic (Countdown 40 seconds per question)
    const [secondsLeft, setSecondsLeft] = useState(40);
    // Anti-Cheating State
    const [isFullscreen, setIsFullscreen] = useState(true);
    // Track if TTS has initiated for the current question to prevent early timer start
    const [hasSpeechStarted, setHasSpeechStarted] = useState(false);

    // Reset Timer on new question or status change
    useEffect(() => {
        setSecondsLeft(40);
        setHasSpeechStarted(false);
    }, [currentQuestion, status]);

    // Track when speech actually starts
    useEffect(() => {
        if (isSpeaking) {
            setHasSpeechStarted(true);
        }
    }, [isSpeaking]);

    useEffect(() => {
        let interval: NodeJS.Timeout;

        // ONLY count down if:
        // 1. Status is active
        // 2. AI is NOT speaking (wait for question to finish)
        // 3. Not paused by fullscreen blocker (optional but good UX)
        // 4. Speech has actually attempted to start (avoids gap between question load and TTS start)
        if (status === 'active' && !isSpeaking && isFullscreen && hasSpeechStarted) {
            interval = setInterval(() => {
                setSecondsLeft(prev => {
                    if (prev <= 1) {
                        clearInterval(interval);
                        // Auto-submit when time runs out
                        onSendMessage(inputValueRef.current || "Time Limit Exceeded");
                        setInputValue("");
                        return 0;
                    }
                    return prev - 1;
                });
            }, 1000);
        }
        return () => clearInterval(interval);
    }, [status, isSpeaking, isFullscreen, onSendMessage, hasSpeechStarted]);

    const reconnectFullscreen = () => {
        document.documentElement.requestFullscreen().catch(e => console.error(e));
    };



    // Anti-Cheating Logic
    useEffect(() => {
        if (status !== 'active') return;

        const handleVisibilityChange = async () => {
            if (document.hidden) {
                const res = await onFlagViolation("Tab Switch / Hidden Window");
                if (res?.warning_count) {
                    alert(`Warning: Violation recorded (${res.warning_count}/${res.limit}). Multiple violations will result in termination.`);
                }
            }
        };

        const handleFullscreenChange = async () => {
            const isFull = !!document.fullscreenElement;
            setIsFullscreen(isFull);
            if (!isFull) {
                const res = await onFlagViolation("Exited Fullscreen");
                if (res?.warning_count) {
                    alert(`Warning: Violation recorded (${res.warning_count}/${res.limit}). Stay in fullscreen.`);
                }
            }
        };

        // Enforce Fullscreen on start?
        // document.documentElement.requestFullscreen().catch(e => console.log("Fullscreen blocked", e));

        document.addEventListener("visibilitychange", handleVisibilityChange);
        document.addEventListener("fullscreenchange", handleFullscreenChange);

        return () => {
            document.removeEventListener("visibilitychange", handleVisibilityChange);
            document.removeEventListener("fullscreenchange", handleFullscreenChange);
        };
    }, [status, onFlagViolation]);

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    // Avatar Animation Frame
    const avatarRef = useRef<HTMLDivElement>(null);
    useEffect(() => {
        let rafId: number;
        const animate = () => {
            if (isSpeaking && avatarRef.current) {
                let scale = getAudioLevel();
                // Fallback Animation for Browser TTS (where getAudioLevel is static 1)
                if (scale <= 1.01) {
                    scale = 1 + Math.random() * 0.15;
                }

                avatarRef.current.style.transform = `scale(${scale})`;
                avatarRef.current.style.backgroundColor = "var(--primary)";
            } else if (isListening && avatarRef.current) {
                avatarRef.current.style.transform = "scale(1)";
                avatarRef.current.style.backgroundColor = "var(--error)"; // Listening red
                avatarRef.current.style.borderRadius = "30%"; // Morph
            } else if (avatarRef.current) {
                avatarRef.current.style.transform = "scale(1)";
                avatarRef.current.style.backgroundColor = "var(--secondary)"; // Idle blue
                avatarRef.current.style.borderRadius = "50%";
            }
            rafId = requestAnimationFrame(animate);
        };
        animate();
        return () => cancelAnimationFrame(rafId);
    }, [isSpeaking, isListening, getAudioLevel]);


    return (
        <div className="relative mx-auto flex h-[85vh] w-full max-w-[1100px] flex-col overflow-hidden rounded-[24px] glass-card neon-border shadow-[0_0_80px_rgba(168,85,247,0.2)] animate-in fade-in zoom-in duration-700 z-10">

            {/* 1. Avatar Area */}
            <div className="relative flex h-[220px] shrink-0 items-center justify-center border-b border-white/10 bg-black/40 backdrop-blur-md">

                {/* Background Grid/Mesh for Avatar Area */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.03)_1px,transparent_1px)] bg-[size:30px_30px] [mask-image:radial-gradient(ellipse_at_center,black,transparent_80%)]"></div>

                {/* Glowing Avatar Centerpiece */}
                <div className="relative group">
                    <div className="absolute inset-0 rounded-full bg-gradient-to-r from-cyan-500 to-purple-600 blur-2xl opacity-40 group-hover:opacity-60 transition-opacity duration-500 animate-pulse-slow"></div>
                    <div ref={avatarRef} className="h-32 w-32 rounded-full bg-black/80 border-2 border-white/20 shadow-2xl relative z-10 flex items-center justify-center transition-all duration-100 ease-out backdrop-blur-sm">
                        <div className="h-24 w-24 rounded-full bg-gradient-to-tr from-cyan-400 to-purple-500 opacity-90 shadow-[0_0_30px_rgba(139,92,246,0.5)]"></div>
                    </div>
                    {/* Orbit Rings */}
                    <div className="absolute inset-[-10px] rounded-full border border-cyan-500/20 border-dashed animate-[spin_10s_linear_infinite]"></div>
                    <div className="absolute inset-[-20px] rounded-full border border-purple-500/20 animate-[spin_15s_linear_infinite_reverse]"></div>
                </div>

                {/* Webcam PiP styled */}
                <div className="absolute left-6 top-6 h-[130px] w-[180px] overflow-hidden rounded-xl border border-white/20 shadow-2xl bg-black/60 backdrop-blur-md group hover:scale-105 transition-transform hover:shadow-cyan-500/20 hover:border-cyan-500/40">
                    <video ref={videoRef} autoPlay muted playsInline className="h-full w-full scale-x-[-1] object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                    <div className="absolute top-2 left-2 flex items-center gap-1.5 rounded-full bg-red-950/80 border border-red-500/30 px-2 py-0.5 text-[10px] font-bold text-red-400 backdrop-blur-md">
                        <div className="h-1.5 w-1.5 animate-pulse rounded-full bg-red-500"></div> LIVE FEED
                    </div>
                </div>

                {/* Status Badge */}
                <div className="absolute right-6 top-6 flex flex-col gap-2 items-end">

                    {/* Timer Badge */}
                    <div className={`rounded-full border px-4 py-1.5 font-mono text-[10px] font-bold shadow-[0_0_15px_rgba(6,182,212,0.1)] backdrop-blur-md flex items-center gap-2 ${secondsLeft < 10 ? 'border-red-500/30 bg-red-500/10 text-red-400' : 'border-cyan-500/30 bg-cyan-500/10 text-cyan-400'}`}>
                        <span className="text-xs">⏱</span> {formatTime(secondsLeft)}
                    </div>
                </div>
            </div>

            {/* TERMINATED BLOCKER OVERLAY */}
            {status === 'terminated' && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/95 backdrop-blur-xl p-8 text-center animate-in fade-in zoom-in duration-300">
                    <IoWarningOutline className="text-6xl text-red-600 mb-4 animate-bounce" />
                    <h2 className="text-3xl font-bold text-red-500 mb-2">Interview Terminated</h2>
                    <p className="text-slate-400 max-w-md mb-8 text-lg">
                        Multiple anti-cheating violations were detected. your session has been permanently locked.
                    </p>
                    <div className="rounded-full bg-red-900/20 border border-red-500/30 px-6 py-2 text-red-400 font-mono">
                        Status: DISQUALIFIED
                    </div>
                </div>
            )}

            {/* FULLSCREEN BLOCKER OVERLAY */}
            {!isFullscreen && status === 'active' && (
                <div className="absolute inset-0 z-50 flex flex-col items-center justify-center bg-black/95 backdrop-blur-xl p-8 text-center animate-in fade-in zoom-in duration-300">
                    <IoWarningOutline className="text-6xl text-red-500 mb-4 animate-bounce" />
                    <h2 className="text-2xl font-bold text-white mb-2">Interview Paused</h2>
                    <p className="text-slate-400 max-w-md mb-8">
                        You have exited fullscreen mode. This is flagged as a potential violation.
                        Please return to fullscreen to continue correctly.
                    </p>
                    <button
                        onClick={reconnectFullscreen}
                        className="rounded-full bg-red-600 px-8 py-3 font-bold text-white hover:bg-red-500 transition-all shadow-[0_0_30px_rgba(239,68,68,0.4)]"
                    >
                        Return to Interview
                    </button>
                </div>
            )}

            {/* 2. Chat Area */}
            <div className="flex-1 overflow-y-auto p-8 scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/10 space-y-8 bg-transparent relative">
                {messages.length === 0 && (
                    <div className="flex h-full flex-col items-center justify-center text-slate-500 opacity-80">
                        <div className="relative">
                            <div className="h-12 w-12 rounded-full border-t-2 border-l-2 border-cyan-500 animate-spin"></div>
                            <div className="absolute inset-0 h-12 w-12 rounded-full border-r-2 border-b-2 border-purple-500 animate-spin-reverse"></div>
                        </div>
                        <p className="font-mono text-xs tracking-[0.2em] mt-6 uppercase text-cyan-400">Initializing Session...</p>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <div key={i} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-in slide-in-from-bottom-2 duration-300`}>
                        <div className={`
                            relative max-w-[80%] rounded-2xl p-6 backdrop-blur-md border shadow-lg text-sm leading-relaxed
                            ${msg.role === 'user'
                                ? 'bg-gradient-to-br from-purple-600/20 to-cyan-600/20 border-purple-500/30 text-white rounded-tr-sm shadow-[0_0_15px_rgba(168,85,247,0.1)]'
                                : 'bg-black/40 border-white/10 text-slate-200 rounded-tl-sm shadow-[0_4px_20px_rgba(0,0,0,0.2)]'}
                        `}>
                            {/* Role Label */}
                            <div className={`absolute -top-3 ${msg.role === 'user' ? 'right-4 text-purple-400' : 'left-4 text-cyan-400'} text-[9px] font-bold uppercase tracking-widest bg-[#050510] px-2 py-0.5 rounded border border-white/10`}>
                                {msg.role === 'user' ? 'Candidate' : 'AI Interviewer'}
                            </div>
                            {msg.content}
                        </div>
                    </div>
                ))}
                <div ref={messagesEndRef} />
            </div>

            {/* 3. Input Area */}
            <div className="shrink-0 border-t border-white/10 bg-black/60 p-6 backdrop-blur-xl relative z-20">
                <form onSubmit={handleSubmit} className="flex gap-4 items-center max-w-4xl mx-auto">
                    <button
                        type="button"
                        onClick={isListening ? stopListening : startListening}
                        className={`
                            group flex h-14 w-14 shrink-0 items-center justify-center rounded-xl border transition-all duration-300
                            ${isListening
                                ? 'bg-red-500/10 border-red-500/50 text-red-400 shadow-[0_0_20px_rgba(239,68,68,0.3)] animate-pulse'
                                : 'bg-white/5 border-white/10 text-slate-400 hover:text-white hover:bg-white/10 hover:border-white/30 hover:shadow-[0_0_15px_rgba(255,255,255,0.1)]'}
                        `}
                    >
                        {isListening ? <IoMicOffOutline className="text-2xl" /> : <IoMicOutline className="text-2xl" />}
                    </button>

                    <div className="relative flex-1 group">
                        <div className="absolute inset-0 bg-gradient-to-r from-purple-500/20 to-cyan-500/20 rounded-xl blur opacity-0 group-focus-within:opacity-100 transition-opacity duration-500"></div>
                        <input
                            type="text"
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            placeholder={isListening ? "Listening..." : "Type your answer here..."}
                            disabled={isListening}
                            className="relative w-full rounded-xl border border-white/10 bg-black/40 p-4 pl-6 text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500/50 focus:bg-black/60 transition-all font-light tracking-wide shadow-inner"
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={!inputValue.trim() && !isListening}
                        className="flex h-14 w-14 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-purple-600 to-cyan-600 text-white shadow-[0_0_20px_rgba(139,92,246,0.3)] transition-all hover:scale-105 hover:shadow-[0_0_30px_rgba(6,182,212,0.5)] active:scale-95 disabled:opacity-50 disabled:grayscale"
                    >
                        <IoSend size={20} className="ml-1" />
                    </button>
                </form>
                {speechError && (
                    <div className="mt-3 text-center">
                        <span className="text-[10px] font-bold text-red-300 bg-red-950/50 border border-red-500/30 py-1 px-3 rounded-full inline-flex items-center gap-1">
                            <IoWarningOutline /> {speechError}
                        </span>
                    </div>
                )}
            </div>

        </div>
    );
}
