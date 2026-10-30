# ml/ — the research side

Everything here is about *training and studying* the model. The web service in `backend/` only needs the two files that `export_for_serving.py` produces.

```
ml/
├── notebooks/sarcasm-detection-using-attention-mechanism-87.ipynb   end-to-end experiment (Kaggle, Python 3.11, GPU)
├── artifacts/                  outputs of the notebook (large; not meant for Git)
│   ├── best_model.pt           trained weights (state_dict, incl. frozen embeddings)
│   ├── word_to_index.pkl       vocabulary
│   ├── word2vec.model          gensim Word2Vec model (only needed to retrain/inspect embeddings)
│   └── embedding_matrix.pkl    the 23,228 × 300 matrix (redundant: it is inside best_model.pt)
├── export_for_serving.py       copies best_model.pt and converts the vocabulary to JSON for backend/artifacts/
└── analysis/                   scripts that measure the deployed model (probes, faithfulness, corpus stats); see docs/ml/VIVA_GUIDE.md, Appendix D
```

## What the notebook does, in order

| Step | Notebook cells | Summary |
|---|---|---|
| Load | 8–15 | News Headlines Sarcasm Dataset v2, 28,619 labelled headlines |
| Clean | 20–36 | lowercase → ASCII → numbers/currency → contractions → punctuation → lemmatize; drop < 3 words and duplicates → 28,407 |
| Explore | 37–47 | class balance, word clouds, frequent words, length histograms |
| Vectorise | 48–87 | Word2Vec (skip-gram, 300-d) on the corpus; vocabulary + embedding matrix; left-pad to 20 tokens |
| Split | 88–95 | random 80/10/10 → 22,725 / 2,840 / 2,842 |
| Tune | 106–114 | Optuna, 100 trials × 5 epochs (batch size, hidden size, optimizer, learning rate) |
| Train | 115–122 | best config, early stopping on validation loss (patience 3) |
| Evaluate | 123–127 | test set: accuracy 86.5% (2459 / 2842) |
| Infer | 128–130 | `get_predicted_class_and_important_words` — label plus high-attention words |

## Replacing the deployed model

1. Retrain in the notebook, so that `best_model.pt` and `word_to_index.pkl` land in `ml/artifacts/`.
2. From the project root: `python ml/export_for_serving.py` (checks that the vocabulary and the embedding table agree).
3. `docker compose up -d --build backend`.

If you change the architecture, update `backend/app/ml/model.py`; if you change the text cleaning, update `backend/app/ml/preprocess.py` and the expected values in `backend/tests/test_preprocess.py`. The service loads weights by parameter name, so layer names must match.

## Reproducibility notes

- The notebook sets **no random seed**, so the 80/10/10 split, weight initialisation, batch order and the random `<UNK>` vector differ on every run. The saved artifacts are therefore the only exact record of the reported results. See [docs/ml/VIVA_GUIDE.md](../docs/ml/VIVA_GUIDE.md) Parts 11–12 for what to add.
- The notebook paths (`/kaggle/input/...`) and `fireducks` pandas backend are Kaggle-specific; to rerun locally, download the dataset JSON and swap the path.
- Training ran on Python 3.11 (Kaggle); the service runs on Python 3.12.10. Weights are plain tensors and load identically.
