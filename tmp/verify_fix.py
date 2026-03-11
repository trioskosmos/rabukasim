
import json
import os
import sys

PROJECT_ROOT = r'c:\Users\trios\.gemini\antigravity\vscode\loveca-copy'
sys.path.insert(0, PROJECT_ROOT)

from engine.game.deck_utils import UnifiedDeckParser

def main():
    # Mock some card data
    mock_db = {
        "member_db": {
            "1": {"card_no": "pl!n-bp3-020-n", "name": "Lowercase Member"}
        },
        "live_db": {},
        "energy_db": {}
    }
    
    parser = UnifiedDeckParser(mock_db)
    
    # Test normalization fix
    test_code = "PL!N-BP3-020-N"
    norm_code = parser.normalize_code(test_code)
    print(f"Testing normalization of '{test_code}': '{norm_code}'")
    
    resolved = parser.resolve_card(test_code)
    if resolved:
        print(f"SUCCESS: Resolved '{test_code}' to '{resolved.get('name')}'")
    else:
        print(f"FAILURE: Could not resolve '{test_code}'")

if __name__ == "__main__":
    main()
