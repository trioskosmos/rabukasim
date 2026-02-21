"""Audit all compiled abilities for potential issues.

Checks:
1. Opcode frequency across all cards.
2. Opcodes used in compiled data but potentially unimplemented in the Rust engine.
3. SELECT_MEMBER / PLAY_MEMBER_FROM_HAND with zero filter attr (potential filter encoding gaps).
4. Cards with extremely large attr values (potential encoding overflow).
5. Cost duplication patterns.
"""
import json
import sys
from collections import Counter, defaultdict

def main():
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with open("data/metadata.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    opcode_map = {}
    if "opcodes" in meta:
        for name, val in meta["opcodes"].items():
            opcode_map[val] = name

    opcode_usage = Counter()
    cards_by_opcode = defaultdict(list)
    total_abilities = 0
    total_cards = 0

    # Issue trackers
    zero_filter_selects = []  # Cards with SELECT_MEMBER/PLAY_FROM_HAND with a=0
    large_attr_values = []   # Cards with suspiciously large attr
    duplicate_cost_candidates = [] # Cards starting with PAY_ENERGY that also have metadata costs
    unknown_opcodes = []     # Opcodes not in metadata
    empty_bytecodes = []
    
    # Opcode IDs
    O_SELECT_MEMBER = 65
    O_PLAY_MEMBER_FROM_HAND = 57
    O_PLAY_MEMBER_FROM_DISCARD = 63
    O_PAY_ENERGY = 64
    O_MOVE_TO_DISCARD = 58
    O_TAP_MEMBER = 53
    O_PLACE_UNDER = 33
    O_RETURN = 1

    for db_name in ["member_db", "live_db"]:
        for cid_str, card in data.get(db_name, {}).items():
            cid = int(cid_str)
            card_name = card.get("name", "???")
            has_ab = False

            for ab_idx, ab in enumerate(card.get("abilities", [])):
                bc = ab.get("bytecode", [])
                costs = ab.get("costs", [])
                
                if not bc:
                    if ab.get("trigger", 0) not in [0, 4]:  # Not NONE or CONSTANT
                        empty_bytecodes.append(f"ID={cid} ({card_name}) ab#{ab_idx} trigger={ab.get('trigger')}")
                    continue

                has_ab = True
                total_abilities += 1

                # Parse bytecode
                for i in range(0, len(bc), 4):
                    if i + 3 >= len(bc):
                        break
                    op, v, a, s = bc[i], bc[i+1], bc[i+2], bc[i+3]

                    opcode_usage[op] += 1
                    if len(cards_by_opcode[op]) < 3:
                        cards_by_opcode[op].append(f"ID={cid}({card_name[:6]})")

                    # Check unknown opcodes
                    if op not in opcode_map and op not in unknown_opcodes:
                        unknown_opcodes.append(f"Opcode {op} in ID={cid} ({card_name})")

                    # Check zero-filter selects
                    if op in [O_SELECT_MEMBER, O_PLAY_MEMBER_FROM_HAND, O_PLAY_MEMBER_FROM_DISCARD]:
                        if a == 0:
                            zero_filter_selects.append(
                                f"ID={cid} ({card_name}) ab#{ab_idx} op={opcode_map.get(op, str(op))} a=0 s={s}"
                            )

                    # Check large attr values (potential overflow)
                    if isinstance(a, int) and abs(a) > 2**30:
                        large_attr_values.append(
                            f"ID={cid} ({card_name}) ab#{ab_idx} op={opcode_map.get(op, str(op))} a={a}"
                        )

                # Check duplicate cost pattern:
                # If bytecode starts with PAY_ENERGY AND metadata costs include energy
                if len(bc) >= 4 and bc[0] == O_PAY_ENERGY:
                    has_energy_cost = any(c.get("type") == 1 for c in costs) if costs else False
                    if has_energy_cost:
                        duplicate_cost_candidates.append(
                            f"ID={cid} ({card_name}) ab#{ab_idx}: PAY_ENERGY(v={bc[1]}) in bytecode + ENERGY cost in metadata"
                        )

            if has_ab:
                total_cards += 1

    # Output report
    print(f"Total cards with abilities: {total_cards}")
    print(f"Total abilities: {total_abilities}")
    print(f"Unique opcodes used: {len(opcode_usage)}")
    print()

    print("=" * 60)
    print("OPCODE FREQUENCY (sorted by ID)")
    print("=" * 60)
    for op in sorted(opcode_usage.keys()):
        count = opcode_usage[op]
        name = opcode_map.get(op, f"UNKNOWN_{op}")
        examples = ", ".join(cards_by_opcode.get(op, [])[:3])
        print(f"  {op:3d} ({name:30s}): {count:4d} uses  | e.g. {examples}")

    print()
    print("=" * 60)
    print(f"ISSUE 1: UNKNOWN OPCODES ({len(unknown_opcodes)} total)")
    print("=" * 60)
    for item in unknown_opcodes:
        print(f"  {item}")

    print()
    print("=" * 60)
    print(f"ISSUE 2: ZERO-FILTER SELECT/PLAY ({len(zero_filter_selects)} total)")
    print("  These cards use SELECT_MEMBER or PLAY_FROM_HAND with a=0,")
    print("  meaning NO name/cost/group filter is applied.")
    print("  Some are intentional (any card), but check cards with JP text")
    print("  that mentions specific names or cost limits.")
    print("=" * 60)
    for item in zero_filter_selects[:30]:
        print(f"  {item}")
    if len(zero_filter_selects) > 30:
        print(f"  ... and {len(zero_filter_selects) - 30} more")

    print()
    print("=" * 60)
    print(f"ISSUE 3: LARGE ATTR VALUES ({len(large_attr_values)} total)")
    print("=" * 60)
    for item in large_attr_values:
        print(f"  {item}")

    print()
    print("=" * 60)
    print(f"ISSUE 4: POTENTIAL DOUBLE-COST ({len(duplicate_cost_candidates)} total)")
    print("  Cards where PAY_ENERGY is in BOTH bytecode AND metadata costs.")
    print("  The engine pre-pays metadata costs, so bytecode PAY_ENERGY may cause double-charge.")
    print("=" * 60)
    for item in duplicate_cost_candidates[:30]:
        print(f"  {item}")
    if len(duplicate_cost_candidates) > 30:
        print(f"  ... and {len(duplicate_cost_candidates) - 30} more")

    print()
    print("=" * 60)
    print(f"ISSUE 5: EMPTY BYTECODES ON NON-CONSTANT ABILITIES ({len(empty_bytecodes)} total)")
    print("=" * 60)
    for item in empty_bytecodes[:20]:
        print(f"  {item}")
    if len(empty_bytecodes) > 20:
        print(f"  ... and {len(empty_bytecodes) - 20} more")

if __name__ == "__main__":
    main()
