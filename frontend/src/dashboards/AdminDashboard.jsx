import { useEffect, useState } from "react";
import { BookOpen, UserPlus, Users } from "lucide-react";

import { EnrollPanel } from "../components/EnrollPanel";
import { RecordList } from "../components/RecordList";
import { Stat } from "../components/Stat";
import { apiJson } from "../lib/api";

export function AdminDashboard({ token }) {
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
    try {
      const payload = {
        ...teacherForm,
        assigned_classes: teacherForm.assigned_classes.split(",").map((item) => item.trim()).filter(Boolean),
      };
      await apiJson("/admin/teachers", { token, method: "POST", body: payload });
      setTeacherForm({ username: "", password: "", name: "", email: "", subject: "", assigned_classes: "" });
      setMessage("Teacher created");
      await loadRecords();
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function createClass(event) {
    event.preventDefault();
    try {
      await apiJson("/admin/classes", {
        token,
        method: "POST",
        body: { ...classForm, teacher_id: classForm.teacher_id || null },
      });
      setClassForm({ class_id: "", name: "", subject: "", teacher_id: "", schedule: "" });
      setMessage("Class created");
      await loadRecords();
    } catch (error) {
      setMessage(error.message);
    }
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
