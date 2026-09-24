import { useState } from "react";
import { Plus, Loader2, Globe2, Trash2 } from "lucide-react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export const AddDomainDialog = ({open, onClose, onAdd}) => {
    const [value, setValue] = useState("");
    const [busy, setBusy] = useState(false);
    return <Dialog open={open} onOpenChange={v => !v && onClose()}><DialogContent data-testid="add-domain-dialog"><DialogHeader><DialogTitle><span className="flex items-center gap-2"><Globe2 size={19}/>Watch a domain</span></DialogTitle><DialogDescription>Daily scans start with a baseline scan. Email alerts are off until you enable them.</DialogDescription></DialogHeader><form onSubmit={async e => {e.preventDefault();setBusy(true);try {if(await onAdd(value)){setValue("");onClose();}} finally {setBusy(false);}}}><label htmlFor="new-domain" className="text-sm font-medium">Domain</label><input id="new-domain" autoFocus required maxLength={253} placeholder="yourapp.com" value={value} onChange={e => setValue(e.target.value)} data-testid="add-domain-input" className="dash-dialog-input"/><Button type="submit" disabled={busy || !value.trim()} className="w-full mt-5" data-testid="add-domain-button">{busy ? <Loader2 size={15} className="animate-spin"/> : <Plus size={15}/>} {busy ? "Adding domain…" : "Watch domain"}</Button></form></DialogContent></Dialog>;
};

export const RemoveDomainDialog = ({domain, onClose, onConfirm}) => {
    const [busy, setBusy] = useState(false);
    return <Dialog open={Boolean(domain)} onOpenChange={v => !v && onClose()}><DialogContent data-testid="remove-domain-dialog"><DialogHeader><DialogTitle>Remove watched domain?</DialogTitle><DialogDescription><span className="break-all">{domain?.domain}</span> will no longer be monitored. Existing reports and alerts are retained.</DialogDescription></DialogHeader><div className="flex gap-3 justify-end"><Button variant="outline" onClick={onClose} data-testid="remove-domain-cancel">Cancel</Button><Button variant="destructive" disabled={busy} data-testid="remove-domain-confirm" onClick={async () => {setBusy(true);try {await onConfirm(domain);}finally {setBusy(false);}}}>{busy ? <Loader2 size={15} className="animate-spin"/> : <Trash2 size={15}/>}Remove domain</Button></div></DialogContent></Dialog>;
};