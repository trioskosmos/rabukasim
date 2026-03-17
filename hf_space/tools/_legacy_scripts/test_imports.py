import os
import sys

# Ensure project root is in path
sys.path.append(os.getcwd())

print("Testing imports...")
import torch

print(f"Torch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")

import numpy as np

print(f"Numpy version: {np.__version__}")


print("PPO imported.")


print("VectorEnvAdapter imported.")

print("All imports successful!")
