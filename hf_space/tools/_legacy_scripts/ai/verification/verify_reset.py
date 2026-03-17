import os
import sys

sys.path.append(os.getcwd())
from ai.vec_env_adapter import VectorEnvAdapter

print("Checking VectorEnv Reset...")
env = VectorEnvAdapter(1)
env.reset()
ctx = env.game_state.batch_global_ctx
print(f"Phase: {ctx[0, 8]}")
print(f"Energy: {ctx[0, 5]}")
