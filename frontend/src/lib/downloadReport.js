import { api, formatApiErrorDetail } from "@/lib/api";
import { toast } from "sonner";

export async function downloadReport(shareId, target) {
    try {
        const { data } = await api.get(`/scan/${shareId}/pdf`, { responseType: "blob" });
        const url = URL.createObjectURL(data);
        const link = document.createElement("a");
        link.href = url;
        link.download = `wevnsec-${target}-${shareId}.pdf`;
        link.click();
        setTimeout(() => URL.revokeObjectURL(url), 1000);
        toast.success("PDF report downloaded");
    } catch (error) {
        toast.error(formatApiErrorDetail(error.response?.data?.detail) || "PDF download failed");
    }
}