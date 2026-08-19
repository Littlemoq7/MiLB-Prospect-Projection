# Prospect Predictor

Predicts whether a minor-league hitter will become a **below-average**, **average**, or **above-average** MLB bat — or never reach the majors at all — using level-weighted MiLB statistics and a multinomial logistic regression.

Enter a prospect's name and the app returns a predicted tier plus the model's confidence across all four categories.

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

- **Modest per-tier recall.** "Average" recall is only 30% — the model still confuses that tier with its neighbors more than it should. Treat predictions as directional, not authoritative.
- **"Did Not Reach MLB" ground truth is imperfect.** A player counts as "graduated" if they appear in `data/MLB_Cleaned.csv`, which itself only includes MLB seasons with PA ≥ 300. A player with only short MLB cameos would be mislabeled as "Did Not Reach MLB" — a limitation of the data on hand, not something the current pipeline corrects for.
- **The ID-based join only recovered a handful of extra graduates.** Most of the ~220 graduates still missing a MiLB match are genuine data-coverage gaps (players who debuted before the 2006 start of MiLB stat tracking, or international signees who skipped affiliated ball), not name-matching bugs.
- **Exact name matching only.** No fuzzy search, so typos and nicknames return "not found".
- `app.secret_key` is hardcoded and `debug=True` — fine for a local demo, not for deployment.
