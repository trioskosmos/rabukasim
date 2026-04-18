"""Convert semantic abilities to frame format.

This tool converts abilities_extracted_from_cards.json (semantic format)
to ability_frame_source.json (frame format) for Rust engine compatibility.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

GROUP_ID_MAP: Dict[str, str] = {
    "Liella!": "LIELLA",
    "Liella": "LIELLA",
    "Aqours": "AQOURS",
    "μ's": "MUSE",
    "μs": "MUSE",
    "Nijigasaki": "NIJIGASAKI",
    "虹ヶ咲": "NIJIGASAKI",
    "蓮ノ空": "HASUNOSORA",
    "Saint Snow": "SAINTSNOW",
    "SaintSnow": "SAINTSNOW",
    "BiBi": "BIBI",
    "Printemps": "PRINTEMPS",
    "lily white": "LILYWHITE",
    "lilywhite": "LILYWHITE",
    "Guilty Kiss": "GUILTY_KISS",
    "AZALEA": "AZALEA",
    "DOLLCHESTRA": "DOLLCHESTRA",
    "スリーズブーケ": "SUISEIBOUQUETTE",
    "みらくらぱーく！": "MIRAPARK",
    "5yncri5e!": "SYNCR5",
    "A-RISE": "ARISE",
    "CatChu!": "CATCHU",
    "EdelNote": "EDELNOTE",
    "KALEIDOSCORE": "KALEIDOSCORE",
    "SunnyPassion": "SUNNYPASSION",
}

CHAR_ID_MAP: Dict[str, str] = {
    "朝香果林": "KARIN",
    "天王寺璃奈": "RINA",
    "優木せつ菜": "SETSUNA",
    "桜坂しずく": "SHIZUKU",
    "上原歩夢": "AYUMU",
    "エマ・ヴェルデ": "EMMA",
    "三船栞子": "SHIORIKO",
    "宮下 愛": "AI",
    "宮下愛": "AI",
    "朝香果林": "KARIN",
    "中須かすみ": "KASUMI",
    "若菜四季": "SHIKI",
    "大沢瑠璃乃": "RURINO",
    "村野さやか": "SAYAKA",
    "日野下花帆": "KAHO",
    "乙宗 梢": "KOSUZU",
    "夕霧綴理": "TSUZURI",
    "藤島 慈": "MEGUMI",
    "百生 吟子": "GINKO",
    "セラス 柳田 リリエンフェルト": "SERAS",
    "鬼塚夏美": "NATSUMI",
    "渡辺曜": "YO",
    "星空 凛": "RIN",
    "桜内梨子": "RIKO",
    "黒澤ダイヤ": "DIA",
    "ミア・テイラー": "MIA",
    "澁谷かのん": "KANON",
}

# Semantic action to frame opcode mapping.
SEMANTIC_TO_OPCODE: Dict[str, str] = {
    "draw_cards": "DRAW",
    "add_to_hand": "ADD_TO_HAND",
    "gain_resource": "ADD_BLADES",
    "add_blades": "ADD_BLADES",
    "look_at_cards": "LOOK_DECK",
    "select_from_looked_at_cards": "LOOK_AND_CHOOSE",
    "look_reorder_discard": "LOOK_REORDER_DISCARD",
    "place_on_deck": "MOVE_TO_DECK",
    "discard_to_waitroom": "MOVE_TO_DISCARD",
    "member_to_wait": "SET_TAPPED",
    "select_member": "SELECT_MEMBER",
    "play_member_from_hand": "PLAY_MEMBER_FROM_HAND",
    "play_member_from_discard": "PLAY_MEMBER_FROM_DISCARD",
    "play_live_from_discard": "PLAY_LIVE_FROM_DISCARD",
    "choose_heart": "COLOR_SELECT",
    "may_place_card": "SELECT_CARDS",
    "add_score": "BOOST_SCORE",
    "pay_energy": "PAY_ENERGY",
    "place_card": "MOVE_TO_DISCARD",
    "activate_energy": "ACTIVATE_ENERGY",
    "activate_member": "ACTIVATE_MEMBER",
    "reduce": "REDUCE_COST",
    "reduce_cost": "REDUCE_COST",
    "increase_heart_cost": "INCREASE_HEART_COST",
    "reduce_heart_cost": "REDUCE_HEART_REQ",
    "deploy_to_stage": "PLAY_MEMBER_FROM_HAND",
    "may_deploy_to_stage": "PLAY_MEMBER_FROM_HAND",
    "select_card": "SELECT_CARDS",
    "select_area": "MOVE_MEMBER",
    "move_member": "MOVE_MEMBER",
    "position_change": "MOVE_MEMBER",
    "may_position_change": "MOVE_MEMBER",
    "opponent_selects": "OPPONENT_CHOOSE",
    "may_move": "MOVE_MEMBER",
    "gain_ability": "GRANT_ABILITY",
    "invalidate_ability": "NEGATE_EFFECT",
    "select_player": "SELECT_PLAYER",
    "may_add_to_hand": "ADD_TO_HAND",
    "modify_cost": "INCREASE_COST",
    "reduce": None,  # Opcode determined dynamically based on payload (REDUCE_COST or REDUCE_HEART_REQ)
    "activation_restriction": "RESTRICTION",
    "repeat_same_effect": "SYNC_COST",
    "cannot_become_active": "PREVENT_ACTIVATE",
    "cannot_activate": "PREVENT_ACTIVATE",
    "cannot": "RESTRICTION",
    "cannot_baton_touch": "PREVENT_BATON_TOUCH",
    "may_baton_touch": "BATON_TOUCH_MOD",
    "cannot_place": "PREVENT_SET_TO_SUCCESS_PILE",
    "treat_as": "TYPE_CHECK",
    "transform_blades": "TRANSFORM_BLADES",
    "transform_heart": "TRANSFORM_HEART",
    "set_original_blade_count": "SET_HEART_COST",
    "formation_change": "FORMATION_CHANGE",
    "set_state": "SET_TAPPED",
    "heart_cost_modifier": "SET_HEART_COST",
    "reduce_score": "SET_SCORE",
    "choose_heart_color": "META_RULE",
    "activate_ability": "GRANT_ABILITY",
    "return_energy_card": "ENERGY_CHARGE",
    "selected_discarded_member_card": "SELECT_CARDS",
    "rotate_areas": "SWAP_AREA",
    "retry_cheer": "REVEAL_CARDS",
    "note": "META_RULE",
}

# Zone name mapping
ZONE_MAP: Dict[str, str] = {
    "hand": "HAND",
    "deck_top": "DECK_TOP",
    "deck_bottom": "DECK_BOTTOM",
    "deck": "DECK",
    "waitroom": "DISCARD",
    "wait": "DISCARD",
    "stage": "STAGE",
    "discard": "DISCARD",
    "success_pile": "SUCCESS_PILE",
    "energy": "ENERGY",
    "yell": "YELL",
    "yell_pile": "YELL",
}

# Trigger mapping (Japanese to English constant)
TRIGGER_MAP: Dict[str, tuple[str, int]] = {
    "起動": ("ACTIVATED", 7),
    "登場": ("ON_PLAY", 1),
    "ライブ開始時": ("LIVE_START", 2),
    "ライブ成功時": ("LIVE_SUCCESS", 3),
    "常時": ("CONSTANT", 0),
    "ターン開始時": ("TURN_START", 4),
    "ターン終了時": ("TURN_END", 5),
    "控え室に置かれた時": ("ON_MOVE_TO_DISCARD", 6),
    "公開された時": ("ON_REVEAL", 9),
}


TRIGGER_MAP = {
    "自動": ("ON_LEAVES", 6),
    "起動": ("ACTIVATED", 7),
    "登場": ("ON_PLAY", 1),
    "ライブ開始時": ("LIVE_START", 2),
    "ライブ成功時": ("LIVE_SUCCESS", 3),
    "常時": ("CONSTANT", 0),
    "ターン開始時": ("TURN_START", 4),
    "ターン終了時": ("TURN_END", 5),
    "控え室に置かれた時": ("ON_MOVE_TO_DISCARD", 6),
    "公開された時": ("ON_REVEAL", 9),
}

def map_zone(zone: str) -> str:
    """Map semantic zone name to frame zone name."""
    return ZONE_MAP.get(zone.lower(), zone.upper())


def map_trigger(japanese_trigger: str) -> tuple[str, int]:
    """Map Japanese trigger to (English constant, ID)."""
    if japanese_trigger is None:
        return ("ACTIVATED", 7)
    
    # Handle comma-separated multiple triggers
    if "," in japanese_trigger:
        japanese_trigger = japanese_trigger.split(",")[0].strip()
    
    return TRIGGER_MAP.get(japanese_trigger.strip(), ("ACTIVATED", 7))


def _frame(
    opcode: str,
    frame_index: int,
    value: Any = 0,
    *,
    attr: Optional[Dict[str, Any]] = None,
    slot: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    frame = {"op": opcode, "frame_index": frame_index}
    if value is not None:
        frame["value"] = value
    if attr:
        frame["attr"] = attr
    if slot:
        frame["slot"] = slot
    if params:
        frame["params"] = params
    return frame


def _group_id(name: str) -> Optional[str]:
    if not name:
        return None
    return GROUP_ID_MAP.get(name, name.replace("!", "").replace(" ", "_").upper())


def _char_id(name: str) -> Optional[str]:
    if not name:
        return None
    return CHAR_ID_MAP.get(name, name.replace(" ", "_").upper())


def _group_or_char_id(name: str, group_type: Optional[str] = None) -> Optional[str]:
    """Get group or character ID based on group_type field.
    If group_type is 'unit', use GROUP_ID_MAP.
    If group_type is 'character', use CHAR_ID_MAP.
    If group_type is None, try GROUP_ID_MAP first, then CHAR_ID_MAP."""
    if not name:
        return None
    
    # If name is very long (likely full Japanese text), return None to avoid putting it in group_id
    if len(name) > 50:
        return None
    
    if group_type == 'unit':
        result = _group_id(name)
        normalized = name.replace("!", "").replace(" ", "_").upper()
        # Check if result exists in GROUP_ID_MAP (result != normalized means it was found)
        if result != normalized or result in GROUP_ID_MAP.values():
            return result
        return None
    elif group_type == 'character':
        result = _char_id(name)
        normalized = name.replace(" ", "_").upper()
        if result != normalized or result in CHAR_ID_MAP.values():
            return result
        return None
    else:
        # Try group first, then character
        result = _group_id(name)
        normalized = name.replace("!", "").replace(" ", "_").upper()
        if result != normalized or result in GROUP_ID_MAP.values():
            return result
        # Try character map
        result = _char_id(name)
        normalized = name.replace(" ", "_").upper()
        if result != normalized or result in CHAR_ID_MAP.values():
            return result
        # Not found in either map, return None to avoid putting raw text
        return None


def _card_type(value: str) -> Optional[str]:
    if not value:
        return None
    if "live" in value:
        return "LIVE"
    if "member" in value:
        return "MEMBER"
    if "energy" in value:
        return "ENERGY"
    return value.upper()


__FULLWIDTH_DIGITS = str.maketrans("０１２３４５６７８９", "0123456789")


def _to_int(value: str) -> int:
    return int(str(value).translate(_FULLWIDTH_DIGITS))


# Heart type to color mask mapping
HEART_TYPE_TO_COLOR_MASK: Dict[str, str] = {
    "01": "RED",
    "02": "RED",
    "03": "GREEN",
    "04": "GREEN",
    "05": "BLUE",
    "06": "ANY",  # heart06 is "any color" not blue
    "heart01": "RED",
    "heart02": "RED",
    "heart03": "GREEN",
    "heart04": "GREEN",
    "heart05": "BLUE",
    "heart06": "ANY",  # heart06 is "any color" not blue
    "red": "RED",
    "green": "GREEN",
    "blue": "BLUE",
    "any": "ANY",
}


def _heart_types_to_color_mask(heart_types: List[str]) -> str:
    """Convert a list of heart types to a color mask string."""
    if not heart_types:
        return "ANY"
    
    colors = set()
    for ht in heart_types:
        ht_lower = ht.lower().replace("heart", "").replace("{{", "").replace("}}", "").strip()
        color = HEART_TYPE_TO_COLOR_MASK.get(ht_lower)
        if color:
            colors.add(color)
    
    if not colors:
        return "ANY"
    
    # Sort colors for consistency
    color_order = ["RED", "GREEN", "BLUE", "ANY"]
    sorted_colors = [c for c in color_order if c in colors]
    
    return "|".join(sorted_colors)


def _maybe_recover_opcode(payload: Dict[str, Any]) -> Optional[str]:
    """Map discard-to-hand recovery actions to legacy recovery opcodes."""
    source = map_zone(payload.get("source", "waitroom"))
    card_type = _card_type(payload.get("card_type", ""))
    if source != "DISCARD":
        return None
    if card_type == "LIVE":
        return "RECOVER_LIVE"
    if card_type == "MEMBER":
        return "RECOVER_MEMBER"
    return None


def _condition_meta(condition_data: Dict[str, Any]) -> Dict[str, Any]:
    meta: Dict[str, Any] = {}
    for key in ("target", "card_type", "group", "position", "location", "operator", "compares", "state_name"):
        value = condition_data.get(key)
        if value is not None:
            meta[key] = value
    if condition_data.get("exclusion"):
        meta["exclusion"] = condition_data["exclusion"]
    return meta


def _convert_unknown_action_to_frames(action_data: Dict[str, Any], frame_index: int) -> tuple[List[Dict[str, Any]], int]:
    """Synthesize frames for semantic nodes that are missing an action name."""
    text = action_data.get("text", "")
    frames: List[Dict[str, Any]] = []
    idx = frame_index

    if "ハートの色" in text and "得る" in text:
        frames.append(
            _frame(
                "COLOR_SELECT",
                idx,
                1,
                attr={"target_player": "SELF", "color_mask": "RED|GREEN|BLUE"},
                slot={"target_slot": "CONTEXT"},
            )
        )
        idx += 1
        frames.append(
            _frame(
                "ADD_HEARTS",
                idx,
                1,
                attr={"target_player": "SELF"},
                slot={"target_slot": "CONTEXT"},
                params={"heart_type": "SELECTED"},
            )
        )
        idx += 1
        return frames, idx

    return frames, idx


def convert_cost_to_frames(cost_data: Dict[str, Any], frame_index: int) -> tuple[List[Dict], int]:
    """Convert cost object to cost frames."""
    frames = []
    idx = frame_index
    
    if not cost_data or isinstance(cost_data, str):
        return frames, idx
    
    cost_type = cost_data.get("type", "")
    is_optional = cost_data.get("optional", False)
    payment = cost_data.get("payment", False)
    value = cost_data.get("count", 0) or cost_data.get("energy", 0)
    full_text = str(cost_data.get("_full_text", ""))
    
    if cost_type == "pay_energy":
        if not is_optional and "支払ってもよい" in full_text:
            is_optional = True
        if payment:
            is_optional = True  # Payment costs are optional
        frame = {
            "op": "PAY_ENERGY",
            "frame_index": idx,
            "value": value,
            "is_cost": True,
        }
        # Add once_per_turn if turn1 is in the text
        if "turn1" in full_text or "ターン1回" in full_text:
            frame.setdefault("attr", {})["once_per_turn"] = 1
        if is_optional:
            if "attr" not in frame:
                frame["attr"] = {}
            frame["attr"]["is_optional"] = 1
            # Add JUMP_IF_FALSE after optional cost
            frames.append(frame)
            idx += 1
            frames.append({
                "op": "JUMP_IF_FALSE",
                "frame_index": idx,
                "value": 1,  # Skip next frame if cost not paid
            })
        else:
            frames.append(frame)
        idx += 1
    
    elif cost_type == "move_cards":
        source = map_zone(cost_data.get("source", ""))
        destination = map_zone(cost_data.get("destination", ""))
        target = cost_data.get("target", "")
        original_destination = cost_data.get("destination", "")
        exclude_member = cost_data.get("exclude_member", False)
        max_count = cost_data.get("max", False)
        order = cost_data.get("order", "")
        position = cost_data.get("position", "")
        energy_cost = cost_data.get("energy", 0)
        
        # Check for once_per_turn
        has_once_per_turn = "turn1" in full_text or "ターン1回" in full_text
        
        if not is_optional and "てもよい" in full_text:
            is_optional = True
        
        # If cost has energy, generate PAY_ENERGY frame first
        if energy_cost > 0:
            frame = {
                "op": "PAY_ENERGY",
                "frame_index": idx,
                "value": energy_cost,
                "is_cost": True,
            }
            if is_optional:
                frame["attr"] = {"is_optional": 1}
                frames.append(frame)
                idx += 1
                frames.append({
                    "op": "JUMP_IF_FALSE",
                    "frame_index": idx,
                    "value": 1,
                })
            else:
                frames.append(frame)
            idx += 1
        
        # Determine opcode based on source/destination/target combination
        # source="STAGE" + destination="DISCARD" + target="this_member" → RETURN or SET_TAPPED
        if (target == "this_member" or target == "member") and source == "STAGE" and destination == "DISCARD":
            if original_destination == "wait":
                frame = {
                    "op": "SET_TAPPED",
                    "frame_index": idx,
                    "attr": {},
                    "is_cost": True,
                }
            else:
                # Check if this is an activated ability cost (discard self to activate)
                # If so, use MOVE_TO_DISCARD instead of RETURN
                if "起動" in full_text or "ACTIVATED" in full_text:
                    frame = {
                        "op": "MOVE_TO_DISCARD",
                        "frame_index": idx,
                        "value": value,
                        "attr": {"target_player": "SELF"},
                        "slot": {"target_slot": "CONTEXT", "source_zone": "STAGE", "dest_zone": "DISCARD"},
                        "is_cost": True,
                    }
                else:
                    frame = {
                        "op": "RETURN",
                        "frame_index": idx,
                        "attr": {},
                        "is_cost": True,
                    }
        else:
            frame = {
                "op": "MOVE_TO_DISCARD",
                "frame_index": idx,
                "value": value,
                "attr": {"target_player": "OPPONENT" if target == "opponent" else "SELF"},
                "slot": {
                    "source_zone": source,
                    "dest_zone": destination,
                    "target_slot": "CONTEXT",
                },
                "is_cost": True,
            }
        
        # Add once_per_turn to attr if present
        if has_once_per_turn:
            frame.setdefault("attr", {})["once_per_turn"] = 1
        
        # Add exclude_member to attr if present
        if exclude_member:
            frame["attr"]["exclude_this_member"] = 1
        
        # Add max to params if present (for "up to N" patterns)
        if max_count:
            if "params" not in frame:
                frame["params"] = {}
            frame["params"]["max"] = True
        
        # Add order to params if present (for "any order" patterns)
        if order == "any":
            if "params" not in frame:
                frame["params"] = {}
            frame["params"]["any_order"] = True
        
        # Add position to attr if present (for center/left_side/right_side requirements)
        if position:
            position_map = {
                "center": 1,
                "left_side": 0,
                "right_side": 2,
            }
            if position in position_map:
                frame["attr"]["position"] = position_map[position]
        
        if is_optional:
            frame["attr"]["is_optional"] = 1
            frames.append(frame)
            idx += 1
            # Add SUM_VALUE + JUMP_IF_FALSE for optional costs that require checking resources
            # Pattern: optional discard to hand followed by energy charge or other resource-dependent action
            if source == "HAND" and destination == "DISCARD":
                if "ブレード" in full_text or "エネルギー" in full_text:
                    frames.append({
                        "op": "SUM_VALUE",
                        "frame_index": idx,
                    })
                    idx += 1
                    frames.append({
                        "op": "JUMP_IF_FALSE",
                        "frame_index": idx,
                        "value": 3,
                    })
                else:
                    frames.append({
                        "op": "JUMP_IF_FALSE",
                        "frame_index": idx,
                        "value": 1,
                    })
            else:
                frames.append({
                    "op": "JUMP_IF_FALSE",
                    "frame_index": idx,
                    "value": 1,
                })
        else:
            frames.append(frame)
        
        idx += 1
    
    return frames, idx


def convert_action_to_frame(action_data: Dict[str, Any], frame_index: int, effect_data: Optional[Dict[str, Any]] = None) -> tuple[Optional[Dict], int]:
    """Convert a single semantic action to a frame."""
    import sys
    idx = frame_index

    if isinstance(action_data, str):
        action_name = action_data
        payload: Dict[str, Any] = {}
    elif isinstance(action_data, dict):
        action_name = action_data.get("action", "")
        if isinstance(action_name, dict):
            return None, idx
        payload = action_data
    else:
        return None, idx

    if action_name in {"note", "whenever_trigger"}:
        return None, idx
    
    # Skip empty action names
    if not action_name:
        return None, idx

    opcode = SEMANTIC_TO_OPCODE.get(action_name)
    if opcode is None and action_name not in {"reduce", "reduce_cost"}:
        raise NotImplementedError(f"Unsupported semantic action: {action_name!r}")

    # Extract value with multiple fallback options
    value = payload.get("count")
    if value is None:
        value = payload.get("amount")
    if value is None:
        value = payload.get("value")
    if value is None:
        value = 0
    
    frame = _frame(opcode, idx, value, attr={"target_player": "SELF"}, slot={})
    
    # Handle timing field for effects with duration constraints
    timing = payload.get("timing", "")
    if timing:
        timing_map = {
            "until_live_end": "LIVE_END",
            "until_turn_end": "TURN_END",
            "permanent": "PERMANENT",
        }
        if timing in timing_map:
            if "params" not in frame:
                frame["params"] = {}
            frame["params"]["timing"] = timing_map[timing]
    
    # Handle duration field for effects with duration constraints
    duration = payload.get("duration", "")
    if duration:
        duration_map = {
            "live_end": "LIVE_END",
            "turn_end": "TURN_END",
        }
        if duration in duration_map:
            if "params" not in frame:
                frame["params"] = {}
            frame["params"]["timing"] = duration_map[duration]
    
    # Store nested 'then' action for later processing
    then_action = payload.get("then")
    
    # Handle multiplier, per_unit, unit_type for dynamic value calculation
    multiplier = payload.get("multiplier", 0)
    per_unit = payload.get("per_unit", "")
    unit_type = payload.get("unit_type", "")
    
    if multiplier or per_unit:
        if "params" not in frame:
            frame["params"] = {}
        if multiplier:
            frame["params"]["multiplier"] = multiplier
        if per_unit:
            unit_type_map = {
                "success_live": "SUCCESS_LIVE",
                "stage_member": "STAGE_MEMBER",
                "energy": "ENERGY",
                "hand": "HAND",
            }
            if unit_type in unit_type_map:
                frame["params"]["per_unit"] = unit_type_map[unit_type]

    if action_name == "draw_cards":
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "look_at_cards":
        frame["slot"] = {"source_zone": map_zone(payload.get("source", "deck_top"))}
        if payload.get("target") == "selected_player":
            frame["attr"]["target_player"] = "SELECTED_PLAYER"

    elif action_name == "select_from_looked_at_cards":
        selection = payload.get("selection", {})
        target_slot = "HAND"
        remainder_zone = payload.get("remainder_zone", "DISCARD")
        if selection.get("destination") == "deck_bottom":
            target_slot = "DECK"
        
        frame["op"] = "LOOK_AND_CHOOSE"
        frame["value"] = {
            "count": payload.get("count", 1),
            "reveal": 1 if payload.get("reveal", True) else 0,
        }
        frame["attr"] = {"is_optional": 1} if payload.get("may") else {}
        
        # Add heart threshold filter if present
        if payload.get("value_threshold") is not None:
            frame["attr"]["value_threshold"] = payload["value_threshold"]
        if payload.get("is_le") is not None:
            frame["attr"]["is_le"] = 1 if payload["is_le"] else 0
        if payload.get("is_cost_type") is not None:
            frame["attr"]["is_cost_type"] = 1 if payload["is_cost_type"] else 0
        
        # Add group filter if present
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        
        # Add card type filter if present
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])
        frame["slot"] = {
            "target_slot": target_slot,
            "source_zone": "DECK_TOP",
            "remainder_zone": remainder_zone,
        }

    elif action_name == "add_to_hand":
        source = map_zone(payload.get("source", "waitroom"))
        # Check for yell_pile in text
        text = str(payload.get("text", "")).lower()
        if "yell" in text or "エール" in text:
            source = "YELL"
        recover_opcode = _maybe_recover_opcode(payload)
        if recover_opcode:
            frame["op"] = recover_opcode
        frame["slot"] = {"source_zone": source, "target_slot": "HAND"}
        if payload.get("may") or payload.get("reveal"):
            frame["attr"]["is_optional"] = 1
        if recover_opcode and payload.get("card_type") == "live_card":
            frame["attr"].pop("target_player", None)
            # Use group_id if group is present, otherwise use zone_mask
            if payload.get("group"):
                frame["attr"]["group_enabled"] = 1
                frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
            else:
                frame["attr"]["zone_mask"] = "ALL"
        elif payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])
        # Add cost_limit filtering attributes
        if payload.get("cost_limit"):
            frame["attr"]["value_enabled"] = 1
            frame["attr"]["value_threshold"] = payload["cost_limit"]
            frame["attr"]["is_le"] = 1
            frame["attr"]["is_cost_type"] = 1

    elif action_name == "discard_to_waitroom":
        source = map_zone(payload.get("source", "hand"))
        frame["slot"] = {"source_zone": source, "dest_zone": "DISCARD"}
        # Only add zone_mask for hand/stage sources, not for deck/waitroom
        if source in ["HAND", "STAGE"]:
            frame["attr"]["zone_mask"] = "Guest+Friend"

    elif action_name == "member_to_wait":
        if payload.get("target") == "opponent":
            frame["op"] = "TAP_OPPONENT"
        else:
            frame["op"] = "SET_TAPPED"
        frame["slot"] = {"source_zone": map_zone(payload.get("source", "stage")), "target_slot": "CONTEXT"}
        if payload.get("target"):
            frame["attr"]["target_player"] = "OPPONENT" if payload["target"] == "opponent" else "SELF"
        # Add blade count filter if present
        original_blade_count = payload.get("original_blade_count")
        original_blade_operator = payload.get("original_blade_operator")
        if original_blade_count is not None and original_blade_operator:
            filter_map = {
                "<=": "BLADE_LE2",
                "<": "BLADE_LT",
                ">=": "BLADE_GE",
                ">": "BLADE_GT",
                "==": "BLADE_EQ"
            }
            if original_blade_operator in filter_map:
                frame["params"] = {"filter": filter_map[original_blade_operator]}

    elif action_name in {"place_on_deck"}:
        destination = map_zone(payload.get("destination", "deck_top"))
        frame["op"] = "MOVE_TO_DECK"
        frame["slot"] = {"dest_zone": destination, "source_zone": map_zone(payload.get("source", "waitroom"))}
        if payload.get("order"):
            frame["attr"]["order"] = payload["order"]

    elif action_name == "select_member":
        frame["op"] = "SELECT_MEMBER"
        frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        frame["attr"]["zone_mask"] = "Guest+Friend"
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("character"):
            frame["attr"]["unique_names"] = 1
            frame["attr"]["unit_id"] = _char_id(payload["character"])
        if payload.get("target") == "opponent":
            frame["attr"]["target_player"] = "OPPONENT"
        if payload.get("cost_limit") is not None:
            frame["attr"]["value_enabled"] = 1
            frame["attr"]["value_threshold"] = payload["cost_limit"]
            frame["attr"]["is_le"] = 1
            frame["attr"]["is_cost_type"] = 1

    elif action_name == "choose_heart":
        frame["op"] = "COLOR_SELECT"
        heart_types = payload.get("heart_types", [])
        color_mask = _heart_types_to_color_mask(heart_types)
        frame["attr"] = {"target_player": "SELF", "color_mask": color_mask}
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "gain_resource":
        resource = payload.get("resource", "")
        heart_types = payload.get("heart_types", [])
        per_unit = payload.get("per_unit", "")
        multiplier = payload.get("multiplier", False)
        unit_type = payload.get("unit_type", "")
        
        # Determine opcode based on resource field
        is_heart = (resource == "heart" or 
                   resource == "ハート" or
                   (isinstance(resource, str) and "heart" in resource.lower()) or
                   heart_types)
        
        if is_heart:
            frame["op"] = "ADD_HEARTS"
            frame["attr"] = {"target_player": "SELF"}
            # Add compare_accumulated if per_unit is success_live or if it's a multiplier with card unit
            if per_unit == "success_live" or (multiplier and unit_type == "card"):
                frame["attr"]["compare_accumulated"] = 1
                frame["attr"]["remainder_zone"] = "SUCCESS_PILE"
                frame["attr"]["is_dynamic"] = 1
            # Add heart_type if specific heart types specified
            if heart_types:
                # For ADD_HEARTS, preserve original heart type format (e.g., "HEART03") instead of converting to color mask
                if len(heart_types) == 1:
                    ht = heart_types[0].upper().replace("HEART", "").replace("{{", "").replace("}}", "").strip()
                    if ht in {"01", "02", "03", "04", "05", "06"}:
                        frame["attr"]["heart_type"] = f"HEART{ht}"
                    else:
                        color_mask = _heart_types_to_color_mask(heart_types)
                        if color_mask != "ANY":
                            frame["attr"]["heart_type"] = color_mask
                else:
                    color_mask = _heart_types_to_color_mask(heart_types)
                    if color_mask != "ANY":
                        frame["attr"]["heart_type"] = color_mask
            # Check for SELECTED heart type
            elif payload.get("heart_type") == "SELECTED":
                frame["attr"]["heart_type"] = "SELECTED"
        else:
            frame["op"] = "ADD_BLADES"
            frame["attr"] = {}
        
        frame["slot"] = {"target_slot": "CONTEXT"}
        
        # Set value
        if not frame.get("value"):
            frame["value"] = payload.get("count", payload.get("resource_count", 1))
        
        # Add multiplier parameter for other cases
        if multiplier:
            frame["params"] = {"multiplier": True}

    elif action_name == "add_score":
        frame["op"] = "BOOST_SCORE"
        frame["value"] = payload.get("amount", 1)
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "pay_energy":
        frame["op"] = "PAY_ENERGY"
        frame["value"] = payload.get("count", payload.get("energy", 1))
        frame["slot"] = {"target_slot": "CONTEXT"}
        if payload.get("optional"):
            frame["attr"]["is_optional"] = 1

    elif action_name == "deploy_to_stage":
        # Handle deploy_to_stage based on source zone
        source = payload.get("source", "hand")
        card_type = payload.get("card_type", "member_card")
        target = payload.get("target", "self")
        
        if source == "waitroom":
            frame["op"] = "SELECT_DISCARD_PLAY" if card_type == "member_card" else "SELECT_DISCARD_LIVE"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "DISCARD"}
        elif source == "hand":
            frame["op"] = "PLAY_MEMBER_FROM_HAND"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        else:
            # Default to hand if source not specified
            frame["op"] = "PLAY_MEMBER_FROM_HAND"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        
        # Set count if present
        if payload.get("count") is not None:
            frame["value"] = payload.get("count")
        if payload.get("up_to") is not None:
            frame["attr"]["up_to"] = 1
        
        # Set card type filter
        if card_type:
            frame["attr"]["card_type"] = _card_type(card_type)
        
        # Set group filter if present
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))

    elif action_name == "place_card":
        destination = payload.get("destination", "waitroom")
        source = payload.get("source", "")
        card_type = payload.get("card_type", "")
        target = payload.get("target", "")
        state = payload.get("state", "")
        
        # Map source and destination to opcode
        source_zone = map_zone(source)
        dest_zone = map_zone(destination)
        
        # Determine opcode based on source/destination combination
        if source_zone == "ENERGY" and dest_zone == "STAGE" and card_type == "energy_card":
            frame["op"] = "ENERGY_CHARGE"
            frame["slot"] = {"source_zone": "ENERGY"}
        elif source_zone == "ENERGY" and card_type == "energy_card" and state == "wait":
            frame["op"] = "PLACE_ENERGY_UNDER_MEMBER"
            frame["slot"] = {"source_zone": "ENERGY"}
        elif dest_zone == "DECK":
            frame["op"] = "MOVE_TO_DECK"
            frame["slot"] = {"source_zone": source_zone, "dest_zone": dest_zone}
        elif dest_zone == "SUCCESS_PILE":
            frame["op"] = "MOVE_TO_SUCCESS"
            frame["slot"] = {"source_zone": source_zone or "HAND", "target_slot": "CONTEXT"}
        elif source_zone == "DISCARD" and dest_zone == "STAGE":
            frame["op"] = "PLAY_MEMBER_FROM_DISCARD" if card_type == "member_card" else "PLAY_LIVE_FROM_DISCARD"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "DISCARD", "is_baton_slot": 1}
        elif source_zone == "HAND" and dest_zone == "STAGE":
            frame["op"] = "PLAY_MEMBER_FROM_HAND"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        else:
            frame["slot"] = {"source_zone": source_zone, "dest_zone": dest_zone, "target_slot": "CONTEXT"}

    elif action_name == "activate_energy":
        frame["op"] = "ACTIVATE_ENERGY"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "play_member_from_hand":
        frame["op"] = "PLAY_MEMBER_FROM_HAND"
        frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        frame["attr"]["zone_mask"] = "Guest+Friend"
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])

    elif action_name == "play_member_from_discard":
        frame["op"] = "PLAY_MEMBER_FROM_DISCARD"
        frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "DISCARD"}
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])

    elif action_name == "play_live_from_discard":
        frame["op"] = "PLAY_LIVE_FROM_DISCARD"
        frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "DISCARD"}
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])

    elif action_name == "activate_member":
        frame["op"] = "ACTIVATE_MEMBER"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name in {"reduce", "reduce_cost"}:
        heart_types = payload.get("heart_types", [])
        if heart_types or "必要ハート" in str(payload.get("text", "")) or "ハート" in str(payload.get("text", "")):
            frame["op"] = "REDUCE_HEART_REQ"
            # Use heart_types count as value
            if heart_types:
                frame["value"] = len(heart_types)
                # Store heart_types count in attr to prevent regex overwriting
                frame.setdefault("attr", {})["heart_types_count"] = len(heart_types)
            elif payload.get("amount"):
                frame["value"] = payload.get("amount")
        else:
            frame["op"] = "REDUCE_COST"
        frame["slot"] = {"target_slot": "CONTEXT"}
        
        # Generate COUNT_STAGE before REDUCE_HEART_REQ when there's a group filter with multiplier
        # Check both action payload and effect-level condition
        group = payload.get("group")
        if not group and effect_data.get("condition"):
            group = effect_data["condition"].get("group")
        multiplier = payload.get("multiplier") or payload.get("per_unit") or effect_data.get("multiplier")
        
        if group and multiplier:
            group_id = _group_or_char_id(group, payload.get("group_type") or effect_data.get("condition", {}).get("group_type"))
            count_frame = _frame("COUNT_STAGE", idx, 0)
            count_frame["attr"] = {"unit_enabled": 1, "group_id": group_id}
            count_frame["slot"] = {"target_slot": "STAGE_0", "comparison": "GE"}
            frames.append(count_frame)
            idx += 1
            # Set REDUCE_HEART_REQ to use accumulated count
            frame["attr"]["compare_accumulated"] = 1
            # Add scalar_dynamic params for authored-style structure
            frame.setdefault("params", {})["scalar_dynamic"] = {"base_value": frame.get("value", 1), "divisor": 1}
        # Also add compare_accumulated if effect has multiplier even without group (for area_move case)
        if effect_data.get("condition") and effect_data["condition"].get("group") and frame["op"] == "REDUCE_HEART_REQ":
            frame["attr"]["compare_accumulated"] = 1
            # Add scalar_dynamic params for authored-style structure
            frame.setdefault("params", {})["scalar_dynamic"] = {"base_value": frame.get("value", 1), "divisor": 1}
        
        # Handle hand-based cost reduction (e.g., "reduce by 1 per other hand card")
        if payload.get("source") == "hand" or "手札" in str(payload.get("text", "")):
            frame["attr"]["zone_mask"] = "HAND"
            # If this is per-card reduction, add filter to exclude self
            if payload.get("per_card") or payload.get("per_unit") or "枚につき" in str(payload.get("text", "")) or "枚ごと" in str(payload.get("text", "")):
                frame["attr"]["not_self"] = 1
        
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        
        # Final check: add compare_accumulated if condition has group (ensure it's set after all other attr modifications)
        if effect_data.get("condition") and effect_data["condition"].get("group") and frame["op"] == "REDUCE_HEART_REQ":
            frame["attr"]["compare_accumulated"] = 1
            frame.setdefault("params", {})["scalar_dynamic"] = {"base_value": frame.get("value", 1), "divisor": 1}
        
        # Extract value with fallbacks
        if payload.get("count") is not None:
            frame["value"] = payload.get("count")
        elif payload.get("amount") is not None:
            frame["value"] = payload.get("amount")
        elif payload.get("cost_reduction") is not None:
            frame["value"] = payload.get("cost_reduction")
        
        # For REDUCE_COST, extract reduction amount from text if not already set
        if frame["op"] == "REDUCE_COST" and frame.get("value") == 0:
            # effect_data may have actions array with _full_text in first action
            if effect_data:
                if isinstance(effect_data, dict) and "_full_text" in effect_data:
                    effect_text = effect_data["_full_text"]
                elif isinstance(effect_data, dict) and "actions" in effect_data and len(effect_data["actions"]) > 0:
                    effect_text = effect_data["actions"][0].get("_full_text", "")
                else:
                    effect_text = ""
            else:
                effect_text = ""
            
            if effect_text:
                import re
                cost_reduce_match = re.search(r"コストは(\d+)減る", effect_text)
                if cost_reduce_match:
                    frame["value"] = int(cost_reduce_match.group(1))

    elif action_name == "increase_heart_cost":
        frame["op"] = "INCREASE_HEART_COST"
        frame["slot"] = {"target_slot": "CONTEXT"}
        hearts = payload.get("heart_types", [])
        if hearts:
            frame["attr"] = {"color_mask": hearts[0] if isinstance(hearts[0], str) else str(hearts[0])}
            # Set value to 1 for heart type modifications (generic increase by 1)
            frame["value"] = 1

    elif action_name == "reduce_heart_cost":
        frame["op"] = "REDUCE_HEART_REQ"
        frame["slot"] = {"target_slot": "CONTEXT"}
        # Use heart_types count as value
        heart_types = payload.get("heart_types", [])
        if heart_types:
            frame["value"] = len(heart_types)
        elif payload.get("amount"):
            frame["value"] = payload["amount"]

    elif action_name in {"deploy_to_stage", "may_deploy_to_stage"}:
        source = map_zone(payload.get("source", "hand"))
        if source == "DISCARD":
            frame["op"] = "PLAY_MEMBER_FROM_DISCARD"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "DISCARD"}
        elif source == "STAGE":
            frame["op"] = "PLAY_MEMBER_FROM_DISCARD"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "STAGE"}
        else:
            frame["op"] = "PLAY_MEMBER_FROM_HAND"
            frame["slot"] = {"target_slot": "CONTEXT", "source_zone": "HAND"}
        frame["attr"]["zone_mask"] = "Guest+Friend"
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])
        if action_name.startswith("may_") or payload.get("may"):
            frame["attr"]["is_optional"] = 1

    elif action_name in {"position_change", "may_position_change", "move_member", "may_move", "select_area"}:
        frame["op"] = "MOVE_MEMBER"
        frame["slot"] = {
            "target_slot": "CONTEXT",
            "source_zone": map_zone(payload.get("source", "stage")),
        }
        if payload.get("destination"):
            frame["slot"]["dest_zone"] = map_zone(payload["destination"])
        if payload.get("target"):
            frame["attr"]["target_player"] = "OPPONENT" if payload["target"] == "opponent" else "SELF"
        if action_name.startswith("may_") or payload.get("may"):
            frame["attr"]["is_optional"] = 1

    elif action_name == "opponent_selects":
        frame["op"] = "OPPONENT_CHOOSE"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["value"] = payload.get("count", 1)

    elif action_name == "select_card":
        source_zone = map_zone(payload.get("source", "waitroom"))
        card_type = _card_type(payload.get("card_type", ""))
        if source_zone == "DISCARD" and card_type in {"LIVE", "MEMBER"}:
            frame["op"] = "RECOVER_LIVE" if card_type == "LIVE" else "RECOVER_MEMBER"
        else:
            frame["op"] = "SELECT_CARDS"
        frame["slot"] = {"target_slot": "CONTEXT", "source_zone": source_zone}
        frame["value"] = payload.get("count", 1)
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])
        if payload.get("card_names"):
            frame["params"] = {"card_names": payload["card_names"]}

    elif action_name == "gain_ability":
        frame["op"] = "GRANT_ABILITY"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["attr"] = {"target_player": "SELF"}
        # Set value to 1 if not specified
        if not frame.get("value"):
            frame["value"] = 1
        frame["params"] = {"raw_effect": payload.get("ability", "")}

    elif action_name == "modify_cost":
        amount = payload.get("amount", 0)
        reference_mode = payload.get("reference_mode", "")
        source = payload.get("source", "")
        operator = payload.get("operator", "")
        if reference_mode == "relative_cost" or source == "selected_member_original_cost":
            frame["op"] = "SYNC_COST"
            frame["slot"] = {"target_slot": "CONTEXT"}
            frame["value"] = amount
            frame["params"] = {
                "reference": payload.get("reference", ""),
                "source": source,
                "operator": operator,
            }
        elif operator == "-":
            frame["op"] = "REDUCE_COST"
            frame["slot"] = {"target_slot": "CONTEXT"}
            frame["value"] = amount
        else:
            frame["op"] = "INCREASE_COST"
            frame["slot"] = {"target_slot": "CONTEXT"}
            frame["value"] = amount
        if payload.get("duration"):
            frame["params"] = dict(frame.get("params", {}), duration=payload["duration"])

    elif action_name == "invalidate_ability":
        frame["op"] = "NEGATE_EFFECT"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["value"] = payload.get("count", 1)
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))

    elif action_name == "select_player":
        frame["op"] = "SELECT_PLAYER"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "may_add_to_hand":
        frame["op"] = "ADD_TO_HAND"
        frame["slot"] = {"source_zone": map_zone(payload.get("source", "waitroom")), "target_slot": "HAND"}
        frame["attr"]["is_optional"] = 1

    elif action_name == "activation_restriction":
        frame["op"] = "RESTRICTION"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "repeat_same_effect":
        frame["op"] = "SYNC_COST"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "cannot_become_active":
        frame["op"] = "PREVENT_ACTIVATE"
        frame["attr"] = {"phase": "ACTIVE"}
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "cannot_activate":
        frame["op"] = "PREVENT_ACTIVATE"
        frame["attr"] = {"phase": "ACTIVE"}
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "cannot":
        frame["op"] = "RESTRICTION"
        frame["slot"] = {"target_slot": "CONTEXT"}
        if payload.get("target"):
            frame["attr"]["target_player"] = "OPPONENT" if payload.get("target") == "opponent" else "SELF"

    elif action_name == "cannot_baton_touch":
        frame["op"] = "PREVENT_BATON_TOUCH"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "may_baton_touch":
        frame["op"] = "BATON_TOUCH_MOD"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["attr"]["is_optional"] = 1

    elif action_name == "cannot_place":
        frame["op"] = "PREVENT_SET_TO_SUCCESS_PILE"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "treat_as":
        frame["op"] = "TYPE_CHECK"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["attr"] = {"card_type": "LIVE"}

    elif action_name == "transform_blades":
        frame["op"] = "TRANSFORM_BLADES"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "transform_heart":
        frame["op"] = "TRANSFORM_HEART"
        frame["slot"] = {"target_slot": "CONTEXT"}
        if payload.get("count") is not None:
            frame["value"] = payload.get("count", 1)
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))

    elif action_name == "heart_cost_modifier":
        frame["op"] = "SET_HEART_COST"
        frame["slot"] = {"target_slot": "CONTEXT"}
        hearts = payload.get("heart_types", [])
        if hearts:
            frame["value"] = {"choices": hearts}

    elif action_name == "set_state":
        text = payload.get("text", "")
        state_name = payload.get("state_name", "")
        if "ハート" in state_name or "ハート" in text:
            frame["op"] = "TRANSFORM_HEART"
        elif "コスト" in state_name or "必要ハート" in state_name or "必要ハート" in text:
            frame["op"] = "SET_HEART_COST"
        elif "スコア" in state_name or "スコア" in text:
            frame["op"] = "SET_SCORE"
        elif "アクティブ" in text or "アクティブ" in state_name:
            frame["op"] = "SET_TAPPED"
        frame["slot"] = {"target_slot": "CONTEXT"}
        if payload.get("value") is not None:
            frame["value"] = payload["value"]

    elif action_name == "reduce_score":
        frame["op"] = "SET_SCORE"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["value"] = -abs(int(payload.get("amount", 1)))

    elif action_name == "return_energy_card":
        frame["op"] = "ENERGY_CHARGE"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "set_original_blade_count":
        frame["op"] = "SET_HEART_COST"
        frame["slot"] = {"target_slot": "CONTEXT"}
        frame["value"] = payload.get("value", 3)

    elif action_name == "formation_change":
        frame["op"] = "FORMATION_CHANGE"
        frame["slot"] = {"target_slot": "CONTEXT"}

    elif action_name == "retry_cheer":
        frame["op"] = "REVEAL_CARDS"
        frame["slot"] = {"target_slot": "HAND"}
        frame["attr"] = {"card_type": "LIVE", "is_optional": 1}
        frame["value"] = 1

    elif action_name == "selected_discarded_member_card":
        frame["op"] = "SELECT_CARDS"
        frame["slot"] = {"source_zone": "DISCARD", "target_slot": "CONTEXT"}

    elif action_name == "select_card":
        frame["op"] = "SELECT_CARDS"
        source = map_zone(payload.get("source", "discard"))
        frame["slot"] = {"source_zone": source, "target_slot": "CONTEXT"}
        if payload.get("count") is not None:
            frame["value"] = payload.get("count", 1)
        if payload.get("card_type"):
            frame["attr"]["card_type"] = _card_type(payload["card_type"])
        if payload.get("group"):
            frame["attr"]["group_enabled"] = 1
            frame["attr"]["group_id"] = _group_or_char_id(payload["group"], payload.get("group_type"))
        if payload.get("target") == "opponent":
            frame["attr"]["target_player"] = "OPPONENT"

    idx += 1
    return frame, idx


def convert_condition_to_frames(condition_data: Dict[str, Any], frame_index: int) -> tuple[List[Dict], int]:
    """Convert condition to COUNT frame with JUMP_IF_FALSE."""
    idx = frame_index
    frames: List[Dict[str, Any]] = []

    cond_type = condition_data.get("type", "")
    value = condition_data.get("value", condition_data.get("count", 0))
    operator = condition_data.get("operator") or condition_data.get("comparison") or "GE"
    target = condition_data.get("target", "self")
    location = condition_data.get("location", "")
    card_type = condition_data.get("card_type", "")
    group = condition_data.get("group", "")
    group_type = condition_data.get("group_type", "")
    text = condition_data.get("text", "")
    threshold = condition_data.get("threshold", "")
    attr: Dict[str, Any] = {"target_player": "SELF" if target != "opponent" else "OPPONENT"}
    slot: Dict[str, Any] = {"target_slot": "CONTEXT", "comparison": operator if operator in {"GE", "GT", "LE", "LT", "EQ", "NE"} else "GE"}

    def append_count(op: str, val: Any = value, *, extra_attr: Optional[Dict[str, Any]] = None, extra_slot: Optional[Dict[str, Any]] = None) -> tuple[List[Dict], int]:
        local_attr = dict(attr)
        if extra_attr:
            local_attr.update(extra_attr)
        # Filter out None values from attr
        local_attr = {k: v for k, v in local_attr.items() if v is not None}
        local_slot = dict(slot)
        if extra_slot:
            local_slot.update(extra_slot)
        return [_frame(op, idx, val, attr=local_attr if local_attr else None, slot=local_slot), _frame("JUMP_IF_FALSE", idx + 1, 1)], idx + 2

    if cond_type in {"card_count_at_least", "card_count_at_most", "hand_card_count_at_most", "hand_card_count_at_least", "hand_card_count_greater_than", "card_count", "exact_count"}:
        if "hand" in cond_type:
            opcode = "COUNT_HAND"
        elif "discard" in location or "discard" in cond_type:
            opcode = "COUNT_DISCARD"
        elif "success_live" in location:
            opcode = "COUNT_SUCCESS_LIVE"
        elif "success" in location and "score" in text:
            opcode = "COUNT_SUCCESS_LIVE_SCORE"
        elif "deck" in location:
            opcode = "COUNT_DISCARD"
        else:
            opcode = "COUNT_STAGE"
        if cond_type in {"card_count_at_most", "hand_card_count_at_most"}:
            slot["comparison"] = "LE"
        elif cond_type in {"hand_card_count_greater_than"}:
            slot["comparison"] = "GT"
        frames, idx = append_count(opcode)
        return frames, idx

    if cond_type in {"energy_at_least", "energy_comparison", "energy_count_greater_than"}:
        slot["comparison"] = operator if operator in {"GE", "GT", "LE", "LT", "EQ", "NE"} else "GE"
        frames, idx = append_count("COUNT_ENERGY")
        return frames, idx

    if cond_type == "state" and condition_data.get("card_type") == "member_card" and condition_data.get("value") == "wait":
        # Convert "tapped member" condition to SELECT_MEMBER frame
        target_player = condition_data.get("target", "SELF")
        attr = {"target_player": target_player.upper(), "is_tapped": 1}
        
        # Extract group from condition text if present
        group = condition_data.get("group", "")
        if group:
            group_id = _group_or_char_id(group, condition_data.get("group_type"))
            if group_id:
                attr["group_enabled"] = 1
                attr["group_id"] = group_id
        
        frames.append(_frame("SELECT_MEMBER", idx, 1, attr=attr, slot={"target_slot": "STAGE_0", "comparison": "GE"}))
        idx += 1
        frames.append(_frame("JUMP_IF_FALSE", idx, 1))
        idx += 1
        return frames, idx

    if cond_type == "state" and (location == "energy" or "エネルギー" in text) and condition_data.get("value") == "active":
        # Convert "all energy active" condition
        if "すべて" in text or "all" in text.lower():
            # Check if all energy is active by comparing total energy count to active energy count
            # Count total energy
            frames.append(_frame("COUNT_ENERGY", idx, 0, slot={"target_slot": "STAGE_0"}))
            idx += 1
            # Count active energy (target_player: None means active/untapped)
            frames.append(_frame("COUNT_ENERGY", idx, 0, attr={"target_player": None}, slot={"target_slot": "STAGE_0"}))
            idx += 1
            # Compare: total energy == active energy
            frames.append(_frame("EQ", idx))
            idx += 1
            frames.append(_frame("JUMP_IF_FALSE", idx, 1))
            idx += 1
            return frames, idx
        else:
            # Just check if at least 1 energy is active
            frames, idx = append_count("COUNT_ENERGY", val=1, extra_attr={"target_player": None}, extra_slot={"target_slot": "STAGE_0"})
            return frames, idx

    if cond_type in {"score_sum_at_least", "has_score"}:
        frames, idx = append_count("SCORE_TOTAL_CHECK")
        return frames, idx

    if cond_type in {"score_comparison", "score_comparison"}:
        slot["comparison"] = operator if operator in {"GE", "GT", "LE", "LT", "EQ", "NE"} else "GE"
        frames, idx = append_count("SCORE_COMPARE")
        return frames, idx

    if cond_type in {"member_count_at_least", "member_count_exact"}:
        if group:
            group_type = condition_data.get("group_type")
            extra_attr = {"group_enabled": 1, "group_id": _group_or_char_id(group, group_type)}
            # Add unique_names if condition specifies different names
            if condition_data.get("names_different") or condition_data.get("different_name"):
                extra_attr["unique_names"] = 1
            # Add all_areas if condition specifies all areas
            if "エリアすべて" in text or "all_areas" in text.lower():
                extra_attr["all_areas"] = 1
            frames, idx = append_count("COUNT_GROUP", extra_attr=extra_attr)
        else:
            frames, idx = append_count("COUNT_STAGE")
        return frames, idx

    if cond_type == "unique_names_count":
        frames, idx = append_count("COUNT_STAGE", extra_attr={"unique_names": 1}, extra_slot={"target_slot": "STAGE_0"})
        return frames, idx

    if cond_type in {"member_presence", "card_presence", "presence"}:
        if "success" in location or "成功" in text:
            frames, idx = append_count(
                "COUNT_SUCCESS_LIVE",
                extra_attr={"card_type": _card_type(card_type)} if card_type else None,
                extra_slot={"target_slot": "STAGE_0"},
            )
        else:
            frames, idx = append_count("HAS_MEMBER", extra_attr={"card_type": _card_type(card_type)} if card_type else None)
        return frames, idx

    if cond_type in {"character_presence"}:
        char_id = _char_id(condition_data.get("char_name") or condition_data.get("character") or condition_data.get("name", ""))
        extra_attr = {"char_id_1": char_id} if char_id else {}
        frames, idx = append_count("HAS_KEYWORD", extra_attr=extra_attr)
        return frames, idx

    # Success live card count equality (self vs opponent)
    if cond_type == "card_count" and "成功ライブカード置き場" in text and "自分と相手" in text:
        frames.append(_frame("RETURN", idx, 0, params={"raw_cond": "SUCCESS_LIVE_COUNT_EQUAL_OPPONENT"}))
        idx += 1
        frames.append(_frame("JUMP_IF_FALSE", idx, 1))
        idx += 1
        return frames, idx
    
    if cond_type in {"group"}:
        group_type = condition_data.get("group_type")
        threshold = condition_data.get("threshold")
        different_name = condition_data.get("different_name", False)
        
        # Extract numeric value from text (e.g., "2人以上" -> 2)
        numeric_value = value
        if isinstance(value, str) and not value.isdigit():
            import re
            num_match = re.search(r'(\d+)', value)
            if num_match:
                numeric_value = int(num_match.group(1))
            else:
                num_match = re.search(r'(\d+)', text)
                if num_match:
                    numeric_value = int(num_match.group(1))
        
        # Determine if this is a unit condition (member_card group) or regular group
        is_unit = card_type == "member_card" or group_type == "unit"
        
        # Build attributes
        extra_attr = {}
        extra_slot = {"target_slot": "STAGE_0"} if location == "stage" else {}
        
        if different_name:
            extra_attr["unique_names"] = 1
        
        if is_unit:
            extra_attr["unit_enabled"] = 1
            unit_id = _group_or_char_id(group or value, "unit")
            if unit_id:
                extra_attr["unit_id"] = unit_id
        else:
            extra_attr["group_enabled"] = 1
            group_id = _group_or_char_id(group or value, group_type)
            if group_id:
                extra_attr["group_id"] = group_id
        
        if threshold and "ブレード" in text:
            # Convert group with threshold to COUNT_BLADES
            # First add SELECT_MEMBER frame for group selection
            if group:
                group_id = _group_or_char_id(group, group_type)
                frames.append(_frame("SELECT_MEMBER", idx, 1, attr={"target_player": "SELF", "group_enabled": 1, "group_id": group_id}, slot={"target_slot": "CONTEXT", "source_zone": "STAGE"}))
                idx += 1
            # Then add COUNT_BLADES with threshold as value
            frames, idx = append_count("COUNT_BLADES", val=threshold)
        elif threshold:
            # Other group with threshold conditions
            frames, idx = append_count("COUNT_GROUP", extra_attr={"value_enabled": 1, "value_threshold": threshold, **extra_attr}, extra_slot=extra_slot)
        elif "ハート" in text or condition_data.get("heart_type") or "総数" in text:
            if condition_data.get("heart_type"):
                extra_attr["heart_type"] = condition_data["heart_type"]
            frames, idx = append_count("COUNT_HEARTS", extra_attr=extra_attr, extra_slot=extra_slot)
        else:
            # Use numeric value if available, otherwise use group_id as value
            if isinstance(numeric_value, int) and numeric_value > 0:
                frames, idx = append_count("COUNT_GROUP", val=numeric_value, extra_attr=extra_attr, extra_slot=extra_slot)
            else:
                group_id_value = group or value or text
                frames, idx = append_count("COUNT_GROUP", extra_attr=extra_attr, extra_slot=extra_slot)
        return frames, idx

    if cond_type in {"position"}:
        position_text = str(condition_data.get("position", "")).lower()
        if "center" in position_text or "center" in text:
            frames, idx = append_count("IS_CENTER")
        elif condition_data.get("destination") == "selected_area" or "別の自分のエリア" in text or "エリア1つを選ぶ" in text or "選ぶ" in text:
            frames, idx = append_count(
                "SELECT_MEMBER",
                extra_attr={"zone_mask": "Guest+Friend"},
                extra_slot={"source_zone": "STAGE"},
            )
        else:
            frames, idx = append_count("AREA_CHECK")
        return frames, idx

    if cond_type in {"area_selection_condition"}:
        area_idx = condition_data.get("area_idx", 0)
        frames, idx = append_count(
            "SELECT_MEMBER",
            extra_attr={"area_idx": area_idx},
            extra_slot={"source_zone": "STAGE"},
        )
        return frames, idx

    if cond_type in {"card_move_trigger", "move_to_waitroom_trigger", "area_move", "member_area_move"}:
        # Check if this is area_move with group filter - should generate COUNT_STAGE instead of IS_SELF_MOVE
        if cond_type == "area_move" and group:
            group_id = _group_or_char_id(group, group_type)
            frames.append(_frame("COUNT_STAGE", idx, 0, attr={"unit_enabled": 1, "group_id": group_id}, slot={"target_slot": "STAGE_0", "comparison": "GE"}))
            idx += 1
            return frames, idx
        if cond_type == "move_to_waitroom_trigger" or target == "self":
            frames, idx = append_count("IS_SELF_MOVE")
        else:
            frames, idx = append_count("HAS_MOVED")
        return frames, idx

    if cond_type in {"baton_touch_deploy"}:
        frames, idx = append_count("BATON")
        return frames, idx

    if cond_type in {"heart_count_at_least", "heart_total_at_least"}:
        extra_attr = {}
        heart_type = condition_data.get("heart_type")
        if heart_type is not None:
            extra_attr["heart_type"] = heart_type
        frames, idx = append_count("COUNT_HEARTS", extra_attr=extra_attr or None)
        return frames, idx

    if cond_type in {"heart_member_presence", "heart_card_presence", "blade_heart_presence"}:
        if condition_data.get("presence") == "absent" or "ない" in text or condition_data.get("negate"):
            frames, idx = append_count("HAS_KEYWORD")
        else:
            frames, idx = append_count("COUNT_LIVE_HEARTS")
        return frames, idx

    if cond_type in {"blade_count_at_least", "count_blades"}:
        # Check if there's a group - need to SELECT_MEMBER first
        if group:
            group_id = _group_or_char_id(group, group_type)
            if group_id:
                frames.append(_frame("SELECT_MEMBER", idx, 1, attr={"target_player": "SELF", "group_enabled": 1, "group_id": group_id}, slot={"target_slot": "CONTEXT", "source_zone": "STAGE"}))
                idx += 1
        frames, idx = append_count("COUNT_BLADES", val=threshold if threshold else value)
        return frames, idx

    if cond_type in {"cost_comparison", "cost_at_least", "cost_total_equal", "member_deploy_cost", "highest_cost_center"}:
        if "highest" in text or cond_type == "highest_cost_center":
            frames, idx = append_count("COST_CHECK", extra_attr={"is_center": 1, "is_highest": 1})
        elif cond_type == "cost_total_equal":
            frames, idx = append_count("CALC_SUM_COST")
        elif cond_type == "member_deploy_cost":
            frames, idx = append_count("GROUP_FILTER")
        elif location == "stage" and condition_data.get("min_cost"):
            # Convert cost-based stage condition to COUNT_STAGE with min_cost
            min_cost = condition_data.get("min_cost", condition_data.get("cost_limit", value))
            frames, idx = append_count("COUNT_STAGE", val=1, extra_attr={"min_cost": min_cost}, extra_slot={"target_slot": "STAGE_0"})
        else:
            frames, idx = append_count("REDUCE_COST")
        return frames, idx

    if cond_type in {"pay_energy_condition", "main_phase", "turn_phase", "live_start_trigger"}:
        frames, idx = append_count("MAIN_PHASE")
        return frames, idx

    if cond_type in {"reveal_cards", "all_revealed_cards_match"}:
        frames, idx = append_count("REVEAL_CARDS", extra_attr={"card_type": _card_type(card_type)} if card_type else None)
        return frames, idx

    if cond_type in {"deck_refresh"}:
        frames, idx = append_count("DECK_REFRESHED")
        return frames, idx

    if cond_type in {"surplus_heart_equal"}:
        frames, idx = append_count("HAS_EXCESS_HEART")
        return frames, idx

    if cond_type in {"opponent_optional_discard"}:
        frames, idx = append_count("SELECT_MODE")
        return frames, idx

    if cond_type in {"all_areas"}:
        frames, idx = append_count("AREA_CHECK")
        return frames, idx

    if cond_type in {"or_trigger", "compound"} and isinstance(condition_data.get("conditions"), list):
        current_idx = idx
        for sub in condition_data["conditions"]:
            sub_frames, current_idx = convert_condition_to_frames(sub, current_idx)
            frames.extend(sub_frames)
        return frames, current_idx

    return [], idx

def convert_effect_to_frames(effect_data: Dict[str, Any], frame_index: int) -> tuple[List[Dict], int]:
    """Convert effect object to effect frames."""
    frames = []
    idx = frame_index
    
    effect_text = effect_data.get("text", "")
    actions = effect_data.get("actions", [])
    
    # Handle condition first
    condition_data = effect_data.get("condition")
    if condition_data:
        # Check if this is a multiplier condition (e.g., "X人につき")
        is_multiplier = condition_data.get("multiplier", False)
        cond_frames, idx = convert_condition_to_frames(condition_data, idx)
        frames.extend(cond_frames)
        # For multiplier conditions, add DIV_VALUE frame to multiply the effect
        if is_multiplier:
            frames.append({
                "op": "DIV_VALUE",
                "frame_index": idx,
                "value": condition_data.get("multiplier_value", 1)
            })
            idx += 1
    
    # Check for choice: true (SELECT_MODE branching)
    is_choice = effect_data.get("choice", False)
    if is_choice:
        # Reconstruct actions array if missing (parser may not have populated it)
        if not actions or len(actions) == 0:
            options = effect_data.get("options", [])
            if "member" in options and "energy" in options:
                member_count = effect_data.get("member_count", 1)
                energy_count = effect_data.get("energy_count", 1)
                actions = [
                    {"action": "activate_member", "count": member_count, "target": "self", "source": "stage"},
                    {"action": "activate_energy", "count": energy_count}
                ]
                effect_data["actions"] = actions
        # Generate SELECT_MODE + JUMP branching for choices
        num_choices = len(actions)
        frames.append(_frame("SELECT_MODE", idx, num_choices))
        idx += 1
        
        # Generate JUMP instructions to branch between choices
        jump_targets = []
        for i in range(num_choices):
            jump_target = idx + num_choices - i + 1  # Calculate jump target
            frames.append(_frame("JUMP", idx, jump_target))
            idx += 1
        
        # Process each choice's actions
        for i, action in enumerate(actions):
            # Convert this choice's actions to frames
            choice_frame, idx = convert_action_to_frame(action, idx)
            if choice_frame:
                frames.append(choice_frame)
            
            # Add JUMP to end after each choice (except last)
            if i < num_choices - 1:
                frames.append(_frame("JUMP", idx, num_choices + 1))
                idx += 1
        
        # Skip the normal action processing since we handled choices
        return frames, idx
    
    actions = effect_data.get("actions", [])
    i = 0
    while i < len(actions):
        action = actions[i]
        
        # Copy effect-level amount to action if not present
        if isinstance(action, dict) and "amount" in effect_data and "amount" not in action:
            action = dict(action)
            action["amount"] = effect_data["amount"]
            actions[i] = action

        if isinstance(action, dict) and isinstance(action.get("action"), dict):
            wrapper_condition = action.get("condition")
            inner_action = dict(action["action"])
            for key in ("duration", "text", "trigger", "source", "target", "count", "card_type", "heart_types", "group", "state", "may", "reveal", "selection", "reference", "reference_mode", "operator", "amount", "cost_limit"):
                if key not in inner_action and key in action:
                    inner_action[key] = action[key]
            if wrapper_condition:
                cond_frames, idx = convert_condition_to_frames(wrapper_condition, idx)
                frames.extend(cond_frames)
            action = inner_action

        if isinstance(action, dict) and action.get("condition") and isinstance(action.get("condition"), dict):
            cond_frames, idx = convert_condition_to_frames(action["condition"], idx)
            frames.extend(cond_frames)
            action = {k: v for k, v in action.items() if k != "condition"}

        # Handle furthermore_condition/furthermore_action pattern
        # This is used for "if X, then Y. Furthermore, if Z, then W" patterns
        # Authored frame pattern: META_RULE -> JUMP_IF_FALSE(skip base) -> base_action -> META_RULE -> JUMP_IF_FALSE(skip further) -> further_action
        if isinstance(action, dict) and action.get("furthermore_condition") and action.get("furthermore_action"):
            # First, add META_RULE and JUMP for furthermore condition
            further_cond = action["furthermore_condition"]
            further_action = action["furthermore_action"]
            
            # Extract group from condition if present
            group = further_cond.get("group", "")
            group_id = None
            if group:
                group_id = _group_or_char_id(group, further_cond.get("group_type"))
            
            # Determine META_RULE type based on condition
            meta_params = {}
            if further_cond.get("location") == "energy":
                meta_params["raw_cond"] = "DID_ACTIVATE_ENERGY"
                meta_params["keyword_energy"] = True
            elif further_cond.get("card_type") == "member_card":
                meta_params["raw_cond"] = "DID_ACTIVATE_MEMBER"
                meta_params["keyword_member"] = True
            
            if group_id:
                meta_params["FILTER"] = f"GROUP={group_id}"
            
            # Add META_RULE frame for furthermore condition
            frames.append(_frame("META_RULE", idx, 0, params=meta_params))
            idx += 1
            
            # Add JUMP_IF_FALSE to skip base action if furthermore condition is met
            # Jump target: skip base action (1 frame) and go to furthermore action
            frames.append(_frame("JUMP_IF_FALSE", idx, 2))
            idx += 1
            
            # Convert base action
            base_frame, idx = convert_action_to_frame(action, idx)
            if base_frame:
                frames.append(base_frame)
            
            # Convert furthermore action
            further_frame, idx = convert_action_to_frame(further_action, idx)
            if further_frame:
                frames.append(further_frame)
            
            i += 1
            continue

        if isinstance(action, dict) and action.get("action") == "unknown":
            synthesized_frames, idx = _convert_unknown_action_to_frames(action, idx)
            if synthesized_frames:
                frames.extend(synthesized_frames)
                i += 1
                continue
        
        # Merge look_at_cards + chooser-style followups into the executable frame shapes.
        if isinstance(action, dict) and action.get("action") == "look_at_cards":
            source = map_zone(action.get("source", "deck_top"))
            look_count = action.get("count", 0)
            if i + 1 < len(actions):
                next_action = actions[i + 1]
                if isinstance(next_action, dict) and next_action.get("action") in {"select_from_looked_at_cards", "add_to_hand"}:
                    selection = next_action.get("selection", {}) if next_action.get("action") == "select_from_looked_at_cards" else {}
                    choose_count = next_action.get("count", 1)
                    has_reorder_followup = False
                    if next_action.get("action") == "select_from_looked_at_cards" and selection.get("order") == "any" and i + 2 < len(actions):
                        maybe_place = actions[i + 2]
                        has_reorder_followup = isinstance(maybe_place, dict) and maybe_place.get("action") == "place_on_deck"
                    if has_reorder_followup:
                        frames.append(_frame(
                            "LOOK_REORDER_DISCARD",
                            idx,
                            look_count,
                            slot={"target_slot": "CONTEXT"},
                        ))
                        idx += 1
                        skip = 3
                        if i + 3 < len(actions):
                            maybe_discard = actions[i + 3]
                            if isinstance(maybe_discard, dict) and maybe_discard.get("action") == "discard_to_waitroom":
                                skip = 4
                        i += skip
                        continue
                    if i > 0:
                        prev_action = actions[i - 1]
                        if isinstance(prev_action, dict) and prev_action.get("action") == "move_to_discard" and prev_action.get("optional"):
                            frames.append(_frame("SUM_VALUE", idx))
                            idx += 1
                    frame = _frame(
                        "LOOK_AND_CHOOSE",
                        idx,
                        {"count": look_count, "reveal": 1},
                        attr={"target_player": "SELF"},
                        slot={
                            "target_slot": "HAND",
                            "source_zone": source,
                            "remainder_zone": "DISCARD",
                        },
                    )
                    frame["params"] = {"choose_count": choose_count}
                    if selection.get("order"):
                        frame["attr"]["order"] = selection["order"]
                    if next_action.get("may") or next_action.get("reveal"):
                        frame["attr"]["is_optional"] = 1
                    if next_action.get("action") == "add_to_hand":
                        if next_action.get("card_type"):
                            frame["attr"]["card_type"] = _card_type(next_action["card_type"])
                        if next_action.get("group"):
                            frame["attr"]["group_enabled"] = 1
                            frame["attr"]["group_id"] = _group_or_char_id(next_action["group"], next_action.get("group_type"))
                    frames.append(frame)
                    idx += 1
                    skip = 2
                    if i + 2 < len(actions):
                        maybe_discard = actions[i + 2]
                        if isinstance(maybe_discard, dict) and maybe_discard.get("action") in {"discard_to_waitroom", "member_to_wait"}:
                            skip = 3
                    i += skip
                    continue
        if isinstance(action, dict) and action.get("action") == "activate_member":
            text = str(action.get("text", "") or effect_text)
            count_value = action.get("count", 1)
            if count_value == 0 or count_value > 1 or action.get("group") or action.get("target") == "opponent" or "???" in text:
                select_frame = _frame(
                    "SELECT_MEMBER",
                    idx,
                    99 if count_value == 0 else count_value,
                    attr={"target_player": "SELF", "zone_mask": "Guest+Friend"},
                    slot={"target_slot": "CONTEXT", "source_zone": "STAGE"},
                )
                frames.append(select_frame)
                idx += 1
            frame, idx = convert_action_to_frame(action, idx, effect_data)
            if frame:
                frames.append(frame)
            i += 1
            continue

        if isinstance(action, dict) and isinstance(action.get("action"), str) and action.get("action") in {"play_member_from_hand", "deploy_to_stage", "may_deploy_to_stage"}:
            value = action.get("count", 1)
            cost_limit = action.get("cost_limit")
            text = str(action.get("text", "") or effect_text)
            source = action.get("source")
            # Determine actual source based on semantic data and text analysis
            # Priority: 1. text analysis for 控え室 (highest priority to fix parser bugs), 2. semantic source, 3. default to hand
            actual_source = source
            if "控え室" in text or "自分の控え室から" in text:
                actual_source = "waitroom"
            elif actual_source is None or actual_source == "stage":
                actual_source = source if source else "hand"
            
            # Determine destination from action name and text
            destination = "stage"  # deploy_to_stage implies stage destination
            
            if cost_limit is None:
                import re
                m = re.search(r"コスト(\d+)以下", text)
                if m:
                    cost_limit = int(m.group(1))
            
            # Base opcode on source and destination
            if actual_source == "waitroom" and destination == "stage":
                select_frame = _frame(
                    "SELECT_DISCARD_PLAY",
                    idx,
                    value,
                    attr={"target_player": "SELF"},
                    slot={"target_slot": "CONTEXT", "source_zone": "DISCARD"},
                )
            elif actual_source == "hand" and destination == "stage":
                select_frame = _frame(
                    "SELECT_MEMBER",
                    idx,
                    value,
                    attr={"target_player": "SELF", "zone_mask": "Guest+Friend"},
                    slot={"target_slot": "CONTEXT", "source_zone": "HAND"},
                )
            else:
                select_frame = _frame(
                    "SELECT_MEMBER",
                    idx,
                    value,
                    attr={"target_player": "SELF", "zone_mask": "Guest+Friend"},
                    slot={"target_slot": "CONTEXT", "source_zone": map_zone(actual_source)},
                )
            if cost_limit is not None:
                select_frame["attr"]["value_enabled"] = 1
                select_frame["attr"]["value_threshold"] = cost_limit
                select_frame["attr"]["is_le"] = 1
                select_frame["attr"]["is_cost_type"] = 1
            frames.append(select_frame)
            idx += 1
            frame, idx = convert_action_to_frame(action, idx, effect_data)
            if frame:
                frames.append(frame)
            i += 1
            continue
        
        frame, idx = convert_action_to_frame(action, idx, effect_data)
        if frame:
            # Check if action has nested 'then' action
            if isinstance(action, dict) and action.get("then"):
                then_action = action["then"]
                # Recursively convert the 'then' action
                then_frame, idx = convert_action_to_frame(then_action, idx, effect_data)
                if then_frame:
                    frames.append(then_frame)
                    # Check if the 'then' action also has a nested 'then'
                    if isinstance(then_action, dict) and then_action.get("then"):
                        then_then_action = then_action["then"]
                        then_then_frame, idx = convert_action_to_frame(then_then_action, idx, effect_data)
                        if then_then_frame:
                            frames.append(then_then_frame)
            # Check if this is draw after discard pattern
            if frame.get("op") == "DRAW" and i > 0:
                prev_action = actions[i - 1]
                if isinstance(prev_action, dict) and prev_action.get("action") == "discard_to_waitroom":
                    # Check if draw count should equal discard count
                    if action.get("count") == 0 or "equal" in action.get("text", "").lower():
                        frame["attr"]["compare_accumulated"] = 1
                        frame["value"] = 0
            if frame.get("op") in {"ADD_BLADES", "GRANT_ABILITY", "REDUCE_HEART_REQ"}:
                import re
                if frame.get("op") == "ADD_BLADES" and "???????????" in effect_text:
                    success_match = re.search(r"??([0-9?-?]+)???", effect_text)
                    if success_match:
                        count_value = _to_int(success_match.group(1))
                        frames.append(_frame(
                            "COUNT_SUCCESS_LIVE",
                            idx,
                            count_value,
                            attr={"target_player": "BOTH", "is_ge": 1},
                            slot={"target_slot": "CONTEXT"},
                        ))
                        idx += 1
                        frame["value"] = count_value
                if frame.get("op") == "GRANT_ABILITY" and "???????????" in effect_text:
                    score_match = re.search(r"???(?:???)??([0-9?-?]+)??", effect_text)
                    if score_match:
                        score_value = _to_int(score_match.group(1))
                        frames.append(_frame(
                            "COUNT_SUCCESS_LIVE",
                            idx,
                            score_value,
                            slot={"target_slot": "STAGE_0", "comparison": "GE"},
                        ))
                        idx += 1
                        frames.append(_frame(
                            "SCORE_COMPARE",
                            idx,
                            score_value,
                            slot={"target_slot": "STAGE_0", "comparison": "LE"},
                        ))
                        idx += 1
                if frame.get("op") == "REDUCE_HEART_REQ" and "???????????" in effect_text:
                    # Check if heart_types_count was set (from heart_types array)
                    if not frame.get("attr", {}).get("heart_types_count"):
                        heart_match = re.search(r"??????.*?([0-9?-?]+)?????", effect_text)
                        if heart_match:
                            reduce_value = _to_int(heart_match.group(1))
                            frames.append(_frame(
                                "COUNT_SUCCESS_LIVE",
                                idx,
                                0,
                                slot={"target_slot": "STAGE_0", "comparison": "GE"},
                            ))
                            idx += 1
                            frame["value"] = reduce_value
            frames.append(frame)
            is_optional_pay = False
            if isinstance(action, dict) and action.get("action") == "pay_energy":
                if action.get("optional"):
                    is_optional_pay = True
                elif "支払ってもよい" in str(action.get("text", "")) or "支払ってもよい" in effect_text:
                    is_optional_pay = True
                    frame.setdefault("attr", {})["is_optional"] = 1
            if isinstance(action, dict) and action.get("action") == "pay_energy" and is_optional_pay:
                jump_value = 1
                if i + 1 < len(actions):
                    next_action = actions[i + 1]
                    if isinstance(next_action, dict) and next_action.get("action") in {
                        "select_member",
                        "play_member_from_hand",
                        "play_member_from_discard",
                        "deploy_to_stage",
                        "may_deploy_to_stage",
                    }:
                        jump_value = 2
                frames.append({
                    "op": "JUMP_IF_FALSE",
                    "frame_index": idx,
                    "value": jump_value,
                })
                idx += 1
        i += 1
    
    # Post-processing: add compare_accumulated to REDUCE_HEART_REQ when effect has multiplier
    if effect_data.get("multiplier"):
        for frame in frames:
            if frame.get("op") == "REDUCE_HEART_REQ":
                frame.setdefault("attr", {})["compare_accumulated"] = 1
                frame.setdefault("params", {})["scalar_dynamic"] = {"base_value": frame.get("value", 1), "divisor": 1}
    
    return frames, idx


def convert_semantic_ability_to_frame_format(extracted_ability: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a single semantic ability to frame format."""
    full_text = extracted_ability.get("full_text", "")
    triggers = extracted_ability.get("triggers", "")
    cost_data = extracted_ability.get("cost")
    effect_data = dict(extracted_ability.get("effect", {}))
    use_limit = extracted_ability.get("use_limit")
    card_refs = extracted_ability.get("cards", [])
    is_null = extracted_ability.get("is_null", False)
    
    
    # Skip frame generation for null abilities (parenthetical notes only)
    if is_null:
        frame_ability = {
            "primary_text_jp": full_text,
            "primary_text_en": "",
            "source_ability_texts": [
                {
                    "jp": full_text,
                    "en": "",
                    "card_examples": card_refs[:3],
                }
            ],
            "trigger_id": 0,  # No trigger for null abilities
            "trigger": "NONE",
            "frames": [],  # Empty frames for null abilities
            "card_refs": [],
            "is_null": True,
        }
        if use_limit:
            frame_ability["use_limit"] = use_limit
        return frame_ability
    
    # Map trigger
    trigger_name, trigger_id = map_trigger(triggers)
    
    # Convert frames
    frames = []
    frame_index = 0
    effect_data["_full_text"] = full_text
    if isinstance(cost_data, dict):
        cost_data = dict(cost_data)
        cost_data["_full_text"] = full_text
    
    # Convert cost
    cost_jump_idx = -1  # Track where to fix jump distance later
    if cost_data:
        cost_frames, frame_index = convert_cost_to_frames(cost_data, frame_index)
        frames.extend(cost_frames)
        # If the last cost frame was JUMP_IF_FALSE with value=1, mark it for later fix
        if frames and frames[-1].get("op") == "JUMP_IF_FALSE" and frames[-1].get("value") == 1:
            cost_jump_idx = len(frames) - 1
    
    # Add once_per_turn attribute to first frame if present
    once_per_turn = extracted_ability.get("once_per_turn")
    if once_per_turn and frames:
        frames[0]["attr"] = frames[0].get("attr", {})
        frames[0]["attr"]["once_per_turn"] = 1
    
    # Add position_requirement handling (center_only, etc.)
    position_requirement = effect_data.get("position_requirement")
    if position_requirement and frames:
        frames[0]["attr"] = frames[0].get("attr", {})
        if position_requirement == "center":
            frames[0]["attr"]["center_only"] = 1
    
    # Convert effect actions
    # Check if effect has top-level condition (not inside actions)
    effect_condition = effect_data.get("condition")
    effect_action = effect_data.get("action")
    
    if effect_condition and effect_action:
        # Handle effect-level condition + action structure
        # Generate condition frames first
        cond_frames, frame_index = convert_condition_to_frames(effect_condition, frame_index)
        frames.extend(cond_frames)
        
        # Mark the JUMP_IF_FALSE after condition for later fix
        cond_jump_idx = len(frames) - 1 if frames and frames[-1].get("op") == "JUMP_IF_FALSE" else -1
        
        # Generate action frames
        if "actions" not in effect_action:
            effect_action = {"actions": [effect_action]}
        action_frames, frame_index = convert_effect_to_frames(effect_action, frame_index)
        frames.extend(action_frames)
        
        # Fix condition JUMP_IF_FALSE to skip action frames
        if cond_jump_idx >= 0 and cond_jump_idx < len(frames):
            jump_distance = len(frames) - cond_jump_idx - 1
            frames[cond_jump_idx]["value"] = jump_distance
    else:
        # Normal effect processing
        if "actions" not in effect_data and "action" in effect_data:
            effect_data = {"actions": [effect_data]}
        effect_frames, frame_index = convert_effect_to_frames(effect_data, frame_index)
        frames.extend(effect_frames)
    
    # Fix cost JUMP_IF_FALSE jump distance to skip entire effect block
    if cost_jump_idx >= 0 and cost_jump_idx < len(frames):
        jump_distance = len(frames) - cost_jump_idx - 1
        frames[cost_jump_idx]["value"] = jump_distance
    
    # Post-processing: add compare_accumulated to REDUCE_HEART_REQ when effect has multiplier
    if extracted_ability.get("effect", {}).get("multiplier"):
        for frame in frames:
            if frame.get("op") == "REDUCE_HEART_REQ":
                frame.setdefault("attr", {})["compare_accumulated"] = 1
                frame.setdefault("params", {})["scalar_dynamic"] = {"base_value": frame.get("value", 1), "divisor": 1}
    
    # Add RETURN at end, unless the cost already included a RETURN frame
    has_return_cost = any(f.get("op") == "RETURN" for f in frames)
    if not has_return_cost:
        frames.append({
            "op": "RETURN",
            "frame_index": frame_index,
        })
        frame_index += 1
    
    # Build card_refs
    formatted_card_refs = []
    for card_ref in card_refs:
        # Parse "PL!-sd1-005-SD | 星空 凛 (ab#0)" format
        parts = card_ref.split(" | ")
        if len(parts) == 2:
            card_no = parts[0].strip()
            name_part = parts[1].strip()
            # Extract ability index
            ability_index = 0
            if "(ab#" in name_part:
                idx_start = name_part.index("(ab#") + 4
                idx_end = name_part.index(")", idx_start)
                ability_index = int(name_part[idx_start:idx_end])
            formatted_card_refs.append({
                "card_no": card_no,
                "ability_index": ability_index,
                "db": "member_db",  # Default, would need proper detection
                "name": name_part.split("(ab#")[0].strip(),
                "trigger": trigger_id,
            })
    
    frame_ability = {
        "primary_text_jp": full_text,
        "primary_text_en": "",
        "source_ability_texts": [
            {
                "jp": full_text,
                "en": "",
                "card_examples": card_refs[:3],  # Show first 3 examples
            }
        ],
        "trigger_id": trigger_id,
        "trigger": trigger_name,
        "frames": frames,
        "card_refs": formatted_card_refs,
    }
    
    # Add use_limit if present
    if use_limit:
        frame_ability["use_limit"] = use_limit
    
    return frame_ability


def convert_extracted_to_frame_format(
    extracted_path: str,
    output_path: str,
) -> None:
    """Convert abilities_extracted_from_cards.json to ability_frame_source.json format."""
    with open(extracted_path, "r", encoding="utf-8-sig") as f:
        extracted_data = json.load(f)
    
    unique_abilities = extracted_data.get("unique_abilities", [])
    
    output_data = {
        "schema": "ability_frame_source.flat.v2",
        "_comment": "Generated from abilities_extracted_from_cards.json by semantic_to_frame_converter.py",
        "abilities": [],
    }
    
    for extracted_ability in unique_abilities:
        frame_ability = convert_semantic_ability_to_frame_format(extracted_ability)
        output_data["abilities"].append(frame_ability)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    
    print(f"Converted {len(unique_abilities)} abilities to frame format")
    print(f"Output written to {output_path}")


if __name__ == "__main__":
    extracted_path = "data/abilities_extracted_from_cards.json"
    output_path = "data/ability_frame_source.json"
    
    convert_extracted_to_frame_format(extracted_path, output_path)
