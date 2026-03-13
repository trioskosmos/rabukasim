import json
import os
import sys

# Add project root to path
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from compiler.parser_v2 import AbilityParserV2
from tools.verify.bytecode_decoder import decode_bytecode

def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def inspect_card(query_id):
    cards_compiled = load_json("data/cards_compiled.json")
    if not cards_compiled:
        print("Error: data/cards_compiled.json not found.")
        return

    # Find card by ID (Packed or Logic)
    target_card = None
    target_cid = None
    
    qid = int(query_id)
    for db_name in ["member_db", "live_db", "energy_db"]:
        db = cards_compiled.get(db_name, {})
        if str(qid) in db:
            target_card = db[str(qid)]
            target_cid = str(qid)
            break
        # Logic ID search
        for cid, c in db.items():
            if (int(cid) & 0x0FFF) == qid:
                target_card = c
                target_cid = cid
                break
        if target_card:
            break

    if not target_card:
        print(f"Card with ID {query_id} not found.")
        return

    card_no = target_card.get("card_no")
    name = target_card.get("name")
    
    print(f"\n# Ability Inspector: {card_no} ({name})")
    print(f"- **Compiled ID**: `{target_cid}`")
    
    # 1. Shows stored logic
    abilities = target_card.get("abilities", [])
    print(f"\n## Stored Logic ({len(abilities)} abilities)")
    
    for i, ab in enumerate(abilities):
        trigger = ab.get("trigger")
        stored_bc = ab.get("bytecode", [])
        semantic_form = ab.get("semantic_form", {})
        print(f"\n### Ability {i} (Trigger: {trigger})")
        print(f"**Stored Bytecode**: `{stored_bc}`")
        if semantic_form:
            print("**Stored Semantic Form**:")
            print("```")
            print(json.dumps(semantic_form, indent=2, ensure_ascii=False))
            print("```")
        print("\n**Decoded Stored Bytecode**:")
        print("```")
        print(decode_bytecode(stored_bc))
        print("```")

    # 2. Live Re-compilation Check
    print("\n## Live Re-compilation Check")
    parser = AbilityParserV2()
    raw_text = target_card.get("ability_text", "")
    if not raw_text:
        print("> [!WARNING]\n> No pseudocode (ability_text) found in compiled data to re-compile.")
        return

    print(f"**Pseudocode used for re-compilation**:\n```\n{raw_text}\n```")
    
    try:
        new_abilities = parser.parse(raw_text)
        for i, ab in enumerate(new_abilities):
            new_bc = ab.compile()
            stored_bc = abilities[i].get("bytecode", []) if i < len(abilities) else None
            
            print(f"\n### Re-compiled Ability {i}")
            if new_bc == stored_bc:
                print("✅ **Bytecode Match**")
            else:
                print("❌ **BYTECODE DESYNC DETECTED**")
                print(f"**New Bytecode**: `{new_bc}`")
                print("\n**Decoded New Bytecode**:")
                print("```")
                print(decode_bytecode(new_bc))
                print("```")
                
                # Highlight differences if same length
                if stored_bc and len(new_bc) == len(stored_bc):
                    diffs = []
                    for j in range(len(new_bc)):
                        if new_bc[j] != stored_bc[j]:
                            diffs.append(f"pos {j}: {stored_bc[j]} -> {new_bc[j]}")
                    if diffs:
                        print("**Differences**:\n- " + "\n- ".join(diffs))
                        
    except Exception as e:
        print(f"❌ **Re-compilation Failed**: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: uv run python tools/inspect_ability.py <ID>")
        sys.exit(1)
    
    inspect_card(sys.argv[1])
