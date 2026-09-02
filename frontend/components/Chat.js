import { useState } from "react";
import { api } from "../lib/api";

export default function Chat({ businessId = 1 }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function send() {
    if (!input.trim()) return;
    const userMsg = { role: "user", text: input };
    setMessages((m) => [...m, userMsg]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.chat(businessId, userMsg.text);
      setMessages((m) => [...m, { role: "agent", text: res.reply }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "agent", text: `Error: ${e.message}` }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ border: "1px solid #ccc", padding: 12, marginTop: 24 }}>
      <h3>Chat with the agent</h3>
      <div style={{ minHeight: 120, marginBottom: 8 }}>
        {messages.map((m, i) => (
          <p key={i}>
            <strong>{m.role === "user" ? "You" : "Agent"}:</strong> {m.text}
          </p>
        ))}
        {loading && <p><em>Agent is thinking...</em></p>}
      </div>
      <input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && send()}
        placeholder="Ask the agent something..."
        style={{ width: "70%" }}
      />
      <button onClick={send} disabled={loading}>Send</button>
    </div>
  );
}
