import os
import sys

# --- PATH SETUP ---
PROJECT_ROOT = os.getcwd()
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if os.path.join(PROJECT_ROOT, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "engine"))

import engine_rust
from game.data_loader import CardDataLoader

from backend.rust_serializer import RustGameStateSerializer


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

    def get_cid(self, card_no):
        if isinstance(card_no, int):
            return card_no
        rid = self.rust_db.id_by_no(card_no)
        if rid is not None:
            return rid

        # Fallback to python loader if needed (should not be needed for core logic)
        for cid, m in self.m_db.items():
            if m.card_no == card_no:
                return cid
        for cid, l in self.l_db.items():
            if l.card_no == card_no:
                return cid
        return None

    def set_state(self, p_idx, hand_cards=[], stage_cards=[], discard_cards=[], energy_count=0):
        p = self.gs.get_player(p_idx)
        p.hand = [self.get_cid(c) for c in hand_cards if self.get_cid(c) is not None]
        p.discard = [self.get_cid(c) for c in discard_cards if self.get_cid(c) is not None]
        p.energy_zone = [40001] * energy_count
        p.set_tapped_energy([False] * energy_count)

        # Set stage cards (slot, card_no)
        for slot, card_no in stage_cards:
            cid = self.get_cid(card_no)
            if cid is not None:
                p.stage[slot] = cid

        self.gs.set_player(p_idx, p)


def run_repro():
    helper = ReproHelper()
    target_card_no = "PL!SP-bp1-005-R"  # 1199
    cid = helper.get_cid(target_card_no)

    # Common Padding IDs
    plinth_cid = 1368
    energy_cid = 40001  # Standard energy

    p0_deck = [plinth_cid] * 50
    p1_deck = [plinth_cid] * 50
    p0_energy = [energy_cid] * 10
    p1_energy = [energy_cid] * 10
    p0_lives = []
    p1_lives = [l for l in helper.l_db.keys()][:1]

    helper.gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)

    print(f"\n--- TESTING {target_card_no} (ID={cid}) ---")

    # Put target in hand and another card to discard
    discard_target = "PL!-sd1-002-SD"
    helper.set_state(0, hand_cards=[target_card_no, discard_target], energy_count=10)

    helper.gs.phase = 4  # Main

    # Step 1: Play the card
    print("Step 1: Playing the member...")
    view = helper.ser.serialize_state(helper.gs, 0)

    all_actions = view.get("legal_actions", [])
    print(f"Total legal actions: {len(all_actions)}")

    play_actions = [a for a in all_actions if a.get("type") == "PLAY" and a.get("source_card_id") == cid]

    if not play_actions:
        print("FAILURE: Play action not found.")
        print("Actions found:")
        for a in all_actions[:10]:
            print(f"  {a.get('type')}: {a.get('name')} (CID={a.get('source_card_id')})")
        return

    # Choose slot 0
    play_action = play_actions[0]
    print(f"Executing Play Action: {play_action['name']} (ID={play_action['id']})")
    helper.gs.step(play_action["id"])

    print(f"Current Phase: {helper.gs.phase} (Expected 10/Response for cost)")
    print(f"Pending Choice Type: {helper.gs.pending_choice_type}")

    # Step 2: Pay the cost (Discard Hand 1)
    print("\nStep 2: Checking for Discard Cost...")
    view = helper.ser.serialize_state(helper.gs, 0)
    all_response_actions = view.get("legal_actions", [])

    # Check if hand cards have the action ID in their valid_actions
    p0_view = view["players"][0]
    for i, c in enumerate(p0_view["hand"]):
        print(f"Hand Card {i}: {c['name']} - Valid Actions: {c.get('valid_actions')}")

    # In response phase for discard cost, actions are usually SELECT_HAND (500-559 or 550+ range)
    discard_actions = [a for a in all_response_actions if a.get("type") == "SELECT_HAND"]

    if not discard_actions:
        print("FAILURE: Discard action (SELECT_HAND) not found in response phase.")
        print("Available actions metadata:")
        for a in all_response_actions:
            print(f"  {a.get('type')}: {a.get('name')} (ID={a.get('id')})")
        return

    print(f"Found {len(discard_actions)} potential discard actions.")
    for a in discard_actions:
        print(f"  Metdata: ID={a['id']}, Name={a['name']}, Type={a['type']}, HandIdx={a.get('hand_idx')}")

    target_discard_action = discard_actions[0]
    print(f"Executing: {target_discard_action['name']} (ID={target_discard_action['id']})")

    p0_before = helper.gs.get_player(0)
    hand_len_before = len(p0_before.hand)
    discard_len_before = len(p0_before.discard)

    helper.gs.step(target_discard_action["id"])

    p0_after = helper.gs.get_player(0)
    print(f"Hand: {hand_len_before} -> {len(p0_after.hand)}")
    print(f"Discard Pile: {discard_len_before} -> {len(p0_after.discard)}")

    if len(p0_after.discard) > discard_len_before:
        print("SUCCESS: Card moved to discard pile.")
    else:
        print("FAILURE: Discard pile did not increase.")

    print(f"Current Phase After Cost: {helper.gs.phase}")
    print(f"Pending Choice Type: {helper.gs.pending_choice_type}")

    # Step 3: Perform LOOK_AND_CHOOSE
    print("\nStep 3: Performing LOOK_AND_CHOOSE...")
    # I need to make sure there are cards in the deck to look at
    p0 = helper.gs.get_player(0)
    p0.deck = [helper.get_cid("PL!-sd1-001-SD")] * 10
    helper.gs.set_player(0, p0)

    view = helper.ser.serialize_state(helper.gs, 0)
    # The actions should be of type SELECT (550-849 range)
    lac_actions = [a for a in view.get("legal_actions", []) if a.get("type") == "SELECT"]

    if not lac_actions:
        print("FAILURE: No LOOK_AND_CHOOSE selection actions found.")
        print("Available actions:")
        for a in view.get("legal_actions", []):
            print(f"  {a.get('type')}: {a.get('name')} (ID={a.get('id')})")
        return

    print(f"Found {len(lac_actions)} selection actions.")
    # Pick the first one
    target_lac_action = lac_actions[0]
    print(f"Executing: {target_lac_action['name']} (ID={target_lac_action['id']})")

    p0_before = helper.gs.get_player(0)
    discard_len_before = len(p0_before.discard)
    hand_len_before = len(p0_before.hand)

    helper.gs.step(target_lac_action["id"])

    p0_after = helper.gs.get_player(0)
    print(f"Hand: {hand_len_before} -> {len(p0_after.hand)}")
    print(f"Discard Pile: {discard_len_before} -> {len(p0_after.discard)}")

    # Expectation: 1 card to hand, 4 cards to discard (from the 5 looked cards)
    if len(p0_after.discard) > discard_len_before:
        print(f"SUCCESS: {len(p0_after.discard) - discard_len_before} cards moved to discard pile.")
    else:
        print("FAILURE: Discard pile did not increase from remainder.")

    print(f"Current Phase After LAC: {helper.gs.phase}")


if __name__ == "__main__":
    run_repro()

if __name__ == "__main__":
    run_repro()
