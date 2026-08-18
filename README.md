# Prospect Predictor

Predicts whether a minor-league hitter will become a **below-average**, **average**, or **above-average** MLB bat, using level-weighted MiLB statistics and a small Keras neural network.

Enter a prospect's name and the app returns a predicted tier plus the model's confidence across all three categories.

## How it works

Minor-league stats are weighted by both **level** (AAA counts 3×, AA 2×, A-and-below 1×) and **plate appearances**, so a strong AAA season outweighs the same line in Single-A. Those weighted stats (`PA`, `BB%`, `K%`, `ISO`, `GB%`, `wRC+`) feed a multinomial logistic regression that outputs a probability for each tier.

Tiers are defined by a player's career average MLB wRC+:

| Tier | Career avg wRC+ |
| --- | --- |
| Below Average | < 100 |
| Average | 100 – 120 |
| Above Average | > 120 |

## Running the app

Install dependencies (a `mlbvenv/` virtualenv is already set up locally):

```bash
python3 -m venv mlbvenv
./mlbvenv/bin/pip install -r requirements.txt
```

**Start the Flask backend:**

```bash
./mlbvenv/bin/python app.py
```

This serves both the JSON API and a minimal server-rendered UI at http://localhost:5000.

**Start the Svelte frontend** (recommended — nicer UI) in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. Vite proxies `/api` to Flask, so no CORS config is needed.

Try `Roman Anthony`, `Walker Jenkins`, or `Brooks Brannon`.

## API

`POST /api/predict` — body `{"player_name": "Roman Anthony"}`

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

Unknown players return `404` with an `error` message. Name matching is exact.

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

## Model

`train.py` fits a multinomial logistic regression inside a scikit-learn `Pipeline`, so the `StandardScaler` is saved as part of the model and inference uses exactly the transform training used.

Evaluation is 5-fold stratified cross-validation. Retrain and see the full report with:

```bash
./mlbvenv/bin/python train.py
```

| Model | 5-fold CV accuracy |
| --- | --- |
| Always guess "Below Average" | 51.1% |
| Neural network (`TensorFlow.py`) | 53.0% (± 5.1) |
| **Logistic regression (served)** | **57.5% (± 2.5)** |

The neural network is kept only to document why it isn't shipped: on 591 rows with 6 features it lands near the majority-class baseline with twice the variance. `TensorFlow.py` deliberately saves nothing.

TensorFlow is **not** installed by `requirements.txt` — it is ~1.1GB and nothing the app serves imports it. To reproduce that baseline row:

```bash
./mlbvenv/bin/pip install tensorflow==2.18.0
./mlbvenv/bin/python TensorFlow.py
```

## Data pipeline

The generated CSVs are committed, so you only need to re-run these to rebuild from scratch:

| Step | Script | Input | Output |
| --- | --- | --- | --- |
| 1 | `mlbdatapullinh.py` | pybaseball API | `data/batting_stats_2023.csv` |
| 2 | `CleaningMLBData.py` | `data/MLB_Cleaned.csv` | `data/MLB_GroupedSimple.csv` |
| 3 | `dataCleaning.py` | `data/milbHitterIndicators.csv` | `weightedMiLBStats.csv` |
| 4 | `merge.py` | outputs of 2 + 3 | `mergedOutput.csv` |
| 5 | `train.py` | `mergedOutput.csv` | `model.joblib` |

Notes:

- `data/milbHitterIndicators.csv` is the raw MiLB export and **cannot be regenerated** by any script here — don't delete it.
- The `to_csv` export at the end of `dataCleaning.py` is intentionally commented out so running the script can't silently overwrite the `weightedMiLBStats.csv` the trained model depends on. Uncomment it deliberately.
- Step 1 needs `pybaseball` (see `requirements.txt`); its output is not currently consumed directly by step 2.

## Known limitations

- **Modest accuracy.** 57.5% against a 51.1% baseline. Treat predictions as directional, not authoritative.
- **"Above Average" is the weak class.** The 591 rows split 302 / 212 / 77, and the model recalls only 17% of true above-average hitters (13 of 77) — the tier the app most wants to surface is the one it finds least reliably. See the confusion matrix printed by `train.py`.
- **Survivorship bias.** `merge.py`'s inner join keeps only players who reached MLB, discarding 13,339 of 13,930 (95.8%). The model effectively answers "given a player reached the majors, how good were they?" rather than "will this prospect be good?" Fixing this is the largest available improvement.
- **Exact name matching only.** No fuzzy search, so typos and nicknames return "not found".
- `app.secret_key` is hardcoded and `debug=True` — fine for a local demo, not for deployment.
