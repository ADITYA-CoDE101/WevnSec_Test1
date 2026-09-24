import { Check } from "lucide-react";
import { Reveal, SectionHeading } from "./Reveal";
import { PRICING } from "./data";

export const Pricing = () => (
    <section id="pricing" data-testid="pricing-section" className="py-24 sm:py-32 border-t border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SectionHeading
                align="center"
                eyebrow="// pricing"
                title="Honest pricing, no security theater"
                sub="Start free. Go continuous when you ship to production. Bring in humans when the stakes demand it."
            />
            <div className="mt-16 grid md:grid-cols-3 gap-5 items-stretch max-w-6xl mx-auto">
                {PRICING.map((p, i) => (
                    <Reveal key={p.id} delay={i * 0.1} className="h-full">
                        <div
                            data-testid={`pricing-card-${p.id}`}
                            className={`relative h-full flex flex-col rounded-xl border p-7 transition-all duration-300 hover:-translate-y-1 ${
                                p.highlighted
                                    ? "border-brand/60 bg-card card-glow md:scale-[1.03]"
                                    : "border-border bg-card hover:border-brand/30"
                            }`}
                        >
                            <span
                                className={`absolute -top-3 left-6 font-mono text-[10px] uppercase tracking-[0.16em] px-2.5 py-1 rounded-full border ${
                                    p.highlighted
                                        ? "bg-brand text-[hsl(var(--primary-foreground))] border-brand"
                                        : "bg-background text-muted-foreground border-border"
                                }`}
                            >
                                {p.badge}
                            </span>
                            <h3 className="text-lg font-semibold tracking-tight text-foreground">{p.name}</h3>
                            <div className="mt-4 flex items-baseline gap-2">
                                <span className="font-mono text-4xl font-semibold tracking-tight text-foreground">{p.price}</span>
                                <span className="text-xs text-muted-foreground">{p.period}</span>
                            </div>
                            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{p.description}</p>
                            <ul className="mt-6 space-y-2.5 flex-1">
                                {p.features.map((f) => (
                                    <li key={f} className="flex items-start gap-2.5 text-sm text-muted-foreground">
                                        <Check size={15} className="mt-0.5 shrink-0 text-brand" />
                                        {f}
                                    </li>
                                ))}
                            </ul>
                            <button
                                data-testid={p.testId}
                                className={`mt-8 h-11 rounded-md text-sm font-semibold transition-all duration-200 active:scale-[0.98] ${
                                    p.highlighted
                                        ? "bg-brand text-[hsl(var(--primary-foreground))] hover:brightness-110 hover:shadow-[0_0_28px_-6px_hsl(var(--brand)/0.7)]"
                                        : "border border-border text-foreground hover:border-brand/50 hover:bg-brand/[0.06]"
                                }`}
                            >
                                {p.cta}
                            </button>
                        </div>
                    </Reveal>
                ))}
            </div>
        </div>
    </section>
);
