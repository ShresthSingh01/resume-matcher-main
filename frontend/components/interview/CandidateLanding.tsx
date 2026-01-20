"use client";

import { IoPlayOutline } from "react-icons/io5";

interface CandidateLandingProps {
    onStart: () => void;
    loading: boolean;
}

export default function CandidateLanding({ onStart, loading }: CandidateLandingProps) {
    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center p-4">
            <div className="glass-card neon-border w-full max-w-[640px] text-center relative overflow-hidden group p-1 z-10">

                {/* Internal container to keep content separated from border padding if needed */}
                <div className="bg-black/40 rounded-xl p-8 backdrop-blur-sm relative h-full w-full">

                    {/* Background Gradients */}
                    <div className="absolute -top-32 -left-32 w-64 h-64 bg-purple-500/20 rounded-full blur-[100px] pointer-events-none group-hover:bg-purple-500/30 transition-all duration-700"></div>
                    <div className="absolute -bottom-32 -right-32 w-64 h-64 bg-cyan-500/20 rounded-full blur-[100px] pointer-events-none group-hover:bg-cyan-500/30 transition-all duration-700"></div>

                    <div className="relative z-10">
                        <div className="mb-8 inline-flex items-center justify-center w-24 h-24 rounded-full bg-gradient-to-br from-white/10 to-transparent border border-white/20 shadow-[0_0_30px_rgba(139,92,246,0.3)] animate-pulse-slow backdrop-blur-sm">
                            <IoPlayOutline size={48} className="text-white drop-shadow-[0_0_10px_rgba(168,85,247,0.8)] ml-1" />
                        </div>

                        <h2 className="mb-4 text-6xl font-black tracking-tighter text-transparent bg-clip-text bg-gradient-to-r from-white via-purple-200 to-cyan-200 drop-shadow-sm">
                            Ready?
                        </h2>
                        <p className="mb-10 text-slate-400 font-light tracking-widest uppercase text-xs">Awaiting Neural Link Connection</p>

                        <div className="mb-12 text-left p-6 bg-white/5 rounded-xl border border-white/10 backdrop-blur-md relative overflow-hidden">
                            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-purple-500 to-cyan-500"></div>
                            <p className="font-bold text-sm text-white mb-4 flex items-center gap-2 uppercase tracking-wide">
                                <span className="text-cyan-400">{'// PROTOCOL:'}</span>
                            </p>
                            <ul className="space-y-4 text-slate-300 font-light text-sm tracking-wide">
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-purple-500 mt-1.5 shadow-[0_0_10px_rgba(168,85,247,0.8)]"></span>
                                    <span>Find a <strong className="text-white font-medium">silent zone</strong> for optimal audio capture.</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-500 mt-1.5 shadow-[0_0_10px_rgba(6,182,212,0.8)]"></span>
                                    <span>Verify <strong className="text-white font-medium">camera & mic</strong> are active/allowed.</span>
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="w-1.5 h-1.5 rounded-full bg-pink-500 mt-1.5 shadow-[0_0_10px_rgba(236,72,153,0.8)]"></span>
                                    <span>Speak <strong className="text-white font-medium">naturally</strong>. The AI is listening.</span>
                                </li>
                            </ul>
                        </div>

                        <button
                            onClick={onStart}
                            disabled={loading}
                            className="group relative w-full max-w-sm mx-auto overflow-hidden rounded-xl bg-white text-black p-1 transition-all hover:scale-[1.02] active:scale-[0.98]"
                        >
                            <div className="absolute inset-0 bg-gradient-to-r from-purple-600 via-cyan-500 to-purple-600 animate-aurora opacity-100 group-hover:opacity-100 transition-opacity"></div>
                            <div className="relative flex items-center justify-center gap-3 bg-black text-white h-14 rounded-[10px] group-hover:bg-black/90 transition-colors uppercase font-bold tracking-[0.15em] text-sm">
                                {loading ? (
                                    <>
                                        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
                                        Initializing...
                                    </>
                                ) : (
                                    <>
                                        Initiate Session <IoPlayOutline className="group-hover:translate-x-1 transition-transform" />
                                    </>
                                )}
                            </div>
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
