"""Semantic Frame Generator - Clean, human-readable effect representation.

This replaces the opcode/bit-packing compiler with a system that preserves
semantic meaning from card text all the way through to execution.
"""

import copy
import re
from typing import Any, Dict, List, Optional, Union

from engine.models.ability import Ability, Condition, ConditionType, Cost, Effect, EffectType
from engine.models.enums import Group, HeartColor, Unit
from engine.models.generated_enums import TargetType, TriggerType


class SemanticFrame:
    """A single semantic frame representing one effect or condition."""
    
    def __init__(
        self,
        frame_type: str,
        params: Dict[str, Any],
        ability_text: str = "",
        original_text: str = ""
    ):
        self.frame_type = frame_type
        self.params = params
        self.ability_text = ability_text
        self.original_text = original_text
    
    def to_dict(self) -> Dict[str, Any]:
        result = {
            "type": self.frame_type,
            **self.params
        }
        if self.ability_text:
            result["_ability_text"] = self.ability_text
        if self.original_text:
            result["_original_text"] = self.original_text
        return result


class SemanticAbility:
    """A complete ability with semantic frames and full text context."""
    
    def __init__(
        self,
        signature: str,
        trigger: str,
        frames: List[SemanticFrame],
        card_no: str = "",
        card_name: str = "",
        original_text: str = "",
        translated_text: str = ""
    ):
        self.signature = signature
        self.trigger = trigger
        self.frames = frames
        self.card_no = card_no
        self.card_name = card_name
        self.original_text = original_text
        self.translated_text = translated_text
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signature": self.signature,
            "trigger": self.trigger,
            "card_no": self.card_no,
            "card_name": self.card_name,
            "original_text": self.original_text,
            "translated_text": self.translated_text,
            "effects": [frame.to_dict() for frame in self.frames]
        }


