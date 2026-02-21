import json
import os

import engine_rust
import numpy as np
from gymnasium import spaces
from stable_baselines3.common.vec_env import VecEnv


class RustVectorEnv(VecEnv):
    def __init__(self, num_envs, action_space=None, opp_mode=0, force_start_order=-1, mcts_sims=50):
        # 1. Load DB
        db_path = "data/cards_compiled.json"
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Card DB not found at {db_path}")

        with open(db_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        self.db = engine_rust.PyCardDatabase(json_str)

        # 2. Create Vector State
        self.game_state = engine_rust.PyVectorGameState(num_envs, self.db, opp_mode, mcts_sims)

        # 3. Setup Spaces
        obs_dim = 350
        self.observation_space = spaces.Box(low=0, high=1, shape=(obs_dim,), dtype=np.float32)

        if action_space is None:
            self.action_space = spaces.Discrete(2000)
        else:
            self.action_space = action_space

        self.num_envs = num_envs
        self.actions = None

        # Pre-allocate buffers for Zero-Copy
        self.obs_buffer = np.zeros((num_envs, obs_dim), dtype=np.float32)
        self.rewards_buffer = np.zeros(num_envs, dtype=np.float32)
        self.dones_buffer = np.zeros(num_envs, dtype=bool)
        # Term obs buffer needs to accommodate worst case (all done)
        self.term_obs_buffer = np.zeros((num_envs, obs_dim), dtype=np.float32)
        self.mask_buffer = np.zeros((num_envs, 2000), dtype=bool)

        # 4. Load Deck Config
        self._load_decks()

        # 5. Initialize (Warmup)
        self.reset()

    def _load_decks(self):
        m_ids = []
        l_ids = []
        try:
            with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
                pool = json.load(f)

            if self.db.has_member(1):
                m_ids = [1] * 48
            else:
                ids = self.db.get_member_ids()
                if ids:
                    m_ids = [ids[0]] * 48
            l_ids = [100] * 12

        except Exception as e:
            print(f"Warning: Failed to load deck config: {e}")
            m_ids = [1] * 48
            l_ids = [100] * 12

        self.p0_deck = m_ids
        self.p1_deck = m_ids
        self.p0_lives = l_ids
        self.p1_lives = l_ids

    def reset(self):
        seed = np.random.randint(0, 1000000)
        self.game_state.initialize(self.p0_deck, self.p1_deck, self.p0_lives, self.p1_lives, seed)
        return self.get_observations()

    def step_async(self, actions):
        self.actions = actions

    def step_wait(self):
        if self.actions is None:
            return self.reset(), np.zeros(self.num_envs), np.zeros(self.num_envs, dtype=bool), [{}] * self.num_envs

        # Ensure int32
        actions = self.actions.astype(np.int32)

        # Call Rust step with pre-allocated buffers
        # Returns list of done indices
        done_indices = self.game_state.step(
            actions, self.obs_buffer, self.rewards_buffer, self.dones_buffer, self.term_obs_buffer
        )

        infos = [{} for _ in range(self.num_envs)]

        # Populate infos for done envs
        if done_indices:
            for i, env_idx in enumerate(done_indices):
                # Copy terminal obs from buffer to info dict
                infos[env_idx]["terminal_observation"] = self.term_obs_buffer[i].copy()

        # Return copies or views?
        # VecEnv expects new arrays usually, or we must ensure they aren't mutated during agent update.
        # SB3 PPO copies to rollout buffer, so views/buffers are fine IF they persist until next step.
        # But we overwrite them next step. This is fine.
        return self.obs_buffer.copy(), self.rewards_buffer.copy(), self.dones_buffer.copy(), infos

    def close(self):
        pass

    def get_attr(self, attr_name, indices=None):
        return [None] * self.num_envs

    def set_attr(self, attr_name, value, indices=None):
        pass

    def env_method(self, method_name, *method_args, **method_kwargs):
        return [None] * self.num_envs

    def env_is_wrapped(self, wrapper_class, indices=None):
        return [False] * self.num_envs

    def get_observations(self):
        self.game_state.get_observations(self.obs_buffer)
        return self.obs_buffer.copy()

    def action_masks(self):
        self.game_state.get_action_masks(self.mask_buffer)
        return self.mask_buffer.copy()
