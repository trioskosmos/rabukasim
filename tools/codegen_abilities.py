import json
import os

OPCODES = {
    1: " ",  # O_RETURN (skip)
    10: "draw_cards({p}, {v} as u32);",  # O_DRAW
    11: "players[{p}].blade_buffs[{s}] += {v};",  # O_BLADES
    12: "players[{p}].heart_buffs[{s}].add_to_color({a} as usize, {v} as i32);",  # O_HEARTS
    13: "players[{p}].cost_reduction += {v};",  # O_REDUCE_COST
    16: "players[{p}].live_score_bonus += {v};",  # O_BOOST
    18: "players[{p}].blade_buffs[{s}] += {v};",  # O_BUFF
    23: "draw_energy_cards({p}, {v});",  # O_CHARGE
    37: "players[{p}].score = {v} as u32;",  # O_SET_SCORE
    39: "players[{p}].color_transforms.push(({a} as u8, {s} as u8));",
    43: "set_member_tapped({p}, {s}, false);",  # O_ACTIVATE_MEMBER
    49: "players[{p}].live_score_bonus += {v};",  # O_MODIFY_SCORE_RULE
    51: "set_member_tapped({p}, {s}, true);",  # O_SET_TAPPED
    64: "pay_energy({p}, {v});",  # O_PAY_ENERGY
    81: "activate_energy({p}, {v});",  # O_ACTIVATE_ENERGY
}


def generate_rust():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    db_path = os.path.join(project_root, "data", "cards_compiled.json")
    out_path = os.path.join(project_root, "engine_rust_src", "src", "core", "hardcoded.rs")

    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)

    out = []
    out.append("// GENERATED CODE - DO NOT EDIT")
    out.append("use crate::core::logic::{GameState, CardDatabase, AbilityContext};")
    out.append("")
    out.append(
        "pub fn execute_hardcoded_ability(state: &mut GameState, _db: &CardDatabase, card_id: i32, ab_idx: usize, ctx: &AbilityContext) -> bool {"
    )
    out.append("    let p_idx = ctx.player_id as usize;")
    out.append("    match (card_id, ab_idx) {")

    count = 0
    for cid_str, card in db["member_db"].items():
        cid = int(cid_str)
        for i, ab in enumerate(card["abilities"]):
            bc = ab["bytecode"]
            if not bc:
                continue

            # Blacklist complex opcodes
            complex_ops = {
                14,
                15,
                17,
                19,
                20,
                21,
                22,
                24,
                25,
                26,
                27,
                28,
                30,
                31,
                32,
                33,
                34,
                35,
                36,
                38,
                40,
                41,
                42,
                44,
                45,
                46,
                47,
                48,
                50,
                52,
                53,
                57,
                58,
                60,
                61,
                62,
                63,
                66,
                69,
                70,
                72,
                74,
                75,
                76,
            }
            is_complex = any(op in complex_ops for op in bc[::4])
            if len(bc) > 24 or is_complex or 2 in bc[::4] or 3 in bc[::4]:
                continue

            rust_lines = []
            valid = True
            for j in range(0, len(bc), 4):
                op, v, a, s = bc[j : j + 4]
                if op == 0:
                    continue

                # Handle negations (mapped in resolve_bytecode as op + 1000)
                real_op = op
                if real_op >= 1000:
                    valid = False
                    break

                slot = "ctx.target_slot as usize" if s == 10 else f"{s} as usize"

                if real_op in OPCODES:
                    line = OPCODES[real_op].format(p="p_idx", v=v, a=a, s=slot)
                    rust_lines.append(line)
                    if real_op == 1:
                        break
                else:
                    valid = False
                    break

            if valid and rust_lines:
                out.append(f"        ({cid}, {i}) => {{")
                for line in rust_lines:
                    line = line.strip()
                    if not line:
                        continue
                    out.append(f"            state.{line}")
                out.append("            true")
                out.append("        },")
                count += 1

    out.append("        _ => false,")
    out.append("    }")
    out.append("}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"Generated hardcoded logic for {count} abilities.")


if __name__ == "__main__":
    generate_rust()
