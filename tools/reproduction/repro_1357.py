import os
import sys

# --- PATH SETUP ---
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

from backend.rust_serializer import RustGameStateSerializer
from game.data_loader import CardDataLoader
import engine_rust


class ReproHelper:
    def __init__(self):
        print("Initializing Repro Environment...")
        # 1. Load Data
        self.loader = CardDataLoader("data/cards.json")
        self.m_db, self.l_db, self.e_db = self.loader.load()
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            compiled_json_str = f.read()

        # 2. Init
        self.rust_db = engine_rust.PyCardDatabase(compiled_json_str)
        self.gs = engine_rust.PyGameState(self.rust_db)
        self.ser = RustGameStateSerializer(self.m_db, self.l_db, self.e_db)

        self._card_no_to_id = {m.card_no: cid for cid, m in self.m_db.items()}
        for cid, l in self.l_db.items():
            self._card_no_to_id[l.card_no] = cid

    def get_cid(self, card_no):
        if isinstance(card_no, int):
            return card_no
        return self._card_no_to_id.get(card_no)

    def set_state(self, p_idx, hand_cards=[], energy_count=0, stage_cards=[]):
        p = self.gs.get_player(p_idx)
        p.hand = [self.get_cid(c) for c in hand_cards if self.get_cid(c)]
        p.energy_zone = [40001] * energy_count
        p.set_tapped_energy([False] * energy_count)

        # Set stage cards (slot, card_no)
        for slot, card_no in stage_cards:
            cid = self.get_cid(card_no)
            if cid:
                p.stage[slot] = cid

        self.gs.set_player(p_idx, p)


def run_repro():
    helper = ReproHelper()
    target_card_no = "PL!SP-bp4-001-R"
    cid = helper.get_cid(target_card_no)

    # Common Padding IDs
    plinth_cid = 1368
    energy_cid = 40000

    # 3. Standard Init
    p0_deck = [plinth_cid] * 50
    p1_deck = [plinth_cid] * 50
    p0_energy = [energy_cid] * 10
    p1_energy = [energy_cid] * 10
    p0_lives = []
    p1_lives = [l for l in helper.l_db.keys()][:1]

    helper.gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    print("\n--- TEST 1: Conditions Met (Liella Only, 7 Energy) ---")
    # Liella is Group 3. CID 1 is Kanon bp1 (Group 3)
    helper.set_state(0, hand_cards=[target_card_no], energy_count=7, stage_cards=[(1, "PL!-sd1-001-SD")])

    p0 = helper.gs.get_player(0)
    print(f"Initial Energy: {len(p0.energy_zone)}")

    helper.gs.phase = 4  # Main
    view = helper.ser.serialize_state(helper.gs, 0)
    # RustGameStateSerializer uses 'PLAY' and 'source_card_id'
    play_actions = [a for a in view["legal_actions"] if a.get("type") == "PLAY" and a.get("source_card_id") == cid]

    if play_actions:
        print(f"Playing {target_card_no}...")
        # Execute the first play action found
        helper.gs.step(play_actions[0]["id"])

        p0_after = helper.gs.get_player(0)
        print(f"Energy After: {len(p0_after.energy_zone)}")
        if len(p0_after.energy_zone) > 7:
            print("SUCCESS: Energy Charged!")
            print(f"Tapped State of last energy: {p0_after.tapped_energy[-1]}")
        else:
            print("FAILURE: Energy NOT Charged.")
            print("Rule Log:")
            for line in helper.gs.rule_log[-10:]:
                print(f"  {line}")
    else:
        print("FAILURE: Play action not found.")

    print("\n--- TEST 2: Condition Failed (6 Energy) ---")
    helper = ReproHelper()
    helper.set_state(0, hand_cards=[target_card_no], energy_count=6, stage_cards=[(1, "PL!-sd1-001-SD")])
    view = helper.ser.serialize_state(helper.gs, 0)
    play_actions = [
        a for a in view.get("legal_actions", []) if a.get("type") == "PLAY" and a.get("source_card_id") == cid
    ]
    if play_actions:
        helper.gs.step(play_actions[0]["id"])
        p0_after = helper.gs.get_player(0)
        print(f"Energy After (Expected 6): {len(p0_after.energy_zone)}")

    print("\n--- TEST 3: Condition Failed (Non-Liella Member) ---")
    # Honoka is Group 1 (MUSE)
    helper = ReproHelper()
    helper.set_state(0, hand_cards=[target_card_no], energy_count=7, stage_cards=[(1, "LL!-sd1-001-SD")])
    view = helper.ser.serialize_state(helper.gs, 0)
    play_actions = [
        a for a in view.get("legal_actions", []) if a.get("type") == "PLAY" and a.get("source_card_id") == cid
    ]
    if play_actions:
        helper.gs.step(play_actions[0]["id"])
        p0_after = helper.gs.get_player(0)
        print(f"Energy After (Expected 7): {len(p0_after.energy_zone)}")


if __name__ == "__main__":
    run_repro()
