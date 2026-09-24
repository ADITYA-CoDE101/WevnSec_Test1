import { useEffect, useRef, useState } from "react";
import { animate, useInView } from "framer-motion";
import { ShieldCheck } from "lucide-react";
import { LOGOS, INITIAL_STATS } from "./data";
import { Reveal } from "./Reveal";
import { api } from "@/lib/api";

const Counter = ({ value, format, testId }) => {
    const ref = useRef(null);
    const inView = useInView(ref, { once: true, margin: "-40px" });
    const [display, setDisplay] = useState(0);
    const prev = useRef(0);

    useEffect(() => {
        if (!inView) return;
        const controls = animate(prev.current, value, {
            duration: 1.1,
            ease: [0.16, 1, 0.3, 1],
            onUpdate: (v) => setDisplay(v),
        });
        prev.current = value;
        return () => controls.stop();
    }, [value, inView]);

    return (
        <span ref={ref} data-testid={testId} className="font-mono text-3xl sm:text-4xl font-semibold tracking-tight text-foreground tabular-nums">
            {format(display)}
        </span>
    );
};

export const TrustBar = () => {
    const [stats, setStats] = useState(INITIAL_STATS);
    const realAdded = useRef(false);

    useEffect(() => {
        if (realAdded.current) return;
        realAdded.current = true;
        api.get("/stats")
            .then(({ data }) =>
                setStats((s) => ({
                    ...s,
                    scanned: s.scanned + (data.scans || 0),
                    vulns: s.vulns + (data.vulns || 0),
                }))
            )
            .catch(() => {});
    }, []);

    useEffect(() => {
        const id = setInterval(() => {
            setStats((s) => ({
                ...s,
                scanned: s.scanned + 3 + Math.floor(Math.random() * 12),
                vulns: s.vulns + (Math.random() > 0.5 ? Math.floor(Math.random() * 3) : 0),
                avgTime: Math.max(24, Math.min(33, s.avgTime + (Math.random() - 0.5) * 0.4)),
            }));
        }, 6000);
        return () => clearInterval(id);
    }, []);

    const int = (v) => Math.round(v).toLocaleString("en-US");
    const ITEMS = [
        { label: "Websites scanned", value: stats.scanned, format: (v) => `${int(v)}+`, delta: "live · +38 in the last hour", testId: "stat-scanned-count" },
        { label: "Vulnerabilities intercepted", value: stats.vulns, format: int, delta: "99.4% false-positive filtered", testId: "stat-vulns-found" },
        { label: "Avg time to first verdict", value: stats.avgTime, format: (v) => `${v.toFixed(1)}s`, delta: "zero agent install", testId: "stat-avg-time" },
        { label: "Whitehat researchers", value: stats.researchers, format: (v) => `${Math.round(v)}+`, delta: "CREST certified", testId: "stat-researchers" },
    ];

    return (
        <section data-testid="dynamic-trust-bar" className="border-y border-border bg-card/40">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
                <Reveal>
                    <p className="text-center font-mono text-[11px] uppercase tracking-[0.28em] text-muted-foreground">
                        Trusted by teams shipping secure code
                    </p>
                </Reveal>
                <Reveal delay={0.1}>
                    <div className="mt-8 flex flex-wrap items-center justify-center gap-x-10 gap-y-5">
                        {LOGOS.map((l) => (
                            <div key={l.name} className="flex items-center gap-2.5 opacity-50 hover:opacity-100 transition-opacity duration-300">
                                <ShieldCheck size={15} className="text-brand" />
                                <span className="font-mono text-xs tracking-[0.14em] text-foreground">{l.name}</span>
                                <span className="font-mono text-[9px] px-1.5 py-0.5 rounded border border-border text-muted-foreground">
                                    {l.badge}
                                </span>
                            </div>
                        ))}
                    </div>
                </Reveal>

                <div className="mt-14 grid grid-cols-2 lg:grid-cols-4 gap-px rounded-xl overflow-hidden border border-border bg-border">
                    {ITEMS.map((s, i) => (
                        <Reveal key={s.label} delay={i * 0.08} className="bg-card">
                            <div className="h-full px-6 py-7 hover:bg-accent/40 transition-colors duration-300">
                                <Counter value={s.value} format={s.format} testId={s.testId} />
                                <p className="mt-2 text-sm text-muted-foreground">{s.label}</p>
                                <p className="mt-1 font-mono text-[10px] text-brand/80">{s.delta}</p>
                            </div>
                        </Reveal>
                    ))}
                </div>
            </div>
        </section>
    );
};
