import { useEffect, useState } from "react";
import { api } from "../lib/api";
import Chat from "../components/Chat";

export default function BusinessPage() {
  const [business, setBusiness] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api.getBusiness(1).then(setBusiness).catch((e) => setError(e.message));
  }, []);

  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Business</h1>
      {error && <p style={{ color: "red" }}>{error}</p>}
      {business && (
        <table>
          <tbody>
            <tr><td>Name</td><td>{business.name}</td></tr>
            <tr><td>Industry</td><td>{business.industry}</td></tr>
            <tr><td>Location</td><td>{business.location}</td></tr>
            <tr><td>Revenue</td><td>{business.revenue}</td></tr>
            <tr><td>Expenses</td><td>{business.expenses}</td></tr>
            <tr><td>Profit</td><td>{business.profit}</td></tr>
            <tr><td>Cash</td><td>{business.cash}</td></tr>
          </tbody>
        </table>
      )}
      <Chat businessId={1} />
    </main>
  );
}
