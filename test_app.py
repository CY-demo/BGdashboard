import os
import streamlit as st
from db_manager import get_player_history, get_game_attributes
from recommender import Recommender
import numpy as np

print("Testing imports and classes...")
try:
    from app import *
    print("app.py imported successfully!")
except Exception as e:
    print(f"Error importing app.py: {e}")

try:
    rec = Recommender(None, None)
    print("Recommender initialized (empty) successfully!")
except Exception as e:
    print(f"Error initializing Recommender: {e}")
