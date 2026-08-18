import pandas as pd


stats_df = pd.read_csv('weightedMiLBStats.csv')
categories_df = pd.read_csv('data/MLB_GroupedSimple.csv')

# Merge the two dataframes on the 'Name' column, keeping only rows that exist in both
merged_df = pd.merge(categories_df, stats_df, on='Name', how='inner')

# Save the final merged dataframe to a new CSV
merged_df.to_csv('mergedOutput.csv', index=False)

print("Merged CSV saved as 'mergedOutput.csv'")