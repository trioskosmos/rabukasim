from typing import List

import numpy as np

from engine.game.ai_compat import njit
from engine.game.fast_logic import batch_apply_action


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
):
    """
    Step N game environments in parallel using JIT logic and Real Card Data.
    """
    # Sync individual scores to global_ctx before stepping
    for i in range(len(actions)):
        batch_global_ctx[i, 0] = batch_scores[i]

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
        bytecode_map,
        bytecode_index,
    )


class VectorGameState:
    """
    Manages a batch of independent GameStates for high-throughput training.
    """

    def __init__(self, num_envs: int):
        self.num_envs = num_envs
        self.turn = 1

        # Batched state buffers
        self.batch_stage = np.full((num_envs, 3), -1, dtype=np.int32)
        self.batch_energy_vec = np.zeros((num_envs, 3, 32), dtype=np.int32)
        self.batch_energy_count = np.zeros((num_envs, 3), dtype=np.int32)
        self.batch_continuous_vec = np.zeros((num_envs, 32, 10), dtype=np.int32)
        self.batch_continuous_ptr = np.zeros(num_envs, dtype=np.int32)
        self.batch_tapped = np.zeros((num_envs, 3), dtype=np.int32)
        self.batch_live = np.zeros((num_envs, 50), dtype=np.int32)
        self.batch_opp_tapped = np.zeros((num_envs, 3), dtype=np.int32)
        self.batch_scores = np.zeros(num_envs, dtype=np.int32)

        # Pre-allocated context buffers (Extreme speed optimization)
        self.batch_flat_ctx = np.zeros((num_envs, 64), dtype=np.int32)
        self.batch_global_ctx = np.zeros((num_envs, 128), dtype=np.int32)
        self.batch_hand = np.zeros((num_envs, 50), dtype=np.int32)
        self.batch_deck = np.zeros((num_envs, 50), dtype=np.int32)

        # Pre-allocated observation buffer (SAVES ALLOCATION TIME)
        self.obs_buffer = np.zeros((num_envs, 320), dtype=np.float32)

        # Load Bytecode Map
        self._load_bytecode()
        self._load_verified_deck_pool()

    def _load_bytecode(self):
        import json

        try:
            with open("data/cards_numba.json", "r") as f:
                raw_map = json.load(f)

            # Convert to numpy array
            # Format: key "cardid_abidx" -> List[int]
            # storage:
            # 1. giant array of bytecodes (N, MaxLen, 4)
            # 2. lookup index (CardID, AbIdx) -> Index in giant array

            self.max_cards = 2000
            self.max_abilities = 4
            self.max_len = 64  # Max 64 instructions per ability

            # Count unique compiled entries
            unique_entries = len(raw_map)
            # (Index 0 is empty/nop)
            self.bytecode_map = np.zeros((unique_entries + 1, self.max_len, 4), dtype=np.int32)
            self.bytecode_index = np.full((self.max_cards, self.max_abilities), 0, dtype=np.int32)

            idx_counter = 1
            for key, bc_list in raw_map.items():
                cid, aid = map(int, key.split("_"))
                if cid < self.max_cards and aid < self.max_abilities:
                    # reshape list to (M, 4)
                    bc_arr = np.array(bc_list, dtype=np.int32).reshape(-1, 4)
                    length = min(bc_arr.shape[0], self.max_len)
                    self.bytecode_map[idx_counter, :length] = bc_arr[:length]
                    self.bytecode_index[cid, aid] = idx_counter
                    idx_counter += 1

            print(f" [VectorEnv] Loaded {unique_entries} compiled abilities.")

        except FileNotFoundError:
            print(" [VectorEnv] Warning: data/cards_numba.json not found. Using empty map.")
            self.bytecode_map = np.zeros((1, 64, 4), dtype=np.int32)
            self.bytecode_index = np.zeros((1, 1), dtype=np.int32)

    def _load_verified_deck_pool(self):
        import json

        try:
            # Load Verified List
            with open("verified_card_pool.json", "r", encoding="utf-8") as f:
                verified_data = json.load(f)

            # Load DB to map CardNo -> CardID
            with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
                db_data = json.load(f)

            self.verified_card_ids = []

            # Map numbers to IDs
            card_no_map = {}
            for cid, cdata in db_data["member_db"].items():
                card_no_map[cdata["card_no"]] = int(cid)

            for v_no in verified_data.get("verified_abilities", []):
                if v_no in card_no_map:
                    self.verified_card_ids.append(card_no_map[v_no])

            # Fallback
            if not self.verified_card_ids:
                print(" [VectorEnv] Warning: No verified cards found. Using ID 1.")
                self.verified_card_ids = [1]
            else:
                print(f" [VectorEnv] Loaded {len(self.verified_card_ids)} verified cards for training.")

            self.verified_card_ids = np.array(self.verified_card_ids, dtype=np.int32)

        except Exception as e:
            print(f" [VectorEnv] Deck Load Error: {e}")
            self.verified_card_ids = np.array([1], dtype=np.int32)

    def reset(self, indices: List[int] = None):
        """Reset specified environments (or all if indices is None)."""
        if indices is None:
            indices = list(range(self.num_envs))

        # Optimization: Bulk operations for indices if supported,
        # but for now loop is fine (reset is rare compared to step)

        # Prepare a random deck selection to broadcast?
        # Actually random.choice is fast.

        for i in indices:
            self.batch_stage[i].fill(-1)
            self.batch_energy_vec[i].fill(0)
            self.batch_energy_count[i].fill(0)
            self.batch_continuous_vec[i].fill(0)
            self.batch_continuous_ptr[i] = 0
            self.batch_tapped[i].fill(0)
            self.batch_live[i].fill(0)
            self.batch_opp_tapped[i].fill(0)
            self.batch_scores[i] = 0

            # Reset contexts
            self.batch_flat_ctx[i].fill(0)
            self.batch_global_ctx[i].fill(0)

            # Initialize Deck with Verified Cards (Random 50)
            # Fast choice from verified pool
            if len(self.verified_card_ids) > 0:
                dk = np.random.choice(self.verified_card_ids, 50)
                self.batch_deck[i] = dk

            # Initialize Hand (Draw 5 from deck)
            # Simple simulation: Move top 5 deck to hand
            self.batch_hand[i, :5] = self.batch_deck[i, :5]
            # Shift deck? Or just pointer?
            # For this benchmark we assume infinite deck or simple pointer logic via opcodes.
            # But the 'hand' array needs to be populated for gameplay to start.

        self.turn = 1

    def step(self, actions: np.ndarray):
        """Apply a batch of actions across all environments."""
        step_vectorized(
            actions,
            self.batch_stage,
            self.batch_energy_vec,
            self.batch_energy_count,
            self.batch_continuous_vec,
            self.batch_continuous_ptr,
            self.batch_tapped,
            self.batch_live,
            self.batch_opp_tapped,
            self.batch_scores,
            self.batch_flat_ctx,
            self.batch_global_ctx,
            self.batch_hand,
            self.batch_deck,
            self.bytecode_map,
            self.bytecode_index,
        )
        # Simplified turn advancement
        # In real VectorEnv, this would be managed by the engine rules
        pass

    def get_observations(self):
        """Return a batched observation for RL models."""
        return encode_observations_vectorized(
            self.num_envs,
            self.batch_stage,
            self.batch_energy_count,
            self.batch_tapped,
            self.batch_scores,
            self.turn,
            self.obs_buffer,
        )


