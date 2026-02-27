"""
cold_start.py
-------------
Cold-start questionnaire for new players with no game history.

When a player has no recorded sessions, ask them a few simple questions
to build a synthetic "preference profile" vector that the Recommender
can use just like a real player profile.

Usage (CLI):
    from cold_start import ColdStart
    cs = ColdStart()
    profile = cs.run()          # interactive CLI
    recs = recommender.recommend_from_profile(profile, top_n=3)

Usage (Streamlit — non-interactive):
    profile = ColdStart.build_profile_from_answers(answers_dict)
"""

from data.game_attributes import FEATURE_KEYS
import numpy as np


# ─────────────────────────────────────────────────────────────────────────────
# Questions — each maps to one or more feature dimensions
# ─────────────────────────────────────────────────────────────────────────────

QUESTIONS = [
    {
        "id": "q_strategy",
        "text_en": "Do you enjoy games that require careful long-term planning?",
        "options_en": ["Not really", "Somewhat", "Yes, love it"],
        "maps_to": {"strategy": [0.1, 0.5, 0.9]},
    },
    {
        "id": "q_luck",
        "text_en": "How much randomness / luck do you enjoy?",
        "options_en": ["None — pure skill", "A little is fine", "Love the chaos"],
        "maps_to": {"luck": [0.05, 0.45, 0.9]},
    },
    {
        "id": "q_social",
        "text_en": "Do you like negotiating, trading, or deceiving other players?",
        "options_en": ["No, I prefer solo decisions", "Sometimes", "Absolutely"],
        "maps_to": {"negotiation": [0.1, 0.5, 0.9]},
    },
    {
        "id": "q_deduction",
        "text_en": "Do you enjoy figuring out hidden information or reading other players?",
        "options_en": ["Not my thing", "It's okay", "Yes, that's exciting"],
        "maps_to": {"deduction": [0.1, 0.5, 0.9]},
    },
    {
        "id": "q_cooperation",
        "text_en": "Would you rather cooperate with friends or compete against them?",
        "options_en": ["Compete!", "Either is fine", "Cooperate!"],
        "maps_to": {"cooperation": [0.05, 0.5, 0.95]},
    },
    {
        "id": "q_complexity",
        "text_en": "How complex of a game are you comfortable with?",
        "options_en": ["Simple rules only", "Medium complexity", "Bring on the rulebook"],
        "maps_to": {"complexity": [0.15, 0.5, 0.9]},
    },
    {
        "id": "q_duration",
        "text_en": "How long do you like your games to last?",
        "options_en": ["Under 30 min", "30–90 min", "2+ hours, no problem"],
        "maps_to": {"duration_norm": [0.1, 0.45, 0.9]},
    },
]


class ColdStart:
    """
    Collects player preferences via a short questionnaire and builds
    a profile vector compatible with the Recommender.
    """

    def run(self) -> np.ndarray:
        """
        Interactive CLI mode — prompts questions in the terminal.
        Shows English text with Chinese translations.

        Returns
        -------
        np.ndarray
            Profile vector of length len(FEATURE_KEYS).
        """
        print("\n Welcome! Let's find your perfect board game.\n")
        answers = {}

        for i, q in enumerate(QUESTIONS, 1):
            text = q['text_en']
            options = q['options_en']

            print(f"Q{i}. {text}")
            for j, opt in enumerate(options, 1):
                print(f"   {j}. {opt}")

            while True:
                try:
                    choice = int(input("   Your answer (1/2/3): ").strip())
                    if choice in (1, 2, 3):
                        answers[q["id"]] = choice - 1  # 0-indexed
                        break
                    print("   Please enter 1, 2, or 3.")
                except ValueError:
                    print("   Invalid input, try again.")
            print()

        return self.build_profile_from_answers(answers)

    @staticmethod
    def build_profile_from_answers(answers: dict) -> np.ndarray:
        """
        Build a profile vector from a dict of answer indices.

        Parameters
        ----------
        answers : dict
            Keys are question IDs (e.g. "q_strategy"), values are 0/1/2 (answer index).

        Returns
        -------
        np.ndarray
            Profile vector of length len(FEATURE_KEYS).
        """
        # Start with neutral profile (0.5 for all)
        profile = {k: 0.5 for k in FEATURE_KEYS}

        for q in QUESTIONS:
            q_id = q["id"]
            if q_id not in answers:
                continue
            idx = answers[q_id]
            for attr, values in q["maps_to"].items():
                profile[attr] = values[idx]

        # deck_building has no direct question — default to 0.3 (slightly below midpoint)
        if "deck_building" not in {attr for q in QUESTIONS for attr in q["maps_to"]}:
            profile["deck_building"] = 0.3

        return np.array([profile[k] for k in FEATURE_KEYS])
