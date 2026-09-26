import { useState } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, AlertTriangle, XCircle, Loader2, ShieldCheck, ArrowUpRight, TerminalSquare } from "lucide-react";
import "./live-scan.css";

const EXAMPLE = [
    {id:"TLS-01",name:"TLS certificate & protocol",status:"pass",detail:"Example: TLS 1.3 negotiated; certificate within its validity period."},
    {id:"HDR-conten",name:"Content Security Policy",status:"fail",detail:"Example: no Content-Security-Policy header on the root response."},
    {id:"CK-01",name:"Cookie security flags",status:"pass",detail:"Example: no cookies set on the entry route."},
    {id:"HDR-SRV",name:"Server fingerprint disclosure",status:"warn",detail:"Example: a software version is exposed in a response header."},
];
const META = {pass:[CheckCircle2,"Passed"],fail:[XCircle,"Findings"],warn:[AlertTriangle,"Warnings"]};

export const Terminal = ({session}) => {
    const [tab,setTab]=useState("all");
    const state=session?.state || "example", example=state==="example", running=state==="running";
    const checks=example ? EXAMPLE : session.checks || [];
    const counts=Object.fromEntries(["pass","fail","warn"].map(status => [status,checks.filter(c => c.status===status).length]));
    const rows=checks.filter(c => tab==="all" || c.status===tab);
    return <div className="live-console" data-testid="scan-console">
        <header className="live-console-header"><span data-testid="console-title"><TerminalSquare size={15}/>WEVNSEC / SCAN ACTIVITY</span><span className={`console-state state-${state}`} data-testid="terminal-status-pill">{running && <Loader2 size={12} className="animate-spin"/>}{example ? "EXAMPLE PREVIEW" : running ? "LIVE SCAN" : state==="complete" ? "COMPLETE" : "SCAN INTERRUPTED"}</span></header>
        <div className="console-overview"><div><p data-testid="console-target-label">{example ? "ILLUSTRATIVE RESULTS · NOT A LIVE SCAN" : "TARGET"}</p><strong data-testid="console-target">{example ? "example.com" : session.target}</strong><span data-testid="console-description">{example ? "A sample of the checks in an Instant Scan." : running ? "Results appear as real probes finish." : state==="complete" ? `${session.report.checks.length} checks saved · ${(session.report.duration_ms/1000).toFixed(1)}s` : session.error}</span></div><div className="console-check-total" data-testid="console-returned-count"><ShieldCheck size={22}/><b>{checks.length}</b><small>{example ? "sample checks" : "checks returned"}</small></div></div>
        <div className="console-tabs" role="tablist" aria-label="Scan results">{[["all","All checks",checks.length],["fail","Findings",counts.fail],["warn","Warnings",counts.warn],["pass","Passed",counts.pass]].map(([id,label,count]) => <button key={id} role="tab" aria-selected={tab===id} onClick={() => setTab(id)} className={tab===id ? "active" : ""} data-testid={`terminal-tab-${id}`}><span>{label}</span><b>{count}</b></button>)}</div>
        <div className="console-results" data-testid="console-results" data-lenis-prevent tabIndex={0} aria-label="Scan check results">
            {rows.map((c,i) => {const [Icon]=META[c.status] || META.warn; return <div key={`${c.id}-${i}`} className={`console-check check-${c.status}`} data-testid={`terminal-check-${i}`}><Icon size={16}/><div><strong data-testid={`terminal-check-title-${i}`}>{c.name}</strong><p data-testid={`terminal-check-detail-${i}`}>{c.detail}</p></div><span data-testid={`terminal-check-status-${i}`}>{c.status.toUpperCase()}</span></div>;})}
            {!rows.length && <div className="console-empty" data-testid="console-empty">{running ? <><Loader2 className="animate-spin" size={20}/>Waiting for completed checks…</> : "No checks in this category."}</div>}
        </div>
        <footer className="console-footer"><span data-testid="terminal-summary">{example ? "Example only. Your scan produces its own results." : running ? "Testing the public root endpoint" : state==="complete" ? "Findings are observations, not proof of exploitation." : "No completed report was saved."}</span>{state==="complete" ? <Link to={`/report/${session.report.share_id}`} data-testid="console-view-report">Full report<ArrowUpRight size={14}/></Link> : <Link to="/docs" data-testid="console-docs-link">Check reference<ArrowUpRight size={14}/></Link>}</footer>
    </div>;
};