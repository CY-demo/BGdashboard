import sys
import os
sys.path.append(os.getcwd())
from db_manager import insert_match_result

# Define archetypes and their corresponding games
# Each game has 8 attributes, so we pick games that score high in the target attribute.
ARCHETYPES = {
    "Sun Tzu": [
        ("Terraforming Mars", 130, True),
        ("Brass: Birmingham", 150, True),
        ("Scythe", 85, True)
    ],
    "Napoleon": [
        ("Exploding Kittens", 5, True),
        ("Uno", 200, True),
        ("Betrayal at House on the Hill", 1, True)
    ],
    "Teddy Roosevelt": [
        ("Catan", 12, True),
        ("Sheriff of Nottingham", 45, True),
        ("7 Wonders", 60, True)
    ],
    "Sherlock": [
        ("The Resistance", 1, True),
        ("Codenames", 25, True),
        ("Mansions of Madness", 100, True)
    ],
    "Henry Ford": [
        ("Dominion", 40, True),
        ("7 Wonders Duel", 55, True),
        ("7 Wonders", 70, True)
    ],
    "Gandhi": [
        ("Pandemic", 1, True),
        ("Gloomhaven", 20, True),
        ("Mansions of Madness", 80, True)
    ],
    "Einstein": [
        ("Gloomhaven", 30, True),
        ("Brass: Birmingham", 160, True),
        ("Terraforming Mars", 140, True)
    ],
    "Mandela": [
        ("Twilight Imperium: Fourth Edition", 120, True),
        ("Gloomhaven", 25, True)
    ]
}

def seed():
    print("Starting data seeding for Archetypes...")
    for player, matches in ARCHETYPES.items():
        print(f"Adding history for {player}...")
        for game, score, winner in matches:
            success = insert_match_result(player, game, score, winner)
            if success:
                print(f"  [OK] {game}")
            else:
                print(f"  [FAIL] {game}")
    print("Seeding complete!")

if __name__ == "__main__":
    seed()
