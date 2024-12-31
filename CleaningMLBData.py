import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('MLB_Cleaned.csv')

# Ensure the column names match your dataset (adjust 'player' and 'season' if necessary)
# Group by player and calculate their total number of seasons and latest season
player_summary = df.groupby('Name').agg(
    total_seasons=('Season', 'count'),
    latest_season=('Season', 'max'),
    PAavg=('PA', 'mean'),
    wRCavg=('wRC+', 'mean')
).reset_index()

# Categorize players based on wRCavg
def categorize(wRCavg):
    if wRCavg < 100:
        return 1
    elif wRCavg > 120:
        return 3
    else:
        return 2

player_summary['category'] = player_summary['wRCavg'].apply(categorize)

# Filter for players with less than 3 seasons and latest season as 2023
filtered_players = player_summary[
    (player_summary['total_seasons'] < 3) & (player_summary['latest_season'] == 2023)
]

player_summary.to_csv('MLB_Grouped.csv', index=False)