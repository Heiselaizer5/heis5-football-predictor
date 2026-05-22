# -*- coding: utf-8 -*-
import streamlit as st
import numpy as np
import scipy.stats as stats
import json
import os
import hashlib
import requests

# Set global professional page layout
st.set_page_config(page_title="HEIS5 Football Predictor", page_icon="⚽", layout="wide")

# -------------------------------------------------------------------------
# 🎨 CUSTOM CSS STYLING INJECTION (PREMIUM DESIGN WITH FOOTBALL BACKGROUND)
# -------------------------------------------------------------------------
st.markdown("""
    <style>
    /* Main background with player kicking a ball and a dark dark overlay for text readability */
    .stApp {
        background-image: linear-gradient(rgba(14, 17, 23, 0.85), rgba(14, 17, 23, 0.85)), 
                          url('https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=1920&auto=format&fit=crop');
        background-size: cover;
        background-position: center center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }
    
    /* Top title styling */
    h1 {
        color: #ffffff !important;
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 800 !important;
        text-shadow: 0px 2px 4px rgba(0,0,0,0.4);
    }
    
    /* Custom CSS styled metric containers */
    .prediction-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #00ff66;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 15px;
    }
    .prediction-title {
        color: #9ca3af;
        font-size: 14px;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 5px;
    }
    .prediction-value {
        color: #ffffff;
        font-size: 24px;
        font-weight: 700;
    }
    
    /* Highlight Top Exact Scores list */
    .score-row {
        background-color: #1f2937;
        padding: 12px 20px;
        border-radius: 8px;
        margin-bottom: 8px;
        border: 1px solid #374151;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* Customizing the main action button */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00ff66 0%, #00cc52 100%) !important;
        color: #000000 !important;
        font-weight: bold !important;
        border: none !important;
        padding: 12px 24px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 12px rgba(0, 255, 102, 0.3) !important;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 255, 102, 0.5) !important;
    }
    
    /* Sidebar adjustments */
    [data-testid="stSidebar"] {
        background-color: #111827;
        border-right: 1px solid #1f2937;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------------------------------------------------------
# FOOTBALL-DATA.ORG API SYSTEM CONFIGURATION (HARDCODED & INVISIBLE)
# -------------------------------------------------------------------------
API_LEAGUES = {
    "English Premier League 🇬🇧": "PL",
    "English Championship 🇬🇧": "ELC",
    "Italian Serie A 🇮🇹": "SA",
    "Spanish La Liga 🇪🇸": "PD",
    "German Bundesliga 🇩🇪": "BL1",
    "French Ligue 1 🇫🇷": "FL1",
    "Netherlands Eredivisie 🇳🇱": "DED",
    "Portugal Primeira Liga 🇵🇹": "PPL",
    "UEFA Champions League 🇪🇺": "CL",
    "FIFA World Cup 🏆": "WC"
}
# 🔒 Hardcode your real football-data.org token string here inside the quotes:
API_TOKEN = "d7bf2e7e47344436b3571ff11c6639c6"
# Change from 3600 to 60 so it refreshes quickly when you test different matchups!
@st.cache_data(ttl=60)
def fetch_league_teams_and_stats(league_code, token):
    if not token or token == "YOUR_ACTUAL_FOOTBALL_DATA_API_KEY":
        return {}
    
    headers = {
        "X-Auth-Token": token,
        "X-Response-Control": "minified"
    }
    try:
        url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
        response = requests.get(url, headers=headers)
        
        # 🚨 DEBUG SYSTEM: If their server rejects us, show the exact reason!
        if response.status_code == 429:
            st.error("⚠️ API Error 429: You have hit the 10-requests-per-minute limit! Wait 1 minute and refresh.")
            return None
        elif response.status_code == 403:
            st.error("⚠️ API Error 403: Restricted League! ")
            return None
        elif response.status_code == 400 or response.status_code == 401:
            st.error("⚠️ API Error 401: Invalid Token! Check your email to make sure the key is correct and activated.")
            return None
        elif response.status_code != 200:
            st.error(f"⚠️ API Error {response.status_code}: Server issue ")
            return None
            
        data = response.json()
        processed_teams = {}
        
        if league_code in ["CL", "WC"]:
            standings_groups = data.get('standings', [])
            for group in standings_groups:
                for row in group.get('table', []):
                    team_name = row['team']['name']
                    played = row['playedGames'] if row['playedGames'] > 0 else 1
                    avg_scored = row['goalsFor'] / played
                    avg_conceded = row['goalsAgainst'] / played
                    processed_teams[team_name] = [avg_scored, avg_conceded, 5.2, 1.9]
        else:
            standings = data['standings'][0]['table']
            for row in standings:
                team_name = row['team']['name']
                played = row['playedGames'] if row['playedGames'] > 0 else 1
                avg_scored = row['goalsFor'] / played
                avg_conceded = row['goalsAgainst'] / played
                processed_teams[team_name] = [avg_scored, avg_conceded, 5.5, 1.8]
            
        return processed_teams
    except Exception as e:
        st.error(f"⚠️ Connection Error: {str(e)}")
        return None

# -------------------------------------------------------------------------
# 1. DATABASE & SECURE USER AUTHENTICATION SYSTEM
# -------------------------------------------------------------------------
USER_DB_FILE = "users_db.json"

def load_users():
    if os.path.exists(USER_DB_FILE):
        try:
            with open(USER_DB_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user(username, password):
    users = load_users()
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    users[username] = {"password": hashed_password}
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    if username in users:
        db_data = users[username]
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if isinstance(db_data, str):
            return db_data == hashed_password
        return db_data["password"] == hashed_password
    return False

# Initialize user sessions
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.sidebar.header("👤 HEIS5 Account")

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Action / Kitendo:", ["Login", "Sign Up"])
    auth_username = st.sidebar.text_input("Username / Jina la Mtumiaji:")
    auth_password = st.sidebar.text_input("Password / Nenosiri:", type="password")
    
    if auth_mode == "Login":
        if st.sidebar.button("Log In", use_container_width=True):
            if verify_user(auth_username, auth_password):
                st.session_state.logged_in = True
                st.session_state.current_user = auth_username
                st.sidebar.success(f"Welcome / Karibu, {auth_username}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Credentials incorrect!")
    elif auth_mode == "Sign Up":
        if st.sidebar.button("Create Account", use_container_width=True):
            if auth_username.strip() == "" or auth_password.strip() == "":
                st.sidebar.warning("⚠️ Fill all fields!")
            elif auth_username in load_users():
                st.sidebar.error("❌ Username taken!")
            else:
                save_user(auth_username, auth_password)
                st.sidebar.success("✅ Created! Select 'Login' to sign in.")
    st.stop()
else:
    st.sidebar.markdown(f"**Account / Akaunti:** ✨ `{st.session_state.current_user}`")
    if st.sidebar.button("Log Out / Toka", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    # -------------------------------------------------------------------------
    # 2. MULTI-TIER PREMIUM PAYWALL CONTROLLER (DIRECT ADMIN OVERRIDE)
    # -------------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🔑 HEIS5 Premium Access")

    WEEK_TOKENS = ["HEIS5_1WEEK_VIP", "WEEK_ACCESS_99"]
    MONTH_TOKENS = ["HEIS5_1MONTH_VIP", "MONTH_ACCESS_88"]
    THREE_MONTH_TOKENS = ["HEIS5_3MONTHS_VIP", "PREMIUM_3M_77"]

    user_token = st.sidebar.text_input("Enter Premium Token:", type="password")
    
    # 👑 DIRECT ACCURATE PASSWORD CHECK
    is_admin = (user_token == "Erasto_HEIS5_Boss_2026")

    if is_admin:
        is_premium = True
        st.sidebar.success("⚡ Admin Verified / Mmiliki Umethibitishwa!")
    else:
        is_premium = user_token in WEEK_TOKENS or user_token in MONTH_TOKENS or user_token in THREE_MONTH_TOKENS

    # If they aren't premium and aren't admin, block them
    if not is_premium:
        st.sidebar.error("🔒 Premium Required / Kifurushi Kinahitajika")
        st.info("### 🔓 Sehemu ya Kupata Utabiri wa Hali ya Juu / Where You Get Premium-Level Predictions")
        st.write("You can pay easily using **Tigo Pesa, M-Pesa, or Airtel Money** (No bank card needed!). Choose your access pass below:")
        
        st.markdown("[📋 Purchase 1-Week Pass / Lipia Wiki 1 (5,000 TZS)](https://selar.co/0xt51n9m6q?currency=TZS)")
        st.markdown("[📅 Purchase 1-Month Pass / Lipia Mwezi 1 (15,000 TZS)](https://selar.co/3195d901k1?currency=TZS)")
        st.markdown("[🏆 Purchase 3-Month Pass / Lipia Miezi 3 (45,000 TZS)](https://selar.co/o9n50311b0?currency=TZS)")
        st.stop()

    # -------------------------------------------------------------------------
    # 3. INTERACTION INTERFACE & API INTEGRATION ENGINE
    # -------------------------------------------------------------------------
    st.title("⚽ HEIS5 Football Predictor App")
    st.write("The home of High-quality Football Predictions")
    st.markdown("---")

    selected_league_name = st.selectbox("Select League / Chagua Ligi:", list(API_LEAGUES.keys()))
    league_code = API_LEAGUES[selected_league_name]

    with st.spinner("Fetching updated standings and team matrices..."):
        LEAGUE_DATA = fetch_league_teams_and_stats(league_code, API_TOKEN)

    if not LEAGUE_DATA:
        st.error("❌ System configuration error: Missing API Token setup.")
        st.stop()

    league_teams = sorted(list(LEAGUE_DATA.keys()))

    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("Home Team / Timu ya Nyumbani:", league_teams, index=0)
    with col2:
        away_team = st.selectbox("Away Team / Timu ya Ugenini:", league_teams, index=1 if len(league_teams) > 1 else 0)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 Run Analytical Prediction Model / Tabiri Sasa", type="primary", use_container_width=True):
        if home_team == away_team:
            st.warning("⚠️ Home Team and Away Team cannot be identical.")
            st.stop()

        home_stats = LEAGUE_DATA[home_team]
        away_stats = LEAGUE_DATA[away_team]

        home_attack, home_defense, home_corners_avg, home_cards_avg = home_stats
        away_attack, away_defense, away_corners_avg, away_cards_avg = away_stats

        home_exp_goals = home_attack * away_defense
        away_exp_goals = away_attack * home_defense
        
        # Calculate Poisson matrix
        max_goals = 6
        matrix = np.zeros((max_goals, max_goals))
        for h in range(max_goals):
            for a in range(max_goals):
                matrix[h, a] = stats.poisson.pmf(h, home_exp_goals) * stats.poisson.pmf(a, away_exp_goals)

        results = []
        for h in range(max_goals):
            for a in range(max_goals):
                results.append(((h, a), matrix[h, a]))
        results.sort(key=lambda x: x[1], reverse=True)

        # 🎯 1. GET THE SINGLE HIGHEST PROBABILITY SCORE
        top_score, top_prob = results[0]  # This is the #1 prediction
        predicted_home_goals = top_score[0]
        predicted_away_goals = top_score[1]
        total_predicted_goals = predicted_home_goals + predicted_away_goals

        # 📊 2. GOAL LINE DEPENDS DIRECTLY ON THE TOP PREDICTED SCORE
        if total_predicted_goals >= 3:
            goal_line_verdict = "Over 2.5 Goals"
        else:
            goal_line_verdict = "Under 2.5 Goals"

        # 🤝 Both Teams To Score (BTTS) depends directly on the top score too
        if predicted_home_goals > 0 and predicted_away_goals > 0:
            btts_verdict = "Yes"
        else:
            btts_verdict = "No"

        # Calculate Corners and Cards lines
        exp_total_corners = home_corners_avg + away_corners_avg
        corners_line = "Over 8.5 Corners" if (1 - stats.poisson.cdf(8, exp_total_corners)) > 0.5 else "Under 8.5 Corners"

        exp_total_cards = home_cards_avg + away_cards_avg
        cards_line = "Over 3.5 Cards" if (1 - stats.poisson.cdf(3, exp_total_cards)) > 0.5 else "Under 3.5 Cards"

        # -------------------------------------------------------------------------
        # DISPLAY RESULTS (ONLY SHOWING 1 HIGH POSSIBLE SCORE)
        # -------------------------------------------------------------------------
        st.markdown(f"### 📊 Predictions for {home_team} vs {away_team}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-title">Goal Line / Magoli</div>
                    <div class="prediction-value">{goal_line_verdict}</div>
                    <div style="color:#71717a; font-size:12px; margin-top:5px;">Based on predicted score</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-title">Corners Line / Kona</div>
                    <div class="prediction-value">{corners_line}</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
                <div class="prediction-card">
                    <div class="prediction-title">Cards Line / Kadi</div>
                    <div class="prediction-value">{cards_line}</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown(f"""
            <div class="prediction-card" style="border-left: 5px solid #38bdf8;">
                <div class="prediction-title">Both Teams To Score (BTTS)</div>
                <div class="prediction-value">{btts_verdict}</div>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🔮 Highest Possible Exact Score / Matokeo Sahihi")
        
        # Only rendering the single Top 1 outcome row
        st.markdown(f"""
            <div class="score-row" style="border-left: 6px solid #00ff66;">
                <span>🎯 <b>HIGH CONFIDENCE PREDICTION</b></span>
                <span style="font-size: 20px;">{home_team} <b>{predicted_home_goals} - {predicted_away_goals}</b> {away_team}</span>
                <span style="color:#00ff66; font-weight:bold;">{top_prob*100:.1f}% Model Probability</span>
            </div>
        """, unsafe_allow_html=True)

        st.button("Reset / Angalia Tena", use_container_width=True)
