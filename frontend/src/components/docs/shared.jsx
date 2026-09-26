import { Link } from "react-router-dom";
import { BookOpen, ShieldCheck, ArrowUpRight, Loader2 } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

export const CoverageBadge = ({article, testId}) => <span className={`docs-badge coverage-${article.coverage}`} data-testid={testId}>{article.coverage==="automated" ? <ShieldCheck size={12}/> : <BookOpen size={12}/>} {article.coverage==="automated" ? "Automated check" : "Reference only"}</span>;
export const ArticleCard = ({article, prefix="docs"}) => <Link to={`/docs/${article.slug}`} className="docs-article-card" data-testid={`${prefix}-article-${article.slug}`}><div><CoverageBadge article={article} testId={`${prefix}-coverage-${article.slug}`}/><ArrowUpRight size={16}/></div><h2 data-testid={`${prefix}-title-${article.slug}`}>{article.title}</h2><p data-testid={`${prefix}-summary-${article.slug}`}>{article.summary}</p><footer data-testid={`${prefix}-category-${article.slug}`}>{article.category}<span>{article.coverage==="automated" && article.check_ids.includes("LEAK-01") ? "Ownership required" : article.coverage==="educational" ? "Not detected by this scanner" : "Included in Instant Scan"}</span></footer></Link>;
export const AdminGate = ({children}) => {
    const {user}=useAuth();
    if(user===undefined)return <div className="docs-loading" data-testid="docs-admin-loading"><Loader2 className="animate-spin"/>Checking access…</div>;
    if(!user || user.role!=="admin")return <main className="docs-page docs-access" data-testid="docs-admin-access-denied"><ShieldCheck size={32}/><h1>Administrator access required</h1><p>Documentation editing is restricted to administrators.</p><Link to={user ? "/docs" : "/signin"} data-testid="docs-admin-signin-link">{user ? "Browse the reference library" : "Sign in to your admin account"}<ArrowUpRight size={15}/></Link></main>;
    return children;
};