import os
import sys

from sb3_contrib import MaskablePPO
from stable_baselines3 import PPO

model_path = r"checkpoints/vector/interrupted_model.zip"
if not os.path.exists(model_path):
    print(f"Model not found: {model_path}")
    sys.exit(1)

try:
    model = MaskablePPO.load(model_path, device="cpu")
    print("Type: MaskablePPO")
    print(f"Obs Space: {model.observation_space}")
    print(f"Action Space: {model.action_space}")
except Exception as e:
    print(f"Failed to load as MaskablePPO: {e}")
    try:
        model = PPO.load(model_path, device="cpu")
        print("Type: PPO")
        print(f"Obs Space: {model.observation_space}")
    except Exception as e2:
        print(f"Failed to load as PPO: {e2}")
