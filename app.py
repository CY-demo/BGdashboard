"""
app.py
------
The main entry point for the Streamlit web application.
This script provides the UI for viewing/editing match history (CRUD)
and displays real-time ML board game recommendations.

Run with: streamlit run app.py
"""

import streamlit as st
from db_manager import get_player_history, get_game_attributes, insert_match_result, delete_match_result, update_match_result
from recommender import Recommender

# -----------------------------------------------------------------------------
# Setup
# -----------------------------------------------------------------------------
st.set_page_config(page_title="BoardGame Recommender", layout="wide")
st.title("BoardGame Recommender")

GAME_ATTRIBUTES = get_game_attributes()
available_games = list(GAME_ATTRIBUTES.keys())

col_data, col_ml = st.columns([1, 1])

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

    # Show history
    st.markdown(f"### History for **{current_player}**")

    player_history_df = get_player_history(current_player)
    
    if player_history_df.empty:
        st.info("No play history found.")
    else:
        st.dataframe(player_history_df[['game_name', 'score', 'is_winner']], use_container_width=True, hide_index=True)

    st.divider()

    # Create new record
st.markdown("### Add New Match Result")

with st.form("add_match_form", clear_on_submit=True):
        new_game = st.selectbox("Select Board Game", available_games)
        new_score = st.number_input("Your Score", min_value=0, value=10, step=1)
        new_is_winner = st.checkbox("Did you win?")

        submitted = st.form_submit_button("Save Match Result", type="primary")
        if submitted:
            if insert_match_result(current_player, new_game, new_score, new_is_winner):
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
        f"{row['game_name']} - {row['played_at']} (Score: {row['score']}) {'🏆' if row['is_winner'] else ''}": row
        for _, row in player_history_df_sorted.iterrows()
    }

    record_to_modify = st.selectbox("Select record to modify:", list(record_options.keys()))
    selected_row = record_options[record_to_modify]

    # Inputs for editing
    edit_score = st.number_input("Update Score", min_value=0, value=int(selected_row['score']), key=f"score_{selected_row['history_id']}")
    edit_is_winner = st.checkbox("Did you win?", value=bool(selected_row['is_winner']), key=f"winner_{selected_row['history_id']}")

    # Buttons for saving or deleting (outside form)
    edit_col1, edit_col2 = st.columns(2)
    with edit_col1:
        if st.button("Save Changes", key=f"save_{selected_row['history_id']}"):
            if update_match_result(selected_row['history_id'], edit_score, edit_is_winner):
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
