"use client";

import { FormEvent, useState } from "react";
import { useSearchParams } from "next/navigation";

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const token = params.get("token") || "";
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setError("");
    setMessage("");
    const apiBase = typeof window !== "undefined" ? `http://${window.location.hostname}:8000` : "http://localhost:8000";
    const response = await fetch(`${apiBase}/api/auth/reset-password`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token, password }),
    });
    const body = await response.json();
    if (!response.ok) setError(body.detail || "This reset link is invalid or expired.");
    else setMessage(body.message);
  };

  return <main className="auth-gate"><div className="auth-gate-glow" /><section className="auth-gate-card"><div className="brand auth-brand"><div className="brand-mark">✦</div><div><strong>AlphaSage</strong><span>INVESTMENT INTELLIGENCE</span></div></div><div className="kicker">ACCOUNT SECURITY</div><h1>Reset password</h1><p className="auth-gate-copy">Choose a new password for your AlphaSage workspace.</p><form onSubmit={submit}><label>New password<input type="password" minLength={8} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" /></label>{error && <p className="auth-error">{error}</p>}{message && <p className="auth-notice">{message}</p>}<button className="primary auth-submit" type="submit">Update password</button></form></section></main>;
}
