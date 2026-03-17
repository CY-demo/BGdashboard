"""
app.py
------
The main entry point for the Streamlit web application.
This script provides the UI for viewing/editing match history (CRUD)
and displays real-time ML board game recommendations.

Run with: streamlit run app.py
"""

import os
import html
import streamlit as st
import plotly.graph_objects as go
from db_manager import get_player_history, get_game_attributes, insert_match_result, delete_match_result, update_match_result, delete_player, get_top_games, get_top_players_for_game, get_recent_activity
from recommender import Recommender

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="BoardGame Recommender", layout="wide", initial_sidebar_state="collapsed")
st.title("BoardGame Recommender")

GAME_ATTRIBUTES = get_game_attributes()
available_games = list(GAME_ATTRIBUTES.keys())

# -----------------------------------------------------------------------------
# Admin Settings
# -----------------------------------------------------------------------------
# Password requirement removed as per request. Admin mode is enabled by default.
st.session_state["is_admin"] = True
# To manage this via .env in the future, use: os.getenv("ADMIN_PASSWORD")

# -----------------------------------------------------------------------------
# Community Dashboard
# -----------------------------------------------------------------------------
st.markdown("## 🌍 Community Dashboard")
dash_col1, dash_col2 = st.columns([1, 1])

with dash_col1:
    st.markdown("### 🔥 Most Popular Game")
    # Get just the #1 most played game
    top_games = get_top_games(1)
    if not top_games:
        st.info("No games played yet.")
    else:
        top_game = top_games[0]
        st.markdown(f"#### **{top_game['game_name']}** (*{top_game['play_count']} total plays*)")
        
        st.markdown("🏆 **Top Champions:**")
        top_players = get_top_players_for_game(top_game['game_id'], 3)
        if not top_players:
            st.write("  No winners recorded yet.")
        else:
            # Pad the list to 3 for the podium
            while len(top_players) < 3:
                top_players.append({"player_name": "-", "wins": 0, "highest_score": None})
            
            p1 = top_players[0]
            p2 = top_players[1]
            p3 = top_players[2]
            
            s1 = f"<br>Score: {p1['highest_score']}" if p1['highest_score'] is not None else ""
            s2 = f"<br>Score: {p2['highest_score']}" if p2['highest_score'] is not None else ""
            s3 = f"<br>Score: {p3['highest_score']}" if p3['highest_score'] is not None else ""
            
            # Secure against XSS injections from user-generated player names
            name1 = html.escape(str(p1['player_name']))
            name2 = html.escape(str(p2['player_name']))
            name3 = html.escape(str(p3['player_name']))
            
            podium_html = f"""
            <div class="podium-container">
                <div class="podium-column">
                    <div class="podium-name-top">{name2}</div>
                    <div class="podium-box podium-2">
                        <div class="podium-rank">🥈</div>
                    </div>
                    <div class="podium-stats">Win: {p2['wins']}{s2}</div>
                </div>
                <div class="podium-column">
                    <div class="podium-name-top">{name1}</div>
                    <div class="podium-box podium-1">
                        <div class="podium-rank">🥇</div>
                    </div>
                    <div class="podium-stats">Win: {p1['wins']}{s1}</div>
                </div>
                <div class="podium-column">
                    <div class="podium-name-top">{name3}</div>
                    <div class="podium-box podium-3">
                        <div class="podium-rank">🥉</div>
                    </div>
                    <div class="podium-stats">Win: {p3['wins']}{s3}</div>
                </div>
            </div>
            """
            st.markdown(podium_html, unsafe_allow_html=True)

with dash_col2:
    st.markdown("### 📡 Recent Activity Feed")
    recent = get_recent_activity(5)
    if not recent:
        st.info("No activity yet.")
    else:
        for row in recent:
            # Map SQL tinyint to boolean for the check
            is_win = bool(row['is_winner'])
            result = "🏆 Won" if is_win else "Played"
            # Format score if exists
            score_text = f" (Score: {int(row['score'])})" if row['score'] is not None else ""
            st.markdown(f"⏱️ *{row['played_at']}* | **{row['player_name']}** {result} **{row['game_name']}**{score_text}")

st.divider()

col_data, col_ml = st.columns([1, 1])

