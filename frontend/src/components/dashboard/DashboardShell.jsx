import { NavLink, Link } from "react-router-dom";
import { ShieldCheck, LayoutDashboard, Globe2, History, Bell, Sun, Moon, LogOut, ArrowUpRight, ChevronRight, Search, RefreshCw } from "lucide-react";

export const DashboardShell = ({user, logout, theme, onToggleTheme, alerts, status, search, setSearch, refresh, refreshing, section, children}) => {
    const nav = [["", "Overview", LayoutDashboard], ["/domains", "Watched domains", Globe2], ["/history", "Scan history", History], ["/alerts", "Drift alerts", Bell]];
    return <div className="dash-shell" data-testid="dashboard-page">
        <aside className="dash-sidebar">
            <Link to="/" className="dash-logo" data-testid="dashboard-brand"><span><ShieldCheck size={22}/></span><strong>WevnSec<span className="text-brand">.</span></strong></Link>
            <div className="dash-workspace" data-testid="dashboard-workspace"><span className="dash-workspace-icon">{(user.name || "W")[0].toUpperCase()}</span><div><strong>Personal workspace</strong><small>{user.name}</small></div></div>
            <p className="dash-nav-label">WORKSPACE</p>
            <nav className="dash-navigation" aria-label="Dashboard">
                {nav.map(([path,label,Icon]) => <NavLink key={path} end to={`/dashboard${path}`} aria-label={label} title={label} data-testid={`dashboard-nav-${path.slice(1)||"overview"}`} className={({isActive}) => `dash-nav-item ${isActive ? "active" : ""}`}><Icon size={17}/><span>{label}</span>{path === "/alerts" && alerts > 0 && <b data-testid="sidebar-alert-count">{alerts}</b>}</NavLink>)}
            </nav>
            <div className="dash-sidebar-bottom">
                <div className="dash-monitor-status" data-testid="scheduler-status"><i className={status?.scheduler_running ? "is-online" : ""}/><span>{status?.scheduler_running ? "Daily monitoring active" : "Monitoring unavailable"}</span></div>
                <Link to="/changelog" data-testid="dashboard-changelog" className="dash-nav-item"><ArrowUpRight size={16}/><span>What’s new</span></Link>
                <Link to="/docs" data-testid="dashboard-documentation" className="dash-nav-item"><ArrowUpRight size={16}/><span>Security reference</span></Link>
                <div className="dash-user"><span className="dash-avatar">{(user.name || "W").slice(0,2).toUpperCase()}</span><div><strong>{user.name}</strong><small title={user.email} data-testid="dashboard-account-email">{user.email}</small></div><button className="dash-icon-button" onClick={logout} title="Sign out" aria-label="Sign out" data-testid="dashboard-signout-button"><LogOut size={16}/></button></div>
            </div>
        </aside>
        <div className="dash-main">
            <header className="dash-topbar"><div className="dash-breadcrumb"><ShieldCheck size={15}/><span>Workspace</span><ChevronRight size={13}/><strong>{section}</strong></div><div className="dash-top-actions"><label className="dash-search"><Search size={15}/><input aria-label="Search domains and scans" placeholder="Search domains…" value={search} onChange={(e) => setSearch(e.target.value)} data-testid="dashboard-search-input"/></label><button className="dash-icon-button" title="Refresh dashboard" aria-label="Refresh dashboard" onClick={refresh} disabled={refreshing} data-testid="dashboard-refresh"><RefreshCw size={16} className={refreshing ? "animate-spin" : ""}/></button><button className="dash-icon-button" title="Toggle theme" aria-label="Toggle theme" onClick={onToggleTheme} data-testid="dashboard-theme-toggle">{theme === "dark" ? <Sun size={17}/> : <Moon size={17}/>}</button></div></header>
            <div className="dash-mobile-account"><span data-testid="dashboard-mobile-email">{user.email}</span><button className="dash-icon-button" onClick={logout} title="Sign out" aria-label="Sign out" data-testid="dashboard-mobile-signout"><LogOut size={15}/></button></div>
            <main className="dash-content">{children}</main>
            <footer className="dash-footnote"><span>WevnSec / Security workspace</span><span>All times shown in your local timezone</span></footer>
        </div>
    </div>;
};