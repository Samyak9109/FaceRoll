import { useEffect, useMemo, useState } from "react";
import { BookOpen, RefreshCw, Users } from "lucide-react";

import { RecordList } from "../components/RecordList";
import { Stat } from "../components/Stat";
import { apiJson } from "../lib/api";

export function StudentDashboard({ token }) {
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
