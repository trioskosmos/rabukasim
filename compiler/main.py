import os
import sys

# Add project root to path to allow imports if running as script
if __name__ == "__main__":
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import json

import numpy as np
from pydantic import TypeAdapter

# from compiler.parser import AbilityParser
from engine.models.ability import AbilityCostType, ConditionType, EffectType, TriggerType
from engine.models.card import EnergyCard, LiveCard, MemberCard
from engine.models.enums import CHAR_MAP
from engine.models.opcodes import Opcode


def compile_cards(input_path: str, output_path: str):
    print(f"Loading raw cards from {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    compiled_data = {"member_db": {}, "live_db": {}, "energy_db": {}, "meta": {"version": "1.0", "source": input_path}}

    sorted_keys = sorted(raw_data.keys())
    # Logic for bit-packed IDs
    # Bits 0-11: Logical ID (0-4095)
    # Bits 12-15: Variant Index (0-15)
    logical_id_map = {}  # (name, ability_text) -> logic_id
    logic_id_to_variant_count = {}  # logic_id -> next_variant_index
    next_logic_id = 0

    success_count = 0
    errors = []

    # Pre-create adapters
    member_adapter = TypeAdapter(MemberCard)
    live_adapter = TypeAdapter(LiveCard)
    energy_adapter = TypeAdapter(EnergyCard)

    processed_keys = set()

    for key in sorted_keys:
        if key in processed_keys:
            continue

        item = raw_data[key]
        ctype = item.get("type", "")

        # Collect variants from rare_list
        variants = [{"card_no": key, "name": item.get("name", ""), "data": item}]
        processed_keys.add(key)

        if "rare_list" in item and isinstance(item["rare_list"], list):
            for r in item["rare_list"]:
                v_no = r.get("card_no")
                if v_no and v_no != key:
                    # Create a variant that inherits base data but overrides metadata
                    if v_no in sorted_keys:
                        processed_keys.add(v_no)  # Mark variant as processed so main loop skips it

                    v_item = item.copy()
                    v_item.update(r)
                    variants.append({"card_no": v_no, "name": r.get("name", item.get("name", "")), "data": v_item})

        for v in variants:
            v_key = v["card_no"]
            v_data = v["data"]

            # Determine Logical Identity
            # We use Name + Original Text (Ability) as the unique logical key
            v_name = str(v_data.get("name", "Unknown"))
            v_ability = str(v_data.get("ability", ""))
            logic_key = (v_name, v_ability)

            if logic_key not in logical_id_map:
                logical_id_map[logic_key] = next_logic_id
                logic_id_to_variant_count[next_logic_id] = 0
                next_logic_id += 1

            logic_id = logical_id_map[logic_key]
            variant_idx = logic_id_to_variant_count[logic_id]
            logic_id_to_variant_count[logic_id] += 1

            # Pack ID: (variant << 12) | logic
            # Bits 0-11: Logical ID (0-4095)
            # Bits 12-15: Variant Index (0-15)

            if logic_id >= 4096:
                print(f"WARNING: Logic ID {logic_id} exceeds 12-bit limit (4096). Card: {v_key}")
            if variant_idx >= 16:
                print(f"WARNING: Variant Index {variant_idx} exceeds 4-bit limit (16). Card: {v_key}")

            packed_id = (variant_idx << 12) | logic_id

            print(f"DEBUG: Processing card_no={v_key}, packed_id={packed_id}")
            try:
                if ctype == "メンバー":
                    m_card = parse_member(packed_id, v_key, v_data)
                    compiled_item = member_adapter.dump_python(m_card, mode="json")
                    compiled_data["member_db"][str(packed_id)] = compiled_item
                elif ctype == "ライブ":
                    l_card = parse_live(packed_id, v_key, v_data)
                    compiled_data["live_db"][str(packed_id)] = live_adapter.dump_python(l_card, mode="json")
                else:
                    e_card = parse_energy(packed_id, v_key, v_data)
                    compiled_data["energy_db"][str(packed_id)] = energy_adapter.dump_python(e_card, mode="json")
                success_count += 1
            except Exception as e:
                import traceback

                traceback.print_exc()
                errors.append(f"Error parsing card {v_key}: {e}")

    print(f"Compilation complete. Processed {success_count} cards.")
    if errors:
        print(f"Encountered {len(errors)} errors. See compiler_errors.log for details.")
        with open("compiler_errors.log", "w", encoding="utf-8") as f_err:
            for err_msg in errors:
                f_err.write(f"- {err_msg}\n")

    # Write output
    print(f"Writing compiled data to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(compiled_data, f, ensure_ascii=False, indent=2)
    print("Done.")


def _resolve_img_path(data: dict) -> str:
    # Use cards_webp as the flattened source
    img_path = str(data.get("_img", ""))
    if img_path:
        filename = os.path.basename(img_path)
        if filename.lower().endswith(".png"):
            filename = filename[:-4] + ".webp"
        return f"cards_webp/{filename}"

    raw_url = str(data.get("img", ""))
    if raw_url:
        filename = os.path.basename(raw_url)
        if filename.lower().endswith(".png"):
            filename = filename[:-4] + ".webp"
        return f"cards_webp/{filename}"

    return raw_url


from compiler.parser_v2 import AbilityParserV2

COST_FLAG_TAP = 0x02

# Flag Constants (Matching Rust engine)
FLAG_DRAW = 1 << 0
FLAG_SEARCH = 1 << 1
FLAG_RECOVER = 1 << 2
FLAG_BUFF = 1 << 3
FLAG_CHARGE = 1 << 4
FLAG_TEMPO = 1 << 5
FLAG_REDUCE = 1 << 6
FLAG_BOOST = 1 << 7
FLAG_TRANSFORM = 1 << 8
FLAG_WIN_COND = 1 << 9
FLAG_MOVE = 1 << 10
FLAG_TAP = 1 << 11

CHOICE_FLAG_LOOK = 1 << 0
CHOICE_FLAG_MODE = 1 << 1
CHOICE_FLAG_COLOR = 1 << 2
CHOICE_FLAG_ORDER = 1 << 3

SYN_FLAG_GROUP = 1 << 0
SYN_FLAG_COLOR = 1 << 1
SYN_FLAG_BATON = 1 << 2
SYN_FLAG_CENTER = 1 << 3
SYN_FLAG_LIFE_LEAD = 1 << 4

COST_FLAG_DISCARD = 0x01


# Initialize parser globally
_v2_parser = AbilityParserV2()

# Load manual overrides
MANUAL_OVERRIDES_PATH = "data/manual_pseudocode.json"
_manual_overrides = {}
if os.path.exists(MANUAL_OVERRIDES_PATH):
    print(f"Loading manual overrides from {MANUAL_OVERRIDES_PATH}")
    with open(MANUAL_OVERRIDES_PATH, "r", encoding="utf-8") as f:
        _manual_overrides = json.load(f)

# Load manual translations
MANUAL_TRANSLATIONS_EN_PATH = "data/manual_translations_en.json"
_manual_translations_en = {}
if os.path.exists(MANUAL_TRANSLATIONS_EN_PATH):
    print(f"Loading manual English translations from {MANUAL_TRANSLATIONS_EN_PATH}")
    with open(MANUAL_TRANSLATIONS_EN_PATH, "r", encoding="utf-8") as f:
        _manual_translations_en = json.load(f)


def compute_flags(card):
    """Replicates Rust flag calculation logic in the Python compiler."""

    ability_flags = 0
    semantic_flags = 0
    synergy_flags = 0
    cost_flags = 0

    flagged_ops = {
        int(Opcode.DRAW): FLAG_DRAW,
        int(Opcode.LOOK_AND_CHOOSE): FLAG_DRAW,
        int(Opcode.RETURN): FLAG_DRAW,
        int(Opcode.SEARCH_DECK): FLAG_SEARCH,
        int(Opcode.RECOVER_LIVE): FLAG_RECOVER,
        int(Opcode.RECOVER_MEMBER): FLAG_RECOVER,
        int(Opcode.ADD_BLADES): FLAG_BUFF,
        int(Opcode.ADD_HEARTS): FLAG_BUFF,
        int(Opcode.MOVE_MEMBER): FLAG_MOVE,
        int(Opcode.SWAP_CARDS): FLAG_MOVE,
        int(Opcode.TAP_OPPONENT): FLAG_TAP,
        int(Opcode.TAP_MEMBER): FLAG_TAP,
        int(Opcode.ENERGY_CHARGE): FLAG_CHARGE,
        int(Opcode.ACTIVATE_MEMBER): FLAG_TEMPO,
        int(Opcode.SET_TAPPED): FLAG_TEMPO,
        int(Opcode.REDUCE_COST): FLAG_REDUCE,
        int(Opcode.BOOST_SCORE): FLAG_BOOST,
        int(Opcode.TRANSFORM_COLOR): FLAG_TRANSFORM,
        int(Opcode.REDUCE_HEART_REQ): FLAG_WIN_COND,
    }

    core_ops = {
        int(Opcode.DRAW),
        int(Opcode.RECOVER_MEMBER),
        int(Opcode.RECOVER_LIVE),
        int(Opcode.ADD_BLADES),
        int(Opcode.ADD_HEARTS),
        int(Opcode.SEARCH_DECK),
        int(Opcode.BOOST_SCORE),
        int(Opcode.ENERGY_CHARGE),
        int(Opcode.MOVE_MEMBER),
        int(Opcode.SWAP_CARDS),
        int(Opcode.TAP_OPPONENT),
        int(Opcode.MODIFY_SCORE_RULE),
        int(Opcode.REDUCE_COST),
        int(Opcode.REDUCE_HEART_REQ),
        int(Opcode.RETURN),
        int(Opcode.LOOK_AND_CHOOSE),
        int(Opcode.TAP_MEMBER),
        int(Opcode.ACTIVATE_MEMBER),
        int(Opcode.SET_TAPPED),
        int(Opcode.TRANSFORM_COLOR),
        int(Opcode.NOP),
        int(Opcode.RETURN),
        int(Opcode.JUMP),
        int(Opcode.JUMP_IF_FALSE),
        int(Opcode.META_RULE),
        int(Opcode.SELECT_MODE),
        int(Opcode.COLOR_SELECT),
        int(Opcode.ORDER_DECK),
        int(Opcode.MOVE_TO_DECK),
        int(Opcode.MOVE_TO_DISCARD),
        int(Opcode.PLAY_MEMBER_FROM_HAND),
    }

    for ab in card.abilities:
        # Semantic Flags
        if ab.trigger == TriggerType.ON_PLAY:
            semantic_flags |= 0x01
        if ab.trigger == TriggerType.ACTIVATED:
            semantic_flags |= 0x02
        if ab.trigger in [TriggerType.TURN_START, TriggerType.TURN_END]:
            semantic_flags |= 0x04
        if ab.is_once_per_turn:
            semantic_flags |= 0x08

        # Bytecode loop for Ability & Choice Flags
        unflagged_logic = False
        for i in range(0, len(ab.bytecode), 4):
            op = ab.bytecode[i]
            if op in flagged_ops:
                ability_flags |= flagged_ops[op]

            if op not in core_ops and op < 100:  # Opcode < 100 are effect opcodes
                unflagged_logic = True

            # Choice Flags
            if op == int(Opcode.LOOK_AND_CHOOSE):
                ab.choice_flags |= CHOICE_FLAG_LOOK
                if ab.choice_count == 0:
                    v = ab.bytecode[i + 1] if i + 1 < len(ab.bytecode) else 3
                    # Extract the high byte (pick count) as the choice count
                    pick_count = (v >> 8) & 0xFF
                    ab.choice_count = pick_count if pick_count > 0 else 3
            elif op == int(Opcode.SELECT_MODE):
                ab.choice_flags |= CHOICE_FLAG_MODE
                if ab.choice_count == 0:
                    ab.choice_count = ab.bytecode[i + 1] if i + 1 < len(ab.bytecode) else 2
            elif op == int(Opcode.COLOR_SELECT):
                ab.choice_flags |= CHOICE_FLAG_COLOR
                if ab.choice_count == 0:
                    ab.choice_count = 6
            elif op == int(Opcode.ORDER_DECK):
                ab.choice_flags |= CHOICE_FLAG_ORDER
                if ab.choice_count == 0:
                    ab.choice_count = 3

        if unflagged_logic:
            semantic_flags |= 0x10

        # Synergy Flags
        for c in ab.conditions:
            if c.type in [ConditionType.COUNT_GROUP, ConditionType.SELF_IS_GROUP]:
                synergy_flags |= SYN_FLAG_GROUP
            if c.type == ConditionType.HAS_COLOR:
                synergy_flags |= SYN_FLAG_COLOR
            if c.type == ConditionType.BATON:
                synergy_flags |= SYN_FLAG_BATON
            if c.type == ConditionType.IS_CENTER:
                synergy_flags |= SYN_FLAG_CENTER
            if c.type == ConditionType.LIFE_LEAD:
                synergy_flags |= SYN_FLAG_LIFE_LEAD

        # Cost Flags
        for cost in ab.costs:
            if cost.type in [AbilityCostType.DISCARD_HAND, AbilityCostType.DISCARD_MEMBER]:
                cost_flags |= COST_FLAG_DISCARD
            if cost.type in [AbilityCostType.TAP_SELF, AbilityCostType.TAP_MEMBER]:
                cost_flags |= COST_FLAG_TAP

    card.ability_flags = ability_flags
    card.semantic_flags = semantic_flags
    card.synergy_flags = synergy_flags
    if hasattr(card, "cost_flags"):
        card.cost_flags = cost_flags


def parse_member(card_id: int, card_no: str, data: dict) -> MemberCard:
    spec = data.get("special_heart", {})
    # Use manual override if present
    override_data = _manual_overrides.get(card_no, {})
    translation_en = _manual_translations_en.get(card_no)

    # Use manual pseudo/text if available, else raw data
    if "pseudocode" in override_data:
        raw_ability = str(override_data["pseudocode"])
    else:
        raw_ability = str(data.get("pseudocode", data.get("ability", "")))

    abilities = _v2_parser.parse(raw_ability)
    if "PL!S-bp2-005-P" in card_no:
        print(f"DEBUG: Processing {repr(card_no)}")
        print(f"DEBUG: In overrides? {card_no in _manual_overrides}")
        if card_no not in _manual_overrides:
            # Find close matches
            for k in _manual_overrides.keys():
                if "PL!S-bp2-005-P" in k:
                    print(f"DEBUG: Potential match in overrides: {repr(k)}")

        print(f"DEBUG: Parsing PL!S-bp2-005-P raw_ability:\n{raw_ability}")
        for ab in abilities:
            for eff in ab.effects:
                if eff.effect_type == 41:  # LOOK_AND_CHOOSE
                    print(f"DEBUG: Found LOOK_AND_CHOOSE in parser output. Params: {eff.params}")

    # --- GRANT_ABILITY FLATTENING ---
    extra_abilities = []
    for ab in abilities:
        for eff in ab.effects:
            if eff.effect_type == EffectType.GRANT_ABILITY:
                if "granted_ability_text" in eff.params:
                    inner_text = str(eff.params.pop("granted_ability_text"))
                    granted_abs = _v2_parser.parse(inner_text)
                    if granted_abs:
                        start_idx = len(abilities) + len(extra_abilities)
                        eff.value = start_idx
                        if "target_str" in eff.params:
                            del eff.params["target_str"]
                        extra_abilities.extend(granted_abs)
    abilities.extend(extra_abilities)
    # --------------------------------

    for ab in abilities:
        try:
            ab.bytecode = ab.compile()
        except Exception as e:
            print(f"Warning: Failed to compile bytecode for {card_no} ability: {e}")

    card = MemberCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Unknown")),
        cost=int(data.get("cost", 0)),
        hearts=parse_hearts(data.get("base_heart", {})),
        blade_hearts=parse_blade_hearts(data.get("blade_heart", {})),
        blades=int(data.get("blade", 0)),
        groups=data.get("series", ""),
        units=data.get("unit", ""),
        abilities=abilities,
        rare=str(override_data.get("rare", data.get("rare", "N"))),
        img_path=_resolve_img_path(data),
        ability_text=raw_ability,
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        volume_icons=int(spec.get("score", data.get("volume", 0))),
        draw_icons=int(spec.get("draw", data.get("draw", 0))),
        char_id=int(CHAR_MAP.get(str(data.get("name", "")), 0)),
        faq=data.get("faq", []),
    )
    compute_flags(card)
    return card


def parse_live(card_id: int, card_no: str, data: dict) -> LiveCard:
    spec = data.get("special_heart", {})
    # Use manual override if present
    override_data = _manual_overrides.get(card_no, {})
    translation_en = _manual_translations_en.get(card_no)
    # Prioritize 'pseudocode' over 'ability'
    raw_ability = str(override_data.get("pseudocode", data.get("pseudocode", data.get("ability", ""))))
    abilities = _v2_parser.parse(raw_ability)

    # --- GRANT_ABILITY FLATTENING ---
    extra_abilities = []
    for ab in abilities:
        for eff in ab.effects:
            if eff.effect_type == EffectType.GRANT_ABILITY:
                if "granted_ability_text" in eff.params:
                    inner_text = str(eff.params.pop("granted_ability_text"))
                    granted_abs = _v2_parser.parse(inner_text)
                    if granted_abs:
                        start_idx = len(abilities) + len(extra_abilities)
                        eff.value = start_idx
                        if "target_str" in eff.params:
                            del eff.params["target_str"]
                        extra_abilities.extend(granted_abs)
    abilities.extend(extra_abilities)
    # --------------------------------
    for ab in abilities:
        try:
            ab.bytecode = ab.compile()
        except Exception as e:
            print(f"Warning: Failed to compile bytecode for {card_no} ability: {e}")

    card = LiveCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Unknown")),
        score=int(data.get("score", 0)),
        required_hearts=parse_live_reqs(data.get("need_heart", {})),
        abilities=abilities,
        groups=data.get("series", ""),
        units=data.get("unit", ""),
        img_path=_resolve_img_path(data),
        ability_text=raw_ability,
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        volume_icons=int(spec.get("score", data.get("volume", 0))),
        draw_icons=int(spec.get("draw", data.get("draw", 0))),
        blade_hearts=parse_blade_hearts(data.get("blade_heart", {})),
        faq=data.get("faq", []),
        rare=str(override_data.get("rare", data.get("rare", "N"))),
    )
    compute_flags(card)
    return card


