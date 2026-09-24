import { useEffect, useState } from "react";
import Lenis from "lenis";
import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import "@/App.css";
import { AuthProvider } from "@/context/AuthContext";
import { Navbar } from "@/components/wevnsec/Navbar";
import { Footer } from "@/components/wevnsec/Footer";
import Landing from "@/pages/Landing";
import Report from "@/pages/Report";
import Auth from "@/pages/Auth";
import Dashboard from "@/pages/Dashboard";
import Changelog from "@/pages/Changelog";

const ScrollToTop = () => {
    const { pathname } = useLocation();
    useEffect(() => {
        if (window.__lenis) window.__lenis.scrollTo(0, { immediate: true });
        else window.scrollTo(0, 0);
    }, [pathname]);
    return null;
};

const SiteHeader = (props) => useLocation().pathname.startsWith("/dashboard") ? null : <Navbar {...props} />;
const SiteFooter = () => useLocation().pathname.startsWith("/dashboard") ? null : <Footer />;

function App() {
    const [theme, setTheme] = useState("dark");

    useEffect(() => {
        const stored = localStorage.getItem("wevnsec-theme");
        const t = stored === "light" ? "light" : "dark";
        setTheme(t);
        document.documentElement.classList.toggle("dark", t === "dark");
    }, []);

    useEffect(() => {
        const lenis = new Lenis({
            duration: 1.15,
            easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
            smoothWheel: true,
        });
        window.__lenis = lenis;
        let raf;
        const loop = (time) => {
            lenis.raf(time);
            raf = requestAnimationFrame(loop);
        };
        raf = requestAnimationFrame(loop);
        return () => {
            cancelAnimationFrame(raf);
            lenis.destroy();
            window.__lenis = null;
        };
    }, []);

    const toggleTheme = () => {
        const next = theme === "dark" ? "light" : "dark";
        setTheme(next);
        document.documentElement.classList.toggle("dark", next === "dark");
        localStorage.setItem("wevnsec-theme", next);
    };

    return (
        <AuthProvider>
            <BrowserRouter>
                <ScrollToTop />
                <div className="min-h-screen bg-background text-foreground antialiased overflow-x-clip">
                    <SiteHeader theme={theme} onToggleTheme={toggleTheme} />
                    <Routes>
                        <Route path="/" element={<Landing />} />
                        <Route path="/report/:id" element={<Report />} />
                        <Route path="/signin" element={<Auth key="signin" mode="signin" />} />
                        <Route path="/signup" element={<Auth key="signup" mode="signup" />} />
                        <Route path="/dashboard/*" element={<Dashboard theme={theme} onToggleTheme={toggleTheme} />} />
                        <Route path="/changelog" element={<Changelog />} />
                    </Routes>
                    <SiteFooter />
                </div>
                <Toaster position="bottom-right" theme={theme} />
            </BrowserRouter>
        </AuthProvider>
    );
}

export default App;
