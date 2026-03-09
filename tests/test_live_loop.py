
import unittest
import numpy as np
from engine.game.game_state import GameState
from engine.game.enums import Phase
from engine.models.card import LiveCard, MemberCard

class TestLiveResultLoop(unittest.TestCase):
    def setUp(self):
        # Setup DBs
        member_db = {
            1: MemberCard(card_id=1, card_no="M1", name="M1", cost=1, blades=1, hearts=[1]*7, blade_hearts=[0]*7),
            2: MemberCard(card_id=2, card_no="M2", name="M2", cost=1, blades=1, hearts=[1]*7, blade_hearts=[0]*7)
        }
        live_db = {
            101: LiveCard(card_id=101, card_no="L1", name="Live1", score=1, required_hearts=[1]*7),
            102: LiveCard(card_id=102, card_no="L2", name="Live2", score=1, required_hearts=[1]*7),
            103: LiveCard(card_id=103, card_no="L3", name="Live3", score=1, required_hearts=[1]*7)
        }

        GameState.initialize_class_db(member_db, live_db)

        self.state = GameState()
        self.state.member_db = member_db
        self.state.live_db = live_db

    def test_score_2_2_loop(self):
        """Test simultaneous win at 2-2 score."""
        p0 = self.state.players[0]
        p1 = self.state.players[1]

        # Setup 2 wins each
        p0.success_lives = [101, 101]
        p1.success_lives = [101, 101]

        # Setup Live Zone for performance
        p0.live_zone = [102]
        p1.live_zone = [102]

        # Setup Stage
        p0.stage[0] = 1 # M1
        p1.stage[0] = 1 # M1

        # Phase Setup
        self.state.phase = Phase.PERFORMANCE_P1
        self.state.first_player = 0
        self.state.current_player = 0

        # Run Performance P1
        self.state = self.state.step(900)
        p0 = self.state.players[0] # Update reference

        self.assertTrue(p0.passed_lives, "P0 should have passed lives")

        # Should be P2 Performance now
        self.assertEqual(self.state.phase, Phase.PERFORMANCE_P2)
        self.state = self.state.step(900)
        p1 = self.state.players[1] # Update reference

        self.assertTrue(p1.passed_lives, "P1 should have passed lives")

        # Should be Live Result now
        self.assertEqual(self.state.phase, Phase.LIVE_RESULT)

        # Step through Live Result
        # Loop detection should happen if it gets stuck
        for i in range(10):
            if self.state.game_over:
                break
            if self.state.phase == Phase.ACTIVE:
                if self.state.game_over:
                    break
                print(f"DEBUG: Loop ended at step {i} in Phase ACTIVE without Game Over. Success Lives: P0={len(p0.success_lives)}, P1={len(p1.success_lives)}")
                break

            self.state = self.state.step(0)
            p0 = self.state.players[0]
            p1 = self.state.players[1]

        self.assertTrue(self.state.game_over, f"Game should be over. P0={len(p0.success_lives)}, P1={len(p1.success_lives)}")
        # Both reach 3 wins -> Draw (2)
        self.assertEqual(self.state.winner, 2)
        self.assertEqual(len(p0.success_lives), 3)
        self.assertEqual(len(p1.success_lives), 3)

if __name__ == "__main__":
    unittest.main()
