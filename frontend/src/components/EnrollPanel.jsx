import { useEffect, useState } from "react";
import { Upload, UserPlus } from "lucide-react";

import { apiForm } from "../lib/api";

export function EnrollPanel({ token, defaultClassId }) {
  const [form, setForm] = useState({ name: "", roll_no: "", class_id: defaultClassId, consent: true });
  const [photo, setPhoto] = useState(null);
  const [message, setMessage] = useState("");

  useEffect(() => setForm((current) => ({ ...current, class_id: defaultClassId })), [defaultClassId]);

  async function enroll(event) {
    event.preventDefault();
    const data = new FormData();
    Object.entries(form).forEach(([key, value]) => data.append(key, value));
    data.append("photo", photo);

    try {
      const payload = await apiForm("/enroll", data, token);
      setMessage(`Enrolled ${payload.name}`);
    } catch (error) {
      setMessage(error.message);
    }
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
