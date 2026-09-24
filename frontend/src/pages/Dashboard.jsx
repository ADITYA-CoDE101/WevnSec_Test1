import { useCallback, useEffect, useState } from "react";
import { useLocation, useNavigate, Link } from "react-router-dom";
import { Plus, ArrowUpRight, Loader2, Mail } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { DashboardShell } from "@/components/dashboard/DashboardShell";
import { DomainList } from "@/components/dashboard/DomainList";
import { Overview } from "@/components/dashboard/Overview";
import { HistoryList, AlertList } from "@/components/dashboard/ActivityViews";
import { AddDomainDialog, RemoveDomainDialog } from "@/components/dashboard/DomainDialogs";
import "@/components/dashboard/dashboard.css";

const SECTIONS = {overview:["Security overview", "Your attack surface, in focus."], domains:["Watched domains", "Daily monitoring across your domains."], history:["Scan history", "A record of every security assessment."], alerts:["Drift alerts", "Security grade changes that need your attention."]};
export default function Dashboard({theme, onToggleTheme}) {
    const {user, logout} = useAuth();
    const navigate = useNavigate();
    const location = useLocation();
    const section = location.pathname.split("/")[2] || "overview";
    const current = SECTIONS[section] ? section : "overview";
    const [domains, setDomains] = useState([]), [history, setHistory] = useState([]), [alerts, setAlerts] = useState([]);
    const [status, setStatus] = useState(null), [loading, setLoading] = useState(true), [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null), [search, setSearch] = useState(""), [busy, setBusy] = useState(null);
    const [addOpen, setAddOpen] = useState(false), [remove, setRemove] = useState(null);
    useEffect(() => {if(user === null) navigate("/signin");},[user,navigate]);
    const load = useCallback(async () => {
        setRefreshing(true);
        try {
            const [d,h,a,s] = await Promise.all([api.get("/domains"),api.get("/scans/history"),api.get("/alerts"),api.get("/monitoring/status")]);
            setDomains(d.data);setHistory(h.data);setAlerts(a.data);setStatus(s.data);setError(null);
        } catch(e) {setError(formatApiErrorDetail(e.response?.data?.detail));}
        finally {setLoading(false);setRefreshing(false);}
    },[]);
    useEffect(() => {if(!user) return;load();const timer=setInterval(load,30000);return () => clearInterval(timer);},[user,load]);
    useEffect(() => {setSearch("");},[current]);
    const addDomain = async domain => {try {await api.post("/domains",{domain});await load();toast.success("Domain watched — baseline scan queued");return true;} catch(e) {toast.error(formatApiErrorDetail(e.response?.data?.detail));return false;}};
    const scan = async target => {if(busy) return;setBusy(target);try {const {data}=await api.post("/scan",{target});navigate(`/report/${data.share_id}`);} catch(e) {toast.error(formatApiErrorDetail(e.response?.data?.detail));} finally {setBusy(null);}};
    const preferences = async (d, values) => {setBusy(d.id);try {await api.patch(`/domains/${d.id}`,values);await load();toast.success(values.email_alerts_enabled === true ? `Grade-drop emails enabled for ${user.email}` : "Monitoring preferences updated");} catch(e) {toast.error(formatApiErrorDetail(e.response?.data?.detail));} finally {setBusy(null);}};
    const removeDomain = async d => {try {await api.delete(`/domains/${d.id}`);setRemove(null);await load();toast.success("Domain removed from monitoring");} catch(e) {toast.error(formatApiErrorDetail(e.response?.data?.detail));}};
    const markRead = async id => {try {await api.patch(`/alerts/${id}/read`);setAlerts(items => items.map(a => a.id === id ? {...a,read:true} : a));} catch(e) {toast.error(formatApiErrorDetail(e.response?.data?.detail));}};
    if(!user) return <main className="min-h-screen flex items-center justify-center" data-testid="dashboard-auth-loading"><Loader2 className="animate-spin text-brand"/></main>;
    const query=search.trim().toLowerCase(), filteredDomains=domains.filter(d => d.domain.includes(query)), filteredHistory=history.filter(s => s.target.includes(query)), filteredAlerts=alerts.filter(a => a.domain.includes(query));
    const listProps={domains:filteredDomains,onAdd:() => setAddOpen(true),onScan:scan,onRemove:setRemove,onPreferences:preferences,busy};
    return <DashboardShell {...{user,theme,onToggleTheme,status,search,setSearch,refreshing}} section={SECTIONS[current][0]} alerts={alerts.filter(a => !a.read).length} refresh={load} logout={() => {logout();navigate("/");}}>
        <div className="dash-page-heading"><div><p className="dash-eyebrow">YOUR SECURITY WORKSPACE</p><h1 data-testid="dashboard-heading">{SECTIONS[current][0]}</h1><p>{SECTIONS[current][1]}</p></div><Button className="dash-primary-action" onClick={() => setAddOpen(true)} data-testid="dashboard-watch-domain"><Plus size={16}/>Watch domain</Button></div>
        {error && <div className="dash-error-banner" role="alert" data-testid="dashboard-load-error">{error}<button onClick={load} data-testid="dashboard-retry">Retry</button></div>}
        {loading ? <div className="dash-loading" data-testid="dashboard-loading"><Loader2 className="animate-spin"/>Loading your workspace…</div> : <div className="dash-view" key={current}>
            {current === "overview" && <><Overview domains={domains} history={history} alerts={alerts}/><DomainList {...listProps} compact/>{domains.length > 4 && <Link to="/dashboard/domains" className="dash-text-link dash-view-all" data-testid="view-all-domains">View all domains<ArrowUpRight size={14}/></Link>}</>}
            {current === "domains" && <><div className="dash-email-note" data-testid="email-recipient-note"><Mail size={15}/><span>Grade-drop emails go to <strong>{user.email}</strong> when enabled.</span></div><DomainList {...listProps}/></>}
            {current === "history" && <HistoryList history={filteredHistory}/>}
            {current === "alerts" && <AlertList alerts={filteredAlerts} onRead={markRead}/>}
        </div>}
        <AddDomainDialog open={addOpen} onClose={() => setAddOpen(false)} onAdd={addDomain}/><RemoveDomainDialog domain={remove} onClose={() => setRemove(null)} onConfirm={removeDomain}/>
    </DashboardShell>;
}