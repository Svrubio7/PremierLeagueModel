import pandas as pd

df1 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_1ST.csv")
df2 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_2ND.csv")
df3 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_ALL.csv")

'''df1.drop(columns=["match_id"], inplace=True)
df2.drop(columns=["match_id"], inplace=True)
df3.drop(columns=["match_id"], inplace=True)'''

df1.to_excel("/Users/jd/Documents/PremierLeagueModel/matches_1ST.xlsx", index=False)
df2.to_excel("/Users/jd/Documents/PremierLeagueModel/matches_2ND.xlsx", index=False)
df3.to_excel("/Users/jd/Documents/PremierLeagueModel/matches_ALL.xlsx", index=False)
