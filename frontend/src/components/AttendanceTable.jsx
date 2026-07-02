export function AttendanceTable({ rows }) {
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
