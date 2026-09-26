import { ShieldCheck } from "lucide-react";
import { Reveal, SectionHeading } from "./Reveal";
import { VERIFY_METHODS } from "./data";

export const Verification = () => (
    <section data-testid="verification-explainer-section" className="py-24 sm:py-32 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid lg:grid-cols-2 gap-14 items-start">
                <div>
                    <SectionHeading
                        eyebrow="// ownership verification"
                        title="We only attack what's yours"
                        sub="Active fuzzing and intrusive probes are dispatched exclusively against infrastructure you legally own. Prove it in under a minute — DNS or meta-tag, your call."
                    />
                    <Reveal delay={0.2}>
                        <div className="mt-8 flex items-start gap-3.5 rounded-xl border border-brand/25 bg-brand/[0.05] p-5">
                            <ShieldCheck size={19} className="mt-0.5 shrink-0 text-brand" />
                            <p className="text-sm leading-relaxed text-muted-foreground">
                                <span className="text-foreground font-medium">Ethical by design.</span>{" "}
                                Verification keeps WevnSec compliant with responsible-disclosure standards — and keeps
                                your deep scans legally bulletproof for SOC2 and ISO audits.
                            </p>
                        </div>
                    </Reveal>
                </div>

                <div className="space-y-5">
                    {VERIFY_METHODS.map((m, i) => (
                        <Reveal key={m.type} delay={0.1 + i * 0.12}>
                            <div className="rounded-xl border border-border bg-card overflow-hidden hover:border-brand/40 transition-colors duration-300">
                                <div className="flex flex-wrap items-center justify-between gap-2 px-5 py-4 border-b border-border">
                                    <p className="font-medium text-foreground">{m.type}</p>
                                    <span className="font-mono text-[10px] uppercase tracking-[0.14em] px-2 py-1 rounded-full border border-border text-muted-foreground">
                                        {m.tag}
                                    </span>
                                </div>
                                <pre className="p-5 font-mono text-[12px] leading-relaxed text-muted-foreground overflow-x-auto">
                                    {m.code}
                                </pre>
                                <p className="px-5 pb-4 font-mono text-[11px] text-brand/80">{m.latency}</p>
                            </div>
                        </Reveal>
                    ))}
                </div>
            </div>
        </div>
    </section>
);
