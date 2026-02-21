import os

import engine_rust
import numpy as np


class RustEnvLite:
    """
    A minimal, high-performance wrapper for the LovecaSim Rust engine.
    Bypasses Gymnasium/SB3 for direct, zero-copy training loops.
    """

    def __init__(self, num_envs, db_path="data/cards_compiled.json", opp_mode=0, mcts_sims=50):
        # 1. Load DB
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Card DB not found at {db_path}")

        with open(db_path, "r", encoding="utf-8") as f:
            json_str = f.read()
        self.db = engine_rust.PyCardDatabase(json_str)

        # 2. Params
        self.num_envs = num_envs
        self.obs_dim = 350
        self.action_dim = 2000

        # 3. Create Vector Engine
        self.game_state = engine_rust.PyVectorGameState(num_envs, self.db, opp_mode, mcts_sims)

        # 4. Pre-allocate Buffers (Zero-Copy)
        self.obs_buffer = np.zeros((num_envs, self.obs_dim), dtype=np.float32)
        self.rewards_buffer = np.zeros(num_envs, dtype=np.float32)
        self.dones_buffer = np.zeros(num_envs, dtype=bool)
        self.term_obs_buffer = np.zeros((num_envs, self.obs_dim), dtype=np.float32)
        self.mask_buffer = np.zeros((num_envs, self.action_dim), dtype=bool)

        # 5. Default Decks (Standard Play)
        # Using ID 1 (Member) and ID 100 (Live) as placeholders or from DB
        self.p0_deck = [1] * 48
        self.p1_deck = [1] * 48
        self.p0_lives = [100] * 12
        self.p1_lives = [100] * 12

    def reset(self, seed=None):
        if seed is None:
            seed = np.random.randint(0, 1000000)
        self.game_state.initialize(self.p0_deck, self.p1_deck, self.p0_lives, self.p1_lives, seed)
        self.game_state.get_observations(self.obs_buffer)
        return self.obs_buffer

    def step(self, actions):
        """
        Actions: np.ndarray (int32)
        Returns: obs (view), rewards (view), dones (view), done_indices
        """
        if actions.dtype != np.int32:
            actions = actions.astype(np.int32)

        done_indices = self.game_state.step(
            actions, self.obs_buffer, self.rewards_buffer, self.dones_buffer, self.term_obs_buffer
        )
        return self.obs_buffer, self.rewards_buffer, self.dones_buffer, done_indices

    def get_masks(self):
        self.game_state.get_action_masks(self.mask_buffer)
        return self.mask_buffer
