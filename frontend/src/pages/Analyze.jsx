import { useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import { useAuth } from "../AuthContext";
import ResultCard from "../components/ResultCard";
import { SAMPLES } from "../samples";

const MAX = 500;

export default function Analyze() {
  const { user } = useAuth();
  const [text, setText] = useState("");
  const [result, setResult] = useState(null);
  const [runId, setRunId] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const resultRef = useRef(null);

  async function submit(e) {
    e.preventDefault();
    if (!text.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      setResult(await api.predict(text));
      setRunId((n) => n + 1); // new key => the result animation replays
      requestAnimationFrame(() =>
        resultRef.current?.scrollIntoView({ behavior: "smooth", block: "start" })
      );
    } catch (err) {
      setResult(null);
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="intro">
        <h1>Was that headline<br />being serious?</h1>
        <p>
          Drop in a headline or a sentence. A neural network reads it word by word, gives its verdict, and marks the
          words that swayed it.
        </p>
      </section>

      <form className="desk" onSubmit={submit}>
        <label htmlFor="text" className="sr-only">Text to analyze</label>
        <textarea
          id="text"
          maxLength={MAX}
          value={text}
          placeholder="Local man shocked that deadline he ignored has arrived…"
          onChange={(e) => setText(e.target.value)}
        />
        <div className="desk-foot">
          <span className="label">{text.length} / {MAX}</span>
          <button className="btn" disabled={busy || !text.trim()}>
            {busy ? (
              <span className="busy-dots">Reading<span>.</span><span>.</span><span>.</span></span>
            ) : (
              "Analyze"
            )}
          </button>
        </div>

        <ul className="samples">
          {SAMPLES.map((s) => (
            <li key={s}>
              <button type="button" onClick={() => setText(s)}>{s}</button>
            </li>
          ))}
        </ul>
        {!user && (
          <p className="muted small" style={{ margin: "14px 0 0" }}>
            <Link to="/login">Sign in</Link> to keep a history of what you've analyzed.
          </p>
        )}
      </form>

      {error && <p className="error" role="alert">{error}</p>}
      <div ref={resultRef} style={{ scrollMarginTop: 12 }}>
        {result && <ResultCard key={runId} result={result} />}
      </div>
    </>
  );
}