def parse_energy(card_id: int, card_no: str, data: dict) -> EnergyCard:
    translation_en = _manual_translations_en.get(card_no)
    return EnergyCard(
        card_id=card_id,
        card_no=card_no,
        name=str(data.get("name", "Energy")),
        img_path=_resolve_img_path(data),
        ability_text=str(data.get("ability", "")),
        original_text=str(data.get("ability", "")),
        original_text_en=str(translation_en) if translation_en else "",
        rare=str(data.get("rare", "N")),
    )


def parse_hearts(heart_dict: dict) -> np.ndarray:
    hearts = np.zeros(7, dtype=np.int32)
    if not heart_dict:
        return hearts
    for k, v in heart_dict.items():
        if k.startswith("heart"):
            try:
                num_str = k.replace("heart", "")
                if num_str == "0":  # Handle heart0 as ANY/STAR
                    hearts[6] = int(v)
                    continue
                idx = int(num_str) - 1
                if 0 <= idx < 6:
                    hearts[idx] = int(v)
            except ValueError:
                pass
        elif k in ["common", "any", "star"]:
            hearts[6] = int(v)
    return hearts


def parse_blade_hearts(heart_dict: dict) -> np.ndarray:
    hearts = np.zeros(7, dtype=np.int32)
    if not heart_dict:
        return hearts
    for k, v in heart_dict.items():
        if k == "b_all":
            hearts[6] = int(v)
        elif k.startswith("b_heart"):
            try:
                idx = int(k.replace("b_heart", "")) - 1
                if 0 <= idx < 6:
                    hearts[idx] = int(v)
            except ValueError:
                pass
    return hearts


