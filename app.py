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
# FOOTBALL-DATA.ORG API SYSTEM CONFIGURATION (CACHED TO PREVENT SPEED BLOCKS)
# -------------------------------------------------------------------------
# Map user friendly names to official API competition codes
API_LEAGUES = {
    "English Premier League 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "PL",
    "English Championship 🏴󠁧󠁢󠁥󠁮󠁧󠁿": "ELC",
    "Italian Serie A 🇮🇹": "SA",
    "Spanish La Liga 🇪🇸": "PD",
    "German Bundesliga 🇩🇪": "BL1",
    "French Ligue 1 🇫🇷": "FL1",
    "Netherlands Eredivisie 🇳🇱": "DED",
    "Portugal Primeira Liga 🇵🇹": "PPL",
    "UEFA Champions League 🇪🇺": "CL",
    "FIFA World Cup 🏆": "WC"
}

# Enter your token here or use the Sidebar input field
API_TOKEN = "d7bf2e7e47344436b3571ff11c6639c6"

@st.cache_data(ttl=3600)  # Keeps data stored for 1 hour to prevent 10 calls/min rate limits
def fetch_league_teams_and_stats(league_code, token):
    if not token:
        return {}
    
    headers = {"X-Auth-Token": token}
    try:
        # Fetch current standings to calculate relative attack/defense matrix indexes
        url = f"https://api.football-data.org/v4/competitions/{league_code}/standings"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            return None
            
        data = response.json()
        processed_teams = {}
        
        # Tournaments like UCL and World Cup use a grouped standings array format
        if league_code in ["CL", "WC"]:
            standings_groups = data.get('standings', [])
            for group in standings_groups:
                for row in group.get('table', []):
                    team_name = row['team']['name']
                    played = row['playedGames'] if row['playedGames'] > 0 else 1
                    avg_scored = row['goalsFor'] / played
                    avg_conceded = row['goalsAgainst'] / played
                    # [Avg Scored, Avg Conceded, Fallback Corners, Fallback Cards]
                    processed_teams[team_name] = [avg_scored, avg_conceded, 5.2, 1.9]
        else:
            # Regular traditional league format processing
            standings = data['standings'][0]['table']
            for row in standings:
                team_name = row['team']['name']
                played = row['playedGames'] if row['playedGames'] > 0 else 1
                avg_scored = row['goalsFor'] / played
                avg_conceded = row['goalsAgainst'] / played
                processed_teams[team_name] = [avg_scored, avg_conceded, 5.5, 1.8]
            
        return processed_teams
    except:
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
    users[username] = {
        "password": hashed_password,
        "trials_used": 0
    }
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    if username in users:
        db_data = users[username]
        if isinstance(db_data, str):
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            return db_data == hashed_password
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return db_data["password"] == hashed_password
    return False

def get_user_trials(username):
    users = load_users()
    if username in users and isinstance(users[username], dict):
        return users[username].get("trials_used", 0)
    return 0

def increment_user_trials(username):
    users = load_users()
    if username in users and isinstance(users[username], dict):
        users[username]["trials_used"] = users[username].get("trials_used", 0) + 1
        with open(USER_DB_FILE, "w") as f:
            json.dump(users, f)

# Initialize user sessions
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.sidebar.header("👤 HEIS5 User Account / Akaunti")

if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Choose Action:", ["Login", "Sign Up"])
    auth_username = st.sidebar.text_input("Username:")
    auth_password = st.sidebar.text_input("Password:", type="password")
    
    if auth_mode == "Login":
        if st.sidebar.button("Log In", use_container_width=True):
            if verify_user(auth_username, auth_password):
                st.session_state.logged_in = True
                st.session_state.current_user = auth_username
                st.sidebar.success(f"Welcome back, {auth_username}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid credentials!")
    elif auth_mode == "Sign Up":
        if st.sidebar.button("Create Account", use_container_width=True):
            if auth_username.strip() == "" or auth_password.strip() == "":
                st.sidebar.warning("⚠️ Please fill in all fields!")
            elif auth_username in load_users():
                st.sidebar.error("❌ Username taken!")
            else:
                save_user(auth_username, auth_password)
                st.sidebar.success("✅ Account created! Select 'Login' to sign in.")
    st.stop()
