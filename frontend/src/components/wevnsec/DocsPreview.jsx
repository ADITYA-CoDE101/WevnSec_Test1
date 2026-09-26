import { useState } from "react";
import { Check, Copy, ArrowUpRight } from "lucide-react";
import { Reveal, SectionHeading } from "./Reveal";
import { DOCS_TABS } from "./data";

export const DocsPreview = () => {
    const [active, setActive] = useState(DOCS_TABS[0].id);
    const [copied, setCopied] = useState(false);
    const tab = DOCS_TABS.find((t) => t.id === active);

    const copy = async () => {
        try {
            await navigator.clipboard.writeText(tab.code);
            setCopied(true);
            setTimeout(() => setCopied(false), 1600);
        } catch (e) { /* clipboard unavailable */ }
    };

    return (
        <section id="docs" data-testid="docs-preview-section" className="py-24 sm:py-32 border-t border-border bg-card/30">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="grid lg:grid-cols-5 gap-14 items-center">
                    <div className="lg:col-span-2">
                        <SectionHeading
                            eyebrow="// docs"
                            title="Built for developers, not compliance checklists"
                            sub="A real API, an official GitHub Action, typed SDKs and signed webhooks. Wire WevnSec into your pipeline in an afternoon."
                        />
                        <Reveal delay={0.2}>
                            <a
                                href="#docs"
                                onClick={(e) => e.preventDefault()}
                                data-testid="docs-read-more-link"
                                className="mt-8 inline-flex items-center gap-1.5 text-sm font-medium text-brand hover:gap-2.5 transition-all duration-200"
                            >
                                Read the docs
                                <ArrowUpRight size={15} />
                            </a>
                        </Reveal>
                    </div>

                    <Reveal delay={0.1} className="lg:col-span-3">
                        <div className="rounded-xl border border-border terminal-shell overflow-hidden card-glow">
                            <div className="flex items-center justify-between border-b border-white/10 px-3">
                                <div className="flex overflow-x-auto">
                                    {DOCS_TABS.map((t) => (
                                        <button
                                            key={t.id}
                                            onClick={() => setActive(t.id)}
                                            data-testid={`docs-tab-${t.id}`}
                                            className={`whitespace-nowrap px-3.5 py-3 font-mono text-[11px] border-b-2 transition-colors duration-200 ${
                                                active === t.id
                                                    ? "text-brand border-brand"
                                                    : "text-slate-500 border-transparent hover:text-slate-300"
                                            }`}
                                        >
                                            {t.label}
                                        </button>
                                    ))}
                                </div>
                                <button
                                    onClick={copy}
                                    data-testid="docs-copy-button"
                                    aria-label="Copy code snippet"
                                    className="ml-2 shrink-0 h-8 w-8 rounded-md flex items-center justify-center text-slate-400 hover:text-brand hover:bg-brand/10 transition-colors duration-200"
                                >
                                    {copied ? <Check size={14} className="text-emerald-400" /> : <Copy size={14} />}
                                </button>
                            </div>
                            <pre className="p-5 font-mono text-[12px] leading-relaxed text-slate-300 overflow-x-auto min-h-[300px]">
                                {tab.code}
                            </pre>
                        </div>
                    </Reveal>
                </div>
            </div>
        </section>
    );
};
