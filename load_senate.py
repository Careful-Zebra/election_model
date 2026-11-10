import pandas as pd

def apply_corrections(df):
    df = df.copy()

    df['stage'] = df['stage'].str.lower() #fixes that it's sometimes all caps 

    #deal with king and sanders
    caucus_d = df['candidate'].str.contains('BERNIE SANDERS|BERNARD SANDERS|ANGUS KING|ANGUS S. KING', na=False)
    df.loc[caucus_d, 'party_simplified'] = 'DEMOCRAT'

    #fix WY 2020
    lummis = df['candidate'] == "CYNTHIA M. LUMMIS"
    df.loc[lummis, 'party_simplified'] = 'REPUBLICAN'
    merav = df['candidate'] == "MERAV BEN DAVID"
    df.loc[merav, 'party_simplified'] = 'DEMOCRAT'

    #fix GA 2000 and MS 2008
    mack = (df['candidate'] == "MACK F. MATTINGLY") & (df['year'] == 2000) & (df['state_po'] == 'GA')
    df.loc[mack, 'party_simplified'] = 'REPUBLICAN'
    ronnie = (df['candidate'] == "RONNIE MUSGROVE") & (df['year'] == 2008) & (df['state_po'] == 'MS')
    df.loc[ronnie, 'party_simplified'] = 'DEMOCRAT'

    #remove ak22 - R v R
    ak22 = (df.year == 2022) & (df.state_po == 'AK')
    df = df[~ak22]

    #catch the van hollen / duckworth issue
    for detailed, simplified in [(['DEMOCRAT', 'DEMOCRATIC'], 'DEMOCRAT'), (['REPUBLICAN'], 'REPUBLICAN')]:
        mislabeled = df['party_detailed'].isin(detailed) & (df['party_simplified'] != simplified)
        df.loc[mislabeled, 'party_simplified'] = simplified

    #label ossoff and warncock runoffs as source of truth for GA senate that cycle, and put them as 2020 to fit with economic data
    ga20 = (df.year == 2020) & (df.state_po == 'GA')
    ga21 = (df.year == 2021) & (df.state_po == 'GA')
    assert ga20.any() and ga21.any(), "GA rows not found"
    df = df[~ga20]
    df.loc[ga21, 'year'] = 2020

    #fix other GA runoffs
    ga22 = (df.year == 2022) & (df.state_po == 'GA')
    first_round = (df['stage'] == 'pre') | (ga22 & (df['stage'] == 'gen'))
    df = df[~first_round]

    #fix LA problems
    la02 = (df.year == 2002) & (df.state_po == 'LA')  
    la02prob = la02 & ((df['candidatevotes'] != 638654.0) & (df['candidatevotes'] != 596642.0))
    df = df[~la02prob]
    laCands = ['BILL CASSIDY', 'MARY L. LANDRIEU', 'JOHN KENNEDY', 'FOSTER CAMPBELL']
    la14 = (df.year == 2014) & (df.state_po == 'LA')
    la14prob = la14 & ~(df['candidate'].isin(laCands))
    df = df[~la14prob]
    la16 = (df.year == 2016) & (df.state_po == 'LA')
    la16prob = la16 & ~(df['candidate'].isin(laCands))
    df = df[~la16prob]
    df.loc[(df['candidate'] == "BILL CASSIDY") & (df['year'] == 2014), 'candidatevotes'] = 712379
    df.loc[(df['candidate'] == "MARY L. LANDRIEU") & (df['year'] == 2014), 'candidatevotes'] = 561210

    race = ['year', 'state_po', 'special']
    is_major = df['party_simplified'].isin(['DEMOCRAT', 'REPUBLICAN']) & df['candidate'].notna()
    lines = df.loc[is_major, race + ['candidate', 'party_simplified']].drop_duplicates()
    lines = lines.rename(columns={'party_simplified': 'candidate_party'})

    df = df.merge(lines, on=race + ['candidate'], how='left', validate='many_to_one')
    df['party_simplified'] = df['candidate_party'].fillna(df['party_simplified'])
    df = df.drop(columns='candidate_party')

    return df

df = pd.read_csv('data/raw/1976-2024-senate-state.csv')

df = apply_corrections(df)

race_key = ['year', 'state_po', 'office', 'special']

all_races = df[race_key].drop_duplicates()  

df = df[(df['party_simplified'] == "DEMOCRAT") | (df['party_simplified'] == "REPUBLICAN")]

df = df[['year', 'state_po', 'office', 'special', 'candidatevotes', 'party_simplified', 'stage']]

races = df.pivot_table(index=['year', 'state_po', 'special', 'office'], columns="party_simplified", values='candidatevotes', aggfunc='sum').reset_index()


missing = races[races[['DEMOCRAT', 'REPUBLICAN']].isna().any(axis=1)]
races = races.dropna(subset=['DEMOCRAT', 'REPUBLICAN'])

lost = all_races.merge(races[race_key], how='left', indicator=True)
print("lost: ")
print(len(lost[lost['_merge'] == 'left_only']))

races['margin'] = (races['DEMOCRAT'] - races['REPUBLICAN']) / (races['DEMOCRAT'] + races['REPUBLICAN'])

assert races['margin'].between(-1, 1).all()
assert not races.duplicated(subset=race_key).any()

print("races sorted by margin")
print(races.sort_values('margin'))

#add a column to the df of the margin of the previous election
def add_prev(df: pd.DataFrame): 
    df = df.copy()
    state_year = df.groupby(['state_po', 'year'], as_index=False)['margin'].mean()
    state_year = state_year.sort_values(['state_po', 'year'])
    state_year['prev_margin'] = state_year.groupby('state_po')['margin'].shift(1)
    state_year['prev_year'] = state_year.groupby('state_po')['year'].shift(1)
    df = df.merge(state_year[['state_po', 'year', 'prev_margin', 'prev_year']], on=['state_po', 'year'], how='left', validate='many_to_one')
    df = df.dropna(subset=['prev_margin']) #as the first races don't have a prev margin, they can't be used for model. Drop them.
    return df

races = add_prev(races)

print("races after add prev")
print(races)

print(races[(races['year'] == 1996) & (races['state_po'] == 'LA')])
print(races[(races['year'] == 2002) & (races['state_po'] == 'LA')])
print(races[(races['year'] == 2008) & (races['state_po'] == 'LA')])
print(races[(races['year'] == 2014) & (races['state_po'] == 'LA')])

races.to_csv('data/processed/senate_races.csv', index=False)

