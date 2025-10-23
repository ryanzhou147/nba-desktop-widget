#!/usr/bin/env bash
set -euo pipefail

# run_venv.sh
# Creates a Python virtual environment in .venv, installs dependencies from
# requirements.txt, and runs app.py. Safe to re-run.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENVDIR="$ROOT_DIR/.venv"
PYTHON=${PYTHON:-python3}

echo "Using python interpreter: $(command -v "$PYTHON" || echo 'not found')"

if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "Python not found. Please install Python 3.8+ and retry." >&2
  exit 2
fi

# Create venv if missing
if [ ! -d "$VENVDIR" ]; then
  echo "Creating virtual environment in $VENVDIR..."
  "$PYTHON" -m venv "$VENVDIR"
fi

# Activate venv for this script
# shellcheck source=/dev/null
source "$VENVDIR/bin/activate"

pip install --upgrade pip setuptools wheel

if [ -f "$ROOT_DIR/requirements.txt" ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r "$ROOT_DIR/requirements.txt"
else
  echo "No requirements.txt found in $ROOT_DIR" >&2
  deactivate || true
  exit 3
fi

echo
echo "Launching NBA Desktop Widget (app.py)..."
cd "$ROOT_DIR"

# Run the app. Forward any CLI args to the python invocation.
exec "$VENVDIR/bin/python" app.py "$@"
