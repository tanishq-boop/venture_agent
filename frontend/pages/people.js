import { useEffect, useState } from "react";

export default function PeoplePage() {
  const [employees, setEmployees] = useState([]);
  const [error, setError] = useState(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  useEffect(() => {
    fetch(`${API_BASE}/employees?business_id=1`)
      .then((r) => r.json())
      .then(setEmployees)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>People</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      <ul>
        {employees.map((e) => (
          <li key={e.id}>{e.name} — {e.role} (${e.salary})</li>
        ))}
      </ul>
    </main>
  );
}
