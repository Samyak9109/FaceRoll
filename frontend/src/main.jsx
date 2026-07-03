import { useState } from "react";
import { createRoot } from "react-dom/client";

import { Login } from "./components/Login";
import { Dashboard } from "./Dashboard";
import "./styles.css";

function App() {
  const [session, setSession] = useState(() => {
    const stored = localStorage.getItem("session");
    return stored ? JSON.parse(stored) : null;
  });
  return session ? <Dashboard session={session} onLogout={() => setSession(null)} /> : <Login onLogin={setSession} />;
}

createRoot(document.getElementById("root")).render(<App />);
