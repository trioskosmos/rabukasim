
import sys
import os
import json

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from engine.game.desc_utils import get_action_desc
from engine.game.enums import Phase

class MockPlayer:
    def __init__(self):
        self.hand = [1, 2, 3]
        self.stage = [10, 20, 30]
        self.live_zone = [100, 200, 300]
        self.discard = []

class MockGameState:
    def __init__(self):
        self.current_player = 0
        self.phase = Phase.MAIN
        self.active_player = MockPlayer()
        self.pending_choices = []
        self.member_db = {
            "1": {"name": "M-01", "card_no": "C01", "cost": 3},
            "2": {"name": "M-02", "card_no": "C02", "cost": 2},
            "10": {"name": "Stage-1", "card_no": "S01", "cost": 1},
            "100": {"name": "Live-1", "card_no": "L01"}
        }
        self.live_db = {
            "100": {"name": "Live-1", "card_no": "L01"}
        }
        self.triggered_abilities = []

def test_descriptions():
    gs = MockGameState()
    
    actions_to_test = [
        0,      # Pass (Main Phase)
        1,      # Play (Hand 0 to Slot 0)
        2,      # Play (Hand 0 to Slot 1)
        200,    # Ability (Slot 0)
        400,    # Live Set (Hand 0)
        580,    # Color Select (Red)
        900,    # Performance (Slot 0)
    ]
    
    print("--- VERIFYING DESCRIPTIONS ---")
    for lang in ["en", "jp"]:
        print(f"\n[{lang.upper()}]")
        for a in actions_to_test:
            desc = get_action_desc(a, gs, lang=lang)
            print(f"Action {a:4}: {desc}")

    # Test with pending choice (Mode Select)
    gs.pending_choices = [("SELECT_MODE", {"options": ["Mode A", "Mode B"]})]
    print(f"\n[MODE SELECT TEST]")
    print(f"Action 570 (EN): {get_action_desc(570, gs, lang='en')}")
    print(f"Action 570 (JP): {get_action_desc(570, gs, lang='jp')}")

if __name__ == "__main__":
    test_descriptions()
