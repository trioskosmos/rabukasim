"""
GPU-Native Vectorized Game Environment.

This module provides VectorEnvGPU - a GPU-resident implementation using CuPy
and Numba CUDA for maximum throughput. All game state arrays live in GPU VRAM,
eliminating PCI-E transfer overhead during RL training.

Usage:
    Set USE_GPU_ENV=1 to enable GPU environment in training.
"""

import json
import os
import time

import numpy as np

# CUDA detection
HAS_CUDA = False
try:
    import cupy as cp
    from numba import cuda

    if cuda.is_available():
        HAS_CUDA = True
        from numba.cuda.random import create_xoroshiro128p_states
except ImportError:
    pass

# Mock objects for CPU fallback
if not HAS_CUDA:

    class MockCP:
        int32 = np.int32
        int8 = np.int8
        float32 = np.float32
        bool_ = np.bool_

        def full(self, shape, val, dtype=None):
            return np.full(shape, val, dtype=dtype)

        def zeros(self, shape, dtype=None):
            return np.zeros(shape, dtype=dtype)

        def ones(self, shape, dtype=None):
            return np.ones(shape, dtype=dtype)

        def asnumpy(self, arr):
            return np.array(arr)

        def array(self, arr, dtype=None):
            return np.array(arr, dtype=dtype)

        def asarray(self, arr, dtype=None):
            return np.asarray(arr, dtype=dtype)

        def arange(self, n, dtype=None):
            return np.arange(n, dtype=dtype)

        def get_default_memory_pool(self):
            class MockPool:
                def used_bytes(self):
                    return 0

            return MockPool()

    cp = MockCP()

    class MockCudaMod:
        def to_device(self, arr):
            return arr

        def device_array(self, shape, dtype=None):
            return np.zeros(shape, dtype=dtype)

        def synchronize(self):
            pass

        def jit(self, *args, **kwargs):
            return lambda x: x

        def grid(self, x):
            return 0

    cuda = MockCudaMod()

    def create_xoroshiro128p_states(n, seed):
        return None


