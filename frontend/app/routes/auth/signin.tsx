import React, { useState } from "react";
import { useNavigate } from "react-router";

export default function SignIn() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await fetch("/auth/signin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.message || "Signin failed");
      if (data.token) {
        localStorage.setItem("token", data.token);
      }
      navigate("/");
    } catch (err: any) {
      setError(err?.message || String(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="container mx-auto px-4 py-24 max-w-md">
      <h1 className="text-2xl font-semibold mb-4">Sign in</h1>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input type="email" className="mt-1 block w-full rounded-md border px-3 py-2" value={email} onChange={(e) => setEmail(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm font-medium">Password</label>
          <input type="password" className="mt-1 block w-full rounded-md border px-3 py-2" value={password} onChange={(e) => setPassword(e.target.value)} />
        </div>

        {error && <div className="text-red-600">{error}</div>}

        <div>
          <button type="submit" className="w-full px-4 py-2 bg-blue-600 text-white rounded-md" disabled={loading}>
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </div>
      </form>
    </div>
  );
}
