"""One-time migration: appends data/milb_2025_stats.csv (2025 season MiLB
stats, sourced separately from the FanGraphs export that data/milbHitterIndicators.csv
originally came from) into data/milbHitterIndicators.csv so the rest of the
pipeline (dataCleaning.py -> CleaningMLBData.py -> merge.py -> train.py)
picks up the new season automatically.

data/milb_2025_stats.csv has no header/PlayerId and stores percentages as
strings (e.g. "14.40%") instead of milbHitterIndicators.csv's fraction floats
(0.144), so it needs reshaping before it can be appended. It also has no
FanGraphs PlayerId column at all: for names that already appear in
milbHitterIndicators.csv, this reuses that player's existing id (preferring a
numeric post-debut id over an "sa..." placeholder, same preference
dataCleaning.py's pick_id already applies downstream); for names with no
prior season in the file, a synthetic "MILB2025_<n>" placeholder id is
assigned. That id is deliberately non-numeric so merge.py's numeric-id join
against MLB_Cleaned.csv can never mistake it for a real graduate.

The new file's names carry accents the existing export sometimes drops for
the same player (e.g. history has unaccented "Jesus Made", but the new file's
2025 row is "Jesus Made" with the accent). Both dataCleaning.py and merge.py
key players by exact Name string, so left alone this forks one real player's
history into two separate rows. Where a new name's accent-stripped form
uniquely matches one existing historical name, this rewrites the new row to
that historical spelling before anything else runs, so grouping and the
PlayerId lookup both see one player. A normalized form matching more than one
distinct historical spelling is left alone rather than guessed at, same as
merge.py's existing policy for ambiguous Name collisions.

Safe to re-run: exits without writing if Season 2025 rows are already present.
"""

import csv
import unicodedata

import pandas as pd


def strip_accents(name):
    return ''.join(c for c in unicodedata.normalize('NFD', name) if unicodedata.category(c) != 'Mn')

INDICATORS_PATH = 'data/milbHitterIndicators.csv'
NEW_STATS_PATH = 'data/milb_2025_stats.csv'

indicators = pd.read_csv(INDICATORS_PATH)

if (indicators['Season'] == 2025).any():
    print('2025 season already present in milbHitterIndicators.csv -- nothing to do.')
    raise SystemExit(0)

# mac_roman: the file was exported with accented names (Peña, José, Pérez,
# etc.) mis-decoding under utf-8/cp1252/latin-1; mac_roman round-trips them
# correctly.
new = pd.read_csv(
    NEW_STATS_PATH, header=None, encoding='mac_roman',
    names=['Rank', 'Season', 'Name', 'Level', 'Age', 'PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+'],
)
# Tolerate an optional header line (the source file has shipped both with and
# without one) -- if the first row's Rank isn't numeric, it's a header, not data.
if not str(new.iloc[0]['Rank']).strip().isdigit():
    new = new.iloc[1:].reset_index(drop=True)
new = new.drop(columns=['Rank'])

for col in ['BB%', 'K%', 'GB%']:
    new[col] = new[col].str.rstrip('%').astype(float) / 100

# Reconcile accent-only spelling drift against history (see module docstring)
# before any Name-keyed lookup or grouping happens downstream.
old_names = set(indicators['Name'])
norm_to_names = {}
for n in old_names:
    norm_to_names.setdefault(strip_accents(n), set()).add(n)

def reconcile_name(name):
    if name in old_names:
        return name
    candidates = norm_to_names.get(strip_accents(name))
    if candidates and len(candidates) == 1:
        return next(iter(candidates))
    return name

renamed = new['Name'].map(reconcile_name)
changed = (renamed != new['Name']).sum()
new['Name'] = renamed

# Prefer a numeric (post-debut) id over an "sa..." placeholder, mirroring
# dataCleaning.py's pick_id; break remaining ties by most recent season so a
# stale placeholder doesn't win over a fresher one.
by_recency = indicators.sort_values('Season', ascending=False)
numeric_ids = by_recency[by_recency['PlayerId'].astype(str).str.isdigit()]
placeholder_ids = by_recency[~by_recency['PlayerId'].astype(str).str.isdigit()]
id_lookup = (
    pd.concat([numeric_ids, placeholder_ids])
    .drop_duplicates(subset='Name', keep='first')
    .set_index('Name')['PlayerId']
)

new['PlayerId'] = new['Name'].map(id_lookup)
missing = new['PlayerId'].isna()
new.loc[missing, 'PlayerId'] = [f'MILB2025_{i}' for i in range(missing.sum())]

new = new[['Season', 'Name', 'Level', 'Age', 'PA', 'BB%', 'K%', 'ISO', 'GB%', 'wRC+', 'PlayerId']]

combined = pd.concat([indicators, new], ignore_index=True)
combined.to_csv(INDICATORS_PATH, index=False, quoting=csv.QUOTE_NONNUMERIC)

print(f'Reconciled {changed} accent-spelling mismatches against existing history.')
print(f'Appended {len(new)} rows for the 2025 season ({missing.sum()} new players got a synthetic PlayerId).')
print(f'{INDICATORS_PATH} now has {len(combined)} total rows.')
