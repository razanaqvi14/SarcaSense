"""Probe the deployed model: parameter count, embedding norms, latency, probe sentences, attention on padding.
Run inside the backend image (see docs/ml/VIVA_GUIDE.md, Appendix D)."""
import time, statistics as st, math
from pathlib import Path
import torch
from app.ml.predictor import Predictor
from app.ml.preprocess import clean_text

p = Predictor(Path("/srv/artifacts/best_model.pt"), Path("/srv/artifacts/word_to_index.json"))
m = p.model
cnt = lambda mod: sum(x.numel() for x in mod.parameters())
print("== PARAMETERS ==")
for name in ["embedding", "lstm", "gru", "attention", "fc"]:
    print(f"{name:10s} {cnt(getattr(m, name)):>10,}")
tot = cnt(m); tr = sum(x.numel() for x in m.parameters() if x.requires_grad)
print(f"total {tot:,} | trainable {tr:,} | frozen {tot-tr:,}")
print("vocab", len(p.word_to_index), "emb shape", tuple(m.embedding.weight.shape))

E = m.embedding.weight.detach()
norms = E.norm(dim=1)
print("\n== EMBEDDING NORMS ==")
print("PAD norm", norms[0].item(), "| UNK norm", round(norms[1].item(), 3),
      "| mean word norm", round(norms[2:].mean().item(), 3), "std", round(norms[2:].std().item(), 3))
cos = torch.nn.functional.cosine_similarity(E[1:2], E[2:], dim=1)
print("UNK cosine to real words: mean", round(cos.mean().item(), 4), "max", round(cos.max().item(), 4))

print("\n== LATENCY (CPU, 1 thread) ==")
s = "Oh great, another Monday. Just what I needed to recharge from the exhausting weekend of doing absolutely nothing."
p.predict(s)
t = []
for _ in range(200):
    a = time.perf_counter(); p.predict(s); t.append((time.perf_counter() - a) * 1000)
t.sort(); print(f"end-to-end ms: median {st.median(t):.2f}  p95 {t[int(.95*len(t))]:.2f}")
x = torch.randint(2, 1000, (1, 20)); t = []
with torch.inference_mode():
    for _ in range(200):
        a = time.perf_counter(); m(x); t.append((time.perf_counter() - a) * 1000)
print(f"model-only ms: median {st.median(t):.2f}")

print("\n== PROBES (my own sentences; not a benchmark) ==")
groups = {
 "headline-style, Onion-like": [
  "Area man heroically finishes entire meeting without saying anything useful",
  "Local man shocked that deadline he ignored has arrived",
  "Nation's dads unanimously agree to pretend they understand the car",
  "Study finds most people would rather not read study",
 ],
 "headline-style, straight news": [
  "Judge blocks new rule on federal student loans",
  "Five dead after storm hits southern states",
  "Senate passes bipartisan infrastructure bill after months of negotiations",
  "Central bank raises interest rates by half a percentage point",
 ],
 "conversational sarcasm": [
  "Oh great, another Monday. Just what I needed to recharge from the exhausting weekend of doing absolutely nothing.",
  "Yeah, because that worked so well last time.",
  "I just love waiting two hours for a five minute appointment.",
  "Thanks for nothing.",
 ],
 "conversational sincere": [
  "I really enjoyed the dinner last night, thank you.",
  "The meeting has been moved to three pm tomorrow.",
  "She studied hard for the exam and passed with distinction.",
 ],
 "robustness: word order / punctuation / case": [
  "area man thrilled to attend meeting",
  "man area thrilled attend to meeting",
  "AREA MAN THRILLED TO ATTEND MEETING!!!",
  "Breaking: area man thrilled to attend meeting",
 ],
 "entity / style bias": [
  "Trump signs executive order on trade",
  "Local man signs executive order on lunch",
  "Obama signs executive order on trade",
 ],
 "edge cases": [
  "Great.",
  "Zxqv blorp flarn quux",
  "Not bad at all for a first attempt",
 ],
}
STOP = set("a an the of to in on for and or but is are was were be been it its this that with at by from as i you he she we they".split())
top_fn = tot_n = 0
for g, items in groups.items():
    print(f"\n[{g}]")
    for s in items:
        r = p.predict(s)
        top = max(r.tokens, key=lambda t: t[1])[0]
        if len(r.tokens) >= 3:
            tot_n += 1; top_fn += top in STOP
        unk = sum(1 for w in clean_text(s).split() if p.word_to_index.get(w, 1) == 1)
        print(f"  P(sarc)={r.probability:.2f} {'S' if r.is_sarcastic else 'N'} | top='{top}' unk={unk} | {s[:70]}")
print(f"\nprobes whose top-attended word is a function word: {top_fn}/{tot_n}")

print("\n== ATTENTION vs POSITION (same word, different slots) ==")
for pos_sent in ["the cat sat", "cat the sat", "cat sat the"]:
    r = p.predict(pos_sent + " near the red barn at dawn")
    print(" ", [(w, round(a, 2)) for w, a in r.tokens])

print("\n== ATTENTION SUM OVER REAL TOKENS (raw softmax over 20 slots incl. padding) ==")
for s in ["Great.", "Local man shocked that deadline he ignored has arrived", "Not bad at all for a first attempt"]:
    toks = clean_text(s).split()[:20]
    idx = [p.word_to_index.get(w, 1) for w in toks]
    padded = [0] * (20 - len(idx)) + idx
    with torch.inference_mode():
        _, a = m(torch.tensor([padded]))
    a = a.squeeze(0)
    print(f"  {len(toks):2d} tokens: mass on real tokens = {a[20-len(toks):].sum().item():.3f}, on padding = {a[:20-len(toks)].sum().item():.3f}")
