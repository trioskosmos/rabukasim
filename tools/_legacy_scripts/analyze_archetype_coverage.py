import json
import os
import sys
from collections import defaultdict

# Fixed opcodes
O_TAP_S = 10
O_TAP_M = 30
O_DAMAGE = 19
O_DISCARD = 58
O_DRAW = 41
O_BUFF = 13
O_RECOVER = 15

# ... (We'll expand this later)


def load_data():
    try:
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def analyze():
    data = load_data()
    if not data:
        print("Data not found.")
        return

    patterns = defaultdict(int)
    examples = {}

    count = 0
    for cid, card in data["member_db"].items():
        for i, ab in enumerate(card.get("abilities", [])):
            bc = ab.get("bytecode", [])
            if not bc:
                continue

            # Simple heuristic: Just the opcode sequence
            # Bytecode is a flat array where every 1st of 4 (or 8?) ints is an opcode?
            # Rust definition: Chunk size is variable?
            # Wait, `compiler/main.py` outputs variable length?
            # Looking at `cards_compiled.json`:
            # "bytecode": [17, 1, 0, 6, 1, 0, 0, 0] -> 8 integers.
            # "bytecode": [58, 3, 2, 6, 16, 3, 0, 0, 1, 0, 0, 0] -> 12 integers.
            # "bytecode": [41, 5, 1, 6, 32, 99, 99, 2, 1, 0, 0, 0] -> 12 integers?
            # It seems chunks might be variable length.
            # 17 (RECOVER_MEMBER): 8 ints.
            # 58 (DISCARD): 4 ints + params? Looks like [58, 3, 2, 6] -> Op, Val, Cond, Target.
            # Then next opcode 16 (BOOST_SCORE) is [16, 3, 0, 0]?
            # Let's assume chunk size 4 for signature analysis.

            # Actually, let's just grab every 4th element as a heuristic for NOW.
            # Or better, just grab the FIRST element of every chunk.
            # Since we don't know chunk sizes perfectly without looking at `opcodes.rs`,
            # Let's try to infer or just list the raw first opcode.

            # But wait, looking at `logic.rs` or `archetype_tests.rs`:
            # vec![58, 1, 2, 6, 41, 3, 16, 1, 1, 0, 0, 0]
            # This is 12 ints.
            # 58 (Discard) -> 4 ints? [58, 1, 2, 6]
            # 41 (Draw) -> 4 ints? [41, 3, 16, 1]
            # 1 (Effect?) -> [1, 0, 0, 0]

            # So standard chunk size is 4.

            ops = []
            for j in range(0, len(bc), 4):
                if j < len(bc):
                    ops.append(bc[j])

            sig = tuple(ops)
            patterns[sig] += 1
            if sig not in examples:
                examples[sig] = f"{card['card_no']} - {ab.get('original_text', '')[:30]}"
            count += 1

    print(f"Analyzed {count} abilities.")
    print(f"Unique Patterns: {len(patterns)}")

    sorted_p = sorted(patterns.items(), key=lambda x: x[1], reverse=True)

    print(f"{'Count':<6} {'Signature':<40} {'Example'}")
    print("-" * 80)
    for sig, c in sorted_p[:20]:
        print(f"{c:<6} {str(sig):<40} {examples[sig]}")


if __name__ == "__main__":
    analyze()
