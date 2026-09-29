import { useState } from "react";
import { Check, Copy, Download, ExternalLink } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

export const CopyValue = ({label, value, id}) => {
    const [copied, setCopied] = useState(false);
    const copy = async () => {
        try {await navigator.clipboard.writeText(value);setCopied(true);toast.success(`${label} copied`);}
        catch {toast.error("Clipboard unavailable. Select and copy the value manually.");}
    };
    return <div className="verification-field"><span data-testid={`${id}-label`}>{label}</span><div><code data-testid={`${id}-value`}>{value}</code><button type="button" aria-label={`Copy ${label.toLowerCase()}`} title={`Copy ${label.toLowerCase()}`} onClick={copy} data-testid={`${id}-copy`}>{copied ? <Check size={15}/> : <Copy size={15}/>}</button></div></div>;
};

export const VerificationInstructions = ({domain, method}) => {
    const data = domain.instructions[method];
    if (method === "dns_txt" || method === "dns_cname") return <div className="verification-instructions" data-testid={`${method}-instructions`}>
        <p className="verification-step" data-testid="dns-instruction">Add this {data.type} record in your domain’s DNS settings.</p>
        <div className="verification-dns-grid"><CopyValue label="Record type" value={data.type} id={`${method}-type`}/><CopyValue label="Name / host" value={data.name} id={`${method}-name`}/></div>
        <CopyValue label="Record value" value={data.value} id={`${method}-record`}/>
        <p className="verification-hint" data-testid="dns-hostname">Record hostname: <strong>{data.hostname}</strong></p>
        <p className="verification-hint" data-testid="dns-propagation-note">DNS changes can take a few minutes to appear. For CNAME records, disable proxying.</p>
    </div>;
    if (method === "html_file") return <div className="verification-instructions" data-testid="html_file-instructions">
        <p className="verification-step" data-testid="file-instruction">Place this text file in your website’s <code>/.well-known/</code> directory.</p>
        <CopyValue label="File contents" value={data.content} id="html-file-content"/>
        <CopyValue label="Public file URL" value={data.url} id="html-file-url"/>
        <Button variant="outline" className="verification-download" data-testid="download-verification-file" onClick={() => {
            const url=URL.createObjectURL(new Blob([data.content],{type:"text/plain"}));const a=document.createElement("a");a.href=url;a.download=data.filename;a.click();setTimeout(() => URL.revokeObjectURL(url),1000);
        }}><Download size={14}/>Download verification file</Button>
    </div>;
    return <div className="verification-instructions" data-testid="html_meta-instructions">
        <p className="verification-step" data-testid="meta-instruction">Add this tag inside the <code>&lt;head&gt;</code> of your homepage’s HTML.</p>
        <CopyValue label="Meta tag" value={data.tag} id="html-meta-tag"/>
        <p className="verification-hint" data-testid="meta-source-note">The tag must appear in the HTML returned by your server, not only after JavaScript runs.</p>
        <a href={data.url} target="_blank" rel="noreferrer" className="dash-text-link" data-testid="open-domain-homepage">Open {domain.domain}<ExternalLink size={13}/></a>
    </div>;
};