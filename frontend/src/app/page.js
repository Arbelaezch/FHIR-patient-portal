"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(err => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen p-8">
      <h1 className="text-4xl font-bold mb-8">FHIR Patient Portal</h1>
      
      <div className="border rounded p-4 max-w-md">
        <h2 className="text-xl font-semibold mb-2">Backend Status</h2>
        {error && <p className="text-red-600">Error: {error}</p>}
        {health && <p className="text-green-600">✓ Backend is {health.status}</p>}
        {!health && !error && <p>Connecting...</p>}
      </div>
    </div>
  );
}