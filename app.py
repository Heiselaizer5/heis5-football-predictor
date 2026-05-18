import streamlit as st
import numpy as np
import scipy.stats as stats
import json
import os
import hashlib

# Set global professional page layout
st.set_page_config(page_title="HEIS5 Football Predictor", page_icon="⚽", layout="wide")

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
    users[username] = hashed_password
    with open(USER_DB_FILE, "w") as f:
        json.dump(users, f)

def verify_user(username, password):
    users = load_users()
    if username in users:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        return users[username] == hashed_password
    return False

# Initialize user sessions
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

st.sidebar.header("👤 HEIS5 User Account / Akaunti")

# Force authentication before showing any prediction models
if not st.session_state.logged_in:
    auth_mode = st.sidebar.radio("Choose Action / Chagua Kitendo:", ["Login", "Sign Up"])
    auth_username = st.sidebar.text_input("Username / Jina la Mtumiaji:")
    auth_password = st.sidebar.text_input("Password / Nenosiri:", type="password")
    
    if auth_mode == "Login":
        if st.sidebar.button("Log In", use_container_width=True):
            if verify_user(auth_username, auth_password):
                st.session_state.logged_in = True
                st.session_state.current_user = auth_username
                st.sidebar.success(f"Welcome back / Karibu, {auth_username}!")
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid credentials! / Jina au Nenosiri si sahihi!")
                
    elif auth_mode == "Sign Up":
        if st.sidebar.button("Create Account / Fungua Akaunti", use_container_width=True):
            if auth_username.strip() == "" or auth_password.strip() == "":
                st.sidebar.warning("⚠️ Please fill in all fields! / Jaza nafasi zote!")
            elif auth_username in load_users():
                st.sidebar.error("❌ Username taken! / Jina hili tayari limetumika!")
            else:
                save_user(auth_username, auth_password)
                st.sidebar.success("✅ Account created! Select 'Login' to sign in. / Akaunti imeundwa! Chagua 'Login' kuingia.")

    st.info("### 🔒 Welcome to HEIS5 Predictor / Karibu HEIS5")
    st.write("Please Log In or Sign Up via the sidebar to access the prediction models.")
    st.write("*Tafadhali Ingia (Log In) au Jisajili (Sign Up) upande wa kushoto ili kupata utabiri.*")
    st.stop()

