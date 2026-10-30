# Model card

Source: [`ml/notebooks/sarcasm-detection-using-attention-mechanism-87.ipynb`](../../ml/notebooks/sarcasm-detection-using-attention-mechanism-87.ipynb) (trained on Kaggle, Python 3.11, GPU). For the full explanation and exam preparation see [VIVA_GUIDE.md](VIVA_GUIDE.md).

## At a glance

| | |
|---|---|
| Task | Binary classification of an English news headline: sarcastic (1) / not sarcastic (0) |
| Data | News Headlines Dataset for Sarcasm Detection v2: 28,619 headlines (14,985 not sarcastic / 13,634 sarcastic); 28,407 after cleaning |
| Split | random 80 / 10 / 10 → 22,725 train / 2,840 validation / 2,842 test (no seed, not stratified) |
| Input | first 20 cleaned tokens, left-padded; vocabulary 23,228 (incl. `<PAD>`=0, `<UNK>`=1) |
| Embeddings | Word2Vec skip-gram, 300-d, window 10, 10 negative samples, 20 epochs, trained on the same 298,747-token corpus; **frozen** |
| Architecture | Embedding → BiLSTM(91) → BiGRU(91) → attention pooling → linear → logit |
| Parameters | 7,405,020 total; **436,620 trainable**; 6,968,400 frozen (embeddings) |
| Loss / optimiser | `BCEWithLogitsLoss`; AdamW, lr 0.0093, batch 128 (found by Optuna) |
| Stopping | early stopping on validation loss, patience 3 → stopped at epoch 5, **checkpoint from epoch 2** |
| **Test result** | **accuracy 86.5 %** (2459 / 2842; 95 % CI ≈ 85.2–87.7 %), macro-F1 0.865, MCC 0.730 |
| Majority-class baseline | 51.7 % on the test split |
| Inference cost | ≈ 0.7 ms per headline on one CPU thread (cleaning + model) |

Test confusion matrix (rows = truth):

| | pred. not sarcastic | pred. sarcastic |
|---|---|---|
| **not sarcastic** (1469) | 1304 | 165 |
| **sarcastic** (1373) | 218 | 1155 |

Sarcastic class: precision 0.875, recall 0.841, F1 0.858. Not-sarcastic: precision 0.857, recall 0.888, F1 0.872.

## Preprocessing (identical in training and in the app)

lowercase → keep only ASCII letters/digits/punctuation (accents stripped, emoji dropped) → normalise numbers (`$1,500`→`1500 dollars`, `50%`→`50 percent`, decimals rounded) → expand contractions (a custom map, then the `contractions` library; any remaining `'s` becomes ` has`) → delete punctuation → collapse whitespace → WordNet lemmatisation (`has`, `us` protected). Headlines with fewer than 3 words and exact duplicates are dropped.

Code: `backend/app/ml/preprocess.py` (ported unchanged).

## Inference in this app

`backend/app/ml/predictor.py` reproduces the notebook's `get_predicted_class_and_important_words`, with deliberate differences:

| Notebook | App |
|---|---|
| Crashes (`IndexError`) for headlines longer than 20 tokens | Uses the first 20 tokens, as in training, and warns |
| Label + important words only | Also returns probability, confidence and per-token attention (relative to the top word) |
| — | Warnings for < 3 words, > 20 words, mostly out-of-vocabulary words |

Everything else (cleaning, left-padding, `<UNK>` = 1, 0.5 threshold, "important" = attention ≥ 50 % of the maximum) is identical. A test reproduces the notebook's saved example exactly (`['exhausting', 'weekend', 'of', 'doing', 'absolutely']`).

Because the attention softmax runs over all 20 slots **including padding** (as trained), the raw weights over real words do not sum to 1 (for a 1-word input, 47 % of the mass sits on padding). The API therefore reports attention relative to the top word.

## Known limitations

- **Domain:** trained on headlines (The Onion vs HuffPost). Conversational or social-media sarcasm is out of distribution (e.g. "I just love waiting two hours for a five minute appointment." → 0.10).
- **Source-style confound:** the model partly learns *which publication* a headline resembles ("Local man…" → 1.00; "Trump signs executive order on trade" → 0.09).
- **Closed vocabulary:** unseen words map to one fixed random vector with ~8× the norm of a real word, so gibberish can be scored with high confidence (`"Zxqv blorp flarn quux"` → 0.98). The app warns when most words are unknown.
- **Preprocessing losses:** punctuation, capitalisation and tense are discarded; possessive `'s` becomes "has" (`"Trump's tariffs"` → `trump has tariff`).
- **Attention ≠ explanation:** a moderate correlation (Spearman 0.51 on a 24-sentence check) between attention and the effect of deleting a word.
- **Reproducibility:** no seed was set; one run; no cross-validation.

## Updating the model

See [ml/README.md](../../ml/README.md): retrain, run `python ml/export_for_serving.py`, rebuild the backend image. If the architecture or cleaning changes, update `backend/app/ml/model.py` / `preprocess.py` and the cleaning tests.
