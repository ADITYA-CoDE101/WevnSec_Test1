import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence, useMotionValue, useSpring, useTransform } from "framer-motion";
import { CheckCircle2, AlertTriangle, XCircle, CircleDashed } from "lucide-react";
import { CHECKS } from "./data";

const STATUS = {
    PASS: { icon: CheckCircle2, cls: "text-emerald-400", chip: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10" },
    WARN: { icon: AlertTriangle, cls: "text-amber-400", chip: "text-amber-400 border-amber-400/30 bg-amber-400/10" },
    FAIL: { icon: XCircle, cls: "text-red-400", chip: "text-red-400 border-red-400/30 bg-red-400/10" },
};

const TABS = [
    { id: "all", label: "All Checks" },
    { id: "FAIL", label: "Critical" },
    { id: "WARN", label: "Warnings" },
    { id: "PASS", label: "Passed" },
];

export const Terminal = ({ target, runNonce }) => {
    const [phase, setPhase] = useState("typing");
    const [typed, setTyped] = useState("");
    const [shown, setShown] = useState(0);
    const [tab, setTab] = useState("all");
    const [cycle, setCycle] = useState(0);
    const timers = useRef([]);

    const mx = useMotionValue(0);
    const my = useMotionValue(0);
    const rotateX = useSpring(useTransform(my, [-0.5, 0.5], [3.5, -3.5]), { stiffness: 140, damping: 18 });
    const rotateY = useSpring(useTransform(mx, [-0.5, 0.5], [-4.5, 4.5]), { stiffness: 140, damping: 18 });

    useEffect(() => {
        timers.current.forEach(clearTimeout);
        timers.current = [];
        const later = (fn, ms) => timers.current.push(setTimeout(fn, ms));
        const cmd = `wevnsec scan --target https://${target}`;

        setPhase("typing");
        setTyped("");
        setShown(0);

        let i = 0;
        const typeNext = () => {
            i += 1;
            setTyped(cmd.slice(0, i));
            if (i < cmd.length) later(typeNext, 16 + Math.random() * 26);
            else {
                setPhase("scanning");
                CHECKS.forEach((_, idx) => {
                    later(() => setShown(idx + 1), 380 * (idx + 1));
                });
                later(() => setPhase("done"), 380 * CHECKS.length + 500);
                later(() => setCycle((c) => c + 1), 380 * CHECKS.length + 7500);
            }
        };
        later(typeNext, 350);
        return () => timers.current.forEach(clearTimeout);
    }, [target, runNonce, cycle]);

    const counts = {
        all: CHECKS.length,
        FAIL: CHECKS.filter((c) => c.status === "FAIL").length,
        WARN: CHECKS.filter((c) => c.status === "WARN").length,
        PASS: CHECKS.filter((c) => c.status === "PASS").length,
    };
    const visible = CHECKS.slice(0, shown).filter((c) => tab === "all" || c.status === tab);

    return (
        <div
            style={{ perspective: 1200 }}
            onMouseMove={(e) => {
                const r = e.currentTarget.getBoundingClientRect();
                mx.set((e.clientX - r.left) / r.width - 0.5);
                my.set((e.clientY - r.top) / r.height - 0.5);
            }}
            onMouseLeave={() => { mx.set(0); my.set(0); }}
        >
            <motion.div
                data-testid="mock-terminal-container"
                style={{ rotateX, rotateY, transformStyle: "preserve-3d" }}
                initial={{ opacity: 0, y: 44 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.9, delay: 0.5, ease: [0.16, 1, 0.3, 1] }}
                className="terminal-shell rounded-xl border border-brand/25 card-glow overflow-hidden text-left"
            >
                <div className="relative flex items-center justify-between px-4 h-11 border-b border-white/10">
                    <div className="absolute inset-x-0 top-0 h-px overflow-hidden">
                        {phase === "scanning" && (
                            <div className="h-full w-1/3 bg-gradient-to-r from-transparent via-brand to-transparent scan-sweep" />
                        )}
                    </div>
                    <div className="flex items-center gap-2">
                        <span className="h-3 w-3 rounded-full bg-[#FF5F57]" />
                        <span className="h-3 w-3 rounded-full bg-[#FEBC2E]" />
                        <span className="h-3 w-3 rounded-full bg-[#28C840]" />
                    </div>
                    <p className="hidden sm:block font-mono text-[11px] text-slate-400 tracking-wider">
                        wevnsec — live scan session
                    </p>
                    <div
                        className={`flex items-center gap-1.5 font-mono text-[10px] px-2 py-1 rounded-full border ${
                            phase === "done"
                                ? "text-emerald-400 border-emerald-400/30 bg-emerald-400/10"
                                : "text-brand border-brand/30 bg-brand/10"
                        }`}
                        data-testid="terminal-status-pill"
                    >
                        <span className={`h-1.5 w-1.5 rounded-full ${phase === "done" ? "bg-emerald-400" : "bg-brand animate-pulse"}`} />
                        {phase === "done" ? "COMPLETE" : phase === "scanning" ? "SCANNING" : "RESOLVING"}
                    </div>
                </div>

                <div className="flex items-center gap-1 px-3 pt-3 overflow-x-auto">
                    {TABS.map((t) => (
                        <button
                            key={t.id}
                            onClick={() => setTab(t.id)}
                            data-testid={`terminal-tab-${t.id.toLowerCase()}`}
                            className={`whitespace-nowrap font-mono text-[11px] px-2.5 py-1.5 rounded-md transition-colors duration-200 ${
                                tab === t.id
                                    ? "bg-brand/15 text-brand border border-brand/30"
                                    : "text-slate-500 hover:text-slate-300 border border-transparent"
                            }`}
                        >
                            {t.label} ({counts[t.id]})
                        </button>
                    ))}
                </div>

                <div className="p-4 sm:p-5 font-mono text-[12px] sm:text-[13px] leading-relaxed min-h-[330px]">
                    <p className="text-slate-400">
                        <span className="text-brand">$</span> {typed}
                        {phase === "typing" && <span className="caret-blink text-brand">▍</span>}
                    </p>

                    <div className="mt-3 space-y-1.5">
                        <AnimatePresence initial={false}>
                            {visible.map((c) => {
                                const S = STATUS[c.status];
                                return (
                                    <motion.div
                                        key={`${c.id}-${cycle}`}
                                        data-testid={`terminal-check-row-${c.id.toLowerCase()}`}
                                        initial={{ opacity: 0, x: -14 }}
                                        animate={{ opacity: 1, x: 0 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
                                        className="group flex items-start gap-3 rounded-lg border border-white/5 bg-white/[0.02] hover:border-brand/30 hover:bg-brand/[0.04] px-3 py-2.5 transition-colors duration-200"
                                    >
                                        <S.icon size={15} className={`mt-0.5 shrink-0 ${S.cls}`} />
                                        <div className="min-w-0 flex-1">
                                            <div className="flex items-center justify-between gap-3">
                                                <p className="text-slate-200 truncate">{c.name}</p>
                                                <span className={`shrink-0 text-[10px] px-1.5 py-0.5 rounded border ${S.chip}`}>
                                                    {c.status}
                                                </span>
                                            </div>
                                            <p className="mt-0.5 text-[11px] text-slate-500 truncate">{c.details}</p>
                                        </div>
                                        <span className="hidden sm:block shrink-0 mt-0.5 text-[10px] text-slate-600">{c.latency}</span>
                                    </motion.div>
                                );
                            })}
                        </AnimatePresence>

                        {phase === "scanning" && shown < CHECKS.length && (
                            <div className="flex items-center gap-3 px-3 py-2.5 text-slate-600">
                                <CircleDashed size={15} className="animate-spin [animation-duration:2.5s]" />
                                <span>probing {CHECKS[shown]?.category.toLowerCase()} vectors…</span>
                            </div>
                        )}

                        {phase === "done" && (
                            <motion.p
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                className="pt-2 text-[11px] text-slate-500"
                                data-testid="terminal-summary"
                            >
                                scan complete in 3.82s —{" "}
                                <span className="text-red-400">{counts.FAIL} critical</span> ·{" "}
                                <span className="text-amber-400">{counts.WARN} warning</span> ·{" "}
                                <span className="text-emerald-400">{counts.PASS} passed</span>
                            </motion.p>
                        )}
                    </div>
                </div>
            </motion.div>
        </div>
    );
};
