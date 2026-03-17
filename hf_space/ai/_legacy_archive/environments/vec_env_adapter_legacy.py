import numpy as np
from ai.vector_env_legacy import VectorGameState
from gymnasium import spaces
from stable_baselines3.common.vec_env import VecEnv


class VectorEnvAdapter(VecEnv):
    """
    Wraps the LEGACY Numba-accelerated VectorGameState (320 dim).
    """

    metadata = {"render_modes": ["rgb_array"]}

    def __init__(self, num_envs, observation_space_dim=320, action_space=None):
        self.num_envs = num_envs
        self.game_state = VectorGameState(num_envs)
        # Observation Space size - Flexible Legacy
        obs_dim = observation_space_dim
        self.observation_space = spaces.Box(low=0, high=1, shape=(obs_dim,), dtype=np.float32)
        if action_space is None:
            action_space = spaces.Discrete(1000)

        self.action_space = action_space
        self.actions = None
        self.render_mode = None

        # Track previous scores for delta-based rewards (Same logic is fine)
        self.prev_scores = np.zeros(num_envs, dtype=np.int32)

    def reset(self):
        self.game_state.reset()
        self.prev_scores.fill(0)
        return self.game_state.get_observations()

    def step_async(self, actions):
        self.actions = actions

    def step_wait(self):
        actions_int32 = self.actions.astype(np.int32)

        # Legacy step doesn't support opponent simulation internally usually?
        # Checked vector_env_legacy.py: step_vectorized DOES exist.
        # But looking at legacy file content:
        # It calls batch_apply_action.
        # It does NOT call step_opponent_vectorized.
        # So legacy environment is "Solitaire" only?
        # That means Opponent Score never increases?
        # If so, comparing against Random Opponent logic inside New Env is unfair.
        # But wait, if Legacy Model was trained in Solitaire, it expects Solitaire.
        # If I want to compare "Performance", I should use the same conditions.
        # However, the user wants to compare "Checkpoints".
        # If legacy checkpoint was trained for "Reach 10 points fast", then benchmark is "Average Turns to 10".

        self.game_state.step(actions_int32)
        obs = self.game_state.get_observations()

        # Rewards (Same logic as modern adapter to ensure fair comparison of metrics?)
        current_scores = self.game_state.batch_scores
        delta_scores = current_scores - self.prev_scores
        rewards = delta_scores.astype(np.float32)
        rewards -= 0.001

        dones = current_scores >= 10
        win_mask = dones & (delta_scores > 0)
        rewards[win_mask] += 5.0

        self.prev_scores = current_scores.copy()

        if np.any(dones):
            reset_indices = np.where(dones)[0]
            self.game_state.reset(list(reset_indices))
            self.prev_scores[reset_indices] = 0
            obs = self.game_state.get_observations()
            infos = []
            for i in range(self.num_envs):
                if dones[i]:
                    infos.append({"terminal_observation": obs[i], "episode": {"r": rewards[i], "l": 10}})
                else:
                    infos.append({})
        else:
            infos = [{} for _ in range(self.num_envs)]

        return obs, rewards, dones, infos

    def close(self):
        pass

    def get_attr(self, attr_name, indices=None):
        return []

    def set_attr(self, attr_name, value, indices=None):
        pass

    def env_method(self, method_name, *method_args, **method_kwargs):
        return []

    def env_is_wrapped(self, wrapper_class, indices=None):
        return [False] * self.num_envs

    def action_masks(self):
        # Legacy env has no masks, return all True
        return np.ones((self.num_envs, 1000), dtype=bool)
