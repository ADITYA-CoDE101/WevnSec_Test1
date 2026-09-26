import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { Reveal, EASE } from "./Reveal";

export const FinalCta = () => {
    const toTop = () => {
        if (window.__lenis) window.__lenis.scrollTo(0);
        else window.scrollTo({ top: 0, behavior: "smooth" });
    };

    return (
        <section className="relative py-28 sm:py-40 border-t border-border overflow-hidden">
            <div className="absolute inset-0 dot-grid [mask-image:radial-gradient(ellipse_60%_70%_at_50%_100%,black,transparent)]" />
            <div className="absolute -bottom-48 left-1/2 -translate-x-1/2 h-[420px] w-[720px] rounded-full bg-brand/12 blur-[120px] pointer-events-none" />
            <div className="relative max-w-3xl mx-auto px-4 text-center">
                <motion.h2
                    initial="hidden"
                    whileInView="show"
                    viewport={{ once: true, margin: "-60px" }}
                    className="text-3xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.08] text-foreground"
                >
                    {[
                        { text: "Scan your site in", accent: false },
                        { text: "30 seconds.", accent: true },
                    ].map((l, i) => (
                        <span key={l.text} className="block overflow-hidden pb-1">
                            <motion.span
                                className={`block ${l.accent ? "text-brand text-glow" : ""}`}
                                variants={{
                                    hidden: { y: "110%" },
                                    show: { y: 0, transition: { duration: 0.9, delay: i * 0.12, ease: EASE } },
                                }}
                            >
                                {l.text}
                            </motion.span>
                        </span>
                    ))}
                </motion.h2>
                <Reveal delay={0.25}>
                    <p className="mt-6 text-lg text-muted-foreground">
                        Free forever. No card, no agent, no excuses.
                    </p>
                </Reveal>
                <Reveal delay={0.35}>
                    <button
                        data-testid="final-cta-scan-button"
                        onClick={toTop}
                        className="group mt-10 inline-flex items-center gap-2 h-13 px-8 py-3.5 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-base font-semibold hover:brightness-110 hover:shadow-[0_0_40px_-8px_hsl(var(--brand)/0.8)] active:scale-[0.98] transition-all duration-200"
                    >
                        Run your free scan
                        <ArrowRight size={17} className="transition-transform duration-200 group-hover:translate-x-1" />
                    </button>
                </Reveal>
            </div>
        </section>
    );
};
