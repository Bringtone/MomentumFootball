import streamlit as st
import pandas as pd


@st.cache_data
def load_league_data(url):
    return pd.read_csv(url)


def calculate_momentum_score_and_details(matches):
    points_for_match = [6, 5, 4, 3, 2, 1]
    momentum_score = 0
    match_details = []

    for index, row in matches.iterrows():
        outcome = 'W' if row['Outcome'] == 'W' else 'L' if row['Outcome'] == 'L' else 'D'
        momentum_score += points_for_match[index] * (1 if outcome == 'W' else -1 if outcome == 'L' else 0)
        match_details.append((outcome, f"{row['GoalsFor']}-{row['GoalsAgainst']}", row['Opponent'], row['HomeAway']))
    return momentum_score, match_details


def fetch_and_prepare_matches(team, df):
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df.sort_values(by='Date', ascending=False, inplace=True)

    rows = []
    for _, row in df.iterrows():
        if len(rows) >= 6:
            break
        if row['HomeTeam'] == team:
            outcome = 'W' if row['FTR'] == 'H' else 'L' if row['FTR'] == 'A' else 'D'
            rows.append({
                'Date': row['Date'],
                'Opponent': row['AwayTeam'],
                'GoalsFor': row['FTHG'],
                'GoalsAgainst': row['FTAG'],
                'Outcome': outcome,
                'HomeAway': 'Home'
            })
        elif row['AwayTeam'] == team:
            outcome = 'W' if row['FTR'] == 'A' else 'L' if row['FTR'] == 'H' else 'D'
            rows.append({
                'Date': row['Date'],
                'Opponent': row['HomeTeam'],
                'GoalsFor': row['FTAG'],
                'GoalsAgainst': row['FTHG'],
                'Outcome': outcome,
                'HomeAway': 'Away'
            })

    matches = pd.DataFrame(rows)
    momentum_score, match_details = calculate_momentum_score_and_details(matches)
    return momentum_score, match_details


def calculate_bet_confidence(team1_momentum, team2_momentum):
    momentum_difference = abs(team1_momentum - team2_momentum)
    if momentum_difference >= 36:
        return momentum_difference, 'FREE MONEY'
    elif momentum_difference >= 29:
        return momentum_difference, 'SAFE'
    elif momentum_difference >= 22:
        return momentum_difference, 'GREAT'
    elif momentum_difference >= 15:
        return momentum_difference, 'GOOD'
    elif momentum_difference >= 8:
        return momentum_difference, 'TOO CLOSE TO CALL'
    else:
        return momentum_difference, 'RISKY'


def display_horizontal_table(teams, match_details_list, momentums, bet_confidence):
    num_matches = len(match_details_list[0])
    columns = ['Team'] + [f"Recent {i + 1}" for i in range(num_matches)] + ['Momentum']
    data = []
    for team, details, momentum in zip(teams, match_details_list, momentums):
        row = {}
        row['Team'] = team
        for i, d in enumerate(details):
            row[f"Recent {i + 1}"] = f"{d[0]} ({d[1]} {d[2]})"
        row['Momentum'] = momentum
        data.append(row)

    st.write(f"### {teams[0]} vs {teams[1]}")
    st.write(f"**Bet Confidence:** {bet_confidence[1]} (Difference: {bet_confidence[0]})")
    df_table = pd.DataFrame(data, columns=columns)
    st.table(df_table)


def analyze_matchup(team1, team2, data):
    momentum1, match_details1 = fetch_and_prepare_matches(team1, data.copy())
    momentum2, match_details2 = fetch_and_prepare_matches(team2, data.copy())
    bet_conf = calculate_bet_confidence(momentum1, momentum2)
    momentum_display1 = f"{momentum1} ({'OKAY' if momentum1 >= 0 else 'DISGUSTING'})"
    momentum_display2 = f"{momentum2} ({'OKAY' if momentum2 >= 0 else 'DISGUSTING'})"

    display_horizontal_table(
        [team1, team2],
        [match_details1, match_details2],
        [momentum_display1, momentum_display2],
        bet_conf
    )


# Mapping leagues to their CSV URLs
league_mapping = {
    "Premier League": "https://www.football-data.co.uk/mmz4281/2324/E0.csv",
    "Bundesliga": "https://www.football-data.co.uk/mmz4281/2324/D1.csv",
    "Serie A": "https://www.football-data.co.uk/mmz4281/2324/I1.csv",
    "La Liga": "https://www.football-data.co.uk/mmz4281/2324/SP1.csv",
    "Ligue 1": "https://www.football-data.co.uk/mmz4281/2324/F1.csv",
    "Eredivisie": "https://www.football-data.co.uk/mmz4281/2324/N1.csv",
    "Belgian Pro League": "https://www.football-data.co.uk/mmz4281/2324/B1.csv",
    "Primeira Liga": "https://www.football-data.co.uk/mmz4281/2324/P1.csv",
    "Turkish Super Lig": "https://www.football-data.co.uk/mmz4281/2324/T1.csv",
    "Greek Super League": "https://www.football-data.co.uk/mmz4281/2324/G1.csv"
}


def main():
    st.title("Football Momentum Analysis")
    st.markdown("Select a league and choose two teams to compare their recent momentum and bet confidence.")

    # League selection
    league_choice = st.selectbox("Choose a League", list(league_mapping.keys()))
    league_url = league_mapping[league_choice]

    # Load the league data and get unique teams
    data = load_league_data(league_url)
    teams = sorted(pd.concat([data["HomeTeam"], data["AwayTeam"]]).unique())

    # Team selection using dropdown menus
    team1 = st.selectbox("Choose Team 1", teams)
    team2 = st.selectbox("Choose Team 2", teams, index=1 if len(teams) > 1 else 0)

    if st.button("Analyze Matchup"):
        if team1 == team2:
            st.error("Please choose two different teams.")
        else:
            try:
                analyze_matchup(team1, team2, data)
            except Exception as e:
                st.error(f"Error processing data: {e}")


if __name__ == '__main__':
    main()
