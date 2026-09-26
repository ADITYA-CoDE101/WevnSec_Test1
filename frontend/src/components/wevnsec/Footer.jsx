import { Github, Twitter, Linkedin } from "lucide-react";
import { LogoMark } from "./Reveal";

const COLS = [
    { title: "Product", links: ["Instant Scan", "Verified Scan", "Pentest", "Changelog"] },
    { title: "Docs", links: ["Quickstart", "API Reference", "GitHub Action", "Vulnerability Library"] },
    { title: "Company", links: ["About", "Blog", "Careers", "Contact"] },
    { title: "Legal", links: ["Privacy", "Terms", "Responsible Disclosure", "DPA"] },
];

export const Footer = () => (
    <footer id="footer" data-testid="wevnsec-footer" className="border-t border-border bg-card/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
            <div className="grid grid-cols-2 md:grid-cols-6 gap-10">
                <div className="col-span-2">
                    <div className="flex items-center gap-2.5">
                        <LogoMark size={26} />
                        <span className="text-[17px] font-semibold tracking-tight text-foreground">
                            wevn<span className="text-brand">sec</span>
                        </span>
                    </div>
                    <p className="mt-4 text-sm leading-relaxed text-muted-foreground max-w-xs">
                        Website audits and pentests, built for developers. You build, we find, you fix.
                    </p>
                    <div
                        className="mt-6 inline-flex items-center gap-2 rounded-full border border-border px-3 py-1.5"
                        data-testid="footer-status"
                    >
                        <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        <span className="font-mono text-[11px] text-muted-foreground">All systems operational</span>
                    </div>
                    <div className="mt-6 flex items-center gap-2">
                        {[
                            { icon: Github, label: "GitHub", id: "github" },
                            { icon: Twitter, label: "Twitter", id: "twitter" },
                            { icon: Linkedin, label: "LinkedIn", id: "linkedin" },
                        ].map((s) => (
                            <a
                                key={s.id}
                                href="#footer"
                                onClick={(e) => e.preventDefault()}
                                aria-label={s.label}
                                data-testid={`footer-social-${s.id}`}
                                className="h-9 w-9 rounded-md border border-border flex items-center justify-center text-muted-foreground hover:text-brand hover:border-brand/50 transition-colors duration-200"
                            >
                                <s.icon size={15} />
                            </a>
                        ))}
                    </div>
                </div>

                {COLS.map((c) => (
                    <div key={c.title}>
                        <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-muted-foreground">{c.title}</p>
                        <ul className="mt-4 space-y-2.5">
                            {c.links.map((l) => (
                                <li key={l}>
                                    <a
                                        href="#footer"
                                        onClick={(e) => e.preventDefault()}
                                        data-testid={`footer-link-${l.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                                        className="text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                                    >
                                        {l}
                                    </a>
                                </li>
                            ))}
                        </ul>
                    </div>
                ))}
            </div>

            <div className="mt-14 pt-7 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-3">
                <p className="font-mono text-[11px] text-muted-foreground">© 2026 WevnSec, Inc. All rights reserved.</p>
                <p className="font-mono text-[11px] text-muted-foreground/60">
                    hack responsibly · <span className="text-brand/70">wn_live_••••••••</span>
                </p>
            </div>
        </div>
    </footer>
);