class VectorEnvGPU:
    """
    GPU-Resident Vectorized Game Environment.

    All state arrays are CuPy arrays in GPU VRAM.
    Observations and actions are passed as GPU tensors with zero-copy.

    Args:
        num_envs: Number of parallel environments
        opp_mode: Opponent mode (0=Heuristic, 1=Random)
        force_start_order: -1=Random, 0=P1, 1=P2
    """

    def __init__(self, num_envs: int = 4096, opp_mode: int = 0, force_start_order: int = -1, seed: int = 42):
        self.num_envs = num_envs
        self.opp_mode = opp_mode  # 0=Heuristic, 1=Random, 2=Solitaire
        self.force_start_order = force_start_order
        self.seed = seed

        print(f" [VectorEnvGPU] Initializing {num_envs} environments. CUDA: {HAS_CUDA}")

        # =========================================================
        # AGENT STATE (GPU-Resident)
        # =========================================================
        self.batch_stage = cp.full((num_envs, 3), -1, dtype=cp.int32)
        self.batch_energy_vec = cp.zeros((num_envs, 3, 32), dtype=cp.int32)
        self.batch_energy_count = cp.zeros((num_envs, 3), dtype=cp.int32)
        self.batch_continuous_vec = cp.zeros((num_envs, 32, 10), dtype=cp.int32)
        self.batch_continuous_ptr = cp.zeros(num_envs, dtype=cp.int32)
        self.batch_tapped = cp.zeros((num_envs, 16), dtype=cp.int32)
        self.batch_live = cp.zeros((num_envs, 50), dtype=cp.int32)
        self.batch_opp_tapped = cp.zeros((num_envs, 16), dtype=cp.int32)
        self.batch_scores = cp.zeros(num_envs, dtype=cp.int32)

        self.batch_flat_ctx = cp.zeros((num_envs, 64), dtype=cp.int32)
        self.batch_global_ctx = cp.zeros((num_envs, 128), dtype=cp.int32)

        self.batch_hand = cp.zeros((num_envs, 60), dtype=cp.int32)
        self.batch_deck = cp.zeros((num_envs, 60), dtype=cp.int32)
        self.batch_trash = cp.zeros((num_envs, 60), dtype=cp.int32)
        self.batch_opp_history = cp.zeros((num_envs, 6), dtype=cp.int32)

        # =========================================================
        # OPPONENT STATE (GPU-Resident)
        # =========================================================
        self.opp_stage = cp.full((num_envs, 3), -1, dtype=cp.int32)
        self.opp_energy_vec = cp.zeros((num_envs, 3, 32), dtype=cp.int32)
        self.opp_energy_count = cp.zeros((num_envs, 3), dtype=cp.int32)
        self.opp_tapped = cp.zeros((num_envs, 16), dtype=cp.int8)
        self.opp_live = cp.zeros((num_envs, 50), dtype=cp.int32)
        self.opp_scores = cp.zeros(num_envs, dtype=cp.int32)
        self.opp_global_ctx = cp.zeros((num_envs, 128), dtype=cp.int32)
        self.opp_hand = cp.zeros((num_envs, 60), dtype=cp.int32)
        self.opp_deck = cp.zeros((num_envs, 60), dtype=cp.int32)
        self.opp_trash = cp.zeros((num_envs, 60), dtype=cp.int32)

        # =========================================================
        # TRACKING STATE
        # =========================================================
        self.prev_scores = cp.zeros(num_envs, dtype=cp.int32)
        self.prev_opp_scores = cp.zeros(num_envs, dtype=cp.int32)
        self.prev_phases = cp.zeros(num_envs, dtype=cp.int32)
        self.episode_returns = cp.zeros(num_envs, dtype=cp.float32)
        self.episode_lengths = cp.zeros(num_envs, dtype=cp.int32)

        # =========================================================
        # OBSERVATION MODE
        # =========================================================
        self.obs_mode = os.getenv("OBS_MODE", "STANDARD")
        if self.obs_mode == "COMPRESSED":
            self.obs_dim = 512
        elif self.obs_mode == "IMAX":
            self.obs_dim = 8192
        elif self.obs_mode == "ATTENTION":
            self.obs_dim = 2240
        else:
            self.obs_dim = 2304
        print(f" [VectorEnvGPU] Observation Mode: {self.obs_mode} ({self.obs_dim}-dim)")

        self.batch_obs = cp.zeros((num_envs, self.obs_dim), dtype=cp.float32)
        self.terminal_obs_buffer = cp.zeros((num_envs, self.obs_dim), dtype=cp.float32)

        # Rewards and Dones
        self.rewards = cp.zeros(num_envs, dtype=cp.float32)
        self.dones = cp.zeros(num_envs, dtype=cp.bool_)
        self.term_scores_agent = cp.zeros(num_envs, dtype=cp.int32)
        self.term_scores_opp = cp.zeros(num_envs, dtype=cp.int32)

        # =========================================================
        # GAME CONFIG
        # =========================================================
        self.scenario_reward_scale = float(os.getenv("SCENARIO_REWARD_SCALE", "1.0"))
        if os.getenv("USE_SCENARIOS", "0") == "1" and self.scenario_reward_scale != 1.0:
            print(f" [VectorEnvGPU] Scenario Reward Scale: {self.scenario_reward_scale}")

        self.game_config = cp.zeros(10, dtype=cp.float32)
        self.game_config[0] = float(os.getenv("GAME_TURN_LIMIT", "100"))
        self.game_config[1] = float(os.getenv("GAME_STEP_LIMIT", "1000"))
        self.game_config[2] = float(os.getenv("GAME_REWARD_WIN", "100.0"))
        self.game_config[3] = float(os.getenv("GAME_REWARD_LOSE", "-100.0"))
        self.game_config[4] = float(os.getenv("GAME_REWARD_SCORE_SCALE", "50.0"))
        self.game_config[5] = float(os.getenv("GAME_REWARD_TURN_PENALTY", "-0.05"))

        # =========================================================
        # GPU RNG
        # =========================================================
        if HAS_CUDA:
            self.rng_states = create_xoroshiro128p_states(num_envs, seed=seed)
        else:
            self.rng_states = None

        # =========================================================
        # KERNEL CONFIGURATION
        # =========================================================
        self.threads_per_block = 128
        self.blocks_per_grid = (num_envs + self.threads_per_block - 1) // self.threads_per_block

        # =========================================================
        # LOAD DATA
        # =========================================================
        self._load_bytecode()
        self._load_card_stats()
        self._load_deck_pool()

        # Memory stats
        if HAS_CUDA:
            mempool = cp.get_default_memory_pool()
            used_mb = mempool.used_bytes() / 1024 / 1024
            print(f" [VectorEnvGPU] GPU VRAM used: {used_mb:.2f} MB")

    def _load_bytecode(self):
        """Load compiled bytecode to GPU."""
        host_map = np.zeros((100, 128, 4), dtype=np.int32)
        host_idx = np.zeros((2000, 8), dtype=np.int32)

        try:
            with open("data/cards_numba.json", "r") as f:
                raw_map = json.load(f)

            max_cards = 2000
            max_abilities = 8
            max_len = 128

            unique_entries = len(raw_map)
            host_map = np.zeros((unique_entries + 1, max_len, 4), dtype=np.int32)
            host_idx = np.full((max_cards, max_abilities), 0, dtype=np.int32)

            idx_counter = 1
            for key, bc_list in raw_map.items():
                cid, aid = map(int, key.split("_"))
                if cid < max_cards and aid < max_abilities:
                    bc_arr = np.array(bc_list, dtype=np.int32).reshape(-1, 4)
                    length = min(bc_arr.shape[0], max_len)
                    host_map[idx_counter, :length] = bc_arr[:length]
                    host_idx[cid, aid] = idx_counter
                    idx_counter += 1

            print(f" [VectorEnvGPU] Loaded {unique_entries} compiled abilities.")
        except FileNotFoundError:
            print(" [VectorEnvGPU] Warning: cards_numba.json not found.")
        except Exception as e:
            print(f" [VectorEnvGPU] Warning: Failed to load bytecode: {e}")

        self.bytecode_map = cp.asarray(host_map)
        self.bytecode_index = cp.asarray(host_idx)

    def _load_card_stats(self):
        """Load card statistics to GPU."""
        host_stats = np.zeros((2000, 80), dtype=np.int32)

        try:
            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db = json.load(f)

            count = 0
            if "member_db" in db:
                for cid_str, card in db["member_db"].items():
                    cid = int(cid_str)
                    if cid < 2000:
                        host_stats[cid, 0] = card.get("cost", 0)
                        host_stats[cid, 1] = card.get("blades", 0)
                        host_stats[cid, 2] = sum(card.get("hearts", []))
                        host_stats[cid, 10] = 1  # Type: Member

                        # Hearts breakdown
                        h_arr = card.get("hearts", [])
                        for r_idx in range(min(len(h_arr), 7)):
                            host_stats[cid, 12 + r_idx] = h_arr[r_idx]

                        # Traits
                        mask = 0
                        for g in card.get("groups", []):
                            try:
                                mask |= 1 << (int(g) % 20)
                            except:
                                pass
                        host_stats[cid, 11] = mask
                        count += 1

            if "live_db" in db:
                for cid_str, card in db["live_db"].items():
                    cid = int(cid_str)
                    if cid < 2000:
                        host_stats[cid, 10] = 2  # Type: Live
                        reqs = card.get("required_hearts", [])
                        for r_idx in range(min(len(reqs), 7)):
                            host_stats[cid, 12 + r_idx] = reqs[r_idx]
                        host_stats[cid, 38] = card.get("score", 0)
                        count += 1

            print(f" [VectorEnvGPU] Loaded stats for {count} cards.")
        except Exception as e:
            print(f" [VectorEnvGPU] Warning: Failed to load card stats: {e}")

        self.card_stats = cp.asarray(host_stats)

    def _load_deck_pool(self):
        """Load verified card pool for deck generation."""
        ability_member_ids = []
        ability_live_ids = []

        try:
            with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
                verified_data = json.load(f)

            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db_data = json.load(f)

            member_no_map = {}
            live_no_map = {}
            for cid, cdata in db_data.get("member_db", {}).items():
                member_no_map[cdata["card_no"]] = int(cid)
            for cid, cdata in db_data.get("live_db", {}).items():
                live_no_map[cdata["card_no"]] = int(cid)

            if isinstance(verified_data, list):
                for v_no in verified_data:
                    if v_no in member_no_map:
                        ability_member_ids.append(member_no_map[v_no])
                    elif v_no in live_no_map:
                        ability_live_ids.append(live_no_map[v_no])
            else:
                source_members = verified_data.get("verified_abilities", []) + verified_data.get("members", [])
                for v_no in source_members:
                    if v_no in member_no_map:
                        ability_member_ids.append(member_no_map[v_no])

                source_lives = verified_data.get("verified_lives", []) + verified_data.get("lives", [])
                for v_no in source_lives:
                    if v_no in live_no_map:
                        ability_live_ids.append(live_no_map[v_no])

                if not ability_member_ids:
                    for v_no in verified_data.get("vanilla_members", []):
                        if v_no in member_no_map:
                            ability_member_ids.append(member_no_map[v_no])
                if not ability_live_ids:
                    for v_no in verified_data.get("vanilla_lives", []):
                        if v_no in live_no_map:
                            ability_live_ids.append(live_no_map[v_no])

            if not ability_member_ids:
                ability_member_ids = [1]
            if not ability_live_ids:
                ability_live_ids = [999]

            print(f" [VectorEnvGPU] Deck Pool: {len(ability_member_ids)} members, {len(ability_live_ids)} lives")
        except Exception as e:
            print(f" [VectorEnvGPU] Deck Load Error: {e}")
            ability_member_ids = [1]
            ability_live_ids = [999]

        self.ability_member_ids = cp.array(ability_member_ids, dtype=cp.int32)
        self.ability_live_ids = cp.array(ability_live_ids, dtype=cp.int32)

    # =========================================================
    # PYTORCH INTERFACE
    # =========================================================

    def get_observations_tensor(self):
        """Return observations as PyTorch CUDA tensor (zero-copy)."""
        import torch

        return torch.as_tensor(self.batch_obs, device="cuda")

    def get_action_masks_tensor(self):
        """Return action masks as PyTorch CUDA tensor."""
        import torch

        masks = self.get_action_masks()
        return torch.as_tensor(masks, device="cuda")

    def get_rewards_tensor(self):
        """Return rewards as PyTorch CUDA tensor."""
        import torch

        return torch.as_tensor(self.rewards, device="cuda")

    def get_dones_tensor(self):
        """Return dones as PyTorch CUDA tensor."""
        import torch

        return torch.as_tensor(self.dones, device="cuda")

    # =========================================================
    # ENVIRONMENT INTERFACE
    # =========================================================

    def reset(self, indices=None):
        """Reset environments."""
        if not HAS_CUDA:
            # CPU fallback
            self.batch_stage.fill(-1)
            self.batch_scores.fill(0)
            self.batch_global_ctx.fill(0)
            self.batch_hand.fill(0)
            self.batch_deck.fill(0)
            return self.batch_obs

        from ai.cuda_kernels import encode_observations_attention_kernel, encode_observations_kernel, reset_kernel

        if indices is None:
            indices_gpu = cp.arange(self.num_envs, dtype=cp.int32)
        else:
            indices_gpu = cp.array(indices, dtype=cp.int32)

        blocks = (len(indices_gpu) + self.threads_per_block - 1) // self.threads_per_block

        reset_kernel[blocks, self.threads_per_block](
            indices_gpu,
            self.batch_stage,
            self.batch_energy_vec,
            self.batch_energy_count,
            self.batch_continuous_vec,
            self.batch_continuous_ptr,
            self.batch_tapped,
            self.batch_live,
            self.batch_scores,
            self.batch_flat_ctx,
            self.batch_global_ctx,
            self.batch_hand,
            self.batch_deck,
            self.batch_trash,
            self.batch_opp_history,
            self.opp_stage,
            self.opp_energy_vec,
            self.opp_energy_count,
            self.opp_tapped,
            self.opp_live,
            self.opp_scores,
            self.opp_global_ctx,
            self.opp_hand,
            self.opp_deck,
            self.opp_trash,
            self.ability_member_ids,
            self.ability_live_ids,
            self.rng_states,
            self.force_start_order,
            self.batch_obs,
            self.card_stats,
        )

        # Encode initial observations
        if self.obs_mode == "ATTENTION":
            encode_observations_attention_kernel[self.blocks_per_grid, self.threads_per_block](
                self.num_envs,
                self.batch_hand,
                self.batch_stage,
                self.batch_energy_count,
                self.batch_tapped,
                self.batch_scores,
                self.opp_scores,
                self.opp_stage,
                self.opp_tapped,
                self.card_stats,
                self.batch_global_ctx,
                self.batch_live,
                self.batch_opp_history,
                self.opp_global_ctx,
                1,
                self.batch_obs,
            )
        else:
            encode_observations_kernel[self.blocks_per_grid, self.threads_per_block](
                self.num_envs,
                self.batch_hand,
                self.batch_stage,
                self.batch_energy_count,
                self.batch_tapped,
                self.batch_scores,
                self.opp_scores,
                self.opp_stage,
                self.opp_tapped,
                self.card_stats,
                self.batch_global_ctx,
                self.batch_live,
                1,
                self.batch_obs,
            )

        # Reset tracking
        if indices is None:
            self.prev_scores.fill(0)
            self.prev_opp_scores.fill(0)
            self.episode_returns.fill(0)
            self.episode_lengths.fill(0)
        else:
            self.prev_scores[indices_gpu] = 0
            self.prev_opp_scores[indices_gpu] = 0
            self.episode_returns[indices_gpu] = 0
            self.episode_lengths[indices_gpu] = 0

        return self.batch_obs

    def step(self, actions):
        """
        Step all environments.

        Args:
            actions: CuPy array or PyTorch tensor of actions

        Returns:
            obs, rewards, dones, infos
        """
        if not HAS_CUDA:
            # Fallback
            return self.batch_obs, self.rewards, self.dones, [{}] * self.num_envs

        import torch
        from ai.cuda_kernels import (
            encode_observations_attention_kernel,
            encode_observations_kernel,
            reset_kernel,
            step_kernel,
        )

        # Convert to CuPy if needed
        if isinstance(actions, torch.Tensor):
            actions_gpu = cp.asarray(actions.cpu().numpy(), dtype=cp.int32)
        elif isinstance(actions, np.ndarray):
            actions_gpu = cp.asarray(actions, dtype=cp.int32)
        else:
            actions_gpu = actions

        # 1. Step kernel
        step_kernel[self.blocks_per_grid, self.threads_per_block](
            self.num_envs,
            actions_gpu,
            self.batch_hand,
            self.batch_deck,
            self.batch_stage,
            self.batch_energy_vec,
            self.batch_energy_count,
            self.batch_continuous_vec,
            self.batch_continuous_ptr,
            self.batch_tapped,
            self.batch_live,
            self.batch_scores,
            self.batch_flat_ctx,
            self.batch_global_ctx,
            self.opp_hand,
            self.opp_deck,
            self.opp_stage,
            self.opp_energy_vec,
            self.opp_energy_count,
            self.opp_tapped,
            self.opp_live,
            self.opp_scores,
            self.opp_global_ctx,
            self.card_stats,
            self.bytecode_map,
            self.bytecode_index,
            self.batch_obs,
            self.rewards,
            self.dones,
            self.prev_scores,
            self.prev_opp_scores,
            self.prev_phases,
            self.terminal_obs_buffer,
            self.batch_trash,
            self.opp_trash,
            self.batch_opp_history,
            self.term_scores_agent,
            self.term_scores_opp,
            self.ability_member_ids,
            self.ability_live_ids,
            self.rng_states,
            self.game_config,
            self.opp_mode,
            self.force_start_order,
        )

        # Apply Scenario Reward Scaling
        if self.scenario_reward_scale != 1.0 and os.getenv("USE_SCENARIOS", "0") == "1":
            self.rewards *= self.scenario_reward_scale

        # 2. Update Episodic Returns/Lengths (Vectorized GPU)
        self.episode_returns += self.rewards
        self.episode_lengths += 1

        # 3. Handle Auto-Reset (High Performance)
        dones_cpu = cp.asnumpy(self.dones)

        # Pre-allocate infos list (reused or created)
        infos = [{} for _ in range(self.num_envs)]

        if np.any(dones_cpu):
            done_indices = np.where(dones_cpu)[0]
            done_indices_gpu = cp.array(done_indices, dtype=cp.int32)

            # A. Capture Terminal Observations (from UNRESET state)
            # Efficient Device-to-Device copy
            # NOTE: step_kernel leaves env in finished state, so batch_obs has terminal state.
            # We must encode it?
            # Actually, step_kernel calls encode at end? No, step_kernel does NOT encode obs in my implementation.
            # I removed the Python-side encode calls from previous impl?
            # Wait, step_kernel logic in my head vs file.
            # In ai/cuda_kernels.py, step_kernel does NOT call encode.
            # So batch_obs is STALE (from previous step)!
            # We MUST encode the terminal state first.

            # Encode CURRENT state (Terminal) for ALL envs? Or just done?
            # Usually we encode all envs at end of step.
            # BUT we need to reset done envs and encode AGAIN.

            # OPTIMIZATION:
            # 1. Encode ALL envs (Next state for running, Terminal for done).
            turn_num = 1  # Dummy, kernels use ctx
            if self.obs_mode == "ATTENTION":
                encode_observations_attention_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    self.batch_opp_history,
                    self.opp_global_ctx,
                    turn_num,
                    self.batch_obs,
                )
            else:
                encode_observations_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    turn_num,
                    self.batch_obs,
                )

            # 2. For Done Envs: Copy encoded terminal state to buffer
            # We can use fancy indexing copy on GPU
            self.terminal_obs_buffer[done_indices_gpu] = self.batch_obs[done_indices_gpu]

            # 3. Fetch Terminal Info Metrics (Bulk D2H)
            final_returns = cp.asnumpy(self.episode_returns[done_indices_gpu])
            final_lengths = cp.asnumpy(self.episode_lengths[done_indices_gpu])
            term_obs_cpu = cp.asnumpy(self.terminal_obs_buffer[done_indices_gpu])
            term_scores_ag = cp.asnumpy(self.term_scores_agent[done_indices_gpu])
            term_scores_op = cp.asnumpy(self.term_scores_opp[done_indices_gpu])

            # 4. Populate Infos (CPU Loop over SMALL subset)
            for k, idx in enumerate(done_indices):
                infos[idx] = {
                    "terminal_observation": term_obs_cpu[k],
                    "episode": {"r": float(final_returns[k]), "l": int(final_lengths[k])},
                    "terminal_score_agent": int(term_scores_ag[k]),
                    "terminal_score_opp": int(term_scores_op[k]),
                }

            # 5. Reset Done Envs
            # Reset accumulators
            self.episode_returns[done_indices_gpu] = 0
            self.episode_lengths[done_indices_gpu] = 0

            # Launch Reset Kernel
            blocks_reset = (len(done_indices) + self.threads_per_block - 1) // self.threads_per_block
            reset_kernel[blocks_reset, self.threads_per_block](
                done_indices_gpu,
                self.batch_stage,
                self.batch_energy_vec,
                self.batch_energy_count,
                self.batch_continuous_vec,
                self.batch_continuous_ptr,
                self.batch_tapped,
                self.batch_live,
                self.batch_scores,
                self.batch_flat_ctx,
                self.batch_global_ctx,
                self.batch_hand,
                self.batch_deck,
                self.batch_trash,
                self.batch_opp_history,
                self.opp_stage,
                self.opp_energy_vec,
                self.opp_energy_count,
                self.opp_tapped,
                self.opp_live,
                self.opp_scores,
                self.opp_global_ctx,
                self.opp_hand,
                self.opp_deck,
                self.opp_trash,
                self.ability_member_ids,
                self.ability_live_ids,
                self.rng_states,
                self.force_start_order,
                self.batch_obs,
                self.card_stats,
            )

            # 6. Re-Encode Reset Envs (to get initial state)
            # We assume reset_kernel updates state but NOT obs.
            # We need to re-run encode kernel ONLY for done indices?
            # Or run global encode again? Global is waste.
            # We need an encode kernel that takes indices.
            # The current kernel takes `num_envs` and assumes `0..N`.
            # We can reuse the global kernel if we are clever or modify it.
            # Modifying kernel to accept indices is best.
            # However, for now, to save complexity, we can re-run global encode.
            # It's redundant for non-done envs but correct.
            # Better: Reset modifies batch_obs directly? No, reset_kernel doesn't encode.

            # Let's re-run global encode. It's fast (GPU) compared to CPU loop.
            if self.obs_mode == "ATTENTION":
                encode_observations_attention_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    self.batch_opp_history,
                    self.opp_global_ctx,
                    turn_num,
                    self.batch_obs,
                )
            else:
                encode_observations_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    turn_num,
                    self.batch_obs,
                )

        else:
            # No resets needed. Just encode once to get next states.
            # Encode observations
            turn_num = 1
            if self.obs_mode == "ATTENTION":
                encode_observations_attention_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    self.batch_opp_history,
                    self.opp_global_ctx,
                    turn_num,
                    self.batch_obs,
                )
            else:
                encode_observations_kernel[self.blocks_per_grid, self.threads_per_block](
                    self.num_envs,
                    self.batch_hand,
                    self.batch_stage,
                    self.batch_energy_count,
                    self.batch_tapped,
                    self.batch_scores,
                    self.opp_scores,
                    self.opp_stage,
                    self.opp_tapped,
                    self.card_stats,
                    self.batch_global_ctx,
                    self.batch_live,
                    turn_num,
                    self.batch_obs,
                )

        return self.batch_obs, self.rewards, self.dones, infos

    def get_observations(self):
        """Return observation buffer (CuPy array)."""
        return self.batch_obs

    def get_action_masks(self):
        """Compute and return action masks (CuPy array)."""
        if not HAS_CUDA:
            return cp.ones((self.num_envs, 2000), dtype=cp.bool_)

        from ai.cuda_kernels import compute_action_masks_kernel

        masks = cp.zeros((self.num_envs, 2000), dtype=cp.bool_)

        compute_action_masks_kernel[self.blocks_per_grid, self.threads_per_block](
            self.num_envs,
            self.batch_hand,
            self.batch_stage,
            self.batch_tapped,
            self.batch_global_ctx,
            self.batch_live,
            self.card_stats,
            masks,
        )

        return masks


