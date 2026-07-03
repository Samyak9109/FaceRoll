import { useEffect, useMemo, useState } from "react";
import { BookOpen, Download, RefreshCw, UserPlus, Users } from "lucide-react";

import { AgentPanel } from "./components/AgentPanel";
import { AttendanceTable } from "./components/AttendanceTable";
import { CameraPanel } from "./components/CameraPanel";
import { EnrollPanel } from "./components/EnrollPanel";
import { apiJson, downloadBlob } from "./lib/api";

export function Dashboard({ session, onLogout }) {
  const token = session.access_token;

  function signOut() {
    localStorage.removeItem("session");
    onLogout();
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <h1>Attendance Console</h1>
          <p>{session.user.name} · {session.role}</p>
        </div>
        <button className="ghost" onClick={signOut}>Sign out</button>
      </header>

      {session.role === "admin" && <AdminDashboard token={token} />}
      {session.role === "teacher" && <TeacherDashboard token={token} />}
      {session.role === "student" && <StudentDashboard token={token} />}
    </main>
  );
}

function AdminDashboard({ token }) {
  const [records, setRecords] = useState({ teachers: [], students: [], classes: [] });
  const [teacherForm, setTeacherForm] = useState({
    username: "",
    password: "",
    name: "",
    email: "",
    subject: "",
    assigned_classes: "",
  });
  const [classForm, setClassForm] = useState({ class_id: "", name: "", subject: "", teacher_id: "", schedule: "" });
  const [classId, setClassId] = useState("CS101");
  const [message, setMessage] = useState("");

  async function loadRecords() {
    setRecords(await apiJson("/admin/records", { token }));
  }

  useEffect(() => {
    loadRecords().catch((error) => setMessage(error.message));
  }, []);

  async function createTeacher(event) {
    event.preventDefault();
    const payload = {
      ...teacherForm,
      assigned_classes: teacherForm.assigned_classes.split(",").map((item) => item.trim()).filter(Boolean),
    };
    await apiJson("/admin/teachers", { token, method: "POST", body: payload });
    setTeacherForm({ username: "", password: "", name: "", email: "", subject: "", assigned_classes: "" });
    setMessage("Teacher created");
    await loadRecords();
  }

  async function createClass(event) {
    event.preventDefault();
    await apiJson("/admin/classes", {
      token,
      method: "POST",
      body: { ...classForm, teacher_id: classForm.teacher_id || null },
    });
    setClassForm({ class_id: "", name: "", subject: "", teacher_id: "", schedule: "" });
    setMessage("Class created");
    await loadRecords();
  }

  return (
    <>
      {message && <div className="notice success">{message}</div>}
      <section className="summary-grid">
        <Stat icon={<Users size={18} />} label="Teachers" value={records.teachers.length} />
        <Stat icon={<Users size={18} />} label="Students" value={records.students.length} />
        <Stat icon={<BookOpen size={18} />} label="Classes" value={records.classes.length} />
      </section>

      <section className="content-grid">
        <form className="panel" onSubmit={createTeacher}>
          <h2><UserPlus size={19} /> Add Teacher</h2>
          <label>Username<input value={teacherForm.username} onChange={(e) => setTeacherForm({ ...teacherForm, username: e.target.value })} required /></label>
          <label>Password<input type="password" value={teacherForm.password} onChange={(e) => setTeacherForm({ ...teacherForm, password: e.target.value })} required /></label>
          <label>Name<input value={teacherForm.name} onChange={(e) => setTeacherForm({ ...teacherForm, name: e.target.value })} required /></label>
          <label>Email<input value={teacherForm.email} onChange={(e) => setTeacherForm({ ...teacherForm, email: e.target.value })} /></label>
          <label>Subject<input value={teacherForm.subject} onChange={(e) => setTeacherForm({ ...teacherForm, subject: e.target.value })} required /></label>
          <label>Assigned Classes<input placeholder="CS101, CS102" value={teacherForm.assigned_classes} onChange={(e) => setTeacherForm({ ...teacherForm, assigned_classes: e.target.value })} /></label>
          <button className="primary">Create teacher</button>
        </form>

        <form className="panel" onSubmit={createClass}>
          <h2><BookOpen size={19} /> Add Class</h2>
          <label>Class ID<input value={classForm.class_id} onChange={(e) => setClassForm({ ...classForm, class_id: e.target.value })} required /></label>
          <label>Name<input value={classForm.name} onChange={(e) => setClassForm({ ...classForm, name: e.target.value })} required /></label>
          <label>Subject<input value={classForm.subject} onChange={(e) => setClassForm({ ...classForm, subject: e.target.value })} required /></label>
          <label>Teacher<select value={classForm.teacher_id} onChange={(e) => setClassForm({ ...classForm, teacher_id: e.target.value })}>
            <option value="">Unassigned</option>
            {records.teachers.map((teacher) => <option key={teacher._id} value={teacher._id}>{teacher.name}</option>)}
          </select></label>
          <label>Schedule<input value={classForm.schedule} onChange={(e) => setClassForm({ ...classForm, schedule: e.target.value })} /></label>
          <button className="primary">Create class</button>
        </form>
      </section>

      <section className="grid">
        <EnrollPanel token={token} defaultClassId={classId} />
        <div className="panel">
          <h2>Admin Records</h2>
          <label>Enrollment Class<input value={classId} onChange={(event) => setClassId(event.target.value)} /></label>
          <RecordList title="Teachers" rows={records.teachers.map((row) => `${row.name} · ${row.subject || "-"} · ${row.assigned_classes.join(", ") || "No classes"}`)} />
          <RecordList title="Students" rows={records.students.map((row) => `${row.roll_no} · ${row.name} · ${row.class_id}`)} />
          <RecordList title="Classes" rows={records.classes.map((row) => `${row.class_id} · ${row.name} · ${row.subject}`)} />
        </div>
      </section>
    </>
  );
}

