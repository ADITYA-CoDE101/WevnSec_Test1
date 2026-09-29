import { Link, useParams } from "react-router-dom";
import useSWR from "swr";
import { ArrowLeft, ArrowUpRight, Loader2, Info } from "lucide-react";
import { api } from "@/lib/api";
import { CoverageBadge } from "@/components/docs/shared";
import "@/components/docs/docs.css";

const SECTIONS=[["explanation","What it means"],["impact","Why it matters"],["mitigation","How to address it"],["validation","Validate your changes"],["limitations","What this check does not prove"]];
export default function DocumentationArticle(){
    const {slug}=useParams();
    const {data:a,error,isLoading,mutate}=useSWR(`/docs/${slug}`,url=>api.get(url).then(r=>r.data));
    return <main className="docs-page" data-testid="documentation-article-page"><div className="docs-container">
        <Link to="/docs" className="docs-back" data-testid="article-back-link"><ArrowLeft size={14}/>Security reference</Link>
        {isLoading ? <div className="docs-loading" data-testid="article-loading"><Loader2 className="animate-spin"/>Loading article…</div> : error ? <div className="docs-empty" data-testid="article-error" role="alert"><h1>{error.response?.status===404 ? "Article not available" : "Unable to load this article"}</h1><p>{error.response?.status===404 ? "It may have been unpublished or removed." : "Please try again in a moment."}</p><button onClick={()=>mutate()} data-testid="article-retry">Try again</button></div> : a && <>
            <header className="docs-article-heading"><div className="docs-article-meta"><CoverageBadge article={a} testId="article-coverage"/><span data-testid="article-category">{a.category}</span></div><h1 data-testid="article-title">{a.title}</h1><p data-testid="article-summary">{a.summary}</p><small data-testid="article-updated">Updated {new Date(a.updated_at).toLocaleDateString(undefined,{year:"numeric",month:"long",day:"numeric"})} · Version {a.version}</small></header>
            <div className="docs-article-layout"><nav className="docs-toc" aria-label="Article contents"><p data-testid="article-toc-label">ON THIS PAGE</p>{SECTIONS.map(([id,title])=><a href={`#${id}`} key={id} onClick={e=>{e.preventDefault();document.getElementById(id)?.scrollIntoView({behavior:"smooth"});}} data-testid={`article-toc-${id}`}>{title}</a>)}<Link to="/docs" data-testid="article-all-topics">All topics<ArrowUpRight size={13}/></Link></nav><article className="docs-article-body">
                <div className={`docs-coverage-note coverage-${a.coverage}`} data-testid="article-scope"><Info size={17}/><span>{a.coverage==="educational" ? "Reference only — the current automated scanner does not detect or rule out this weakness." : `Related scanner checks: ${a.check_ids.join(", ")}.${a.check_ids.includes("LEAK-01") ? " Advanced scanning requires verified ownership." : " Available in Instant Scan; some checks depend on site responses."}`}</span></div>
                {SECTIONS.map(([id,title])=><section id={id} key={id} className="docs-prose-section" data-testid={`article-section-${id}`}><h2 data-testid={`article-heading-${id}`}>{title}</h2><p data-testid={`article-content-${id}`}>{a[id]}</p></section>)}
                {a.reference_url && <a href={a.reference_url} target="_blank" rel="noreferrer" className="docs-reference-link" data-testid="article-reference-link">Further reading<ArrowUpRight size={14}/></a>}
                <div className="docs-article-bottom"><Link to="/" data-testid="article-run-scan">Return to Instant Scan<ArrowUpRight size={14}/></Link><Link to="/docs" data-testid="article-browse-all">Browse all documentation</Link></div>
            </article></div>
        </>}
    </div></main>;
}