# ============================================================================
# BENCHMARK
# ============================================================================


def benchmark_gpu_env(num_envs=4096, steps=1000):
    """Benchmark GPU environment throughput."""
    print("\n=== GPU Environment Benchmark ===")
    print(f"Environments: {num_envs}")
    print(f"Steps: {steps}")

    env = VectorEnvGPU(num_envs=num_envs)
    env.reset()

    # Warmup
    for _ in range(10):
        actions = cp.zeros(num_envs, dtype=cp.int32)
        env.step(actions)

    if HAS_CUDA:
        cuda.synchronize()

    # Benchmark
    start = time.time()
    for _ in range(steps):
        actions = cp.zeros(num_envs, dtype=cp.int32)  # Pass action
        env.step(actions)

    if HAS_CUDA:
        cuda.synchronize()

    elapsed = time.time() - start
    total_steps = num_envs * steps
    sps = total_steps / elapsed

    print("\nResults:")
    print(f"  Total Steps: {total_steps:,}")
    print(f"  Time: {elapsed:.2f}s")
    print(f"  Throughput: {sps:,.0f} steps/sec")

    return sps


if __name__ == "__main__":
    # Quick test
    env = VectorEnvGPU(num_envs=128)
    obs = env.reset()
    print(f"Observation shape: {obs.shape}")

    actions = cp.zeros(128, dtype=cp.int32)
    obs, rewards, dones, infos = env.step(actions)
    print(f"Step completed. Rewards shape: {rewards.shape}")

    # Benchmark
    benchmark_gpu_env(num_envs=1024, steps=100)
