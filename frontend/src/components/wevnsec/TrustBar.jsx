import { useEffect } from "react";
import { Link } from "react-router-dom";
import useSWR from "swr";
import { RefreshCw, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import "./live-scan.css";

export const TrustBar = () => {
    const {data,error,isValidating,mutate}=useSWR("/stats",url => api.get(url).then(r => r.data),{refreshInterval:15000,refreshWhenHidden:false,revalidateOnFocus:true});
    useEffect(() => {const refresh=() => mutate();window.addEventListener("wevnsec:scan-completed",refresh);return () => window.removeEventListener("wevnsec:scan-completed",refresh);},[mutate]);
    const items=[
        ["scans","Completed scans","Saved assessments, including repeat scans.","stat-scanned-count"],
        ["findings","Recorded findings","Failed checks + warnings; repeats included.","stat-vulns-found"],
        ["checks_supported","Automated check types","Implemented checks, not unique vulnerabilities.","stat-checks-count"],
        ["docs_count","Published reference articles","Scanner guidance + reference-only topics.","stat-docs-count"],
    ];
    return <section data-testid="dynamic-trust-bar" className="border-y border-border bg-card/40"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="live-stats-heading"><div><h2 data-testid="stats-heading">Real scans. A growing security reference.</h2><p data-testid="stats-description">Our activity so far, directly from saved results.</p></div><div className="stats-refresh"><span data-testid="stats-updated">{error ? "Refresh unavailable" : data ? `Updated ${new Date(data.updated_at).toLocaleTimeString([], {hour:"2-digit",minute:"2-digit"})}` : "Loading live totals…"}</span><button onClick={() => mutate()} title="Refresh totals" aria-label="Refresh totals" disabled={isValidating} data-testid="stats-refresh-button"><RefreshCw size={14} className={isValidating ? "animate-spin" : ""}/></button></div></div>
        <div className="live-stats-grid">{items.map(([key,label,note,id]) => <div className="live-stat" key={key}><strong data-testid={id}>{data ? Number(data[key]).toLocaleString() : "—"}</strong><h3 data-testid={`${id}-label`}>{label}</h3><p data-testid={`${id}-note`}>{note}</p></div>)}</div>
        <div className="live-stats-note"><p data-testid="stats-counting-note">{error ? (data ? "Showing the last received totals. Automatic updates will resume when available." : "Totals are temporarily unavailable. No estimated numbers are shown.") : "Counts update after scans finish. Findings are observations, not confirmed exploits or fixes."}</p><Link to="/docs" data-testid="stats-docs-link" className="inline-flex items-center gap-2"><BookOpen size={13}/>Explore the reference library</Link></div>
    </div></section>;
};