def parse_live_reqs(req_dict: dict) -> np.ndarray:
    # Use parse_hearts directly as it now handles 7 elements correctly
    return parse_hearts(req_dict)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="data/cards.json", help="Path to raw cards.json")
    parser.add_argument("--output", default="data/cards_compiled.json", help="Output path")
    args = parser.parse_args()

    # Resolve paths relative to cwd if needed, or assume running from root
    compile_cards(args.input, args.output)

    # Copy to both data/ and engine/data/ for compatibility with all scripts
    import shutil

    root_data_path = os.path.join(os.getcwd(), "data", "cards_compiled.json")
    engine_data_path = os.path.join(os.getcwd(), "engine", "data", "cards_compiled.json")

    # Sync to root data/
    if os.path.abspath(args.output) != os.path.abspath(root_data_path):
        try:
            shutil.copy(args.output, root_data_path)
            print(f"Copied compiled data to {root_data_path}")
        except Exception as e:
            print(f"Warning: Failed to copy to root data directory: {e}")

    # Sync to engine/data/ to keep paths consistent
    try:
        os.makedirs(os.path.dirname(engine_data_path), exist_ok=True)
        shutil.copy(root_data_path, engine_data_path)
        print(f"Synced compiled data to {engine_data_path}")
    except Exception as e:
        print(f"Warning: Failed to sync to engine/data directory: {e}")
