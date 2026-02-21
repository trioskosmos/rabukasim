import os
import sys
import unittest

import numpy as np

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from ai.obs_adapters import UnifiedObservationEncoder

from engine.game.enums import Phase
from engine.game.game_state import GameState


class TestObsAlignment(unittest.TestCase):
    def test_encode_8192_mappings(self):
        print("Verifying UnifiedObservationEncoder._encode_8192 alignment...")

        # 1. Create Mock GameState
        state = GameState()
        p = state.players[0]
        opp = state.players[1]

        # Set known values to distinct integers to trace them
        # Counts:
        # Score: 5 (Distinct from Phase values 3, 4)

        p.success_lives = [1] * 5
        opp.success_lives = [1] * 2

        p.discard = [1] * 11
        p.hand = [1] * 4
        p.energy_zone = [1] * 5
        p.main_deck = [1] * 20
        opp.discard = [1] * 7
        opp.hand = [1] * 6
        opp.main_deck = [1] * 25

        state.phase = Phase.MAIN  # 4
        state.turn_number = 10

        # 2. Encode
        obs = UnifiedObservationEncoder.encode(state, 8192, 0)

        # 3. Verify Output in Observation Vector

        SCORE_START = 8000
        # obs[SCORE_START] = score / 9.0
        self.assertAlmostEqual(obs[SCORE_START], 5.0 / 9.0, places=4, msg="My Score Mismatch")

        VOLUMES_START = 7800
        # My Deck (DK=20) -> VOL+0
        self.assertAlmostEqual(obs[VOLUMES_START], 20.0 / 50.0, places=4, msg="My Deck Volume Mismatch")

        # Opp Deck (DK=25) -> VOL+1
        self.assertAlmostEqual(obs[VOLUMES_START + 1], 25.0 / 50.0, places=4, msg="Opp Deck Volume Mismatch")

        # My Hand (HD=4) -> VOL+2
        self.assertAlmostEqual(obs[VOLUMES_START + 2], 4.0 / 20.0, places=4, msg="My Hand Volume Mismatch")

        # My Trash (TR=11) -> VOL+3
        self.assertAlmostEqual(obs[VOLUMES_START + 3], 11.0 / 50.0, places=4, msg="My Trash Volume Mismatch")

        # Opp Hand (HD=6) -> VOL+4
        self.assertAlmostEqual(obs[VOLUMES_START + 4], 6.0 / 20.0, places=4, msg="Opp Hand Volume Mismatch")

        # Opp Trash (OT=7) -> VOL+5
        val_opp_trash = obs[VOLUMES_START + 5] * 50.0
        print(f"Observed Opp Trash (Volume): {val_opp_trash} (Expected 7)")
        if abs(val_opp_trash - 7.0) > 0.1:
            self.fail(f"Opp Trash mismatch: Got {val_opp_trash}, Expected 7")

        # One-Hot Phase
        # Index 20 + Phase. Phase.MAIN = 4 -> Index 24.
        # Score is 5.
        # If code reads [0] (Score=5), it sets Index 25.
        # If code reads [8] (Phase=4), it sets Index 24.

        if obs[24] == 1.0:
            print("Phase correctly identified as MAIN (4).")
        elif obs[25] == 1.0:
            print("Phase identified as 5 (Score value!) -> Mismatch.")
            self.fail("Phase encoding is reading Score index!")
        else:
            print("Phase not set at expected index 24?")
            # Check if it's somewhere else
            idx = np.where(obs[20:30] == 1.0)[0]
            print(f"Phase set at relative index: {idx}")
            self.fail(f"Phase encoding failed. Index 24 not set. Found set at relative: {idx}")


if __name__ == "__main__":
    unittest.main()
