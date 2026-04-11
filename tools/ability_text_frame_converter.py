#!/usr/bin/env python3
"""
Ability Text <-> Frame Two-Way Converter (Diagnostic Tool)

Converts between Japanese ability text and frame sequences to verify consistency.
This is a diagnostic tool - not connected to the runtime, purely for analysis.

Usage:
    python ability_text_frame_converter.py text-to-frames "カードを1枚引き、手札を1枚控え室に置く。"
    python ability_text_frame_converter.py frames-to-text ability_frame_source.json 5
    python ability_text_frame_converter.py verify ability_frame_source.json
"""

import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum, auto


class Opcode(Enum):
    """Frame opcodes matching the runtime"""
    DRAW = "DRAW"
    MOVE_TO_DISCARD = "MOVE_TO_DISCARD"
    MOVE_TO_DECK = "MOVE_TO_DECK"
    SELECT_CARDS = "SELECT_CARDS"
    LOOK_AND_CHOOSE = "LOOK_AND_CHOOSE"
    LOOK_DECK = "LOOK_DECK"
    PAY_ENERGY = "PAY_ENERGY"
    ENERGY_CHARGE = "ENERGY_CHARGE"
    ACTIVATE_ENERGY = "ACTIVATE_ENERGY"
    ADD_BLADES = "ADD_BLADES"
    ADD_HEARTS = "ADD_HEARTS"
    SET_TAPPED = "SET_TAPPED"
    TAP_OPPONENT = "TAP_OPPONENT"
    JUMP_IF_FALSE = "JUMP_IF_FALSE"
    JUMP = "JUMP"
    SELECT_MODE = "SELECT_MODE"
    BATON = "BATON"
    COUNT_STAGE = "COUNT_STAGE"
    COUNT_ENERGY = "COUNT_ENERGY"
    HAS_KEYWORD = "HAS_KEYWORD"
    IS_CENTER = "IS_CENTER"
    META_RULE = "META_RULE"
    NOP = "NOP"
    RETURN = "RETURN"
    RECOVER_MEMBER = "RECOVER_MEMBER"
    RECOVER_LIVE = "RECOVER_LIVE"
    NEGATE_EFFECT = "NEGATE_EFFECT"
    SWAP_ZONE = "SWAP_ZONE"
    SCORE_TOTAL_CHECK = "SCORE_TOTAL_CHECK"
    GROUP_FILTER = "GROUP_FILTER"
    SUM_VALUE = "SUM_VALUE"
    PLAY_MEMBER_FROM_HAND = "PLAY_MEMBER_FROM_HAND"
    PLAY_MEMBER_FROM_DISCARD = "PLAY_MEMBER_FROM_DISCARD"
    DISCARDED_CARDS = "DISCARDED_CARDS"
    ORDER_DECK = "ORDER_DECK"
    LOOK_REORDER_DISCARD = "LOOK_REORDER_DISCARD"
    SELECT_MEMBER = "SELECT_MEMBER"
    MOVE_MEMBER = "MOVE_MEMBER"


class TriggerType(Enum):
    ON_PLAY = 1
    ON_REVEAL = 9
    LIVE_START = 2
    LIVE_END = 3
    ACTIVATED = 4
    AUTO = 5


@dataclass
class Frame:
    """Represents a single frame instruction"""
    op: Opcode
    value: int = 0
    optional: bool = False
    slot: Optional[str] = None
    source_zone: Optional[str] = None
    dest_zone: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    
    def to_human(self) -> str:
        """Convert frame to human-readable description"""
        parts = [self.op.value]
        
        if self.optional:
            parts.append("[optional]")
        
        if self.value != 0:
            parts.append(f"value={self.value}")
        
        if self.slot:
            parts.append(f"slot={self.slot}")
        
        if self.source_zone:
            parts.append(f"from={self.source_zone}")
        
        if self.dest_zone:
            parts.append(f"to={self.dest_zone}")
        
        if self.filters:
            for k, v in self.filters.items():
                parts.append(f"{k}={v}")
        
        return " ".join(parts)


@dataclass
class AbilityPattern:
    """A recognized ability pattern"""
    name: str
    text_patterns: List[str]  # Regex patterns to match
    trigger_hint: Optional[str] = None
    frames: List[Frame] = field(default_factory=list)
    confidence: str = "high"  # high, medium, low


