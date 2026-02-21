"""Audit all cards with LOOK_AND_CHOOSE (opcode 41) bytecode."""
import json

with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
    data = json.load(f)

print("=== ALL CARDS WITH O_LOOK_AND_CHOOSE (opcode 41) ===")
print(f"{'ID':>6} | {'Card No':<30} | {'Name':<20} | Trig | look pick  a       s  src      dest")
print("-" * 130)

count = 0
bug_count = 0
for db_name in ["member_db", "live_db"]:
    for cid, card in data.get(db_name, {}).items():
        for ab_idx, ab in enumerate(card.get("abilities", [])):
            bc = ab.get("bytecode", [])
            for i in range(0, len(bc), 4):
                if bc[i] == 41:  # O_LOOK_AND_CHOOSE
                    v = bc[i + 1] if i + 1 < len(bc) else 0
                    a = bc[i + 2] if i + 2 < len(bc) else 0
                    s = bc[i + 3] if i + 3 < len(bc) else 0

                    look_count = v & 0xFF
                    pick_count = (v >> 8) & 0xFF

                    # Decode source zone from s
                    src_map = {6: "HAND", 7: "DISCARD", 8: "DECK"}
                    src = src_map.get(s, f"DECK(s={s})")

                    # Decode destination from a bits
                    dest_bits = a & 0x07
                    if dest_bits & 0x01:
                        dest = "DISCARD"
                    elif dest_bits & 0x02:
                        dest = "DECK"
                    elif dest_bits & 0x04:
                        dest = "STAGE"
                    else:
                        dest = "HAND(default)"

                    trigger = ab.get("trigger", "?")
                    
                    is_bug = (s == 6)  # source=HAND when it should be DECK
                    marker = " *** BUG" if is_bug else ""
                    if is_bug:
                        bug_count += 1

                    print(
                        f"{cid:>6} | {card.get('card_no', '?'):<30} | {card.get('name', '?'):<20} | {trigger:>4} | "
                        f"look={look_count:<3} pick={pick_count:<3} a={a:#06x} s={s} src={src:<10} dest={dest}{marker}"
                    )
                    count += 1

print(f"\nTotal cards with LOOK_AND_CHOOSE: {count}")
print(f"Cards with s=6 (potential hand bug): {bug_count}")
