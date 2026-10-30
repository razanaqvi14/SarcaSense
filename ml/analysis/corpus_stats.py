"""Word2Vec corpus statistics and nearest neighbours (needs gensim).
See docs/ml/VIVA_GUIDE.md, Appendix D for how to run it."""
import collections
from gensim.models import Word2Vec
w = Word2Vec.load("/ml/word2vec.model")
wv = w.wv
counts = [wv.get_vecattr(k, "count") for k in wv.index_to_key]
tot = sum(counts)
print("vocab", len(counts), "| total tokens", tot, "| mean tokens/headline ~", round(tot / 28407, 2))
print("words seen exactly once:", sum(c == 1 for c in counts), f"({sum(c==1 for c in counts)/len(counts):.1%} of vocab, {sum(c for c in counts if c==1)/tot:.2%} of tokens)")
print("words seen <=2:", sum(c <= 2 for c in counts), f"({sum(c<=2 for c in counts)/len(counts):.1%})", "| <=5:", sum(c <= 5 for c in counts), f"({sum(c<=5 for c in counts)/len(counts):.1%})")
print("top 12 words:", [(k, wv.get_vecattr(k, 'count')) for k in wv.index_to_key[:12]])
print("train epochs", w.epochs, "window", w.window, "sg", w.sg, "negative", w.negative, "vector_size", w.vector_size)
for q in ["man", "trump", "area", "president", "nation"]:
    if q in wv: print(q, "->", [x for x, _ in wv.most_similar(q, topn=6)])
