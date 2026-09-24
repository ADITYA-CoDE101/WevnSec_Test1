import { motion } from "framer-motion";
import { Reveal, EASE } from "@/components/wevnsec/Reveal";

const ENTRIES = [
    {
        version: "v2.4.0",
        date: "2026-07-20",
        tag: "LIVE ENGINE",
        tagCls: "text-brand border-brand/40 bg-brand/10",
        title: "Real-time scan engine goes live",
        items: [
            "Hero scans now run live TLS, header, CORS and .env probes against real domains",
            "Shareable report pages with severity scores and remediation snippets",
            "SPA catch-all detection to kill false positives on exposed-file probes",
        ],
    },
    {
        version: "v2.3.0",
        date: "2026-06-28",
        tag: "NEW",
        tagCls: "text-emerald-400 border-emerald-400/40 bg-emerald-400/10",
        title: "Dashboards, watchlists & drift alerts",
        items: [
            "Save domains to a personal dashboard and rescan on demand",
            "Alerts when a rescan finds more vulnerabilities than the previous run",
            "Scan history with grade tracking per target",
        ],
    },
    {
        version: "v2.2.1",
        date: "2026-06-02",
        tag: "IMPROVED",
        tagCls: "text-amber-400 border-amber-400/40 bg-amber-400/10",
        title: "False-positive filtering pass",
        items: [
            "99.4% of noisy findings now auto-triaged before reaching your inbox",
            "CORS origin-reflection checks no longer flag credential-less wildcards",
        ],
    },
    {
        version: "v2.1.0",
        date: "2026-05-11",
        tag: "NEW",
        tagCls: "text-emerald-400 border-emerald-400/40 bg-emerald-400/10",
        title: "GitHub Action & CI gate",
        items: [
            "wevnsec/scan-action@v2 fails builds on high or critical findings",
            "Signed webhooks for scan.completed events",
        ],
    },
    {
        version: "v2.0.0",
        date: "2026-04-01",
        tag: "MAJOR",
        tagCls: "text-brand border-brand/40 bg-brand/10",
        title: "WevnSec 2.0",
        items: [
            "Verified deep scans behind DNS TXT / meta-tag ownership checks",
            "Human pentest tier with CREST & OSCP vetted researchers",
            "Public vulnerability + mitigation library",
        ],
    },
];

export default function Changelog() {
    return (
        <main className="pt-32 pb-28 min-h-screen" data-testid="changelog-page">
            <div className="max-w-3xl mx-auto px-4 sm:px-6">
                <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE }}>
                    <p className="font-mono text-[11px] uppercase tracking-[0.25em] text-brand">// changelog</p>
                    <h1 className="mt-4 text-3xl sm:text-4xl font-semibold tracking-tight text-foreground">
                        Shipped, not promised
                    </h1>
                    <p className="mt-4 text-base text-muted-foreground leading-relaxed">
                        Every engine improvement, check addition and false-positive fix — in reverse chronological order.
                    </p>
                </motion.div>

                <div className="mt-14 relative">
                    <div className="absolute left-[7px] top-2 bottom-2 w-px bg-border" />
                    <div className="space-y-12">
                        {ENTRIES.map((e, i) => (
                            <Reveal key={e.version} delay={i * 0.06}>
                                <div className="relative pl-10">
                                    <span className="absolute left-0 top-1.5 h-[15px] w-[15px] rounded-full border-2 border-brand bg-background" />
                                    <div className="flex flex-wrap items-center gap-3">
                                        <span className="font-mono text-sm font-semibold text-foreground" data-testid={`changelog-version-${e.version.replace(/\./g, "-")}`}>
                                            {e.version}
                                        </span>
                                        <span className={`font-mono text-[10px] uppercase tracking-[0.16em] px-2 py-0.5 rounded border ${e.tagCls}`}>
                                            {e.tag}
                                        </span>
                                        <span className="font-mono text-[11px] text-muted-foreground">{e.date}</span>
                                    </div>
                                    <h2 className="mt-3 text-xl font-semibold tracking-tight text-foreground">{e.title}</h2>
                                    <ul className="mt-3 space-y-2">
                                        {e.items.map((it) => (
                                            <li key={it} className="flex items-start gap-2.5 text-sm text-muted-foreground leading-relaxed">
                                                <span className="mt-2.5 h-px w-3 shrink-0 bg-brand/60" />
                                                {it}
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            </Reveal>
                        ))}
                    </div>
                </div>
            </div>
        </main>
    );
}
