import { Reveal, SectionHeading } from "./Reveal";
import { STEPS } from "./data";

export const HowItWorks = () => (
    <section id="how-it-works" data-testid="how-it-works-section" className="py-24 sm:py-32">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SectionHeading
                eyebrow="// how it works"
                title="From URL to verdict in three moves"
                sub="Passive recon first. Verified deep scans when you prove ownership. Human pentesters when it matters."
            />
            <div className="mt-16 grid md:grid-cols-3 gap-5">
                {STEPS.map((s, i) => (
                    <Reveal key={s.step} delay={i * 0.12}>
                        <div className="group relative h-full rounded-xl border border-border bg-card p-6 sm:p-8 hover:border-brand/40 hover:-translate-y-1 hover:card-glow transition-all duration-300">
                            <div className="flex items-center justify-between">
                                <span className="font-mono text-4xl font-semibold text-brand/25 group-hover:text-brand/60 transition-colors duration-300">
                                    {s.step}
                                </span>
                                <span className="font-mono text-[10px] uppercase tracking-[0.18em] px-2.5 py-1 rounded-full border border-brand/30 text-brand bg-brand/[0.06]">
                                    {s.badge}
                                </span>
                            </div>
                            <h3 className="mt-6 text-xl sm:text-2xl font-semibold tracking-tight text-foreground">{s.title}</h3>
                            <p className="mt-1.5 text-sm text-brand/90">{s.lead}</p>
                            <p className="mt-4 text-sm leading-relaxed text-muted-foreground">{s.description}</p>
                            <pre className="mt-6 rounded-lg border border-border bg-background p-4 font-mono text-[11px] leading-relaxed text-muted-foreground overflow-x-auto whitespace-pre-wrap">
                                {s.code}
                            </pre>
                        </div>
                    </Reveal>
                ))}
            </div>
        </div>
    </section>
);
