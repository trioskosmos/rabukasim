from ai.gym_env import LoveLiveCardGameEnv

print("Test: Initializing Environment...")
env = LoveLiveCardGameEnv()
print("Test: Resetting...")
obs, info = env.reset()
print(f"Test: Reset Complete. Obs shape: {obs.shape}")

print("Test: Stepping...")
action = env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
print(f"Test: Step Complete. Reward: {reward}")
print("Test: SUCCESS")
