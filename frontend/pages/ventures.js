import { useEffect, useState } from "react";
import { api } from "../lib/api";
import Chat from "../components/Chat";

export default function VenturesPage() {
  const [ventures, setVentures] = useState([]);
  const [evaluating, setEvaluating] = useState(null);
  const [error, setError] = useState(null);

  function load() {
    api.getVentures(1).then(setVentures).catch((e) => setError(e.message));
  }

  useEffect(() => {
    load();
  }, []);

  async function evaluate(ventureId) {
    setEvaluating(ventureId);
    try {
      await api.evaluateVenture(ventureId);
      load();
    } catch (e) {
      setError(e.message);
    } finally {
      setEvaluating(null);
    }
  }

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Ventures</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {ventures.map((v) => (
        <div key={v.id} style={{ border: "1px solid #ddd", padding: 12, marginBottom: 12 }}>
          <p><strong>Objective:</strong> {v.objective}</p>
          <p><strong>Budget:</strong> {v.budget}</p>
          <p><strong>Status:</strong> {v.status}</p>
          <button onClick={() => evaluate(v.id)} disabled={evaluating === v.id}>
            {evaluating === v.id ? "Evaluating..." : "Evaluate Venture"}
          </button>
          {v.recommendation && (
            <div style={{ marginTop: 8 }}>
              <strong>Agent Recommendation:</strong>
              <p>{v.recommendation}</p>
            </div>
          )}
        </div>
      ))}
      <Chat businessId={1} />
    </main>
  );
}
