import { useState } from "react";
import { LogIn, ShieldCheck } from "lucide-react";

import { apiJson } from "../lib/api";

export function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    try {
      const data = await apiJson("/auth/login", { method: "POST", body: { username, password } });
      localStorage.setItem("session", JSON.stringify(data));
      onLogin(data);
    } catch {
      setError("Invalid credentials");
    }
  }

  return (
    <main className="login-shell">
      <form className="login-panel" onSubmit={submit}>
        <div className="brand-mark">
          <ShieldCheck size={28} />
        </div>
        <h1>Face Attendance</h1>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} autoComplete="username" />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} autoComplete="current-password" />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit">
          <LogIn size={18} /> Sign in
        </button>
      </form>
    </main>
  );
}
