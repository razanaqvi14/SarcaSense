import { useEffect, useMemo, useState } from "react";

const STRONG = 0.6; // attention above which a word is treated as a heavy hitter
const WORD_STEP_MS = 45; // keep in sync with --n * 45ms in styles.css

function useCountUp(target, delay, duration = 1000) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setValue(target);
      return;
    }
    let raf;
    const timer = setTimeout(() => {
      let start;
      const tick = (now) => {
        start ??= now;
        const p = Math.min(1, (now - start) / duration);
        setValue(Math.round(target * (1 - Math.pow(1 - p, 3))));
        if (p < 1) raf = requestAnimationFrame(tick);
      };
      raf = requestAnimationFrame(tick);
    }, delay);
    return () => {
      clearTimeout(timer);
      cancelAnimationFrame(raf);
    };
  }, [target, delay, duration]);
  return value;
}

export default function ResultCard({ result }) {
  const sarcastic = result.is_sarcastic;
  const n = result.tokens.length;
  const pct = Math.round(result.confidence * 100);

  // Settle the needle on the next frame so the CSS transition runs from the centre.
  const [settled, setSettled] = useState(false);
  useEffect(() => {
    const id = requestAnimationFrame(() => setSettled(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const shown = useCountUp(pct, n * WORD_STEP_MS + 1250);

  // Footnote ranks (1-3) for the most-attended words, and the list of top influences.
  const { ranks, top } = useMemo(() => {
    const order = result.tokens
      .map((t, i) => ({ ...t, i }))
      .sort((a, b) => b.attention - a.attention);
    const ranks = new Map();
    order
      .filter((t) => t.attention >= 0.5)
      .slice(0, 3)
      .forEach((t, r) => ranks.set(t.i, r + 1));
    const seen = new Set();
    const top = [];
    for (const t of order) {
      if (seen.has(t.word)) continue;
      seen.add(t.word);
      top.push(t);
      if (top.length === 5) break;
    }
    return { ranks, top };
  }, [result]);

  return (
    <article
      className={`dispatch ${sarcastic ? "is-sarcastic" : "is-sincere"}`}
      style={{ "--n": n }}
      aria-live="polite"
    >
      <div className="dispatch-head">
        <div>
          <div className="label" style={{ marginBottom: 12 }}>The verdict</div>
          <div className="stamp">{result.label}</div>
        </div>
        <div className="confidence">
          <div className="label">Confidence</div>
          <div className="num">
            {shown}
            <sup>%</sup>
          </div>
        </div>
      </div>

      <p className="tokens" aria-label={result.cleaned_text}>
        {result.tokens.map((t, i) => (
          <span
            key={i}
            className={`token${t.attention >= STRONG ? " strong" : ""}`}
            style={{ "--i": i, "--a": t.attention }}
            data-tip={`influence ${Math.round(t.attention * 100)}%`}
          >
            {t.word}
            {ranks.has(i) && <sup>{ranks.get(i)}</sup>}
          </span>
        ))}
      </p>
      <p className="label caption">
        Marker strength = how much weight the model gave each word
      </p>

      <div className="gauge">
        <div className="gauge-scale">
          <div className="gauge-needle" style={{ left: `${(settled ? result.probability : 0.5) * 100}%` }} />
        </div>
        <div className="gauge-ends label">
          <span>Not sarcastic</span>
          <span>Sarcastic</span>
        </div>
      </div>

      <ol className="influence">
        {top.map((t, r) => (
          <li key={t.word} style={{ "--r": r, "--a": t.attention }}>
            <span className="rank">{String(r + 1).padStart(2, "0")}</span>
            <span className="word">{t.word}</span>
            <span className="bar"><i /></span>
            <span className="pct">{Math.round(t.attention * 100)}%</span>
          </li>
        ))}
      </ol>

      {result.warnings.map((w) => (
        <p key={w} className="notice">{w}</p>
      ))}
      <p className="muted small fineprint">
        Shown as the model reads it: lowercased, contractions expanded, words reduced to their root. Attention shows
        what the model weighted, not proof of why it decided.
      </p>
    </article>
  );
}
