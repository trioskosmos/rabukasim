# Import our environment
from ai.gym_env import LoveLiveCardGameEnv
from sb3_contrib import MaskablePPO
from sb3_contrib.common.maskable.utils import get_action_masks
from sb3_contrib.common.wrappers import ActionMasker


def make_env():
    env = LoveLiveCardGameEnv()
    # Wrap with ActionMasker for MaskablePPO logic
    env = ActionMasker(env, lambda env: env.action_masks())
    return env


def main():
    # Create Environment
    env = make_env()

    # Define Model (MaskablePPO)
    model = MaskablePPO(
        "MlpPolicy", env, verbose=1, gamma=0.99, learning_rate=3e-4, tensorboard_log="./logs/ppo_tensorboard/"
    )

    print("Starting Training...")
    # Train for 100k steps
    model.learn(total_timesteps=100_000, progress_bar=True)

    # Save Model
    model.save("checkpoints/lovelive_ppo_agent")
    print("Training Complete. Model Saved.")

    # Test Run
    obs, _ = env.reset()
    done = False
    total_reward = 0
    while not done:
        # Predict using masks
        action_masks = get_action_masks(env)
        action, _states = model.predict(obs, action_masks=action_masks, deterministic=True)

        obs, reward, done, truncated, info = env.step(action)
        total_reward += reward
        env.render()

    print(f"Test Run Reward: {total_reward}")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print(f"Import Error: {e}")
        print("Please install: pip install -r requirements_rl.txt")
