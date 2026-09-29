import { useEffect, useRef, useState } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import { toast } from "sonner";
import { ArrowRight, Globe, Loader2 } from "lucide-react";
import { Terminal } from "./Terminal";
import { SAMPLE_DOMAINS } from "./data";
import { EASE } from "./Reveal";
import { liveScan } from "@/lib/liveScan";

const LINES = [
    { text: "You build.", accent: false },
    { text: "We find.", accent: true },
    { text: "You fix.", accent: false },
];

export const Hero = () => {
    const [input, setInput] = useState("");
    const [session, setSession] = useState({state:"example"});
    const requestRef = useRef(null);
    const [scanning, setScanning] = useState(false);
    useEffect(() => () => requestRef.current?.abort(), []);
    const { scrollY } = useScroll();
    const glowY = useTransform(scrollY, [0, 700], [0, 160]);
    const gridY = useTransform(scrollY, [0, 700], [0, 60]);

    const runScan = async (domain) => {
        if (requestRef.current) return;
        const clean = (domain || input || "")
            .trim()
            .replace(/^https?:\/\//i, "")
            .replace(/\/.*$/, "");
        if (!clean) {
            toast.error("Enter a domain to scan");
            return;
        }
        setInput(clean);
        const controller=new AbortController();requestRef.current=controller;
        setSession({state:"running",target:clean,checks:[]});
        setScanning(true);
        try {
            await liveScan(clean,{signal:controller.signal,onEvent:event => {
                if(event.type==="started")setSession(s => ({...s,target:event.target}));
                if(event.type==="check")setSession(s => ({...s,checks:[...s.checks,event.check]}));
                if(event.type==="complete"){
                    setSession({state:"complete",target:event.report.target,checks:event.report.checks,report:event.report});
                    window.dispatchEvent(new Event("wevnsec:scan-completed"));
                    toast.success("Scan saved. Your results are ready below.");
                }
            }});
        } catch (e) {
            if(e.name!=="AbortError") {setSession(s => ({...s,state:"error",error:e.message}));toast.error(e.message);}
        } finally {
            requestRef.current=null;setScanning(false);
        }
    };

    return (
        <section id="top" className="relative overflow-hidden pt-36 pb-20 sm:pt-44 sm:pb-28">
            <motion.div style={{ y: gridY }} className="absolute inset-0 dot-grid [mask-image:radial-gradient(ellipse_75%_60%_at_50%_0%,black,transparent)]" />
            <motion.div
                style={{ y: glowY }}
                className="absolute -top-40 left-1/2 -translate-x-1/2 h-[480px] w-[820px] rounded-full bg-brand/15 blur-[130px] pointer-events-none"
            />

            <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="max-w-3xl">
                    <motion.div
                        initial={{ opacity: 0, y: 14 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.6, delay: 0.05, ease: EASE }}
                        className="inline-flex items-center gap-2 rounded-full border border-brand/30 bg-brand/[0.07] px-3.5 py-1.5"
                    >
                        <span className="h-1.5 w-1.5 rounded-full bg-brand animate-pulse" />
                        <span className="font-mono text-[11px] tracking-[0.18em] uppercase text-brand">
                            v2.4 — live engine · real TLS & header probes
                        </span>
                    </motion.div>

                    <h1 className="mt-7 text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.06] text-foreground">
                        {LINES.map((l, i) => (
                            <span key={l.text} className="block overflow-hidden pb-1">
                                <motion.span
                                    className={`block ${l.accent ? "text-brand text-glow" : ""}`}
                                    initial={{ y: "112%" }}
                                    animate={{ y: 0 }}
                                    transition={{ duration: 0.95, delay: 0.15 + i * 0.14, ease: EASE }}
                                >
                                    {l.text}
                                </motion.span>
                            </span>
                        ))}
                    </h1>

                    <motion.p
                        initial={{ opacity: 0, y: 18 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.7, delay: 0.62, ease: EASE }}
                        className="mt-6 text-lg leading-relaxed text-muted-foreground max-w-xl"
                    >
                        Check your website’s TLS, security headers, and public configuration.
                        Understand each finding, then take the next step toward a safer site.
                    </motion.p>

                    <motion.form
                        initial={{ opacity: 0, y: 18 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.7, delay: 0.74, ease: EASE }}
                        onSubmit={(e) => { e.preventDefault(); runScan(); }}
                        className="mt-9 flex flex-col sm:flex-row gap-3 max-w-xl"
                    >
                        <div className="flex-1 flex items-center gap-2 rounded-md border border-border bg-card px-3.5 h-12 focus-within:border-brand/60 focus-within:shadow-[0_0_0_3px_hsl(var(--brand)/0.15)] transition-all duration-200">
                            <Globe size={16} className="text-muted-foreground shrink-0" />
                            <span className="font-mono text-sm text-muted-foreground select-none">https://</span>
                            <input
                                data-testid="hero-url-input"
                                value={input}
                                disabled={scanning}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder="yourapp.com"
                                spellCheck={false}
                                autoComplete="off"
                                className="w-full bg-transparent font-mono text-sm text-foreground placeholder:text-muted-foreground/50 outline-none"
                                aria-label="Website URL to scan"
                            />
                        </div>
                        <button
                            type="submit"
                            disabled={scanning}
                            data-testid="hero-run-scan-button"
                            className="group h-12 px-6 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-sm font-semibold flex items-center justify-center gap-2 hover:brightness-110 hover:shadow-[0_0_32px_-6px_hsl(var(--brand)/0.7)] active:scale-[0.98] disabled:opacity-70 transition-all duration-200"
                        >
                            {scanning ? (
                                <>
                                    <Loader2 size={15} className="animate-spin" />
                                    Scanning live…
                                </>
                            ) : (
                                <>
                                    Run instant scan
                                    <ArrowRight size={15} className="transition-transform duration-200 group-hover:translate-x-0.5" />
                                </>
                            )}
                        </button>
                    </motion.form>

                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ duration: 0.7, delay: 0.9 }}
                        className="mt-4 flex flex-wrap items-center gap-2"
                    >
                        <span className="font-mono text-[11px] text-muted-foreground mr-1">scan for real:</span>
                        {SAMPLE_DOMAINS.map((d) => (
                            <button
                                key={d}
                                onClick={() => runScan(d)}
                                disabled={scanning}
                                data-testid={`sample-domain-${d.replace(/[^a-z0-9]/gi, "-")}`}
                                className="font-mono text-[11px] px-2.5 py-1 rounded-full border border-border text-muted-foreground hover:text-brand hover:border-brand/50 hover:bg-brand/[0.06] transition-colors duration-200"
                            >
                                {d}
                            </button>
                        ))}
                    </motion.div>
                </div>

                <div className="mt-16 max-w-3xl lg:max-w-4xl">
                    <Terminal session={session} />
                </div>
            </div>
        </section>
    );
};
