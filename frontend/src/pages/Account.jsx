import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";

export default function Account() {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function remove(e) {
    e.preventDefault();
    if (!window.confirm("Permanently delete your account and all history?")) return;
    setBusy(true);
    setError("");
    try {
      await api.deleteAccount(password);
      setUser(null);
      navigate("/");
    } catch (err) {
      setError(err.message);
      setBusy(false);
    }
  }

  return (
    <>
      <div className="label" style={{ marginBottom: 10 }}>Subscriber details</div>
      <h1>Account</h1>
      <div className="facts">
        <div><span className="label">Email</span><p>{user.email}</p></div>
        <div><span className="label">Reading since</span><p>{new Date(user.created_at).toLocaleDateString()}</p></div>
      </div>

      <form className="sheet wide" onSubmit={remove}>
        <h2>Cancel subscription</h2>
        <p className="muted">
          This permanently removes your account and every saved analysis. Enter your password to confirm.
        </p>
        <label>
          <span className="label">Password</span>
          <input type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn danger" disabled={busy}>Delete my account</button>
      </form>
    </>
  );
}
