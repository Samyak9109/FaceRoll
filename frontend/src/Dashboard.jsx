import { useEffect, useState } from "react";
import { Download, RefreshCw } from "lucide-react";

import { AgentPanel } from "./components/AgentPanel";
import { AttendanceTable } from "./components/AttendanceTable";
import { CameraPanel } from "./components/CameraPanel";
import { EnrollPanel } from "./components/EnrollPanel";
import { apiJson, downloadBlob } from "./lib/api";

export function Dashboard({ token, onLogout }) {
  const [classId, setClassId] = useState("CS101");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [attendance, setAttendance] = useState([]);
  const [recognition, setRecognition] = useState(null);
  const [error, setError] = useState("");

  async function loadAttendance() {
    try {
      setError("");
      setAttendance(await apiJson(`/attendance/${classId}/${date}`, { token }));
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  useEffect(() => {
    loadAttendance();
  }, [classId, date]);

  async function exportReport() {
    const monthStart = `${date.slice(0, 8)}01`;
    const path = `/report/${classId}?start_date=${monthStart}&end_date=${date}&format=csv`;
    try {
      const blob = await downloadBlob(path, token);
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = `${classId}-attendance.csv`;
      link.click();
      URL.revokeObjectURL(href);
    } catch (requestError) {
      setError(requestError.message);
    }
  }

  function signOut() {
    localStorage.removeItem("token");
    onLogout();
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Attendance Console</h1>
          <p>Local face recognition, encrypted embeddings, auditable attendance.</p>
        </div>
        <button className="ghost" onClick={signOut}>Sign out</button>
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
      {error && <div className="notice warning">{error}</div>}

      <section className="content-grid">
        <AttendanceTable rows={attendance} />
        <AgentPanel token={token} />
      </section>
    </main>
  );
}
