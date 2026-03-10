"""
bgg_fetcher.py
--------------
Fetches board game data from BoardGameGeek API and converts it into
ML-friendly features (0.0 to 1.0) for the recommender system.

Run: python bgg_fetcher.py
"""

import json

def convert_to_ml_features(bgg_data):
    """Converts raw BGG data into 8 ML profile dimensions [0.0, 1.0]."""
    tags_str = " ".join(bgg_data["tags"]).lower()
    
    # 1. Complexity (Weight is 1-5)
    complexity = (bgg_data["weight"] - 1.0) / 4.0
    
    # 2. Duration (Max 180 mins)
    avg_time = (bgg_data["min_time"] + bgg_data["max_time"]) / 2.0
    duration_norm = min(avg_time / 180.0, 1.0)
    
    # Default base scores
    features = {
        "strategy": 0.1, 
        "luck": 0.1, 
        "negotiation": 0.1, 
        "deduction": 0.1, 
        "deck_building": 0.0, 
        "cooperation": 0.0,
        "complexity": complexity,
        "duration_norm": duration_norm
    }
    
    # ── Strategy ──
    if "worker placement" in tags_str: features["strategy"] += 0.5
    if "action points" in tags_str or "network and route" in tags_str: features["strategy"] += 0.4
    if "engine building" in tags_str: features["strategy"] += 0.4
    if complexity > 0.6: features["strategy"] += 0.2
    
    # ── Luck ──
    if "dice rolling" in tags_str or "push your luck" in tags_str: features["luck"] += 0.5
    if "card drafting" in tags_str: features["luck"] += 0.2
    
    # ── Negotiation ──
    if "negotiation" in tags_str or "trading" in tags_str: features["negotiation"] += 0.5
    if "bluffing" in tags_str: features["negotiation"] += 0.4
    if "social deduction" in tags_str: features["negotiation"] += 0.3
    
    # ── Deduction ──
    if "deduction" in tags_str: features["deduction"] += 0.7
    if "hidden roles" in tags_str or "secret unit deployment" in tags_str: features["deduction"] += 0.5
    if "memory" in tags_str: features["deduction"] += 0.4
    
    # ── Deck Building ──
    if "deck, bag, and pool building" in tags_str: features["deck_building"] = 1.0
    elif "deck construction" in tags_str: features["deck_building"] += 0.5
    
    # ── Cooperation ──
    if "cooperative" in tags_str: features["cooperation"] = 1.0
    elif "team-based" in tags_str or "partnerships" in tags_str: features["cooperation"] = 0.5
    
    # Normalize everything to strictly [0.0, 1.0] and round for cleanliness
    for key in features:
        features[key] = round(min(max(features[key], 0.0), 1.0), 2)
        
    return features

def main():
    print("=== BGG Data to ML Feature Pipeline ===")
    print("This script demonstrates the mathematical logic used to convert raw BGG data into our 8-Dimensional ML profile.\n")

    # 1. Provide a raw sample dictionary simulating what a web scraper would return
    raw_bgg_sample = {
        "name": "Scythe",
        "weight": 3.44,              # Scythe has a complexity rating of ~3.44 / 5.0
        "min_time": 90.0,            # Min play time 90 mins
        "max_time": 115.0,           # Max play time 115 mins
        "tags": [
            "Action Points",         # Strategic mechanics
            "Area Majority", 
            "Engine Building", 
            "Card-Driven",           # Some luck/deck component
            "Economic",
            "Strategy"      
        ]
    }

    print("--- [INPUT] Raw BGG Data ---")
    print(json.dumps(raw_bgg_sample, indent=4, ensure_ascii=False))

    # 2. Run our conversion formula
    print("\n--- [PROCESSING] Running conversion logic... ---")
    ml_features_output = convert_to_ml_features(raw_bgg_sample)
    
    # 3. Output the final result
    print("\n--- [OUTPUT] 8-Dimensional ML Vector [0.0 - 1.0] ---")
    print(json.dumps(ml_features_output, indent=4, ensure_ascii=False))
    
    print("\n✅ This logic was manually applied to the 23 games stored in data/games.json")

if __name__ == "__main__":
    main()
