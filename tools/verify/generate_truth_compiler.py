import json
import multiprocessing
import os
import sys

# Force UTF-8 for Windows consoles (Python 3.7+)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path to import compiler and engine models
sys.path.append(os.getcwd())

from compiler.parser_v2 import AbilityParserV2
from engine.models.ability import AbilityCostType, EffectType


class CompilerTruthOracle:
    def __init__(self):
        self.parser = AbilityParserV2()
        with open("data/manual_pseudocode.json", "r", encoding="utf-8") as f:
            self.manual_pseudocode = json.load(f)
        with open("data/cards.json", "r", encoding="utf-8") as f:
            self.db = json.load(f)

    def map_effect_to_deltas(self, effect, tag_prefix=""):
        deltas = []
        if not hasattr(effect, "effect_type"):
            return deltas

        etype = effect.effect_type
        val = effect.value

        if etype == EffectType.DRAW:
            deltas.append({"tag": tag_prefix + "HAND_DELTA", "value": val})
        elif etype == EffectType.MOVE_TO_DISCARD:
            src = effect.params.get("source", "HAND").upper()
            if src == "HAND":
                deltas.append({"tag": tag_prefix + "HAND_DISCARD", "value": val})
            elif src == "STAGE":
                deltas.append({"tag": tag_prefix + "STAGE_DELTA", "value": -val})
                deltas.append({"tag": tag_prefix + "DISCARD_DELTA", "value": val})
        elif etype == EffectType.BOOST_SCORE:
            deltas.append({"tag": tag_prefix + "SCORE_DELTA", "value": val})
        elif etype == EffectType.ADD_HEARTS:
            deltas.append({"tag": tag_prefix + "HEART_DELTA", "value": val})
        elif etype == EffectType.ADD_BLADES:
            deltas.append({"tag": tag_prefix + "BLADE_DELTA", "value": val})
        elif etype == EffectType.RECOVER_MEMBER:
            deltas.append({"tag": tag_prefix + "HAND_DELTA", "value": val})
            deltas.append({"tag": tag_prefix + "DISCARD_DELTA", "value": -val})
        elif etype == EffectType.RECOVER_LIVE:
            deltas.append({"tag": tag_prefix + "LIVE_RECOVER", "value": val})
        elif etype in [EffectType.ENERGY_CHARGE, EffectType.ACTIVATE_ENERGY, EffectType.ACTIVATE_MEMBER]:
            deltas.append({"tag": tag_prefix + "ENERGY_DELTA", "value": val})
        elif etype == EffectType.PAY_ENERGY:
            deltas.append({"tag": tag_prefix + "ENERGY_COST", "value": val})
        elif etype in [EffectType.TAP_MEMBER, EffectType.TAP_OPPONENT]:
            # NOTE: val=99 represents "All"
            deltas.append({"tag": tag_prefix + "MEMBER_TAP_DELTA", "value": val})
        elif etype in [
            EffectType.PREVENT_ACTIVATE,
            EffectType.PREVENT_BATON_TOUCH,
            EffectType.RESTRICTION,
            EffectType.PREVENT_PLAY_TO_SLOT,
        ]:
            deltas.append({"tag": tag_prefix + "ACTION_PREVENTION", "value": 1})
        elif etype in [
            EffectType.LOOK_AND_CHOOSE,
            EffectType.SEARCH_DECK,
            EffectType.ORDER_DECK,
            EffectType.REVEAL_CARDS,
            EffectType.LOOK_DECK,
        ]:
            deltas.append({"tag": tag_prefix + "DECK_SEARCH", "value": 1})
        elif etype == EffectType.SWAP_CARDS:
            deltas.append({"tag": tag_prefix + "HAND_DISCARD", "value": val})
            deltas.append({"tag": tag_prefix + "HAND_DELTA", "value": val})
        elif etype == EffectType.ADD_TO_HAND:
            deltas.append({"tag": tag_prefix + "HAND_DELTA", "value": val})
        elif etype in [EffectType.SELECT_MODE, EffectType.SELECT_PLAYER]:
            # RECURSIVE MAPPING for modal options
            if hasattr(effect, "modal_options"):
                for opt_list in effect.modal_options:
                    for sub_etype in opt_list:
                        if isinstance(sub_etype, (list, tuple)):
                            for sub_eff in sub_etype:
                                deltas.extend(self.map_effect_to_deltas(sub_eff, tag_prefix))
                        else:
                            deltas.extend(self.map_effect_to_deltas(sub_etype, tag_prefix))
        elif etype in [
            EffectType.BUFF_POWER,
            EffectType.TRANSFORM_COLOR,
            EffectType.TRANSFORM_HEART,
            EffectType.GRANT_ABILITY,
            EffectType.SELECT_MEMBER,
        ]:
            deltas.append({"tag": tag_prefix + "STATE_CHANGE", "value": 1})
        elif etype == EffectType.PLAY_MEMBER_FROM_HAND:
            deltas.append({"tag": tag_prefix + "STAGE_DELTA", "value": 1})
            deltas.append({"tag": tag_prefix + "HAND_DELTA", "value": -1})

        return deltas

    def map_cost_to_deltas(self, cost):
        ctype = cost.type
        val = cost.value or 1
        deltas = []

        if ctype == AbilityCostType.ENERGY or ctype == AbilityCostType.PAY_ENERGY:
            deltas.append({"tag": "COST_ENERGY_DELTA", "value": val})
        elif ctype == AbilityCostType.DISCARD_HAND:
            deltas.append({"tag": "COST_HAND_DISCARD", "value": val})
        elif ctype == AbilityCostType.TAP_SELF or ctype == AbilityCostType.TAP_MEMBER:
            deltas.append({"tag": "COST_MEMBER_TAP_DELTA", "value": 1})
        elif ctype == AbilityCostType.SACRIFICE_SELF or ctype == AbilityCostType.MOVE_TO_DISCARD:
            deltas.append({"tag": "COST_STAGE_DELTA", "value": -1})
            deltas.append({"tag": "COST_DISCARD_DELTA", "value": 1})

        return deltas

    def interpret_card(self, card_id):
        # Prioritize manual pseudocode if available
        text = ""
        source = "JP_TEXT"
        if card_id in self.manual_pseudocode:
            text = self.manual_pseudocode[card_id].get("pseudocode", "")
            source = "PSEUDOCODE"

        if not text:
            # Fallback to Japanese text
            text = self.db.get(card_id, {}).get("ability", "")

        if not text:
            return None, "NO_TEXT", source

        try:
            abilities = self.parser.parse(text)
        except Exception as e:
            return None, f"PARSER_ERROR: {e}", source

        if not abilities:
            return None, "EMPTY_ABILITIES", source

        unmapped_types = []
        card_expectations = []
        for ability in abilities:
            sequence = []

            # Use instructions to maintain order if V2.1+ parser
            items = ability.instructions if hasattr(ability, "instructions") and ability.instructions else []
            if not items:
                # Fallback to split lists if instructions empty
                items = ability.conditions + ability.costs + ability.effects

            for item in items:
                deltas = []
                from engine.models.ability import Cost, Effect

                if isinstance(item, Cost):
                    deltas = self.map_cost_to_deltas(item)
                elif isinstance(item, Effect):
                    deltas = self.map_effect_to_deltas(item)
                    if not deltas:
                        unmapped_types.append(
                            item.effect_type.name if hasattr(item.effect_type, "name") else item.effect_type
                        )

                if deltas:
                    instr_text = f"{item}"
                    if isinstance(item, Effect):
                        instr_text = f"EFFECT: {item.effect_type.name}({item.value})"
                    elif isinstance(item, Cost):
                        instr_text = f"COST: {item.type.name}({item.value})"

                    sequence.append({"text": instr_text, "deltas": deltas})

            if sequence:
                card_expectations.append({"trigger": ability.trigger.name, "sequence": sequence})

        if not card_expectations:
            # Check if it was because we have no mapped deltas
            msg = f"NO_MAPPED_DELTAS: {list(set(unmapped_types))}" if unmapped_types else "NO_TRACEABLE_ITEMS"
            return None, msg, source

        return {"id": card_id, "abilities": card_expectations}, "SUCCESS", source


