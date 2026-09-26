import { MARQUEE_ITEMS } from "./data";

export const Marquee = () => {
    const row = [...MARQUEE_ITEMS, ...MARQUEE_ITEMS];
    return (
        <div className="border-b border-border py-5 overflow-hidden marquee-mask" aria-hidden="true">
            <div className="flex w-max animate-marquee gap-14 pr-14">
                {row.map((item, i) => (
                    <span key={i} className="flex items-center gap-14 font-mono text-[11px] tracking-[0.3em] text-muted-foreground/70 whitespace-nowrap">
                        {item}
                        <span className="text-brand/60">✦</span>
                    </span>
                ))}
            </div>
        </div>
    );
};
