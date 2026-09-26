import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { toast } from "sonner";
import {
    CheckCircle2, AlertTriangle, XCircle, Copy, Check, RefreshCw,
    BookmarkPlus, ArrowLeft, Clock3, Zap, Download, Loader2,
} from "lucide-react";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { EASE } from "@/components/wevnsec/Reveal";
import { downloadReport } from "@/lib/downloadReport";

const STATUS_META = {
    pass: { icon: CheckCircle2, cls: "text-emerald-400", chip: "text-emerald-400 border-emerald-400/30 bg-emerald-400/10", label: "PASS" },
    warn: { icon: AlertTriangle, cls: "text-amber-400", chip: "text-amber-400 border-amber-400/30 bg-amber-400/10", label: "WARN" },
    fail: { icon: XCircle, cls: "text-red-400", chip: "text-red-400 border-red-400/30 bg-red-400/10", label: "FAIL" },
};

const SEV_RANK = { critical: 0, high: 1, medium: 2, low: 3, none: 4 };
const STATUS_RANK = { fail: 0, warn: 1, pass: 2 };

const gradeColor = (g) =>
    g?.startsWith("A") ? "text-emerald-400" : g === "B" ? "text-brand" : g === "C" ? "text-amber-400" : "text-red-400";
const ringColor = (score) =>
    score >= 85 ? "#34D399" : score >= 70 ? "#38BDF8" : score >= 55 ? "#FBBF24" : "#F87171";

const ScoreRing = ({ score, grade }) => {
    const r = 52;
    const c = 2 * Math.PI * r;
    return (
        <div className="relative h-32 w-32" data-testid="report-grade">
            <svg width="128" height="128" viewBox="0 0 128 128" className="-rotate-90">
                <circle cx="64" cy="64" r={r} fill="none" strokeWidth="7" className="stroke-border" />
                <motion.circle
                    cx="64" cy="64" r={r} fill="none"
                    stroke={ringColor(score)}
                    strokeWidth="7"
                    strokeLinecap="round"
                    strokeDasharray={c}
                    initial={{ strokeDashoffset: c }}
                    animate={{ strokeDashoffset: c * (1 - score / 100) }}
                    transition={{ duration: 1.3, ease: EASE }}
                />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className={`font-mono text-3xl font-semibold ${gradeColor(grade)}`}>{grade}</span>
                <span className="font-mono text-[11px] text-muted-foreground">{score}/100</span>
            </div>
        </div>
    );
};

