import numpy as np

from engine.game.game_state import GameState


class UnifiedObservationEncoder:
    """
    Translates current GameState into various historic observation formats.
    """

    @staticmethod
    def encode(state: GameState, dim: int, player_idx: int = None) -> np.ndarray:
        if player_idx is None:
            player_idx = state.current_player

        if dim == 8192:
            return UnifiedObservationEncoder._encode_8192(state, player_idx)
        elif dim == 2048:
            return UnifiedObservationEncoder._encode_2048(state, player_idx)
        elif dim == 320:
            return UnifiedObservationEncoder._encode_320(state, player_idx)
        elif dim == 128:
            return UnifiedObservationEncoder._encode_128(state, player_idx)
        else:
            raise ValueError(f"Unsupported observation dimension: {dim}")

    @staticmethod
    def _encode_8192(state: GameState, player_idx: int) -> np.ndarray:
        from ai.vector_env import VectorGameState as VGS
        from ai.vector_env import encode_observations_vectorized

        p = state.players[player_idx]
        opp = state.players[1 - player_idx]

        # Prepare arrays (mirroring VectorGameState layout)
        batch_hand = np.zeros((1, 60), dtype=np.int32)
        h_len = min(len(p.hand), 60)
        for i in range(h_len):
            batch_hand[0, i] = p.hand[i]

        batch_stage = np.full((1, 3), -1, dtype=np.int32)
        for i in range(3):
            if i < len(p.stage):
                batch_stage[0, i] = p.stage[i]

        batch_energy_count = np.zeros((1, 3), dtype=np.int32)
        # Assuming p.stage_energy_count exists (based on _encode_2048)
        if hasattr(p, "stage_energy_count"):
            for i in range(3):
                if i < len(p.stage_energy_count):
                    batch_energy_count[0, i] = p.stage_energy_count[i]

        # NOTE: VectorEnv uses size 16 for tapped (Energy Tapping)
        batch_tapped = np.zeros((1, 16), dtype=np.int32)
        if hasattr(p, "tapped_members"):
            for i in range(min(3, len(p.tapped_members))):
                batch_tapped[0, i] = 1 if p.tapped_members[i] else 0

        batch_scores = np.array([len(p.success_lives)], dtype=np.int32)
        opp_scores = np.array([len(opp.success_lives)], dtype=np.int32)

        opp_stage = np.full((1, 3), -1, dtype=np.int32)
        for i in range(3):
            if i < len(opp.stage):
                opp_stage[0, i] = opp.stage[i]

        opp_tapped = np.zeros((1, 16), dtype=np.int32)
        if hasattr(opp, "tapped_members"):
            for i in range(min(3, len(opp.tapped_members))):
                opp_tapped[0, i] = 1 if opp.tapped_members[i] else 0

        # Global Context - FIXED MAPPING
        # Index 0 (SC): len(p.success_lives)
        # Index 1 (OS): len(opp.success_lives)
        # Index 2 (TR): len(p.discard)
        # Index 3 (HD): len(p.hand)
        # Index 4 (DI): len(opp.hand)
        # Index 5 (EN): p.energy_count
        # Index 6 (DK): len(p.main_deck)
        # Index 7 (OT): len(opp.discard)
        # Index 8 (PH): int(state.phase)
        # Index 9 (OD): len(opp.main_deck)
        g_ctx = np.zeros((1, 128), dtype=np.int32)
        g_ctx[0, 0] = len(p.success_lives)
        g_ctx[0, 1] = len(opp.success_lives)
        g_ctx[0, 2] = len(p.discard)
        g_ctx[0, 3] = len(p.hand)
        g_ctx[0, 4] = len(opp.hand)
        g_ctx[0, 5] = p.energy_count
        g_ctx[0, 6] = len(p.main_deck)
        g_ctx[0, 7] = len(opp.discard)
        g_ctx[0, 8] = int(state.phase)
        g_ctx[0, 9] = len(opp.main_deck)

        # Additional Buffers for Updated Signature
        batch_live = np.zeros((1, 50), dtype=np.int32)
        batch_opp_history = np.zeros((1, 50), dtype=np.int32)

        # Fill opp history with discard (Top Cards)
        d_len = min(len(opp.discard), 50)
        # VectorEnv assumes LIFO/Top-is-last.
        for i in range(d_len):
            batch_opp_history[0, i] = opp.discard[-(i + 1)]

        # VGS Cache
        if not hasattr(UnifiedObservationEncoder, "_vgs_cache"):
            UnifiedObservationEncoder._vgs_cache = VGS(1)
        vgs = UnifiedObservationEncoder._vgs_cache

        # Output
        obs = np.zeros((1, 8192), dtype=np.float32)

        encode_observations_vectorized(
            1,
            batch_hand,
            batch_stage,
            batch_energy_count,
            batch_tapped,
            batch_scores,
            opp_scores,
            opp_stage,
            opp_tapped,
            vgs.card_stats,
            g_ctx,
            batch_live,
            batch_opp_history,
            state.turn_number,
            obs,
        )
        return obs[0]

    @staticmethod
    def _encode_320(state: GameState, player_idx: int) -> np.ndarray:
        # LEGACY 320 (First Speed-up Era)
        # Replicates the encoding from ai/vector_env_legacy.py exactly.
        # This era ONLY saw Self Stage and Self Score. Hand/Opp were 0.

        obs = np.zeros(320, dtype=np.float32)
        p = state.players[player_idx]
        max_id_val = 2000.0  # Standard for VectorEnv

        # Phase [5] = 1.0 (Mocking Main Phase index from Legacy VectorEnv)
        obs[5] = 1.0
        # Current Player [16]
        obs[16] = 1.0

        # Stage [168:204] (3 slots * 12 features)
        # Note: Hand [36:168] remains 0.0 as in legacy training.
        for i in range(3):
            cid = p.stage[i]
            base = 168 + i * 12
            if cid >= 0:
                obs[base] = 1.0  # Exist
                obs[base + 1] = cid / max_id_val
                # Legacy energy count was normalized by 5.0
                obs[base + 11] = min(p.stage_energy_count[i] / 5.0, 1.0)

        # Score [270] (Self Score normalized by 5.0 in legacy)
        obs[270] = min(len(p.success_lives) / 5.0, 1.0)

        return obs

    @staticmethod
    def _encode_128(state: GameState, player_idx: int) -> np.ndarray:
        # 128-dim is the global_ctx vector
        p = state.players[player_idx]
        opp = state.players[1 - player_idx]

        g_ctx = np.zeros(128, dtype=np.float32)
        # Standard normalization from AlphaZero era
        g_ctx[0] = len(p.success_lives) / 3.0
        g_ctx[1] = len(opp.success_lives) / 3.0
        g_ctx[2] = len(p.discard) / 50.0
        g_ctx[3] = len(p.hand) / 50.0  # Normalized to deck size usually
        g_ctx[5] = p.energy_count / 10.0
        g_ctx[6] = len(p.main_deck) / 50.0

        # Turn info
        g_ctx[10] = state.turn_number / 20.0
        g_ctx[11] = 1.0 if state.current_player == player_idx else 0.0

        return g_ctx
