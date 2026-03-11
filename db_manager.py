# db_manager.py
# Handles MySQL connections and CRUD operations.

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd
import json
import streamlit as st
import pandas as pd
import json

# Load environment variables from .env file
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "boardgame_tracker")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_db_connection():
    """Establishes and returns a connection to the MySQL database."""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        if connection.is_connected():
            return connection
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
        return None

@st.cache_data(ttl=3600)  # Cache the game attributes for 1 hour to prevent constant reloading
def get_game_attributes():
    """
    Retrieves all games from the BoardGames table and formats them into
    the exact nested dictionary expected by the recommender system.
        
    If the database is empty or fails, it falls back to the local games.json
    """
    connection = get_db_connection()
    if not connection:
        return _fallback_local_games_json()
        
    try:
        query = "SELECT * FROM BoardGames"
        
        # We use dictionary cursor so rows come back as dicts
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query)
        records = cursor.fetchall()
        
        if not records:
            return _fallback_local_games_json()
            
        # Reconstruct into the {"Game Name": {"strategy": 0.8, ...}} nested format
        game_dict = {}
        for row in records:
            name = row.pop("game_name")
            # The remaining columns (strategy, luck, category) become the inner dict
            game_dict[name] = row
            
        return game_dict
        
    except Error as e:
        print(f"Error fetching game attributes: {e}")
        return _fallback_local_games_json()
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def _fallback_local_games_json():
    """Fallback method to load local JSON if DB fails/is empty during development."""
    print("⚠️ [DB Warning] Connecting failed or table empty. Falling back to local games.json")
    try:
        with open('data/games.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def get_player_history(player_name=None):
    """
    Retrieves match history from PlayHistory table.
    If player_name is provided, filters for that specific player.
    Returns a pandas DataFrame.
    """
    connection = get_db_connection()
    # Dummy fallback during early development before DB is populated
    if not connection:
        return _fallback_local_history_df(player_name)
        
    try:
        if player_name:
            query = "SELECT history_id, player_name, game_name, score, is_winner FROM PlayHistory WHERE player_name = %s"
            params = (player_name,)
        else:
            query = "SELECT history_id, player_name, game_name, score, is_winner FROM PlayHistory"
            params = None
            
        # pandas can read SQL directly using the connection object!
        df = pd.read_sql(query, connection, params=params)
        
        if df.empty:
            return _fallback_local_history_df(player_name)
            
        return df
        
    except Error as e:
        print(f"Error fetching history: {e}")
        return _fallback_local_history_df(player_name)
    finally:
        if connection and connection.is_connected():
            connection.close()

def _fallback_local_history_df(player_name=None):
    """Fallback mock dataframe for development."""
    mock_history = [
        {"history_id": 1, "player_name": "Alice", "game_name": "Catan", "score": 10, "is_winner": True},
        {"history_id": 2, "player_name": "Alice", "game_name": "7 Wonders", "score": 50, "is_winner": False},
        {"history_id": 3, "player_name": "Bob", "game_name": "Dixit", "score": 3, "is_winner": True},
    ]
    df = pd.DataFrame(mock_history)
    if player_name:
        df = df[df["player_name"] == player_name]
    return df

def insert_match_result(player_name, game_name, score, is_winner):
    """Inserts a new match record into the database."""
    connection = get_db_connection()
    if not connection:
        print("⚠️ [DB Warning] Cannot insert match result: Database offline.")
        return False
        
    try:
        cursor = connection.cursor()
        query = """
            INSERT INTO PlayHistory (player_name, game_name, score, is_winner) 
            VALUES (%s, %s, %s, %s)
        """
        # Convert boolean to 1/0 for safe MySQL storage
        winner_bit = 1 if is_winner else 0
        cursor.execute(query, (player_name, game_name, score, winner_bit))
        connection.commit()
        return True
    except Error as e:
        print(f"Error inserting match result: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def update_match_result(history_id, new_score, new_is_winner):
    """Updates an existing match record (e.g. fixing a typo)."""
    connection = get_db_connection()
    if not connection:
        print("⚠️ [DB Warning] Cannot update match: Database offline.")
        return False
        
    try:
        cursor = connection.cursor()
        query = "UPDATE PlayHistory SET score = %s, is_winner = %s WHERE history_id = %s"
        winner_bit = 1 if new_is_winner else 0
        cursor.execute(query, (new_score, winner_bit, history_id))
        connection.commit()
        return True
    except Error as e:
        print(f"Error updating match: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def delete_match_result(history_id):
    """Deletes a match record from the database."""
    connection = get_db_connection()
    if not connection:
        print("⚠️ [DB Warning] Cannot delete match: Database offline.")
        return False
        
    try:
        cursor = connection.cursor()
        query = "DELETE FROM PlayHistory WHERE history_id = %s"
        cursor.execute(query, (history_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error deleting match: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

# Quick test if run directly
if __name__ == "__main__":
    print("Testing DB Manager...")
    test_conn = get_db_connection()
    if test_conn:
        print("✅ Successfully connected to MySQL database!")
        test_conn.close()
    else:
        print("❌ Could not connect to MySQL database. Please check XAMPP/MySQL service and .env file.")
