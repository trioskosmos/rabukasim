import json
import os
from collections import defaultdict

# Paths
CARDS_COMPILED_PATH = "data/cards_compiled.json"
OUTPUT_PATH = "engine_rust_src/data/scenarios.json"


def get_signature(bytecode):
    return tuple(bytecode)


def generate_scenarios():
    if not os.path.exists(CARDS_COMPILED_PATH):
        print(f"Error: {CARDS_COMPILED_PATH} not found.")
        return

    with open(CARDS_COMPILED_PATH, "r", encoding="utf-8") as f:
        db = json.load(f)

    members = db.get("member_db", {})

    # Group by signature
    patterns = defaultdict(list)
    for card_id, card in members.items():
        for ability in card.get("abilities", []):
            sig = get_signature(ability.get("bytecode", []))
            if sig:
                patterns[sig].append(
                    {"id": card_id, "text": card.get("original_text", ""), "card_no": card.get("card_no", "")}
                )

    # Sort patterns by frequency
    sorted_patterns = sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True)

    scenarios = []

    # Mapping for known archetype behaviors (Initial Set)
    # We define logical expectations for the signature itself
    KNOWLEDGE_BASE = {
        (58, 0, 0, 4, 15, 1, 0, 6): {
            "name": "Discard self -> Recover Live",
            "setup": {"discard": [200], "live": [200]},
            "choices": [0],
            "expect": {"hand_count": 1, "discard_count": 1, "hand_contains": [200]},
        },
        (58, 0, 0, 4, 41, 1, 0, 6): {
            "name": "Discard self -> Draw 1",
            "setup": {"deck": [100]},
            "expect": {"hand_count": 1, "discard_count": 1, "hand_contains": [100]},
        },
        (10, 0, 0, 4, 41, 1, 0, 6): {
            "name": "Tap self -> Draw 1",
            "setup": {"deck": [100]},
            "expect": {"hand_count": 1, "stage_tapped": [0], "hand_contains": [100]},
        },
    }

    # Generate top 20 scenarios
    for sig, examples in sorted_patterns[:20]:
        example = examples[0]

        # Look up in knowledge base or create skeleton
        kb_entry = KNOWLEDGE_BASE.get(
            sig,
            {"name": f"Archetype {hash(sig) & 0xFFFF:04X}", "setup": {"deck": [100, 101]}, "expect": {"phase": "Main"}},
        )

        scenario = {
            "id": f"archetype_{example['id']}",
            "signature": list(sig),
            "scenario_name": kb_entry["name"],
            "original_text_jp": example["text"],
            "real_card_id": int(example["id"]),
            "setup": {
                "hand": [int(example["id"])],
                "deck": kb_entry["setup"].get("deck", [100, 101]),
                "live": kb_entry["setup"].get("live", []),
                "discard": kb_entry["setup"].get("discard", []),
            },
            "action": {"type": "PLAY_MEMBER", "hand_idx": 0, "slot_idx": 0},
            "choices": kb_entry.get("choices"),
            "expect": kb_entry["expect"],
        }
        scenarios.append(scenario)

    output_data = {"scenarios": scenarios}

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    print(f"Generated {len(scenarios)} scenarios in {OUTPUT_PATH}")


if __name__ == "__main__":
    generate_scenarios()
