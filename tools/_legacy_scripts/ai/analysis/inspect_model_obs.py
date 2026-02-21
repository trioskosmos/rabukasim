import os

from sb3_contrib import MaskablePPO

model_path = "checkpoints/vector/interrupted_model.zip"
if os.path.exists(model_path):
    model = MaskablePPO.load(model_path, device="cpu")
    print(f"Model Path: {model_path}")
    print(f"Observation Space: {model.observation_space}")
    print(f"Action Space: {model.action_space}")
else:
    print(f"Model not found: {model_path}")
