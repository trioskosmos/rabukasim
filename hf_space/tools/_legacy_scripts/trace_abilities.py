"""Trace a multi-ability card through the execution pipeline."""

import json

# Load compiled cards
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    db = json.load(f)

# Example multi-ability cards to trace
test_cards = [
    "PL!-bp3-001-P",  # ON_ACTIVATE + ON_LIVE_START
    "PL!HS-bp1-004-P",  # RECOVER_LIVE + ON_LIVE_START
    "PL!N-bp1-002-P",  # ON_PLAY + ON_ACTIVATE (from discard)
]

# Write results to file
with open("trace_results.log", "w", encoding="utf-8") as f:
    f.write("=" * 60 + "\n")
    f.write("MULTI-ABILITY CARD EXECUTION TRACE\n")
    f.write("=" * 60 + "\n")

    for target in test_cards:
        for card_id, card in db["member_db"].items():
            if card.get("card_no") == target:
                f.write(f"\n### Card: {card['card_no']} ({card['name']})\n")
                f.write(f"    Card ID: {card_id}\n")
                f.write(f"    Abilities: {len(card.get('abilities', []))}\n")

                for i, ab in enumerate(card.get("abilities", [])):
                    trigger = ab.get("trigger", "unknown")
                    bytecode = ab.get("bytecode", [])

                    # Decode bytecode opcodes
                    opcodes = []
                    for j in range(0, len(bytecode), 4):
                        if j + 3 < len(bytecode):
                            op = bytecode[j]
                            if op == 10:
                                opcodes.append("O_DRAW")
                            elif op == 11:
                                opcodes.append("O_BLADES")
                            elif op == 12:
                                opcodes.append("O_HEARTS")
                            elif op == 15:
                                opcodes.append("O_RECOV_L")
                            elif op == 17:
                                opcodes.append("O_RECOV_M")
                            elif op == 30:
                                opcodes.append("O_SELECT_MODE")
                            elif op == 41:
                                opcodes.append("O_LOOK_AND_CHOOSE")
                            elif op == 43:
                                opcodes.append("O_ACTIVATE_MEMBER")
                            elif op == 45:
                                opcodes.append("O_COLOR_SELECT")
                            elif op == 51:
                                opcodes.append("O_SET_TAPPED")
                            elif op == 81:
                                opcodes.append("O_ACTIVATE_ENERGY")
                            elif op >= 200:
                                opcodes.append(f"C_{op}")
                            elif op == 1:
                                opcodes.append("O_RETURN")
                            elif op > 0:
                                opcodes.append(f"O_{op}")

                    f.write(f"\n    Ability {i}:\n")
                    f.write(f"      Trigger: {trigger}\n")
                    f.write(f"      Bytecode length: {len(bytecode)}\n")
                    f.write(f"      Opcodes: {opcodes}\n")

                break
        else:
            f.write(f"\n### Card {target} NOT FOUND\n")

    f.write("\n" + "=" * 60 + "\n")
    f.write("EXECUTION PATH SUMMARY:\n")
    f.write("=" * 60 + "\n")
    f.write(
        """
1. PLAY MEMBER (Action ID 1-180):
   - Player selects card from hand + target slot
   - step() calls play_member_with_choice()
   - trigger_abilities_from(TriggerType::OnPlay) fires ALL OnPlay abilities

2. ON_ACTIVATE (Action ID 181-299):
   - Player selects ability on stage member
   - step() calls activate_ability_with_choice()
   - Single ability's bytecode executes

3. LIVE_START TRIGGER (Automatic):
   - When live phase begins
   - trigger_abilities_from(TriggerType::OnLiveStart) fires ALL matching abilities
   - Each ability gets unique ability_index in context

4. PAUSING FOR CHOICE:
   - Opcodes like O_SELECT_MODE, O_COLOR_SELECT pause execution
   - State stored in pending_ctx, pending_ab_idx
   - Phase switches to Response
   - get_legal_actions() generates choice action IDs

5. RESUMPTION:
   - Player selects choice (Action ID in 550+ range)
   - step() retrieves pending_ctx with program_counter
   - resolve_bytecode() continues from saved position
"""
    )
    print("Trace completed. Results written to trace_results.log")
