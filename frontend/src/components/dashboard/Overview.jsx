import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Globe2, ShieldCheck, TriangleAlert, Bell, ArrowUpRight, Activity, ScanLine } from "lucide-react";
import { ResponsiveContainer as RechartsContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from "recharts";
import { issueCount } from "./shared";

const tooltipStyle = {background:"hsl(var(--popover))",border:"1px solid hsl(var(--border))",borderRadius:6,color:"hsl(var(--foreground))",fontSize:12};
const ResponsiveContainer = (props) => <RechartsContainer initialDimension={{width:1,height:1}} minWidth={1} minHeight={1} {...props}/>;
export const Overview = ({domains, history, alerts}) => {
    const latest = domains.map(d => d.last_scan).filter(Boolean);
    const average = latest.length ? Math.round(latest.reduce((v,s) => v+s.score,0)/latest.length) : null;
    const active = domains.filter(d => d.monitoring_enabled).length;
    const findings = latest.reduce((v,s) => v+issueCount(s),0);
    const critical = latest.reduce((v,s) => v+(s.counts.critical||0)+(s.counts.high||0),0);
    const unread = alerts.filter(a => !a.read).length;
    const metrics = [
        {id:"score", label:"Average security score", value:average ?? "—", unit:"/100", Icon:ShieldCheck, detail:latest.length ? `Across ${latest.length} scanned ${latest.length === 1 ? "domain" : "domains"}` : "Awaiting your first scan", color:"cyan"},
        {id:"domains", label:"Watched domains", value:domains.length, Icon:Globe2, detail:`${active} on a daily schedule`, color:"neutral"},
        {id:"findings", label:"Open findings", value:latest.length ? findings : "—", Icon:TriangleAlert, detail:`${critical} critical & high severity`, color:"amber"},
        {id:"alerts", label:"Unread drift alerts", value:unread, Icon:Bell, detail:unread ? "Grade declines need attention" : "No unread grade drops", color:unread ? "red" : "green"},
    ];
    return <>
        <div className="dash-metrics">{metrics.map(({id,label,value,unit,Icon,detail,color}) => <div className={`dash-metric metric-${color}`} key={id} data-testid={`metric-card-${id}`}><div><span>{label}</span><Icon size={16}/></div><strong data-testid={`metric-value-${id}`}>{value}<small>{unit}</small></strong><p data-testid={`metric-detail-${id}`}>{detail}</p></div>)}</div>
        <div className="dash-telemetry"><Coverage domains={domains}/><ScoreHistory history={history}/></div>
        {unread > 0 && <Link to="/dashboard/alerts" className="dash-drift-banner" data-testid="overview-drift-link"><Bell size={17}/><span>{unread} unread grade {unread === 1 ? "drop" : "drops"} in your drift inbox</span><ArrowUpRight size={17}/></Link>}
    </>;
};

const Coverage = ({domains}) => {
    const scanned = domains.map(d => d.last_scan).filter(Boolean);
    const categories = {"SSL/TLS":"TLS",TRANSPORT:"Transport",HEADERS:"Headers",SESSION:"Cookies",CORS:"CORS",ENV_LEAK:"Exposure",NETWORK:"Network"};
    const data = Object.entries(categories).map(([key,label]) => {
        const checks = scanned.flatMap(s => s.checks || []).filter(c => c.category === key);
        return {label, total:checks.length, passed:checks.filter(c => c.status === "pass").length, value:checks.length ? Math.round(checks.filter(c => c.status === "pass").length/checks.length*100) : null};
    }).filter(c => c.total);
    const checks = scanned.flatMap(s => s.checks || []);
    const rate = checks.length ? Math.round(checks.filter(c => c.status === "pass").length/checks.length*100) : null;
    return <section className="dash-coverage" data-testid="security-coverage"><div className="dash-section-heading"><h2><ScanLine size={17}/>Security posture</h2><span className="dash-live-label">LATEST SCANS</span></div><div className="dash-radar-layout">
        <div className="dash-radar" data-testid="coverage-chart">{data.length >= 3 ? <ResponsiveContainer width="100%" height="100%"><RadarChart data={data} outerRadius="66%"><PolarGrid stroke="hsl(var(--border))"/><PolarAngleAxis dataKey="label" tick={{fill:"hsl(var(--muted-foreground))",fontSize:11}}/><PolarRadiusAxis domain={[0,100]} tick={false} axisLine={false}/><Radar dataKey="value" name="Passed checks (%)" stroke="hsl(var(--brand))" fill="hsl(var(--brand))" fillOpacity={0.17} strokeWidth={2} dot={{r:3,fill:"hsl(var(--brand))"}}/><Tooltip contentStyle={tooltipStyle} formatter={(value) => [`${value}%`,"Pass rate"]}/></RadarChart></ResponsiveContainer> : <div className="dash-empty"><ShieldCheck size={32}/><p>No coverage baseline yet</p></div>}</div>
        <div className="dash-coverage-stats"><span className="dash-label">CHECKS PASSING</span><strong data-testid="coverage-pass-rate">{rate ?? "—"}<small>{rate !== null ? "%" : ""}</small></strong><p data-testid="coverage-check-count">{checks.filter(c => c.status === "pass").length} of {checks.length} checks</p><div className="dash-severity-bars">{[["critical","Critical"],["high","High"],["medium","Medium"],["low","Low"]].map(([key,label]) => {const count=scanned.reduce((n,s) => n+(s.counts[key]||0),0);return <div key={key} data-testid={`severity-${key}`}><span><i className={`severity-dot ${key}`}/>{label}</span><b>{count}</b></div>;})}</div></div>
    </div></section>;
};

const ScoreHistory = ({history}) => {
    const targets = [...new Set(history.map(s => s.target))];
    const [selected, setSelected] = useState("");
    const [days, setDays] = useState(30);
    const target = targets.includes(selected) ? selected : targets[0] || "";
    const data = useMemo(() => history.filter(s => s.target === target && Date.now()-new Date(s.created_at).getTime() <= days*86400000).slice().reverse().map(s => ({...s,time:new Date(s.created_at).getTime()})), [history,target,days]);
    const latest = data[data.length-1];
    return <section className="dash-trends" data-testid="score-history-panel"><div className="dash-section-heading"><h2><Activity size={17}/>Score history</h2><div className="dash-segments">{[7,30].map(d => <button key={d} onClick={() => setDays(d)} data-testid={`chart-range-${d}`} aria-pressed={days === d} className={days === d ? "selected" : ""}>{d}D</button>)}</div></div><div className="dash-trend-summary"><div><strong data-testid="chart-latest-score">{latest?.score ?? "—"}<small>/100</small></strong><span data-testid="chart-scan-count">{data.length} scans in {days} days</span></div><select aria-label="Score history domain" data-testid="chart-target-select" value={target} onChange={e => setSelected(e.target.value)}>{targets.length ? targets.map(t => <option key={t} value={t}>{t}</option>) : <option value="">No scans yet</option>}</select></div><div className="dash-area-chart" data-testid="score-history-chart">{data.length ? <ResponsiveContainer width="100%" height="100%"><AreaChart data={data} margin={{top:10,right:12,left:-25,bottom:0}}><defs><linearGradient id="score-history-fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="hsl(var(--brand))" stopOpacity={0.22}/><stop offset="100%" stopColor="hsl(var(--brand))" stopOpacity={0}/></linearGradient></defs><CartesianGrid vertical={false} stroke="hsl(var(--border))" strokeDasharray="3 5"/><XAxis dataKey="time" type="number" domain={['dataMin','dataMax']} tickFormatter={v => new Date(v).toLocaleDateString([],{month:"short",day:"numeric"})} tick={{fontSize:10,fill:"hsl(var(--muted-foreground))"}} axisLine={false} tickLine={false} minTickGap={40}/><YAxis domain={[0,100]} ticks={[0,25,50,75,100]} tick={{fontSize:10,fill:"hsl(var(--muted-foreground))"}} axisLine={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle} labelFormatter={v => new Date(v).toLocaleString()} formatter={v => [`${v}/100`,"Score"]}/><Area type="linear" dataKey="score" stroke="hsl(var(--brand))" fill="url(#score-history-fill)" strokeWidth={2} dot={{r:3,fill:"hsl(var(--brand))",strokeWidth:0}} isAnimationActive={false}/></AreaChart></ResponsiveContainer> : <div className="dash-empty" data-testid="chart-empty"><Activity size={27}/><p>No scans in this time range</p></div>}</div></section>;
};