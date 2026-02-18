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

GAME_ATTRIBUTES = {
    # ── Strategy ──────────────────────────────────────────────────────────────
    "Catan": {
        "strategy":       0.7,
        "luck":           0.5,
        "negotiation":    0.8,
        "deduction":      0.1,
        "deck_building":  0.0,
        "cooperation":    0.0,
        "complexity":     0.5,
        "duration_norm":  0.5,
        "category":       "Strategy",
    },
    "7 Wonders": {
        "strategy":       0.8,
        "luck":           0.2,
        "negotiation":    0.3,
        "deduction":      0.2,
        "deck_building":  0.4,
        "cooperation":    0.0,
        "complexity":     0.5,
        "duration_norm":  0.3,
        "category":       "Strategy",
    },
    "Terraforming Mars": {
        "strategy":       0.9,
        "luck":           0.3,
        "negotiation":    0.2,
        "deduction":      0.3,
        "deck_building":  0.5,
        "cooperation":    0.0,
        "complexity":     0.8,
        "duration_norm":  0.8,
        "category":       "Strategy",
    },

    # ── Deck Building ─────────────────────────────────────────────────────────
    "Dominion": {
        "strategy":       0.8,
        "luck":           0.3,
        "negotiation":    0.1,
        "deduction":      0.2,
        "deck_building":  1.0,
        "cooperation":    0.0,
        "complexity":     0.6,
        "duration_norm":  0.3,
        "category":       "Deck Building",
    },
    "Splendor": {
        "strategy":       0.7,
        "luck":           0.1,
        "negotiation":    0.1,
        "deduction":      0.3,
        "deck_building":  0.6,
        "cooperation":    0.0,
        "complexity":     0.4,
        "duration_norm":  0.3,
        "category":       "Engine Building",
    },

    # ── Worker Placement ──────────────────────────────────────────────────────
    "Agricola": {
        "strategy":       0.9,
        "luck":           0.2,
        "negotiation":    0.2,
        "deduction":      0.3,
        "deck_building":  0.0,
        "cooperation":    0.0,
        "complexity":     0.9,
        "duration_norm":  0.7,
        "category":       "Worker Placement",
    },
    "Viticulture": {
        "strategy":       0.7,
        "luck":           0.3,
        "negotiation":    0.2,
        "deduction":      0.2,
        "deck_building":  0.0,
        "cooperation":    0.0,
        "complexity":     0.6,
        "duration_norm":  0.6,
        "category":       "Worker Placement",
    },

    # ── Cooperative ───────────────────────────────────────────────────────────
    "Pandemic": {
        "strategy":       0.8,
        "luck":           0.4,
        "negotiation":    0.5,
        "deduction":      0.5,
        "deck_building":  0.0,
        "cooperation":    1.0,
        "complexity":     0.5,
        "duration_norm":  0.4,
        "category":       "Cooperative",
    },
    "Mansions of Madness": {
        "strategy":       0.6,
        "luck":           0.5,
        "negotiation":    0.3,
        "deduction":      0.7,
        "deck_building":  0.0,
        "cooperation":    0.9,
        "complexity":     0.7,
        "duration_norm":  0.9,
        "category":       "Cooperative",
    },

    # ── Social Deduction ──────────────────────────────────────────────────────
    "Avalon": {
        "strategy":       0.5,
        "luck":           0.0,
        "negotiation":    0.7,
        "deduction":      1.0,
        "deck_building":  0.0,
        "cooperation":    0.5,
        "complexity":     0.3,
        "duration_norm":  0.2,
        "category":       "Social Deduction",
    },
    "Werewolf": {
        "strategy":       0.3,
        "luck":           0.2,
        "negotiation":    0.8,
        "deduction":      0.8,
        "deck_building":  0.0,
        "cooperation":    0.5,
        "complexity":     0.2,
        "duration_norm":  0.2,
        "category":       "Social Deduction",
    },

    # ── Party ─────────────────────────────────────────────────────────────────
    "Dixit": {
        "strategy":       0.3,
        "luck":           0.4,
        "negotiation":    0.2,
        "deduction":      0.5,
        "deck_building":  0.0,
        "cooperation":    0.0,
        "complexity":     0.1,
        "duration_norm":  0.3,
        "category":       "Party",
    },
    "Codenames": {
        "strategy":       0.5,
        "luck":           0.1,
        "negotiation":    0.3,
        "deduction":      0.8,
        "deck_building":  0.0,
        "cooperation":    0.5,
        "complexity":     0.2,
        "duration_norm":  0.2,
        "category":       "Party",
    },

    # ── Thematic ──────────────────────────────────────────────────────────────
    "Betrayal at House on the Hill": {
        "strategy":       0.4,
        "luck":           0.6,
        "negotiation":    0.2,
        "deduction":      0.4,
        "deck_building":  0.0,
        "cooperation":    0.7,
        "complexity":     0.5,
        "duration_norm":  0.5,
        "category":       "Thematic",
    },
    "Arkham Horror": {
        "strategy":       0.7,
        "luck":           0.5,
        "negotiation":    0.3,
        "deduction":      0.6,
        "deck_building":  0.2,
        "cooperation":    0.9,
        "complexity":     0.9,
        "duration_norm":  1.0,
        "category":       "Thematic",
    },
}

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
