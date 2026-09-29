import { ShieldCheck, Clock3, AlertTriangle, CircleX } from "lucide-react";

const STATUSES = {
    pending: [Clock3, "Pending"], verified: [ShieldCheck, "Verified"],
    needs_reverification: [AlertTriangle, "Needs re-verification"], failed: [CircleX, "Failed"],
};
export const VerificationStatus = ({status="pending", testId}) => {
    const [Icon, label] = STATUSES[status] || STATUSES.pending;
    return <span className={`verification-status verification-${status}`} data-testid={testId}><Icon size={12}/>{label}</span>;
};