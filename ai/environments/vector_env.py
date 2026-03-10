import os
from typing import List

import numpy as np
from numba import njit, prange

import ai.research.integrated_step_numba as isn
from engine.game.fast_logic import (
    batch_apply_action,
    resolve_bytecode,
)


@njit(cache=True)
def step_vectorized(
    actions: np.ndarray,
    batch_stage: np.ndarray,
    batch_energy_vec: np.ndarray,
    batch_energy_count: np.ndarray,
    batch_continuous_vec: np.ndarray,
    batch_continuous_ptr: np.ndarray,
    batch_tapped: np.ndarray,
    batch_live: np.ndarray,
    batch_opp_tapped: np.ndarray,
    batch_scores: np.ndarray,
    batch_flat_ctx: np.ndarray,
    batch_global_ctx: np.ndarray,
    batch_hand: np.ndarray,
    batch_deck: np.ndarray,
    # New: Bytecode Maps
    bytecode_map: np.ndarray,  # (GlobalOpMapSize, MaxBytecodeLen, 4)
    bytecode_index: np.ndarray,  # (NumCards, NumAbilities) -> Index in map
    card_stats: np.ndarray,
    batch_trash: np.ndarray,  # Added
):
    """
    Step N game environments in parallel using JIT logic and Real Card Data.
    """
    # Score sync now handled internally by batch_apply_action

    batch_apply_action(
        actions,
        0,  # player_id
        batch_stage,
        batch_energy_vec,
        batch_energy_count,
        batch_continuous_vec,
        batch_continuous_ptr,
        batch_tapped,
        batch_scores,
        batch_live,
        batch_opp_tapped,
        batch_flat_ctx,
        batch_global_ctx,
        batch_hand,
        batch_deck,
        batch_trash,  # Added
        bytecode_map,
        bytecode_index,
        card_stats,
    )

    rewards = np.zeros(actions.shape[0], dtype=np.float32)
    dones = np.zeros(actions.shape[0], dtype=np.bool_)
    return rewards, dones


