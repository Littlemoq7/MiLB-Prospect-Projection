import pandas as pd


stats_df = pd.read_csv('weightedMiLBStats.csv')
categories_df = pd.read_csv('data/MLB_GroupedSimple.csv')

# Join on PlayerId first -- it's collision-free, unlike Name (444 MiLB names
# map to more than one distinct PlayerId). Only categories_df rows with a
# numeric (post-debut) PlayerId can match this way; MiLB-only "sa..." ids
# never appear in stats_df under the same value as a graduate's IDfg.
is_numeric_id = categories_df['PlayerId'].astype(str).str.isdigit()
id_matched = pd.merge(
    categories_df[is_numeric_id], stats_df, on='PlayerId', how='inner', suffixes=('', '_milb')
).drop(columns=['Name_milb'])

# Fall back to a Name join for whatever didn't match by id -- except where the
# Name match's own PlayerId is numeric and disagrees with categories_df's
# PlayerId (e.g. "Jose Reyes", "Matt Duffy"): that's positive evidence of two
# different real players sharing a name, not a missing id, so attaching that
# row would silently blend in the wrong player's minor-league stats. Leave
# those unmatched instead of guessing.
unmatched = categories_df[~categories_df['Name'].isin(id_matched['Name'])]
name_lookup = pd.merge(unmatched, stats_df[['Name', 'PlayerId']], on='Name', how='left', suffixes=('', '_milb'))
milb_id_numeric = name_lookup['PlayerId_milb'].astype(str).str.isdigit()
is_collision = milb_id_numeric & (name_lookup['PlayerId_milb'].astype(str) != name_lookup['PlayerId'].astype(str))
safe_unmatched = unmatched[~unmatched['Name'].isin(name_lookup.loc[is_collision, 'Name'])]
name_matched = pd.merge(safe_unmatched, stats_df, on='Name', how='inner', suffixes=('', '_milb')).drop(columns=['PlayerId_milb'])

merged_df = pd.concat([id_matched, name_matched], ignore_index=True).drop_duplicates(subset='Name')

# Save the final merged dataframe to a new CSV
merged_df.to_csv('mergedOutput.csv', index=False)

print(f'Matched by PlayerId : {len(id_matched)}')
print(f'Matched by Name      : {len(name_matched)}')
print(f'Total merged rows    : {len(merged_df)} / {len(categories_df)} labeled players')
print("Merged CSV saved as 'mergedOutput.csv'")