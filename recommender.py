# recommender.py
# Recommendation engine using KNN or statistical fallback.

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors

FEATURE_KEYS = [
    "strategy",
    "luck",
    "negotiation",
    "deduction",
    "deck_building",
    "cooperation",
    "complexity",
    "duration_norm"
]

class Recommender:
    """
    Board game recommender for a specific player.

    Parameters
    ----------
    results_df : pd.DataFrame
        Must have columns: [player_name, game_name, score, is_winner]
        Each row = one player's result in one session.
    game_attrs : dict, optional
        Override the default GAME_ATTRIBUTES dict (useful for testing).
    """

    def __init__(self, results_df: pd.DataFrame, game_attrs: dict = None):
        self.results_df = results_df.copy()
        self.game_attrs = game_attrs or {}

        # Build game feature matrix (DataFrame)
        self._game_df = self._build_game_matrix()

    # Public API

    def recommend(self, player_name: str, top_n: int = 3):
        """
        Return top_n game recommendations for a player using KNN.
        """
        played = self._games_played_by(player_name)
        unplayed = [g for g in self.game_attrs if g not in played]

        if not unplayed:
            return []  # Player has played everything — nothing to recommend

        try:
            return self._ml_recommend(player_name, unplayed, top_n)
        except Exception as e:
            print(f"[Recommender] ML failed ({e})")
            return []



    # ML Recommendation

    def _ml_recommend(self, player_name: str, unplayed: list, top_n: int):
        """
        1. Build player profile vector (weighted average of game vectors,
           weighted by relative win-rate / normalised score).
        2. Use KNN (cosine distance) to find closest unplayed games.
        """
        profile = self._build_player_profile(player_name)

        # Filter game matrix to unplayed games only
        unplayed_df = self._game_df.loc[
            self._game_df.index.isin(unplayed), FEATURE_KEYS
        ]

        if unplayed_df.empty:
            return []

        # KNN with cosine distance
        k = min(top_n, len(unplayed_df))
        knn = NearestNeighbors(n_neighbors=k, metric="cosine")
        knn.fit(unplayed_df.values)

        distances, indices = knn.kneighbors([profile])
        recommended_games = unplayed_df.iloc[indices[0]].index.tolist()
        similarity_scores = 1 - distances[0]  # cosine similarity

        return [
            {
                "game": game,
                "score": round(float(sim), 3),
                "method": "ML (KNN Cosine Similarity)",
            }
            for game, sim in zip(recommended_games, similarity_scores)
        ]

    def get_player_traits(self, player_name: str) -> dict:
        """
        Analyses the player's profile and returns a descriptive trait based on their highest feature weight.
        """
        try:
            profile = self._build_player_profile(player_name)
            max_idx = np.argmax(profile)
            top_feature = FEATURE_KEYS[max_idx]

            traits_map = {
                "strategy": {"title": "You are a Strategist! 🧠", "desc": "You carefully plan every move to ensure absolute victory."},
                "luck": {"title": "You are lucky! 🎲", "desc": "You thrive in chaos and trust your luck to carry the day!"},
                "negotiation": {"title": "You are a Negotiator! 🗣️", "desc": "You are a master of words, talking your way into the lead."},
                "deduction": {"title": "You are a Detective! 🔍", "desc": "Nothing escapes your keen eye and logical mind."},
                "deck_building": {"title": "You are an Engine Builder! ⚙️", "desc": "You love creating powerful combos and efficient systems."},
                "cooperation": {"title": "You are a Collaborator! 🤝", "desc": "You are a great team player who brings everyone together."},
                "complexity": {"title": "You are brave! 🧩", "desc": "You love diving into deep, complex game mechanics!"},
                "duration_norm": {"title": "You are an Endurance Gamer! ⏱️", "desc": "You have the patience and focus for epic, long-lasting games."}
            }

            return traits_map.get(top_feature, {"title": "You are a Versatile Gamer! 🎮", "desc": "You have a balanced and adaptable playstyle."})

        except Exception as e:
            return {"title": "You are a Mystery Gamer! 🕵️", "desc": "Your playstyle is truly unpredictable!"}


    def _build_player_profile(self, player_name: str) -> np.ndarray:
        """
        Player profile = weighted average of game feature vectors.
        Weight = player's normalised performance in that game.

        Performance metric: relative score (player score / avg score in that game)
        capped at [0, 1].
        """
        played = self._games_played_by(player_name)
        weights = []
        vectors = []

        for game in played:
            if game not in self.game_attrs:
                continue

            perf = self._player_performance(player_name, game)
            vec = np.array([self.game_attrs[game][k] for k in FEATURE_KEYS])
            weights.append(perf)
            vectors.append(vec)

        if not vectors:
            raise ValueError(f"No valid game data for player '{player_name}'")

        weights = np.array(weights)
        # Avoid division by zero
        if weights.sum() == 0:
            weights = np.ones(len(weights))
        weights = weights / weights.sum()

        profile = np.average(np.array(vectors), axis=0, weights=weights)
        return profile



    # Utilities

    def _games_played_by(self, player_name: str) -> list:
        mask = self.results_df["player_name"] == player_name
        return self.results_df.loc[mask, "game_name"].unique().tolist()

    def _player_performance(self, player_name: str, game_name: str) -> float:
        """
        Returns a normalised performance score in [0, 1].
        Blends win rate (70%) and relative score vs. other players (30%).
        If the game has no valid numerical scores (win/loss only), uses 100% win rate.
        """
        game_data = self.results_df[self.results_df["game_name"] == game_name]
        player_data = game_data[game_data["player_name"] == player_name]

        if player_data.empty:
            return 0.0

        # Calculate Win Rate component (0.0 or 1.0)
        win_rate = 0.0
        if "is_winner" in player_data.columns:
            win_rate = float(player_data["is_winner"].mean())

        # Filter out rows where score is None/NaN
        has_scores = False
        if "score" in game_data.columns:
            valid_scores_mask = game_data["score"].notna()
            valid_game_data = game_data[valid_scores_mask]
            valid_player_data = player_data[player_data["score"].notna()]
            
            if not valid_game_data.empty and not valid_player_data.empty:
                has_scores = True
                
        # Calculate Relative Score component (0.0 to 1.0) if scores exist
        if has_scores:
            all_scores = valid_game_data["score"].astype(float)
            player_avg = valid_player_data["score"].astype(float).mean()
            overall_avg = all_scores.mean()
            overall_std = all_scores.std()

            rel_score_norm = 0.5
            if overall_std > 0:
                # Normalise with sigmoid-like clamp
                relative = (player_avg - overall_avg) / (overall_std + 1e-9)
                rel_score_norm = float(np.clip((relative + 2) / 4, 0, 1))

            # Blend the two metrics
            blended_score = (0.7 * win_rate) + (0.3 * rel_score_norm)
            return float(np.clip(blended_score, 0, 1))
        else:
            # If no valid scores exist (e.g. Avalon, Betrayal), performance is purely based on win rate
            return float(np.clip(win_rate, 0.1, 1.0)) # Give at least 0.1 for playing the game

    def _build_game_matrix(self) -> pd.DataFrame:
        """Build a DataFrame of game feature vectors."""
        rows = {}
        for game, attrs in self.game_attrs.items():
            rows[game] = {k: attrs.get(k, 0.0) for k in FEATURE_KEYS}
        return pd.DataFrame.from_dict(rows, orient="index")
