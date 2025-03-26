# Set CRAN mirror
options(repos = "https://cran.rstudio.com/")

if (!requireNamespace("devtools", quietly = TRUE)) {
  install.packages("devtools")
}
# Install worldfootballR from GitHub
devtools::install_github("JaseZiv/worldfootballR")

# Load required libraries
library(worldfootballR)
library(dplyr)

# Define the Big 5 leagues and seasons
big5_leagues <- c("England", "Spain", "Italy", "Germany", "France")
seasons <- c(2023, 2024)

# Rest of your script...
get_team_urls <- function(league, season) {
  tm_league_team_urls(country_name = league, start_year = season)
}

team_urls_list <- lapply(seasons, function(season) {
  lapply(big5_leagues, function(league) {
    data.frame(
      league = league,
      season = season,
      team_url = get_team_urls(league, season)
    )
  }) %>% bind_rows()
}) %>% bind_rows()

get_transfers <- function(team_urls, season) {
  tm_team_transfers(team_url = team_urls, transfer_window = "all")
}

transfers_list <- lapply(seasons, function(season) {
  season_urls <- team_urls_list %>% filter(season == !!season) %>% pull(team_url)
  transfers <- get_transfers(season_urls, season)
  transfers$season_start <- season
  return(transfers)
})

all_transfers <- bind_rows(transfers_list)

transfers_cleaned <- all_transfers %>%
  select(
    season = season_start,
    league = country,
    transfer_type,
    player_name,
    player_position,
    player_age,
    from_club = club_2,
    from_league = league_2,
    from_country = country_2,
    to_club = club_name,
    to_league = league_name,
    to_country = country,
    transfer_fee
  ) %>%
  mutate(
    transfer_fee = as.numeric(transfer_fee) / 1000000
  )

big5_transfers <- transfers_cleaned %>%
  filter(to_league %in% c("Premier League", "LaLiga", "Serie A", "Bundesliga", "Ligue 1"))

write.csv(big5_transfers, "big5_league_transfers_2023_2024.csv", row.names = FALSE)