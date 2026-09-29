import { useEffect, useState } from "react";
import { ShieldCheck, Loader2, RefreshCw, CircleAlert, Globe2, Link2, FileText, Code2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { api, formatApiErrorDetail } from "@/lib/api";
import { VerificationStatus } from "./VerificationStatus";
import { VerificationInstructions } from "./VerificationInstructions";
import "./verification.css";

const METHODS = [["dns_txt","DNS TXT",Globe2],["dns_cname","CNAME",Link2],["html_file","HTML file",FileText],["html_meta","Meta tag",Code2]];
const ERRORS = {dns_record_not_found:"The DNS record was not found. Check your DNS settings and try again.",dns_record_mismatch:"The DNS record does not match the expected value.",http_file_unreachable:"The verification URL or file contents could not be confirmed.",meta_tag_missing:"The verification meta tag was not found in the homepage’s head.",timeout:"Verification timed out. Please try again."};

export const VerificationDialog = ({domainId, onClose, onUpdated}) => {
    const [domain,setDomain]=useState(null),[method,setMethod]=useState("dns_txt"),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(null);
    const [loadVersion,setLoadVersion]=useState(0);
    useEffect(() => {
        if (!domainId) return;
        let active=true;setDomain(null);setError(null);setLoading(true);
        api.get(`/domains/${domainId}`).then(({data}) => {if(active){setDomain(data);setMethod(data.verification_method || "dns_txt");}})
            .catch(e => {if(active)setError(formatApiErrorDetail(e.response?.data?.detail));}).finally(() => {if(active)setLoading(false);});
        return () => {active=false;};
    },[domainId,loadVersion]);
    const verify = async () => {
        setBusy(true);setError(null);
        try {const {data}=await api.post(`/domains/${domainId}/${domain.verified ? "reverify" : "verify"}`,{method});setDomain(data);
            if(data.success) toast.success("Domain ownership verified");else {setError(data.message || ERRORS[data.reason]);toast.error(data.message || ERRORS[data.reason]);}
            await onUpdated();
        } catch(e){const message=formatApiErrorDetail(e.response?.data?.detail);setError(message);toast.error(message);}
        finally {setBusy(false);}
    };
    const expired=domain && !domain.verified && new Date(domain.token_expires_at)<=new Date();
    return <Dialog open={Boolean(domainId)} onOpenChange={open => {if(!open && !busy)onClose();}}><DialogContent className="verification-dialog" data-testid="verification-dialog" data-lenis-prevent><DialogHeader>
        <div className="verification-eyebrow" data-testid="verification-eyebrow"><ShieldCheck size={16}/>DOMAIN OWNERSHIP</div>
        <DialogTitle className="verification-title" data-testid="verification-dialog-title">{domain?.domain || "Verify your domain"}</DialogTitle>
        <DialogDescription data-testid="verification-dialog-description">{domain?.verified ? "Ownership confirmed for this domain and its subdomains." : "Verify ownership to unlock advanced security scans."}</DialogDescription>
    </DialogHeader>
    {loading && <div className="verification-loading" data-testid="verification-loading"><Loader2 className="animate-spin" size={20}/>Loading verification details…</div>}
    {domain && <>
        <div className="verification-summary"><VerificationStatus status={domain.status} testId="verification-current-status"/><span data-testid="verification-expiry">{domain.verified ? "No expiry after verification" : expired ? "Token expired" : `Token expires ${new Date(domain.token_expires_at).toLocaleDateString(undefined,{month:"short",day:"numeric"})}`}</span></div>
        {domain.status === "needs_reverification" && <div className="verification-notice" data-testid="reverification-notice">Your last recheck failed. Advanced scans remain available while you update your verification record.</div>}
        {expired && <div className="verification-error" role="alert" data-testid="verification-expired">This token has expired. Remove this domain and add it again to receive a fresh token.</div>}
        <Tabs value={method} onValueChange={value => {setMethod(value);setError(null);}} className="verification-tabs"><TabsList className="verification-methods" data-testid="verification-method-tabs">{METHODS.map(([id,label,Icon]) => <TabsTrigger key={id} value={id} disabled={busy} data-testid={`verification-tab-${id}`}><Icon size={14}/><span>{label}</span></TabsTrigger>)}</TabsList>
            {METHODS.map(([id]) => <TabsContent key={id} value={id} data-testid={`verification-panel-${id}`}><VerificationInstructions domain={domain} method={id}/></TabsContent>)}
        </Tabs>
        {!error && domain.last_verification_error && <p className="verification-hint" data-testid="last-verification-error">Last check: {ERRORS[domain.last_verification_error] || domain.last_verification_error}</p>}
    </>}
    {error && <div className="verification-error" role="alert" data-testid="verification-error"><CircleAlert size={16}/><span>{error}</span></div>}
    {!domain && !loading && error && <Button variant="outline" onClick={() => setLoadVersion(v => v+1)} data-testid="verification-load-retry">Try again</Button>}
    {domain && <div className="verification-footer"><span data-testid="verification-subdomain-note"><ShieldCheck size={15}/>{domain.verified ? "Subdomains inherit ownership" : "Only one method is needed"}</span><Button disabled={busy || expired} onClick={verify} data-testid="verify-domain-button">{busy ? <Loader2 size={15} className="animate-spin"/> : domain.verified ? <RefreshCw size={15}/> : <ShieldCheck size={15}/>} {busy ? "Checking…" : domain.verified ? "Re-verify" : "Verify now"}</Button></div>}
    </DialogContent></Dialog>;
};