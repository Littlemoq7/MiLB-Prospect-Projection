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


def search_player_names(query, limit=10):
    """Return up to `limit` player names containing `query` (case-insensitive).

    Names starting with the query are ranked ahead of names that merely
    contain it, since that's the more likely intent while typing.
    """
    query = (query or '').strip().lower()
    if not query:
        return []

    names = milbHitters['Name'].unique()
    starts_with = sorted(name for name in names if name.lower().startswith(query))
    contains = sorted(
        name for name in names
        if query in name.lower() and not name.lower().startswith(query)
    )
    return (starts_with + contains)[:limit]


def predict_manual(feature_values):
    """Predict an MLB performance tier from manually entered stat values.

    feature_values: dict with a numeric value for every name in FEATURES.
    Returns a dict shaped like one entry from predict_players' output list.
    """
    row = [[float(feature_values[feature]) for feature in FEATURES]]
    probabilities = model.predict_proba(row)[0]

    # predict_proba's columns follow model.classes_ (the 0/1/2/3 category
    # codes), so map each column back to its label rather than assuming order.
    labels = [CATEGORY_LABELS[category] for category in model.classes_]

    top = int(probabilities.argmax())
    return {
        'category': labels[top],
        'confidence': float(probabilities[top]),
        'probabilities': {label: float(p) for label, p in zip(labels, probabilities)},
    }


# --- Manual entry, season by season -----------------------------------------
# Reproduces the level-weighting CleaningMLBData.py/dataCleaning.py used to
# build weightedMiLBStats.csv, so seasons entered by hand get aggregated (and
# AgeRelLevel derived) the same way as every other player's data instead of
# asking the user to supply a derived stat they have no way to know.

_milbIndicators = pd.read_csv('data/milbHitterIndicators.csv').dropna()

_LEVEL_ORDER = ['DSL', 'CPX', 'R', 'A-', 'A', 'A+', 'AA', 'AAA']
_available_levels = set(_milbIndicators['Level'].unique())
LEVELS = [level for level in _LEVEL_ORDER if level in _available_levels]

SEASON_FIELDS = ['Season', 'Level', 'PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+', 'Age']
_SEASON_STAT_COLUMNS = ['BB%', 'K%', 'ISO', 'GB%', 'wRC+', 'Age', 'AgeRelLevel']


def _avg_by_pa(stat, pa):
    return (stat * pa).sum() / pa.sum()


# PA-weighted average age at each (season, level) on file, for turning a raw
# age into AgeRelLevel the same way dataCleaning.py does.
_LEVEL_AVG_AGE_BY_SEASON = {
    key: _avg_by_pa(group['Age'], group['PA'])
    for key, group in _milbIndicators.groupby(['Season', 'Level'])
}
# Fallback for a season outside the historical data on file (e.g. the current
# season): PA-weighted average age at that level across all seasons.
_LEVEL_AVG_AGE = {
    level: _avg_by_pa(group['Age'], group['PA'])
    for level, group in _milbIndicators.groupby('Level')
}


def _weighted_across_levels(level_rows, column):
    """Combines one row per level into a single value: AAA counts 3x, AA 2x,
    and every other level counts 1x (pooled together first). Mirrors
    CleaningMLBData.py's stat_by_weight, operating on already-per-level rows.
    """
    by_level = {row['Level']: row for row in level_rows}
    other = [row for row in level_rows if row['Level'] not in ('AAA', 'AA')]

    aaa_val, aaa_pa = (by_level['AAA'][column], by_level['AAA']['PA']) if 'AAA' in by_level else (0, 0)
    aa_val, aa_pa = (by_level['AA'][column], by_level['AA']['PA']) if 'AA' in by_level else (0, 0)
    if other:
        other_pa = sum(row['PA'] for row in other)
        other_val = sum(row[column] * row['PA'] for row in other) / other_pa
    else:
        other_pa, other_val = 0, 0

    weighted_pa = other_pa + 2 * aa_pa + 3 * aaa_pa
    levels_weight = sum(weight for weight, pa in ((1, other_pa), (2, aa_pa), (3, aaa_pa)) if pa != 0)

    by_pa = (other_val * other_pa + 2 * aa_val * aa_pa + 3 * aaa_val * aaa_pa) / weighted_pa
    by_level_only = (other_val + 2 * aa_val + 3 * aaa_val) / levels_weight
    return (3 * by_pa + 2 * by_level_only) / 5


def aggregate_season_rows(rows):
    """Turns individually entered MiLB seasons into one aggregate feature row
    ready for predict_manual.

    rows: list of dicts, each with Season (int), Level (str, one of LEVELS),
    PA (float > 0), and a numeric value for BB%, K%, ISO, GB%, wRC+, Age.
    """
    if not rows:
        raise ValueError('Enter at least one season.')

    enriched = []
    for row in rows:
        if row['Level'] not in LEVELS:
            raise ValueError(f"Unknown level \"{row['Level']}\".")
        if row['PA'] <= 0:
            raise ValueError('PA must be greater than 0.')
        level_avg_age = _LEVEL_AVG_AGE_BY_SEASON.get(
            (row['Season'], row['Level']), _LEVEL_AVG_AGE[row['Level']]
        )
        enriched.append({**row, 'AgeRelLevel': row['Age'] - level_avg_age})

    # Stage 1: PA-weighted average per level, across however many seasons
    # were entered at that level (mirrors dataCleaning.py's (Name, Level)
    # groupby).
    by_level = {}
    for row in enriched:
        by_level.setdefault(row['Level'], []).append(row)

    level_rows = []
    for level, seasons in by_level.items():
        pa_total = sum(row['PA'] for row in seasons)
        level_row = {'Level': level, 'PA': pa_total}
        for column in _SEASON_STAT_COLUMNS:
            level_row[column] = sum(row[column] * row['PA'] for row in seasons) / pa_total
        level_rows.append(level_row)

    # Stage 2: combine levels the same way stat_by_weight does.
    result = {'PA': sum(row['PA'] for row in level_rows)}
    for column in _SEASON_STAT_COLUMNS:
        result[column] = _weighted_across_levels(level_rows, column)
    return result


def predict_from_seasons(rows):
    """Predict an MLB performance tier from individually entered MiLB
    seasons, aggregating them the same way the training data was built."""
    return predict_manual(aggregate_season_rows(rows))
