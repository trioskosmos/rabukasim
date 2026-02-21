import numpy as np
from ai.vector_env import VectorGameState


def test_minimal():
    print("Initializing VectorGameState(1)...")
    env = VectorGameState(num_envs=1)

    print("Resetting...")
    obs = env.reset()

    print("Stepping with action 0 (Pass)...")
    actions = np.zeros(1, dtype=np.int32)
    obs, rewards, dones, infos = env.step(actions)

    print(f"Match results: Reward={rewards[0]}, Done={dones[0]}")
    print("Success!")


if __name__ == "__main__":
    test_minimal()
