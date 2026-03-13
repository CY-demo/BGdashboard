# db_manager.py
# Handles MySQL connections (via automatic SSH tunnel) and CRUD operations.

import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import pandas as pd
import json
import streamlit as st

try:
    from sshtunnel import SSHTunnelForwarder
    SSHTUNNEL_AVAILABLE = True
except ImportError:
    SSHTUNNEL_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# SSH Tunnel settings
SSH_HOST     = os.getenv("SSH_HOST", "")
SSH_PORT     = int(os.getenv("SSH_PORT", "22"))
SSH_USER     = os.getenv("SSH_USER", "")
SSH_PASSWORD = os.getenv("SSH_PASSWORD", "")

# MySQL settings
DB_HOST     = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT     = int(os.getenv("DB_PORT", "3306"))
DB_NAME     = os.getenv("DB_NAME", "boardgame_tracker")
DB_USER     = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── Tunnel management ──────────────────────────────────────────────────────────
_tunnel = None

def _start_tunnel():
    """Start SSH tunnel if credentials are provided and sshtunnel is installed."""
    global _tunnel
    if not SSHTUNNEL_AVAILABLE or not SSH_HOST or not SSH_USER:
        return None   # No tunnel — assume direct connection or PuTTY tunnel already open

    if _tunnel and _tunnel.is_active:
        return _tunnel  # Reuse existing tunnel

    try:
        _tunnel = SSHTunnelForwarder(
            (SSH_HOST, SSH_PORT),
            ssh_username=SSH_USER,
            ssh_password=SSH_PASSWORD,
            remote_bind_address=(DB_HOST, DB_PORT),
        )
        _tunnel.start()
        print(f"✅ SSH Tunnel established: {SSH_HOST} → {DB_HOST}:{DB_PORT}")
        return _tunnel
    except Exception as e:
        print(f"⚠️ SSH Tunnel failed ({e}). Trying direct connection...")
        return None


def get_db_connection():
    """Establishes and returns a connection to the MySQL database (via SSH tunnel if configured)."""
    tunnel = _start_tunnel()

    # If tunnel is active, connect through it; otherwise connect directly
    local_port = tunnel.local_bind_port if tunnel else DB_PORT

    try:
        connection = mysql.connector.connect(
            host="127.0.0.1",
            port=local_port,
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
    Retrieves match history from player_history table via JOIN.
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
        print("⚠️ [DB Warning] Cannot insert match result: Database offline.")
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
        cursor.execute(
            "INSERT INTO player_history (player_id, game_id, score, is_winner) VALUES (%s, %s, %s, %s)",
            (player_id, game_id, score, 1 if is_winner else 0)
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
        cursor.execute(
            "UPDATE player_history SET score = %s, is_winner = %s WHERE history_id = %s",
            (new_score, 1 if new_is_winner else 0, history_id)
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


# ── Quick connection test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing DB connection (with auto SSH tunnel if configured)...")
    conn = get_db_connection()
    if conn:
        print("✅ Successfully connected to MySQL!")
        conn.close()
    else:
        print("❌ Could not connect. Check your .env SSH and DB credentials.")
