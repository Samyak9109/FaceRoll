import { useEffect, useState } from "react";
import { Download, RefreshCw, Users } from "lucide-react";

import { AgentPanel } from "../components/AgentPanel";
import { AttendanceTable } from "../components/AttendanceTable";
import { CameraPanel } from "../components/CameraPanel";
import { RecordList } from "../components/RecordList";
import { Stat } from "../components/Stat";
import { apiJson, downloadBlob } from "../lib/api";

export function TeacherDashboard({ token }) {
  const [classes, setClasses] = useState([]);
  const [classId, setClassId] = useState("");
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [attendance, setAttendance] = useState([]);
  const [summary, setSummary] = useState({ classes: [], daily: [] });
  const [recognition, setRecognition] = useState(null);
  const [error, setError] = useState("");
  const [sessionStarted, setSessionStarted] = useState(false);

  async function loadClasses() {
    const rows = await apiJson("/teacher/classes", { token });
    setClasses(rows);
    if (!classId && rows.length) setClassId(rows[0].class_id);
  }

  async function loadDashboard(targetClass = classId) {
    if (!targetClass) return;
    const payload = await apiJson(`/teacher/dashboard?class_id=${targetClass}&attendance_date=${date}`, { token });
    setSummary({ classes: payload.classes, daily: payload.daily });
    setAttendance(payload.attendance);
  }

  useEffect(() => {
    loadClasses().catch((loadError) => setError(loadError.message));
  }, []);

  useEffect(() => {
    loadDashboard().catch((loadError) => setError(loadError.message));
  }, [classId, date]);

  async function exportReport() {
    try {
      const monthStart = `${date.slice(0, 8)}01`;
      const blob = await downloadBlob(`/report/${classId}?start_date=${monthStart}&end_date=${date}&format=csv`, token);
      const href = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = href;
      link.download = `${classId}-attendance.csv`;
      link.click();
      URL.revokeObjectURL(href);
    } catch (downloadError) {
      setError(downloadError.message);
    }
  }

  return (
    <>
      {error && <div className="notice warning">{error}</div>}
      <section className="toolbar">
        <label>Class<select value={classId} onChange={(event) => setClassId(event.target.value)}>
          {classes.map((row) => <option key={row.class_id} value={row.class_id}>{row.class_id} · {row.subject}</option>)}
        </select></label>
        <label>Date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
        <button onClick={() => loadDashboard()}><RefreshCw size={17} /> Refresh</button>
        <button onClick={exportReport}><Download size={17} /> Export</button>
        <button className={sessionStarted ? "danger" : "primary"} onClick={() => setSessionStarted((current) => !current)}>
          {sessionStarted ? "Stop attendance" : "Start attendance"}
        </button>
      </section>

      <section className="summary-grid">
        {summary.classes.map((row) => (
          <Stat key={row.class_id} label={row.class_id} value={`${row.present_today}/${row.students}`} icon={<Users size={18} />} />
        ))}
      </section>

      <div className="grid">
        {sessionStarted ? (
          <CameraPanel token={token} classId={classId} onResult={(result) => { setRecognition(result); loadDashboard(); }} />
        ) : (
          <div className="panel">
            <h2>Attendance Session</h2>
            <p>Select a class and start attendance to enable camera recognition for that class.</p>
          </div>
        )}
        <div className="panel">
          <h2>Day-wise Analysis</h2>
          <RecordList rows={summary.daily.map((row) => `${row.date} · ${row.class_id} · ${row.present} present`)} />
        </div>
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
        <AgentPanel token={token} />
      </section>
    </>
  );
}
