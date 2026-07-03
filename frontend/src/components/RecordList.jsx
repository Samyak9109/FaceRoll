export function RecordList({ title, rows }) {
  return (
    <div className="record-list">
      {title && <h3>{title}</h3>}
      {rows.length ? rows.map((row) => <p key={row}>{row}</p>) : <p>No records yet.</p>}
    </div>
  );
}
