import { useState } from "react";
import { createRoot } from "react-dom/client";

import { Login } from "./components/Login";
import { Dashboard } from "./Dashboard";
import "./styles.css";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  return token ? <Dashboard token={token} onLogout={() => setToken("")} /> : <Login onLogin={setToken} />;
}

createRoot(document.getElementById("root")).render(<App />);
