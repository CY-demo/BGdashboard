import numpy as np
import pandas as pd
from cold_start import ColdStart
from recommender import Recommender


def main():
    print("=== Board Game Recommender Test Pipeline ===")

    print("\n" + "="*50)
    print("SCENARIO 1: EXISTING PLAYER (WITH HISTORY)")
    print("="*50)

    # Simulate an existing player's history (Alice has played and won Strategy games)
    mock_history = [
        {"player_name": "Alice", "game_name": "Catan", "score": 10, "is_winner": True},
        {"player_name": "Alice", "game_name": "7 Wonders", "score": 50, "is_winner": True},
        {"player_name": "Bob", "game_name": "Dixit", "score": 3, "is_winner": False},
    ]
    history_df = pd.DataFrame(mock_history)
    
    rec_history = Recommender(history_df)
    
    print("\n--- Alice's Game History ---")
    print(history_df[history_df["player_name"] == "Alice"][["game_name", "is_winner"]])

    print("\n--- Calculating ML Recommendations for Alice ---")
    alice_recs = rec_history.recommend(player_name="Alice", top_n=3)
    
    for r in alice_recs:
        print(f"🎲 {r['game']} (Similarity Score: {r['score']}) - Method: {r['method']}")


    print("\n\n" + "="*50)
    print("SCENARIO 2: NEW PLAYER (COLD START QUESTIONNAIRE)")
    print("="*50)

    # Initialize Recommender with empty history (simulating a brand new database)
    empty_df = pd.DataFrame(columns=["player_name", "game_name", "score", "is_winner"])
    rec_cold = Recommender(empty_df)

    # Run the Cold Start Questionnaire
    print("\n--- Starting Cold Start Questionnaire ---")
    cs = ColdStart()
    new_player_profile = cs.run()

    print("\n--- Generated Profile Vector ---")
    print(np.round(new_player_profile, 2))  # Rounded for readability

    # Get Recommendations
    print("\n--- Calculating ML Recommendations for New Player ---")
    recommendations = rec_cold.recommend_from_profile(new_player_profile, top_n=3)

    print("\nRecommended Games:")
    for r in recommendations:
        print(f"🎲 {r['game']} (Similarity Score: {r['score']}) - Method: {r['method']}")


if __name__ == "__main__":
    main()
