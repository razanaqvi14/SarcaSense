import json
import threading
from dataclasses import dataclass
from pathlib import Path

import torch

from .model import SarcasmClassifier
from .preprocess import clean_text

MAX_LENGTH = 20
PAD_INDEX = 0
UNK_INDEX = 1
# Words with attention >= this fraction of the maximum are reported as "important".
IMPORTANT_WORD_RATIO = 0.5


class EmptyTextError(ValueError):
    """The text has no analysable words once cleaned."""


@dataclass
class Prediction:
    is_sarcastic: bool
    probability: float
    cleaned_text: str
    tokens: list[tuple[str, float]]
    important_words: list[str]
    warnings: list[str]


class Predictor:
    def __init__(self, model_path: Path, vocab_path: Path):
        with open(vocab_path, encoding="utf-8") as f:
            self.word_to_index: dict[str, int] = json.load(f)

        # weights_only=True refuses to unpickle arbitrary objects from the file.
        state_dict = torch.load(model_path, map_location="cpu", weights_only=True)
        vocab_size, embedding_dim = state_dict["embedding.weight"].shape
        hidden_dim = state_dict["attention.weight"].shape[1] // 2

        self.model = SarcasmClassifier(vocab_size, embedding_dim, hidden_dim)
        self.model.load_state_dict(state_dict)
        self.model.eval()
        # Inference is cheap; keep it from fighting the web server for cores.
        torch.set_num_threads(1)
        self._lock = threading.Lock()

    def predict(self, text: str) -> Prediction:
        cleaned = clean_text(text)
        words = cleaned.split()
        if not words:
            raise EmptyTextError("No analysable words found in the text.")

        # The model only sees the first MAX_LENGTH tokens, left-padded (as in training).
        used = words[:MAX_LENGTH]
        indices = [self.word_to_index.get(w, UNK_INDEX) for w in used]
        padded = [PAD_INDEX] * (MAX_LENGTH - len(indices)) + indices
        n_pad = MAX_LENGTH - len(indices)

        with self._lock, torch.inference_mode():
            logit, attention = self.model(torch.tensor([padded]))
        probability = torch.sigmoid(logit).item()
        weights = attention.squeeze(0).tolist()[n_pad:]

        top = max(weights)
        relative = [w / top if top > 0 else 0.0 for w in weights]
        important = [
            w for w, r in zip(used, relative) if r >= IMPORTANT_WORD_RATIO
        ]

        warnings = []
        if len(words) < 3:
            warnings.append(
                "Very short text: the model was trained on headlines of 3+ words, "
                "so this result is less reliable."
            )
        if len(words) > MAX_LENGTH:
            warnings.append(
                f"Only the first {MAX_LENGTH} words were analysed."
            )
        unknown = sum(1 for i in indices if i == UNK_INDEX)
        if unknown and unknown / len(indices) >= 0.5:
            warnings.append(
                "Most words are outside the model's vocabulary, so this result is less reliable."
            )

        return Prediction(
            is_sarcastic=probability > 0.5,
            probability=probability,
            cleaned_text=cleaned,
            tokens=list(zip(used, relative)),
            important_words=important,
            warnings=warnings,
        )
