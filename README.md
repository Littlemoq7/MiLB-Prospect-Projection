# Prospect Predictor

**A full-stack ML app that projects whether a minor-league hitter becomes a below-average, average, or above-average MLB bat — or never reaches the majors at all.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.6-F7931E?logo=scikitlearn&logoColor=white)
![Svelte](https://img.shields.io/badge/Svelte-5-FF3E00?logo=svelte&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-8-646CFF?logo=vite&logoColor=white)

NOTE: Data from and references to MLB are for educational and non-commercial purposes only.

Enter a prospect's name and the app returns a predicted tier plus the model's confidence across all four categories, backed by a Flask API and a Svelte frontend.

## Highlights

- **Fixed a survivorship-bias flaw in the original approach.** Training only on players who'd already reached the majors meant the model could answer "how good is this graduate?" but not "will this prospect make it?" Rebuilding the label set to include the ~87% of minor leaguers who never reached MLB is what makes this a genuine prospect-projection tool rather than a graduate-ranking one.
- **3.5x recall on the highest-value class.** The tier this app most wants to get right — future above-average bats — went from 17% recall (13/77) under the old graduates-only model to **59% recall (70/118)** after fixing the label bias and adding class-balanced weighting.
- **Custom feature engineering for minor-league data**, weighting each season by both **level** (AAA 3×, AA 2×, everything below 1×) and **plate appearances**, plus an age-relative-to-level feature computed from the historical PA-weighted average age at each level/season.
- **End-to-end product, not just a notebook**: a Flask JSON API, a Svelte SPA with live name autocomplete, and a season-by-season manual entry form for prospects not yet in the dataset — all backed by a reproducible data pipeline from raw exports to a served `model.joblib`.

## How it works

Minor-league stats are weighted by both **level** (AAA counts 3×, AA 2×, A-and-below 1×) and **plate appearances**, so a strong AAA season outweighs the same line in Single-A. Those weighted stats (`PA`, `BB%`, `K%`, `ISO`, `GB%`, `wRC+`, `Age`, `AgeRelLevel`) feed a multinomial logistic regression that outputs a probability for each tier.

Training data includes minor leaguers who never reached the majors, not just graduates ranked against each other — without them the model would only be able to answer "given a player reached the majors, how good were they?" instead of "will this prospect be good?"

Tiers are defined by a player's career MLB wRC+, weighted by plate appearances:

| Tier | Definition |
| --- | --- |
| Did Not Reach MLB | Last MiLB season ≤ 2018 (6+ years of runway) and career MiLB PA ≥ 500, but never accumulated real MLB playing time |
| Below Average | Career avg wRC+ < 95 |
| Average | Career avg wRC+ 95 – 114 |
| Above Average | Career avg wRC+ ≥ 115 |

## Tech stack

| Layer | Tools |
| --- | --- |
| Model | scikit-learn (multinomial logistic regression + `StandardScaler` in a `Pipeline`), pandas, numpy, joblib |
| API | Flask (JSON API + server-rendered fallback UI) |
| Frontend | Svelte 5 + Vite |
| Data pipeline | pandas-based cleaning/merging scripts over FanGraphs MiLB/MLB exports |

## Running the app

```bash
./start.sh
```

This sets up the `mlbvenv/` virtualenv and `frontend/node_modules` on first run (if missing), trains the model if `model.joblib` isn't present, then starts the Flask API in the background and the Svelte frontend in the foreground, opening http://localhost:5173 — the **Svelte app is the main way to use Prospect Predictor**, with a name search (autocomplete included) and a manual stat-entry form for players not in the dataset.

Try `Roman Anthony`, `Walker Jenkins`, or `Brooks Brannon` in the search tab.

To run the pieces yourself instead:

```bash
./mlbvenv/bin/python app.py       # Flask API on :5001
cd frontend && npm install && npm run dev   # Svelte UI on :5173
```

Vite proxies `/api` to Flask, so no CORS config is needed. Flask also serves a minimal server-rendered fallback UI directly at http://localhost:5001 for use without the frontend.

## API

`POST /api/predict` — body `{"player_name": "Roman Anthony"}`

```json
{
  "name": "Roman Anthony",
  "category": "Above Average",
  "confidence": 0.703,
  "probabilities": {
    "Did Not Reach MLB": 0.036,
    "Below Average": 0.055,
    "Average": 0.207,
    "Above Average": 0.703
  }
}
```

Unknown players return `404` with an `error` message. Name matching is exact — use `GET /api/player-names?q=<query>` for autocomplete suggestions (up to 10 matching names).

`POST /api/predict-seasons` — body `{"seasons": [{"Season": 2023, "Level": "AA", "PA": 400, "BB%": 0.09, "K%": 0.21, "ISO": 0.15, "GB%": 0.42, "wRC+": 105, "Age": 22}, ...]}`, for evaluating a prospect season-by-season instead of looking one up by name. `AgeRelLevel` is deliberately not part of the input — it's derived per season from `Age` minus the historical PA-weighted average age at that `Season`/`Level` (falling back to that level's all-time average age if the exact season isn't on file), then the seasons are aggregated into one feature row using the same level-weighting (`AAA` 3x, `AA` 2x, everything else 1x) `CleaningMLBData.py`/`dataCleaning.py` used to build the training data. Returns the same shape as `/api/predict` minus `name`. `GET /api/season-fields` returns the per-season field list + hints and the valid `Level` values, which the Svelte form renders itself from.

## Project layout

```
app.py               Flask server: web UI + /api/predict
train.py             Trains + evaluates the served model
prediction.py        Loads model.joblib, maps output to tiers
model.joblib         Trained pipeline (scaler + classifier)
TensorFlow.py        Neural-net baseline, for comparison only
frontend/            Svelte + Vite UI
data/                Source + intermediate CSVs
```

## Model & results

`train.py` fits a multinomial logistic regression (`class_weight='balanced'`) inside a scikit-learn `Pipeline`, so the `StandardScaler` is saved as part of the model and inference uses exactly the transform training used.

Evaluation is 5-fold stratified cross-validation over all 4,590 labeled players. Overall accuracy isn't a meaningful headline number here — "Did Not Reach MLB" alone makes up 87% of the data, so a model that just guessed that class for everyone would already score 87.1%, close to what's actually shipped (73.4%). `class_weight='balanced'` deliberately trades away some of that raw accuracy to actually catch the minority classes, which is the entire point of the app. Recall per tier is the number that matters:

| Tier | Recall | Support |
| --- | --- | --- |
| Did Not Reach MLB | 78% | 3,997 |
| Below Average | 49% | 215 |
| Average | 30% | 260 |
| **Above Average** | **59%** | 118 |

For comparison, the previous 3-class model (graduates only, no `Age` feature, unweighted labels) recalled only 17% of true above-average hitters (13 of 77) — the tier the app most wants to surface was the one it found least reliably. Fixing the survivorship bias and class-weighting the loss function raised that to 59%.

Retrain and see the full report (class counts, join diagnostics, confusion matrix) with:

```bash
./mlbvenv/bin/python train.py
```

`TensorFlow.py` is kept only to document why a neural net isn't shipped: evaluated against the old graduates-only dataset (591 rows, 3 classes, no `Age` feature), it landed near the majority-class baseline with twice the variance of logistic regression. It has not been re-evaluated against the current 4-class dataset. `TensorFlow.py` deliberately saves nothing.

TensorFlow is **not** installed by `requirements.txt` — it is ~1.1GB and nothing the app serves imports it. To reproduce that baseline row:

```bash
./mlbvenv/bin/pip install tensorflow==2.18.0
./mlbvenv/bin/python TensorFlow.py
```

## Data pipeline

The generated CSVs are committed, so you only need to re-run these to rebuild from scratch. Order matters — `CleaningMLBData.py` reads `weightedMiLBStats.csv`, so `dataCleaning.py` must run first:

| Step | Script | Reads | Writes |
| --- | --- | --- | --- |
| 1 | `dataCleaning.py` | `data/milbHitterIndicators.csv` | `weightedMiLBStats.csv` |
| 2 | `CleaningMLBData.py` | `data/MLB_Cleaned.csv`, `data/milbHitterIndicators.csv`, `weightedMiLBStats.csv` | `data/MLB_GroupedSimple.csv` |
| 3 | `merge.py` | outputs of 1 + 2 | `mergedOutput.csv` |
| 4 | `train.py` | `mergedOutput.csv` | `model.joblib` |

Run the whole pipeline and start the app in one go:

```bash
./mlbvenv/bin/python3 dataCleaning.py && \
./mlbvenv/bin/python3 CleaningMLBData.py && \
./mlbvenv/bin/python3 merge.py && \
./mlbvenv/bin/python3 train.py && \
./mlbvenv/bin/python3 app.py
```

Notes:

- `data/milbHitterIndicators.csv` and `data/MLB_Cleaned.csv` are raw exports and **cannot be regenerated** by any script here — don't delete them.
- `merge.py` joins on FanGraphs `PlayerId`/`IDfg` first (collision-free) and only falls back to a `Name` join for players without a matching numeric id — printed diagnostics show how many matched each way.
- `mlbdatapullinh.py` needs `pybaseball` (not installed — see `requirements.txt`) and isn't part of this pipeline; its output isn't consumed by any other script.

## Known limitations

- **Modest per-tier recall.** "Average" recall is only 30% — it's a narrow 95–114 wRC+ band squeezed between two open-ended tiers, so borderline players easily slip into "Below Average" or "Above Average" instead. Treat predictions as directional, not authoritative.
- **"Did Not Reach MLB" ground truth is imperfect.** A player counts as "graduated" if they appear in `data/MLB_Cleaned.csv`, which itself only includes MLB seasons with PA ≥ 300. A player with only short MLB cameos is labeled as "Did Not Reach MLB".
