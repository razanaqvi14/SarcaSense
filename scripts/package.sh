#!/usr/bin/env bash
# Packs the project into one archive to copy to another PC.
# Leaves out secrets (.env), build output, caches, and the large training outputs in ml/artifacts/
# that the app does not need at runtime (the model the app uses is backend/artifacts/best_model.pt).
#
# Usage: scripts/package.sh [output.tar.gz]     (default: ../sarcasense.tar.gz)
set -euo pipefail
cd "$(dirname "$0")/.."

out="${1:-../sarcasense.tar.gz}"

tar czf "$out" \
  --exclude='./.env' \
  --exclude='node_modules' --exclude='dist' \
  --exclude='__pycache__' --exclude='.pytest_cache' --exclude='dev.db' \
  --exclude='./ml/artifacts' \
  --transform 's,^\.,sarcasense,' \
  .

echo "Wrote $out ($(du -h "$out" | cut -f1))"
echo "Contents sanity check:"
tar tzf "$out" | grep -E 'backend/artifacts/(best_model.pt|word_to_index.json)|package-lock.json|docker-compose.yml' | sed 's/^/  /'
