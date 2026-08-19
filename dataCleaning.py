import pandas as pd

milbHitters = pd.read_csv("data/milbHitterIndicators.csv")
milbHitters.dropna(inplace = True)

# Averages a stat weighted by PAs, takes pandas series as arguments
def avg_by_PA(stat, PA):
    return (stat * PA).sum() / PA.sum()

# Age relative to the PA-weighted average age at that level in that season --
# turns raw age into a performance-like signal (negative = young for the
# competition, a good sign) instead of a purely physical one. Season matters
# alongside Level since age norms per level drift year to year.
levelAge = milbHitters.groupby(['Season', 'Level']).apply(
    lambda g: avg_by_PA(g['Age'], g['PA']), include_groups=False
).reset_index(name='LevelAvgAge')
milbHitters = milbHitters.merge(levelAge, on=['Season', 'Level'], how='left')
milbHitters['AgeRelLevel'] = milbHitters['Age'] - milbHitters['LevelAvgAge']

# Picks one PlayerId to represent a player. FanGraphs tags a player's
# pre-debut minor-league seasons with a placeholder "sa..." id and switches to
# their numeric id once they reach affiliated ball's ID system, so prefer a
# numeric id (needed to join against MLB_Cleaned's IDfg in merge.py) and fall
# back to whatever id is present otherwise.
def pick_id(ids):
    numeric = [i for i in ids if str(i).isdigit()]
    return numeric[0] if numeric else ids.iloc[0]

# Returns a new value for a given statistic based on weighting formula, takes pandas series as arguments
def stat_by_weight(stat, level, PA):
    temp = zip(stat, level, PA)
    seasons = []
    for year in temp:
        seasons.append(list(year))

    AAA = [x for x in seasons if x[1] == 'AAA']
    AA = [x for x in seasons if x[1] == 'AA']
    loLevel = [x for x in seasons if (x[1] != 'AAA' and x[1] != 'AA')]

    if AAA == []:
        AAAavg = 0
        AAApa = 0
    else:
        AAAavg = AAA[0][0]
        AAApa = AAA[0][2]

    if AA == []:
        AAavg = 0
        AApa = 0
    else:
        AAavg = AA[0][0]
        AApa = AA[0][2]
    
    if loLevel == []:
        loLevelpa = 0
        loLevelAvg = 0
    else:
        loLevelStatList = [x[0] for x in loLevel]
        loLevelPAList = [x[2] for x in loLevel]
        loLevelpa = sum(loLevelPAList)
        loLevelStatList = pd.Series(loLevelStatList)
        loLevelPAList = pd.Series(loLevelPAList)
        loLevelAvg = avg_by_PA(loLevelStatList, loLevelPAList)
    
    WeightedPA = (loLevelpa + 2*AApa + 3*AAApa)
    
    # Creates denominator for second stat based on the levels the player has data for
    levelsWeight = 0
    listOfLevelPAs = [loLevelpa, AApa, AAApa]
    for i in range(0, 3):
        if listOfLevelPAs[i] != 0:
            levelsWeight += i + 1

    # Weighted based on level and PA count
    weightedStat1 = (loLevelAvg*loLevelpa + 2*AAavg*AApa + 3*AAAavg*AAApa) / WeightedPA
    # Weighted just on levels
    weightedStat2 = (loLevelAvg + 2*AAavg + 3*AAAavg) / levelsWeight
    # Blends above two values
    weightedStat = (3*weightedStat1 + 2*weightedStat2) / 5
    return weightedStat

# Averages each level
playerStats = milbHitters.groupby(['Name', 'Level']).apply(
    lambda g: pd.Series({
        'Name': g.name[0],
        'Level': g.name[1],
        'PA': g['PA'].sum(),
        'BB%': avg_by_PA(g['BB%'], g['PA']),
        'K%': avg_by_PA(g['K%'], g['PA']),
        'ISO': avg_by_PA(g['ISO'], g['PA']),
        'GB%': avg_by_PA(g['GB%'], g['PA']),
        'wRC+': avg_by_PA(g['wRC+'], g['PA']),
        'Age': avg_by_PA(g['Age'], g['PA']),
        'AgeRelLevel': avg_by_PA(g['AgeRelLevel'], g['PA']),
        'PlayerId': pick_id(g['PlayerId'])
    }), include_groups=False
).reset_index(drop=True)

print(playerStats.query('Name == "Bryce Harper"'))

# Uses weighted averages
cleanedStats = playerStats.groupby(['Name']).apply(
    lambda g: pd.Series({
        'Name': g.name,
        'PA': g['PA'].sum(),
        'BB%': stat_by_weight(g['BB%'], g['Level'], g['PA']),
        'K%': stat_by_weight(g['K%'], g['Level'], g['PA']),
        'ISO': stat_by_weight(g['ISO'], g['Level'], g['PA']),
        'GB%': stat_by_weight(g['GB%'], g['Level'], g['PA']),
        'wRC+': stat_by_weight(g['wRC+'], g['Level'], g['PA']),
        'Age': stat_by_weight(g['Age'], g['Level'], g['PA']),
        'AgeRelLevel': stat_by_weight(g['AgeRelLevel'], g['Level'], g['PA']),
        'PlayerId': pick_id(g['PlayerId'])
    }), include_groups=False
).reset_index(drop=True)

# Tests
print(cleanedStats.head(10))
print(cleanedStats.query('Name == "Aaron Judge" or Name == "Bryce Harper" or Name == "Jarren Duran"'))

# Exports data to csv
cleanedStats.to_csv('weightedMiLBStats.csv', index=False)