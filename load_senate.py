import pandas as pd

def apply_corrections(df):
    df = df.copy()

    df['stage'] = df['stage'].str.lower() #fixes that it's sometimes all caps 

    #deal with king and sanders
    caucus_d = df['candidate'].str.contains('BERNIE SANDERS|BERNARD SANDERS|ANGUS KING|ANGUS S. KING', na=False)
    print(df.loc[caucus_d, ['year', 'state_po', 'candidate', 'party_detailed', 'candidatevotes']])
    df.loc[caucus_d, 'party_simplified'] = 'DEMOCRAT'

    #catch the van hollen / duckworth issue
    for detailed, simplified in [(['DEMOCRAT', 'DEMOCRATIC'], 'DEMOCRAT'), (['REPUBLICAN'], 'REPUBLICAN')]:
        mislabeled = df['party_detailed'].isin(detailed) & (df['party_simplified'] != simplified)
        print(df[mislabeled])
        df.loc[mislabeled, 'party_simplified'] = simplified

    #label ossoff and warncock runoffs as source of truth for GA senate that cycle, and put them as 2020 to fit with economic data
    ga20 = (df.year == 2020) & (df.state_po == 'GA')
    ga21 = (df.year == 2021) & (df.state_po == 'GA')
    assert ga20.any() and ga21.any(), "GA rows not found"
    df = df[~ga20]
    df.loc[ga21, 'year'] = 2020

    return df

df = pd.read_csv('data/raw/1976-2024-senate-state.csv')

df.to_csv('data/processed/firstDF.csv') #for inspection

df = apply_corrections(df)
print(df['stage'].value_counts())


df = df[(df['party_simplified'] == "DEMOCRAT") | (df['party_simplified'] == "REPUBLICAN")]

df = df[['year', 'state_po', 'office', 'special', 'candidatevotes', 'party_simplified', 'stage']]

race_key = ['year', 'state_po', 'office', 'special']

races = df.pivot_table(index=['year', 'state_po', 'special', 'office'], columns="party_simplified", values='candidatevotes', aggfunc='sum').reset_index()

missing = races[races[['DEMOCRAT', 'REPUBLICAN']].isna().any(axis=1)]
print(missing) #check uncontested races
races = races.dropna(subset=['DEMOCRAT', 'REPUBLICAN'])

races['margin'] = (races['DEMOCRAT'] - races['REPUBLICAN']) / (races['DEMOCRAT'] + races['REPUBLICAN'])
print(races[(races.year == 2020) & (races.state_po == 'AZ')])

assert races['margin'].between(-1, 1).all()
assert not races.duplicated(subset=race_key).any()

print(races.sort_values('margin'))