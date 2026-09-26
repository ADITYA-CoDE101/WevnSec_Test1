import { createContext, useContext, useEffect, useState } from "react";
import { api } from "@/lib/api";

const AuthCtx = createContext(null);

export const useAuth = () => useContext(AuthCtx);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(undefined);

    useEffect(() => {
        const token = localStorage.getItem("wevnsec-token");
        if (!token) {
            setUser(null);
            return;
        }
        api.get("/auth/me")
            .then((r) => setUser(r.data))
            .catch(() => {
                localStorage.removeItem("wevnsec-token");
                setUser(null);
            });
    }, []);

    const login = async (email, password) => {
        const { data } = await api.post("/auth/login", { email, password });
        localStorage.setItem("wevnsec-token", data.token);
        setUser(data.user);
    };

    const signup = async (name, email, password) => {
        const { data } = await api.post("/auth/register", { name, email, password });
        localStorage.setItem("wevnsec-token", data.token);
        setUser(data.user);
    };

    const logout = () => {
        localStorage.removeItem("wevnsec-token");
        api.post("/auth/logout").catch(() => {});
        setUser(null);
    };

    return <AuthCtx.Provider value={{ user, login, signup, logout }}>{children}</AuthCtx.Provider>;
};
