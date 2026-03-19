import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from engine.game.desc_utils import get_action_desc

class MockGameState:
    def __init__(self, pending_choices):
        self.pending_choices = pending_choices
    def get_player(self, idx): return None
    @property
    def active_player(self): return None
    @property
    def current_player(self): return 0
    @property
    def member_db(self): return {}
    @property
    def live_db(self): return {}
    @property
    def energy_db(self): return {}

def test_card_420_text():
    # Card 420 ability text with icons
    choice_text = "{{toujyou.png|登場}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}{{icon_energy.png|E}}支払ってもよい：自分の控え室から、コストの合計が4以下になるようにメンバーカードを2枚までステージに登場させる。"
    
    # Mock parameters from PendingInteraction
    params = {
        "choice_text": choice_text
    }
    
    gs = MockGameState([("Optional", params)])
    
    # Action 11000 is "Yes"
    desc_yes = get_action_desc(11000, gs, lang="jp")
    # Action 11001 is "No"
    desc_no = get_action_desc(11001, gs, lang="jp")
    
    print(f"Yes Action (11000) Label: {desc_yes}")
    print(f"No Action (11001) Label: {desc_no}")
    
    # Check if Yes action shows the full text (if it didn't split incorrectly)
    assert "登場" in desc_yes
    assert "支払ってもよい" in desc_yes
    # Check if No action shows "いいえ" (the fallback)
    assert desc_no == "いいえ"

if __name__ == "__main__":
    try:
        test_card_420_text()
        print("Verification successful!")
    except Exception as e:
        print(f"Verification failed: {e}")
        import traceback
        traceback.print_exc()
