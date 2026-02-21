import sys
import os

# --- PATH SETUP ---
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

import engine_rust
from backend.rust_serializer import RustGameStateSerializer
from game.data_loader import CardDataLoader


class ReproHelper:
    def __init__(self):
        # 1. Load Data
        self.loader = CardDataLoader("data/cards.json")
        self.m_db, self.l_db, self.e_db = self.loader.load()
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled_json_str = f.read()

        # 2. Init
        self.rust_db = engine_rust.PyCardDatabase(compiled_json_str)
        self.gs = engine_rust.PyGameState(self.rust_db)
        self.ser = RustGameStateSerializer(self.m_db, self.l_db, self.e_db)

    def get_cid(self, card_no):
        for cid, card in self.m_db.items():
            if card.card_no == card_no:
                return cid
        return None

    def set_state(self, p_idx, hand_cards=[], energy_count=0, deck_cards=[]):
        p = self.gs.get_player(p_idx)
        p.hand = [self.get_cid(c) for c in hand_cards if self.get_cid(c)]
        p.deck = [self.get_cid(c) for c in deck_cards if self.get_cid(c)]
        p.energy_zone = [40001] * energy_count
        p.set_tapped_energy([False] * energy_count)
        self.gs.set_player(p_idx, p)


# --- RUN REPRO ---
def run_repro():
    helper = ReproHelper()
    target_card_no = "PL!-sd1-011-SD"
    cid = helper.get_cid(target_card_no)

    # Test Setup: Eri in hand, 1 fodder card, 3 cards in deck
    fodder = "PL!-sd1-001-SD"
    deck_pool = ["PL!-sd1-001-SD", "PL!-sd1-002-SD", "PL!-sd1-003-SD"]
    helper.set_state(0, hand_cards=[target_card_no, fodder], energy_count=4, deck_cards=deck_pool)

    # Advance to Main Phase
    helper.gs.phase = 4  # Main

    print("\n--- TEST: Look and Choose (PL!-sd1-011-SD) ---")
    view = helper.ser.serialize_state(helper.gs, 0)
    play_actions = [
        a for a in view.get("legal_actions", []) if a.get("type") == "PLAY" and a.get("source_card_id") == cid
    ]

    if play_actions:
        print(f"Playing {target_card_no}...")
        helper.gs.step(play_actions[0]["id"])

        # 1. OPTIONAL COST: Discard fodder or skip
        view_cost = helper.ser.serialize_state(helper.gs, 0)
        print(f"Pending Choice (Cost): {view_cost.get('pending_choice_text')}")
        actions = view_cost.get("legal_actions", [])
        print(f"DEBUG: Legal Actions IDs: {[a.get('id') for a in actions]}")
        done_action = [
            a
            for a in actions
            if a.get("desc") == "Done" or a.get("desc") == "終了" or str(a.get("id")) in ["0", "99", "999"]
        ]

        if done_action:
            print("SKIPPING COST (Done)...")
            helper.gs.step(done_action[0]["id"])
        else:
            print("FAILURE: Done action not found for optional cost.")
            return

        # 2. EFFECT: Look and Choose
        view_effect = helper.ser.serialize_state(helper.gs, 0)
        print(f"Pending Choice (Effect): {view_effect.get('pending_choice_text')}")

        effect_actions = [a for a in view_effect.get("legal_actions", []) if a.get("type") == "SELECT"]

        if effect_actions:
            print(f"Selecting card from effect: {effect_actions[0]['name']}...")
            helper.gs.step(effect_actions[0]["id"])

            p0_final = helper.gs.get_player(0)
            print(f"Hand Count After Skip: {len(p0_final.hand)}")
            # If logic is correct, effect should have been skipped and hand count should be same as after playing Eri (1).
        else:
            print("CORRECT: Effect skipped after bypassing optional cost.")
        for log in helper.gs.rule_log:
            print(f"LOG: {log}")

    else:
        print("FAILURE: Play action not found.")


if __name__ == "__main__":
    run_repro()
