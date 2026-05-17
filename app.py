import streamlit as st
import pandas as pd
import numpy as np
import requests

# -------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & STYLING
# -------------------------------------------------------------------------
st.set_page_config(page_title="HEIS5 Live Match Predictor", page_icon="⚽", layout="wide")

st.markdown("""
    <style>
    .main-header { font-size: 36px; font-weight: bold; color: #1E3A8A; text-align: center; margin-bottom: 20px; }
    .section-header { font-size: 22px; font-weight: bold; color: #1F2937; margin-top: 15px; margin-bottom: 15px; }
    .metric-box { padding: 15px; background-color: #F3F4F6; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .vs-text { font-size: 28px; font-weight: bold; text-align: center; margin-top: 35px; color: #4B5563; }
    </style>
""", unsafe_allow_html=True)  # <-- Fixed this parameter right here!

st.markdown('<div class="main-header">⚽ HEIS5 Live Multi-League Match Predictor</div>', unsafe_allow_html=True) # <-- Fixed here too!
# -------------------------------------------------------------------------
# 2. LIVE LEAGUE REGISTRY MAPPING (API-Football IDs)
# -------------------------------------------------------------------------
# Instead of CSV files, we map leagues to their official API-Football IDs
LEAGUE_MAP = {
    "English Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": {"league_id": 39, "season": 2025},
    "German Bundesliga 🇩🇪": {"league_id": 78, "season": 2025},
    "Spanish La Liga 🇪🇸": {"league_id": 140, "season": 2025},
    "French Ligue 1 🇫🇷": {"league_id": 61, "season": 2025},
    "Portuguese Primeira Liga 🇵🇹": {"league_id": 94, "season": 2025},
    "Swiss Super League 🇨🇭": {"league_id": 207, "season": 2025},
    "Russian Premier League 🇷🇺": {"league_id": 235, "season": 2025},
    "Ukrainian Premier League 🇺🇦": {"league_id": 333, "season": 2025},
    "UAE Pro League 🇦🇪": {"league_id": 301, "season": 2025},
    "Oman Professional League 🇴🇲": {"league_id": 312, "season": 2025},
    "Turkish Süper Lig 🇹🇷": {"league_id": 203, "season": 2025},
    "USA Major League Soccer 🇺🇸": {"league_id": 253, "season": 2026},  # MLS runs on calendar years
    "Tanzanian Ligi Kuu 🇹🇿": {"league_id": 401, "season": 2025}
}

# Your API Key - input it directly here or use Streamlit secrets
API_KEY = "90f1333a79ec156e426803bf6c997d23" 

# -------------------------------------------------------------------------
# 3. LIVE DATA FETCHING & DATAFRAME GENERATION (DEBUGGING VERSION)
# -------------------------------------------------------------------------
@st.cache_data(ttl=3600)  
def load_live_league_data(league_id, season):
    url = "https://v3.football.api-sports.io/standings"
    headers = {
        'x-rapidapi-host': 'v3.football.api-sports.io',
        'x-rapidapi-key': API_KEY
    }
    params = {'league': league_id, 'season': season}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # Check if the API sent an error message back
        if "errors" in data and data["errors"]:
            st.error(f"❌ API Server Error Response: {data['errors']}")
            return None
            
        standings = data['response'][0]['league']['standings'][0]
        
        team_data = []
        for team in standings:
            team_name = team['team']['name']
            played = team['all']['played']
            goals_for = team['all']['goals']['for']
            goals_against = team['all']['goals']['against']
            
            corners_simulated = int(goals_for * 2.5 + played * 2) 
            cards_simulated = int(goals_against * 1.2 + played * 1.5)

            team_data.append({
                "team_name": team_name,
                "matches_played": played if played > 0 else 1,
                "goals_scored": goals_for,
                "goals_conceded": goals_against,
                "corners_won": corners_simulated,
                "cards_received": cards_simulated
            })
            
        return pd.DataFrame(team_data)
    except Exception as e:
        st.error(f"❌ Python Connection Error: {str(e)}")
        return None

# -------------------------------------------------------------------------
# 4. SIDEBAR CONTROL PANEL
# -------------------------------------------------------------------------
st.sidebar.header("🛠️ Prediction Setup")
selected_league_label = st.sidebar.selectbox("Select Competition:", list(LEAGUE_MAP.keys()))
league_info = LEAGUE_MAP[selected_league_label]

if API_KEY == "YOUR_API_FOOTBALL_KEY_HERE":
    st.info("💡 Please paste your API-Football Key into line 42 of your script to activate live data fetching.")
    df_league = None
else:
    df_league = load_live_league_data(league_info["league_id"], league_info["season"])

if df_league is not None:
    team_list = sorted(df_league['team_name'].unique())
    
    col1, col_vs, col2 = st.columns([4, 1, 4])
    with col1:
        home_team = st.selectbox("🏠 Home Team", team_list, index=0)
    with col_vs:
        st.markdown('<div class="vs-text">VS</div>', unsafe_content_html=True)
    with col2:
        default_away_idx = min(1, len(team_list) - 1)
        away_team = st.selectbox("🚀 Away Team", team_list, index=default_away_idx)

    # -------------------------------------------------------------------------
    # 5. PREDICTION SIMULATION ENGINE
    # -------------------------------------------------------------------------
    if st.button("🔮 Run HEIS5 Live Match Simulation", use_container_width=True):
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
        
        # --- SCORE MATRIX (Poisson) ---
        max_g = 6
        home_poisson = [np.exp(-exp_home_goals) * (exp_home_goals**i) / np.math.factorial(i) for i in range(max_g)]
        away_poisson = [np.exp(-exp_away_goals) * (exp_away_goals**j) / np.math.factorial(j) for j in range(max_g)]
        score_matrix = np.outer(home_poisson, away_poisson)
        best_score_idx = np.unravel_index(np.argmax(score_matrix), score_matrix.shape)
        predicted_score = f"{best_score_idx[0]} - {best_score_idx[1]}"
        
        # -------------------------------------------------------------------------
        # 6. GRAPHICAL DASHBOARD DISPLAY
        # -------------------------------------------------------------------------
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Live Simulated Analytical Projections</div>', unsafe_content_html=True)
        
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(f'<div class="metric-box"><p style="margin:0; font-size:14px; color:#6B7280; font-weight:bold;">🏆 PREDICTED SCORE</p><p style="margin:5px 0 0 0; font-size:28px; color:#1E3A8A; font-weight:bold;">{predicted_score}</p></div>', unsafe_content_html=True)
        with m_col2:
            st.markdown(f'<div class="metric-box"><p style="margin:0; font-size:14px; color:#6B7280; font-weight:bold;">⚽ TOTAL GOALS</p><p style="margin:5px 0 0 0; font-size:28px; color:#10B981; font-weight:bold;">{exp_home_goals + exp_away_goals:.2f}</p></div>', unsafe_content_html=True)
        with m_col3:
            st.markdown(f'<div class="metric-box"><p style="margin:0; font-size:14px; color:#6B7280; font-weight:bold;">🚩 EXPECTED CORNERS</p><p style="margin:5px 0 0 0; font-size:28px; color:#F59E0B; font-weight:bold;">{exp_total_corners:.1f}</p></div>', unsafe_content_html=True)
        with m_col4:
            st.markdown(f'<div class="metric-box"><p style="margin:0; font-size:14px; color:#6B7280; font-weight:bold;">🟨 EXPECTED CARDS</p><p style="margin:5px 0 0 0; font-size:28px; color:#EF4444; font-weight:bold;">{exp_total_cards:.1f}</p></div>', unsafe_content_html=True)