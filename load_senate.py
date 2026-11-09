import pandas as pd

df = pd.read_csv('data/raw/1976-2024-senate-state.csv')

df.to_csv('data\processed/firstDF.csv') #for inspection

df['stage'] = df['stage'].str.lower() #fixes that it's sometimes all caps 

df = df[(df['party_simplified'] == "DEMOCRAT") | (df['party_simplified'] == "REPUBLICAN")]

df = df[['year', 'state_po', 'office', 'special', 'candidatevotes', 'party_simplified', 'stage']]


race_key = ['year', 'state_po', 'office', 'special']

dupes = df.groupby(race_key + ['party_simplified', 'stage']).size()
print(dupes[dupes > 1])

races = df.pivot_table(index=['year', 'state_po', 'special', 'office'], columns="party_simplified", values='candidatevotes')

races = races.dropna(subset=['DEMOCRAT', 'REPUBLICAN'])


# print(races.head())
# print(races.groupby(["year", "office"]).size())
# assert not races.duplicated(subset=race_key).any()