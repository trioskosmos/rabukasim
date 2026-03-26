import copy
import re
from typing import Any, Dict, List, Tuple, Union

from engine.models.enums import CHAR_MAP, Unit, Group, HeartColor
from engine.models.ability import Condition, Cost, Effect
from engine.models.opcodes import Opcode
from engine.models.ability_filter import PackedFilterSpec
from engine.models.generated_enums import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType
from engine.models.generated_metadata import (
    COMPARISONS, 
    COUNT_SOURCES, 
    EXTRA_CONSTANTS, 
    HEART_COLOR_MAP, 
    META_RULE_TYPES, 
    ZONES,
    CHARACTER_IDS
)
from engine.models.generated_packer import (
    pack_a_heart_cost,
    pack_s_standard,
    pack_v_heart_counts,
    pack_v_look_choose,
    pack_v_scalar_dynamic,
)

def to_signed_32(x):
    """Utility to convert an integer to a signed 32-bit integer."""
    x = int(x) & 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x

class AbilityCompiler:
    def __init__(self):
        self._last_counted_zone = None
        self.filters = []

    def _is_effect_instruction(self, instr: Any) -> bool:
        return hasattr(instr, "effect_type")

    def _is_condition_instruction(self, instr: Any) -> bool:
        return hasattr(instr, "is_negated") and hasattr(instr, "type") and not hasattr(instr, "effect_type")

    def _is_cost_instruction(self, instr: Any) -> bool:
        return hasattr(instr, "type") and not hasattr(instr, "effect_type") and not hasattr(instr, "is_negated")

    def compile_to_frames(self, ability) -> List[Union[str, Dict[str, Any]]]:
        return self._build_frame_program_from_source(ability)

    def _frame_program_frames(self, frame_program: Any) -> list[Any]:
        if isinstance(frame_program, dict):
            frames = frame_program.get("frames", [])
        else:
            frames = frame_program

        if not isinstance(frames, list):
            return []

        return [copy.deepcopy(frame) for frame in frames]

    def _hydrate_instruction_frames(self, ability) -> list[Union[Effect, Condition, Cost]]:
        instructions = copy.deepcopy(list(getattr(ability, "instructions", []) or []))
        if not instructions:
            instructions = [
                *copy.deepcopy(getattr(ability, "costs", []) or []),
                *copy.deepcopy(getattr(ability, "conditions", []) or []),
                *copy.deepcopy(getattr(ability, "effects", []) or []),
            ]

        trigger = getattr(ability, "trigger", TriggerType.NONE)
        for instr in instructions:
            if self._is_condition_instruction(instr):
                # CONSTANT abilities keep conditions out of emitted bytecode, but
                # the frame export still needs hydrated condition metadata.
                self._compile_single_condition(instr, [])
            elif self._is_effect_instruction(instr):
                self._compile_single_effect(instr, [])
            elif self._is_cost_instruction(instr):
                self._compile_single_cost(instr, [])

        if trigger == TriggerType.CONSTANT:
            return instructions

        return instructions

    def _build_frame_program_from_source(self, ability) -> List[Union[str, Dict[str, Any]]]:
        existing_frame_program = getattr(ability, "frame_program", None)
        frames = self._frame_program_frames(existing_frame_program)
        if frames:
            return frames

        sparse_frame_index = getattr(ability, "sparse_frame_index", None)
        frames = self._frame_program_frames(sparse_frame_index)
        if frames:
            return frames

        instructions = self._hydrate_instruction_frames(ability)

        frames_out: list[Union[str, Dict[str, Any]]] = []
        for instr in instructions:
            frame = self._instruction_to_frame(instr)
            if frame:
                frames_out.append(frame)

        if not frames_out or frames_out[-1] != "Return":
            frames_out.append("Return")
        return frames_out

    def compile_to_bytecode(self, ability) -> List[int]:
        return []


    def _compile_all_players_block(self, bytecode, block, last_target):
        last_target = self._emit_target_opcode_if_needed(bytecode, TargetType.PLAYER, last_target)
        for eff in block:
            e_self = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.PLAYER, eff.params.copy())
            e_self.is_optional = eff.is_optional
            self._compile_single_effect(e_self, bytecode)
        last_target = self._emit_target_opcode_if_needed(bytecode, TargetType.OPPONENT, last_target)
        for eff in block:
            e_opp = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.OPPONENT, eff.params.copy())
            e_opp.is_optional = eff.is_optional
            self._compile_single_effect(e_opp, bytecode)
        return last_target

    def _emit_target_opcode_if_needed(self, bc, target, last):
        desired = TargetType.PLAYER if target in (TargetType.SELF, TargetType.PLAYER) else TargetType.OPPONENT
        if desired == last: return last
        op = Opcode.SET_TARGET_SELF if desired == TargetType.PLAYER else Opcode.SET_TARGET_OPPONENT
        bc.extend([int(op), 0, 0, 0, 0])
        return desired

    def _compile_effect_with_target_persistence(self, eff, bc, last):
        if eff.target == TargetType.ALL_PLAYERS: return self._compile_all_players_block(bc, [eff], last)
        next_t = self._emit_target_opcode_if_needed(bc, eff.target, last) if last is not None else None
        self._compile_single_effect(eff, bc)
        return next_t if eff.target in (TargetType.SELF, TargetType.PLAYER, TargetType.OPPONENT) else None

    # --- Massive packing logic starts here ---
    def _pack_filter_attr(self, source):
        return self._pack_filter_attr_with_obj(source)[0]

    def _pack_filter_attr_with_obj(self, source) -> Tuple[int, Dict[str, Any]]:
        from engine.models.enums import Group, HeartColor, Unit

        params = source.params if hasattr(source, "params") else (source if isinstance(source, dict) else {})
        params_upper = {str(k).upper(): v for k, v in params.items() if isinstance(k, str)}
        raw_filter_str = str(params.get("filter") or params_upper.get("FILTER") or "")
        filter_str = raw_filter_str.upper()

        filter_obj = {
            "target_player": 0,
            "card_type": 0,
            "group_enabled": False,
            "group_id": 0,
            "is_tapped": False,
            "has_blade_heart": False,
            "not_has_blade_heart": False,
            "unique_names": False,
            "unit_enabled": False,
            "unit_id": 0,
            "value_enabled": False,
            "value_threshold": 0,
            "is_le": False,
            "is_cost_type": False,
            "color_mask": 0,
            "char_id_1": 0,
            "char_id_2": 0,
            "zone_mask": 0,
            "special_id": 0,
            "is_setsuna": False,
            "compare_accumulated": False,
            "is_optional": False,
            "keyword_energy": False,
            "keyword_member": False,
        }

        # 1. Player Target (Bits 0-1)
        if hasattr(source, "target") and source.target == TargetType.OPPONENT:
            filter_obj["target_player"] = 2
        elif params_upper.get("OPPONENT") or "STATUS=OPPONENT" in filter_str:
            filter_obj["target_player"] = 2
        elif hasattr(source, "target") and source.target == TargetType.SELF:
            filter_obj["target_player"] = 1

        # 2. Card Type (Bits 2-3: 0=Any, 1=Member, 2=Live)
        ctype = str(params.get("type", "")).lower()
        if not ctype:
            # Infer from filter string
            if "TYPE=LIVE" in filter_str or "LIVE_SET" in filter_str:
                ctype = "live"
            elif "TYPE=MEMBER" in filter_str:
                ctype = "member"

        if "live" in ctype:
            filter_obj["card_type"] = 2
        elif "member" in ctype:
            filter_obj["card_type"] = 1

        # 3. Group Filter (Bits 4-5 Enabled + Bits 6-11 ID)
        group_val = params.get("group") or params_upper.get("GROUP")
        if not group_val and "GROUP=" in filter_str:
            m = re.search(r"GROUP=([A-Z_]+)", filter_str)
            if m:
                group_val = m.group(1)

        if group_val:
            try:
                g_idx = int(Group[str(group_val).upper()])
                filter_obj["group_enabled"] = True
                filter_obj["group_id"] = g_idx & 0x3F
            except (KeyError, TypeError, ValueError):
                pass

        # 4. Unit Filter (Bits 16-17 Enabled + Bits 18-24 ID)
        unit_val = params.get("unit") or params_upper.get("UNIT")
        if not unit_val and "UNIT=" in filter_str:
            m = re.search(r"UNIT=([A-Z_]+)", filter_str)
            if m:
                unit_val = m.group(1)

        if unit_val:
            try:
                u_idx = int(Unit[str(unit_val).upper()])
                filter_obj["unit_enabled"] = True
                filter_obj["unit_id"] = u_idx & 0x7F
            except (KeyError, TypeError, ValueError):
                pass

        # 5. Value/Cost Threshold (Bits 25-29 Threshold + Bit 30=LE/GE + Bit 31=Type=1)
        c_min = params.get("min_cost") or params.get("cost_ge") or params_upper.get("COST_GE")
        c_max = params.get("max_cost") or params.get("cost_le") or params_upper.get("COST_LE")
        f_val = 0
        sid = 0
        colors = params.get("color") or params.get("heart_type") or params_upper.get("COLOR")

        if not c_min and "COST_GE=" in filter_str:
            m = re.search(r"COST_GE=(\d+)", filter_str)
            if m:
                c_min = m.group(1)
        if not c_max and "COST_LE=" in filter_str:
            m = re.search(r"COST_LE=(\d+)", filter_str)
            if m:
                c_max = m.group(1)

        if "COST_LT_TARGET_VAL" in filter_str:
            filter_obj["value_enabled"] = True
            filter_obj["is_le"] = True
            filter_obj["compare_accumulated"] = True
            filter_obj["is_cost_type"] = True
        elif "COST_EQ=BASE_COST+" in filter_str:
            m = re.search(r"COST_EQ=BASE_COST\+(\d+)", filter_str)
            if m:
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = int(m.group(1)) & 0x1F
                filter_obj["compare_accumulated"] = True
                filter_obj["is_cost_type"] = True
                filter_obj["special_id"] = 5
        elif "COST_EQ_TARGET_PLUS_" in filter_str:
            m = re.search(r"COST_EQ_TARGET_PLUS_(\d+)", filter_str)
            if m:
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = int(m.group(1)) & 0x1F
                filter_obj["compare_accumulated"] = True
                filter_obj["is_cost_type"] = True
                filter_obj["special_id"] = 5
        elif c_min is not None:
            try:
                val_c = int(c_min)
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = val_c & 0x1F
                filter_obj["is_cost_type"] = True
                filter_obj["is_le"] = False
            except (TypeError, ValueError):
                pass
        elif c_max is not None:
            try:
                val_c = int(c_max)
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = val_c & 0x1F
                filter_obj["is_cost_type"] = True
                filter_obj["is_le"] = True
            except (TypeError, ValueError):
                pass

        # 5.1 Heart Sum Support
        sum_ge = params.get("sum_heart_total_ge") or params_upper.get("SUM_HEART_TOTAL_GE")
        sum_le = params.get("sum_heart_total_le") or params_upper.get("SUM_HEART_TOTAL_LE")
        if not sum_ge and "SUM_HEART_TOTAL_GE=" in filter_str:
            m = re.search(r"SUM_HEART_TOTAL_GE=(\d+)", filter_str)
            if m:
                sum_ge = m.group(1)
        if not sum_le and "SUM_HEART_TOTAL_LE=" in filter_str:
            m = re.search(r"SUM_HEART_TOTAL_LE=(\d+)", filter_str)
            if m:
                sum_le = m.group(1)
        if sum_ge is not None:
            filter_obj["value_enabled"] = True
            filter_obj["value_threshold"] = int(sum_ge) & 0x1F
            filter_obj["is_cost_type"] = False
            filter_obj["is_le"] = False
        elif sum_le is not None:
            filter_obj["value_enabled"] = True
            filter_obj["value_threshold"] = int(sum_le) & 0x1F
            filter_obj["is_cost_type"] = False
            filter_obj["is_le"] = True

        # 6. Character Filter
        names = params.get("name") or params_upper.get("NAME")
        if not names and "NAME=" in filter_str:
            m = re.search(r"NAME=([^,]+)", raw_filter_str, re.IGNORECASE)
            if m:
                names = m.group(1)
        if not names and "NAME_IN=[" in filter_str:
            names = re.findall(r"'([^']+)'", raw_filter_str)
        if not names and raw_filter_str and "/" in raw_filter_str and "=" not in raw_filter_str:
            names = raw_filter_str

        if names:
            n_list = names if isinstance(names, (list, tuple)) else str(names).split("/")
            for i, n in enumerate(n_list[:3]):
                try:
                    n_norm = n.strip().replace(" ", "").replace("驍ｵ・ｲ・つ€", "")
                    c_id = 0
                    for k, cid in CHAR_MAP.items():
                        if k.replace(" ", "").replace("驍ｵ・ｲ・つ€", "") == n_norm:
                            c_id = cid
                            break
                    if c_id == 0:
                        c_id = int(CHARACTER_IDS.get(n_norm.upper(), 0))
                    if c_id > 0:
                        if i < 2:
                            filter_obj[f"char_id_{i + 1}"] = c_id & 0x7F
                        elif not filter_obj["unit_enabled"]:
                            filter_obj["unit_id"] = c_id & 0x7F
                except:
                    pass

        # 7. Heart Value and Color Filter
        if "HAS_HEART_" in filter_str:
            match = re.search(r"HAS_HEART_(\d+)(?:_X(\d+))?", filter_str)
            if match:
                color_code = match.group(1)
                count = match.group(2)
                try:
                    c_idx = int(color_code)
                    if not colors:
                        colors = [c_idx]
                    if count:
                        f_val = int(count)
                except (TypeError, ValueError):
                    pass
        elif "HAS_COLOR_" in filter_str:
            match = re.search(r"HAS_COLOR_([A-Z]+)(?:_X(\d+))?", filter_str)
            if match:
                color_name = match.group(1).upper()
                count = match.group(2)
                try:
                    c_idx = int(HeartColor[color_name])
                    if not colors:
                        colors = [c_idx]
                    if count:
                        f_val = int(count)
                except (KeyError, TypeError, ValueError):
                    pass

        if f_val > 0:
            filter_obj["value_enabled"] = True
            filter_obj["value_threshold"] = f_val & 0x1F
            filter_obj["is_cost_type"] = False

        if colors or "COLOR=" in filter_str:
            color_mask = 0
            for c in colors if isinstance(colors, list) else [colors]:
                if c is None:
                    continue
                try:
                    if isinstance(c, str):
                        c_idx = int(c) if c.isdigit() else int(HeartColor[c.upper()])
                    else:
                        c_idx = int(c)
                    color_mask |= 1 << c_idx
                except (KeyError, TypeError, ValueError):
                    pass
            if color_mask > 0:
                filter_obj["color_mask"] = color_mask & 0x7F

        # 8. Meta Flags
        zone_val = params.get("zone") or params.get("source") or params_upper.get("ZONE")
        if zone_val:
            z_str = str(zone_val).upper()
            z_mask = 0
            if "STAGE" in z_str:
                z_mask = int(EXTRA_CONSTANTS.get("ZONE_MASK_STAGE", 4))
            elif "HAND" in z_str:
                z_mask = int(EXTRA_CONSTANTS.get("ZONE_MASK_HAND", 6))
            elif "DISCARD" in z_str:
                z_mask = int(EXTRA_CONSTANTS.get("ZONE_MASK_DISCARD", 7))
            if z_mask > 0:
                filter_obj["zone_mask"] = z_mask & 0x07

        if not sid and "NOT_TARGET" in filter_str:
            sid = 7
        elif not sid and "NOT_SELF" in filter_str:
            sid = 3
        elif not sid and "SAME_NAME_AS_REVEALED" in filter_str:
            sid = 4
        elif not sid and "SELECTED_DISCARD" in filter_str:
            sid = 6

        if sid:
            try:
                filter_obj["special_id"] = int(sid) & 0x07
            except (TypeError, ValueError):
                pass

        if params.get("is_setsuna") or params_upper.get("IS_SETSUNA") or (names and "SETSUNA" in str(names).upper()):
            filter_obj["is_setsuna"] = True

        if getattr(source, "is_optional", False) or params.get("is_optional") or "(Optional)" in str(params.get("pseudocode", "")):
            filter_obj["is_optional"] = True

        keyword = str(params.get("keyword") or params.get("filter") or "").upper()
        if params.get("KEYWORD_ENERGY") or "ACTIVATED_ENERGY" in keyword or "DID_ACTIVATE_ENERGY" in keyword:
            filter_obj["keyword_energy"] = True
        if params.get("KEYWORD_MEMBER") or "ACTIVATED_MEMBER" in keyword or "DID_ACTIVATE_MEMBER" in keyword:
            filter_obj["keyword_member"] = True

        if params.get("is_tapped") or "STATUS=TAPPED" in filter_str or "STATUS=TAP" in filter_str:
            filter_obj["is_tapped"] = True
        
        bh = params.get("has_blade_heart")
        if bh is True or "HAS_BLADE_HEART" in filter_str:
            filter_obj["has_blade_heart"] = True
        elif bh is False or "NOT_HAS_BLADE_HEART" in filter_str:
            filter_obj["not_has_blade_heart"] = True
        
        if params.get("UNIQUE_NAMES") or params_upper.get("UNIQUE_NAMES") or "UNIQUE_NAMES" in filter_str:
            filter_obj["unique_names"] = True

        spec = PackedFilterSpec(**filter_obj)
        self.filters.append(spec.to_debug_dict())
        return spec.pack(), spec.to_debug_dict()

    def _compile_single_condition(self, cond: Condition, bytecode: List[int]):
        # Special handling for BATON condition - must be first since it uses different param keys
        if cond.type == ConditionType.BATON:
            # Special handling for BATON condition
            # Bytecode format: [CHECK_BATON, val, attr, attr_hi, slot]
            # val: expected baton touch count (0 = any > 0, 2 = exactly 2)
            # attr: GROUP_ID filter (lower 32 bits)
            if hasattr(Opcode, "CHECK_BATON"):
                params_upper = {k.upper(): v for k, v in cond.params.items() if isinstance(k, str)}

                # Value: expected baton touch count
                val = 0
                count_eq = (
                    cond.params.get("count_eq")
                    or params_upper.get("COUNT_EQ")
                    or cond.params.get("val")
                    or cond.params.get("value")
                    or params_upper.get("VAL")
                    or params_upper.get("VALUE")
                )
                if count_eq:
                    try:
                        val = int(count_eq)
                    except (ValueError, TypeError):
                        val = 0

                # Attr: Standardized packing for filters
                attr = self._pack_filter_attr(cond)

                bytecode.extend(
                    [
                        int(Opcode.CHECK_BATON),
                        to_signed_32(val),
                        to_signed_32(attr & 0xFFFFFFFF),
                        to_signed_32((attr >> 32) & 0xFFFFFFFF),
                        0,
                    ]
                )
                cond.value = val
                cond.attr = attr
                cond.runtime_opcode = int(Opcode.CHECK_BATON)
            return

        if cond.type == ConditionType.TYPE_CHECK:
            if hasattr(Opcode, "CHECK_TYPE_CHECK"):
                ctype = 1 if str(cond.params.get("card_type", "")).lower() == "live" else 0
                bytecode.extend(
                    [
                        int(Opcode.CHECK_TYPE_CHECK),
                        to_signed_32(ctype),
                        0,
                        0,
                        0,
                    ]
                )
                cond.value = ctype
                cond.attr = 0
                cond.runtime_filter = {"card_type": ctype}
                cond.runtime_slot = {"target_slot": 0}
                cond.runtime_opcode = int(Opcode.CHECK_TYPE_CHECK)
            return

        op_name = f"CHECK_{cond.type.name}"
        op = getattr(Opcode, op_name, None)

        if op is None and cond.type == ConditionType.NONE and cond.params:
            op = 0

        if op is not None:
            # Fixed width: [Opcode, Value, Attr, TargetSlot]
            attr = 0
            params_upper = {k.upper(): v for k, v in cond.params.items() if isinstance(k, str)}

            v_raw = (
                cond.params.get("min")
                or cond.params.get("count")
                or cond.params.get("value")
                or cond.params.get("diff")
                or cond.params.get("GE")
                or cond.params.get("LE")
                or cond.params.get("GT")
                or cond.params.get("LT")
                or cond.params.get("EQ")
                or cond.params.get("COUNT_GE")
                or cond.params.get("COUNT_LE")
                or cond.params.get("COUNT_GT")
                or cond.params.get("COUNT_LT")
                or cond.params.get("COUNT_EQ")
                or cond.params.get("val")
                or params_upper.get("MIN")
                or params_upper.get("COUNT")
                or params_upper.get("VALUE")
                or params_upper.get("DIFF")
                or params_upper.get("GE")
                or params_upper.get("LE")
                or params_upper.get("GT")
                or params_upper.get("LT")
                or params_upper.get("EQ")
                or 0
            )
            try:
                val = int(v_raw) if v_raw is not None else 0
            except (ValueError, TypeError):
                val = 0
            if cond.params.get("ALL") or params_upper.get("ALL"):
                val |= 0x04

            # Unified Filter Packing
            if op == int(Opcode.CHECK_HAS_KEYWORD):
                attr = 0
                kw = str(cond.params.get("keyword") or "").upper()
                if "PLAYED_THIS_TURN" in kw:
                    attr |= 1 << 44
                elif "YELL_COUNT" in kw:
                    attr |= 1 << 45
                elif "HAS_LIVE_SET" in kw:
                    attr |= 1 << 46
                elif "ENERGY" in kw:
                    attr |= 1 << 62
                    attr |= self._pack_filter_attr(cond)
                elif "MEMBER" in kw:
                    attr |= 1 << 63
                    attr |= self._pack_filter_attr(cond)
                else:
                    if cond.type == ConditionType.HAS_KEYWORD:
                        cond.params["keyword"] = "PLAYED_THIS_TURN"
                        attr |= 1 << 44
            elif op == int(Opcode.CHECK_HEART_COMPARE):
                from engine.models.enums import HeartColor
                color_name = str(cond.params.get("color") or "").upper()
                try:
                    attr = int(HeartColor[color_name])
                except (KeyError, TypeError, ValueError):
                    f_str = str(cond.params.get("filter", "")).upper()
                    if "YELLOW" in f_str: attr = 2
                    elif "RED" in f_str: attr = 1
                    elif "PINK" in f_str: attr = 0
                    elif "BLUE" in f_str: attr = 4
                    elif "GREEN" in f_str: attr = 3
                    elif "PURPLE" in f_str: attr = 5
                    else: attr = 7
                attr = self._pack_filter_attr(cond)
            else:
                attr = self._pack_filter_attr(cond)

            # Persist back to the Condition object
            cond.value = val
            cond.attr = attr
            
            # Map back to structured filter object
            packed_a, filter_dict = self._pack_filter_attr_with_obj(cond)
            cond.runtime_filter = filter_dict

            # Comparison and Slot Mapping
            comp_str = str(cond.params.get("comparison") or params_upper.get("COMPARISON") or "GE").upper()
            comp_val = COMPARISONS.get(comp_str, 0)

            slot = 0
            zone = str(cond.params.get("zone") or params_upper.get("ZONE") or "").upper()
            if zone == "LIVE_ZONE":
                slot = 13  
            elif zone == "STAGE":
                slot = int(TargetType.MEMBER_SELF)
            elif zone == "YELL" or zone == "YELL_REVEALED":
                slot = ZONES.get("YELL", 17)
            elif str(cond.params.get("context", "")).lower() == "excess":
                slot = 2
            else:
                slot_raw = cond.params.get("TargetSlot") or params_upper.get("TARGETSLOT") or 0
                slot = int(slot_raw)

            area_val = cond.params.get("area") or params_upper.get("AREA")
            if area_val:
                a_str = str(area_val).upper()
                if "LEFT" in a_str: slot |= 1 << 29
                elif "CENTER" in a_str: slot |= 2 << 29
                elif "RIGHT" in a_str: slot |= 3 << 29

            packed_slot = (slot & 0x0F) | ((comp_val & 0x0F) << 4) | (slot & 0xFFFFFF00)
            
            cond.runtime_slot = {
                "target_slot": slot & 0x0F,
                "comparison": comp_val,
                "raw_slot": slot
            }

            cond.runtime_opcode = int(op) + (1000 if cond.is_negated else 0)
            bytecode.extend(
                [
                    to_signed_32(cond.runtime_opcode),
                    to_signed_32(val),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(packed_slot),
                ]
            )

        elif cond.type == ConditionType.UNIQUE_NAMES_COUNT:
            attr = self._pack_filter_attr(cond)
            attr |= EXTRA_CONSTANTS.get("FILTER_UNIQUE_NAMES", 32768)
            val = cond.value
            if val == 0:
                val = int(cond.params.get("min") or cond.params.get("count") or 0)
            
            comp_str = str(cond.params.get("comparison") or "GE").upper()
            comp_val = COMPARISONS.get(comp_str, 3) 
            slot = (int(TargetType.MEMBER_SELF) & 0x0F) | ((comp_val & 0x0F) << 4)

            op_code = 203
            cond.value = val
            cond.attr = attr
            cond.runtime_opcode = op_code
            bytecode.extend(
                [
                    to_signed_32(op_code),
                    to_signed_32(val),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(slot),
                ]
            )
        else:
            if cond.type != ConditionType.NONE:
                print(f"CRITICAL WARNING: No opcode mapping for condition type: {cond.type.name}")

    def _compile_single_effect(self, eff: Effect, bytecode: List[int]):
        # Normalize params to lowercase keys for consistent lookups
        eff.params = {str(k).lower(): v for k, v in eff.params.items()}
        if hasattr(Opcode, eff.effect_type.name):
            op = getattr(Opcode, eff.effect_type.name)

            move_member_raw_value = str(eff.params.get("raw_val") or "").upper()
            if eff.effect_type == EffectType.MOVE_MEMBER and (
                str(eff.value).upper() in ["ALL", "TARGETS"] or move_member_raw_value in ["ALL", "TARGET", "TARGETS"]
            ):
                val = 99
                attr = 99
            else:
                try:
                    val = int(eff.value)
                except (ValueError, TypeError):
                    val = 1
                attr = eff.params.get("color", eff.params.get("heart_type", 0))
                if not isinstance(attr, int):
                    attr = 0

            slot_params = {
                "target_slot": eff.target.value if hasattr(eff.target, "value") else int(eff.target),
                "remainder_zone": 0,
                "source_zone": 0,
                "dest_zone": 0,
                "is_opponent": False,
                "is_reveal_until_live": False,
                "is_empty_slot": False,
                "is_wait": False,
                "area_idx": 0,
                "is_dynamic": False,
            }

            self._resolve_effect_target(eff, slot_params)

            # --- Systemic Area Packing ---
            area_raw = eff.params.get("area", "")
            if not area_raw:
                f_str = str(eff.params.get("filter", "")).upper()
                if "AREA=CENTER" in f_str: area_raw = "CENTER"
                elif "AREA=LEFT" in f_str: area_raw = "LEFT_SIDE"
                elif "AREA=RIGHT" in f_str: area_raw = "RIGHT_SIDE"

            if area_raw:
                a_str = str(area_raw).upper()
                if "LEFT" in a_str: slot_params["area_idx"] = 1
                elif "CENTER" in a_str: slot_params["area_idx"] = 2
                elif "RIGHT" in a_str: slot_params["area_idx"] = 3

            self._resolve_effect_source_zone(eff, slot_params)

            # TAP/Interactive selection
            tap_raw_value = str(eff.params.get("raw_val") or "").upper()
            if eff.effect_type in (EffectType.TAP_OPPONENT, EffectType.TAP_MEMBER):
                if eff.effect_type == EffectType.TAP_MEMBER and tap_raw_value in ["TARGET", "TARGETS"]:
                    attr = 0
                else:
                    attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.TAP_MEMBER and tap_raw_value not in ["TARGET", "TARGETS"]:
                    attr |= 0x02  # Bit 1: Selection mode

            # PLACE_UNDER params
            if eff.effect_type == EffectType.PLACE_UNDER:
                source = str(eff.params.get("from") or eff.params.get("source") or "").lower()
                u_src_val = 0
                if source == "energy": u_src_val = ZONES.get("ENERGY", 3)
                elif source == "discard": u_src_val = ZONES.get("DISCARD", 7)
                slot_params["source_zone"] = u_src_val

            # ENERGY_CHARGE params
            if eff.effect_type == EffectType.ENERGY_CHARGE:
                if eff.params.get("wait") or eff.params.get("state") == "wait":
                    slot_params["is_wait"] = True

            # Empty Slot flag
            dest = str(eff.params.get("destination") or "").lower()
            if eff.params.get("is_empty_slot") or dest == "stage_empty" or "EMPTY" in dest:
                slot_params["is_empty_slot"] = True

            # Specialized Opcode Packing
            if eff.effect_type == EffectType.SELECT_MEMBER:
                attr = self._pack_filter_attr(eff)

            if eff.effect_type == EffectType.MOVE_MEMBER:
                destination = str(eff.params.get("destination") or "").lower()
                if destination == "target" or move_member_raw_value in ["TARGET", "TARGETS"]:
                    attr = 99

            if eff.effect_type in (EffectType.PLAY_MEMBER_FROM_HAND, EffectType.PLAY_MEMBER_FROM_DISCARD):
                attr = self._pack_filter_attr(eff)
                dest_raw = str(eff.params.get("destination") or "").upper()
                if dest_raw == "STAGE_EMPTY": slot_params["target_slot"] = 4
                elif "BATON" in dest_raw: slot_params["is_baton_slot"] = True

            if eff.effect_type == EffectType.PLAY_LIVE_FROM_DISCARD:
                attr = self._pack_filter_attr(eff)

            if eff.effect_type == EffectType.LOOK_AND_CHOOSE:
                val = self._pack_effect_look_and_choose(eff, val, slot_params)
                attr |= self._pack_filter_attr(eff)

            if eff.effect_type in (
                EffectType.SELECT_CARDS,
                EffectType.SELECT_MEMBER,
                EffectType.SELECT_LIVE,
                EffectType.MOVE_TO_DISCARD,
                EffectType.RECOVER_LIVE,
                EffectType.RECOVER_MEMBER,
            ):
                attr = self._pack_filter_attr(eff)
                src_zone_str = str(eff.params.get("source") or eff.params.get("from") or eff.params.get("zone") or "DECK").upper()
                if "," not in src_zone_str:
                    if src_zone_str == "HAND": src_val = ZONES.get("HAND", 6)
                    elif src_zone_str == "DISCARD": src_val = ZONES.get("DISCARD", 7)
                    elif src_zone_str in ("YELL", "REVEALED", "CHEER"): src_val = ZONES.get("YELL", 15)
                    elif src_zone_str in ("STAGE", "TARGET_STAGE"): src_val = ZONES.get("STAGE", 4)
                    elif src_zone_str == "DECK" and eff.effect_type in (EffectType.SELECT_MEMBER, EffectType.MOVE_TO_DISCARD):
                        src_val = ZONES.get("STAGE", 4)
                    else: src_val = ZONES.get("DECK_TOP", 1)
                    slot_params["source_zone"] = src_val

                rem_val = eff.params.get("remainder_zone", 0)
                if not rem_val and eff.params.get("raw_val") == "REMAINDER":
                    rem_val = "DISCARD"
                    slot_params["target_slot"] = 0
                if isinstance(rem_val, str):
                    rem_map = {"DISCARD": ZONES.get("DISCARD", 7), "DECK": ZONES.get("DECK_TOP", 1), "HAND": ZONES.get("HAND", 6), "DECK_TOP": EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1), "DECK_BOTTOM": EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2)}
                    rem_val = rem_map.get(rem_val.upper(), 0)
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type == EffectType.SET_HEART_COST:
                val, attr = self._pack_effect_heart_cost(eff, val, attr)

            if eff.effect_type == EffectType.REVEAL_UNTIL:
                attr = self._pack_filter_attr(eff)
                if eff.value_cond == ConditionType.TYPE_CHECK and str(eff.params.get("card_type", "")).lower() == "live":
                    slot_params["is_reveal_until_live"] = True
                elif eff.value_cond == ConditionType.COST_CHECK:
                    attr = int(eff.params.get("min", 0))

            if eff.effect_type == EffectType.META_RULE:
                m_type = str(eff.params.get("type", "") or eff.params.get("meta_type", "") or "CHEER_MOD").upper()
                attr = META_RULE_TYPES.get(m_type, 0)
                if attr == 1:
                    src = str(eff.params.get("source", "")).lower()
                    if src == "all_blade" or m_type == "ALL_BLADE_AS_ANY_HEART": val = 1
                    elif src == "blade": val = 2

            if eff.effect_type == EffectType.RESTRICTION:
                restriction_type = str(eff.params.get("type", "")).lower()
                restriction_map = {"live": 1, "placement": 2}
                attr = restriction_map.get(restriction_type, attr)

            if eff.effect_type in (EffectType.MOVE_TO_DISCARD, EffectType.COLOR_SELECT, EffectType.TRANSFORM_HEART, EffectType.TRANSFORM_COLOR):
                attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.MOVE_TO_DISCARD and eff.params.get("operation") == "UNTIL_SIZE":
                    val = (int(val) & 0x7FFFFFFF) | (1 << 31)

            val, attr = self._resolve_effect_dynamic_multiplier(eff, val, slot_params, attr)

            # Defaults
            is_non_stage_discard = eff.effect_type == EffectType.MOVE_TO_DISCARD and slot_params["source_zone"] in (ZONES.get("HAND", 6), ZONES.get("DECK", 5))
            if (eff.target in (TargetType.SELF, TargetType.PLAYER) and not is_non_stage_discard and not slot_params.get("is_dynamic", False) and not (eff.effect_type == EffectType.MOVE_MEMBER and attr == 99)):
                slot_params["target_slot"] = 4

            if (str(eff.params.get("destination") or "").lower() == "targets" and eff.target == TargetType.PLAYER and eff.effect_type in (EffectType.ADD_BLADES, EffectType.ADD_HEARTS, EffectType.BUFF_POWER, EffectType.GRANT_ABILITY)):
                slot_params["target_slot"] = int(TargetType.PLAYER)

            if eff.effect_type == EffectType.REDUCE_COST and slot_params.get("is_dynamic"): val = 1
            if eff.params.get("wait") or eff.params.get("wait_flow"): slot_params["is_wait"] = True

            slot = pack_s_standard(**slot_params)

            if eff.is_optional or eff.params.get("is_optional"):
                attr |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)

            attr_val = attr if not eff.params.get("all") else (attr | 0x80)

            if eff.effect_type == EffectType.LOOK_REORDER_DISCARD:
                op = Opcode.LOOK_REORDER_DISCARD
                bytecode.extend([int(op), to_signed_32(val), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            elif eff.effect_type == EffectType.DIV_VALUE:
                op = Opcode.DIV_VALUE
                v = int(eff.params.get("divisor") or eff.value or 2)
                bytecode.extend([int(op), to_signed_32(v), 0, 0, 0])
            elif eff.effect_type == EffectType.REVEAL_UNTIL:
                op = Opcode.REVEAL_UNTIL
                bytecode.extend([int(op), to_signed_32(val), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            elif eff.effect_type == EffectType.CALC_SUM_COST:
                op = Opcode.CALC_SUM_COST
                bytecode.extend([int(op), to_signed_32(val), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            else:
                if "filter" in eff.params and attr == 0:
                    attr_val = self._pack_filter_attr(eff)
                    if eff.is_optional or eff.params.get("is_optional"):
                        attr_val |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)

                if (op == Opcode.MOVE_TO_DISCARD and val == 0 and slot in (int(TargetType.MEMBER_SELF), int(TargetType.MEMBER_OTHER), int(TargetType.MEMBER_SELECT))):
                    val = 1

                _, filter_dict = self._pack_filter_attr_with_obj(eff)
                eff.runtime_filter = filter_dict
                eff.runtime_slot_params = slot_params
                eff.runtime_opcode = int(op)
                eff.runtime_value = val
                eff.runtime_attr = attr_val
                eff.runtime_slot = slot

                bytecode.extend([int(op), to_signed_32(val), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])

    def _compile_single_cost(self, cost: Cost, bytecode: List[int]):
        """Compile a cost into its corresponding opcode."""
        mapping = {
            AbilityCostType.ENERGY: Opcode.PAY_ENERGY,
            AbilityCostType.TAP_SELF: Opcode.SET_TAPPED,
            AbilityCostType.TAP_MEMBER: Opcode.TAP_MEMBER,
            AbilityCostType.DISCARD_HAND: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.DISCARD_TOP_DECK: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.PLACE_ENERGY_FROM_DECK: Opcode.PLACE_ENERGY_FROM_DECK,
            AbilityCostType.RETURN_HAND: Opcode.MOVE_MEMBER,
            AbilityCostType.SACRIFICE_SELF: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.RETURN_MEMBER_TO_DECK: Opcode.MOVE_TO_DECK,
            AbilityCostType.RETURN_LIVE_TO_DECK: Opcode.MOVE_TO_DECK,
            AbilityCostType.RETURN_DISCARD_TO_DECK: Opcode.MOVE_TO_DECK,
            AbilityCostType.DISCARD_MEMBER: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.DISCARD_LIVE: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.DISCARD_ENERGY: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.DISCARD_SUCCESS_LIVE: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.DISCARD_STAGE_ENERGY: Opcode.MOVE_TO_DISCARD,
            AbilityCostType.REVEAL_HAND: Opcode.REVEAL_CARDS,
            AbilityCostType.REVEAL_HAND_ALL: Opcode.REVEAL_CARDS,
        }

        op = None
        if cost.params.get("cost_type_name") == "CALC_SUM_COST":
            op = Opcode.CALC_SUM_COST
        elif cost.params.get("cost_type_name") == "SELECT_CARDS":
            op = Opcode.SELECT_CARDS
        elif cost.params.get("cost_type_name") == "SELECT_MEMBER":
            op = Opcode.SELECT_MEMBER
        elif cost.params.get("cost_type_name") == "SELECT_ENERGY":
            op = Opcode.PLACE_ENERGY_UNDER_MEMBER
        else:
            op = mapping.get(cost.type)

        if op is not None:
            attr = 0
            slot_params = {
                "target_slot": 0,
                "remainder_zone": 0,
                "source_zone": 0,
                "dest_zone": 0,
                "is_opponent": False,
                "is_reveal_until_live": False,
                "is_empty_slot": False,
                "is_wait": False,
                "is_dynamic": False,
                "area_idx": 0,
            }

            params_upper = {k.upper(): v for k, v in cost.params.items() if isinstance(k, str)}
            filter_expr = cost.params.get("filter") or params_upper.get("FILTER")
            source_name = str(cost.params.get("from") or params_upper.get("FROM") or "").lower()
            uses_filtered_discard_selection = (op == Opcode.MOVE_TO_DECK and source_name == "discard" and bool(filter_expr))

            if uses_filtered_discard_selection:
                select_attr = self._pack_filter_attr(cost)
                if cost.is_optional:
                    select_attr |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)
                select_slot = pack_s_standard(target_slot=int(TargetType.CARD_DISCARD), remainder_zone=0, source_zone=int(ZONES.get("DISCARD", 7)), dest_zone=int(ZONES.get("DECK", 8)), is_opponent=False, is_reveal_until_live=False, is_empty_slot=False, is_wait=False, is_dynamic=False, area_idx=0)
                value = cost.value or int(cost.params.get("count") or params_upper.get("COUNT") or 0)
                bytecode.extend([int(Opcode.SELECT_CARDS), to_signed_32(int(value)), to_signed_32(select_attr & 0xFFFFFFFF), to_signed_32((select_attr >> 32) & 0xFFFFFFFF), to_signed_32(select_slot)])
                return

            if cost.type in [AbilityCostType.DISCARD_HAND, AbilityCostType.RETURN_HAND, AbilityCostType.REVEAL_HAND, AbilityCostType.REVEAL_HAND_ALL]:
                slot_params["target_slot"] = int(TargetType.CARD_HAND)
            elif cost.type in [AbilityCostType.TAP_SELF, AbilityCostType.TAP_MEMBER, AbilityCostType.SACRIFICE_SELF]:
                slot_params["target_slot"] = int(TargetType.MEMBER_SELF)
            elif cost.type == AbilityCostType.DISCARD_ENERGY:
                slot_params["target_slot"] = int(TargetType.SELF)
            elif cost.type in [AbilityCostType.RETURN_DISCARD_TO_DECK]:
                slot_params["target_slot"] = int(TargetType.CARD_DISCARD)
            elif cost.type == AbilityCostType.DISCARD_TOP_DECK:
                slot_params["source_zone"] = ZONES.get("DECK_TOP", 1)
            elif cost.type in [AbilityCostType.RETURN_SUCCESS_LIVE_TO_HAND, AbilityCostType.DISCARD_SUCCESS_LIVE]:
                slot_params["source_zone"] = ZONES.get("SUCCESS_PILE", 14)
            elif cost.params.get("cost_type_name") == "SELECT_ENERGY":
                slot_params["target_slot"] = int(TargetType.SELF)
                slot_params["source_zone"] = ZONES.get("ENERGY", 3)
            else:
                slot_params["target_slot"] = int(TargetType.SELF)

            if op == Opcode.MOVE_TO_DECK:
                to = str(cost.params.get("to") or params_upper.get("TO") or "top").lower()
                if to == "bottom": slot_params["remainder_zone"] = int(EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2))
                elif to == "top": slot_params["remainder_zone"] = int(EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1))

            if op in [Opcode.SELECT_CARDS, Opcode.SELECT_MEMBER, Opcode.TAP_MEMBER, Opcode.PLAY_MEMBER_FROM_HAND, Opcode.PLAY_MEMBER_FROM_DISCARD, Opcode.MOVE_TO_DISCARD]:
                attr = self._pack_filter_attr(cost)

            if cost.is_optional or cost.params.get("is_optional"):
                attr |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)

            slot = pack_s_standard(**slot_params)
            value = cost.value or int(cost.params.get("count") or params_upper.get("COUNT") or 0)
            
            cost.runtime_opcode = int(op)
            cost.runtime_filter = self._pack_filter_attr_with_obj(cost)[1]
            cost.runtime_slot = slot_params

            bytecode.extend([int(op), to_signed_32(value), to_signed_32(attr & 0xFFFFFFFF), to_signed_32((attr >> 32) & 0xFFFFFFFF), to_signed_32(slot)])

    def _resolve_effect_target(self, eff: Effect, slot_params: Dict[str, Any]):
        target_raw = eff.params.get("target") or eff.params.get("to")
        if target_raw:
            target_str = str(target_raw).upper()
            target_map = {
                "HAND": TargetType.CARD_HAND,
                "CARD_HAND": TargetType.CARD_HAND,
                "DISCARD": TargetType.CARD_DISCARD,
                "CARD_DISCARD": TargetType.CARD_DISCARD,
                "DECK": TargetType.CARD_DECK_TOP,
                "CARD_DECK_TOP": TargetType.CARD_DECK_TOP,
                "PLAYER": TargetType.PLAYER,
                "SELF": TargetType.SELF,
                "OPPONENT": TargetType.OPPONENT,
                "MEMBER_SELF": TargetType.MEMBER_SELF,
                "MEMBER_SELECT": TargetType.MEMBER_SELECT,
            }
            if target_str in target_map:
                eff.target = target_map[target_str]
            elif "MEMBER" in target_str:
                eff.target = TargetType.MEMBER_OTHER if "OTHER" in target_str else TargetType.MEMBER_SELECT
        elif eff.effect_type == EffectType.TAP_OPPONENT:
            eff.target = TargetType.OPPONENT
        slot_params["target_slot"] = int(eff.target)

    def _resolve_effect_source_zone(self, eff: Effect, slot_params: Dict[str, Any]):
        src_val = 0
        if eff.effect_type in (EffectType.RECOVER_MEMBER, EffectType.RECOVER_LIVE, EffectType.PLAY_MEMBER_FROM_DISCARD, EffectType.PLAY_LIVE_FROM_DISCARD):
            source = str(eff.params.get("source") or eff.params.get("zone") or "discard").lower()
            src_val = ZONES.get("DISCARD", 7) if source == "discard" else 0
            if source == "yell": src_val = ZONES.get("YELL", 15)
            elif source in ("deck", "deck_top"): src_val = ZONES.get("DECK_TOP", 1)
            slot_params["source_zone"] = src_val

    def _pack_effect_look_and_choose(self, eff: Effect, val: int, slot_params: Dict[str, Any]) -> int:
        char_ids = []
        raw_names = str(eff.params.get("group") or eff.params.get("target_name") or eff.params.get("character") or "")
        if raw_names:
            parts = raw_names.replace(",", "/").split("/")
            for p in parts[:3]:
                p = p.strip()
                if p in CHAR_MAP: char_ids.append(CHAR_MAP[p])
        
        look_v = {
            "count": val,
            "char_id_1": char_ids[0] if char_ids else 0,
            "char_id_2": char_ids[1] if len(char_ids) > 1 else 0,
            "char_id_3": char_ids[2] if len(char_ids) > 2 else 0,
            "reveal": 1 if eff.params.get("reveal") else 0,
            "dest_discard": 1 if eff.params.get("destination") == "discard" or eff.params.get("dest_discard") else 0,
        }
        val = pack_v_look_choose(**look_v)
        src = str(eff.params.get("source") or eff.params.get("zone") or "DECK").upper()
        if src == "HAND": slot_params["source_zone"] = ZONES.get("HAND", 6)
        elif src == "DISCARD": slot_params["source_zone"] = ZONES.get("DISCARD", 7)
        else: slot_params["source_zone"] = ZONES.get("DECK_TOP", 1)
        return val

    def _pack_effect_heart_cost(self, eff: Effect, val: int, attr: int) -> Tuple[int, int]:
        from engine.models.enums import HeartColor
        v_params = {
            "pink": int(eff.params.get("pink", 0)),
            "red": int(eff.params.get("red", 0)),
            "yellow": int(eff.params.get("yellow", 0)),
            "green": int(eff.params.get("green", 0)),
            "blue": int(eff.params.get("blue", 0)),
            "purple": int(eff.params.get("purple", 0)),
        }
        val = pack_v_heart_counts(**v_params)
        return val, attr

    def _resolve_effect_dynamic_multiplier(self, eff: Effect, val: int, slot_params: Dict[str, Any], attr: int) -> Tuple[int, int]:
        per_card = eff.params.get("per_card")
        per_energy = eff.params.get("per_energy")
        if not per_card and not per_energy: return val, attr

        slot_params["is_dynamic"] = True
        divisor = 1
        if per_energy:
            try: divisor = int(per_energy)
            except: divisor = 1
        
        packed_val = pack_v_scalar_dynamic(base_value=val, divisor=divisor)
        attr |= (1 << 60) # Bit 60 indicates dynamic multiplier enabled
        
        # Determine source zone for dynamic multiplier
        source_str = str(per_card or per_energy or "stage").lower()
        if "hand" in source_str: slot_params["source_zone"] = ZONES.get("HAND", 6)
        elif "discard" in source_str: slot_params["source_zone"] = ZONES.get("DISCARD", 7)
        elif "deck" in source_str: slot_params["source_zone"] = ZONES.get("DECK_TOP", 1)
        elif "yell" in source_str: slot_params["source_zone"] = ZONES.get("YELL", 15)
        else: slot_params["source_zone"] = ZONES.get("STAGE", 4)
        
        return packed_val, attr

    def _instruction_to_frame(self, instr: Union[Effect, Condition, Cost]) -> Union[str, Dict[str, Any]]:
        """Map a single instruction (Effect/Condition/Cost) to an AbilityFrame JSON-compatible dict."""
        opcode_id = 0
        opcode_name = "NONE"
        value = 0
        attr = {}
        slot = {}
        raw = copy.deepcopy(getattr(instr, "params", {})) if hasattr(instr, "params") else {}

        if self._is_effect_instruction(instr):
            opcode_name = instr.effect_type.name
            try:
                opcode_id = getattr(instr, "runtime_opcode", 0)
            except AttributeError:
                opcode_id = 0
            
            # Fallback if runtime_opcode is not set
            if opcode_id == 0:
                from engine.models.opcodes import Opcode
                if hasattr(Opcode, opcode_name):
                    opcode_id = int(getattr(Opcode, opcode_name))
            
            value = instr.value
            attr = getattr(instr, "runtime_filter", {})
            slot = getattr(instr, "runtime_slot_params", {})
        elif self._is_condition_instruction(instr):
            opcode_name = f"CHECK_{instr.type.name}"
            try:
                opcode_id = getattr(instr, "runtime_opcode", 0) % 1000
            except AttributeError:
                opcode_id = 0
            
            # Fallback if runtime_opcode is not set
            if opcode_id == 0:
                from engine.models.generated_metadata import CONDITIONS
                opcode_id = CONDITIONS.get(instr.type.name, 0)
            
            value = instr.value
            attr = getattr(instr, "runtime_filter", {})
            slot = getattr(instr, "runtime_slot", {})
        elif self._is_cost_instruction(instr):
            mapping = {
                AbilityCostType.ENERGY: "PAY_ENERGY",
                AbilityCostType.TAP_SELF: "SET_TAPPED",
                AbilityCostType.TAP_MEMBER: "TAP_MEMBER",
                AbilityCostType.DISCARD_HAND: "MOVE_TO_DISCARD",
                AbilityCostType.PLACE_ENERGY_FROM_DECK: "PLACE_ENERGY_FROM_DECK",
                AbilityCostType.RETURN_HAND: "MOVE_MEMBER",
                AbilityCostType.SACRIFICE_SELF: "MOVE_TO_DISCARD",
                AbilityCostType.DISCARD_TOP_DECK: "MOVE_TO_DISCARD",
                AbilityCostType.RETURN_MEMBER_TO_DECK: "MOVE_TO_DECK",
            }
            opcode_name = mapping.get(instr.type, "NONE")
            try:
                opcode_id = getattr(instr, "runtime_opcode", 0)
            except AttributeError:
                opcode_id = 0
                
            # Fallback if runtime_opcode is not set
            if opcode_id == 0:
                from engine.models.generated_metadata import COSTS
                opcode_id = COSTS.get(opcode_name, 0)
                if opcode_id == 0:
                    from engine.models.opcodes import Opcode
                    if hasattr(Opcode, opcode_name):
                        opcode_id = int(getattr(Opcode, opcode_name))

            value = instr.value
            attr = getattr(instr, "runtime_filter", {})
            slot = getattr(instr, "runtime_slot", {})
        if opcode_name == "RETURN":
            return "Return"
        
        # Short-hands for standard frames
        if opcode_name == "DRAW" or opcode_name == "DRAW_UNTIL":
            return {"Draw": {"count": int(value), "is_until": opcode_name == "DRAW_UNTIL"}}
        if opcode_name == "RECOVER_LIVE":
            return {"RecoverLive": {"count": int(value), "filter": attr, "slot": slot}}
        if opcode_name == "RECOVER_MEMBER":
            return {"RecoverMember": {"count": int(value), "filter": attr, "slot": slot}}
        if opcode_name == "LOOK_AND_CHOOSE":
            return {"LookAndChoose": {"params": value, "filter": attr, "slot": slot}}
        if opcode_name == "SELECT_MEMBER":
            return {"SelectMember": {"count": int(value), "filter": attr, "slot": slot}}
        if opcode_name == "MOVE_MEMBER":
            return {"MoveMember": {"filter": attr, "slot": slot}}
        if opcode_name == "MOVE_TO_DISCARD":
            return {"MoveToDiscard": {"count": int(value), "filter": attr, "slot": slot}}
        if opcode_name == "MOVE_TO_DECK":
            return {"MoveToDeck": {"count": int(value), "filter": attr, "slot": slot}}
        if opcode_name == "META_RULE":
            return {"MetaRule": {"rule_type": int(value), "filter": attr, "slot": slot}}

        # Default: Generic Semantic Frame
        return {
            "Semantic": {
                "opcode": opcode_id,
                "value": int(value),
                "filter": attr,
                "slot": slot,
                "params": raw,
            }
        }


def build_frame_program(ability) -> List[Union[str, Dict[str, Any]]]:
    """Build a frame program without round-tripping through bytecode."""
    return AbilityCompiler()._build_frame_program_from_source(ability)
