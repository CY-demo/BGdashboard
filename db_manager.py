# db_manager.py
# Handles MySQL connections and CRUD operations.
# Uses direct MySQL connection — no SSH tunnel needed with cloud databases like Railway.

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd
import json
import streamlit as st

# Load environment variables from .env file
load_dotenv()

DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME", "")
DB_USER     = os.getenv("DB_USER", "")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_db_connection():
    """Establishes and returns a direct connection to the MySQL database."""
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

# ── Game Attributes ────────────────────────────────────────────────────────────

@st.cache_data(ttl=3600)
def get_game_attributes():
    """
    Retrieves all games from the `games` table and formats them into
    the nested dictionary expected by the recommender system.
    Falls back to local games.json if the DB is unreachable.
    """
    connection = get_db_connection()
    if not connection:
        return _fallback_local_games_json()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM games")
        records = cursor.fetchall()

        if not records:
            return _fallback_local_games_json()

        game_dict = {}
        for row in records:
            name = row.pop("name", None) or row.pop("game_name", None)
            row.pop("game_id", None)
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
    """Fallback to local JSON if DB fails / is empty during development."""
    print("⚠️ [DB Warning] Falling back to local games.json")
    try:
        with open('data/games.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

# ── Player History ─────────────────────────────────────────────────────────────

def get_player_history(player_name=None):
    """
    Retrieves match history via JOIN across players, games, player_history.
    Returns a pandas DataFrame.
    """
    connection = get_db_connection()
    if not connection:
        return _fallback_local_history_df(player_name)

    try:
        base_query = """
            SELECT ph.history_id, p.player_name, g.name as game_name,
                   ph.score, ph.is_winner, ph.created_at as played_at
            FROM player_history ph
            JOIN players p ON ph.player_id = p.player_id
            JOIN games g   ON ph.game_id   = g.game_id
        """
        if player_name:
            query  = base_query + " WHERE p.player_name = %s"
            params = (player_name,)
        else:
            query  = base_query
            params = None

        df = pd.read_sql(query, connection, params=params)

        if df.empty:
            return _fallback_local_history_df(player_name)

        # Ensure empty scores (NULL in DB) are treated properly, not as NaN floats
        df['score'] = df['score'].astype(object)
        df['score'] = df['score'].where(pd.notnull(df['score']), None)

        # Convert 'played_at' from UTC to PST (US/Pacific)
        if 'played_at' in df.columns:
            df['played_at'] = pd.to_datetime(df['played_at'])
            if df['played_at'].dt.tz is None:
                # If naive, assume it's UTC from the DB, then convert to PST
                df['played_at'] = df['played_at'].dt.tz_localize('UTC').dt.tz_convert('US/Pacific')
            else:
                df['played_at'] = df['played_at'].dt.tz_convert('US/Pacific')
            # Format back to a clean string for UI
            df['played_at'] = df['played_at'].dt.strftime('%Y-%m-%d %H:%M:%S PST')

        return df

    except Error as e:
        print(f"Error fetching history: {e}")
        return _fallback_local_history_df(player_name)
    finally:
        if connection and connection.is_connected():
            connection.close()


def _fallback_local_history_df(player_name=None):
    """Fallback mock dataframe for development / offline mode."""
    mock_history = [
        {"history_id": 1, "player_name": "Alice", "game_name": "Catan",     "score": 10, "is_winner": True,  "played_at": "2025-03-01"},
        {"history_id": 2, "player_name": "Alice", "game_name": "7 Wonders", "score": 50, "is_winner": False, "played_at": "2025-03-02"},
        {"history_id": 3, "player_name": "Bob",   "game_name": "Dixit",     "score": 3,  "is_winner": True,  "played_at": "2025-03-03"},
    ]
    df = pd.DataFrame(mock_history)
    if player_name:
        df = df[df["player_name"] == player_name]
    return df

# ── CRUD Operations ────────────────────────────────────────────────────────────

def insert_match_result(player_name, game_name, score, is_winner):
    """Inserts a new match record into the database."""
    connection = get_db_connection()
    if not connection:
        print("⚠️ [DB Warning] Cannot insert: Database offline.")
        return False

    try:
        cursor = connection.cursor()

        # 1. Get or create player_id
        cursor.execute("SELECT player_id FROM players WHERE player_name = %s", (player_name,))
        row = cursor.fetchone()
        player_id = row[0] if row else None
        if not player_id:
            cursor.execute("INSERT INTO players (player_name) VALUES (%s)", (player_name,))
            player_id = cursor.lastrowid

        # 2. Look up game_id
        cursor.execute("SELECT game_id FROM games WHERE name = %s", (game_name,))
        row = cursor.fetchone()
        if not row:
            print(f"⚠️ Game '{game_name}' not found in DB.")
            return False
        game_id = row[0]

        # 3. Insert record
        # Use None for SQL NULL if the score wasn't provided (for win/loss only games)
        sql_score = score if score is not None and str(score).strip() != "" else None
        
        cursor.execute(
            "INSERT INTO player_history (player_id, game_id, score, is_winner) VALUES (%s, %s, %s, %s)",
            (player_id, game_id, sql_score, 1 if is_winner else 0)
        )
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
    """Updates an existing match record."""
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        
        sql_score = new_score if new_score is not None and str(new_score).strip() != "" else None
        
        cursor.execute(
            "UPDATE player_history SET score = %s, is_winner = %s WHERE history_id = %s",
            (sql_score, 1 if new_is_winner else 0, history_id)
        )
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
        return False

    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM player_history WHERE history_id = %s", (history_id,))
        connection.commit()
        return True
    except Error as e:
        print(f"Error deleting match: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def delete_player(player_name):
    """Deletes a player and all their associated match history from the database."""
    connection = get_db_connection()
    if not connection:
        return False

    try:
        cursor = connection.cursor()
        
        # 1. Look up player_id
        cursor.execute("SELECT player_id FROM players WHERE player_name = %s", (player_name,))
        row = cursor.fetchone()
        if not row:
            print(f"⚠️ Player '{player_name}' not found.")
            return False
            
        player_id = row[0]
        
        # 2. Delete their history first (to respect foreign key constraints)
        cursor.execute("DELETE FROM player_history WHERE player_id = %s", (player_id,))
        
        # 3. Delete the player
        cursor.execute("DELETE FROM players WHERE player_id = %s", (player_id,))
        
        connection.commit()
        return True
    except Error as e:
        print(f"Error deleting player: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


# ── Quick connection test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing DB connection...")
    conn = get_db_connection()
    if conn:
        print("✅ Successfully connected to MySQL!")
        conn.close()
    else:
        print("❌ Could not connect. Check your .env DB credentials.")
