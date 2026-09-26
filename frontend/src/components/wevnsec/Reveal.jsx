import { motion } from "framer-motion";

export const EASE = [0.16, 1, 0.3, 1];

export const Reveal = ({ children, delay = 0, y = 26, className = "", ...rest }) => (
    <motion.div
        className={className}
        initial={{ opacity: 0, y }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-70px" }}
        transition={{ duration: 0.75, delay, ease: EASE }}
        {...rest}
    >
        {children}
    </motion.div>
);

export const SectionHeading = ({ eyebrow, title, sub, align = "left" }) => (
    <div className={align === "center" ? "text-center mx-auto max-w-2xl" : "max-w-2xl"}>
        <Reveal>
            <p className="font-mono text-xs uppercase tracking-[0.25em] text-brand">{eyebrow}</p>
        </Reveal>
        <Reveal delay={0.08}>
            <h2 className="mt-4 text-2xl sm:text-3xl lg:text-4xl font-semibold tracking-tight leading-tight text-foreground">
                {title}
            </h2>
        </Reveal>
        {sub && (
            <Reveal delay={0.16}>
                <p className="mt-4 text-base text-muted-foreground leading-relaxed">{sub}</p>
            </Reveal>
        )}
    </div>
);

export const LogoMark = ({ size = 28 }) => (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
        <rect width="64" height="64" rx="14" className="fill-foreground" />
        <path
            d="M15 19 L24 45 L32 27 L40 45 L49 19"
            fill="none"
            className="stroke-brand"
            strokeWidth="4.5"
            strokeLinecap="round"
            strokeLinejoin="round"
        />
    </svg>
);
