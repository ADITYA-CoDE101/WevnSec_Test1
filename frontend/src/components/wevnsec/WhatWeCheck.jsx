import { Reveal, SectionHeading } from "./Reveal";
import { GRID } from "./data";

export const WhatWeCheck = () => (
    <section data-testid="vulnerability-category-grid" className="py-24 sm:py-32 border-t border-border bg-card/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <SectionHeading
                eyebrow="// what we check"
                title="27 vulnerability classes, zero noise"
                sub="Every scan maps to the OWASP Top 10 and beyond — with false positives filtered before they ever reach your inbox."
            />
            <div className="mt-16 grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {GRID.map((g, i) => (
                    <Reveal key={g.category} delay={(i % 3) * 0.1}>
                        <div className="group h-full rounded-xl border border-border bg-card p-6 hover:border-brand/40 hover:-translate-y-1 transition-all duration-300">
                            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-brand">{g.category}</p>
                            <h3 className="mt-3 text-lg sm:text-xl font-medium tracking-tight text-foreground">{g.title}</h3>
                            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{g.description}</p>
                            <ul className="mt-5 space-y-2">
                                {g.items.map((it) => (
                                    <li key={it} className="flex items-center gap-2.5 text-xs text-muted-foreground">
                                        <span className="h-px w-3 bg-brand/60 group-hover:w-5 transition-all duration-300" />
                                        <span className="font-mono">{it}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </Reveal>
                ))}
            </div>
        </div>
    </section>
);
