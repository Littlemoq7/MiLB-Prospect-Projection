import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('data/MLB_Cleaned.csv')

# Group by player and calculate their career wRC+, weighted by PA. A plain
# mean of season wRC+ treats a 20-PA cameo the same as a 600-PA season, which
# can swing the average by 5-10 wRC+ points -- enough to flip a player across
# a cutoff below.
player_summary = df.groupby('Name').apply(
    lambda g: pd.Series({
        'wRCavg': (g['wRC+'] * g['PA']).sum() / g['PA'].sum(),
        'PlayerId': g['IDfg'].iloc[0]
    }), include_groups=False
).reset_index()
# The dict above is purely numeric (float wRCavg, int PlayerId) with no string
# to force object dtype, so pandas silently upcasts PlayerId to float64
# (15640 -> 15640.0). Cast back before it round-trips through a CSV as
# "15640.0" and stops string-matching weightedMiLBStats.csv's clean "15640".
player_summary['PlayerId'] = player_summary['PlayerId'].astype(int)

# Categorize players based on wRCavg
def categorize(wRCavg):
    if wRCavg < 95:
        return 1
    elif wRCavg >= 115:
        return 3
    else:
        return 2

player_summary['category'] = player_summary['wRCavg'].apply(categorize)
player_summary = player_summary.drop(columns=['wRCavg'])

# --- Survivorship bias -----------------------------------------------------
# Everything above only labels players who actually reached the majors, so
# the model never sees the much larger population of minor leaguers who
# didn't make it -- it can only rank graduates against each other, not learn
# what separates a future big leaguer from organizational depth. Label that
# population as category 0 ("Did Not Reach MLB"), restricted to players who've
# had a real chance to debut (last MiLB season 2018 or earlier -- 6+ years of
# runway as of this dataset's 2024 ceiling) and a real look (career MiLB PA
# >= 500, ruling out injury-shortened/token stints).
#
# Known limitation: "graduated" is defined as appearing in MLB_Cleaned.csv
# above, which itself only includes MLB seasons with PA >= 300. A player with
# only short MLB cameos would be mislabeled as "Did Not Reach MLB" here --
# accepted limitation of the data on hand, not fixed by this change.
milbHitters = pd.read_csv('data/milbHitterIndicators.csv')
milbHitters.dropna(inplace=True)
last_milb_season = milbHitters.groupby('Name')['Season'].max()

weightedMiLBStats = pd.read_csv('weightedMiLBStats.csv')

graduated_ids = set(player_summary['PlayerId'].astype(str))
graduated_names = set(player_summary['Name'])
already_graduated = (
    weightedMiLBStats['PlayerId'].astype(str).isin(graduated_ids)
    | weightedMiLBStats['Name'].isin(graduated_names)
)

candidates = weightedMiLBStats[
    ~already_graduated
    & (weightedMiLBStats['Name'].map(last_milb_season) <= 2018)
    & (weightedMiLBStats['PA'] >= 500)
]

non_graduates = pd.DataFrame({
    'Name': candidates['Name'],
    'PlayerId': candidates['PlayerId'],
    'category': 0
})

player_summary = pd.concat([player_summary, non_graduates], ignore_index=True)

print('category counts:', player_summary['category'].value_counts().sort_index().to_dict())
player_summary.to_csv('data/MLB_GroupedSimple.csv', index=False)