class SemanticGenerator:
    """Generate semantic frames from parsed abilities.
    
    No opcodes. No bit-packing. Just clean, human-readable semantics.
    """
    
    # Effect type to semantic type mapping
    EFFECT_MAP = {
        EffectType.RECOVER_MEMBER: "move_cards",
        EffectType.RECOVER_LIVE: "move_cards",
        EffectType.MOVE_TO_DISCARD: "move_cards",
        EffectType.MOVE_TO_DECK: "move_cards",
        EffectType.MOVE_MEMBER: "move_member",
        EffectType.SELECT_CARDS: "select_cards",
        EffectType.SELECT_MEMBER: "select_cards",
        EffectType.SELECT_LIVE: "select_cards",
        EffectType.DRAW: "draw",
        EffectType.DRAW_UNTIL: "draw_until",
        EffectType.ADD_BLADES: "add_blades",
        EffectType.ADD_HEARTS: "add_hearts",
        EffectType.BOOST_SCORE: "boost_score",
        EffectType.REDUCE_COST: "reduce_cost",
        EffectType.TAP_MEMBER: "tap_member",
        EffectType.TAP_OPPONENT: "tap_opponent",
        EffectType.ENERGY_CHARGE: "energy_charge",
        EffectType.PAY_ENERGY: "pay_energy",
        EffectType.PLAY_MEMBER_FROM_HAND: "play_member",
        EffectType.PLAY_MEMBER_FROM_DISCARD: "play_member",
        EffectType.PLAY_LIVE_FROM_DISCARD: "play_live",
        EffectType.LOOK_AND_CHOOSE: "look_and_choose",
        EffectType.REVEAL_UNTIL: "reveal_until",
        EffectType.GRANT_ABILITY: "grant_ability",
        EffectType.SET_HEART_COST: "set_heart_cost",
        EffectType.TRANSFORM_HEART: "transform_heart",
        EffectType.TRANSFORM_COLOR: "transform_color",
        EffectType.META_RULE: "meta_rule",
        EffectType.NEGATE_EFFECT: "negate_effect",
        EffectType.JUMP_IF_FALSE: "jump_if_false",
        EffectType.RETURN: "return",
        EffectType.SET_TARGET_SELF: "set_target",
        EffectType.SET_TARGET_OPPONENT: "set_target",
    }
    
    # Zone mapping from internal to semantic
    ZONE_MAP = {
        1: "deck_top",
        2: "deck_bottom", 
        3: "energy",
        4: "stage",
        5: "deck",
        6: "hand",
        7: "discard",
        13: "live_zone",
        15: "yell",
        17: "yell_revealed",
        "DECK_TOP": "deck_top",
        "DECK": "deck",
        "HAND": "hand",
        "DISCARD": "discard",
        "ENERGY": "energy",
        "STAGE": "stage",
        "YELL": "yell",
        "LIVE_ZONE": "live_zone",
    }
    
    # Target mapping
    TARGET_MAP = {
        TargetType.SELF: "self",
        TargetType.PLAYER: "self",
        TargetType.OPPONENT: "opponent",
        TargetType.ALL_PLAYERS: "all",
        TargetType.MEMBER_SELF: "self_stage",
        TargetType.MEMBER_OTHER: "opponent_stage",
    }
    
    def __init__(self):
        self.filters = []
    
    def generate_semantic_ability(
        self,
        ability: Ability,
        card_no: str = "",
        card_name: str = "",
        original_text: str = "",
        translated_text: str = ""
    ) -> SemanticAbility:
        """Generate a complete semantic ability from a parsed ability."""
        signature = getattr(ability, 'signature', '')
        trigger = self._trigger_to_string(getattr(ability, 'trigger', TriggerType.NONE))
        
        frames = []
        instructions = self._get_instructions(ability)
        
        for instr in instructions:
            frame = self._instruction_to_frame(instr, original_text)
            if frame:
                frames.append(frame)
        
        # Add return if not present
        if not frames or frames[-1].frame_type != "return":
            frames.append(SemanticFrame("return", {}, original_text))
        
        return SemanticAbility(
            signature=signature,
            trigger=trigger,
            frames=frames,
            card_no=card_no,
            card_name=card_name,
            original_text=original_text,
            translated_text=translated_text
        )
    
    def _get_instructions(self, ability: Ability) -> List[Union[Effect, Condition, Cost]]:
        """Extract all instructions from an ability."""
        instructions = copy.deepcopy(list(getattr(ability, "instructions", []) or []))
        if not instructions:
            instructions = [
                *copy.deepcopy(getattr(ability, "costs", []) or []),
                *copy.deepcopy(getattr(ability, "conditions", []) or []),
                *copy.deepcopy(getattr(ability, "effects", []) or []),
            ]
        return instructions
    
    def _instruction_to_frame(
        self,
        instr: Union[Effect, Condition, Cost],
        original_text: str = ""
    ) -> Optional[SemanticFrame]:
        """Convert a single instruction to a semantic frame."""
        if hasattr(instr, "effect_type"):
            return self._effect_to_frame(instr, original_text)
        elif hasattr(instr, "is_negated") and hasattr(instr, "type"):
            return self._condition_to_frame(instr, original_text)
        elif hasattr(instr, "type"):
            return self._cost_to_frame(instr, original_text)
        return None
    
    def _effect_to_frame(self, eff: Effect, original_text: str) -> SemanticFrame:
        """Convert an effect to a semantic frame."""
        semantic_type = self.EFFECT_MAP.get(eff.effect_type, eff.effect_type.name.lower())
        
        # Normalize params
        params = {str(k).lower(): v for k, v in eff.params.items()} if eff.params else {}
        
        # Build semantic params based on effect type
        semantic_params = self._build_semantic_params(eff, params, semantic_type)
        
        return SemanticFrame(
            frame_type=semantic_type,
            params=semantic_params,
            ability_text=getattr(eff, 'raw_text', ''),
            original_text=original_text
        )
    
    def _build_semantic_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        semantic_type: str
    ) -> Dict[str, Any]:
        """Build semantic parameters for an effect."""
        result = {}
        
        # Common: target
        if hasattr(eff, 'target') and eff.target:
            result["target"] = self.TARGET_MAP.get(eff.target, str(eff.target))
        
        # Common: optional
        if getattr(eff, 'is_optional', False) or params.get('is_optional'):
            result["optional"] = True
        
        # Effect-specific parameters
        if semantic_type == "move_cards":
            self._build_move_cards_params(eff, params, result)
        elif semantic_type == "select_cards":
            self._build_select_cards_params(eff, params, result)
        elif semantic_type == "draw":
            result["count"] = int(eff.value) if eff.value else 1
            result["from"] = "deck"
            result["to"] = "hand"
        elif semantic_type == "draw_until":
            result["target_hand_size"] = int(eff.value) if eff.value else 5
        elif semantic_type == "add_blades":
            result["count"] = int(eff.value) if eff.value else 1
        elif semantic_type == "add_hearts":
            result["count"] = int(eff.value) if eff.value else 1
        elif semantic_type == "boost_score":
            result["amount"] = int(eff.value) if eff.value else 1
        elif semantic_type == "reduce_cost":
            result["amount"] = int(eff.value) if eff.value else 1
        elif semantic_type == "tap_member":
            result["count"] = int(eff.value) if eff.value else 1
            if "filter" in params:
                result["filter"] = self._build_semantic_filter(params)
        elif semantic_type == "play_member":
            self._build_play_member_params(eff, params, result)
        elif semantic_type == "play_live":
            self._build_play_live_params(eff, params, result)
        elif semantic_type == "look_and_choose":
            self._build_look_and_choose_params(eff, params, result)
        elif semantic_type == "energy_charge":
            result["count"] = int(eff.value) if eff.value else 1
            if params.get('wait') or params.get('state') == 'wait':
                result["wait"] = True
        elif semantic_type == "pay_energy":
            result["count"] = int(eff.value) if eff.value else 1
        elif semantic_type == "jump_if_false":
            result["offset"] = int(eff.value) if eff.value else 1
        elif semantic_type == "set_target":
            result["target"] = "self" if eff.effect_type == EffectType.SET_TARGET_SELF else "opponent"
        elif semantic_type == "meta_rule":
            m_type = str(params.get("type", params.get("meta_type", "CHEER_MOD"))).upper()
            result["rule_type"] = m_type.lower()
        elif semantic_type == "grant_ability":
            result["ability_id"] = params.get("ability_id", params.get("id", 0))
        
        return result
    
    def _build_move_cards_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Build parameters for move_cards effect."""
        effect_name = eff.effect_type.name
        
        # Determine from/to based on effect type
        if "RECOVER" in effect_name or effect_name == "RECOVER_MEMBER":
            result["from"] = self._resolve_zone(params.get('source', params.get('from', 'discard')))
            result["to"] = "hand"
        elif "RECOVER_LIVE" in effect_name:
            result["from"] = self._resolve_zone(params.get('source', params.get('from', 'discard')))
            result["to"] = "hand"
        elif "MOVE_TO_DISCARD" in effect_name:
            result["from"] = self._resolve_zone(params.get('source', params.get('from', 'hand')))
            result["to"] = "discard"
        elif "MOVE_TO_DECK" in effect_name:
            result["from"] = self._resolve_zone(params.get('source', params.get('from', 'hand')))
            result["to"] = "deck"
            if params.get('position') == 'top' or params.get('raw_val') == 'DECK_TOP':
                result["position"] = "top"
            elif params.get('position') == 'bottom' or params.get('raw_val') == 'DECK_BOTTOM':
                result["position"] = "bottom"
        else:
            result["from"] = self._resolve_zone(params.get('source', params.get('from', 'discard')))
            result["to"] = self._resolve_zone(params.get('destination', params.get('to', 'hand')))
        
        # Count
        val = str(eff.value).upper() if eff.value else "1"
        if val in ["ALL", "TARGETS", "TARGET"]:
            result["cards"] = "selected"
        else:
            try:
                result["count"] = int(eff.value) if eff.value else 1
            except (ValueError, TypeError):
                result["count"] = 1
        
        # Filter
        if "filter" in params or any(k in params for k in ['group', 'unit', 'type', 'cost_ge', 'cost_le']):
            result["filter"] = self._build_semantic_filter(params)
    
    def _build_select_cards_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Build parameters for select_cards effect."""
        # Source zone
        zone = params.get('zone', params.get('source', params.get('from', 'deck')))
        result["from"] = self._resolve_zone(zone)
        
        # Count
        result["count"] = int(eff.value) if eff.value else 1
        
        # Filter
        if "filter" in params or any(k in params for k in ['group', 'unit', 'type', 'cost_ge', 'cost_le']):
            result["filter"] = self._build_semantic_filter(params)
        
        # Save as variable
        result["save_as"] = params.get('save_as', 'selected')
    
    def _build_play_member_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Build parameters for play_member effect."""
        # Source
        if "FROM_HAND" in eff.effect_type.name:
            result["source"] = "hand"
        elif "FROM_DISCARD" in eff.effect_type.name:
            result["source"] = "selected" if params.get('target') else "discard"
        else:
            result["source"] = self._resolve_zone(params.get('source', 'hand'))
        
        # Destination
        dest = str(params.get('destination', '')).lower()
        if 'empty' in dest or 'stage_empty' in dest:
            result["destination"] = "stage_empty"
        elif 'baton' in dest:
            result["destination"] = "baton"
        else:
            result["destination"] = "stage"
        
        # Filter for selection
        if "filter" in params:
            result["filter"] = self._build_semantic_filter(params)
    
    def _build_play_live_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Build parameters for play_live effect."""
        result["source"] = "selected" if params.get('target') else "discard"
        result["destination"] = "success_pile"
        
        if "filter" in params:
            result["filter"] = self._build_semantic_filter(params)
    
    def _build_look_and_choose_params(
        self,
        eff: Effect,
        params: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """Build parameters for look_and_choose effect."""
        result["look_count"] = int(eff.value) if eff.value else 1
        
        # Choose count
        choose = params.get('choose', params.get('choose_count', 1))
        result["choose_count"] = int(choose) if choose else 1
        
        # Reveal
        if params.get('reveal') or params.get('is_reveal'):
            result["reveal"] = True
        
        # Remainder
        remainder = params.get('remainder', params.get('remainder_zone', 'deck'))
        result["remainder_to"] = self._resolve_zone(remainder)
        
        # From
        result["from"] = self._resolve_zone(params.get('source', params.get('from', 'deck')))
        
        # Filter
        if "filter" in params:
            result["filter"] = self._build_semantic_filter(params)
    
    def _build_semantic_filter(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build a semantic filter (human-readable, not bit-packed)."""
        result = {}
        
        # Target player
        target = params.get('target', 'self')
        if target in ['opponent', 'OPPONENT']:
            result["target"] = "opponent"
        elif target in ['self', 'player', 'SELF', 'PLAYER']:
            result["target"] = "self"
        elif target in ['all', 'ALL', 'all_players']:
            result["target"] = "all"
        
        # Group
        group = params.get('group')
        if group:
            result["group"] = str(group)
        
        # Unit
        unit = params.get('unit')
        if unit:
            result["unit"] = str(unit)
        
        # Card type
        card_type = params.get('type', params.get('card_type'))
        if card_type:
            result["card_type"] = str(card_type).lower()
        
        # Cost constraints
        cost_min = params.get('cost_ge', params.get('min_cost'))
        if cost_min is not None:
            result["cost_min"] = int(cost_min)
        
        cost_max = params.get('cost_le', params.get('max_cost'))
        if cost_max is not None:
            result["cost_max"] = int(cost_max)
        
        # Heart/color constraints
        color = params.get('color', params.get('heart_type'))
        if color:
            result["color"] = str(color)
        
        # Status constraints
        if params.get('is_tapped') or params.get('tapped'):
            result["tapped"] = True
        
        if params.get('has_blade_heart'):
            result["has_blade_heart"] = True
        
        if params.get('not_has_blade_heart'):
            result["has_blade_heart"] = False
        
        # Name constraints
        name = params.get('name')
        if name:
            if isinstance(name, list):
                result["names"] = name
            else:
                result["names"] = [n.strip() for n in str(name).split('/') if n.strip()]
        
        # Zone
        zone = params.get('zone')
        if zone:
            result["zone"] = self._resolve_zone(zone)
        
        # Optional flag
        if params.get('is_optional'):
            result["optional"] = True
        
        # Keyword constraints (for conditions)
        keyword = params.get('keyword')
        if keyword:
            result["keyword"] = str(keyword)
        
        return result
    
    def _resolve_zone(self, zone: Any) -> str:
        """Resolve a zone value to semantic name."""
        if zone is None:
            return "deck"
        
        zone_str = str(zone).upper()
        
        # Check direct mapping
        if zone_str in self.ZONE_MAP:
            return self.ZONE_MAP[zone_str]
        
        # Numeric mapping
        try:
            zone_int = int(zone)
            if zone_int in self.ZONE_MAP:
                return self.ZONE_MAP[zone_int]
        except (ValueError, TypeError):
            pass
        
        # String matching
        if 'DECK' in zone_str:
            return "deck"
        elif 'HAND' in zone_str:
            return "hand"
        elif 'DISCARD' in zone_str:
            return "discard"
        elif 'ENERGY' in zone_str:
            return "energy"
        elif 'STAGE' in zone_str:
            return "stage"
        elif 'YELL' in zone_str:
            return "yell"
        elif 'LIVE' in zone_str:
            return "live_zone"
        
        return str(zone).lower()
    
    def _condition_to_frame(self, cond: Condition, original_text: str) -> Optional[SemanticFrame]:
        """Convert a condition to a semantic frame."""
        cond_type = cond.type.name.lower() if cond.type else "condition"
        params = {str(k).lower(): v for k, v in cond.params.items()} if cond.params else {}
        
        semantic_params = {
            "condition_type": cond_type,
        }
        
        # Add condition-specific params
        if cond.type == ConditionType.ZONE_COUNT or cond.type == ConditionType.COUNT_SUCCESS_LIVE:
            zone = params.get('zone', 'stage')
            semantic_params["zone"] = self._resolve_zone(zone)
            
            # Comparison
            comp = params.get('comparison', 'ge')
            semantic_params["comparison"] = comp.lower()
            
            # Value
            val = params.get('value', params.get('val', params.get('count', 0)))
            try:
                semantic_params["value"] = int(val)
            except (ValueError, TypeError):
                semantic_params["value"] = val
        
        elif cond.type == ConditionType.HAS_KEYWORD:
            keyword = params.get('keyword', '')
            semantic_params["keyword"] = str(keyword)
        
        elif cond.type == ConditionType.COST_CHECK:
            semantic_params["cost_min"] = params.get('min', 0)
            semantic_params["cost_max"] = params.get('max', 999)
        
        # Negation
        if getattr(cond, 'is_negated', False):
            semantic_params["negated"] = True
        
        return SemanticFrame(
            frame_type="condition",
            params=semantic_params,
            ability_text=params.get('raw_cond', ''),
            original_text=original_text
        )
    
    def _cost_to_frame(self, cost: Cost, original_text: str) -> Optional[SemanticFrame]:
        """Convert a cost to a semantic frame."""
        cost_type_name = cost.type.name if cost.type else "unknown"
        
        COST_MAP = {
            "ENERGY": "pay_energy",
            "TAP_SELF": "tap_self",
            "TAP_MEMBER": "tap_member",
            "DISCARD_HAND": "discard",
            "DISCARD_TOP_DECK": "deck_to_discard",
            "RETURN_HAND": "return_to_hand",
            "SACRIFICE_SELF": "sacrifice",
            "REVEAL_HAND": "reveal",
        }
        
        frame_type = COST_MAP.get(cost_type_name, f"cost_{cost_type_name.lower()}")
        
        params = {str(k).lower(): v for k, v in cost.params.items()} if cost.params else {}
        
        semantic_params = {
            "is_cost": True,
        }
        
        # Add count/value
        if hasattr(cost, 'value') and cost.value:
            try:
                semantic_params["count"] = int(cost.value)
            except (ValueError, TypeError):
                semantic_params["value"] = str(cost.value)
        
        # Zone for discards
        if cost_type_name in ["DISCARD_HAND", "DISCARD_TOP_DECK"]:
            semantic_params["from"] = "hand" if cost_type_name == "DISCARD_HAND" else "deck_top"
            semantic_params["to"] = "discard"
        
        return SemanticFrame(
            frame_type=frame_type,
            params=semantic_params,
            ability_text=params.get('cost_type_name', ''),
            original_text=original_text
        )
    
    def _trigger_to_string(self, trigger: TriggerType) -> str:
        """Convert trigger type to string."""
        return trigger.name if trigger else "NONE"


# Convenience function for quick generation
def generate_semantic_frames(
    abilities: List[Ability],
    card_data: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """Generate semantic frames for a list of abilities with card context."""
    generator = SemanticGenerator()
    
    card_no = card_data.get('card_no', '')
    card_name = card_data.get('name', '')
    original_text = card_data.get('original_text', '')
    translated_text = card_data.get('original_text_en', '')
    
    results = []
    for ability in abilities:
        semantic_ability = generator.generate_semantic_ability(
            ability=ability,
            card_no=card_no,
            card_name=card_name,
            original_text=original_text,
            translated_text=translated_text
        )
        results.append(semantic_ability.to_dict())
    
    return results
