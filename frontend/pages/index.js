import Link from "next/link";

export default function Home() {
  return (
    <main style={{ padding: 24, fontFamily: "sans-serif" }}>
      <h1>Venture Agent Prototype</h1>
      <p>An autonomous business advisor for small and medium-sized businesses.</p>
      <ul>
        <li><Link href="/business">Business</Link></li>
        <li><Link href="/ventures">Ventures</Link></li>
        <li><Link href="/people">People</Link></li>
        <li><Link href="/finance">Finance</Link></li>
      </ul>
    </main>
  );
}