# Custom CSS 
st.markdown("""
<style>
    /* Import Space Grotesk font */
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    /* Main app styling - Cream/Nude background */
    .main {
        background-color: #F5F1E8;
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* streamlit's default white background override */
    .stApp {
        background-color: #F5F1E8;
    }
    
    /* headers */
    h1 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 700 !important;
        font-size: 3.2rem !important;
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem !important;
        letter-spacing: -1px !important;
    }
    
    h2 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 2.2rem !important;
        color: #3E5641 !important;
        margin-top: 1.5rem !important;
        margin-bottom: 1rem !important;
        letter-spacing: -0.5px !important;
    }
    
    h3 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 1.6rem !important;
        color: #556B58 !important;
        margin-top: 1rem !important;
        letter-spacing: -0.3px !important;
    }
    
    h4 {
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1.3rem !important;
        color: #6B8E6F !important;
    }
    
    /* regular text */
    p, .stMarkdown, label, div {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        color: #3E3E3E !important;
        line-height: 1.7 !important;
    }
    
    /* input box */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > select {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.05rem !important;
        background-color: #FFFFFF !important;
        border: 2.5px solid #B8C5B0 !important;
        border-radius: 12px !important;
        padding: 0.8rem !important;
        transition: all 0.3s ease !important;
        color: #3E3E3E !important;
    }
    
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {
        border-color: #6B8E6F !important;
        box-shadow: 0 0 0 4px rgba(107, 142, 111, 0.15) !important;
        background-color: #FFFFFF !important;
    }
    
    /* buttons = sage green */
    .stButton > button {
        font-family: 'Space Grotesk', sans-serif !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background: linear-gradient(135deg, #B8C5B0 0%, #A5B59D 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(107, 142, 111, 0.25) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%) !important;
        box-shadow: 0 6px 18px rgba(107, 142, 111, 0.35) !important;
        transform: translateY(-3px) !important;
    }
    
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #6B8E6F 0%, #556B58 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #556B58 0%, #3E5641 100%) !important;
        box-shadow: 0 6px 20px rgba(107, 142, 111, 0.4) !important;
    }
    
    /* Dataframe = white with sage border */
    .stDataFrame {
        background-color: #FFFFFF !important;
        border: 2.5px solid #B8C5B0 !important;
        border-radius: 15px !important;
        overflow: hidden !important;
        box-shadow: 0 5px 20px rgba(107, 142, 111, 0.15) !important;
    }
    
    /* info warning boxes */
    .stAlert {
        font-family: 'Space Grotesk', sans-serif !important;
        border-radius: 12px !important;
        font-size: 1.05rem !important;
        border-left: 5px solid !important;
        background-color: #FFFFFF !important;
    }
    
    div[data-testid="stNotificationContentInfo"] {
        background-color: #FFFFFF !important;
        border-left-color: #6B8E6F !important;
        color: #3E5641 !important;
    }
    
    div[data-testid="stNotificationContentSuccess"] {
        background-color: #FFFFFF !important;
        border-left-color: #5A8A5A !important;
        color: #2D5C2D !important;
    }
    
    div[data-testid="stNotificationContentWarning"] {
        background-color: #FFFFFF !important;
        border-left-color: #BC8B6A !important;
        color: #8B6F47 !important;
    }
    
    div[data-testid="stNotificationContentError"] {
        background-color: #FFFFFF !important;
        border-left-color: #A67C5D !important;
        color: #8B6F47 !important;
    }
    
    /* divider=sage green */
    hr {
        margin: 2.5rem 0 !important;
        border: none !important;
        height: 3px !important;
        background: linear-gradient(90deg, transparent, #B8C5B0, transparent) !important;
    }
    
    /* checkbox */
    .stCheckbox {
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* form colors */
    .stForm {
        background: #FFFFFF !important;
        border: 2.5px solid #B8C5B0 !important;
        border-radius: 18px !important;
        padding: 2rem !important;
        box-shadow: 0 5px 25px rgba(107, 142, 111, 0.15) !important;
    }
    
    /* reco boxes */
    .rec-card {
        background: #FFFFFF;
        border: 2.5px solid #B8C5B0;
        border-radius: 18px;
        padding: 1.8rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(107, 142, 111, 0.12);
    }
    
    .rec-card:hover {
        border-color: #6B8E6F;
        box-shadow: 0 8px 25px rgba(107, 142, 111, 0.25);
        transform: translateY(-4px);
    }
    
    .rec-card h3 {
        margin: 0 0 0.8rem 0 !important;
        color: #6B8E6F !important;
        font-weight: 700 !important;
        font-size: 1.5rem !important;
    }
    
    .rec-card p {
        margin: 0 !important;
        color: #5D5D5D !important;
        font-size: 1.05rem !important;
    }
    
    /* column style =cream  */
    [data-testid="column"] {
        background: #FFFFFF;
        border: 2.5px solid #D4CEC3;
        border-radius: 18px;
        padding: 2.5rem;
        box-shadow: 0 5px 20px rgba(107, 142, 111, 0.1);
    }
    
    /* spinner = sage */
    .stSpinner > div {
        border-top-color: #6B8E6F !important;
    }
    
    /* metrics = sage accent */
    [data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #6B8E6F !important;
        font-family: 'Space Grotesk', sans-serif !important;
    }
    
    /* Podium Styles */
    .podium-container {
        display: flex;
        justify-content: center;
        align-items: flex-end;
        gap: 20px;
        margin-top: 25px;
    }
    
    .podium-column {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: flex-end;
    }
    
    .podium-box {
        text-align: center;
        border-radius: 12px 12px 0 0;
        padding: 10px;
        color: white;
        font-weight: 600;
        box-shadow: 0 -4px 15px rgba(0,0,0,0.1);
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        position: relative;
    }
    
    .podium-1 {
        height: 130px;
        width: 110px;
        background: linear-gradient(135deg, #FFD700 0%, #FDB931 100%);
        z-index: 3;
    }
    
    .podium-2 {
        height: 85px;
        width: 100px;
        background: linear-gradient(135deg, #E0E0E0 0%, #BDBDBD 100%);
        z-index: 2;
    }
    
    .podium-3 {
        height: 50px;
        width: 100px;
        background: linear-gradient(135deg, #CD7F32 0%, #A0522D 100%);
        z-index: 1;
    }
    
    .podium-rank {
        font-size: 1.8rem;
        margin-bottom: 5px;
    }
    
    .podium-name-top {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 5px;
        text-align: center;
        word-wrap: break-word;
        max-width: 110px;
    }
    
    .podium-stats {
        margin-top: 8px;
        font-size: 0.95rem;
        color: #555;
        font-weight: 500;
        text-align: center;
        line-height: 1.4;
        height: 45px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
    }
    
    /*dropdown box */
    .stSelectbox [data-baseweb="select"] {
        background-color: #FFFFFF !important;
    }
    
    /*make sure all backgrounds are cream */
    [data-testid="stAppViewContainer"] {
        background-color: #F5F1E8 !important;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /*caption text */
    .stCaption {
        font-family: 'Space Grotesk', sans-serif !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading & ML Engine Initialization (Optimized)
# -----------------------------------------------------------------------------
history_df = get_player_history() # Cached
rec_engine = None
existing_players = []
if not history_df.empty:
    existing_players = history_df["player_name"].unique().tolist()

# -----------------------------------------------------------------------------
# Main Columns
# -----------------------------------------------------------------------------
col_data, col_ml = st.columns([1, 1], gap="large")

with col_data:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>Who is playing?</h2>", unsafe_allow_html=True)
    current_player = st.selectbox("Select Player", existing_players)
    
    # Initialize Recommender once for use in both columns
    if current_player and not history_df.empty:
        try:
            rec_engine = Recommender(history_df, game_attrs=GAME_ATTRIBUTES)
        except:
             pass
    
    if st.session_state.get("is_admin", False):
        new_p = st.text_input("Or enter a new player name to create/select:")
        if new_p.strip():
            current_player = new_p.strip()
        
    if not current_player:
        st.warning("Please select or enter a player name to continue.")
        st.stop()

    # Display the user's top 3 best games (highest win count, or best score)
    st.markdown(f"### Profile for **{current_player}**")

    player_history_df = get_player_history(current_player)
    
    if player_history_df.empty:
        st.info("No play history found.")
    else:
        # Calculate their top 3 games
        wins_df = player_history_df[player_history_df['is_winner'] == 1]
        
        st.markdown("🏅 **Personal Best Games**")
        if wins_df.empty:
            # No wins, just show highest scores
            best_scores = player_history_df.dropna(subset=['score']).sort_values('score', ascending=False)
            if best_scores.empty:
                st.write("Keep playing to earn your first win!")
            else:
                top_3 = best_scores.head(3)
                for _, row in top_3.iterrows():
                    st.markdown(f"- **{row['game_name']}** (Score: *{row['score']}*)")
        else:
            # Show top 3 by win count
            win_counts = wins_df.groupby('game_name').size().reset_index(name='wins').sort_values('wins', ascending=False).head(3)
            for _, row in win_counts.iterrows():
                st.markdown(f"- **{row['game_name']} — *Win: {row['wins']}* 👑**")

        # --- Personality Analysis (Moved to Profile) ---
        if rec_engine:
            try:
                traits = rec_engine.get_player_traits(current_player)
                
                # Use .get() to avoid KeyError 'person' or others
                t_title = traits.get('title', 'You are a Versatile Gamer! 🎮')
                t_desc = traits.get('desc', 'You have a balanced and adaptable playstyle.')
                t_person = traits.get('person', 'Unknown')
                t_status = traits.get('status', 'A mysterious figure in history.')
                t_quote = traits.get('quote', '"Success is not final, failure is not fatal."')
                
                st.success("Based on your tracking data, here is your analysis:")
                
                # --- Radar Chart (Hexagon - 6 Attributes) ---
                all_metrics = rec_engine.get_player_profile_metrics(current_player)
                target_features = ["strategy", "luck", "negotiation", "deduction", "cooperation", "complexity"]
                
                # Filter and reorder categories
                categories = []
                values = []
                for feat in target_features:
                    if feat in all_metrics:
                        # Prettify labels
                        label = feat.replace('_', ' ').title()
                        # Override Complexity label as requested
                        if label == "Complexity":
                            label = "Organization"
                        categories.append(label)
                        values.append(all_metrics[feat])
                
                # Close the loop
                if categories:
                    categories += [categories[0]]
                    values += [values[0]]
                else:
                    st.info("No data available for the radar chart.")
                    st.stop()

                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Player Profile',
                    line_color='#FFD700',
                    fillcolor='rgba(255, 215, 0, 0.3)'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 1], showticklabels=False),
                        bgcolor='rgba(0,0,0,0)'
                    ),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=20, b=20),
                    height=300,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)'
                )
                st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

                st.markdown(f"""
                <div style="padding:15px; border-radius:12px; border-left: 5px solid #FFD700; background-color: #FFFDF0; margin-bottom:10px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
                    <h3 style="margin:0 0 10px 0; color: #D4AF37;">🌟 {t_title}</h3>
                    <p style="margin:0 0 10px 0; color: #555; font-size: 1.05rem;">{t_desc}</p>
                    <div style="padding-top: 10px; border-top: 1px dashed #E0D3A8;">
                        <p style="margin:0 0 5px 0; color: #3E5641; font-weight: 600;">Historical Match: {t_person}</p>
                        <p style="margin:0 0 5px 0; color: #777; font-size: 0.95rem;"><i>{t_status}</i></p>
                        <p style="margin:0; color: #A67C5D; font-style: italic; font-weight: 500;">{t_quote}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            except Exception as e:
                st.error(f"Analysis error: {e}")

    st.divider()

    st.divider()

    # -----------------------------------------------------------------------------
    # Admin Section: Grouped for visibility control
    # -----------------------------------------------------------------------------
    if st.session_state.get("is_admin", False):
        st.markdown("## 🛠 Admin Controls")
        
        # 1. Add New Match Result
        st.markdown("### ➕ Add New Match Result")
        with st.form("add_match_form", clear_on_submit=True):
            game_options = ["-- Select a Game --"] + available_games
            new_game = st.selectbox("Select Board Game", game_options)
            new_score_raw = st.text_input("Your Score (Leave empty for win/loss only games)", value="")
            new_is_winner = st.checkbox("Did you win?")
    
            submitted = st.form_submit_button("Save Match Result", type="primary")
            if submitted:
                if new_game == "-- Select a Game --":
                    st.warning("Please select a game first.")
                    st.stop()
                parsed_score = None
                if new_score_raw.strip():
                    try:
                        parsed_score = int(new_score_raw)
                    except ValueError:
                        st.error("Score must be a number or left empty.")
                        st.stop()
                if insert_match_result(current_player, new_game, parsed_score, new_is_winner):
                    st.success(f"Successfully added {new_game} to history!")
                    st.rerun()
                else:
                    st.error("Failed to save to database")

        st.divider()

        # 2. Manage Play History
        if not player_history_df.empty:
            st.markdown("### ⚙️ Manage Play History")
            display_df = player_history_df[['game_name', 'score', 'is_winner', 'played_at']].copy()
            display_df['score'] = display_df['score'].fillna("-")
            display_df['is_winner'] = display_df['is_winner'].map({1: "👑", 0: "", True: "👑", False: ""})
            display_df = display_df.rename(columns={"game_name": "Game", "score": "Score", "is_winner": "Winner", "played_at": "Date"})
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            player_history_df_sorted = player_history_df.sort_values("played_at", ascending=False)
            record_options = {
                f"{row['game_name']} - {row['played_at']} (Score: {row['score'] if row['score'] is not None else '-'}) {'🏆' if row['is_winner'] else ''}": row
                for _, row in player_history_df_sorted.iterrows()
            }
            record_to_modify = st.selectbox("Select record to modify or delete:", list(record_options.keys()))
            selected_row = record_options[record_to_modify]
            current_score_str = str(int(selected_row['score'])) if selected_row['score'] is not None else ""
            edit_score_raw = st.text_input("Update Score", value=current_score_str, key=f"score_{selected_row['history_id']}")
            edit_is_winner = st.checkbox("Did you win?", value=bool(selected_row['is_winner']), key=f"winner_{selected_row['history_id']}")
            
            edit_col1, edit_col2 = st.columns(2)
            with edit_col1:
                if st.button("Save Changes", key=f"save_{selected_row['history_id']}"):
                    parsed_edit_score = None
                    if edit_score_raw.strip():
                        try:
                            parsed_edit_score = int(edit_score_raw)
                        except ValueError:
                            st.error("Score must be a number.")
                            st.stop()
                    if update_match_result(selected_row['history_id'], parsed_edit_score, edit_is_winner):
                        st.success("Successfully updated record!")
                        st.rerun()
            with edit_col2:
                if st.button("🗑 Delete Record", key=f"delete_{selected_row['history_id']}"):
                    if delete_match_result(selected_row['history_id']):
                        st.success("Successfully deleted record!")
                        st.rerun()

            st.divider()
            st.markdown("### ⚠️ Danger Zone")
            if current_player != "-- Create New Player --":
                if st.button("🗑 Delete Entire Player Profile", key="del_player_btn", type="primary"):
                    if delete_player(current_player):
                        st.success(f"Player {current_player} deleted.")
                        st.rerun()
                    else:
                        st.error("Failed to delete.")

# -----------------------------------------------------------------------------
# Right Column: ML Engine
# -----------------------------------------------------------------------------
with col_ml:
    st.markdown("<h2 style='text-align: center; margin-bottom: 20px;'>You may like...</h2>", unsafe_allow_html=True)
    
    if history_df.empty or not current_player:
        st.info("Not enough data to make recommendations. Please add at least 1 game to your history.")
    else:
        try:
            if rec_engine:
                with st.spinner('Calculating...'):
                    recommendations = rec_engine.recommend(current_player, top_n=5)
                
                if not recommendations:
                    st.warning("All available games played.")
                else:
                    for i, rec_dict in enumerate(recommendations):
                        game_name = rec_dict["game"]
                        match_score = rec_dict["score"]
                        
                        stats = GAME_ATTRIBUTES.get(game_name, {})
                        category = stats.get('category', 'Unknown')
                        complexity = stats.get('complexity', 0)
                        
                        st.markdown(f"""
                        <div style="padding:15px; border-radius:10px; border:1px solid #ddd; margin-bottom:10px; background-color: #f8f9fa;">
                            <h3 style="margin:0; color: #1E88E5;">#{i+1}. {game_name}</h3>
                            <p style="margin:5px 0 0 0; color: #555;">
                                <b>Match Score:</b> {int(match_score * 100)}% | <b>Category:</b> {category} | <b>Complexity:</b> {int(complexity * 100)}%
                            </p>
                        </div>
                        """, unsafe_allow_html=True)
                                
        except Exception as e:
            st.error(f"Error: {e}")
