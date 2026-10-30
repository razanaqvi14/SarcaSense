"""Faithfulness of attention (occlusion) + check that embedding_matrix.pkl equals the checkpoint embedding.
See docs/ml/VIVA_GUIDE.md, Appendix D for how to run it."""
import pickle, statistics as st, random
from pathlib import Path
import numpy as np, torch
from app.ml.predictor import Predictor
from app.ml.preprocess import clean_text

p = Predictor(Path("/srv/artifacts/best_model.pt"), Path("/srv/artifacts/word_to_index.json"))
m = p.model

# 1) is the pickled matrix the same thing as the checkpoint's embedding?
M = pickle.load(open("/ml/embedding_matrix.pkl", "rb"))
E = m.embedding.weight.detach().numpy()
print("embedding_matrix.pkl == checkpoint embedding:", M.shape == E.shape, "max abs diff", float(np.abs(M - E).max()))

def prob(tokens):
    idx = [p.word_to_index.get(w, 1) for w in tokens[:20]]
    x = torch.tensor([[0] * (20 - len(idx)) + idx])
    with torch.inference_mode():
        lg, a = m(x)
    return torch.sigmoid(lg).item(), a.squeeze(0).tolist()[20 - len(idx):]

S = [
 "Area man heroically finishes entire meeting without saying anything useful",
 "Local man shocked that deadline he ignored has arrived",
 "Nation's dads unanimously agree to pretend they understand the car",
 "Study finds most people would rather not read study",
 "Judge blocks new rule on federal student loans",
 "Five dead after storm hits southern states",
 "Senate passes bipartisan infrastructure bill after months of negotiations",
 "Central bank raises interest rates by half a percentage point",
 "Oh great, another Monday. Just what I needed to recharge from the exhausting weekend of doing absolutely nothing.",
 "Yeah, because that worked so well last time.",
 "I just love waiting two hours for a five minute appointment.",
 "I really enjoyed the dinner last night, thank you.",
 "The meeting has been moved to three pm tomorrow.",
 "She studied hard for the exam and passed with distinction.",
 "Trump signs executive order on trade",
 "Local man signs executive order on lunch",
 "Obama signs executive order on trade",
 "Scientists discover new species of frog in Amazon rainforest",
 "Man who lost job to automation excited to learn robot will take his place at dinner",
 "Mayor announces plan to repair city roads over next five years",
 "Report: Nation's office workers still waiting for meeting to become email",
 "Government unveils new budget with tax cuts for middle class families",
 "Congress heroically passes bill to study whether to pass another bill",
 "Police investigate string of burglaries in downtown neighborhood",
]
rows = []   # (attention_rel, |delta|, signed delta toward verdict)
top_d, rand_d, all_d = [], [], []
random.seed(0)
for s in S:
    toks = clean_text(s).split()[:20]
    if len(toks) < 5: continue
    p0, att = prob(toks)
    top = max(att); rel = [a / top for a in att]
    deltas = []
    for i in range(len(toks)):
        pi, _ = prob(toks[:i] + toks[i + 1:])
        deltas.append(abs(p0 - pi))
    rows += list(zip(rel, deltas))
    top_d.append(deltas[int(np.argmax(att))])
    all_d.append(st.mean(deltas))
    rand_d.append(deltas[random.randrange(len(toks))])
def spearman(a, b):
    ra = np.argsort(np.argsort(a)); rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])
a, d = zip(*rows)
print(f"sentences: {len(top_d)}  tokens pooled: {len(rows)}")
print(f"Spearman(attention, |delta P| when token removed) = {spearman(a, d):.3f}")
print(f"mean |delta P| removing TOP-attended token: {st.mean(top_d):.3f}")
print(f"mean |delta P| removing a RANDOM token:     {st.mean(rand_d):.3f}")
print(f"mean |delta P| averaged over all tokens:    {st.mean(all_d):.3f}")
print("sentences where top-attended removal changes the verdict (p crosses 0.5):", end=" ")
flip = 0
for s in S:
    toks = clean_text(s).split()[:20]
    if len(toks) < 5: continue
    p0, att = prob(toks); i = int(np.argmax(att)); pi, _ = prob(toks[:i] + toks[i + 1:])
    flip += (p0 > .5) != (pi > .5)
print(flip)
