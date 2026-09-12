import { useEffect, useState } from "react";

/** Placeholder shell. Proves the frontend can reach the API through Caddy. */
export function App() {
  const [status, setStatus] = useState("checking...");

  useEffect(() => {
    fetch("/api/health")
      .then((r) => r.json())
      .then((d: { status: string }) => setStatus(d.status))
      .catch(() => setStatus("unreachable"));
  }, []);

  return (
    <main>
      <h1>hackrice</h1>
      <p>api: {status}</p>
    </main>
  );
}
