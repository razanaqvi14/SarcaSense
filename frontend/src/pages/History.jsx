import { useCallback, useEffect, useState } from "react";
import { api } from "../api";

const PAGE = 10;

export default function History() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [page, s] = await Promise.all([api.history(PAGE, offset), api.stats()]);
      // If the last item of a page was deleted, step back a page.
      if (page.items.length === 0 && offset > 0) return setOffset(Math.max(0, offset - PAGE));
      setItems(page.items);
      setTotal(page.total);
      setStats(s);
    } catch (e) {
      setError(e.message);
    }
  }, [offset]);

  useEffect(() => { load(); }, [load]);

  async function remove(id) {
    await api.deleteOne(id).catch((e) => setError(e.message));
    load();
  }

  async function clearAll() {
    if (!window.confirm("Delete your entire history? This cannot be undone.")) return;
    await api.deleteAll().catch((e) => setError(e.message));
    setOffset(0);
    load();
  }

  return (
    <>
      <div className="page-title">
        <div>
          <div className="label" style={{ marginBottom: 10 }}>The archive</div>
          <h1>Your history</h1>
        </div>
        {total > 0 && <button className="btn ghost small" onClick={clearAll}>Delete all</button>}
      </div>

      {stats && stats.total > 0 && (
        <div className="tally">
          <div><b>{stats.total}</b><span className="label">analyzed</span></div>
          <div><b>{stats.sarcastic}</b><span className="label">sarcastic</span></div>
          <div><b>{stats.not_sarcastic}</b><span className="label">not sarcastic</span></div>
        </div>
      )}

      {error && <p className="error" role="alert">{error}</p>}
      {stats && total === 0 && <p className="empty">Nothing filed yet. Analyze a headline and it will land here.</p>}

      <ul className="entries">
        {items.map((it, i) => {
          const conf = Math.round((it.is_sarcastic ? it.probability : 1 - it.probability) * 100);
          return (
            <li key={it.id} style={{ "--i": i }}>
              <div className="meta">
                <span className={`verdict-tag ${it.is_sarcastic ? "s" : "n"}`}>
                  {it.is_sarcastic ? "Sarcastic" : "Not sarcastic"} · {conf}%
                </span>
                <button className="linkbtn" onClick={() => remove(it.id)} aria-label="Delete this entry">Remove</button>
              </div>
              <blockquote>{it.text}</blockquote>
              <p className="muted small">
                {new Date(it.created_at).toLocaleString()}
                {it.important_words.length > 0 && <> · leaned on: {[...new Set(it.important_words)].join(", ")}</>}
              </p>
            </li>
          );
        })}
      </ul>

      {total > PAGE && (
        <div className="pager">
          <button className="btn ghost small" disabled={offset === 0} onClick={() => setOffset(offset - PAGE)}>← Newer</button>
          <span className="label">{offset + 1}–{Math.min(offset + PAGE, total)} of {total}</span>
          <button className="btn ghost small" disabled={offset + PAGE >= total} onClick={() => setOffset(offset + PAGE)}>Older →</button>
        </div>
      )}
    </>
  );
}
