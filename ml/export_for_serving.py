"""Promote a trained model from ml/artifacts/ to backend/artifacts/ (what the web service loads).

The notebook saves two things the service needs:
  best_model.pt        torch state_dict (includes the frozen embedding matrix)
  word_to_index.pkl    vocabulary dict {"<PAD>": 0, "<UNK>": 1, word: index, ...}

The service reads the vocabulary as JSON, so it never has to unpickle anything at runtime.

Usage (from the project root):
    python ml/export_for_serving.py
    python ml/export_for_serving.py --out /some/other/dir
"""
import argparse
import json
import pickle
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", type=Path, default=ROOT / "ml" / "artifacts")
    ap.add_argument("--out", type=Path, default=ROOT / "backend" / "artifacts")
    args = ap.parse_args()

    # pickle.load can execute code: only run this on files you produced yourself.
    with open(args.src / "word_to_index.pkl", "rb") as f:
        vocab = pickle.load(f)

    assert isinstance(vocab, dict), "vocabulary must be a dict"
    assert vocab.get("<PAD>") == 0 and vocab.get("<UNK>") == 1, "<PAD>/<UNK> must map to 0/1"
    assert sorted(vocab.values()) == list(range(len(vocab))), "indices must be 0..N-1 with no gaps"

    args.out.mkdir(parents=True, exist_ok=True)
    with open(args.out / "word_to_index.json", "w", encoding="utf-8") as f:
        json.dump(vocab, f)
    shutil.copyfile(args.src / "best_model.pt", args.out / "best_model.pt")

    try:  # optional: the embedding table must have one row per vocabulary entry
        import torch

        rows = torch.load(args.out / "best_model.pt", map_location="cpu", weights_only=True)["embedding.weight"].shape[0]
        assert rows == len(vocab), f"embedding has {rows} rows but vocabulary has {len(vocab)} entries"
        print(f"checked: embedding rows == vocabulary size == {rows}")
    except ImportError:
        print("torch not installed; skipped the embedding/vocabulary size check")

    print(f"exported {len(vocab)} words + model to {args.out}")
    print("now rebuild the service:  docker compose up -d --build backend")


if __name__ == "__main__":
    main()
