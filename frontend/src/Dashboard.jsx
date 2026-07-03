import { AdminDashboard } from "./dashboards/AdminDashboard";
import { StudentDashboard } from "./dashboards/StudentDashboard";
import { TeacherDashboard } from "./dashboards/TeacherDashboard";

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
