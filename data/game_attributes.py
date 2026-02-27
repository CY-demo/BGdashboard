"""
game_attributes.py
------------------
Defines the feature vector for each board game.
All values are normalized to [0.0, 1.0].

Attributes:
  strategy      - Long-term planning / strategic depth
  luck          - Randomness / luck factor
  negotiation   - Trading, bluffing, social manipulation
  deduction     - Logic, hidden info, deduction
  deck_building - Card/deck construction mechanic
  cooperation   - How cooperative the game is (0=pure competitive, 1=pure co-op)
  complexity    - Overall rule complexity
  duration_norm - Normalized play time (0=<30min, 1=>3hrs)

Category is used for the fallback (non-ML) recommendation system.
"""

import json
import os

# Load games data from JSON
_dir = os.path.dirname(os.path.abspath(__file__))
_json_path = os.path.join(_dir, "games.json")

with open(_json_path, "r", encoding="utf-8") as f:
    GAME_ATTRIBUTES = json.load(f)

# Ordered list of numeric feature keys (used for ML vector construction)
FEATURE_KEYS = [
    "strategy",
    "luck",
    "negotiation",
    "deduction",
    "deck_building",
    "cooperation",
    "complexity",
    "duration_norm",
]
