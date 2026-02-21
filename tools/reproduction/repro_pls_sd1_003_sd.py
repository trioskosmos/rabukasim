import os
import sys
import json
import traceback

# --- PATH SETUP ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

import engine_rust
from backend.rust_serializer import RustGameStateSerializer
from game.data_loader import CardDataLoader


class ReproHelper:
    def __init__(self, gs, serializer, m_db, l_db, e_db):
        self.gs = gs
        self.ser = serializer
        self.m_db = m_db
        self.l_db = l_db
        self.e_db = e_db
        self._card_no_to_id = {m.card_no: cid for cid, m in m_db.items()}
        for cid, l in l_db.items():
            self._card_no_to_id[l.card_no] = cid

    def get_cid(self, card_no):
        if isinstance(card_no, int):
            return card_no
        return self._card_no_to_id.get(card_no)

    def set_hand(self, player_idx, card_nos):
        cids = [self.get_cid(c) for c in card_nos if self.get_cid(c) is not None]
        self.gs.set_hand_cards(player_idx, cids)
        print(f"Set Player {player_idx} hand to: {card_nos}")

    def set_discard(self, player_idx, card_nos):
        p = self.gs.get_player(player_idx)
        p.discard = [self.get_cid(c) for c in card_nos if self.get_cid(c) is not None]
        self.gs.set_player(player_idx, p)
        print(f"Set Player {player_idx} discard to: {card_nos}")

    def set_energy(self, player_idx, count, tapped=False):
        p = self.gs.get_player(player_idx)
        energy_cid = list(self.e_db.keys())[0] if self.e_db else 40000
        p.energy_zone = [energy_cid] * count
        p.tapped_energy = [tapped] * count
        self.gs.set_player(player_idx, p)
        print(f"Set Player {player_idx} energy to {count} (tapped={tapped})")

    def set_stage(self, player_idx, slot, card_no):
        cid = self.get_cid(card_no)
        if cid:
            self.gs.set_stage_card(player_idx, slot, cid)
            print(f"Placed {card_no} in Player {player_idx} Slot {slot}")

    def show_actions(self):
        print("\n[CURRENT ACTIONS]")
        view = self.ser.serialize_state(self.gs, viewer_idx=self.gs.current_player)
        legal = view.get("legal_actions", [])
        for a in legal:
            print(f"  - ID {a['id']}: {a['description']}")
        return legal

    def step(self, action_id):
        print(f"\nExecuting Action {action_id}...")
        try:
            self.gs.step(action_id)
            print("Done.")
        except Exception as e:
            print(f"!!! CRASH: {e}")
            traceback.print_exc()


def run_repro():
    print("=" * 60)
    print("REPRODUCTION: PL!-sd1-003-SD (南 ことり)")
    print("=" * 60)

    # 1. Load Data
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()
    with open(os.path.join(PROJECT_ROOT, "data/cards_compiled.json"), "r", encoding="utf-8") as f:
        compiled_json_str = f.read()

    # 2. Init
    rust_db = engine_rust.PyCardDatabase(compiled_json_str)
    gs = engine_rust.PyGameState(rust_db)
    serializer = RustGameStateSerializer(m_db, l_db, e_db)

    # Common Padding IDs
    plinth_cid = 1368
    energy_cid = 40000

    # 3. Standard Init
    p0_deck = [plinth_cid] * 60
    p1_deck = [plinth_cid] * 60
    p0_energy = [energy_cid] * 60
    p1_energy = [energy_cid] * 60
    p0_lives = [l for l in l_db.keys()][:3]
    p1_lives = [l for l in l_db.keys()][:3]
    gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    helper = ReproHelper(gs, serializer, m_db, l_db, e_db)

    # --- CUSTOM SETUP START ---
    target_card_no = "PL!-sd1-003-SD"
    card_type = "MEMBER"

    # Setup God Mode
    helper.set_energy(0, 20, tapped=False)

    # Add a COST 4 μ's MEMBER card to discard for recovery
    p0 = gs.get_player(0)
    # PL!-sd1-010-SD is cost 4 Honoka (μ's)
    p0.discard = [helper.get_cid("PL!-sd1-010-SD")] * 3
    gs.set_player(0, p0)

    if card_type == "MEMBER":
        helper.set_hand(0, [target_card_no])
        # Add some cards to discard for testing recovery abilities
        helper.set_discard(0, ["PL!SP-bp4-004-R＋"] * 5)
        gs.phase = 4  # Main
        play_action = 1  # Play to slot 0
    else:
        helper.set_hand(0, [target_card_no])
        gs.phase = 5  # LiveSet
        play_action = 400

    # --- CUSTOM SETUP END ---

    print(f"Phase: {gs.phase}")

    # 5. Show Actions & Execute
    legal = helper.show_actions()

    # Auto-play if target found
    if any(a["id"] == play_action for a in legal):
        helper.step(play_action)
    else:
        print(f"!!! Play action {play_action} not found in legal actions !!!")

    # 6. Post-Action Analysis
    print("\n[POST-ACTION STATE]")
    p0 = gs.get_player(0)
    print(f"  Phase: {gs.phase}")
    print(f"  Hand Size: {len(p0.hand)}")
    print(f"  Discard Size: {len(p0.discard)}")
    print(f"  Score: {p0.score}")

    helper.show_actions()

    # TODO: Add your assertions!
    # assert p0.score == 1


if __name__ == "__main__":
    run_repro()

"""
# Reference Tables for Debugging
# ------------------------------
# Effect Types: 0:DRAW, 1:ADD_BLADES, 2:ADD_HEARTS, 5:RECOVER_LIVE, 6:BOOST_SCORE, 7:RECOVER_MEMBER, 8:BUFF_POWER
# Target Types: 0:SELF, 1:PLAYER, 2:OPPONENT, 6:CARD_HAND, 7:CARD_DISCARD, 12:OPPONENT_MEMBER
# Condition Types: 9:COUNT_GROUP, 14:COUNT_ENERGY, 19:COUNT_SUCCESS_LIVE, 32:BATON
# ------------------------------
"""