export default function Report() {
    const { id } = useParams();
    const navigate = useNavigate();
    const { user } = useAuth();
    const [report, setReport] = useState(null);
    const [error, setError] = useState(null);
    const [copied, setCopied] = useState(false);
    const [rescanning, setRescanning] = useState(false);
    const [saved, setSaved] = useState(false);
    const [downloading, setDownloading] = useState(false);

    useEffect(() => {
        setReport(null);
        setError(null);
        api.get(`/scan/${id}`)
            .then((r) => setReport(r.data))
            .catch((e) => setError(formatApiErrorDetail(e.response?.data?.detail)));
    }, [id]);

    const copyLink = async () => {
        try {
            await navigator.clipboard.writeText(window.location.href);
            setCopied(true);
            toast.success("Report link copied — anyone with it can view this scan");
            setTimeout(() => setCopied(false), 1600);
        } catch (e) { /* clipboard unavailable */ }
    };

    const rescan = async () => {
        if (!report || rescanning) return;
        setRescanning(true);
        try {
            const { data } = await api.post("/scan", { target: report.target });
            navigate(`/report/${data.share_id}`);
        } catch (e) {
            toast.error(formatApiErrorDetail(e.response?.data?.detail));
        } finally {
            setRescanning(false);
        }
    };

    const saveDomain = async () => {
        if (!user) {
            toast.error("Sign in to save domains to your dashboard");
            navigate("/signin");
            return;
        }
        try {
            await api.post("/domains", { domain: report.target });
            setSaved(true);
            toast.success(`${report.target} saved to your dashboard`);
        } catch (e) {
            toast.error(formatApiErrorDetail(e.response?.data?.detail));
        }
    };

    if (error) {
        return (
            <main className="pt-36 pb-32 min-h-screen">
                <div className="max-w-2xl mx-auto px-4 text-center">
                    <XCircle size={40} className="mx-auto text-red-400" />
                    <h1 className="mt-6 text-2xl font-semibold tracking-tight">Report unavailable</h1>
                    <p className="mt-3 text-muted-foreground">{error}</p>
                    <Link to="/" className="mt-8 inline-flex items-center gap-2 text-brand text-sm font-medium" data-testid="report-back-link">
                        <ArrowLeft size={15} /> Run a new scan
                    </Link>
                </div>
            </main>
        );
    }

    if (!report) {
        return (
            <main className="pt-36 pb-32 min-h-screen">
                <div className="max-w-4xl mx-auto px-4 animate-pulse space-y-6">
                    <div className="h-8 w-64 rounded bg-accent" />
                    <div className="h-32 w-32 rounded-full bg-accent" />
                    <div className="space-y-3">
                        {[...Array(6)].map((_, i) => <div key={i} className="h-20 rounded-xl bg-accent" />)}
                    </div>
                </div>
            </main>
        );
    }

    const sorted = [...report.checks].sort(
        (a, b) => STATUS_RANK[a.status] - STATUS_RANK[b.status] || SEV_RANK[a.severity] - SEV_RANK[b.severity]
    );
    const { counts } = report;

    return (
        <main className="pt-28 pb-28 min-h-screen" data-testid="report-page">
            <div className="max-w-4xl mx-auto px-4 sm:px-6">
                <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease: EASE }}>
                    <Link to="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors" data-testid="report-back-link">
                        <ArrowLeft size={14} /> new scan
                    </Link>

                    <div className="mt-6 flex flex-col sm:flex-row sm:items-center gap-8 rounded-xl border border-border bg-card p-6 sm:p-8">
                        <ScoreRing score={report.score} grade={report.grade} />
                        <div className="flex-1 min-w-0">
                            <p className="font-mono text-[11px] uppercase tracking-[0.22em] text-brand">scan report</p>
                            <h1 className="mt-2 font-mono text-xl sm:text-2xl font-semibold tracking-tight text-foreground break-all" data-testid="report-target">
                                {report.target}
                            </h1>
                            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[11px] text-muted-foreground">
                                <span className="flex items-center gap-1.5"><Clock3 size={12} /> {new Date(report.created_at).toLocaleString()}</span>
                                <span className="flex items-center gap-1.5"><Zap size={12} /> {(report.duration_ms / 1000).toFixed(1)}s · {report.checks.length} checks</span>
                            </div>
                            <div className="mt-4 flex flex-wrap gap-2">
                                <span className="font-mono text-[11px] px-2 py-1 rounded border border-red-400/30 bg-red-400/10 text-red-400" data-testid="report-count-fail">
                                    {counts.critical + counts.high + counts.medium + counts.low} failed
                                </span>
                                <span className="font-mono text-[11px] px-2 py-1 rounded border border-amber-400/30 bg-amber-400/10 text-amber-400">
                                    {counts.warning} warnings
                                </span>
                                <span className="font-mono text-[11px] px-2 py-1 rounded border border-emerald-400/30 bg-emerald-400/10 text-emerald-400">
                                    {counts.passed} passed
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="mt-5 flex flex-wrap gap-2.5">
                        <button data-testid="download-report-pdf" disabled={downloading} onClick={async () => { setDownloading(true); try { await downloadReport(report.share_id, report.target); } finally { setDownloading(false); } }} className="flex items-center gap-2 h-10 px-4 rounded-md border border-brand/40 text-sm text-brand hover:bg-brand/10 disabled:opacity-60 transition-colors">
                            {downloading ? <Loader2 size={15} className="animate-spin" /> : <Download size={15} />} {downloading ? "Preparing PDF…" : "Download PDF"}
                        </button>
                        <button
                            onClick={copyLink}
                            data-testid="share-copy-button"
                            className="flex items-center gap-2 h-10 px-4 rounded-md border border-border text-sm text-foreground hover:border-brand/50 hover:bg-brand/[0.06] transition-colors duration-200"
                        >
                            {copied ? <Check size={15} className="text-emerald-400" /> : <Copy size={15} />}
                            {copied ? "Copied" : "Copy share link"}
                        </button>
                        <button
                            onClick={rescan}
                            disabled={rescanning}
                            data-testid="rescan-button"
                            className="flex items-center gap-2 h-10 px-4 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-sm font-semibold hover:brightness-110 disabled:opacity-70 transition-all duration-200"
                        >
                            <RefreshCw size={15} className={rescanning ? "animate-spin" : ""} />
                            {rescanning ? "Rescanning…" : "Rescan now"}
                        </button>
                        <button
                            onClick={saveDomain}
                            disabled={saved}
                            data-testid="save-domain-button"
                            className="flex items-center gap-2 h-10 px-4 rounded-md border border-border text-sm text-foreground hover:border-brand/50 hover:bg-brand/[0.06] disabled:opacity-60 transition-colors duration-200"
                        >
                            <BookmarkPlus size={15} />
                            {saved ? "Saved" : "Save to dashboard"}
                        </button>
                    </div>
                </motion.div>

                <div className="mt-10 space-y-3">
                    {sorted.map((c, i) => {
                        const S = STATUS_META[c.status];
                        return (
                            <motion.div
                                key={c.id + i}
                                data-testid={`report-check-${c.id.toLowerCase()}`}
                                initial={{ opacity: 0, y: 16 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.5, delay: 0.08 + i * 0.045, ease: EASE }}
                                className={`rounded-xl border bg-card p-5 ${
                                    c.status === "fail" ? "border-red-400/25" : c.status === "warn" ? "border-amber-400/20" : "border-border"
                                }`}
                            >
                                <div className="flex items-start gap-3.5">
                                    <S.icon size={18} className={`mt-0.5 shrink-0 ${S.cls}`} />
                                    <div className="min-w-0 flex-1">
                                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
                                            <p className="font-medium text-foreground">{c.name}</p>
                                            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted-foreground">{c.category}</span>
                                            <span className={`ml-auto font-mono text-[10px] px-1.5 py-0.5 rounded border ${S.chip}`}>{S.label}</span>
                                            {c.status === "fail" && (
                                                <span className="font-mono text-[10px] uppercase px-1.5 py-0.5 rounded border border-red-400/30 text-red-400/90">
                                                    {c.severity}
                                                </span>
                                            )}
                                        </div>
                                        <p className="mt-2 text-sm leading-relaxed text-muted-foreground break-words">{c.detail}</p>
                                        {c.fix && (
                                            <div className="mt-3.5 rounded-lg border border-border bg-background overflow-hidden">
                                                <p className="px-3.5 py-2 border-b border-border font-mono text-[10px] uppercase tracking-[0.18em] text-brand">
                                                    $ remediation
                                                </p>
                                                <pre className="px-3.5 py-3 font-mono text-[12px] leading-relaxed text-muted-foreground whitespace-pre-wrap break-words">
                                                    {c.fix}
                                                </pre>
                                            </div>
                                        )}
                                    </div>
                                    <span className="hidden sm:block shrink-0 mt-1 font-mono text-[10px] text-muted-foreground/60">{c.latency_ms}ms</span>
                                </div>
                            </motion.div>
                        );
                    })}
                </div>
            </div>
        </main>
    );
}
