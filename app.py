"""
app.py
------
The main entry point for the Streamlit web application.
This script provides the UI for viewing/editing match history (CRUD)
and displays real-time ML board game recommendations.

Run with: streamlit run app.py
"""

import streamlit as st
from db_manager import get_player_history, get_game_attributes, insert_match_result, delete_match_result, update_match_result, delete_player
from recommender import Recommender

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="BoardGame Recommender", layout="wide", initial_sidebar_state="collapsed")
st.title("BoardGame Recommender")

GAME_ATTRIBUTES = get_game_attributes()
available_games = list(GAME_ATTRIBUTES.keys())

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
# Left Column: DB CRUD
# -----------------------------------------------------------------------------
with col_data:
    st.header("Manage Play History")
    
    st.markdown("### Player Select")
    history_df = get_player_history()
    existing_players = []
    if not history_df.empty:
        existing_players = history_df["player_name"].unique().tolist()
        
    current_player = st.selectbox("Who is playing?", existing_players + ["-- Create New Player --"])
    
    if current_player == "-- Create New Player --":
        current_player = st.text_input("Enter new player name:")
        
    if not current_player:
        st.warning("Please select or enter a player name to continue.")
        st.stop()

    # Show history header
    st.markdown(f"### History for **{current_player}**")

    player_history_df = get_player_history(current_player)
    
    if player_history_df.empty:
        st.info("No play history found.")
    else:
        # Display score as '-' if it is None, and map winner to emoji
        display_df = player_history_df[['game_name', 'score', 'is_winner']].copy()
        display_df['score'] = display_df['score'].fillna("-")
        display_df['is_winner'] = display_df['is_winner'].map({True: "👑", False: ""})
        
        # Rename columns for better presentation
        display_df = display_df.rename(columns={
            "game_name": "Game",
            "score": "Score",
            "is_winner": "Winner"
        })
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.divider()

    # Create new record
st.markdown("### Add New Match Result")

with st.form("add_match_form", clear_on_submit=True):
        # Add a placeholder option at the top so it doesn't default to the first game
        game_options = ["-- Select a Game --"] + available_games
        new_game = st.selectbox("Select Board Game", game_options)
        
        # Use text_input instead of number_input to allow empty values
        new_score_raw = st.text_input("Your Score (Leave empty for win/loss only games)", value="")
        new_is_winner = st.checkbox("Did you win?")

        submitted = st.form_submit_button("Save Match Result", type="primary")
        if submitted:
            if new_game == "-- Select a Game --":
                st.warning("Please select a game first.")
                st.stop()
                
            # Parse score: None if empty, integer if valid number
            parsed_score = None
            if new_score_raw.strip():
                try:
                    parsed_score = int(new_score_raw)
                except ValueError:
                    st.error("Score must be a number or left empty.")
                    st.stop()
                    
            if insert_match_result(current_player, new_game, parsed_score, new_is_winner):
                st.success(f"Successfully added {new_game} to history!")
                st.rerun()  # refresh the page
            else:
                st.error("Failed to save to database")

st.divider()
          
     # Edit/Delete
if not player_history_df.empty:
    # Sort by played_at / session_date
    player_history_df_sorted = player_history_df.sort_values("played_at", ascending=False)

    # Build options for the selectbox
    record_options = {
        f"{row['game_name']} - {row['played_at']} (Score: {row['score'] if row['score'] is not None else '-'}) {'🏆' if row['is_winner'] else ''}": row
        for _, row in player_history_df_sorted.iterrows()
    }

    record_to_modify = st.selectbox("Select record to modify:", list(record_options.keys()))
    selected_row = record_options[record_to_modify]

    # Inputs for editing
    current_score_str = str(int(selected_row['score'])) if selected_row['score'] is not None else ""
    edit_score_raw = st.text_input("Update Score (Leave empty for win/loss only games)", value=current_score_str, key=f"score_{selected_row['history_id']}")
    edit_is_winner = st.checkbox("Did you win?", value=bool(selected_row['is_winner']), key=f"winner_{selected_row['history_id']}")

    # Buttons for saving or deleting (outside form)
    edit_col1, edit_col2 = st.columns(2)
    with edit_col1:
        if st.button("Save Changes", key=f"save_{selected_row['history_id']}"):
            parsed_edit_score = None
            if edit_score_raw.strip():
                try:
                    parsed_edit_score = int(edit_score_raw)
                except ValueError:
                    st.error("Score must be a number or left empty.")
                    st.stop()
                    
            if update_match_result(selected_row['history_id'], parsed_edit_score, edit_is_winner):
                st.success(f"Successfully updated {selected_row['game_name']} record!")
                st.rerun()
            else:
                st.error("Failed to update record.")
    with edit_col2:
        if st.button("🗑 Delete Record", key=f"delete_{selected_row['history_id']}"):
            if delete_match_result(selected_row['history_id']):
                st.success(f"Successfully deleted {selected_row['game_name']} record!")
                st.rerun()
            else:
                st.error("Failed to delete record.")
                
    st.divider()
    st.markdown("### Danger Zone")
    if current_player != "-- Create New Player --":
        if st.button("🗑 Delete Entire Player Profile", key=f"del_player_btn", type="primary"):
            if delete_player(current_player):
                st.success(f"Player {current_player} deleted.")
                st.rerun()
            else:
                st.error("Failed to delete.")

# -----------------------------------------------------------------------------
# Right Column: ML Engine
# -----------------------------------------------------------------------------
with col_ml:
    st.header("ML Recommendations")
    
    fresh_history_df = get_player_history()
    
    if fresh_history_df.empty or current_player not in fresh_history_df["player_name"].values:
        st.info("Not enough data to make recommendations. Please add at least 1 game to your history.")
    else:
        try:
            rec_engine = Recommender(fresh_history_df, game_attrs=GAME_ATTRIBUTES)
            
            with st.spinner('Calculating...'):
                recommendations = rec_engine.recommend(current_player, top_n=5)
            
            if not recommendations:
                st.warning("All available games played.")
            else:
                st.success("Analysis Complete")
                
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
