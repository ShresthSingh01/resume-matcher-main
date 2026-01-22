"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { IoAlertCircleOutline, IoCheckmarkCircle } from "react-icons/io5";
import { toast } from "sonner";

export default function LoginPage() {
    const router = useRouter();
    const [isRegister, setIsRegister] = useState(false);
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError("");

        const endpoint = isRegister ? "/api/register" : "/api/login";

        // Convert to FormData as expected by backend (FastAPI Form(...))
        const formData = new FormData();
        formData.append("username", username);
        formData.append("password", password);

        try {
            const res = await fetch(endpoint, {
                method: "POST",
                body: formData,
            });

            const data = await res.json().catch(() => ({}));

            if (res.ok) {
                if (isRegister) {
                    toast.success("Account created! Please log in.");
                    setIsRegister(false);
                    setLoading(false);
                } else {
                    // Success
                    // Next.js router push
                    router.push("/");
                }
            } else {
                setError(data.detail || "Authentication Failed");
                setLoading(false);
            }
        } catch (err) {
            console.error(err);
            setError("Connection Error");
            setLoading(false);
        }
    };

    return (
        <div className="flex min-h-screen items-center justify-center p-4 bg-[var(--bg-primary)]">
            <div className="w-full max-w-[400px] text-center animate-in fade-in zoom-in duration-500">
                {/* Card */}
                <div className="relative overflow-hidden rounded-lg border border-[var(--border-color)] bg-[var(--bg-secondary)] p-8 shadow-xl">

                    {/* Logo */}
                    {/* Logo */}
                    <div className="relative z-10 mb-6 flex justify-center">
                        <img src="/VirexLogo.jpg" alt="Virex AI" className="h-16 w-auto object-contain rounded-md" />
                    </div>
                    <div className="relative z-10 mb-8 font-medium text-xs text-[var(--text-muted)] tracking-wide uppercase">
                        {isRegister ? "Create Organization Account" : "Enterprise Login"}
                    </div>

                    <form onSubmit={handleSubmit} className="relative z-10 text-left">
                        <div className="mb-4">
                            <label className="mb-1 block text-xs font-semibold uppercase text-[var(--text-muted)]">Username</label>
                            <input
                                type="text"
                                required
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter your username"
                                className="w-full"
                            />
                        </div>

                        <div className="mb-8">
                            <label className="mb-1 block text-xs font-semibold uppercase text-[var(--text-muted)]">Password</label>
                            <input
                                type="password"
                                required
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                className="w-full"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full btn btn-primary"
                        >
                            {loading ? (
                                <span className="flex items-center justify-center gap-2">
                                    <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white"></span>
                                    {isRegister ? "Creating..." : "Verifying..."}
                                </span>
                            ) : isRegister ? (
                                "Create Account"
                            ) : (
                                "Login"
                            )}
                        </button>

                        {error && (
                            <div className="mt-6 flex items-center justify-center gap-2 rounded bg-red-500/10 p-3 text-xs font-medium text-red-500 border border-red-500/20">
                                <IoAlertCircleOutline size={16} /> {error}
                            </div>
                        )}

                        <div className="mt-6 text-center text-sm text-[var(--text-secondary)]">
                            <span id="toggle-text">{isRegister ? "Already have an account?" : "No account?"}</span>{" "}
                            <button
                                type="button"
                                onClick={() => setIsRegister(!isRegister)}
                                className="font-semibold text-blue-500 hover:text-blue-400 hover:underline transition-colors ml-1"
                            >
                                {isRegister ? "Login" : "Register"}
                            </button>
                        </div>
                    </form>
                </div>

                <div className="mt-8 font-mono text-[10px] text-[var(--text-muted)]">
                    &copy; {new Date().getFullYear()} VIREX AI Enterprise
                </div>
            </div>
        </div>
    );
}
