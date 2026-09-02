import { useEffect, useState } from "react";

export default function FinancePage() {
  const [finance, setFinance] = useState(null);
  const [error, setError] = useState(null);
  const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

  useEffect(() => {
    fetch(`${API_BASE}/finance?business_id=1`)
      .then((r) => r.json())
      .then(setFinance)
      .catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Finance</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {finance && (
        <table>
          <tbody>
            <tr><td>Revenue</td><td>{finance.revenue}</td></tr>
            <tr><td>Expenses</td><td>{finance.expenses}</td></tr>
            <tr><td>Profit</td><td>{finance.profit}</td></tr>
            <tr><td>Cash</td><td>{finance.cash}</td></tr>
            <tr><td>Debt</td><td>{finance.debt}</td></tr>
          </tbody>
        </table>
      )}
    </main>
  );
}
