import os
import random
import sys

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import engine_rust

from ai.headless_runner import RandomAgent
from backend.rust_serializer import RustCompatGameState, RustGameStateSerializer
from engine.game.data_loader import CardDataLoader


def audit_state(state_dict, game_id, turn, phase):
    """Scan the serialized state for anomalies."""
    issues = []

    # 1. Scan legal_actions
    for action in state_dict.get("legal_actions", []):
        aid = action.get("id")
        desc = action.get("text", "")
        raw = action.get("raw_text", "")

        # Check for undefined/None
        if desc is None or "undefined" in str(desc) or "None" in str(desc):
            issues.append(f"Action {aid}: Description is '{desc}'")

        # Check for technical leakages in friendly mode (if the text looks like raw pseudocode but didn't translate)
        # Note: Frontend does the translation, but we can check if the provided 'text' is just raw opcodes
        if desc and desc.startswith("O_") or "TRIGGER:" in str(desc):
            issues.append(f"Action {aid}: Description looks technical: '{desc}'")

        # Check for missing images in ability actions
        if action.get("type") == "ABILITY" and not action.get("img"):
            issues.append(f"Action {aid}: Missing image for ABILITY action")

    # 2. Scan pending_choice
    pc = state_dict.get("pending_choice")
    if pc:
        desc = pc.get("description", "")
        if not desc or "undefined" in str(desc) or "None" in str(desc):
            issues.append(f"Pending Choice: Description is '{desc}'")

        if pc.get("source_member") == "Game" and pc.get("type") in ["SELECT_FROM_LIST", "SELECT_MODE"]:
            # This might be fine, but worth noting if we expect a card
            pass

    return issues


def run_audit(num_games=10):
    print(f"Starting UI Audit: {num_games} games...")

    # Load Data properly using CardDataLoader
    compiled_path = os.path.join(PROJECT_ROOT, "data", "cards_compiled.json")
    loader = CardDataLoader(compiled_path)
    member_db, live_db, energy_db = loader.load()

    # Still need the raw JSON for the Rust engine DB
    with open(compiled_path, "r", encoding="utf-8") as f:
        json_str = f.read()

    db = engine_rust.PyCardDatabase(json_str)

    # Setup Serializer
    # The serializer expects string keys in some places or handles MaskedDB
    serializer = RustGameStateSerializer(member_db, live_db, energy_db)

    agent = RandomAgent()
    total_issues = 0
    all_anomalies = []

    for g_idx in range(num_games):
        print(f"Game {g_idx + 1}/{num_games}...", end="\r")
        gs = engine_rust.PyGameState(db)

        # Setup random decks
        m_ids = [int(k) for k in member_db.keys()]
        l_ids = [int(k) for k in live_db.keys()]
        e_id = int(list(energy_db.keys())[0]) if energy_db else 40000

        def get_rand_deck():
            random.shuffle(m_ids)
            random.shuffle(l_ids)
            main = []
            for mid in m_ids[:15]:
                main.extend([mid] * 4)
            for lid in l_ids[:4]:
                main.extend([lid] * 4)
            random.shuffle(main)
            return main[:60], [e_id] * 12, l_ids[:3]

        p0_m, p0_e, p0_l = get_rand_deck()
        p1_m, p1_e, p1_l = get_rand_deck()

        gs.initialize_game(p0_m, p1_m, p0_e, p1_e, p0_l, p1_l)

        turn_limit = 300
        while not gs.is_terminal() and gs.turn < turn_limit:
            # Audit State
            compat_gs = RustCompatGameState(gs, member_db, live_db, energy_db)
            state_dict = serializer.serialize_state(compat_gs, viewer_idx=0)

            issues = audit_state(state_dict, g_idx, gs.turn, gs.phase)
            if issues:
                for iss in issues:
                    anomaly = f"[G{g_idx} T{gs.turn} P{gs.phase}] {iss}"
                    if anomaly not in all_anomalies:
                        all_anomalies.append(anomaly)
                        print(f"\n{anomaly}")
                        total_issues += 1

            # Step
            mask = gs.get_legal_actions()
            if not any(mask):
                break

            # Simple random step
            legal_indices = [i for i, possible in enumerate(mask) if possible]
            action = random.choice(legal_indices)
            gs = gs.step(action)

    print(f"\nAudit Complete. Total Anomalies found: {total_issues}")
    if all_anomalies:
        with open("ui_audit_report.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(all_anomalies))
        print("Detailed report saved to ui_audit_report.txt")


if __name__ == "__main__":
    run_audit(num_games=20)