def worker(card_id):
    # Oracle is light, but parser might have state?
    # AbilityParserV2 uses get_registry() which is cached globally.
    oracle = CompilerTruthOracle()
    return oracle.interpret_card(card_id)


def run_extraction():
    oracle = CompilerTruthOracle()  # For initial card list
    card_ids = list(oracle.db.keys())
    total = len(card_ids)

    print(f"Extraction for {total} cards using all ({multiprocessing.cpu_count()}) cores...")

    with multiprocessing.Pool() as pool:
        results = pool.map(worker, card_ids)

    truth_db = {}
    skipped = {}

    # Results is [(interp, status, source), ...] for each card_id
    id_to_res = {cid: res for cid, res in zip(card_ids, results)}

    for cid, (interp, status, source) in id_to_res.items():
        if interp and interp["abilities"]:
            truth_db[cid] = interp
        else:
            if status not in skipped:
                skipped[status] = []
            skipped[status].append(cid)

    # Cross reference with manual_pseudocode to see why we are missing those 769
    pc_ids = set(oracle.manual_pseudocode.keys())
    found_ids = set(truth_db.keys())
    missing_pc = pc_ids - found_ids

    print("\n--- Skip Summary ---")
    for status, cids in sorted(skipped.items()):
        print(f"   {status}: {len(cids)}")

    print("\n--- Discrepancy Analysis ---")
    print(f"   Manual Pseudocode Cards: {len(pc_ids)}")
    print(f"   Extracted Traceable Cards: {len(found_ids)}")
    print(f"   Missing from Pseudocode: {len(missing_pc)}")

    # Categorize missing_pc by status
    missing_by_status = {}
    for cid in missing_pc:
        res = id_to_res.get(cid)
        status = res[1] if res else "NOT_IN_DB"
        if status not in missing_by_status:
            missing_by_status[status] = []
        missing_by_status[status].append(cid)

    print("\n--- Missing Cards by Category ---")
    for status, cids in sorted(missing_by_status.items()):
        print(f"   {status}: {len(cids)}")
        if status != "NOT_IN_DB":
            print(f"     Sample: {sorted(cids)[:10]}")

    with open("reports/semantic_truth.json", "w", encoding="utf-8") as f:
        json.dump(truth_db, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Truth set generated with {len(truth_db)} entries.")


if __name__ == "__main__":
    run_extraction()
