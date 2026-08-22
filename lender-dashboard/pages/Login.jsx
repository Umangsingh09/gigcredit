import { useState } from "react";

import { login, register } from "../src/data/api";

function Login({ onAuthenticated }) {
  const [mode, setMode] = useState("register");
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleChange = (event) => {
    setForm((current) => ({ ...current, [event.target.name]: event.target.value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setMessage("");
    try {
      const response = mode === "register" ? await register(form) : await login({ email: form.email, password: form.password });
      if (response.access_token) {
        onAuthenticated(response);
      } else {
        setMode("login");
        setMessage("Account created. Sign in with your email and password.");
      }
    } catch (error) {
      setMessage(error.message || "Unable to authenticate. Check your details and try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="auth-page">
      <div className="auth-shell">
        <div className="auth-aside"><span className="brand-mark">G</span><p className="eyebrow">LENDER PORTAL</p><h1>Make every decision with more context.</h1><p>Secure access to your applications, portfolio intelligence, and review workflow.</p></div>
        <form className="auth-card" onSubmit={handleSubmit}>
          <div className="auth-heading"><p className="eyebrow">{mode === "register" ? "NEW LENDER" : "RETURNING LENDER"}</p><h2>{mode === "register" ? "Create your account" : "Sign in to your workspace"}</h2><p>{mode === "register" ? "Enter your details to get started." : "Use your email and password to continue."}</p></div>
          {mode === "register" && <label>Full name<input name="full_name" type="text" value={form.full_name} onChange={handleChange} required autoComplete="name" placeholder="Umang Raj" /></label>}
          <label>Email address<input name="email" type="email" value={form.email} onChange={handleChange} required autoComplete="email" placeholder="you@example.com" /></label>
          <label>Password<input name="password" type="password" minLength="6" value={form.password} onChange={handleChange} required autoComplete={mode === "register" ? "new-password" : "current-password"} placeholder="At least 6 characters" /></label>
          {message && <p className="auth-message">{message}</p>}
          <button className="auth-submit" type="submit" disabled={submitting}>{submitting ? "Working..." : mode === "register" ? "Create account" : "Sign in"}<span>→</span></button>
          <p className="auth-switch">{mode === "register" ? "Already have an account?" : "New to GigCredit?"} <button type="button" onClick={() => { setMode(mode === "register" ? "login" : "register"); setMessage(""); }}>{mode === "register" ? "Sign in" : "Create account"}</button></p>
        </form>
      </div>
    </main>
  );
}

export default Login;
