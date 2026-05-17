import streamlit as st
import pandas as pd
import os
import random

# Page Configuration for Browser Tab
st.set_page_config(page_title="Pro Football Predictor", page_icon="⚽", layout="centered")

def load_database():
    csv_file = "leaguetable.csv"
    if not os.path.exists(csv_file):
        return None
    df = pd.read_csv(csv_file)
    df.columns = df.columns.str.strip()
    return df

# App Web Layout Headers
st.title("⚽ HEIS5 live Football Predictor")
st.markdown("Welcome to your advanced simulation matrix. Select teams below to project match statistics.")
st.divider()

df = load_database()

if df is not None:
    # Extract clean team lists for dropdown menus
    team_list = sorted(df['team_name'].unique())
    
    # Create web dropdown selectors
    col1, col2 = st.columns(2)
    with col1:
        home_selection = st.selectbox("🏟️ Select Home Team:", team_list, index=0)
    with col2:
        away_selection = st.selectbox("🚀 Select Away Team:", team_list, index=min(1, len(team_list)-1))
        
    if st.button("🔥 Run Match Simulation Matrix", use_container_width=True):
        if home_selection == away_selection:
            st.error("❌ A team cannot play against itself! Select two different teams.")
        else:
            # Get Row Data
            home_row = df[df['team_name'] == home_selection].iloc[0]
            away_row = df[df['team_name'] == away_selection].iloc[0]
            
            # Math Variables
            h_mp = max(int(home_row['matches_played']), 1)
            a_mp = max(int(away_row['matches_played']), 1)
            
            home_att = home_row['goals_scored'] / h_mp
            home_def = home_row['goals_conceded'] / h_mp
            away_att = away_row['goals_scored'] / a_mp
            away_def = away_row['goals_conceded'] / a_mp
            
            home_corners_avg = home_row['corners_won'] / h_mp
            away_corners_avg = away_row['corners_won'] / a_mp
            
            # Phase 2 & 3 Matrix Math
            home_xg = home_att * away_def * 1.15
            away_xg = away_att * home_def * 0.90
            
            home_score = round(random.uniform(max(0, home_xg - 0.5), home_xg + 0.5))
            away_score = round(random.uniform(max(0, away_xg - 0.5), away_xg + 0.5))
            
            total_corners = round(random.uniform(home_corners_avg - 1, home_corners_avg + 2) + random.uniform(away_corners_avg - 1, away_corners_avg + 2))
            
            # UI Outcome Box Display
            st.subheader("🎯 Simulated Scoreline Result")
            st.metric(label="Predicted Final Score", value=f"{home_selection}  {home_score} - {away_score}  {away_selection}")
            
            col_stat1, col_stat2 = st.columns(2)
            with col_stat1:
                st.info(f"📐 Total Corners: **{total_corners}**")
            with col_stat2:
                btts = "YES" if home_score > 0 and away_score > 0 else "NO"
                st.info(f"💥 Both Teams to Score: **{btts}**")
                
            st.caption(f"Raw Strength Weights Vector Model -> xG Projections: {home_selection}: {home_xg:.2f} | {away_selection}: {away_xg:.2f}")
else:
    st.error("❌ Could not read 'leaguetable.csv'. Make sure it's in the same folder!")