#!/usr/bin/env bash
# Sets up (if needed) and starts the Prospect Predictor: the Flask API in the
# background, and the Svelte frontend (the app's main UI) in the foreground.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -d mlbvenv ]; then
    echo "Creating virtualenv..."
    python3 -m venv mlbvenv
fi

./mlbvenv/bin/pip install -q -r requirements.txt

if [ ! -f model.joblib ]; then
    echo "No model.joblib found, training model..."
    ./mlbvenv/bin/python train.py
fi

if [ ! -d frontend/node_modules ]; then
    echo "Installing frontend dependencies..."
    (cd frontend && npm install)
fi

echo "Starting Flask API on http://localhost:5001"
./mlbvenv/bin/python app.py &
FLASK_PID=$!
trap 'kill $FLASK_PID 2>/dev/null' EXIT

echo "Starting Svelte frontend at http://localhost:5173"
(sleep 1 && open http://localhost:5173) &
(cd frontend && npm run dev)