else:
    st.sidebar.markdown(f"**Account / Akaunti:** ✨ `{st.session_state.current_user}`")
    if st.sidebar.button("Log Out / Toka", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.rerun()

    # -------------------------------------------------------------------------
    # 2. MULTI-TIER PREMIUM PAYWALL CONTROLLER
    # -------------------------------------------------------------------------
    st.sidebar.markdown("---")
    st.sidebar.header("🔑 HEIS5 Premium Access")

    if "sim_clicks" not in st.session_state:
        st.session_state.sim_clicks = 0

    # Defined secure system tokens
    WEEK_TOKENS = ["HEIS5_1WEEK_VIP", "WEEK_ACCESS_99"]
    MONTH_TOKENS = ["HEIS5_1MONTH_VIP", "MONTH_ACCESS_88"]
    THREE_MONTH_TOKENS = ["HEIS5_3MONTHS_VIP", "PREMIUM_3M_77"]

    user_token = st.sidebar.text_input("Enter Premium Token / Weka Token yako:", type="password")

    is_week = user_token in WEEK_TOKENS
    is_month = user_token in MONTH_TOKENS
    is_3month = user_token in THREE_MONTH_TOKENS
    is_premium = is_week or is_month or is_3month

    if not is_premium:
        remaining_trials = max(0, 3 - st.session_state.sim_clicks)
        if remaining_trials > 0:
            st.sidebar.info(f"🎁 Free Trial: **{remaining_trials}** matches left.\n\n*Jaribio la Bure: Mechi **{remaining_trials}** zimebaki.*")
        else:
            st.sidebar.error("❌ Free Trial Expired! / Jaribio Limeisha!")
            st.info("### 🔒 Premium Access Required / Kifurushi Kinahitajika")
            st.write("Select a plan below to unlock full premium data including Exact Scores, Corners, Cards, and BTTS predictions via M-Pesa or Tigo Pesa:")
            st.write("*Chagua kifurushi hapa chini ili kufungua utabiri mzima wa Matokeo Sahihi, Corners, na Cards kupitia M-Pesa au Tigo Pesa:*")
            
            # --- LIVE PAYMENT LINKS (Add your copied Selar URLs inside these parentheses) ---
            st.markdown("[📋 Purchase 1-Week Pass / Lipia Wiki 1 (5,000 TZS)](https://selar.co/0xt51n9m6q)")
            st.markdown("[📅 Purchase 1-Month Pass / Lipia Mwezi 1 (15,000 TZS)](https://selar.co/3195d901k1)")
            st.markdown("[🏆 Purchase 3-Month Pass / Lipia Miezi 3 (45,000 TZS)](https://selar.co/o9n50311b0)")
            st.stop()
    else:
        if is_week:
            st.sidebar.success("👑 1-Week Premium Active! / Wiki 1 Iko Active!")
        elif is_month:
            st.sidebar.success("👑 1-Month Premium Active! / Mwezi 1 Uko Active!")
        elif is_3month:
            st.sidebar.success("👑 3-Month Ultimate VIP Active! / Miezi 3 Iko Active!")

    # -------------------------------------------------------------------------
    # 3. CORE ANALYTICAL ENGINE (MATHEMATICAL CALCULATIONS)
    # -------------------------------------------------------------------------
    st.title("⚽ HEIS5 Football Predictor Engine")
    st.write("Advanced Predictive Modeling using Professional Poisson Distributions.")
    st.write("*Utabiri wa Kisasa wa Kandanda kwa Kutumia Mfumo wa Kihesabu wa Poisson.*")
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🏠 Home Team Inputs / Data za Nyumbani")
        home_team = st.text_input("Home Team Name:", "Arsenal")
        home_attack = st.number_input("Home Attack Strength (Avg Goals Scored):", min_value=0.1, max_value=5.0, value=1.8, step=0.1)
        home_defense = st.number_input("Home Defense Weakness (Avg Goals Conceded):", min_value=0.1, max_value=5.0, value=0.9, step=0.1)
        home_corners_avg = st.number_input("Home Avg Corners per Match:", min_value=1.0, max_value=15.0, value=6.2, step=0.1)
        home_cards_avg = st.number_input("Home Avg Cards per Match:", min_value=0.0, max_value=10.0, value=1.4, step=0.1)

    with col2:
        st.subheader("🚀 Away Team Inputs / Data za Ugenini")
        away_team = st.text_input("Away Team Name:", "Chelsea")
        away_attack = st.number_input("Away Attack Strength (Avg Goals Scored):", min_value=0.1, max_value=5.0, value=1.4, step=0.1)
        away_defense = st.number_input("Away Defense Weakness (Avg Goals Conceded):", min_value=0.1, max_value=5.0, value=1.5, step=0.1)
        away_corners_avg = st.number_input("Away Avg Corners per Match:", min_value=1.0, max_value=15.0, value=4.8, step=0.1)
        away_cards_avg = st.number_input("Away Avg Cards per Match:", min_value=0.0, max_value=10.0, value=2.1, step=0.1)

    st.markdown("---")

    if st.button("🚀 Run Analytical Prediction Model / Tabiri Sasa", type="primary", use_container_width=True):
        if not is_premium:
            st.session_state.sim_clicks += 1

        # Calculate Expected Goals (Lambda values)
        home_exp_goals = home_attack * away_defense
        away_exp_goals = away_attack * home_defense
        
        # Build Goal Outcome Distribution Matrix
        max_goals = 6
        matrix = np.zeros((max_goals, max_goals))
        for h in range(max_goals):
            for a in range(max_goals):
                matrix[h, a] = stats.poisson.pmf(h, home_exp_goals) * stats.poisson.pmf(a, away_exp_goals)

        # Extract top exact scores
        results = []
        for h in range(max_goals):
            for a in range(max_goals):
                results.append(((h, a), matrix[h, a]))
        results.sort(key=lambda x: x[1], reverse=True)

        # --- GOAL LINE & BTTS VERDICT LOGIC WITHOUT PERCENTAGES ---
        prob_under_05 = matrix[0, 0]  # Probability of a 0-0 match
        prob_over_05 = 1.0 - prob_under_05
        goal_line_verdict = "Over 0.5 Goals" if prob_over_05 > prob_under_05 else "Under 0.5 Goals"

        prob_btts_yes = sum(matrix[h, a] for h in range(1, max_goals) for a in range(1, max_goals))
        prob_btts_no = 1.0 - prob_btts_yes
        btts_verdict = "Yes" if prob_btts_yes > prob_btts_no else "No"

        # Calculate Corners and Cards lines
        exp_total_corners = home_corners_avg + away_corners_avg
        corners_line = "Over 8.5 Corners" if (1 - stats.poisson.cdf(8, exp_total_corners)) > 0.5 else "Under 8.5 Corners"

        exp_total_cards = home_cards_avg + away_cards_avg
        cards_line = "Over 3.5 Cards" if (1 - stats.poisson.cdf(3, exp_total_cards)) > 0.5 else "Under 3.5 Cards"

        # Display Outcomes
        st.success("### 📊 Predictive Modeling Outcomes / Matokeo ya Utabiri")
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Goal Line / Soko la Magoli:", goal_line_verdict)
            st.write(f"Expected Rate: {home_exp_goals:.2f} - {away_exp_goals:.2f}")
            
        with c2:
            st.metric("Corners Line / Soko la Kona:", corners_line)
            st.write(f"Projected Total: ~ {round(exp_total_corners)} Corners")
            
        with c3:
            st.metric("Cards Line / Soko la Kadi:", cards_line)
            st.write(f"Projected Total: ~ {round(exp_total_cards)} Cards")

        st.markdown("---")
        st.metric("Both Teams To Score (BTTS):", btts_verdict)

        # Display Top Exact Scores
        st.markdown("---")
        st.subheader("🔮 Top 3 Exact Score Probabilities / Matokeo Sahihi Yanayofaa")
        for i in range(3):
            score, prob = results[i]
            st.write(f"🎯 **Top {i+1}:** {home_team} **{score[0]} - {score[1]}** {away_team} — Chance: **{prob*100:.1f}%**")

        st.utility = True