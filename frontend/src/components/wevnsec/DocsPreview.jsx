import { Link } from "react-router-dom";
import useSWR from "swr";
import { ArrowUpRight, BookOpen } from "lucide-react";
import { Reveal, SectionHeading } from "./Reveal";
import { ArticleCard } from "@/components/docs/shared";
import { api } from "@/lib/api";
import "@/components/docs/docs.css";

export const DocsPreview=()=>{
    const {data,error}=useSWR("/docs",url=>api.get(url).then(r=>r.data));
    const articles=(data || []).filter(a=>a.coverage==="automated").slice(0,3);
    return <section id="docs" data-testid="docs-preview-section" className="py-24 sm:py-32 border-t border-border bg-card/30"><div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"><SectionHeading eyebrow="// security reference" title="A finding is only the beginning." sub="Understand what was observed, how to address it, and what an automated check cannot tell you."/><div className="mt-10 grid md:grid-cols-3 gap-5">{articles.map(a=><ArticleCard key={a.id} article={a} prefix="preview"/>)}</div>{!data && <p className="text-sm text-muted-foreground mt-8" data-testid="docs-preview-state">{error ? "The library is temporarily unavailable." : "Loading the reference library…"}</p>}<Reveal><Link to="/docs" data-testid="docs-read-more-link" className="mt-8 inline-flex items-center gap-2 text-sm font-medium text-brand"><BookOpen size={16}/>Explore all documentation<ArrowUpRight size={15}/></Link></Reveal></div></section>;
};