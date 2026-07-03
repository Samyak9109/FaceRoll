import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { Login } from "./components/Login";
import { Dashboard } from "./Dashboard";
import { apiJson } from "./lib/api";
import "./styles.css";

function App() {
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem("session");
    return stored ? JSON.parse(stored) : null;
  });

  useEffect(() => {
    if (!session?.access_token) return;
    apiJson("/auth/me", { token: session.access_token })
      .then((user) => setSession((current) => current ? { ...current, user, role: user.role } : current))
      .catch(() => {
        localStorage.removeItem("session");
        setSession(null);
      });
  }, [session?.access_token]);

  return session ? <Dashboard session={session} onLogout={() => setSession(null)} /> : <Login onLogin={setSession} />;
}

createRoot(document.getElementById("root")).render(<App />);
