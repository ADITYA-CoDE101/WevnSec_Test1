import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Loader2, ArrowRight } from "lucide-react";
import { LogoMark, EASE } from "@/components/wevnsec/Reveal";
import { useAuth } from "@/context/AuthContext";
import { formatApiErrorDetail } from "@/lib/api";

export default function Auth({ mode }) {
    const isSignup = mode === "signup";
    const { login, signup } = useAuth();
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    const submit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            if (isSignup) await signup(name, email, password);
            else await login(email, password);
            navigate("/dashboard");
        } catch (err) {
            setError(formatApiErrorDetail(err.response?.data?.detail));
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="relative min-h-screen flex items-center justify-center px-4 pt-16 overflow-hidden" data-testid="auth-page">
            <div className="absolute inset-0 dot-grid [mask-image:radial-gradient(ellipse_60%_50%_at_50%_30%,black,transparent)]" />
            <div className="absolute -top-32 left-1/2 -translate-x-1/2 h-[360px] w-[600px] rounded-full bg-brand/12 blur-[110px] pointer-events-none" />

            <motion.div
                initial={{ opacity: 0, y: 24 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, ease: EASE }}
                className="relative w-full max-w-sm rounded-xl border border-border bg-card p-8 card-glow"
            >
                <div className="flex items-center gap-2.5">
                    <LogoMark size={30} />
                    <span className="text-lg font-semibold tracking-tight text-foreground">
                        wevn<span className="text-brand">sec</span>
                    </span>
                </div>
                <p className="mt-6 font-mono text-[11px] uppercase tracking-[0.22em] text-brand">
                    {isSignup ? "// create account" : "// welcome back"}
                </p>
                <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                    {isSignup ? "Start watching your attack surface" : "Sign in to your dashboard"}
                </h1>

                <form onSubmit={submit} className="mt-7 space-y-4">
                    {isSignup && (
                        <div>
                            <label htmlFor="auth-name" className="block font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground mb-1.5">Name</label>
                            <input
                                id="auth-name"
                                data-testid="auth-name-input"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Ada Lovelace"
                                className="w-full h-11 rounded-md border border-border bg-background px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-brand/60 focus:shadow-[0_0_0_3px_hsl(var(--brand)/0.15)] transition-all"
                            />
                        </div>
                    )}
                    <div>
                        <label htmlFor="auth-email" className="block font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground mb-1.5">Email</label>
                        <input
                            id="auth-email"
                            type="email"
                            required
                            data-testid="auth-email-input"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="you@company.com"
                            className="w-full h-11 rounded-md border border-border bg-background px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-brand/60 focus:shadow-[0_0_0_3px_hsl(var(--brand)/0.15)] transition-all"
                        />
                    </div>
                    <div>
                        <label htmlFor="auth-password" className="block font-mono text-[11px] uppercase tracking-[0.14em] text-muted-foreground mb-1.5">Password</label>
                        <input
                            id="auth-password"
                            type="password"
                            required
                            minLength={isSignup ? 8 : 1}
                            data-testid="auth-password-input"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder={isSignup ? "8+ characters" : "••••••••"}
                            className="w-full h-11 rounded-md border border-border bg-background px-3.5 text-sm text-foreground placeholder:text-muted-foreground/50 outline-none focus:border-brand/60 focus:shadow-[0_0_0_3px_hsl(var(--brand)/0.15)] transition-all"
                        />
                    </div>

                    {error && (
                        <p data-testid="auth-error" className="rounded-md border border-red-400/30 bg-red-400/10 px-3.5 py-2.5 text-sm text-red-400">
                            {error}
                        </p>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        data-testid="auth-submit-button"
                        className="w-full h-11 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-sm font-semibold flex items-center justify-center gap-2 hover:brightness-110 disabled:opacity-70 transition-all duration-200"
                    >
                        {loading ? <Loader2 size={15} className="animate-spin" /> : <ArrowRight size={15} />}
                        {isSignup ? "Create account" : "Sign in"}
                    </button>
                </form>

                <p className="mt-6 text-center text-sm text-muted-foreground">
                    {isSignup ? "Already have an account? " : "New to WevnSec? "}
                    <Link
                        to={isSignup ? "/signin" : "/signup"}
                        className="text-brand font-medium hover:underline"
                        data-testid="auth-mode-switch"
                    >
                        {isSignup ? "Sign in" : "Create one free"}
                    </Link>
                </p>
            </motion.div>
        </main>
    );
}
