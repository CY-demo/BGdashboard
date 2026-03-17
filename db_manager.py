# db_manager.py
# Handles MySQL connections and CRUD operations.
# Uses direct MySQL connection — no SSH tunnel needed with cloud databases like Railway.

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd
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
        return {}

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM games")
        records = cursor.fetchall()

        if not records:
            return {}

        game_dict = {}
        for row in records:
            name = row.pop("name", None) or row.pop("game_name", None)
            row.pop("game_id", None)
            game_dict[name] = row

        return game_dict

    except Error as e:
        print(f"Error fetching game attributes: {e}")
        return {}
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()




# ── Player History ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def get_player_history(player_name=None):
    """
    Retrieves match history via JOIN across players, games, player_history.
    Returns a pandas DataFrame.
    """
    connection = get_db_connection()
    if not connection:
        return pd.DataFrame()

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
            return pd.DataFrame()

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
        return pd.DataFrame()
    finally:
        if connection and connection.is_connected():
            connection.close()

@st.cache_data(ttl=600)
def get_top_games(limit=3):
    """Returns the most played games across all players."""
    connection = get_db_connection()
    if not connection:
        return []

    try:
        query = """
            SELECT g.game_id, g.name as game_name, COUNT(ph.history_id) as play_count
            FROM player_history ph
            JOIN games g ON ph.game_id = g.game_id
            GROUP BY g.game_id, g.name
            ORDER BY play_count DESC
            LIMIT %s
        """
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching top games: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()
            
@st.cache_data(ttl=600)
def get_recent_activity(limit=5):
    """Returns the most recent matches played across all players."""
    connection = get_db_connection()
    if not connection:
        return []

    try:
        query = """
            SELECT p.player_name, g.name as game_name, ph.score, ph.is_winner, ph.created_at as played_at
            FROM player_history ph
            JOIN players p ON ph.player_id = p.player_id
            JOIN games g ON ph.game_id = g.game_id
            ORDER BY ph.created_at DESC
            LIMIT %s
        """
        df = pd.read_sql(query, connection, params=(limit,))
        if df.empty:
            return []
            
        # Ensure empty scores are None, not NaN floats
        df['score'] = df['score'].astype(object)
        df['score'] = df['score'].where(pd.notnull(df['score']), None)
            
        # Timezone conversion for display
        if 'played_at' in df.columns:
            df['played_at'] = pd.to_datetime(df['played_at'])
            if df['played_at'].dt.tz is None:
                df['played_at'] = df['played_at'].dt.tz_localize('UTC').dt.tz_convert('US/Pacific')
            else:
                df['played_at'] = df['played_at'].dt.tz_convert('US/Pacific')
            df['played_at'] = df['played_at'].dt.strftime('%H:%M PST')
            
        return df.to_dict('records')
    except Error as e:
        print(f"Error fetching recent activity: {e}")
        return []
    finally:
        if connection and connection.is_connected():
            connection.close()




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
        st.cache_data.clear() # Clear cache on data modification
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
        st.cache_data.clear() # Clear cache on data modification
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
        st.cache_data.clear() # Clear cache on data modification
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
        st.cache_data.clear() # Clear cache on data modification
        return True
    except Error as e:
        print(f"Error deleting player: {e}")
        return False
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()


def get_top_players_for_game(game_id, limit=3):
    """Returns the top players for a specific game based on win count (or score if win count ties)."""
    connection = get_db_connection()
    if not connection:
        return []
        
    try:
        query = """
            SELECT p.player_name, COUNT(ph.history_id) as wins, MAX(ph.score) as highest_score
            FROM player_history ph
            JOIN players p ON ph.player_id = p.player_id
            WHERE ph.game_id = %s AND ph.is_winner = 1
            GROUP BY p.player_id
            ORDER BY wins DESC, highest_score DESC
            LIMIT %s
        """
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, (game_id, limit))
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching top players for game: {e}")
        return []
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
