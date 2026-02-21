import json
import re


def generate_strict_tests():
    # Load compiled data
    with open("engine/data/cards_compiled.json", "r", encoding="utf-8") as f:
        compiled_db = json.load(f)

    output_path = "engine/tests/cards/batches/test_auto_generated_strict_v2.py"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("import pytest\n")
        f.write("from engine.game.game_state import initialize_game\n")
        f.write("from engine.models.ability import ConditionType, EffectType, TriggerType\n\n")

        f.write("@pytest.fixture\n")
        f.write("def game():\n")
        f.write("    return initialize_game(deck_type='training')\n\n")

        count = 0

        def write_card_test(f, card_data, is_live=False):
            cno = card_data.get("card_no")
            abilities = card_data.get("abilities", [])

            # Skip vanilla
            if not abilities:
                return False

            # Only generate for cards with bytecode (valid parser output)
            if not any(ab.get("bytecode") for ab in abilities):
                return False

            # Robust sanitization for function name
            safe_cno = re.sub(r"[^a-zA-Z0-9_]", "_", cno)
            prefix = "live_" if is_live else ""
            func_name = f"test_strict_{prefix}{safe_cno}"
            db_name = "live_db" if is_live else "member_db"

            f.write(f"def {func_name}(game):\n")
            f.write(f'    cno = "{cno}"\n')
            f.write("    cid = None\n")
            f.write(f"    for k, v in game.{db_name}.items():\n")
            f.write("        if v.card_no == cno:\n")
            f.write("            cid = k\n")
            f.write("            break\n")
            f.write("    if cid is None:\n")
            f.write('        pytest.skip(f"{cno} not found in DB")\n\n')
            f.write(f"    card = game.{db_name}[cid]\n")
            f.write(f"    assert len(card.abilities) == {len(abilities)}, 'Ability count mismatch'\n\n")

            for i, ab in enumerate(abilities):
                f.write(f"    # Ability {i}\n")
                f.write(f"    ab{i} = card.abilities[{i}]\n")
                f.write(
                    f"    assert ab{i}.trigger == {ab['trigger']}, f'Trigger mismatch: {{ab{i}.trigger}} != {ab['trigger']}'\n"
                )

                conds = ab.get("conditions", [])
                f.write(f"    assert len(ab{i}.conditions) == {len(conds)}, 'Condition count mismatch'\n")
                for j, cond in enumerate(conds):
                    f.write(f"    assert ab{i}.conditions[{j}].type == {cond['type']}, 'Condition {j} type mismatch'\n")

                effs = ab.get("effects", [])
                f.write(f"    assert len(ab{i}.effects) == {len(effs)}, 'Effect count mismatch'\n")
                for j, eff in enumerate(effs):
                    f.write(
                        f"    assert ab{i}.effects[{j}].effect_type == {eff['effect_type']}, 'Effect {j} type mismatch'\n"
                    )
                    if isinstance(eff.get("value"), (int, float)):
                        f.write(f"    assert ab{i}.effects[{j}].value == {eff['value']}, 'Effect {j} value mismatch'\n")

                f.write("\n")

            f.write("\n")
            return True

        # Iterate members
        member_db = compiled_db.get("member_db", {})
        for mid in sorted(member_db.keys(), key=lambda x: int(x)):
            if write_card_test(f, member_db[mid], is_live=False):
                count += 1

        # Iterate lives
        live_db = compiled_db.get("live_db", {})
        for lid in sorted(live_db.keys(), key=lambda x: int(x)):
            if write_card_test(f, live_db[lid], is_live=True):
                count += 1

    print(f"Generated {count} tests in {output_path}")


if __name__ == "__main__":
    generate_strict_tests()