else:
    st.sidebar.markdown(f"**Account:** ✨ `{st.session_state.current_user}`")
    if st.sidebar.button("Log Out / Toka", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    # -------------------------------------------------------------------------
    # 2. MULTI-TIER PREMIUM PAYWALL CONTROLLER (PERSISTENT TRACKING)
    # -------------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🔑 HEIS5 Premium Access")

    WEEK_TOKENS = ["HEIS5_1WEEK_VIP", "WEEK_ACCESS_99"]
    MONTH_TOKENS = ["HEIS5_1MONTH_VIP", "MONTH_ACCESS_88"]
    THREE_MONTH_TOKENS = ["HEIS5_3MONTHS_VIP", "PREMIUM_3M_77"]

    ADMIN_TOKENS = ["HEIS5_OWNER_2026", "HEIS5_ADMIN"]

    user_token = st.sidebar.text_input("Enter Premium Token:", type="password")
    is_premium = user_token in WEEK_TOKENS or user_token in MONTH_TOKENS or user_token in THREE_MONTH_TOKENS or user_token in ADMIN_TOKENS

    trials_used = get_user_trials(st.session_state.current_user)

    if not is_premium:
        remaining_trials = max(0, 3 - trials_used)
        if remaining_trials > 0:
            st.sidebar.info(f"🎁 Free Trial: **{remaining_trials}** matches left.")
        else:
            st.sidebar.error("❌ Free Trial Expired!")
            st.info("### 🔒 Premium Access Required / Kifurushi Kinahitajika")
            st.markdown("[📋 Purchase 1-Week Pass (5,000 TZS)](https://selar.co/0xt51n9m6q)")
            st.markdown("[📅 Purchase 1-Month Pass (15,000 TZS)](https://selar.co/3195d901k1)")
            st.markdown("[🏆 Purchase 3-Month Pass (45,000 TZS)](https://selar.co/o9n50311b0)")
            st.stop()

    # -------------------------------------------------------------------------
    # 3. INTERACTION INTERFACE & API INTEGRATION ENGINE
    # -------------------------------------------------------------------------
    st.title("⚽ HEIS5 Football Predictor App")
    st.write("The home of high-quality football predictions")
    st.markdown("---")

    selected_league_name = st.selectbox("Select League / Chagua Ligi:", list(API_LEAGUES.keys()))
    league_code = API_LEAGUES[selected_league_name]

    # Pull data from cached web service
    with st.spinner("Fetching updated standings and team matrices..."):
        LEAGUE_DATA = fetch_league_teams_and_stats(league_code, API_TOKEN)

    if not LEAGUE_DATA:
        st.error("❌ Failed to reach API. Please double check your Token or wait a minute before refreshing.")
        st.stop()

    league_teams = sorted(list(LEAGUE_DATA.keys()))

    col1, col2 = st.columns(2)
    with col1:
        home_team = st.selectbox("Home Team / Timu ya Nyumbani:", league_teams, index=0)
    with col2:
        away_team = st.selectbox("Away Team / Timu ya Ugenini:", league_teams, index=1 if len(league_teams) > 1 else 0)

    if home_team == away_team:
        st.warning("⚠️ Warning: Home Team and Away Team cannot be identical.")

    st.markdown("---")

    if st.button("🚀 Run Analytical Prediction Model / Tabiri Sasa", type="primary", use_container_width=True) and home_team != away_team:
        if not is_premium:
            increment_user_trials(st.session_state.current_user)

        # Pull dynamic calculations from API parsed matrix
        home_attack, home_defense, home_corners_avg, home_cards_avg = LEAGUE_DATA[home_team]
        away_attack, away_defense, away_corners_avg, away_cards_avg = LEAGUE_DATA[away_team]

        # Process Poisson Distribution Variables 
        home_exp_goals = home_attack * away_defense
        away_exp_goals = away_attack * home_defense
        
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

        # Output Text Market Lines
        prob_under_05 = matrix[0, 0]
        goal_line_verdict = "Over 0.5 Goals" if (1.0 - prob_under_05) > prob_under_05 else "Under 0.5 Goals"

        prob_btts_yes = sum(matrix[h, a] for h in range(1, max_goals) for a in range(1, max_goals))
        btts_verdict = "Yes" if prob_btts_yes > (1.0 - prob_btts_yes) else "No"

        exp_total_corners = home_corners_avg + away_corners_avg
        corners_line = "Over 8.5 Corners" if (1 - stats.poisson.cdf(8, exp_total_corners)) > 0.5 else "Under 8.5 Corners"

        exp_total_cards = home_cards_avg + away_cards_avg
        cards_line = "Over 3.5 Cards" if (1 - stats.poisson.cdf(3, exp_total_cards)) > 0.5 else "Under 3.5 Cards"

        # Present Results Layout
        st.success(f"### 📊 Predictions for {home_team} vs {away_team}")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Goal Line / Soko la Magoli:", goal_line_verdict)
            st.write(f"API Live xG Rate: {home_exp_goals:.2f} - {away_exp_goals:.2f}")
        with c2:
            st.metric("Corners Line / Soko la Kona:", corners_line)
        with c3:
            st.metric("Cards Line / Soko la Kadi:", cards_line)

        st.markdown("---")
        st.metric("Both Teams To Score (BTTS):", btts_verdict)

        st.markdown("---")
        st.subheader("🔮 Top 3 Exact Score Probabilities / Matokeo Sahihi")
        for i in range(3):
            score, prob = results[i]
            st.write(f"🎯 **Top {i+1}:** {home_team} **{score[0]} - {score[1]}** {away_team} — Chance: **{prob*100:.1f}%**")

        st.button("Refresh View", use_container_width=True)