import pandas as pd

milbHitters = pd.read_csv("milbHitterIndicators.csv")
milbHitters.dropna(inplace = True)

def avg_by_PA(stat, PA):
    return (stat * PA).sum() / PA.sum()

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
        loLevelpa = 0
        loLevelStatList = []
        loLevelPAList = []
        for year in loLevel:
            loLevelpa += year[2]
            loLevelStatList.append(year[0])
            loLevelPAList.append(year[2])
        loLevelStatList = pd.Series(loLevelStatList)
        loLevelPAList = pd.Series(loLevelPAList)
        loLevelAvg = avg_by_PA(loLevelStatList, loLevelPAList)
    
    TotalPA = loLevelpa + AApa + AAApa
    WeightedPA = (loLevelpa + 2*AApa + 3*AAApa)

    weightedStat1 = (loLevelAvg*loLevelpa + 2*AAavg*AApa + 3*AAAavg*AAApa) / WeightedPA
    weightedStat2 = (loLevelAvg + 2*AAavg + 3*AAAavg) / 6
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
        'wRC+': avg_by_PA(g['wRC+'], g['PA'])
    }), include_groups=False
).reset_index(drop=True)

# Uses weighted averages
cleanedStats = playerStats.groupby(['Name']).apply(
    lambda g: pd.Series({
        'Name': g.name,
        'PA': g['PA'].sum(),
        'BB%': stat_by_weight(g['BB%'], g['Level'], g['PA']),
        'K%': stat_by_weight(g['K%'], g['Level'], g['PA']),
        'ISO': stat_by_weight(g['ISO'], g['Level'], g['PA']),
        'GB%': stat_by_weight(g['GB%'], g['Level'], g['PA']),
        'wRC+': stat_by_weight(g['wRC+'], g['Level'], g['PA'])
    }), include_groups=False
).reset_index(drop=True)

'''
judge = playerStats.query('Name == "Aaron Judge"')

cleanedStats = judge.groupby(['Name']).apply(
    lambda g: pd.Series({
        'Name': g.name,
        'PA': g['PA'].sum(),
        'BB%': stat_by_weight(g['BB%'], g['Level'], g['PA']),
        'K%': stat_by_weight(g['K%'], g['Level'], g['PA']),
        'ISO': stat_by_weight(g['ISO'], g['Level'], g['PA']),
        'GB%': stat_by_weight(g['GB%'], g['Level'], g['PA']),
        'wRC+': stat_by_weight(g['wRC+'], g['Level'], g['PA'])
    }), include_groups=False
).reset_index(drop=True)
'''

print(cleanedStats.head(10))

print(cleanedStats.query('Name == "Aaron Judge" or Name == "Mike Trout" or Name == "Jarren Duran"'))

# cleanedStats.to_csv('weightedMiLBStats.csv', index=False)