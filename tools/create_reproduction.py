import argparse
import json
import os
import sys

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
ENGINE_PATH = os.path.join(PROJECT_ROOT, "engine")
if ENGINE_PATH not in sys.path:
    sys.path.insert(0, ENGINE_PATH)

from game.data_loader import CardDataLoader

TEMPLATE = """import os
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
        self._card_no_to_id = {{m.card_no: cid for cid, m in m_db.items()}}
        for cid, l in l_db.items(): self._card_no_to_id[l.card_no] = cid

    def get_cid(self, card_no):
        if isinstance(card_no, int): return card_no
        return self._card_no_to_id.get(card_no)

    def set_hand(self, player_idx, card_nos):
        cids = [self.get_cid(c) for c in card_nos if self.get_cid(c) is not None]
        self.gs.set_hand_cards(player_idx, cids)
        print(f"Set Player {{player_idx}} hand to: {{card_nos}}")

    def set_discard(self, player_idx, card_nos):
        p = self.gs.get_player(player_idx)
        p.discard = [self.get_cid(c) for c in card_nos if self.get_cid(c) is not None]
        self.gs.set_player(player_idx, p)
        print(f"Set Player {{player_idx}} discard to: {{card_nos}}")

    def set_energy(self, player_idx, count, tapped=False):
        p = self.gs.get_player(player_idx)
        energy_cid = list(self.e_db.keys())[0] if self.e_db else 40000
        p.energy_zone = [energy_cid] * count
        p.set_tapped_energy([tapped] * count)
        self.gs.set_player(player_idx, p)
        print(f"Set Player {{player_idx}} energy to {{count}} (tapped={{tapped}})")

    def set_stage(self, player_idx, slot, card_no):
        cid = self.get_cid(card_no)
        if cid:
            self.gs.set_stage_card(player_idx, slot, cid)
            print(f"Placed {{card_no}} in Player {{player_idx}} Slot {{slot}}")

    def show_actions(self):
        print("\\n[CURRENT ACTIONS]")
        view = self.ser.serialize_state(self.gs, viewer_idx=self.gs.current_player)
        legal = view.get("legal_actions", [])
        for a in legal:
            print(f"  - ID {{a['id']}}: {{a['description']}}")
        return legal

    def step(self, action_id):
        print(f"\\nExecuting Action {{action_id}}...")
        try:
            self.gs.step(action_id)
            print("Done.")
        except Exception as e:
            print(f"!!! CRASH: {{e}}")
            traceback.print_exc()

def run_repro():
    print("=" * 60)
    print("REPRODUCTION: {card_no} ({card_name})")
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
    plinth_cid = {plinth_cid}
    energy_cid = {energy_cid}
    
    # 3. Standard Init
    # NOTE: Deck initialization uses integers.
    p0_deck = [plinth_cid] * 50
    p1_deck = [plinth_cid] * 50
    p0_energy = [energy_cid] * 10
    p1_energy = [energy_cid] * 10
    p0_lives = [l for l in l_db.keys()][:3]
    p1_lives = [l for l in l_db.keys()][:3]
    
    print(f"Initializing game with Plinth CID: {{plinth_cid}}")
    try:
        gs.initialize_game(p0_deck, p1_deck, p0_energy, p1_energy, p0_lives, p1_lives)
    except Exception as e:
        print(f"Initialization Failed: {{e}}")
        traceback.print_exc()
        return

    helper = ReproHelper(gs, serializer, m_db, l_db, e_db)

    # --- CUSTOM SETUP START ---
    target_card_no = "{card_no}"
    card_type = "{card_type}"

    # Setup God Mode
    helper.set_energy(0, 20, tapped=False)
    
    if card_type == "MEMBER":
        helper.set_hand(0, [target_card_no])
        # Add some cards to discard for testing recovery abilities
        helper.set_discard(0, ["{plinth_no}"] * 5) 
        gs.phase = 4  # Main
        play_action = 1 # Play to slot 0
    else:
        helper.set_hand(0, [target_card_no])
        gs.phase = 5  # LiveSet
        play_action = 400

    # --- CUSTOM SETUP END ---

    print(f"Phase: {{gs.phase}}")
    
    # 5. Show Actions & Execute
    legal = helper.show_actions()
    
    # Auto-play if target found
    if any(a['id'] == play_action for a in legal):
        helper.step(play_action)
    else:
        print(f"!!! Play action {{play_action}} not found in legal actions !!!")

    # 6. Post-Action Analysis
    print("\\n[POST-ACTION STATE]")
    p0 = gs.get_player(0)
    print(f"  Phase: {{gs.phase}}")
    print(f"  Hand Size: {{len(p0.hand)}}")
    print(f"  Discard Size: {{len(p0.discard)}}")
    print(f"  Score: {{p0.score}}")
    
    helper.show_actions()

    # TODO: Add your assertions!
    # assert p0.score == 1

if __name__ == "__main__":
    run_repro()
"""


def main():
    parser = argparse.ArgumentParser(description="Generate a reproduction script for a card")
    parser.add_argument("card_id", help="Card Number (e.g. BP01-001) or Integer ID")
    parser.add_argument("--name", help="Custom name for the repro file", default=None)
    args = parser.parse_args()

    print(f"Searching for card: {args.card_id}...")
    loader = CardDataLoader("data/cards.json")
    m_db, l_db, e_db = loader.load()

    target_card = None
    target_cid = None
    card_type = None

    # Try integer lookup first
    try:
        int_id = int(args.card_id)
        if int_id in m_db:
            target_card = m_db[int_id]
            target_cid = int_id
            card_type = "MEMBER"
        elif int_id in l_db:
            target_card = l_db[int_id]
            target_cid = int_id
            card_type = "LIVE"
    except ValueError:
        pass

    # Try string lookup
    if not target_card:
        for cid, m in m_db.items():
            if m.card_no == args.card_id:
                target_card = m
                target_cid = cid
                card_type = "MEMBER"
                break

    if not target_card:
        for cid, l in l_db.items():
            if l.card_no == args.card_id:
                target_card = l
                target_cid = cid
                card_type = "LIVE"
                break

    if not target_card:
        print(f"Error: Card {args.card_id} not found in database.")
        return

    plinth_cid = None
    plinth_no = "PL!SP-bp4-004-R＋"
    ULTIMATE_PLINTH = plinth_no
    for cid, m in m_db.items():
        if m.card_no == ULTIMATE_PLINTH:
            plinth_cid = cid
            break
    if not plinth_cid:
        # Fallback to any card
        plinth_cid = list(m_db.keys())[0] if m_db else 1
        plinth_no = m_db[plinth_cid].card_no if plinth_cid in m_db else "Unknown"

    energy_cid = list(e_db.keys())[0] if e_db else 40000

    # Sanitize filename
    safe_id = str(args.card_id).replace("!", "s").replace("-", "_").lower()
    filename = args.name if args.name else f"repro_{safe_id}.py"
    output_path = os.path.join(PROJECT_ROOT, "tools", "reproduction", filename)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    content = TEMPLATE.format(
        card_no=target_card.card_no,
        card_name=target_card.name,
        target_cid=target_cid,
        plinth_cid=plinth_cid,
        plinth_no=plinth_no,
        energy_cid=energy_cid,
        card_type=card_type,
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Generated reproduction script: {output_path}")
    print(f"Run it with: uv run python tools/reproduction/{filename}")


if __name__ == "__main__":
    main()
