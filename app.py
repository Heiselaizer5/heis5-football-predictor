import streamlit as st
import pandas as pd
import numpy as np
import requests
import math

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -------------------------------------------------------------------------
st.set_page_config(page_title="HEIS5 Multi-Source Predictor", page_icon="⚽", layout="wide")

st.title("⚽ Welcome to HEIS5 Match Predictor")

# -------------------------------------------------------------------------
# 2. COMPETITION REGISTRY MAPPING (Hybrid Setup)
# -------------------------------------------------------------------------
LEAGUE_MAP = {
    # Live API Competitions (Football-Data.org codes)
    "English Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": {"type": "api", "code": "PL"},
    "Spanish La Liga 🇪🇸": {"type": "api", "code": "PD"},
    "German Bundesliga 🇩🇪": {"type": "api", "code": "BL1"},
    "French Ligue 1 🇫🇷": {"type": "api", "code": "FL1"},
    "Portuguese Primeira Liga 🇵🇹": {"type": "api", "code": "PPL"},
    
    # Local CSV Datasets (Stored in your GitHub Repo)
    "FIFA World Cup 2026 🏆": {"type": "csv", "file": "world_cup.csv"},
    "UEFA Champions League 🇪🇺": {"type": "csv", "file": "ucl.csv"},
    "English Championship 🇬🇧": {"type": "csv", "file": "championship.csv"},
    "Dutch Eredivisie 🇳🇱": {"type": "csv", "file": "netherlands.csv"}
}

# 🛠️ Paste your Football-Data.org API token here inside the quotes
API_TOKEN = "d7bf2e7e47344436b3571ff11c6639c6"

# -------------------------------------------------------------------------
# 3. HYBRID DATA LOADING SYSTEM
# -------------------------------------------------------------------------
@st.cache_data(ttl=3600)
def load_competition_data(config):
    if config["type"] == "csv":
        try:
            df = pd.read_csv(config["file"])
            return df
        except Exception as e:
            st.error(f"❌ Error loading local file '{config['file']}': {str(e)}")
            return None
            
    elif config["type"] == "api":
        if API_TOKEN == "d7bf2e7e47344436b3571ff11c6639c6" or not API_TOKEN:
            st.warning("⚠️ Please insert your API Token to access live leagues.")
            return None
            
        url = f"https://api.football-data.org/v4/competitions/{config['code']}/standings"
        headers = {"X-Auth-Token": API_TOKEN}
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 403:
                st.error("❌ API Access Denied. Verify your token permissions.")
                return None
                
            data = response.json()
            standings = data['standings'][0]['table']
            
            team_data = []
            for row in standings:
                played = row['playedGames']
                gf = row['goalsFor']
                ga = row['goalsAgainst']
                
                team_data.append({
                    "team_name": row['team']['name'],
                    "matches_played": played if played > 0 else 1,
                    "goals_scored": gf,
                    "goals_conceded": ga,
                    "corners_won": int(gf * 2.3 + played * 2),
                    "cards_received": int(ga * 1.1 + played * 1.6)
                })
            return pd.DataFrame(team_data)
        except Exception as e:
            st.error(f"❌ Server Connection Error: {str(e)}")
            return None

# -------------------------------------------------------------------------
# 4. SIDEBAR CONTROL PANEL
# -------------------------------------------------------------------------
st.sidebar.header("🛠️ Prediction Setup")
selected_label = st.sidebar.selectbox("Select Competition:", list(LEAGUE_MAP.keys()))
config = LEAGUE_MAP[selected_label]

df_league = load_competition_data(config)

if df_league is not None:
    team_list = sorted(df_league['team_name'].unique())
    
    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("🏠 Home Team", team_list, index=0)
    with col2:
        default_away_idx = min(1, len(team_list) - 1)
        away_team = st.selectbox("🚀 Away Team", team_list, index=default_away_idx)

    # -------------------------------------------------------------------------
    # 5. PREDICTION SIMULATION ENGINE (Poisson Math)
    # -------------------------------------------------------------------------
    if st.button("🔮 Run HEIS5 Match Simulation", use_container_width=True):
        home_stats = df_league[df_league['team_name'] == home_team].iloc[0]
        away_stats = df_league[df_league['team_name'] == away_team].iloc[0]
        
        avg_goals_scored = df_league['goals_scored'].sum() / df_league['matches_played'].sum()
        
        # --- GOALS PROJECTIONS ---
        home_att = home_stats['goals_scored'] / home_stats['matches_played']
        home_def = home_stats['goals_conceded'] / home_stats['matches_played']
        away_att = away_stats['goals_scored'] / away_stats['matches_played']
        away_def = away_stats['goals_conceded'] / away_stats['matches_played']
        
        exp_home_goals = (home_att * (away_def / (avg_goals_scored if avg_goals_scored > 0 else 1))) * 1.10
        exp_away_goals = away_att * (home_def / (avg_goals_scored if avg_goals_scored > 0 else 1))
        
        # --- CORNERS & CARDS PROJECTIONS ---
        home_corners_avg = home_stats['corners_won'] / home_stats['matches_played']
        away_corners_avg = away_stats['corners_won'] / away_stats['matches_played']
        exp_total_corners = home_corners_avg + away_corners_avg
        
        home_cards_avg = home_stats['cards_received'] / home_stats['matches_played']
        away_cards_avg = away_stats['cards_received'] / away_stats['matches_played']
        exp_total_cards = home_cards_avg + away_cards_avg
        
        # --- SCORE MATRIX ---
        max_g = 6
        home_poisson = [np.exp(-exp_home_goals) * (exp_home_goals**i) / math.factorial(i) for i in range(max_g)]
        away_poisson = [np.exp(-exp_away_goals) * (exp_away_goals**j) / math.factorial(j) for j in range(max_g)]
        score_matrix = np.outer(home_poisson, away_poisson)
        best_score_idx = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)
        predicted_score = f"{best_score_idx[0]} - {best_score_idx[1]}"
        
        # -------------------------------------------------------------------------
        # 6. GRAPHICAL DASHBOARD DISPLAY (Native Metrics Engine)
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.subheader("📊 Analytical Projections Matrix")
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.metric(label="🏆 PREDICTED SCORE", value=predicted_score)
        with m_col2:
            st.metric(label="⚽ TOTAL GOALS", value=f"{exp_home_goals + exp_away_goals:.2f}")
        with m_col3:
            st.metric(label="🚩 EXPECTED CORNERS", value=f"{exp_total_corners:.1f}")
        with m_col4:
            st.metric(label="🟨 EXPECTED CARDS", value=f"{exp_total_cards:.1f}")