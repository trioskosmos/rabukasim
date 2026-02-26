# -*- coding: utf-8 -*-
"""Quick audit of ability system health metrics."""
import json

# Cards compiled
with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# Metadata
with open("data/metadata.json", "r", encoding="utf-8") as f:
    meta = json.load(f)

total_cards = 0
cards_with_ab = 0
total_ab = 0
empty_bc = 0
has_bc = 0

used_opcodes = set()
used_conditions = set()
used_triggers = set()

for db_key in ["member_db", "live_db"]:
    db = data.get(db_key, {})
    for cid, card in db.items():
        total_cards += 1
        abilities = card.get("abilities", [])
        if not abilities:
            continue
        cards_with_ab += 1
        for a in abilities:
            total_ab += 1
            bc = a.get("bytecode")
            if not bc or bc == [1, 0, 0, 0, 0]:
                empty_bc += 1
            else:
                has_bc += 1
                for i in range(0, len(bc), 4):
                    if i < len(bc):
                        op = bc[i]
                        if op >= 200:
                            used_conditions.add(op)
                        elif 1 <= op < 200:
                            used_opcodes.add(op)

            trig = a.get("trigger")
            if trig is not None:
                used_triggers.add(trig)

opcode_names = {v: k for k, v in meta["opcodes"].items()}
cond_names = {v: k for k, v in meta["conditions"].items()}
trigger_names = {v: k for k, v in meta["triggers"].items()}

defined_opcodes = set(meta["opcodes"].values()) - {0, 1, 2, 3}
defined_conditions = set(meta["conditions"].values())
real_used_opcodes = used_opcodes - {0, 1, 2, 3}

unused_opcodes = defined_opcodes - real_used_opcodes
unused_conditions = defined_conditions - used_conditions

print("=" * 60)
print("ABILITY SYSTEM HEALTH REPORT")
print("=" * 60)
print()
print(f"Total cards in database:       {total_cards}")
print(f"Cards with abilities:          {cards_with_ab}")
print(f"Total abilities:               {total_ab}")
print(f"Abilities with valid bytecode: {has_bc}")
print(f"Empty/stub bytecodes:          {empty_bc}")
print(f"Bytecode coverage:             {has_bc}/{total_ab} ({100*has_bc/total_ab:.1f}%)")
print()
print(f"--- Opcode Usage ---")
print(f"Defined effect opcodes:        {len(defined_opcodes)}")
print(f"Used in compiled cards:        {len(real_used_opcodes)}")
print(f"Opcode utilization:            {len(real_used_opcodes)}/{len(defined_opcodes)} ({100*len(real_used_opcodes)/len(defined_opcodes):.0f}%)")
if unused_opcodes:
    print(f"\nUnused opcodes ({len(unused_opcodes)}):")
    for op in sorted(unused_opcodes):
        print(f"  {op:3d} = {opcode_names.get(op, '???')}")

print()
print(f"--- Condition Usage ---")
print(f"Defined conditions:            {len(defined_conditions)}")
print(f"Used in compiled cards:        {len(used_conditions)}")
print(f"Condition utilization:         {len(used_conditions)}/{len(defined_conditions)} ({100*len(used_conditions)/len(defined_conditions):.0f}%)")
if unused_conditions:
    print(f"\nUnused conditions ({len(unused_conditions)}):")
    for c in sorted(unused_conditions):
        print(f"  {c:3d} = {cond_names.get(c, '???')}")

print()
print(f"--- Trigger Usage ---")
for t in sorted(used_triggers):
    print(f"  {t} = {trigger_names.get(t, '???')}")

print()
print(f"--- Metadata Totals ---")
print(f"Effect opcodes (defined):      {len(meta['opcodes'])}")
print(f"Conditions (defined):          {len(meta['conditions'])}")
print(f"Triggers (defined):            {len(meta['triggers'])}")
print(f"Targets (defined):             {len(meta['targets'])}")
print(f"Cost types (defined):          {len(meta['costs'])}")