class VectorGameState:
    """
    Manages a batch of independent GameStates for high-throughput training.
    """

    def __init__(self, num_envs: int, opp_mode: int = 0, force_start_order: int = -1):
        self.num_envs = num_envs
        # opp_mode: 0=Heuristic, 1=Random, 2=Solitaire (Pass Only)
        self.opp_mode = opp_mode
        self.force_start_order = force_start_order  # -1=Random, 0=P1, 1=P2
        self.turn = 1

        # Batched state buffers - Player 0 (Agent)
        self.batch_stage = np.full((num_envs, 3), -1, dtype=np.int32)
        self.batch_energy_vec = np.zeros((num_envs, 3, 32), dtype=np.int32)
        self.batch_energy_count = np.zeros((num_envs, 3), dtype=np.int32)
        self.batch_continuous_vec = np.zeros((num_envs, 32, 10), dtype=np.int32)
        self.batch_continuous_ptr = np.zeros(num_envs, dtype=np.int32)
        self.batch_tapped = np.zeros((num_envs, 16), dtype=np.int32)  # Slots 0-2, Energy 3-15
        self.batch_live = np.zeros((num_envs, 50), dtype=np.int32)
        self.batch_opp_tapped = np.zeros((num_envs, 16), dtype=np.int32)
        self.batch_scores = np.zeros(num_envs, dtype=np.int32)

        # Batched state buffers - Opponent State (Player 1)
        self.opp_stage = np.full((num_envs, 3), -1, dtype=np.int32)
        self.opp_energy_vec = np.zeros((num_envs, 3, 32), dtype=np.int32)  # Match Agent Shape
        self.opp_energy_count = np.zeros((num_envs, 3), dtype=np.int32)
        self.opp_tapped = np.zeros((num_envs, 16), dtype=np.int8)
        self.opp_live = np.zeros((num_envs, 50), dtype=np.int32)  # Added Opp Live
        self.opp_scores = np.zeros(num_envs, dtype=np.int32)

        # New State Tracking for Integrated Step
        self.prev_scores = np.zeros(num_envs, dtype=np.int32)
        self.prev_opp_scores = np.zeros(num_envs, dtype=np.int32)
        self.prev_phases = np.zeros(num_envs, dtype=np.int32)
        self.episode_returns = np.zeros(num_envs, dtype=np.float32)
        self.episode_lengths = np.zeros(num_envs, dtype=np.int32)

        # Opponent Finite Deck Buffers
        self.opp_hand = np.zeros((num_envs, 60), dtype=np.int32)
        self.opp_deck = np.zeros((num_envs, 60), dtype=np.int32)

        # Load Numba functions
        import os

        if os.getenv("USE_SCENARIOS", "0") == "1":
            self._load_scenarios()

        # Scenario Reward Scaling
        self.scenario_reward_scale = float(os.getenv("SCENARIO_REWARD_SCALE", "1.0"))
        if os.getenv("USE_SCENARIOS", "0") == "1" and self.scenario_reward_scale != 1.0:
            print(f" [VectorEnv] Scenario Reward Scale: {self.scenario_reward_scale}")

        # New: Opponent History Buffer (Top 20 cards e.g.)
        self.batch_opp_history = np.zeros((num_envs, 50), dtype=np.int32)

        # Pre-allocated context buffers (Extreme speed optimization)
        self.batch_flat_ctx = np.zeros((num_envs, 64), dtype=np.int32)
        self.batch_global_ctx = np.zeros((num_envs, 128), dtype=np.int32)
        self.opp_global_ctx = np.zeros((num_envs, 128), dtype=np.int32)  # Persistent Opponent Context
        self.batch_hand = np.zeros((num_envs, 60), dtype=np.int32)
        self.batch_deck = np.zeros((num_envs, 60), dtype=np.int32)
        self.batch_trash = np.zeros((num_envs, 60), dtype=np.int32)  # Added Trash
        self.opp_trash = np.zeros((num_envs, 60), dtype=np.int32)  # Added Opp Trash
        # Observation Buffer
        # 20480 floats per env to handle Full Hand (60 cards) + Opponent + Stats
        # Increased for "Real Vision" upgrade
        # Observation Buffer
        # Mode Selection
        import os

        self.obs_mode = os.getenv("OBS_MODE", "STANDARD")
        if self.obs_mode == "COMPRESSED":
            self.obs_dim = 512
            self.action_space_dim = 2000
            print(" [VectorEnv] Observation Mode: COMPRESSED (512-dim)")
        elif self.obs_mode == "IMAX":
            self.obs_dim = 8192
            self.action_space_dim = 2000
            print(" [VectorEnv] Observation Mode: IMAX (8192-dim)")
        elif self.obs_mode == "ATTENTION":
            self.obs_dim = 2240
            self.action_space_dim = 512
            print(" [VectorEnv] Observation Mode: ATTENTION (2240-dim)")
        else:
            self.obs_dim = 2304
            self.action_space_dim = 2000
            print(" [VectorEnv] Observation Mode: STANDARD (2304-dim)")

        self.obs_buffer = np.zeros((self.num_envs, self.obs_dim), dtype=np.float32)
        # Terminal Obs Buffer for Auto-Reset
        self.terminal_obs_buffer = np.zeros((self.num_envs, self.obs_dim), dtype=np.float32)

        # Global Turn Counter (Pointer for Numba)
        self.turn_number_ptr = np.zeros(1, dtype=np.int32)
        self.turn_number_ptr[0] = 1

        # Game Config (Turn Limits & Rewards)
        # 0: Turn Limit, 1: Step Limit, 2: Win Reward, 3: Lose Reward, 4: Score Scale, 5: Turn Penalty
        self.game_config = np.zeros(10, dtype=np.float32)
        self.game_config[0] = float(os.getenv("GAME_TURN_LIMIT", "100"))
        self.game_config[1] = float(os.getenv("GAME_STEP_LIMIT", "1000"))
        self.game_config[2] = float(os.getenv("GAME_REWARD_WIN", "100.0"))
        self.game_config[3] = float(os.getenv("GAME_REWARD_LOSE", "-100.0"))
        self.game_config[4] = float(os.getenv("GAME_REWARD_SCORE_SCALE", "50.0"))
        self.game_config[5] = float(os.getenv("GAME_REWARD_TURN_PENALTY", "-0.05"))
        print(
            f" [VectorEnv] Game Config: Turns={int(self.game_config[0])}, Steps={int(self.game_config[1])}, Win={self.game_config[2]}, Lose={self.game_config[3]}"
        )

        # Load Bytecode Map
        self._load_bytecode()

        # Check for Fixed Deck Override
        fixed_deck_path = os.getenv("USE_FIXED_DECK")
        if fixed_deck_path:
            self._load_fixed_deck_pool(fixed_deck_path)
        else:
            self._load_verified_deck_pool()

    def _load_bytecode(self):
        import json
        import re

        try:
            # Unified Source: cards_compiled.json
            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db = json.load(f)

            self.max_cards = 2000
            self.max_abilities = 8
            self.max_len = 128

            # 1. Count unique abilities for bytecode_map
            # We'll build a temp list of bytecodes to populate the map
            bytecode_list = []

            self.bytecode_index = np.full((self.max_cards, self.max_abilities), 0, dtype=np.int32)
            self.card_stats = np.zeros((self.max_cards, 80), dtype=np.int32)

            name_to_id = {}
            all_cards = {**db.get("member_db", {}), **db.get("live_db", {})}

            # First pass: Character Name mapping
            for cid_str, card in db.get("member_db", {}).items():
                name = card.get("name", "")
                if name:
                    name_to_id[name] = int(cid_str)

            # Second pass: Process Stats and Bytecode
            processed_count = 0
            for cid_str, card in all_cards.items():
                cid = int(cid_str)
                if cid >= self.max_cards:
                    continue

                # --- STATS ---
                is_member = cid_str in db.get("member_db", {})
                self.card_stats[cid, 10] = 1 if is_member else 2  # Type
                self.card_stats[cid, 0] = card.get("cost", 0)
                self.card_stats[cid, 1] = card.get("blades", 0)

                h_arr = card.get("hearts", card.get("required_hearts", []))
                self.card_stats[cid, 2] = sum(h_arr)
                for r_idx in range(min(len(h_arr), 7)):
                    self.card_stats[cid, 12 + r_idx] = h_arr[r_idx]

                bh = card.get("blade_hearts", [])
                for b_idx in range(min(len(bh), 7)):
                    self.card_stats[cid, 40 + b_idx] = bh[b_idx]

                self.card_stats[cid, 4] = card.get("volume_icons", 0)
                self.card_stats[cid, 5] = card.get("draw_icons", 0)
                self.card_stats[cid, 38] = card.get("score", 0)

                # Character ID link
                name = card.get("name", "")
                if name in name_to_id:
                    self.card_stats[cid, 19] = name_to_id[name]

                # Traits mask
                mask = 0
                for g in card.get("groups", []):
                    mask |= 1 << (int(g) % 20)
                for u in card.get("units", []):
                    mask |= 1 << ((int(u) % 20) + 5)
                self.card_stats[cid, 11] = mask

                # --- BYTECODE ---
                ab_list = card.get("abilities", [])
                for ab_idx, ab in enumerate(ab_list):
                    if ab_idx >= self.max_abilities:
                        break

                    # Pack fixed geography stats
                    base_idx = 20 + (ab_idx * 12) if ab_idx > 0 else 20
                    # Note: Ability 1 (idx 0) has extra logic for Options in some builds,
                    # but here we follow the standard logic.
                    self.card_stats[cid, base_idx] = ab.get("trigger", 0)

                    bc = ab.get("bytecode", [])
                    if bc:
                        bc_np = np.array(bc, dtype=np.int32)
                        if bc_np.size % 4 != 0:
                            pad_size = 4 - (bc_np.size % 4)
                            bc_np = np.concatenate((bc_np, np.zeros(pad_size, dtype=np.int32)))
                        # Register in bytecode_map
                        bc_idx = len(bytecode_list) + 1  # 1-based
                        bytecode_list.append(bc_np)
                        self.bytecode_index[cid, ab_idx] = bc_idx

                processed_count += 1

            # Populate bytecode_map
            self.bytecode_map = np.zeros((len(bytecode_list) + 32, self.max_len, 4), dtype=np.int32)
            for i, bc_arr in enumerate(bytecode_list):
                bc_reshaped = bc_arr.reshape(-1, 4)
                length = min(bc_reshaped.shape[0], self.max_len)
                self.bytecode_map[i + 1, :length] = bc_reshaped[:length]

            print(
                f" [VectorEnv] Loaded {processed_count} cards and {len(bytecode_list)} abilities from cards_compiled.json."
            )

            # --- BATON PASS PATCHING ---
            baton_pattern = re.compile(r"「(.+?)」からバトンタッチして")
            patched_count = 0
            idx_counter = len(bytecode_list) + 1

            for cid_str, card in all_cards.items():
                cid = int(cid_str)
                if cid >= self.max_cards:
                    continue

                for ab_idx, ab in enumerate(card.get("abilities", [])):
                    raw_text = ab.get("raw_text", "")
                    match = baton_pattern.search(raw_text)
                    if match:
                        target_name = match.group(1)
                        target_cid = name_to_id.get(target_name, -1)
                        if target_cid != -1:
                            original_bc = ab.get("bytecode", [])
                            if original_bc:
                                # Prepend C_BATON (231) + TargetID
                                new_bc = [231, target_cid, 0, 0] + original_bc
                                if idx_counter < self.bytecode_map.shape[0]:
                                    bc_np = np.array(new_bc, dtype=np.int32)
                                    if bc_np.size % 4 != 0:
                                        pad_size = 4 - (bc_np.size % 4)
                                        bc_np = np.concatenate((bc_np, np.zeros(pad_size, dtype=np.int32)))

                                    bc_reshaped = bc_np.reshape(-1, 4)
                                    length = min(bc_reshaped.shape[0], self.max_len)
                                    self.bytecode_map[idx_counter, :length] = bc_reshaped[:length]
                                    self.bytecode_index[cid, ab_idx] = idx_counter
                                    idx_counter += 1
                                    patched_count += 1

            if patched_count > 0:
                print(f" [VectorEnv] Applied {patched_count} runtime Baton Pass patches.")

        except Exception as e:
            print(f" [VectorEnv] ERROR loading bytecode/stats: {e}")
            import traceback

            traceback.print_exc()
            self.bytecode_map = np.zeros((1, 64, 4), dtype=np.int32)
            self.bytecode_index = np.zeros((self.max_cards, self.max_abilities), dtype=np.int32)
            self.card_stats = np.zeros((self.max_cards, 80), dtype=np.int32)

    def _load_verified_deck_pool(self):
        import json

        try:
            # Load Verified List
            with open("data/verified_card_pool.json", "r", encoding="utf-8") as f:
                verified_data = json.load(f)

            # Load DB to map CardNo -> CardID
            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db_data = json.load(f)

            self.ability_member_ids = []
            self.ability_live_ids = []
            self.vanilla_member_ids = []
            self.vanilla_live_ids = []

            # Map numbers to IDs and types
            member_no_map = {}
            live_no_map = {}
            for cid, cdata in db_data.get("member_db", {}).items():
                member_no_map[cdata["card_no"]] = int(cid)
            for cid, cdata in db_data.get("live_db", {}).items():
                live_no_map[cdata["card_no"]] = int(cid)

            # Check for list compatibility mode
            if isinstance(verified_data, list):
                print(" [VectorEnv] Loading Verified Pool from List (Compatibility Mode)")
                for v_no in verified_data:
                    if v_no in member_no_map:
                        self.ability_member_ids.append(member_no_map[v_no])
                    elif v_no in live_no_map:
                        self.ability_live_ids.append(live_no_map[v_no])
            else:
                # 1. Primary Pool: Abilities (Categorized)
                # Support both old keys (verified_abilities) and new keys (members)
                source_members = verified_data.get("verified_abilities", []) + verified_data.get("members", [])
                for v_no in source_members:
                    if v_no in member_no_map:
                        self.ability_member_ids.append(member_no_map[v_no])

                source_lives = verified_data.get("verified_lives", []) + verified_data.get("lives", [])
                for v_no in source_lives:
                    if v_no in live_no_map:
                        self.ability_live_ids.append(live_no_map[v_no])

                # 2. Secondary Pool: Vanilla
                for v_no in verified_data.get("vanilla_members", []):
                    if v_no in member_no_map:
                        self.vanilla_member_ids.append(member_no_map[v_no])
                for v_no in verified_data.get("vanilla_lives", []):
                    if v_no in live_no_map:
                        self.vanilla_live_ids.append(live_no_map[v_no])

            # Fallback/Warnings
            if not self.ability_member_ids:
                if self.vanilla_member_ids:
                    print(" [VectorEnv] Warning: No ability members. using vanilla members.")
                    self.ability_member_ids = self.vanilla_member_ids
                else:
                    print(" [VectorEnv] Warning: No members found. Using ID 1.")
                    self.ability_member_ids = [1]

            if not self.ability_live_ids:
                if self.vanilla_live_ids:
                    print(" [VectorEnv] Warning: No ability lives. Using vanilla lives.")
                    self.ability_live_ids = self.vanilla_live_ids
                else:
                    print(" [VectorEnv] Warning: No lives found. Using ID 999 (Dummy).")
                    self.ability_live_ids = [999]

            print(
                f" [VectorEnv] Pools: {len(self.ability_member_ids)} Ability Members, {len(self.ability_live_ids)} Ability Lives."
            )
            print(
                f" [VectorEnv] Fallbacks: {len(self.vanilla_member_ids)} Vanilla Members, {len(self.vanilla_live_ids)} Vanilla Lives."
            )

            self.ability_member_ids = np.array(self.ability_member_ids, dtype=np.int32)
            self.ability_live_ids = np.array(self.ability_live_ids, dtype=np.int32)
            self.vanilla_member_ids = np.array(self.vanilla_member_ids, dtype=np.int32)
            self.vanilla_live_ids = np.array(self.vanilla_live_ids, dtype=np.int32)

        except Exception as e:
            print(f" [VectorEnv] Deck Load Error: {e}")
            self.ability_member_ids = np.array([1], dtype=np.int32)
            self.ability_live_ids = np.array([999], dtype=np.int32)
            self.vanilla_member_ids = np.array([], dtype=np.int32)
            self.vanilla_live_ids = np.array([], dtype=np.int32)

    def _load_fixed_deck_pool(self, deck_path: str):
        import json
        import re

        print(f" [VectorEnv] Loading FIXED DECK from: {deck_path}")
        try:
            # 1. Load DB to map CardNo -> CardID
            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db_data = json.load(f)

            member_no_map = {}
            live_no_map = {}
            for cid, cdata in db_data.get("member_db", {}).items():
                member_no_map[cdata["card_no"]] = int(cid)
            for cid, cdata in db_data.get("live_db", {}).items():
                live_no_map[cdata["card_no"]] = int(cid)

            # 2. Parse Markdown
            with open(deck_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            members = []
            lives = []

            for line in lines:
                # Look for "4x [PL!-...]" - flexible for markdown bolding like **4x**
                match = re.search(r"(\d+)x.*?\[(PL!-[^\]]+)\]", line)
                if match:
                    count = int(match.group(1))
                    card_no = match.group(2)
                    if card_no in member_no_map:
                        for _ in range(count):
                            members.append(member_no_map[card_no])
                    elif card_no in live_no_map:
                        for _ in range(count):
                            lives.append(live_no_map[card_no])

            # 3. Finalize
            if len(members) != 48:
                print(f" [VectorEnv] Warning: Fixed deck members count is {len(members)}, expected 48.")
            if len(lives) != 12:
                print(f" [VectorEnv] Warning: Fixed deck lives count is {len(lives)}, expected 12.")

            self.ability_member_ids = np.array(members, dtype=np.int32)
            self.ability_live_ids = np.array(lives, dtype=np.int32)
            self.vanilla_member_ids = np.array([], dtype=np.int32)
            self.vanilla_live_ids = np.array([], dtype=np.int32)

            print(
                f" [VectorEnv] Fixed Deck Loaded: {len(self.ability_member_ids)} members, {len(self.ability_live_ids)} lives."
            )

        except Exception as e:
            print(f" [VectorEnv] Fixed Deck Load Error: {e}")
            self._load_verified_deck_pool()

    def _load_scenarios(self, path="data/scenarios.npz"):
        try:
            import numpy as np

            data = np.load(path)
            self.scenarios = {k: data[k] for k in data.files}
            self.num_scenarios = len(self.scenarios["batch_hand"])
            print(f" [VectorEnv] Loaded {self.num_scenarios} scenarios from {path}")
        except Exception as e:
            print(f" [VectorEnv] Failed to load scenarios: {e}")
            self.scenarios = None

    def reset(self, indices: List[int] = None):
        """Reset specified environments (or all if indices is None)."""
        if indices is None:
            # Full Reset
            # Optimization: If resetting all, just loop all in Numba
            # We can use a special function or pass all indices
            indices_arr = np.arange(self.num_envs, dtype=np.int32)
        else:
            indices_arr = np.array(indices, dtype=np.int32)

        # Use new reset_single logic via loop or parallel
        # We can reuse integrated_step_numba's reset logic helper
        # But we need a standalone reset kernel
        isn.reset_kernel_numba(
            indices_arr,
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
            self.opp_stage,
            self.opp_energy_vec,
            self.opp_energy_count,
            self.opp_tapped,
            self.opp_live,
            self.opp_scores,
            self.opp_global_ctx,
            self.opp_hand,
            self.opp_deck,
            self.batch_trash,
            self.opp_trash,
            self.batch_opp_history,
            self.ability_member_ids,
            self.ability_live_ids,
            int(self.force_start_order),
        )

        # Scenario Overwrite
        if getattr(self, "scenarios", None) is not None and os.getenv("USE_SCENARIOS", "0") == "1":
            try:
                # Select random scenarios
                num_reset = self.num_envs if indices is None else len(indices_arr)
                reset_indices = np.arange(self.num_envs) if indices is None else indices_arr
                scen_indices = np.random.randint(0, self.num_scenarios, size=num_reset)

                def load_field(name, target):
                    if name in self.scenarios:
                        data = self.scenarios[name][scen_indices]
                        if target.ndim == 1 and data.ndim == 2 and data.shape[1] == 1:
                            data = data.ravel()
                        target[reset_indices] = data

                load_field("batch_hand", self.batch_hand)
                load_field("batch_deck", self.batch_deck)
                load_field("batch_stage", self.batch_stage)
                load_field("batch_energy_vec", self.batch_energy_vec)
                load_field("batch_energy_count", self.batch_energy_count)
                load_field("batch_continuous_vec", self.batch_continuous_vec)
                load_field("batch_continuous_ptr", self.batch_continuous_ptr)
                load_field("batch_tapped", self.batch_tapped)
                load_field("batch_live", self.batch_live)
                load_field("batch_scores", self.batch_scores)
                load_field("batch_flat_ctx", self.batch_flat_ctx)
                load_field("batch_global_ctx", self.batch_global_ctx)

                load_field("opp_hand", self.opp_hand)
                load_field("opp_deck", self.opp_deck)
                load_field("opp_stage", self.opp_stage)
                load_field("opp_energy_vec", self.opp_energy_vec)
                load_field("opp_energy_count", self.opp_energy_count)
                load_field("opp_tapped", self.opp_tapped)
                load_field("opp_live", self.opp_live)
                load_field("opp_scores", self.opp_scores)
                load_field("opp_global_ctx", self.opp_global_ctx)

            except Exception as e:
                print(f" [VectorEnv] Error loading scenario data: {e}")

        # Reset local trackers
        if indices is None:
            self.turn = 1
            self.prev_scores.fill(0)
            self.prev_opp_scores.fill(0)
            self.prev_phases.fill(0)
            self.episode_returns.fill(0)
            self.episode_lengths.fill(0)
        else:
            for idx in indices:
                self.prev_scores[idx] = 0
                self.prev_opp_scores[idx] = 0
                self.prev_phases[idx] = 0
                self.episode_returns[idx] = 0
                self.episode_lengths[idx] = 0

        # Return observations
        return self.get_observations()

    def step(self, actions: np.ndarray):
        """Apply a batch of actions across all environments using Optimized Integrated Step."""
        # Ensure actions are int32
        if actions.dtype != np.int32:
            actions = actions.astype(np.int32)

        return self.integrated_step(actions)

    def integrated_step(self, actions: np.ndarray):
        """
        Executes the optimized Numba Integrated Step.
        Returns: obs, rewards, dones, infos (list of dicts)
        """
        term_scores_agent = np.zeros(self.num_envs, dtype=np.int32)
        term_scores_opp = np.zeros(self.num_envs, dtype=np.int32)

        rewards, dones = isn.integrated_step_numba(
            self.num_envs,
            actions,
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
            self.opp_live,  # Added
            self.opp_scores,
            self.opp_global_ctx,
            self.card_stats,
            self.bytecode_map,
            self.bytecode_index,
            self.batch_opp_history,
            self.obs_buffer,
            self.prev_scores,
            self.prev_opp_scores,
            self.prev_phases,
            self.ability_member_ids,
            self.ability_live_ids,
            self.turn_number_ptr,
            self.terminal_obs_buffer,
            self.batch_trash,
            self.opp_trash,
            term_scores_agent,
            term_scores_opp,
            0
            if self.obs_mode == "IMAX"
            else (1 if self.obs_mode == "STANDARD" else (3 if self.obs_mode == "ATTENTION" else 2)),
            self.game_config,  # New Config
            int(self.opp_mode),
            int(self.force_start_order),
        )

        # Apply Scenario Reward Scaling
        if self.scenario_reward_scale != 1.0 and os.getenv("USE_SCENARIOS", "0") == "1":
            rewards *= self.scenario_reward_scale

        # Construct Infos (minimal python overhead)
        infos = []
        for i in range(self.num_envs):
            if dones[i]:
                infos.append(
                    {
                        "terminal_observation": self.terminal_obs_buffer[i].copy(),
                        "episode": {"r": float(rewards[i]), "l": 10},
                        "terminal_score_agent": int(term_scores_agent[i]),
                        "terminal_score_opp": int(term_scores_opp[i]),
                    }
                )
            else:
                # Accumulate rewards for ongoing episodes
                # NOTE: rewards[i] is the delta reward for this specific integrated step.
                self.episode_returns[i] += rewards[i]
                self.episode_lengths[i] += 1
                infos.append({})

        # After loop, update terminal infos for done envs with the SUMMED returns
        for i in range(self.num_envs):
            if dones[i]:
                # Add terminal reward to the return
                final_return = self.episode_returns[i] + rewards[i]
                final_length = self.episode_lengths[i] + 1
                infos[i]["episode"] = {"r": float(final_return), "l": int(final_length)}
                # Reset accumulators for the next episode in this slot
                self.episode_returns[i] = 0
                self.episode_lengths[i] = 0

        return self.obs_buffer, rewards, dones, infos

    def get_action_masks(self):
        """Return legal action masks."""
        if self.obs_mode == "ATTENTION":
            return compute_action_masks_attention(
                self.num_envs,
                self.batch_hand,
                self.batch_stage,
                self.batch_tapped,
                self.batch_global_ctx,
                self.batch_live,
                self.card_stats,
            )
        else:
            return compute_action_masks(
                self.num_envs,
                self.batch_hand,
                self.batch_stage,
                self.batch_tapped,
                self.batch_global_ctx,
                self.batch_live,
                self.card_stats,
            )

    def get_observations(self):
        """Return a batched observation for RL models."""
        if self.obs_mode == "COMPRESSED":
            return isn.encode_observations_compressed(
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
                self.turn,
                self.obs_buffer,
            )
        elif self.obs_mode == "IMAX":
            return isn.encode_observations_imax(
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
                self.turn,
                self.obs_buffer,
            )
        elif self.obs_mode == "ATTENTION":
            return isn.encode_observations_attention(
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
                self.turn,
                self.obs_buffer,
            )
        else:
            return isn.encode_observations_standard(
                self.num_envs,
                self.batch_hand,
                self.batch_deck,
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
                self.turn,
                self.obs_buffer,
            )


@njit(cache=True)
def step_opponent_vectorized(
    opp_hand: np.ndarray,  # (N, 60)
    opp_deck: np.ndarray,  # (N, 60)
    opp_stage: np.ndarray,
    opp_energy_vec: np.ndarray,
    opp_energy_count: np.ndarray,
    opp_tapped: np.ndarray,
    opp_scores: np.ndarray,
    agent_tapped: np.ndarray,
    opp_global_ctx: np.ndarray,  # (N, 128)
    bytecode_map: np.ndarray,
    bytecode_index: np.ndarray,
):
    """
    Very simplified opponent step. Reuses agent bytecode but targets opponent buffers.
    """
    num_envs = len(opp_hand)
    # Dummy buffers for context (reused per env)
    f_ctx = np.zeros(64, dtype=np.int32)

    # We use the passed Hand/Deck buffers directly!
    live = np.zeros(50, dtype=np.int32)  # Dummy live zone for opponent

    # Reusable dummies to avoid allocation in loop
    dummy_cont_vec = np.zeros((32, 10), dtype=np.int32)
    dummy_ptr = np.zeros(1, dtype=np.int32)  # Ref Array
    dummy_bonus = np.zeros(1, dtype=np.int32)  # Ref Array

    for i in range(num_envs):
        # RESET local context per environment
        f_ctx.fill(0)

        # 1. Select Random Legal Action from Hand
        # Scan hand for valid bytecodes
        # Use fixed array for Numba compatibility (no lists)
        candidates = np.zeros(60, dtype=np.int32)
        c_ptr = 0

        for j in range(60):  # Hand size
            cid = opp_hand[i, j]
            if cid > 0:
                candidates[c_ptr] = j  # Store Index in Hand
                c_ptr += 1

        if c_ptr == 0:
            continue

        # Pick one random index
        idx_choice = np.random.randint(0, c_ptr)
        hand_idx = candidates[idx_choice]
        act_id = opp_hand[i, hand_idx]

        # 2. Execute
        if act_id > 0 and act_id < bytecode_index.shape[0]:
            map_idx = bytecode_index[act_id, 0]
            if map_idx > 0:
                code_seq = bytecode_map[map_idx]
                opp_global_ctx[i, 0] = opp_scores[i]
                opp_global_ctx[i, 3] -= 1  # Decrement Hand Count (HD) after playing

                # Reset dummies
                dummy_ptr[0] = 0
                dummy_bonus[0] = 0

                # Pass Row Slices of Hand/Deck
                # Careful: slicing in loop might allocate. Pass full array + index?
                # resolve_bytecode expects 1D array.
                # We can't pass a slice 'opp_hand[i]' effectively if function modifies it in place?
                # Actually resolve_bytecode modifies it.
                # Numba slices are views, should work.

                resolve_bytecode(
                    code_seq,
                    f_ctx,
                    opp_global_ctx[i],
                    1,
                    opp_hand[i],
                    opp_deck[i],
                    opp_stage[i],
                    opp_energy_vec[i],
                    opp_energy_count[i],
                    dummy_cont_vec,
                    dummy_ptr,
                    opp_tapped[i],
                    live,
                    agent_tapped[i],
                    bytecode_map,
                    bytecode_index,
                    dummy_bonus,
                )
                # Neutralized: opp_scores[i] = opp_global_ctx[i, 0]
                # SC = 0; OS = 1; TR = 2; HD = 3; DI = 4; EN = 5; DK = 6; OT = 7
                # Resolve bytecode puts score in SC (index 0) for the current player?
                # Let's check fast_logic.py: it uses global_ctx[SC].
                # So opp_scores[i] = opp_global_ctx[i, 0] is correct if they are the "current player" in that call.

                # 3. Post-Play Cleanup (Draw to refill?)
                # If card played, act_id removed from hand by resolve_bytecode (Opcode 11/12/13 usually).
                # To simulate "Draw", we check if hand size < 5.
                # Count current hand
                cnt = 0
                for j in range(60):
                    if opp_hand[i, j] > 0:
                        cnt += 1

                if cnt < 5:
                    # Draw top card from Deck
                    # Find first card in Deck
                    top_card = 0
                    deck_idx = -1
                    for j in range(60):
                        if opp_deck[i, j] > 0:
                            top_card = opp_deck[i, j]
                            deck_idx = j
                            break

                    if top_card > 0:
                        # Move to Hand (First empty slot)
                        for j in range(60):
                            if opp_hand[i, j] == 0:
                                opp_hand[i, j] = top_card
                                opp_deck[i, deck_idx] = 0  # Remove from deck
                                opp_global_ctx[i, 3] += 1  # Increment Hand Count (HD)
                                opp_global_ctx[i, 6] -= 1  # Decrement Deck Count (DK)
                                break


@njit(cache=True)
def resolve_auto_phases(
    num_envs: int,
    batch_hand: np.ndarray,
    batch_deck: np.ndarray,
    batch_global_ctx: np.ndarray,
    batch_tapped: np.ndarray,
    single_step: bool = False,
):
    """
    Automatically advances the game through non-interactive phases (0, 1, 2)
    until it reaches the Main Phase (3) or the game is over.
    Includes Turn Start Draw (Phase 2).
    """
    for i in range(num_envs):
        # We loop to handle multiple phase jumps if needed
        # SAFETY: Limit iterations
        max_iters = 1 if single_step else 10
        for _ in range(max_iters):
            ph = int(batch_global_ctx[i, 8])

            # 0 (MULLIGAN) or 8 (LIVE_RESULT) -> 1 (ACTIVE)
            if ph == 0 or ph == 8:
                # Turn Start: Reset Slot Played Flags (Indices 51-53)
                batch_global_ctx[i, 51:54] = 0

                # Reset Tapped Status (Members 0-2, Energy 3-15)
                batch_tapped[i, 0:16] = 0

                # Increment Energy Count (Index 5) (Up to 12)
                cur_ec = batch_global_ctx[i, 5]
                if cur_ec == 0:
                    batch_global_ctx[i, 5] = 3
                elif cur_ec < 12:
                    batch_global_ctx[i, 5] = cur_ec + 1

                # Increment Turn Counter (Index 54)
                batch_global_ctx[i, 54] += 1

                batch_global_ctx[i, 8] = 1
                continue

            # ACTIVE (1) -> ENERGY (2)
            if ph == 1:
                batch_global_ctx[i, 8] = 2
                continue

            # ENERGY (2) -> DRAW (3)
            if ph == 2:
                batch_global_ctx[i, 8] = 3
                continue

            # DRAW (3) -> MAIN (4)
            if ph == 3:
                # DRAW 1 CARD
                top_card = 0
                deck_idx = -1
                for d_idx in range(60):
                    if batch_deck[i, d_idx] > 0:
                        top_card = batch_deck[i, d_idx]
                        deck_idx = d_idx
                        break

                # REPLENISH DECK IF EMPTY (Infinite play for benchmarks)
                if top_card == 0:
                    batch_global_ctx[i, 8] = 4
                    continue

                if top_card > 0:
                    for h_idx in range(60):
                        if batch_hand[i, h_idx] == 0:
                            batch_hand[i, h_idx] = top_card
                            batch_deck[i, deck_idx] = 0
                            batch_global_ctx[i, 3] = 0
                            for k in range(60):
                                if batch_hand[i, k] > 0:
                                    batch_global_ctx[i, 3] += 1
                            batch_global_ctx[i, 6] -= 1
                            break

                batch_global_ctx[i, 8] = 4
                continue

            # If ph == 4 (Main), we stop and let the agent act.
            if ph == 4:
                break

            # If ph is not handled, break to avoid infinite loop
            break


@njit(parallel=True, cache=True)
def compute_action_masks_attention(
    num_envs: int,
    batch_hand: np.ndarray,
    batch_stage: np.ndarray,
    batch_tapped: np.ndarray,
    batch_global_ctx: np.ndarray,
    batch_live: np.ndarray,
    card_stats: np.ndarray,
):
    """
    Compute legal action masks for ATTENTION mode (512 actions).
    Mapping:
    - 0: Pass
    - 1-45: Play Member (15 hand idx * 3 slots)
    - 46-60: Set Live (15 hand idx)
    - 61-63: Activate Ability (3 slots)
    - 64-69: Mulligan Select (6 cards)
    - 100-299: Choice Actions (Not fully implemented yet)
    """
    masks = np.zeros((num_envs, 512), dtype=np.bool_)
    masks[:, 0] = True  # Pass always legal

    for i in prange(num_envs):
        phase = batch_global_ctx[i, 8]

        # --- Mulligan (Phase Includes -1, 0) ---
        if phase <= 0:
            # Allow pass (0) to finish
            masks[i, 0] = True
            # Allow select mulligan (64-69) for first 6 cards
            # ONE-WAY: If already selected (flag=1), mask it.
            for h_idx in range(6):
                if batch_hand[i, h_idx] > 0:
                    if batch_global_ctx[i, 120 + h_idx] == 0:
                        masks[i, 64 + h_idx] = True
            continue

        # --- Main Phase (4) ---
        if phase == 4:
            ec = batch_global_ctx[i, 5]
            tapped_count = 0
            for e_idx in range(min(ec, 12)):
                if batch_tapped[i, 3 + e_idx] > 0:
                    tapped_count += 1
            available_energy = ec - tapped_count

            # 1. Play Actions (1-45) & Set Live (46-60)
            # Hand limit for this mode is 15 primary indices
            for h_idx in range(15):
                cid = batch_hand[i, h_idx]
                if cid <= 0 or cid >= card_stats.shape[0]:
                    continue

                is_member = card_stats[cid, 10] == 1
                is_live = card_stats[cid, 10] == 2

                if is_member:
                    # Play to Slot 0-2 (Actions 1-45)
                    # Base = 1 + h_idx * 3
                    cost = card_stats[cid, 0]
                    for slot in range(3):
                        # One play per slot per turn check
                        if batch_global_ctx[i, 51 + slot] > 0:
                            continue

                        # Effective Cost (Baton Touch)
                        effective_cost = cost
                        prev_cid = batch_stage[i, slot]
                        if prev_cid > 0 and prev_cid < card_stats.shape[0]:
                            effective_cost = max(0, cost - card_stats[prev_cid, 0])

                        if effective_cost <= available_energy:
                            masks[i, 1 + h_idx * 3 + slot] = True

                # Set Live (Actions 46-60)
                # Rule 8.3 & 8.2.2: ANY card can be set.
                # Limit 3 cards in zone
                live_count = 0
                for lx in range(6):  # Check full 6 capacity (3 pending + 3 success)
                    if batch_live[i, lx] > 0:
                        live_count += 1

                if live_count < 3:
                    masks[i, 46 + h_idx] = True

            # 2. Activate Abilities (61-63)
            for slot in range(3):
                cid = batch_stage[i, slot]
                if cid > 0 and not batch_tapped[i, slot]:
                    masks[i, 61 + slot] = True

        # --- Choice Handling (Phase 7+) ---
        if phase >= 7 or phase == 4:
            # Allow hand selection (100-159)
            for h_idx in range(60):
                if batch_hand[i, h_idx] > 0:
                    masks[i, 100 + h_idx] = True

            # Allow energy selection (160-171)
            ec_val = batch_global_ctx[i, 5]
            for e_idx in range(min(ec_val, 12)):
                masks[i, 160 + e_idx] = True

    return masks


@njit(parallel=True, cache=True)
def compute_action_masks(
    num_envs: int,
    batch_hand: np.ndarray,
    batch_stage: np.ndarray,
    batch_tapped: np.ndarray,
    batch_global_ctx: np.ndarray,
    batch_live: np.ndarray,
    card_stats: np.ndarray,
):
    """
    Compute legal action masks using Python-compatible action IDs:
    - 0: Pass (always legal in Main Phase)
    - 1-180: Play Member from Hand (HandIdx * 3 + Slot + 1)
    - 200-202: Activate Ability (Slot)
    - 400-459: Set Live Card (HandIdx)
    """
    masks = np.zeros((num_envs, 2000), dtype=np.bool_)

    # Action 0 (Pass) is always legal
    masks[:, 0] = True

    for i in prange(num_envs):
        phase = batch_global_ctx[i, 8]
        # Mulligan Phases (-1, 0)
        # Mulligan Phases (-1, 0)
        if phase == -1 or phase == 0:
            masks[i, 0] = True  # Pass to finalize
            # Only allow selection if the card exists AND isn't already selected (One-way)
            for h_idx in range(6):  # Only first 6 cards are mull-able (Parity)
                if batch_hand[i, h_idx] > 0:
                    selected = batch_global_ctx[i, 120 + h_idx]
                    if selected == 0:
                        masks[i, 300 + h_idx] = True
            continue

        # Only compute member/ability actions in Main Phase (4)
        if phase == 4:
            # Calculate available untapped energy
            ec = batch_global_ctx[i, 5]  # EC at index 5
            tapped_count = 0
            for e_idx in range(min(ec, 12)):
                if batch_tapped[i, 3 + e_idx] > 0:
                    tapped_count += 1
            available_energy = ec - tapped_count

            # --- Member Play Actions (1-180) ---
            # Action ID = HandIdx * 3 + Slot + 1
            for h_idx in range(60):
                cid = batch_hand[i, h_idx]
                # CRITICAL SAFETY: card_stats shape check
                if cid <= 0 or cid >= card_stats.shape[0]:
                    continue

                # Check if this is a Member card (Type 1)
                if card_stats[cid, 10] != 1:
                    # Check if this is a Live card (Type 2) for play actions 400-459
                    if card_stats[cid, 10] == 2:
                        # Action ID = 400 + h_idx
                        action_id = 400 + h_idx

                        # --- RULE ACCURACY: Live cards can be set without checking hearts ---
                        # Requirements are checked during Performance phase (Rule 8.3)
                        # We allow setting if hand size limit not reached (max 3 in zone)
                        count_in_zone = 0
                        for j in range(50):
                            if batch_live[i, j] > 0:
                                count_in_zone += 1

                        if count_in_zone < 3:
                            masks[i, action_id] = True
                    continue

                # Member cost in card_stats[cid, 0]
                cost = card_stats[cid, 0]

                for slot in range(3):
                    action_id = h_idx * 3 + slot + 1

                    # Rule: One play per slot per turn (Indices 51-53)
                    if batch_global_ctx[i, 51 + slot] > 0:
                        continue

                    # Calculate effective cost (Baton Touch reduction)
                    effective_cost = cost
                    prev_cid = batch_stage[i, slot]
                    # SAFETY: Check cid range to avoid out-of-bounds card_stats access
                    if prev_cid >= 0 and prev_cid < card_stats.shape[0]:
                        prev_cost = card_stats[prev_cid, 0]
                        effective_cost = cost - prev_cost
                        if effective_cost < 0:
                            effective_cost = 0

                    if effective_cost <= available_energy:
                        masks[i, action_id] = True

            # --- Activate Ability Actions (200-202) ---
            for slot in range(3):
                cid = batch_stage[i, slot]
                if cid > 0 and not batch_tapped[i, slot]:
                    # Check if card has an activated ability
                    # For now, assume all untapped members can activate
                    masks[i, 200 + slot] = True

        # --- Mandatory Choice Handling (Phase 7, 8 & Fallback) ---
        if phase >= 7 or phase == 4:
            # Allow hand selection/discard actions (500-559) if hand has cards
            # This prevents Zero Legal Moves when a choice is pending.
            for h_idx in range(60):
                if batch_hand[i, h_idx] > 0:
                    masks[i, 500 + h_idx] = True

            # Allow energy selection actions (600-611) if energy exists
            energy_count = batch_global_ctx[i, 5]
            for e_idx in range(min(energy_count, 12)):
                masks[i, 600 + e_idx] = True

    return masks


# Export for legacy/external compatibility
encode_observations_vectorized = isn.encode_observations_standard
