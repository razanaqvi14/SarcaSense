import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../AuthContext";

export default function AuthForm({ mode }) {
  const isRegister = mode === "register";
  const { user, login, register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      await (isRegister ? register : login)(email, password);
      navigate("/");
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="sheet" onSubmit={submit}>
      <div>
        <div className="label" style={{ marginBottom: 10 }}>{isRegister ? "New reader" : "Returning reader"}</div>
        <h2>{isRegister ? "Start your history" : "Welcome back"}</h2>
      </div>
      <label>
        <span className="label">Email</span>
        <input type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
      </label>
      <label>
        <span className="label">Password</span>
        <input
          type="password"
          required
          minLength={isRegister ? 10 : 1}
          maxLength={128}
          autoComplete={isRegister ? "new-password" : "current-password"}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {isRegister && <span className="muted small">At least 10 characters.</span>}
      </label>
      {error && <p className="error" role="alert">{error}</p>}
      <button className="btn" disabled={busy}>
        {busy ? "One moment…" : isRegister ? "Create account" : "Sign in"}
      </button>
      <p className="muted small">
        {isRegister ? (
          <>Already registered? <Link to="/login">Sign in</Link></>
        ) : (
          <>First time here? <Link to="/register">Create an account</Link></>
        )}
      </p>
    </form>
  );
}
