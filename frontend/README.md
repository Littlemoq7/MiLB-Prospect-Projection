# Prospect Predictor — Frontend

Svelte + Vite UI for the Prospect Predictor model.

## Running

The frontend calls the Flask API, so both need to be running.

**Terminal 1 — Flask backend (from the repo root):**

```bash
./mlbvenv/bin/python app.py
```

**Terminal 2 — Vite dev server:**

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to Flask on port 5000, so there are no CORS issues in development.

## API

`POST /api/predict` with `{"player_name": "Roman Anthony"}` returns:

```json
{
  "name": "Roman Anthony",
  "category": "Average",
  "confidence": 0.698,
  "probabilities": {
    "Below Average": 0.065,
    "Average": 0.698,
    "Above Average": 0.237
  }
}
```

Unknown players return `404` with an `error` message.
