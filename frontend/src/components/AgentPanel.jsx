import { useState } from "react";
import { MessageSquare } from "lucide-react";

import { apiJson } from "../lib/api";

export function AgentPanel({ token }) {
  const [answer, setAnswer] = useState("");
  const [query, setQuery] = useState("Who was absent in CS101 today?");

  async function askAgent(event) {
    event.preventDefault();
    setAnswer("Thinking...");
    try {
      const data = await apiJson("/agent/query", { token, method: "POST", body: { query } });
      setAnswer(data.answer);
    } catch (error) {
      setAnswer(error.message);
    }
  }

  return (
    <form className="agent-panel" onSubmit={askAgent}>
      <h2><MessageSquare size={19} /> Attendance Chat</h2>
      <textarea value={query} onChange={(event) => setQuery(event.target.value)} />
      <button className="primary" type="submit">Ask agent</button>
      <pre>{answer}</pre>
    </form>
  );
}
