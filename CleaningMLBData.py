import pandas as pd

# Load the CSV file into a DataFrame
df = pd.read_csv('data/MLB_Cleaned.csv')

# Ensure the column names match your dataset (adjust 'player' and 'season' if necessary)
# Group by player and calculate their total number of seasons and latest season
player_summary = df.groupby('Name').agg(
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
player_summary = player_summary.drop(columns=['wRCavg'])
player_summary.to_csv('data/MLB_GroupedSimple.csv', index=False)