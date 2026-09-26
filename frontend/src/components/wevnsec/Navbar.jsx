import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { Moon, Sun, Menu, X, ArrowRight, LayoutDashboard } from "lucide-react";
import { LogoMark } from "./Reveal";
import { useAuth } from "@/context/AuthContext";

const LINKS = [
    { label: "Product", hash: "#how-it-works" },
    { label: "Docs", hash: "#docs" },
    { label: "Pricing", hash: "#pricing" },
    { label: "Changelog", route: "/changelog" },
];

const scrollToEl = (hash) => {
    if (window.__lenis) window.__lenis.scrollTo(hash, { offset: -72 });
    else document.querySelector(hash)?.scrollIntoView({ behavior: "smooth" });
};

export const Navbar = ({ theme, onToggleTheme }) => {
    const [scrolled, setScrolled] = useState(false);
    const [open, setOpen] = useState(false);
    const { user } = useAuth();
    const navigate = useNavigate();
    const location = useLocation();

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 12);
        onScroll();
        window.addEventListener("scroll", onScroll, { passive: true });
        return () => window.removeEventListener("scroll", onScroll);
    }, []);

    const go = (link) => {
        setOpen(false);
        if (link.route) {
            navigate(link.route);
            return;
        }
        if (location.pathname !== "/") {
            navigate("/");
            setTimeout(() => scrollToEl(link.hash), 400);
        } else {
            scrollToEl(link.hash);
        }
    };

    const goScan = () => {
        setOpen(false);
        if (location.pathname !== "/") {
            navigate("/");
            setTimeout(() => scrollToEl("#top"), 400);
        } else {
            scrollToEl("#top");
        }
    };

    return (
        <motion.header
            data-testid="wevnsec-navbar"
            initial={{ y: -64, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1] }}
            className={`fixed top-0 inset-x-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-300 ${
                scrolled
                    ? "bg-background/80 backdrop-blur-xl border-b border-border"
                    : "bg-transparent border-b border-transparent"
            }`}
        >
            <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4" aria-label="Main navigation" data-testid="main-navigation">
                <button
                    onClick={() => { setOpen(false); location.pathname !== "/" ? navigate("/") : scrollToEl("#top"); }}
                    className="flex items-center gap-2.5 shrink-0"
                    aria-label="WevnSec home"
                    data-testid="nav-logo"
                >
                    <LogoMark size={26} />
                    <span className="text-[17px] font-semibold tracking-tight text-foreground">
                        wevn<span className="text-brand">sec</span>
                    </span>
                </button>

                <div className="hidden lg:flex items-center justify-center gap-1 mx-auto" data-testid="nav-desktop-links">
                    {LINKS.map((l) => (
                        <button
                            key={l.label}
                            onClick={() => go(l)}
                            className="px-3.5 py-2 text-sm whitespace-nowrap text-muted-foreground hover:text-foreground rounded-md hover:bg-accent/60 transition-colors duration-200"
                            data-testid={`nav-link-${l.label.toLowerCase()}`}
                        >
                            {l.label}
                        </button>
                    ))}
                </div>

                <div className="flex items-center gap-2 shrink-0">
                    <button
                        data-testid="theme-toggle-button"
                        onClick={onToggleTheme}
                        aria-label="Toggle theme"
                        className="h-9 w-9 rounded-md border border-border flex items-center justify-center text-muted-foreground hover:text-foreground hover:border-brand/50 transition-colors duration-200"
                    >
                        {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
                    </button>
                    {user ? (
                        <button
                            onClick={() => navigate("/dashboard")}
                            className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                            data-testid="nav-dashboard-link"
                        >
                            <LayoutDashboard size={14} />
                            Dashboard
                        </button>
                    ) : (
                        <button
                            onClick={() => navigate("/signin")}
                            className="hidden sm:block px-3.5 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors duration-200"
                            data-testid="nav-sign-in"
                        >
                            Sign in
                        </button>
                    )}
                    <button
                        data-testid="nav-start-scan-button"
                        onClick={goScan}
                        className="hidden sm:flex items-center gap-1.5 h-9 px-4 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-sm font-medium hover:brightness-110 hover:shadow-[0_0_24px_-6px_hsl(var(--brand)/0.6)] transition-all duration-200"
                    >
                        Start free scan
                        <ArrowRight size={14} />
                    </button>
                    <button
                        className="lg:hidden h-9 w-9 rounded-md border border-border flex items-center justify-center text-foreground"
                        onClick={() => setOpen((v) => !v)}
                        aria-label={open ? "Close menu" : "Open menu"}
                        aria-expanded={open}
                        aria-controls="mobile-navigation"
                        data-testid="nav-mobile-menu-button"
                    >
                        {open ? <X size={16} /> : <Menu size={16} />}
                    </button>
                </div>
            </nav>

            <AnimatePresence>
                {open && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                        id="mobile-navigation"
                        data-testid="nav-mobile-links"
                        className="lg:hidden overflow-hidden border-b border-border bg-background/95 backdrop-blur-xl"
                    >
                        <div className="px-4 py-3 flex flex-col gap-1">
                            {LINKS.map((l) => (
                                <button
                                    key={l.label}
                                    onClick={() => go(l)}
                                    className="text-left px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent/60"
                                    data-testid={`nav-mobile-link-${l.label.toLowerCase()}`}
                                >
                                    {l.label}
                                </button>
                            ))}
                            <button
                                onClick={() => { setOpen(false); navigate(user ? "/dashboard" : "/signin"); }}
                                className="text-left px-3 py-2.5 text-sm text-muted-foreground hover:text-foreground rounded-md hover:bg-accent/60"
                                data-testid="nav-mobile-auth-link"
                            >
                                {user ? "Dashboard" : "Sign in"}
                            </button>
                            <button
                                data-testid="nav-mobile-start-scan-button"
                                onClick={goScan}
                                className="mt-2 flex items-center justify-center gap-1.5 h-10 rounded-md bg-brand text-[hsl(var(--primary-foreground))] text-sm font-medium"
                            >
                                Start free scan
                                <ArrowRight size={14} />
                            </button>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.header>
    );
};
