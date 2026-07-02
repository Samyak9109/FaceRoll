import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Camera,
  Download,
  LogIn,
  MessageSquare,
  RefreshCw,
  ShieldCheck,
  Upload,
  UserPlus,
} from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  return token ? <Dashboard token={token} onLogout={() => setToken("")} /> : <Login onLogin={setToken} />;
}

function Login({ onLogin }) {
  const [username, setUsername] = useState("teacher");
  const [password, setPassword] = useState("teacher123");
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      setError("Invalid credentials");
      return;
    }
    const data = await response.json();
    localStorage.setItem("token", data.access_token);
    onLogin(data.access_token);
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
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {error && <p className="error">{error}</p>}
        <button className="primary" type="submit">
          <LogIn size={18} /> Sign in
        </button>
      </form>
    </main>
  );
}

function Dashboard({ token, onLogout }) {
  const [classId, setClassId] = useState("CS101");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [attendance, setAttendance] = useState([]);
  const [recognition, setRecognition] = useState(null);
  const [agentAnswer, setAgentAnswer] = useState("");
  const [agentQuery, setAgentQuery] = useState("Who was absent in CS101 today?");
  const authHeaders = { Authorization: `Bearer ${token}` };

  async function loadAttendance() {
    const response = await fetch(`${API_BASE}/attendance/${classId}/${date}`, { headers: authHeaders });
    if (response.ok) setAttendance(await response.json());
  }

  useEffect(() => {
    loadAttendance();
  }, [classId, date]);

  async function askAgent(event) {
    event.preventDefault();
    setAgentAnswer("Thinking...");
    const response = await fetch(`${API_BASE}/agent/query`, {
      method: "POST",
      headers: { ...authHeaders, "Content-Type": "application/json" },
      body: JSON.stringify({ query: agentQuery }),
    });
    const data = await response.json();
    setAgentAnswer(response.ok ? data.answer : data.detail || "Agent request failed");
  }

  function exportReport() {
    const start = new Date(date);
    start.setDate(1);
    const url = `${API_BASE}/report/${classId}?start_date=${start.toISOString().slice(0, 10)}&end_date=${date}&format=csv`;
    fetch(url, { headers: authHeaders })
      .then((response) => response.blob())
      .then((blob) => {
        const href = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = href;
        link.download = `${classId}-attendance.csv`;
        link.click();
        URL.revokeObjectURL(href);
      });
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Attendance Console</h1>
          <p>Local face recognition, encrypted embeddings, auditable attendance.</p>
        </div>
        <button className="ghost" onClick={() => { localStorage.removeItem("token"); onLogout(); }}>Sign out</button>
      </header>

      <section className="toolbar">
        <label>
          Class
          <input value={classId} onChange={(event) => setClassId(event.target.value)} />
        </label>
        <label>
          Date
          <input type="date" value={date} onChange={(event) => setDate(event.target.value)} />
        </label>
        <button onClick={loadAttendance}>
          <RefreshCw size={17} /> Refresh
        </button>
        <button onClick={exportReport}>
          <Download size={17} /> Export
        </button>
      </section>

      <div className="grid">
        <CameraPanel token={token} classId={classId} onResult={(result) => { setRecognition(result); loadAttendance(); }} />
        <EnrollPanel token={token} defaultClassId={classId} />
      </div>

      {recognition && (
        <div className={recognition.matched ? "notice success" : "notice warning"}>
          {recognition.message}
          {recognition.student ? `: ${recognition.student.name} (${recognition.student.roll_no})` : ""}
          {typeof recognition.score === "number" ? `, score ${recognition.score.toFixed(3)}` : ""}
        </div>
      )}

      <section className="content-grid">
        <AttendanceTable rows={attendance} />
        <form className="agent-panel" onSubmit={askAgent}>
          <h2><MessageSquare size={19} /> Attendance Chat</h2>
          <textarea value={agentQuery} onChange={(event) => setAgentQuery(event.target.value)} />
          <button className="primary" type="submit">Ask agent</button>
          <pre>{agentAnswer}</pre>
        </form>
      </section>
    </main>
  );
}

function CameraPanel({ token, classId, onResult }) {
  const videoRef = useRef(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    navigator.mediaDevices?.getUserMedia({ video: true }).then((stream) => {
      if (videoRef.current) videoRef.current.srcObject = stream;
    }).catch(() => setStatus("Camera permission is required."));
  }, []);

  async function recognize() {
    const video = videoRef.current;
    if (!video) return;
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    const blob = await new Promise((resolve) => canvas.toBlob(resolve, "image/jpeg", 0.92));
    const form = new FormData();
    form.append("class_id", classId);
    form.append("frame", blob, "frame.jpg");
    const response = await fetch(`${API_BASE}/recognize`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: form,
    });
    const data = await response.json();
    if (!response.ok) setStatus(data.detail || "Recognition failed");
    else onResult(data);
  }

  return (
    <section className="panel">
      <h2><Camera size={19} /> Live Recognition</h2>
      <video ref={videoRef} autoPlay playsInline muted />
      <button className="primary" onClick={recognize}>Recognize & mark</button>
      {status && <p className="error">{status}</p>}
    </section>
  );
}

function EnrollPanel({ token, defaultClassId }) {
  const [form, setForm] = useState({ name: "", roll_no: "", class_id: defaultClassId, consent: true });
  const [photo, setPhoto] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => setForm((current) => ({ ...current, class_id: defaultClassId })), [defaultClassId]);

  async function enroll(event) {
    event.preventDefault();
    const data = new FormData();
    Object.entries(form).forEach(([key, value]) => data.append(key, value));
    data.append("photo", photo);
    const response = await fetch(`${API_BASE}/enroll`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      body: data,
    });
    const payload = await response.json();
    setMessage(response.ok ? `Enrolled ${payload.name}` : payload.detail || "Enrollment failed");
  }

  return (
    <form className="panel enroll" onSubmit={enroll}>
      <h2><UserPlus size={19} /> Student Enrollment</h2>
      <label>Name<input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} required /></label>
      <label>Roll No<input value={form.roll_no} onChange={(e) => setForm({ ...form, roll_no: e.target.value })} required /></label>
      <label>Class<input value={form.class_id} onChange={(e) => setForm({ ...form, class_id: e.target.value })} required /></label>
      <label className="check"><input type="checkbox" checked={form.consent} onChange={(e) => setForm({ ...form, consent: e.target.checked })} /> Consent captured</label>
      <label className="file"><Upload size={17} /> Photo<input type="file" accept="image/*" onChange={(e) => setPhoto(e.target.files[0])} required /></label>
      <button className="primary" type="submit">Enroll</button>
      {message && <p>{message}</p>}
    </form>
  );
}

function AttendanceTable({ rows }) {
  return (
    <section className="table-panel">
      <h2>Attendance</h2>
      <table>
        <thead><tr><th>Roll</th><th>Name</th><th>Date</th><th>Time</th><th>Status</th></tr></thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row._id}>
              <td>{row.roll_no || "-"}</td>
              <td>{row.name || row.student_id}</td>
              <td>{row.date}</td>
              <td>{row.time}</td>
              <td><span className="pill">{row.status}</span></td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan="5">No attendance marked for this date.</td></tr>}
        </tbody>
      </table>
    </section>
  );
}

createRoot(document.getElementById("root")).render(<App />);
