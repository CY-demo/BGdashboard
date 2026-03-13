import os
import random
import mysql.connector
from dotenv import load_dotenv

# Load database credentials
load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', 4000)),
    database=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
cursor = conn.cursor()

# 1. Clear existing test data (optional, but ensures a clean slate)
# Uncomment these if you want to wipe the slate clean before inserting:
# cursor.execute("DELETE FROM player_history")
# cursor.execute("DELETE FROM players")
# conn.commit()

# 2. Get Game IDs and logic definitions
cursor.execute("SELECT game_id, name FROM games")
games_db = {name: game_id for game_id, name in cursor.fetchall()}

# Define realistic scoring behaviors for the mock data
GAME_LOGIC = {
    "Catan": {"type": "score", "win_range": (10, 12), "lose_range": (4, 9)},
    "7 Wonders": {"type": "score", "win_range": (55, 75), "lose_range": (35, 54)},
    "7 Wonders Duel": {"type": "score", "win_range": (60, 80), "lose_range": (40, 59)},
    "Agricola": {"type": "score", "win_range": (40, 55), "lose_range": (20, 39)},
    "Wingspan": {"type": "score", "win_range": (80, 110), "lose_range": (50, 79)},
    "Scythe": {"type": "score", "win_range": (70, 100), "lose_range": (30, 69)},
    "Terraforming Mars": {"type": "score", "win_range": (90, 130), "lose_range": (60, 89)},
    "Ticket to Ride": {"type": "score", "win_range": (100, 140), "lose_range": (60, 99)},
    "Carcassonne": {"type": "score", "win_range": (90, 130), "lose_range": (50, 89)},
    "Dominion": {"type": "score", "win_range": (40, 60), "lose_range": (10, 39)},
    "Splendor": {"type": "score", "win_range": (15, 18), "lose_range": (8, 14)},
    "Everdell": {"type": "score", "win_range": (60, 85), "lose_range": (40, 59)},
    
    # Win/Lose only games (no scores)
    "Avalon": {"type": "win_lose"},
    "Betrayal at House on the Hill": {"type": "win_lose"},
    "Arkham Horror": {"type": "win_lose"},
    "Pandemic": {"type": "win_lose"},
    "Nemesis": {"type": "win_lose"},
    "Mansions of Madness": {"type": "win_lose"},
    
    # Party / Light games (scores are highly variable but let's give them ranges)
    "Dixit": {"type": "score", "win_range": (30, 35), "lose_range": (10, 29)},
    "Codenames": {"type": "win_lose"},
    "Secret Hitler": {"type": "win_lose"}
}

# 3. Create Players
players = ["Alice", "Bob", "Charlie", "David", "Eve"]
player_ids = {}

for p in players:
    cursor.execute("SELECT player_id FROM players WHERE player_name = %s", (p,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO players (player_name) VALUES (%s)", (p,))
        conn.commit()
        player_ids[p] = cursor.lastrowid
    else:
        player_ids[p] = row[0]

# 4. Generate Match History
# Alice is a hardcore strategy gamer (wins heavy games, loses party/social games)
# Bob is a social/party gamer (wins Avalon/Dixit, struggles with Scythe)
# Charlie is aggressively average, chaotic records.

print("Generating mock match history...")
count = 0

def insert_match(player, game_name, is_winner):
    global count
    if game_name not in games_db:
        return
        
    game_id = games_db[game_name]
    logic = GAME_LOGIC.get(game_name, {"type": "score", "win_range": (50, 100), "lose_range": (10, 49)})
    
    score = None
    if logic["type"] == "score":
        if is_winner:
            score = random.randint(logic["win_range"][0], logic["win_range"][1])
        else:
            score = random.randint(logic["lose_range"][0], logic["lose_range"][1])
            
    cursor.execute(
        "INSERT INTO player_history (player_id, game_id, score, is_winner) VALUES (%s, %s, %s, %s)",
        (player_ids[player], game_id, score, int(is_winner))
    )
    count += 1

# --- ALICE'S PROFILE (Loves heavy strategy, hates luck/social) ---
# High win rate in Euros/Strategy
for _ in range(4): insert_match("Alice", "Agricola", True)
for _ in range(2): insert_match("Alice", "Agricola", False)
for _ in range(3): insert_match("Alice", "Scythe", True)
insert_match("Alice", "Terraforming Mars", True)
insert_match("Alice", "Terraforming Mars", True)
insert_match("Alice", "Catan", True)
insert_match("Alice", "Catan", False)
# Low win rate in party/social
insert_match("Alice", "Avalon", False)
insert_match("Alice", "Avalon", False)
insert_match("Alice", "Dixit", False)

# --- BOB'S PROFILE (Loves social deduction and party) ---
# High win rate in Social/Party
for _ in range(5): insert_match("Bob", "Avalon", True)
for _ in range(2): insert_match("Bob", "Secret Hitler", True)
for _ in range(3): insert_match("Bob", "Dixit", True)
insert_match("Bob", "Codenames", True)
insert_match("Bob", "Betrayal at House on the Hill", True)
# Low win rate in Euros
insert_match("Bob", "Agricola", False)
insert_match("Bob", "Scythe", False)
insert_match("Bob", "Terraforming Mars", False)

# --- CHARLIE'S PROFILE (Loves engine building / mid-weight) ---
for _ in range(3): insert_match("Charlie", "Wingspan", True)
for _ in range(2): insert_match("Charlie", "Splendor", True)
for _ in range(4): insert_match("Charlie", "7 Wonders", True)
insert_match("Charlie", "7 Wonders", False)
insert_match("Charlie", "Ticket to Ride", True)
insert_match("Charlie", "Catan", True)
insert_match("Charlie", "Dominion", True)

# Commit all generated matches
conn.commit()
cursor.close()
conn.close()

print(f"✅ Successfully inserted {count} realistic match records into TiDB!")
print("Refresh your Streamlit app to see the ML algorithms in action.")