# Comprehensive pattern database based on audit findings
# See docs/ability_audit_findings.md for detailed documentation
ABILITY_PATTERNS = [
    # === BASIC DRAW PATTERNS (6 patterns) ===
    AbilityPattern(
        name="simple_draw_1",
        text_patterns=[r"カードを1枚引く"],
        trigger_hint="ON_PLAY",
        frames=[Frame(Opcode.DRAW, value=1)],
        confidence="high",
    ),
    AbilityPattern(
        name="simple_draw_n",
        text_patterns=[r"カードを(\d+)枚引く"],
        trigger_hint="ON_PLAY",
        frames=[Frame(Opcode.DRAW, value=0)],  # value filled from capture
        confidence="high",
    ),
    AbilityPattern(
        name="draw_1_discard_1",
        text_patterns=[r"カードを1枚引き、手札を1枚控え室に置く"],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.DRAW, value=1),
            Frame(Opcode.MOVE_TO_DISCARD, value=1, source_zone="HAND"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="draw_2_discard_1",
        text_patterns=[r"カードを2枚引き、手札を1枚控え室に置く"],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.DRAW, value=2),
            Frame(Opcode.MOVE_TO_DISCARD, value=1, source_zone="HAND"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="draw_2_discard_2",
        text_patterns=[r"カードを2枚引き、手札を2枚控え室に置く"],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.DRAW, value=2),
            Frame(Opcode.MOVE_TO_DISCARD, value=2, source_zone="HAND"),
        ],
        confidence="high",
    ),
    
    # === CONDITIONAL DISCARD THEN DRAW ===
    AbilityPattern(
        name="discard_1_then_draw_1",
        text_patterns=[
            r"手札を1枚控え室に置いてもよい[。:：]それを行った場合、?カードを1枚引く",
            r"手札を1枚控え室に置いてもよい[。:：]そうした場合、?カードを1枚引く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=1, source_zone="HAND", optional=True),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.DRAW, value=1),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="discard_up_to_3_draw_accumulated",
        text_patterns=[
            r"手札を(\d+)枚まで控え室に置いてもよい[。:：]それらのカード(\d+)枚を引く",
            r"手札を(\d+)枚まで控え室に置いてもよい[。:：]その枚数分引く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=3, source_zone="HAND", optional=True),
            Frame(Opcode.DRAW, value=0, params={"compare_accumulated": True}),
        ],
        confidence="high",
    ),
    
    # === MILL PATTERNS (3 patterns) ===
    AbilityPattern(
        name="mill_3_deck_all_member_then_blade",
        text_patterns=[
            r"ライブ開始時、?デッキの上からカードを3枚控え室に置く[。:：]すべてメンバーカードならブレード2得る",
            r"デッキの上からカードを3枚控え室に置く[。:：]すべてメンバーカードならブレードを2得る",
        ],
        trigger_hint="LIVE_START",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=3, source_zone="DECK"),
            Frame(Opcode.DISCARDED_CARDS, filters={"card_type": "MEMBER"}),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.ADD_BLADES, value=2),
        ],
        confidence="medium",
    ),
    AbilityPattern(
        name="mill_10_deck",
        text_patterns=[
            r"デッキの上からカードを10枚控え室に置く",
            r"自分のデッキの上からカードを10枚控え室に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=10, source_zone="DECK"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="mill_3_deck",
        text_patterns=[r"デッキの上からカードを3枚控え室に置く"],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=3, source_zone="DECK"),
        ],
        confidence="high",
    ),
    
    # === RECOVERY PATTERNS (4 patterns) ===
    AbilityPattern(
        name="recover_live_from_discard",
        text_patterns=[
            r"控え室からライブカードを1枚手札に加える",
            r"自分の控え室からライブカードを1枚手札に加える",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.RECOVER_LIVE, value=1, filters={"card_type": "LIVE"}),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="recover_group_live_from_discard",
        text_patterns=[
            r"控え室から『(.+?)』のライブカードを1枚手札に加える",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.RECOVER_LIVE, value=1, filters={"card_type": "LIVE", "group_enabled": True}),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="recover_member_cost_le_2",
        text_patterns=[
            r"控え室からコスト2以下のメンバーを1枚手札に加える",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.RECOVER_MEMBER, value=1, filters={"cost_max": 2}),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="recover_group_member_from_discard",
        text_patterns=[
            r"控え室から(μ's|Aqours|Liella|虹ヶ咲)のメンバーを1枚手札に加える",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.RECOVER_MEMBER, value=1, filters={"group_enabled": True}),
        ],
        confidence="high",
    ),
    
    # === ENERGY PATTERNS (5 patterns) ===
    AbilityPattern(
        name="pay_energy_e_then_draw",
        text_patterns=[
            r"エネルギーを1個支払ってもよい[。:：]そうした場合、?カードを1枚引く",
            r"エネルギー1個を支払う：カードを1枚引く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.PAY_ENERGY, value=1, optional=True),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.DRAW, value=1),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="pay_energy_ee_optional",
        text_patterns=[
            r"エネルギーを2個支払ってもよい",
            r"エネルギー2個を支払う",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.PAY_ENERGY, value=2, optional=True),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="place_energy_tapped",
        text_patterns=[
            r"エネルギーを1個リラックス状態で置く",
            r"エネルギーを2個リラックス状態で置く",
            r"エネルギーを(\d+)個リラックス状態で置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.ENERGY_CHARGE, value=0, params={"is_wait": True}),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="activate_energy",
        text_patterns=[
            r"エネルギーを2個アクティブにする",
            r"エネルギーを(\d+)個アクティブにする",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.ACTIVATE_ENERGY, value=2),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="energy_count_condition",
        text_patterns=[
            r"エネルギーが(\d+)個以上の場合",
            r"エネルギーが(\d+)個以上なら",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.COUNT_ENERGY, value=0, filters={"comparison": ">="}),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
        ],
        confidence="high",
    ),
    
    # === BLADE/HEART PATTERNS ===
    AbilityPattern(
        name="gain_blades_2",
        text_patterns=[
            r"ブレードを2得る",
            r"ブレード2得る",
            r"ブレードを2得る[。:]",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.ADD_BLADES, value=2),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="gain_blades_n",
        text_patterns=[r"ブレードを(\d+)得る"],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.ADD_BLADES, value=0),
        ],
        confidence="high",
    ),
    
    # === TAP PATTERNS (4 patterns) ===
    AbilityPattern(
        name="tap_self_optional",
        text_patterns=[
            r"このメンバーをリラックスしてもよい",
            r"このメンバーをリラックスしてもよい[。:]",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.SET_TAPPED, optional=True),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="tap_self_cost_then_effect",
        text_patterns=[
            r"このメンバーをリラックスしてもよい[。:：]そうした場合、",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.SET_TAPPED, optional=True),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="tap_opponent_1",
        text_patterns=[
            r"相手のステージのメンバーを1体リラックスする",
            r"相手のメンバーを1体リラックスする",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.TAP_OPPONENT, value=1),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="tap_opponent_2_cost_le_4",
        text_patterns=[
            r"相手のステージのコスト4以下のメンバーを2体までリラックスする",
            r"相手のコスト4以下のメンバーを2体までリラックスする",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.TAP_OPPONENT, value=2, filters={"cost_max": 4}),
        ],
        confidence="high",
    ),
    
    # === BATON PATTERNS (3 patterns) ===
    AbilityPattern(
        name="baton_draw_discard",
        text_patterns=[
            r"【バトン】カードを2枚引き、手札を2枚控え室に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.BATON),
            Frame(Opcode.DRAW, value=2),
            Frame(Opcode.MOVE_TO_DISCARD, value=2, source_zone="HAND"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="baton_then_energy",
        text_patterns=[
            r"【バトン】エネルギーが7個以上なら、?エネルギーを2個リラックス状態で置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.BATON),
            Frame(Opcode.COUNT_ENERGY, value=7, filters={"comparison": ">="}),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.ENERGY_CHARGE, value=2, params={"is_wait": True}),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="baton_from_specific_member",
        text_patterns=[
            r"このメンバーにバトンタッチしたとき",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.BATON),
        ],
        confidence="medium",
    ),
    
    # === LOOK/CHOOSE PATTERNS (4 patterns) ===
    AbilityPattern(
        name="look_deck_3_choose_1_discard_rest",
        text_patterns=[
            r"デッキの上からカードを3枚見て、?1枚手札に加え、?残りを控え室に置く",
            r"デッキの上からカードを3枚見て、?1枚まで手札に加え、?残りを控え室に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.LOOK_AND_CHOOSE, value=3, source_zone="DECK"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="look_deck_3_reorder_discard",
        text_patterns=[
            r"デッキの上からカードを3枚見て、?好きな順番でデッキの上に戻し、?残りを控え室に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.LOOK_DECK, value=3),
            Frame(Opcode.ORDER_DECK, value=3),
            Frame(Opcode.MOVE_TO_DISCARD, value=1, source_zone="CONTEXT", dest_zone="DISCARD"),
        ],
        confidence="medium",
    ),
    AbilityPattern(
        name="tap_self_look_2_reorder_discard",
        text_patterns=[
            r"このメンバーをリラックスしてもよい[。:：]そうした場合、?デッキの上からカードを2枚見て、?好きな順番でデッキに戻し、?残りを控え室に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.SET_TAPPED, optional=True),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.LOOK_REORDER_DISCARD, value=2),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="discard_cost_look_5_choose_cost_ge_9",
        text_patterns=[
            r"手札を1枚控え室に置いてもよい[。:：]そうした場合、?デッキの上からカードを5枚見て、?コスト9以上のメンバーを1枚手札に加える",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.MOVE_TO_DISCARD, value=1, source_zone="HAND", optional=True),
            Frame(Opcode.JUMP_IF_FALSE, value=1),
            Frame(Opcode.LOOK_AND_CHOOSE, value=5, filters={"cost_min": 9, "card_type": "MEMBER"}),
        ],
        confidence="high",
    ),
    
    # === DECK MANIPULATION PATTERNS (2 patterns) ===
    AbilityPattern(
        name="select_discard_to_deck_bottom",
        text_patterns=[
            r"控え室からライブカードを1枚までデッキの一番下に置く",
            r"控え室からライブカードを1枚までデッキの下に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.SELECT_CARDS, value=1, source_zone="DISCARD", filters={"card_type": "LIVE"}, optional=True),
            Frame(Opcode.MOVE_TO_DECK, dest_zone="DECK_BOTTOM"),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="select_discard_to_deck_top",
        text_patterns=[
            r"控え室からカードを1枚までデッキの一番上に置く",
            r"控え室からカードを1枚までデッキの上に置く",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.SELECT_CARDS, value=1, source_zone="DISCARD", optional=True),
            Frame(Opcode.MOVE_TO_DECK, dest_zone="DECK_TOP"),
        ],
        confidence="high",
    ),
    
    # === POSITION-BASED PATTERNS (3 patterns) ===
    AbilityPattern(
        name="center_position_check",
        text_patterns=[
            r"【センター】",
            r"センターにいるとき",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.IS_CENTER),
        ],
        confidence="high",
    ),
    AbilityPattern(
        name="left_side_check",
        text_patterns=[
            r"【左サイド】",
            r"左サイドにいるとき",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.HAS_KEYWORD, params={"position_check": "LEFT"}),
        ],
        confidence="medium",
    ),
    AbilityPattern(
        name="right_side_check",
        text_patterns=[
            r"【右サイド】",
            r"右サイドにいるとき",
        ],
        trigger_hint="ON_PLAY",
        frames=[
            Frame(Opcode.HAS_KEYWORD, params={"position_check": "RIGHT"}),
        ],
        confidence="medium",
    ),
    
    # === META RULE PATTERNS (YELL abilities) ===
    AbilityPattern(
        name="yell_no_live_re_yell",
        text_patterns=[
            r"{{jidou.png|自動}}.*エールにより公開された.*ライブカードがないとき.*もう一度エール",
            r"自動.*エールにより公開された.*ライブカードがないとき.*もう一度エール",
        ],
        trigger_hint="ON_REVEAL",
        frames=[
            Frame(Opcode.META_RULE, params={"raw_cond": "YELL_PILE_CONTAINS", "FILTER": "TYPE=LIVE", "EQ": 0}),
            Frame(Opcode.META_RULE, params={"raw_effect": "DISCARD_YELL_PILE"}, optional=True),
            Frame(Opcode.META_RULE, params={"raw_effect": "RE_YELL"}),
        ],
        confidence="high",
    ),
]