function TeacherDashboard({ token }) {
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

  async function loadAttendance(targetClass = classId) {
    if (!targetClass) return;
    setAttendance(await apiJson(`/attendance/${targetClass}/${date}`, { token }));
    setSummary(await apiJson(`/teacher/dashboard?class_id=${targetClass}`, { token }));
  }

  useEffect(() => {
    loadClasses().catch((loadError) => setError(loadError.message));
  }, []);

  useEffect(() => {
    loadAttendance().catch((loadError) => setError(loadError.message));
  }, [classId, date]);

  async function exportReport() {
    const monthStart = `${date.slice(0, 8)}01`;
    const blob = await downloadBlob(`/report/${classId}?start_date=${monthStart}&end_date=${date}&format=csv`, token);
    const href = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = href;
    link.download = `${classId}-attendance.csv`;
    link.click();
    URL.revokeObjectURL(href);
  }

  return (
    <>
      {error && <div className="notice warning">{error}</div>}
      <section className="toolbar">
        <label>Class<select value={classId} onChange={(event) => setClassId(event.target.value)}>
          {classes.map((row) => <option key={row.class_id} value={row.class_id}>{row.class_id} · {row.subject}</option>)}
        </select></label>
        <label>Date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
        <button onClick={() => loadAttendance()}><RefreshCw size={17} /> Refresh</button>
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
          <CameraPanel token={token} classId={classId} onResult={(result) => { setRecognition(result); loadAttendance(); }} />
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

function StudentDashboard({ token }) {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiJson("/student/dashboard", { token }).then(setDashboard).catch((loadError) => setError(loadError.message));
  }, []);

  const missed = useMemo(() => {
    if (!dashboard) return [];
    return dashboard.missed_dates || [];
  }, [dashboard]);

  if (error) return <div className="notice warning">{error}</div>;
  if (!dashboard) return <div className="notice">Loading student dashboard...</div>;

  return (
    <>
      <section className="summary-grid">
        <Stat label="Classes Attended" value={dashboard.attended_count} icon={<BookOpen size={18} />} />
        <Stat label="Class" value={dashboard.student.class_id} icon={<Users size={18} />} />
        <Stat label="Missed Records" value={dashboard.missed_count} icon={<RefreshCw size={18} />} />
      </section>
      <section className="content-grid">
        <div className="panel">
          <h2>Attendance Records</h2>
          <RecordList rows={dashboard.records.map((row) => `${row.date} · ${row.class_id} · ${row.time} · ${row.status}`)} />
        </div>
        <div className="panel">
          <h2>Missed Classes</h2>
          <RecordList rows={missed.length ? missed.map((item) => `${dashboard.student.class_id} · ${item}`) : ["No missed class records"]} />
        </div>
      </section>
    </>
  );
}

function Stat({ icon, label, value }) {
  return (
    <div className="stat">
      {icon}
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RecordList({ title, rows }) {
  return (
    <div className="record-list">
      {title && <h3>{title}</h3>}
      {rows.length ? rows.map((row) => <p key={row}>{row}</p>) : <p>No records yet.</p>}
    </div>
  );
}
