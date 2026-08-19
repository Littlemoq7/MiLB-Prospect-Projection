import joblib
import pandas as pd

# The saved bundle carries the fitted StandardScaler inside the pipeline, so
# inference uses exactly the transform the model was trained with. Refitting a
# scaler here (the previous approach) produced slightly different means and
# scales than training did, skewing every prediction.
bundle = joblib.load('model.joblib')
model = bundle['model']
FEATURES = bundle['features']
CATEGORY_LABELS = bundle['labels']

milbHitters = pd.read_csv("weightedMiLBStats.csv")

# List of player names
playerNames = ["Roman Anthony", "Walker Jenkins", "Brooks Brannon", "Mike Trout", "Juan Soto"]


def predict_players(names):
    """Predict MLB performance tiers for the given player names.

    Returns (predictions, not_found). Name matching is exact.
    """
    matches = milbHitters[milbHitters['Name'].isin(names)]

    output = []
    if not matches.empty:
        # Select features by name so a column reorder in the CSV can't silently
        # feed the model the wrong values.
        probabilities = model.predict_proba(matches[FEATURES].values)

        # predict_proba's columns follow model.classes_ (the 0/1/2/3 category
        # codes), so map each column back to its label rather than assuming order.
        labels = [CATEGORY_LABELS[category] for category in model.classes_]

        for name, row in zip(matches['Name'], probabilities):
            top = int(row.argmax())
            output.append({
                'name': name,
                'category': labels[top],
                'confidence': float(row[top]),
                'probabilities': {label: float(p) for label, p in zip(labels, row)},
            })

    # Names that were requested but had no matching stats row
    found_names = set(matches['Name'])
    not_found = [name for name in names if name not in found_names]

    return output, not_found