class TextToFrameConverter:
    """Converts ability text to frame sequences"""
    
    def __init__(self):
        self.patterns = ABILITY_PATTERNS
    
    def convert(self, text: str, trigger_hint: Optional[str] = None) -> Tuple[List[Frame], List[str]]:
        """
        Convert ability text to frames.
        Returns: (frames, notes/warnings)
        """
        frames = []
        notes = []
        matched_patterns = []
        
        # Try to match each pattern
        for pattern in self.patterns:
            for regex in pattern.text_patterns:
                match = re.search(regex, text)
                if match:
                    # Adjust value if captured
                    new_frames = [Frame(
                        op=f.op,
                        value=int(match.group(1)) if match.groups() and f.value == 0 else f.value,
                        optional=f.optional,
                        slot=f.slot,
                        source_zone=f.source_zone,
                        dest_zone=f.dest_zone,
                        filters=dict(f.filters),
                        params=dict(f.params),
                    ) for f in pattern.frames]
                    
                    matched_patterns.append((pattern.name, new_frames, match.group(0)))
                    break
        
        # Build frame sequence from matched patterns
        # This is naive - real implementation needs proper sequencing
        for name, pattern_frames, matched_text in matched_patterns:
            frames.extend(pattern_frames)
            notes.append(f"Matched '{name}' from '{matched_text}'")
        
        if not frames:
            notes.append("WARNING: No patterns matched - manual frame creation needed")
        
        # Add RETURN if missing
        if not frames or frames[-1].op != Opcode.RETURN:
            frames.append(Frame(Opcode.RETURN))
        
        return frames, notes
    
    def detect_trigger(self, text: str) -> Tuple[Optional[TriggerType], str]:
        """Detect trigger type from ability text"""
        if "{{toujyou.png|登場}}" in text or "【登場】" in text:
            return TriggerType.ON_PLAY, "ON_PLAY"
        if "{{jidou.png|自動}}" in text or "【自動】" in text:
            return TriggerType.AUTO, "AUTO"
        if "{{kido.png|起動}}" in text or "【起動】" in text:
            return TriggerType.ACTIVATED, "ACTIVATED"
        if "ライブ開始時" in text:
            return TriggerType.LIVE_START, "LIVE_START (text says this, not ON_PLAY)"
        if "ライブ終了時" in text:
            return TriggerType.LIVE_END, "LIVE_END"
        if "エール" in text and "公開" in text:
            return TriggerType.ON_REVEAL, "ON_REVEAL"
        
        return None, "Could not detect trigger - manual check needed"


