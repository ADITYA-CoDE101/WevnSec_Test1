import { useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import useSWR from "swr";
import { Search, ArrowUpRight, BookOpen, Loader2, SlidersHorizontal } from "lucide-react";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { ArticleCard } from "@/components/docs/shared";
import "@/components/docs/docs.css";

export default function Documentation(){
    const {user}=useAuth();const [params,setParams]=useSearchParams();
    const [query,setQuery]=useState(params.get("q") || ""),[coverage,setCoverage]=useState(params.get("coverage") || "all"),[category,setCategory]=useState("all");
    const {data,error,isLoading,mutate}=useSWR("/docs",url=>api.get(url).then(r=>r.data));
    const categories=useMemo(()=>[...new Set((data || []).map(a=>a.category))].sort(),[data]);
    const filtered=(data || []).filter(a=>(coverage==="all" || a.coverage===coverage) && (category==="all" || a.category===category) && [a.title,a.summary,a.category,a.explanation,a.mitigation,...a.check_ids].join(" ").toLowerCase().includes(query.trim().toLowerCase()));
    const changeQuery=value=>{setQuery(value);setParams(value ? {q:value} : {},{replace:true});};
    return <main className="docs-page" data-testid="documentation-page"><div className="docs-container">
        <div className="docs-page-topline"><span className="docs-eyebrow" data-testid="docs-eyebrow"><BookOpen size={14}/>WEVNSEC / SECURITY REFERENCE</span>{user?.role==="admin" && <Link to="/docs/manage" className="docs-manage-link" data-testid="docs-manage-link"><SlidersHorizontal size={14}/>Manage documentation<ArrowUpRight size={14}/></Link>}</div>
        <header className="docs-page-heading"><h1 data-testid="docs-heading">Understand the finding.<br/><span>Know what to fix.</span></h1><p data-testid="docs-introduction">Practical explanations, mitigation steps, and the limits of each check. Built for the people shipping the fix.</p></header>
        <div className="docs-search-row"><label className="docs-search"><Search size={18}/><input value={query} onChange={e=>changeQuery(e.target.value)} placeholder="Search weaknesses, headers, or check IDs…" aria-label="Search documentation" data-testid="docs-search-input"/></label><span data-testid="docs-article-count">{data ? `${data.length} published articles` : "Reference library"}</span></div>
        <div className="docs-layout"><aside className="docs-sidebar"><p data-testid="docs-browse-label">BROWSE BY TOPIC</p><button className={category==="all" ? "active" : ""} onClick={()=>setCategory("all")} data-testid="docs-category-all">All topics <span>{data?.length ?? "—"}</span></button>{categories.map((c,i)=><button key={c} className={category===c ? "active" : ""} onClick={()=>setCategory(c)} data-testid={`docs-category-${i}`}>{c}<span>{data.filter(a=>a.category===c).length}</span></button>)}<div className="docs-scope-note" data-testid="docs-scope-note"><ShieldScope/>Reference-only topics are educational. They are not detected or ruled out by the current scanner.</div></aside>
            <section className="docs-library"><div className="docs-coverage-tabs" role="tablist" aria-label="Documentation coverage">{[["all","All articles"],["automated","Scanner checks"],["educational","Reference only"]].map(([id,label])=><button key={id} role="tab" aria-selected={coverage===id} className={coverage===id ? "active" : ""} onClick={()=>setCoverage(id)} data-testid={`docs-filter-${id}`}>{label}</button>)}</div>
                {isLoading ? <div className="docs-loading" data-testid="docs-loading"><Loader2 className="animate-spin"/>Loading the reference library…</div> : error ? <div className="docs-empty" role="alert" data-testid="docs-error"><h2>The library couldn’t be loaded.</h2><button onClick={()=>mutate()} data-testid="docs-retry">Try again</button></div> : filtered.length ? <><p className="docs-results-count" data-testid="docs-results-count">{filtered.length} {filtered.length===1 ? "article" : "articles"}</p><div className="docs-article-grid">{filtered.map(a=><ArticleCard key={a.id} article={a}/>)}</div></> : <div className="docs-empty" data-testid="docs-no-results"><Search size={25}/><h2>No matching articles</h2><p>Try another topic or clear your filters.</p><button onClick={()=>{changeQuery("");setCategory("all");setCoverage("all");}} data-testid="docs-clear-filters">Clear filters</button></div>}
            </section>
        </div>
    </div></main>;
}
const ShieldScope=()=> <BookOpen size={17}/>;