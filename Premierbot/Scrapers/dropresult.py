import pandas as pd

df1 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_1ST.csv")
df2 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_2ND.csv")
df3 = pd.read_csv("/Users/jd/Documents/PremierLeagueModel/matches_ALL.csv")

df1.drop(columns=["RESULT"], inplace=True)
df2.drop(columns=["RESULT"], inplace=True)
df3.drop(columns=["RESULT"], inplace=True)

df1.to_csv("/Users/jd/Documents/PremierLeagueModel/matches_1ST.csv", index=False)
df2.to_csv("/Users/jd/Documents/PremierLeagueModel/matches_2ND.csv", index=False)
df3.to_csv("/Users/jd/Documents/PremierLeagueModel/matches_ALL.csv", index=False)
