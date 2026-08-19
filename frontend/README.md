# Prospect Predictor — Frontend

Svelte + Vite UI for the Prospect Predictor model — this is the app's main interface. It offers two tabs: search by player name (with autocomplete), and manual entry for evaluating a prospect season-by-season.

## Running

From the repo root, `./start.sh` runs both this and the Flask API together. To run them separately:

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

Open http://localhost:5173. Vite proxies `/api` to Flask on port 5001, so there are no CORS issues in development.

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

`GET /api/player-names?q=trou` returns up to 10 matching names, e.g. `["Mike Trout"]` — backs the search tab's autocomplete.

`GET /api/season-fields` returns the per-season field list (each with a hint) plus the valid `Level` values, which the manual-entry tab renders its form from:

```json
{
  "fields": [{ "name": "Season", "hint": "Year, e.g. 2024" }, ...],
  "levels": ["DSL", "CPX", "R", "A-", "A", "A+", "AA", "AAA"]
}
```

`POST /api/predict-seasons` with `{"seasons": [{ "Season": 2023, "Level": "AA", "PA": 400, "BB%": 0.09, "K%": 0.21, "ISO": 0.15, "GB%": 0.42, "wRC+": 105, "Age": 22 }, ...]}` returns the same shape as `/api/predict`, minus `name`. There's no `AgeRelLevel` input — the backend derives it per season from historical level-average ages and aggregates seasons the same way the training data was built (`AAA` weighted 3x, `AA` 2x, everything else 1x).