@njit(cache=True)
def encode_observations_vectorized(
    num_envs: int,
    batch_stage: np.ndarray,  # (N, 3)
    batch_energy_count: np.ndarray,  # (N, 3)
    batch_tapped: np.ndarray,  # (N, 3)
    batch_scores: np.ndarray,  # (N,)
    turn_number: int,
    observations: np.ndarray,  # (N, 320)
):
    # Reset buffer (extremely fast on pre-allocated)
    observations.fill(0.0)
    max_id_val = 2000.0  # Normalization constant

    for i in range(num_envs):
        # --- 1. METADATA [0:36] ---
        # Phase (Simplify: Always Main Phase=1 for now in vector env)
        # Phase 1=Start, 2=Draw, 3=Main... Main is index 3+2=5?
        # GameState logic: phase_val = int(phase) + 2. Main is 3. So 5.
        observations[i, 5] = 1.0

        # Current Player [16:18] - Always Player 0 for this vector view
        observations[i, 16] = 1.0

        # --- 2. HAND [36:168] ---
        # VectorEnv doesn't track hand yet. Leave 0.0.

        # --- 3. SELF STAGE [168:204] (3 slots * 12 features) ---
        for slot in range(3):
            cid = batch_stage[i, slot]
            base = 168 + slot * 12
            if cid >= 0:
                observations[i, base] = 1.0
                observations[i, base + 1] = cid / max_id_val
                observations[i, base + 2] = 1.0 if batch_tapped[i, slot] else 0.0

                # Mock attributes (since we don't have full DB access inside JIT yet)
                # In real imp, we'd pass arrays like member_costs
                observations[i, base + 3] = 0.5  # Default power

                # Energy Count
                observations[i, base + 11] = min(batch_energy_count[i, slot] / 5.0, 1.0)

        # --- 4. OPPONENT STAGE [204:240] ---
        # Not tracked in partial vector env yet.

        # --- 5. LIVE ZONE [240:270] ---
        # Not tracked in partial vector env yet.

        # --- 6. SCORES [270:272] ---
        observations[i, 270] = min(batch_scores[i] / 5.0, 1.0)

    return observations
