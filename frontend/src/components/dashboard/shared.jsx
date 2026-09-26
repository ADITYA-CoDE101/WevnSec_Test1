import { Link } from "react-router-dom";
import { Download, ExternalLink, Loader2 } from "lucide-react";
import { useState } from "react";
import { downloadReport } from "@/lib/downloadReport";

export const slug = (s) => s.replace(/[^a-z0-9]/gi, "-");
export const issueCount = (s) => s ? ["critical", "high", "medium", "low"].reduce((n,k) => n + (s.counts[k] || 0), 0) : 0;
export const ago = (iso) => {
    if (!iso) return "Not scanned";
    const minutes = Math.max(0, Math.floor((Date.now() - new Date(iso).getTime()) / 60000));
    return minutes < 1 ? "Just now" : minutes < 60 ? `${minutes}m ago` : minutes < 1440 ? `${Math.floor(minutes/60)}h ago` : `${Math.floor(minutes/1440)}d ago`;
};
export const nextScan = (iso) => iso ? new Date(iso) <= new Date() ? "Queued" : new Date(iso).toLocaleString([], {month:"short",day:"numeric",hour:"2-digit",minute:"2-digit"}) : "Paused";
export const Grade = ({grade, testId}) => <span data-testid={testId} className={`dash-grade grade-${grade?.startsWith("A") ? "a" : grade === "B" ? "b" : grade === "C" ? "c" : grade ? "f" : "none"}`}>{grade || "—"}</span>;
export const ReportActions = ({scan, prefix}) => {
    const [loading, setLoading] = useState(false);
    if (!scan) return null;
    return <>
        <Link data-testid={`${prefix}-report`} className="dash-icon-button" to={`/report/${scan.share_id}`} title="View report" aria-label={`View report for ${scan.target}`}><ExternalLink size={15}/></Link>
        <button data-testid={`${prefix}-pdf`} className="dash-icon-button" disabled={loading} title="Download PDF" aria-label={`Download PDF for ${scan.target}`} onClick={async () => {setLoading(true); try {await downloadReport(scan.share_id, scan.target);} finally {setLoading(false);}}}>{loading ? <Loader2 size={15} className="animate-spin"/> : <Download size={15}/>}</button>
    </>;
};