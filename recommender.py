# recommender.py
# Recommendation engine using KNN or statistical fallback.

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import MinMaxScaler

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
        Uses win rate if available, otherwise relative score vs. other players.
        """
        game_data = self.results_df[self.results_df["game_name"] == game_name]
        player_data = game_data[game_data["player_name"] == player_name]

        if player_data.empty:
            return 0.0

        # Prefer win rate
        if "is_winner" in player_data.columns:
            win_rate = player_data["is_winner"].mean()
            return float(win_rate)

        # Fallback: relative score
        if "score" in game_data.columns:
            all_scores = game_data["score"]
            player_avg = player_data["score"].mean()
            overall_avg = all_scores.mean()
            overall_std = all_scores.std()

            if overall_std == 0:
                return 0.5
            # Normalise with sigmoid-like clamp
            relative = (player_avg - overall_avg) / (overall_std + 1e-9)
            return float(np.clip((relative + 2) / 4, 0, 1))  # map [-2,2] → [0,1]

        return 0.5  # neutral if no data

    def _build_game_matrix(self) -> pd.DataFrame:
        """Build a DataFrame of game feature vectors."""
        rows = {}
        for game, attrs in self.game_attrs.items():
            rows[game] = {k: attrs.get(k, 0.0) for k in FEATURE_KEYS}
        return pd.DataFrame.from_dict(rows, orient="index")
