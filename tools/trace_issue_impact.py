# -*- coding: utf-8 -*-
"""Trace each audit issue to real cards that use the affected opcodes."""

import json

from engine.models.bytecode_readable import CONDITION_NAMES, OPCODE_NAMES

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)
with open("data/metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

opcode_by_name = meta["opcodes"]
TRACE_EFFECTS = {
    "SELECT_CARDS": opcode_by_name.get("SELECT_CARDS", -1),
    "LOSE_EXCESS_HEARTS": opcode_by_name.get("LOSE_EXCESS_HEARTS", -1),
    "SKIP_ACTIVATE_PHASE": opcode_by_name.get("SKIP_ACTIVATE_PHASE", -1),
    "PAY_ENERGY_DYNAMIC": opcode_by_name.get("PAY_ENERGY_DYNAMIC", -1),
    "LOOK_DECK_DYNAMIC": opcode_by_name.get("LOOK_DECK_DYNAMIC", -1),
    "REPEAT_ABILITY": opcode_by_name.get("REPEAT_ABILITY", -1),
    "REDUCE_SCORE": opcode_by_name.get("REDUCE_SCORE", -1),
    "DRAW_UNTIL": opcode_by_name.get("DRAW_UNTIL", -1),
}

TRACE_CONDS = {
    "HAS_KEYWORD": meta["conditions"].get("HAS_KEYWORD", -1),
    "COUNT_ENERGY": meta["conditions"].get("COUNT_ENERGY", -1),
    "COUNT_ENERGY_EXACT": meta["conditions"].get("COUNT_ENERGY_EXACT", -1),
}


def find_cards(target_op):
    results = []
    for db_key in ["member_db", "live_db"]:
        db = data.get(db_key, {})
        for cid, card in db.items():
            card_no = card.get("card_no", "?")
            name = card.get("name", "?")
            for ab_idx, ab in enumerate(card.get("abilities", [])):
                bc = ab.get("bytecode", [])
                if not bc or bc == [1, 0, 0, 0, 0]:
                    continue
                for i in range(0, len(bc), 5):
                    op = bc[i]
                    real_op = op - 1000 if op >= 1000 else op
                    if real_op == target_op:
                        results.append((card_no, cid, ab_idx, name, bc[i : i + 5]))
                        break
    return results


lines = []


def p(s=""):
    lines.append(s)


p("=" * 70)
p("ISSUE IMPACT TRACE REPORT")
p("=" * 70)

p()
p("=== EFFECT OPCODES ===")
for name, op_id in sorted(TRACE_EFFECTS.items(), key=lambda x: x[1]):
    if op_id == -1:
        p(f"  {name}: NOT IN METADATA")
        continue
    cards = find_cards(op_id)
    p(f"\n  {name} (op={op_id}): {len(cards)} cards")
    for card_no, cid, ab_idx, cname, instr in cards[:8]:
        p(f"    {card_no} (ID={cid} Ab{ab_idx}) {instr}")
    if len(cards) > 8:
        p(f"    ...+{len(cards) - 8} more")

p()
p("=== CONDITION OPCODES ===")
for name, cond_id in sorted(TRACE_CONDS.items(), key=lambda x: x[1]):
    if cond_id == -1:
        p(f"  {name}: NOT IN METADATA")
        continue
    cards = find_cards(cond_id)
    p(f"\n  {name} (op={cond_id}): {len(cards)} cards")
    for card_no, cid, ab_idx, cname, instr in cards[:5]:
        p(f"    {card_no} (ID={cid} Ab{ab_idx}) {instr}")
    if len(cards) > 5:
        p(f"    ...+{len(cards) - 5} more")

p()
p("=== ALL OPCODES IN COMPILED BYTECODE ===")
all_ops = {}
for db_key in ["member_db", "live_db"]:
    db = data.get(db_key, {})
    for cid, card in db.items():
        for ab in card.get("abilities", []):
            bc = ab.get("bytecode", [])
            if not bc or bc == [1, 0, 0, 0, 0]:
                continue
            for i in range(0, len(bc), 5):
                op = bc[i]
                real_op = op - 1000 if op >= 1000 else op
                all_ops[real_op] = all_ops.get(real_op, 0) + 1

for op_id in sorted(all_ops.keys()):
    nm = OPCODE_NAMES.get(op_id, CONDITION_NAMES.get(op_id, f"UNK_{op_id}"))
    p(f"  {op_id:4d} {nm:35s} {all_ops[op_id]:4d} uses")

with open("reports/trace_impact.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("Done. Written to reports/trace_impact.txt")