class FrameToTextConverter:
    """Converts frame sequences to human-readable ability text"""
    
    def __init__(self):
        self.opcode_handlers = {
            Opcode.DRAW: self._handle_draw,
            Opcode.MOVE_TO_DISCARD: self._handle_move_to_discard,
            Opcode.MOVE_TO_DECK: self._handle_move_to_deck,
            Opcode.SELECT_CARDS: self._handle_select_cards,
            Opcode.LOOK_AND_CHOOSE: self._handle_look_and_choose,
            Opcode.PAY_ENERGY: self._handle_pay_energy,
            Opcode.ENERGY_CHARGE: self._handle_energy_charge,
            Opcode.ACTIVATE_ENERGY: self._handle_activate_energy,
            Opcode.ADD_BLADES: self._handle_add_blades,
            Opcode.SET_TAPPED: self._handle_set_tapped,
            Opcode.TAP_OPPONENT: self._handle_tap_opponent,
            Opcode.JUMP_IF_FALSE: self._handle_jump_if_false,
            Opcode.BATON: self._handle_baton,
            Opcode.RECOVER_LIVE: self._handle_recover_live,
            Opcode.RECOVER_MEMBER: self._handle_recover_member,
            Opcode.COUNT_STAGE: self._handle_count_stage,
            Opcode.COUNT_ENERGY: self._handle_count_energy,
            Opcode.HAS_KEYWORD: self._handle_has_keyword,
            Opcode.IS_CENTER: self._handle_is_center,
            Opcode.META_RULE: self._handle_meta_rule,
            Opcode.NOP: self._handle_nop,
            Opcode.RETURN: self._handle_return,
            Opcode.SELECT_MODE: self._handle_select_mode,
        }
    
    def convert(self, frames: List[Frame]) -> Tuple[str, List[str]]:
        """
        Convert frames to human-readable text.
        Returns: (text_description, notes)
        """
        parts = []
        notes = []
        skip_next = 0
        
        for i, frame in enumerate(frames):
            if skip_next > 0:
                skip_next -= 1
                continue
            
            handler = self.opcode_handlers.get(frame.op)
            if handler:
                result = handler(frame, frames[i+1:] if i < len(frames)-1 else [])
                if isinstance(result, tuple):
                    text, extra_skip = result
                    skip_next = extra_skip
                else:
                    text = result
                
                if text:
                    parts.append(text)
            else:
                notes.append(f"No handler for opcode: {frame.op.value}")
        
        return "。".join([p for p in parts if p]), notes
    
    def _handle_draw(self, frame: Frame, next_frames: List[Frame]) -> str:
        if frame.value == 0:
            return "カードを（枚数に応じて）枚引く"
        return f"カードを{frame.value}枚引く"
    
    def _handle_move_to_discard(self, frame: Frame, next_frames: List[Frame]) -> str:
        source = "手札" if frame.source_zone == "HAND" else "デッキ"
        if frame.optional:
            if frame.value == 1:
                return f"{source}を{frame.value}枚控え室に置いてもよい"
            return f"{source}を{frame.value}枚まで控え室に置いてもよい"
        return f"{source}を{frame.value}枚控え室に置く"
    
    def _handle_move_to_deck(self, frame: Frame, next_frames: List[Frame]) -> str:
        if frame.dest_zone == "DECK_BOTTOM":
            return "デッキの一番下に置く"
        if frame.dest_zone == "DECK_TOP":
            return "デッキの一番上に置く"
        return "デッキに置く"
    
    def _handle_select_cards(self, frame: Frame, next_frames: List[Frame]) -> str:
        source = "控え室" if frame.source_zone == "DISCARD" else frame.source_zone
        card_type = frame.filters.get("card_type", "カード")
        if frame.optional:
            return f"{source}から{card_type}を{frame.value}枚まで選び"
        return f"{source}から{card_type}を{frame.value}枚選び"
    
    def _handle_look_and_choose(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"デッキの上からカードを{frame.value}枚見て、1枚手札に加え残りを控え室に置く"
    
    def _handle_pay_energy(self, frame: Frame, next_frames: List[Frame]) -> str:
        if frame.optional:
            return f"エネルギーを{frame.value}個支払ってもよい。支払わなかった場合、"
        return f"エネルギーを{frame.value}個支払う："
    
    def _handle_energy_charge(self, frame: Frame, next_frames: List[Frame]) -> str:
        state = "リラックス状態で" if frame.params.get("is_wait") else "アクティブ状態で"
        return f"エネルギーを{frame.value}個{state}置く"
    
    def _handle_activate_energy(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"エネルギーを{frame.value}個アクティブにする"
    
    def _handle_add_blades(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"ブレードを{frame.value}得る"
    
    def _handle_set_tapped(self, frame: Frame, next_frames: List[Frame]) -> str:
        if frame.optional:
            return "このメンバーをリラックスしてもよい。そうした場合、"
        return "このメンバーをリラックスする"
    
    def _handle_tap_opponent(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"相手のステージのメンバーを{frame.value}体リラックスする"
    
    def _handle_jump_if_false(self, frame: Frame, next_frames: List[Frame]) -> Tuple[str, int]:
        # This indicates a conditional branch
        # Check what comes after the jump
        if next_frames and len(next_frames) >= frame.value:
            next_op = next_frames[frame.value - 1].op if frame.value > 0 else None
            if next_op == Opcode.RETURN:
                return "（条件を満たさない場合、能力終了）", 0
        return f"（条件を満たさない場合、次の{frame.value}フレームをスキップ）", 0
    
    def _handle_baton(self, frame: Frame, next_frames: List[Frame]) -> str:
        return "【バトン】"
    
    def _handle_recover_live(self, frame: Frame, next_frames: List[Frame]) -> str:
        group = frame.filters.get("group_id", "")
        group_text = f"{group}の" if group else ""
        return f"控え室から{group_text}ライブカードを{frame.value}枚手札に加える"
    
    def _handle_recover_member(self, frame: Frame, next_frames: List[Frame]) -> str:
        group = frame.filters.get("group_id", "")
        cost_max = frame.filters.get("cost_max", "")
        filters = []
        if group:
            filters.append(group)
        if cost_max:
            filters.append(f"コスト≤{cost_max}")
        filter_text = "、".join(filters) if filters else ""
        return f"控え室から{filter_text}メンバーを{frame.value}枚手札に加える"
    
    def _handle_count_stage(self, frame: Frame, next_frames: List[Frame]) -> str:
        return "（ステージのメンバー数を確認）"
    
    def _handle_count_energy(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"（エネルギーが{frame.value}個以上の場合）"
    
    def _handle_has_keyword(self, frame: Frame, next_frames: List[Frame]) -> str:
        keyword = frame.params.get("char_id_1", "")
        return f"（{keyword}キーワードチェック）"
    
    def _handle_is_center(self, frame: Frame, next_frames: List[Frame]) -> str:
        return "【センター】"
    
    def _handle_meta_rule(self, frame: Frame, next_frames: List[Frame]) -> str:
        cond = frame.params.get("raw_cond", "")
        effect = frame.params.get("raw_effect", "")
        if cond:
            return f"【メタルール：{cond}】"
        if effect:
            return f"【メタルール：{effect}】"
        return "【メタルール】"
    
    def _handle_nop(self, frame: Frame, next_frames: List[Frame]) -> str:
        raw_cond = frame.params.get("raw_cond", "")
        if raw_cond:
            return f"（条件チェック：{raw_cond} - 未実装）"
        return "（NOP）"
    
    def _handle_return(self, frame: Frame, next_frames: List[Frame]) -> str:
        return ""  # End of ability, no text
    
    def _handle_select_mode(self, frame: Frame, next_frames: List[Frame]) -> str:
        return f"（モード選択：{frame.value}つの選択肢）"


class AbilityVerifier:
    """Verifies ability text matches frames and vice versa"""
    
    def __init__(self):
        self.text_converter = TextToFrameConverter()
        self.frame_converter = FrameToTextConverter()
    
    def verify(self, text: str, frames: List[Frame], trigger: str) -> Dict:
        """
        Verify text and frames match.
        Returns detailed analysis.
        """
        # Convert both directions
        expected_frames, text_notes = self.text_converter.convert(text)
        generated_text, frame_notes = self.frame_converter.convert(frames)
        
        detected_trigger, trigger_note = self.text_converter.detect_trigger(text)
        
        # Compare
        issues = []
        warnings = []
        
        # Check trigger mismatch
        if detected_trigger and detected_trigger.name != trigger:
            issues.append({
                "type": "TRIGGER_MISMATCH",
                "severity": "CRITICAL",
                "message": f"Text says {detected_trigger.name} but frames have {trigger}",
                "note": trigger_note,
            })
        
        # Check frame count mismatch
        if len(expected_frames) != len(frames):
            warnings.append({
                "type": "FRAME_COUNT_MISMATCH",
                "severity": "WARNING",
                "message": f"Text implies {len(expected_frames)} frames, found {len(frames)}",
            })
        
        # Check specific opcodes
        text_ops = [f.op.value for f in expected_frames]
        frame_ops = [f.op.value for f in frames]
        
        # Look for major mismatches
        if "DRAW" in text_ops and "DRAW" not in frame_ops:
            issues.append({
                "type": "MISSING_DRAW",
                "severity": "MAJOR",
                "message": "Text mentions drawing but frames have no DRAW opcode",
            })
        
        if "手札" in text and "MOVE_TO_DISCARD" in frame_ops:
            # Check if source is HAND
            discard_frames = [f for f in frames if f.op == Opcode.MOVE_TO_DISCARD]
            hand_discard = any(f.source_zone == "HAND" for f in discard_frames)
            if not hand_discard and "控え室" not in text:
                warnings.append({
                    "type": "DISCARD_SOURCE_UNCLEAR",
                    "severity": "WARNING",
                    "message": "Text mentions hand but discard frame source_zone unclear",
                })
        
        # Check for copy-paste patterns (major mismatch indicator)
        if len(frames) >= 2:
            if frames[0].op == Opcode.MOVE_TO_DISCARD and frames[0].optional:
                if len(frames) > 1 and frames[1].op == Opcode.DRAW and frames[1].value == 0:
                    if "手札を" not in text or "枚まで" not in text:
                        issues.append({
                            "type": "COPY_PASTE_PATTERN",
                            "severity": "CRITICAL",
                            "message": "Frames have 'discard up to N, draw that many' pattern but text doesn't match",
                            "hint": "This looks like a copy-paste error from another ability",
                        })
        
        return {
            "text": text[:100] + "..." if len(text) > 100 else text,
            "trigger_in_text": detected_trigger.name if detected_trigger else None,
            "trigger_in_frames": trigger,
            "generated_frames": [f.to_human() for f in expected_frames],
            "actual_frames": [f.to_human() for f in frames],
            "generated_text": generated_text,
            "issues": issues,
            "warnings": warnings,
            "text_notes": text_notes,
            "frame_notes": frame_notes,
            "status": "FAIL" if issues else ("WARN" if warnings else "PASS"),
        }


def load_json_ability(json_path: str, ability_index: int) -> Optional[Dict]:
    """Load a specific ability from the JSON file"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if ability_index < 0 or ability_index >= len(data.get("abilities", [])):
            return None
        
        return data["abilities"][ability_index]
    except Exception as e:
        print(f"Error loading JSON: {e}")
        return None


def parse_frames_from_json(ability: Dict) -> List[Frame]:
    """Convert JSON frame format to Frame objects"""
    frames = []
    
    for frame_data in ability.get("frames", []):
        op_str = frame_data.get("op", "NOP")
        try:
            op = Opcode(op_str)
        except ValueError:
            op = Opcode.NOP
        
        frame = Frame(
            op=op,
            value=frame_data.get("value", 0),
            optional=frame_data.get("attr", {}).get("is_optional", 0) == 1,
            slot=frame_data.get("slot", {}).get("target_slot"),
            source_zone=frame_data.get("slot", {}).get("source_zone"),
            dest_zone=frame_data.get("slot", {}).get("dest_zone"),
            filters={
                k: v for k, v in {
                    "card_type": frame_data.get("attr", {}).get("card_type"),
                    "group_id": frame_data.get("attr", {}).get("char_id_1") or frame_data.get("attr", {}).get("group_id"),
                    "cost_max": frame_data.get("attr", {}).get("cost_max"),
                }.items() if v is not None
            },
            params=frame_data.get("params", {}),
        )
        frames.append(frame)
    
    return frames


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "text-to-frames":
        if len(sys.argv) < 3:
            print("Usage: python ability_text_frame_converter.py text-to-frames 'カードを1枚引く'")
            sys.exit(1)
        
        text = sys.argv[2]
        converter = TextToFrameConverter()
        frames, notes = converter.convert(text)
        trigger, trigger_note = converter.detect_trigger(text)
        
        print(f"\n=== Text to Frames ===")
        print(f"Input: {text}")
        print(f"Detected Trigger: {trigger.name if trigger else 'Unknown'} ({trigger_note})")
        print(f"\nGenerated Frames ({len(frames)}):")
        for i, frame in enumerate(frames):
            print(f"  [{i}] {frame.to_human()}")
        
        if notes:
            print(f"\nNotes:")
            for note in notes:
                print(f"  - {note}")
    
    elif command == "frames-to-text":
        if len(sys.argv) < 4:
            print("Usage: python ability_text_frame_converter.py frames-to-text ability_frame_source.json 5")
            sys.exit(1)
        
        json_path = sys.argv[2]
        ability_index = int(sys.argv[3])
        
        ability = load_json_ability(json_path, ability_index)
        if not ability:
            print(f"Could not load ability #{ability_index}")
            sys.exit(1)
        
        frames = parse_frames_from_json(ability)
        converter = FrameToTextConverter()
        text, notes = converter.convert(frames)
        
        print(f"\n=== Frames to Text ===")
        print(f"Ability #{ability_index}")
        print(f"Cards: {', '.join([c['card_no'] for c in ability.get('card_refs', [])[:3]])}")
        print(f"\nOriginal Text:")
        print(f"  {ability.get('primary_text_jp', 'N/A')[:80]}...")
        print(f"\nGenerated Text:")
        print(f"  {text}")
        
        print(f"\nFrame Breakdown ({len(frames)}):")
        for i, frame in enumerate(frames):
            print(f"  [{i}] {frame.to_human()}")
        
        if notes:
            print(f"\nNotes:")
            for note in notes:
                print(f"  - {note}")
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: python ability_text_frame_converter.py verify ability_frame_source.json [ability_index]")
            sys.exit(1)
        
        json_path = sys.argv[2]
        specific_index = int(sys.argv[3]) if len(sys.argv) > 3 else None
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error loading JSON: {e}")
            sys.exit(1)
        
        verifier = AbilityVerifier()
        
        abilities = data.get("abilities", [])
        if specific_index is not None:
            abilities = [abilities[specific_index]] if specific_index < len(abilities) else []
        
        results = []
        stats = {"PASS": 0, "WARN": 0, "FAIL": 0}
        
        for i, ability in enumerate(abilities):
            text = ability.get("primary_text_jp", "")
            trigger = ability.get("trigger", "UNKNOWN")
            frames = parse_frames_from_json(ability)
            
            result = verifier.verify(text, frames, trigger)
            results.append((i, result))
            stats[result["status"]] += 1
        
        # Print results
        print(f"\n{'='*60}")
        print(f"ABILITY VERIFICATION RESULTS")
        print(f"{'='*60}")
        print(f"Total: {len(results)} | PASS: {stats['PASS']} | WARN: {stats['WARN']} | FAIL: {stats['FAIL']}")
        print(f"{'='*60}\n")
        
        # Show failures first
        for idx, result in results:
            if result["status"] == "FAIL":
                print(f"\n--- Ability #{idx}: {result['status']} ---")
                print(f"Text: {result['text']}")
                print(f"Trigger: Text={result['trigger_in_text']}, Frames={result['trigger_in_frames']}")
                for issue in result["issues"]:
                    print(f"  [{issue['severity']}] {issue['type']}: {issue['message']}")
                    if "hint" in issue:
                        print(f"    Hint: {issue['hint']}")
        
        # Show warnings
        for idx, result in results:
            if result["status"] == "WARN":
                print(f"\n--- Ability #{idx}: {result['status']} ---")
                print(f"Text: {result['text']}")
                for warning in result["warnings"]:
                    print(f"  [{warning['severity']}] {warning['type']}: {warning['message']}")
        
        # Summary of frame->text samples
        print(f"\n{'='*60}")
        print("SAMPLE FRAME→TEXT CONVERSIONS")
        print(f"{'='*60}")
        for idx, result in results[:5]:  # First 5
            if result["generated_text"]:
                print(f"\nAbility #{idx}:")
                print(f"  Original: {result['text'][:60]}...")
                print(f"  Generated: {result['generated_text'][:60]}...")
    
    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
