import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple, Union

from engine.models.enums import CHAR_MAP
from engine.models.opcodes import Opcode

from .generated_enums import AbilityCostType, ConditionType, EffectType, TargetType, TriggerType
from .generated_metadata import COMPARISONS, COUNT_SOURCES, EXTRA_CONSTANTS, HEART_COLOR_MAP, META_RULE_TYPES, ZONES
from .generated_packer import (
    pack_a_heart_cost,
    pack_a_standard,
    pack_s_standard,
    pack_v_heart_counts,
    pack_v_look_choose,
)


def to_signed_32(x):
    """Utility to convert an integer to a signed 32-bit integer."""
    x = int(x) & 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


# Original definitions removed, now using generated_enums.


# --- DESCRIPTIONS ---

EFFECT_DESCRIPTIONS = {
    EffectType.DRAW: "Draw {value} card(s)",
    EffectType.LOOK_DECK: "Look at top {value} card(s) of deck",
    EffectType.ADD_BLADES: "Gain {value} Blade(s)",
    EffectType.ADD_HEARTS: "Gain {value} Heart(s)",
    EffectType.REDUCE_COST: "Reduce cost by {value}",
    EffectType.BOOST_SCORE: "Boost live score by {value}",
    EffectType.RECOVER_LIVE: "Recover {value} Live card(s) from discard",
    EffectType.RECOVER_MEMBER: "Recover {value} Member card(s) from discard",
    EffectType.BUFF_POWER: "Power Up {value} (Blade/Heart)",
    EffectType.IMMUNITY: "Gain Immunity",
    EffectType.MOVE_MEMBER: "Move Member to another zone",
    EffectType.SWAP_CARDS: "Discard {value} card(s) then Draw {value}",
    EffectType.SEARCH_DECK: "Search Deck",  # [UNUSED]
    EffectType.ENERGY_CHARGE: "Charge {value} Energy",
    EffectType.SET_BLADES: "Set Blade(s) to {value}",
    EffectType.SET_HEARTS: "Set Heart(s) to {value}",
    EffectType.FORMATION_CHANGE: "Rearrange members on stage",  # [UNUSED]
    EffectType.NEGATE_EFFECT: "Negate effect",
    EffectType.ORDER_DECK: "Reorder top {value} cards of deck",
    EffectType.META_RULE: "[Rule modifier]",
    EffectType.SELECT_MODE: "Choose One:",
    EffectType.MOVE_TO_DECK: "Return {value} card(s) to Deck",
    EffectType.TAP_OPPONENT: "Tap {value} Opponent Member(s)",
    EffectType.PLACE_UNDER: "Place card under Member",
    EffectType.RESTRICTION: "Apply Restriction",
    EffectType.BATON_TOUCH_MOD: "Modify Baton Touch rules",
    EffectType.SET_SCORE: "Set Live Score to {value}",
    EffectType.REVEAL_CARDS: "Reveal {value} card(s)",
    EffectType.LOOK_AND_CHOOSE: "Look at {value} card(s) from deck and choose",
    EffectType.ACTIVATE_MEMBER: "Active {value} Member(s)/Energy",
    EffectType.ADD_TO_HAND: "Add {value} card(s) to Hand",
    EffectType.TRIGGER_REMOTE: "Trigger Remote Ability",
    EffectType.CHEER_REVEAL: "Reveal via Cheer",
    EffectType.REDUCE_HEART_REQ: "Modify Heart Requirement",
    EffectType.SWAP_ZONE: "Swap card zones",  # [UNUSED]
    EffectType.MOVE_TO_DISCARD: "Move {value} card(s) to Discard",
    EffectType.PLAY_MEMBER_FROM_HAND: "Play member from hand",
    EffectType.TAP_MEMBER: "Tap {value} Member(s)",
}

EFFECT_DESCRIPTIONS_JP = {
    EffectType.DRAW: "{value}枚ドロー",
    EffectType.LOOK_DECK: "デッキの上から{value}枚見る",
    EffectType.ADD_BLADES: "ブレード+{value}",
    EffectType.ADD_HEARTS: "ハート+{value}",
    EffectType.REDUCE_COST: "コスト-{value}",
    EffectType.BOOST_SCORE: "スコア+{value}",
    EffectType.RECOVER_LIVE: "控えライブ{value}枚回収",
    EffectType.RECOVER_MEMBER: "控えメンバー{value}枚回収",
    EffectType.BUFF_POWER: "パワー+{value}",
    EffectType.IMMUNITY: "効果無効",
    EffectType.MOVE_MEMBER: "メンバー移動",
    EffectType.SWAP_CARDS: "手札交換({value}枚捨て{value}枚引く)",
    EffectType.SEARCH_DECK: "デッキ検索",  # [UNUSED]
    EffectType.ENERGY_CHARGE: "エネルギーチャージ+{value}",
    EffectType.SET_BLADES: "ブレードを{value}にセット",
    EffectType.SET_HEARTS: "ハートを{value}にセット",
    EffectType.FORMATION_CHANGE: "配置変更",  # [UNUSED]
    EffectType.NEGATE_EFFECT: "効果打ち消し",
    EffectType.ORDER_DECK: "デッキトップ{value}枚並べ替え",
    EffectType.META_RULE: "[ルール変更]",
    EffectType.SELECT_MODE: "モード選択:",
    EffectType.MOVE_TO_DECK: "{value}枚をデッキに戻す",
    EffectType.TAP_OPPONENT: "相手メンバー{value}人をウェイトにする",
    EffectType.PLACE_UNDER: "メンバーの下に置く",
    EffectType.RESTRICTION: "プレイ制限適用",
    EffectType.BATON_TOUCH_MOD: "バトンタッチルール変更",
    EffectType.SET_SCORE: "ライブスコアを{value}にセット",
    EffectType.REVEAL_CARDS: "{value}枚公開",
    EffectType.LOOK_AND_CHOOSE: "デッキから{value}枚見て選ぶ",
    EffectType.ACTIVATE_MEMBER: "{value}人/エネをアクティブにする",
    EffectType.ADD_TO_HAND: "手札に{value}枚加える",
    EffectType.TRIGGER_REMOTE: "リモート能力誘発",
    EffectType.CHEER_REVEAL: "応援で公開",
    EffectType.REDUCE_HEART_REQ: "ハート条件変更",
    EffectType.SWAP_ZONE: "カード移動(ゾーン間)",  # [UNUSED]
    EffectType.MOVE_TO_DISCARD: "控え室に{value}枚置く",
    EffectType.PLAY_MEMBER_FROM_HAND: "手札からメンバーを登場させる",
    EffectType.TAP_MEMBER: "{value}人をウェイトにする",
    EffectType.ACTIVATE_ENERGY: "エネルギーを{value}枚アクティブにする",
}

TRIGGER_DESCRIPTIONS = {
    TriggerType.ON_PLAY: "[On Play]",
    TriggerType.ON_LIVE_START: "[Live Start]",
    TriggerType.ON_LIVE_SUCCESS: "[Live Success]",
    TriggerType.TURN_START: "[Turn Start]",
    TriggerType.TURN_END: "[Turn End - live]",
    TriggerType.CONSTANT: "[Constant - live]",
    TriggerType.ACTIVATED: "[Activated]",
    TriggerType.ON_LEAVES: "[When Leaves]",
}

TRIGGER_DESCRIPTIONS_JP = {
    TriggerType.ON_PLAY: "【登場時】",
    TriggerType.ON_LIVE_START: "【ライブ開始時】",
    TriggerType.ON_LIVE_SUCCESS: "【ライブ成功時】",
    TriggerType.TURN_START: "【ターン開始時】",
    TriggerType.TURN_END: "【ターン終了時】",
    TriggerType.CONSTANT: "【常時】",
    TriggerType.ACTIVATED: "【起動】",
    TriggerType.ON_LEAVES: "【離脱時】",
}


@dataclass(slots=True)
class Condition:
    type: ConditionType
    params: Dict[str, Any] = field(default_factory=dict)
    is_negated: bool = False  # "If NOT X" / "Except X"
    value: int = 0
    attr: int = 0


@dataclass(slots=True)
class Effect:
    effect_type: EffectType
    value: int = 0
    value_cond: ConditionType = ConditionType.NONE
    target: TargetType = TargetType.SELF
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False  # ～てもよい
    modal_options: List[List[Any]] = field(default_factory=list)  # For SELECT_MODE


@dataclass(slots=True)
class ResolvingEffect:
    """Wrapper for an effect currently being resolved to track its source and progress."""

    effect: Effect
    source_card_id: int
    step_index: int
    total_steps: int


# Original AbilityCostType removed, now using generated_enums.


@dataclass
class Cost:
    type: AbilityCostType
    value: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False

    @property
    def cost_type(self) -> AbilityCostType:
        return self.type


@dataclass
class Ability:
    raw_text: str
    trigger: TriggerType
    effects: List[Effect]
    conditions: List[Condition] = field(default_factory=list)
    costs: List[Cost] = field(default_factory=list)
    modal_options: List[List[Any]] = field(default_factory=list)  # For SELECT_MODE
    is_once_per_turn: bool = False
    bytecode: List[int] = field(default_factory=list)
    # Ordered list of operations (Union[Effect, Condition]) for precise execution order
    instructions: List[Union[Effect, Condition, Cost]] = field(default_factory=list)
    card_no: str = ""  # Metadata for debugging/tracing
    requires_selection: bool = False
    choice_flags: int = 0
    choice_count: int = 0
    pseudocode: str = ""
    filters: List[Dict[str, Any]] = field(default_factory=list)

    def compile(self) -> List[int]:
        """Compile ability into fixed-width bytecode sequence (groups of 4 ints)."""
        if "103" in str(self.card_no) or "018" in str(self.card_no):
            print(f"DEBUG: Compiling card {self.card_no}")
        bytecode = []
        self.filters = []  # Reset filters for this compilation

        # 0. Compile Ordered Instructions (If present - New Parser V2.1)
        if self.instructions:
            # Pass 1: Pre-calculate individual instruction sizes
            instr_bytecodes = []
            self._last_counted_zone = None
            for instr in self.instructions:
                if isinstance(instr, Effect) and instr.params.get("raw_effect") == "COUNT_CARDS":
                    self._last_counted_zone = (instr.params.get("zone") or instr.params.get("ZONE") or "").upper()

                temp_bc = []
                if isinstance(instr, Condition):
                    self._compile_single_condition(instr, temp_bc)
                elif isinstance(instr, Effect):
                    self._compile_effect_wrapper(instr, temp_bc)
                elif isinstance(instr, Cost):
                    mapping = {
                        AbilityCostType.ENERGY: Opcode.PAY_ENERGY,
                        AbilityCostType.TAP_SELF: Opcode.TAP_MEMBER,
                        AbilityCostType.TAP_MEMBER: Opcode.TAP_MEMBER,
                        AbilityCostType.DISCARD_HAND: Opcode.MOVE_TO_DISCARD,
                        AbilityCostType.RETURN_HAND: Opcode.MOVE_MEMBER,
                        AbilityCostType.SACRIFICE_SELF: Opcode.MOVE_TO_DISCARD,
                        AbilityCostType.RETURN_DISCARD_TO_DECK: Opcode.MOVE_TO_DECK,
                        AbilityCostType.NONE: Opcode.SELECT_CARDS,  # Fallback for named costs
                    }
                    if (
                        instr.is_optional
                        or instr.type in mapping
                        or instr.params.get("cost_type_name") in ["CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER"]
                    ):
                        self._compile_single_cost(instr, temp_bc)
                instr_bytecodes.append(temp_bc)

            # Pass 2: Emit bytecode with accurate jump targets
            for i, instr in enumerate(self.instructions):
                bc_chunk = instr_bytecodes[i]
                bytecode.extend(bc_chunk)

                if isinstance(instr, Cost) and instr.is_optional:
                    # Calculate jump target based on BYTECODE size, not instruction count
                    # skip_size = sum of lengths of remaining bytecode chunks / 5
                    remaining_bc_sum = sum(len(c) for c in instr_bytecodes[i + 1 :])
                    # We jump to the instruction AFTER the remaining ones (the RETURN)
                    skip_count = remaining_bc_sum // 5
                    bytecode.extend([int(Opcode.JUMP_IF_FALSE), to_signed_32(skip_count), 0, 0, 0])

            bytecode.extend([int(Opcode.RETURN), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
            return bytecode

        # 1. Compile Conditions (Legacy/Split Mode)
        for cond in self.conditions:
            self._compile_single_condition(cond, bytecode)

        # 1.5. Compile Costs (Note: Modern engine handles costs via pay_cost shell)
        # We don't compile costs into bytecode unless they are meant for mid-ability execution.

        # 2. Compile Effects (with ALL_PLAYERS grouping)
        i = 0
        while i < len(self.effects):
            eff = self.effects[i]
            if eff.target == TargetType.ALL_PLAYERS:
                # Group consecutive ALL_PLAYERS effects
                block = [eff]
                j = i + 1
                while j < len(self.effects) and self.effects[j].target == TargetType.ALL_PLAYERS:
                    block.append(self.effects[j])
                    j += 1

                # Emit block for SELF
                bytecode.extend(
                    [int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)]
                )
                for e in block:
                    # Create a copy with target=PLAYER (Self)
                    e_self = Effect(e.effect_type, e.value, e.value_cond, TargetType.PLAYER, e.params)
                    e_self.is_optional = e.is_optional
                    self._compile_effect_wrapper(e_self, bytecode)

                # Emit block for OPPONENT
                bytecode.extend(
                    [
                        int(Opcode.SET_TARGET_OPPONENT),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(0),
                    ]
                )
                for e in block:
                    # Create a copy with target=OPPONENT
                    e_opp = Effect(e.effect_type, e.value, e.value_cond, TargetType.OPPONENT, e.params)
                    e_opp.is_optional = e.is_optional
                    self._compile_effect_wrapper(e_opp, bytecode)

                # Reset context
                bytecode.extend(
                    [int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)]
                )

                i = j
            else:
                self._compile_effect_wrapper(eff, bytecode)
                i += 1

        # 3. Add Costs to bytecode if present (Fallback for non-instruction abilities)
        # DISABLE: Modern engine handles costs via pay_costs_transactional in the trigger/activation shell.
        # if not self.instructions:
        #     for cost in self.costs:
        #         self._compile_single_cost(cost, bytecode)

        # Terminator
        bytecode.extend([int(Opcode.RETURN), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
        return bytecode

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
                        to_signed_32(0),
                    ]
                )
            return

        op_name = f"CHECK_{cond.type.name}"
        op = getattr(Opcode, op_name, None)

        if op is None and cond.type == ConditionType.NONE and cond.params:
            # Systemic Fix: Preserve unknown conditions as Opcode 0 (NOP/UNKNOWN)
            # This allows the engine to see the params even if it doesn't have a specific opcode.
            op = 0

        if op is not None:
            # Fixed width: [Opcode, Value, Attr, TargetSlot]
            # Check multiple potential keys for the value (min, count, value, diff) - case insensitive
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
                    # Fallback for implicit keywords
                    if cond.type == ConditionType.HAS_KEYWORD:
                        cond.params["keyword"] = "PLAYED_THIS_TURN"
                        attr |= 1 << 44
            elif op == int(Opcode.CHECK_HEART_COMPARE):
                # Heart compare uses raw color index in bits 0-6
                from engine.models.enums import HeartColor

                color_name = str(cond.params.get("color") or "").upper()
                try:
                    attr = int(HeartColor[color_name])
                except:
                    # Fallback: try to extract from filter string if directly missing
                    f_str = str(cond.params.get("filter", "")).upper()
                    if "YELLOW" in f_str:
                        attr = 2
                    elif "RED" in f_str:
                        attr = 1
                    elif "PINK" in f_str:
                        attr = 0
                    elif "BLUE" in f_str:
                        attr = 4
                    elif "GREEN" in f_str:
                        attr = 3
                    elif "PURPLE" in f_str:
                        attr = 5
                    else:
                        attr = 7  # Total count fallback
            else:
                attr = self._pack_filter_attr(cond)

            # Persist back to the Condition object for JSON serialization
            cond.value = val
            cond.attr = attr

            # Comparison and Slot Mapping
            comp_str = str(cond.params.get("comparison") or params_upper.get("COMPARISON") or "GE").upper()
            comp_val = COMPARISONS.get(comp_str, 0)

            slot = 0
            zone = str(cond.params.get("zone") or params_upper.get("ZONE") or "").upper()
            if zone == "LIVE_ZONE":
                slot = 13  # LIVE_SET
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
                if "LEFT" in a_str:
                    slot |= 1 << 29
                elif "CENTER" in a_str:
                    slot |= 2 << 29
                elif "RIGHT" in a_str:
                    slot |= 3 << 29

            packed_slot = (slot & 0x0F) | ((comp_val & 0x0F) << 4) | (slot & 0xFFFFFF00)

            bytecode.extend(
                [
                    to_signed_32(int(op) + (1000 if cond.is_negated else 0)),
                    to_signed_32(val),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(packed_slot),
                ]
            )

        elif cond.type == ConditionType.TYPE_CHECK:
            if hasattr(Opcode, "CHECK_TYPE_CHECK"):
                # card_type: "live" = 1, "member" = 0
                ctype = 1 if str(cond.params.get("card_type", "")).lower() == "live" else 0
                bytecode.extend(
                    [
                        int(Opcode.CHECK_TYPE_CHECK),
                        to_signed_32(ctype),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(0),
                    ]
                )
        elif cond.type == ConditionType.SELECT_MEMBER:
            # Format: SELECT_MEMBER(1) {FILTER="HAS_HEART_02_X3", AREA="LEFT"}
            attr = self._pack_filter_attr(cond)
            slot = self._pack_filter_slot(str(cond.params.get("area", "")).upper())
            bytecode.extend(
                [
                    int(Opcode.SELECT_MEMBER),
                    to_signed_32(1),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(slot),
                ]
            )
        else:
            if cond.type != ConditionType.NONE:
                print(f"CRITICAL WARNING: No opcode mapping for condition type: {cond.type.name}")

    def _compile_single_cost(self, cost: Cost, bytecode: List[int]):
        """Compile a cost into its corresponding opcode."""
        mapping = {
            AbilityCostType.ENERGY: Opcode.PAY_ENERGY,
            AbilityCostType.TAP_SELF: Opcode.TAP_MEMBER,
            AbilityCostType.TAP_MEMBER: Opcode.TAP_MEMBER,
            AbilityCostType.DISCARD_HAND: Opcode.MOVE_TO_DISCARD,
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

        # Handle Named Costs (e.g. metadata-only costs handled via code)
        if cost.params.get("cost_type_name") == "CALC_SUM_COST":
            op = Opcode.CALC_SUM_COST
        elif cost.params.get("cost_type_name") == "SELECT_CARDS":
            op = Opcode.SELECT_CARDS
        elif cost.params.get("cost_type_name") == "SELECT_MEMBER":
            op = Opcode.SELECT_MEMBER
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

            # --- Resolve Slot (Source) ---
            if cost.type in [
                AbilityCostType.DISCARD_HAND,
                AbilityCostType.RETURN_HAND,
                AbilityCostType.REVEAL_HAND,
                AbilityCostType.REVEAL_HAND_ALL,
            ]:
                slot_params["target_slot"] = int(TargetType.CARD_HAND)
            elif cost.type in [AbilityCostType.TAP_SELF, AbilityCostType.TAP_MEMBER, AbilityCostType.SACRIFICE_SELF]:
                slot_params["target_slot"] = int(TargetType.MEMBER_SELF)
            elif cost.type == AbilityCostType.DISCARD_ENERGY:
                slot_params["target_slot"] = int(TargetType.SELF)
            elif cost.type in [AbilityCostType.RETURN_DISCARD_TO_DECK]:
                slot_params["target_slot"] = int(TargetType.CARD_DISCARD)
            elif cost.type in [AbilityCostType.RETURN_SUCCESS_LIVE_TO_HAND, AbilityCostType.DISCARD_SUCCESS_LIVE]:
                slot_params["source_zone"] = ZONES.get("SUCCESS_PILE", 14)
            else:
                slot_params["target_slot"] = int(TargetType.SELF)

            # --- Resolve Attr (Params/Destination) ---
            params_upper = {k.upper(): v for k, v in cost.params.items() if isinstance(k, str)}

            if op == Opcode.MOVE_TO_DECK:
                # 0=Discard, 1=Top, 2=Bottom
                to = str(cost.params.get("to") or params_upper.get("TO") or "top").lower()
                if to == "bottom":
                    slot_params["remainder_zone"] = int(EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2))
                elif to == "top":
                    slot_params["remainder_zone"] = int(EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1))

            # O_SELECT_MEMBER / O_PLAY_MEMBER_FROM_HAND / MOVE_TO_DISCARD, encode filters into 'attr' (a)
            # O_SELECT_MEMBER / O_PLAY_MEMBER_FROM_HAND / MOVE_TO_DISCARD, encode filters into 'attr' (a)
            if op in [
                Opcode.SELECT_MEMBER,
                Opcode.PLAY_MEMBER_FROM_HAND,
                Opcode.PLAY_MEMBER_FROM_DISCARD,
                Opcode.MOVE_TO_DISCARD,
            ]:
                attr = self._pack_filter_attr(cost)
                # Value capture flag (Bit 25 of slot)
                if cost.params.get("destination") == "target_val" or params_upper.get("DESTINATION") == "TARGET_VAL":
                    slot_params["is_reveal_until_live"] = True  # Reuse bit 25 for capture

            if cost.is_optional:
                attr |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)

            # Use value from cost params if available (max/count)
            value = cost.value
            count_raw = cost.params.get("count") or params_upper.get("COUNT")
            if not value and count_raw is not None:
                value = int(count_raw)

            # Fix: Default MOVE_TO_DISCARD for members to 1
            cur_slot_val = slot_params["target_slot"]
            if (
                op == Opcode.MOVE_TO_DISCARD
                and value == 0
                and cur_slot_val
                in (int(TargetType.MEMBER_SELF), int(TargetType.MEMBER_OTHER), int(TargetType.MEMBER_SELECT))
            ):
                value = 1

            slot = pack_s_standard(**slot_params)
            bytecode.extend(
                [
                    int(op),
                    to_signed_32(int(value)),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(slot),
                ]
            )
        else:
            if cost.type != AbilityCostType.NONE:
                # This ensures we don't silently drop costs like we did with TAP_MEMBER
                print(f"CRITICAL WARNING: No opcode mapping for cost type: {cost.type.name}")

    def _compile_effect_wrapper(self, eff: Effect, bytecode: List[int]):
        # Fix: Use name comparison to avoid Enum identity issues from reloading/imports
        if eff.effect_type.name == "ORDER_DECK":
            # O_ORDER_DECK requires looking at cards first.
            # Emit: [O_LOOK_DECK, val, 0, 0] -> [O_ORDER_DECK, val, attr, 0]
            # attr: 0=Discard, 1=DeckTop, 2=DeckBottom
            rem = eff.params.get("remainder", "discard").lower()
            attr = 0
            if rem == "deck_top":
                attr = 1
            elif rem == "deck_bottom":
                attr = 2

            bytecode.extend(
                [int(Opcode.LOOK_DECK), to_signed_32(eff.value), to_signed_32(0), to_signed_32(0), to_signed_32(0)]
            )
            bytecode.extend(
                [
                    int(Opcode.ORDER_DECK),
                    to_signed_32(eff.value),
                    to_signed_32(attr & 0xFFFFFFFF),
                    to_signed_32((attr >> 32) & 0xFFFFFFFF),
                    to_signed_32(0),
                ]
            )
            return

        # Check for modal options on Effect OR Ability (fallback)
        modal_opts = eff.modal_options if eff.modal_options else self.modal_options

        if eff.effect_type == EffectType.SELECT_MODE and modal_opts:
            # Handle SELECT_MODE with jump table
            num_options = len(modal_opts)
            slot = 0
            if eff.target == TargetType.OPPONENT:
                slot |= 1 << 24
            # Emit header: [SELECT_MODE, NumOptions, 0, 0, slot]
            if hasattr(Opcode, "SELECT_MODE"):
                bytecode.extend(
                    [
                        int(Opcode.SELECT_MODE),
                        to_signed_32(num_options),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(slot),
                    ]
                )

            # Placeholders for Jump Table
            jump_table_start_idx = len(bytecode)
            for _ in range(num_options):
                bytecode.extend([int(Opcode.JUMP), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])

            # Compile each option and track start/end
            option_start_offsets = []
            end_jumps_locations = []

            for opt_instructions in modal_opts:
                # Record start offset (relative to current instruction pointer)
                current_idx = len(bytecode) // 5
                option_start_offsets.append(current_idx)

                # Compile option instructions
                for opt_instr in opt_instructions:
                    if isinstance(opt_instr, Cost):
                        self._compile_single_cost(opt_instr, bytecode)
                    elif isinstance(opt_instr, Condition):
                        self._compile_single_condition(opt_instr, bytecode)
                    else:
                        self._compile_single_effect(opt_instr, bytecode)

                # Add Jump to End (placeholder)
                end_jumps_locations.append(len(bytecode))
                bytecode.extend([int(Opcode.JUMP), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])

            # Determine End Index
            end_idx = len(bytecode) // 5

            # Patch Jump Table (Start Jumps)
            for i in range(num_options):
                jump_instr_idx = (jump_table_start_idx // 5) + i
                target_idx = option_start_offsets[i]
                offset = target_idx - jump_instr_idx
                bytecode[jump_instr_idx * 5 + 1] = offset

            # Patch End Jumps
            for loc in end_jumps_locations:
                jump_instr_idx = loc // 5
                offset = end_idx - jump_instr_idx
                bytecode[loc + 1] = offset

        else:
            if eff.target == TargetType.ALL_PLAYERS:
                # ALL_PLAYERS: Emit sequences for both SELF and OPPONENT
                # 1. SET_TARGET_SELF
                bytecode.extend(
                    [int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)]
                )
                # 2. Compile for SELF
                eff_self = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.PLAYER, eff.params)
                eff_self.is_optional = eff.is_optional
                self._compile_single_effect(eff_self, bytecode)

                # 3. SET_TARGET_OPPONENT
                bytecode.extend(
                    [
                        int(Opcode.SET_TARGET_OPPONENT),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(0),
                        to_signed_32(0),
                    ]
                )
                # 4. Compile for OPPONENT
                eff_opp = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.OPPONENT, eff.params)
                eff_opp.is_optional = eff.is_optional
                self._compile_single_effect(eff_opp, bytecode)

                # 5. Restore context to SELF (optional safety)
                bytecode.extend(
                    [int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)]
                )
            else:
                self._compile_single_effect(eff, bytecode)

    def _compile_single_effect(self, eff: Effect, bytecode: List[int]):
        # Normalize params to lowercase keys for consistent lookups
        eff.params = {str(k).lower(): v for k, v in eff.params.items()}
        source_val = 0
        if hasattr(Opcode, eff.effect_type.name):
            op = getattr(Opcode, eff.effect_type.name)

            if eff.effect_type == EffectType.MOVE_MEMBER and str(eff.value).upper() in ["ALL", "TARGETS"]:
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
                if "AREA=CENTER" in f_str:
                    area_raw = "CENTER"
                elif "AREA=LEFT" in f_str:
                    area_raw = "LEFT_SIDE"
                elif "AREA=RIGHT" in f_str:
                    area_raw = "RIGHT_SIDE"

            if area_raw:
                a_str = str(area_raw).upper()
                if "LEFT" in a_str:
                    slot_params["area_idx"] = 1
                elif "CENTER" in a_str:
                    slot_params["area_idx"] = 2
                elif "RIGHT" in a_str:
                    slot_params["area_idx"] = 3

            self._resolve_effect_source_zone(eff, slot_params)

            # TAP/Interactive selection
            if eff.effect_type in (EffectType.TAP_OPPONENT, EffectType.TAP_MEMBER):
                attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.TAP_MEMBER:
                    attr |= 0x02  # Bit 1: Selection mode

            # PLACE_UNDER params
            if eff.effect_type == EffectType.PLACE_UNDER:
                source = str(eff.params.get("from") or eff.params.get("source") or "").lower()
                u_src_val = 0
                if source == "energy":
                    u_src_val = ZONES.get("ENERGY", 3)
                elif source == "discard":
                    u_src_val = ZONES.get("DISCARD", 7)
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

            if eff.effect_type in (EffectType.PLAY_MEMBER_FROM_HAND, EffectType.PLAY_MEMBER_FROM_DISCARD):
                attr = self._pack_filter_attr(eff)
                dest_raw = str(eff.params.get("destination") or "").upper()
                if dest_raw == "STAGE_EMPTY":
                    slot_params["target_slot"] = 4

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
                EffectType.MOVE_MEMBER,
                EffectType.RECOVER_LIVE,
                EffectType.RECOVER_MEMBER,
            ):
                attr = self._pack_filter_attr(eff)
                src_zone_str = str(eff.params.get("source") or eff.params.get("zone") or "DECK").upper()
                if "," not in src_zone_str:
                    src_val = ZONES.get("DECK_TOP", 1)
                    if src_zone_str == "HAND":
                        src_val = ZONES.get("HAND", 6)
                    elif src_zone_str == "DISCARD":
                        src_val = ZONES.get("DISCARD", 7)
                    elif src_zone_str in ("YELL", "REVEALED", "CHEER"):
                        src_val = ZONES.get("YELL", 15)
                    slot_params["source_zone"] = src_val

                rem_val = eff.params.get("remainder_zone", 0)
                if isinstance(rem_val, str):
                    rem_map = {
                        "DISCARD": ZONES.get("DISCARD", 7),
                        "DECK": ZONES.get("DECK_TOP", 1),
                        "HAND": ZONES.get("HAND", 6),
                        "DECK_TOP": EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1),
                        "DECK_BOTTOM": EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2),
                    }
                    rem_val = rem_map.get(rem_val.upper(), 0)
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type == EffectType.SET_HEART_COST:
                val, attr = self._pack_effect_heart_cost(eff, val, attr)

            if eff.effect_type == EffectType.REVEAL_UNTIL:
                attr = self._pack_filter_attr(eff)
                if (
                    eff.value_cond == ConditionType.TYPE_CHECK
                    and str(eff.params.get("card_type", "")).lower() == "live"
                ):
                    slot_params["is_reveal_until_live"] = True
                elif eff.value_cond == ConditionType.COST_CHECK:
                    attr = int(eff.params.get("min", 0))

            if eff.effect_type == EffectType.META_RULE:
                m_type = str(eff.params.get("type", "") or eff.params.get("meta_type", "") or "CHEER_MOD").upper()
                attr = META_RULE_TYPES.get(m_type, 0)
                if attr == 1:
                    src = str(eff.params.get("source", "")).lower()
                    if src == "all_blade" or m_type == "ALL_BLADE_AS_ANY_HEART":
                        val = 1
                    elif src == "blade":
                        val = 2

            if eff.effect_type in (
                EffectType.MOVE_TO_DISCARD,
                EffectType.COLOR_SELECT,
                EffectType.TRANSFORM_HEART,
                EffectType.TRANSFORM_COLOR,
            ):
                attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.MOVE_TO_DISCARD and eff.params.get("operation") == "UNTIL_SIZE":
                    val = (int(val) & 0x7FFFFFFF) | (1 << 31)

            attr = self._resolve_effect_dynamic_multiplier(eff, val, slot_params, attr)

            # Default to Choice (slot 4) if target is generic
            is_non_stage_discard = eff.effect_type == EffectType.MOVE_TO_DISCARD and slot_params["source_zone"] in (
                ZONES.get("HAND", 6),
                ZONES.get("DECK", 5),
            )
            if (
                eff.target in (TargetType.SELF, TargetType.PLAYER)
                and not is_non_stage_discard
                and not slot_params.get("is_dynamic", False)
            ):
                slot_params["target_slot"] = 4

            # SYSTEMIC FIX: If this is REDUCE_COST with dynamic multiplier, base value should be 1
            if eff.effect_type == EffectType.REDUCE_COST and slot_params.get("is_dynamic"):
                val = 1

            # SYSTEMIC FIX: Set is_wait if wait flow is detected
            if eff.params.get("wait") or eff.params.get("wait_flow"):
                slot_params["is_wait"] = True

            slot = pack_s_standard(**slot_params)

            # Redundant setting for PREVENT_PLAY_TO_SLOT (relies on slot bit 24)
            if eff.effect_type == EffectType.PREVENT_PLAY_TO_SLOT:
                pass  # Target opponent bit 24 handles this generically

            # ENSURE OPTIONAL BIT 61 SET FOR ALL OPCODES
            if eff.is_optional or eff.params.get("is_optional"):
                attr |= EXTRA_CONSTANTS.get("FILTER_IS_OPTIONAL", 1 << 61)

            attr_val = attr if not eff.params.get("all") else (attr | 0x80)

            # --- SYSTEMIC FIX: Ensure Opcode Mapping for all types ---
            if eff.effect_type == EffectType.LOOK_REORDER_DISCARD:
                op = Opcode.LOOK_REORDER_DISCARD
                v = int(val)
                bytecode.extend(
                    [
                        int(op),
                        to_signed_32(v),
                        to_signed_32(attr_val & 0xFFFFFFFF),
                        to_signed_32((attr_val >> 32) & 0xFFFFFFFF),
                        to_signed_32(slot),
                    ]
                )
            elif eff.effect_type == EffectType.DIV_VALUE:
                op = Opcode.DIV_VALUE
                v = int(eff.params.get("divisor") or eff.value or 2)
                bytecode.extend([int(op), to_signed_32(v), 0, 0, 0])
            elif eff.effect_type == EffectType.REVEAL_UNTIL:
                op = Opcode.REVEAL_UNTIL
                v = int(val)
                bytecode.extend(
                    [
                        int(op),
                        to_signed_32(v),
                        to_signed_32(attr_val & 0xFFFFFFFF),
                        to_signed_32((attr_val >> 32) & 0xFFFFFFFF),
                        to_signed_32(slot),
                    ]
                )
            elif eff.effect_type == EffectType.CALC_SUM_COST:
                op = Opcode.CALC_SUM_COST
                bytecode.extend(
                    [
                        int(op),
                        to_signed_32(val),
                        to_signed_32(attr_val & 0xFFFFFFFF),
                        to_signed_32((attr_val >> 32) & 0xFFFFFFFF),
                        to_signed_32(slot),
                    ]
                )
            else:
                # Fix: Default MOVE_TO_DISCARD for members to 1
                if (
                    op == Opcode.MOVE_TO_DISCARD
                    and val == 0
                    and slot
                    in (int(TargetType.MEMBER_SELF), int(TargetType.MEMBER_OTHER), int(TargetType.MEMBER_SELECT))
                ):
                    val = 1

                bytecode.extend(
                    [
                        int(op),
                        to_signed_32(val),
                        to_signed_32(attr_val & 0xFFFFFFFF),  # a_low
                        to_signed_32((attr_val >> 32) & 0xFFFFFFFF),  # a_high
                        to_signed_32(slot),
                    ]
                )

    def _resolve_effect_target(self, eff: Effect, slot_params: Dict[str, Any]):
        """--- Target Resolution from Params ---"""
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

    def _resolve_effect_source_zone(self, eff: Effect, slot_params: Dict[str, Any]):
        """--- Zone Relocation ---"""
        src_val = 0
        if eff.effect_type in (
            EffectType.RECOVER_MEMBER,
            EffectType.RECOVER_LIVE,
            EffectType.PLAY_MEMBER_FROM_DISCARD,
            EffectType.PLAY_LIVE_FROM_DISCARD,
        ):
            source = str(eff.params.get("source") or eff.params.get("zone") or "discard").lower()
            src_val = ZONES.get("DISCARD", 7) if source == "discard" else 0
            if source == "yell":
                src_val = ZONES.get("YELL", 15)
            elif source in ("deck", "deck_top"):
                src_val = ZONES.get("DECK_TOP", 1)
            slot_params["source_zone"] = src_val

        # TAP/Interactive selection also uses source zone
        if eff.effect_type in (EffectType.TAP_OPPONENT, EffectType.TAP_MEMBER):
            slot_params["source_zone"] = src_val

    def _pack_effect_look_and_choose(self, eff: Effect, val: int, slot_params: Dict[str, Any]) -> int:
        """Special encoding for LOOK_AND_CHOOSE: val = look_count | (pick_count << 8) | (color_mask << 23)"""
        char_ids = []
        # Simple extraction of up to 3 character IDs
        raw_names = str(eff.params.get("group") or eff.params.get("target_name") or eff.params.get("character") or "")
        if raw_names:
            parts = raw_names.replace(",", "/").split("/")
            for p in parts[:3]:
                p = p.strip()
                if p in CHAR_MAP:
                    char_ids.append(CHAR_MAP[p])

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
        src_val = ZONES.get("DECK_TOP", 1)
        if src == "HAND":
            src_val = ZONES.get("HAND", 6)
        elif src == "DISCARD":
            src_val = ZONES.get("DISCARD", 7)
        elif src in ("YELL", "REVEALED", "CHEER"):
            src_val = ZONES.get("YELL", 15)
        elif src == "ENERGY":
            src_val = ZONES.get("ENERGY", 3)
        slot_params["source_zone"] = src_val

        rem_dest_str = str(eff.params.get("remainder") or eff.params.get("destination") or "").upper()
        rem_val = 0
        if rem_dest_str == "DISCARD":
            rem_val = ZONES.get("DISCARD", 7)
        elif rem_dest_str == "DECK":
            rem_val = ZONES.get("DECK_TOP", 1)
        elif rem_dest_str == "HAND":
            rem_val = ZONES.get("HAND", 6)
        elif rem_dest_str == "DECK_TOP":
            rem_val = EXTRA_CONSTANTS.get("DECK_POSITION_TOP", 1)
        elif rem_dest_str == "DECK_BOTTOM":
            rem_val = EXTRA_CONSTANTS.get("DECK_POSITION_BOTTOM", 2)
        slot_params["remainder_zone"] = rem_val

        # Parity Fix: Set is_wait if 'wait' parameter is present
        if eff.params.get("wait") or eff.params.get("wait_flow"):
            slot_params["is_wait"] = True

        return val

    def _pack_effect_heart_cost(self, eff: Effect, val: int, attr: int) -> Tuple[int, int]:
        """Specialized packing for SET_HEART_COST."""
        colors = ["pink", "red", "yellow", "green", "blue", "purple"]
        v_params = {c: int(eff.params.get(c, 0)) for c in colors}
        val = pack_v_heart_counts(**v_params)

        color_map = HEART_COLOR_MAP
        req_list = []
        add_val = eff.params.get("add")
        if isinstance(add_val, (str, list)):
            parts = add_val.replace(",", "/").split("/") if isinstance(add_val, str) else add_val
            req_list = [color_map.get(str(p).strip().upper(), 0) for p in parts[:8]]

        any_count = int(eff.params.get("any", 0))
        for _ in range(any_count):
            if len(req_list) < 8:
                req_list.append(HEART_COLOR_MAP.get("ANY", 7))

        a_params = {f"req_{i + 1}": req_list[i] if i < len(req_list) else 0 for i in range(8)}
        unit_val = eff.params.get("unit")
        if unit_val:
            try:
                from engine.models.enums import Unit

                u_id = int(str(unit_val)) if str(unit_val).isdigit() else int(Unit.from_japanese_name(str(unit_val)))
                a_params["unit_enabled"] = True
                a_params["unit_id"] = u_id & 0x7F
            except:
                pass
        attr = pack_a_heart_cost(**a_params)
        return val, attr

    def _resolve_effect_dynamic_multiplier(self, eff: Effect, val: int, slot_params: Dict[str, Any], attr: int) -> int:
        """Resolve dynamic multiplier logic for effects."""
        if not (eff.params.get("per_card") or eff.params.get("per_member") or eff.params.get("has_multiplier")):
            return attr

        count_src = str(eff.params.get("per_card", "")).upper()
        if count_src == "COUNT" and hasattr(self, "_last_counted_zone") and self._last_counted_zone:
            count_src = self._last_counted_zone

        count_op = COUNT_SOURCES.get(count_src, int(ConditionType.COUNT_STAGE))
        slot_params["remainder_zone"] = count_op
        slot_params["is_dynamic"] = True

        # Ensure multiplier threshold is 1 if not specified
        if not eff.params.get("value_enabled") and not eff.params.get("cost_ge") and not eff.params.get("cost_le"):
            eff.params["value_enabled"] = True
            eff.params["value_threshold"] = 1

        # SYSTEMIC FIX: If this is REDUCE_COST, base value should be 1
        if eff.effect_type == EffectType.REDUCE_COST:
            # We can't easily change 'val' here because it's passed by value
            # But we can update the effect value in place if needed, or caller handles it.
            pass

        # Ensure the DYNAMIC_VALUE bit (bit 60) is set in the attribute for the engine to recognize scaling
        dynamic_bit = EXTRA_CONSTANTS.get("DYNAMIC_VALUE", 1 << 60)
        return self._pack_filter_attr(eff) | dynamic_bit

    def _pack_filter_slot(self, area_str: str) -> int:
        """Helper to pack area strings into slot bits (29-31)."""
        slot = 0
        a_str = area_str.upper()
        if "LEFT" in a_str:
            slot |= 1 << 29
        elif "CENTER" in a_str:
            slot |= 2 << 29
        elif "RIGHT" in a_str:
            slot |= 3 << 29
        return slot

    def _pack_filter_attr(self, source: Any) -> int:
        """
        Standardized packing for all filter parameters (Revision 5, 64-bit).
        'source' can be an Effect, Condition, or direct Dict params.
        """
        attr = 0
        from engine.models.enums import CHAR_MAP, Group, HeartColor, Unit

        # 0. Initialize params from various sources
        if hasattr(source, "params"):
            params = source.params
        elif isinstance(source, dict):
            params = source
        else:
            params = {}

        params_upper = {str(k).upper(): v for k, v in params.items() if isinstance(k, str)}

        # Extract filter string and other parameters
        filter_str = str(
            params.get("filter")
            or params_upper.get("FILTER")
            or params.get("player_center_filter")
            or params_upper.get("PLAYER_CENTER_FILTER")
            or params.get("opponent_center_filter")
            or params_upper.get("OPPONENT_CENTER_FILTER")
            or ""
        ).upper()

        # Structured object for Phase 3 parity
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

        # Use a separate local variable for filter-specific value thresholding
        # to avoid 'val' contamination from the parent command (e.g. COUNT_MEMBER(2) shouldn't require 2 hearts)
        f_val = 0
        colors = params.get("colors") or params.get("choices") or ([params.get("color")] if "color" in params else [])
        sid = params.get("special_id") or params_upper.get("SPECIAL_ID")

        # 1. Target Player (Bits 0-1)
        if hasattr(source, "target") and source.target == TargetType.OPPONENT:
            filter_obj["target_player"] = 2
        elif params_upper.get("OPPONENT") or params_upper.get("TARGET_OPPONENT"):
            filter_obj["target_player"] = 2
        elif "OPPONENT" in filter_str:
            filter_obj["target_player"] = 2
        elif hasattr(source, "target") and source.target in (TargetType.PLAYER, TargetType.SELF):
            filter_obj["target_player"] = 1
        else:
            filter_obj["target_player"] = 0  # Parity Fix: Default to 0 (Unspecified)

        # 2. Card Type (Bits 2-3)
        ctype = str(params.get("type") or params.get("card_type") or "").lower()
        if not ctype and "TYPE=" in filter_str:
            m = re.search(r"TYPE=(\w+)", filter_str)
            if m:
                ctype = m.group(1).lower()

        if "live" in ctype:
            filter_obj["card_type"] = 2
        elif "member" in ctype:
            filter_obj["card_type"] = 1

        # 3. Group Filter (Bit 4 + Bits 5-11)
        group_val = params.get("group") or params.get("group_id") or params_upper.get("GROUP_ID")
        if not group_val and "GROUP_ID=" in filter_str:
            m = re.search(r"GROUP_ID=(\d+)", filter_str)
            if m:
                group_val = m.group(1)
        elif not group_val and "GROUP_" in filter_str:
            m = re.search(r"GROUP_([A-Z]+)", filter_str)
            if m:
                group_val = m.group(1)
        elif not group_val and "NIJIGASAKI" in filter_str:
            group_val = 2
        elif not group_val and "LIELLA" in filter_str:
            group_val = 3
        elif not group_val and "HASUNOSORA" in filter_str:
            group_val = 4

        if group_val:
            try:
                g_id = (
                    int(str(group_val))
                    if str(group_val).isdigit()
                    else int(Group.from_japanese_name(str(group_val).replace("_", " ")))
                )
                filter_obj["group_enabled"] = True
                filter_obj["group_id"] = g_id & 0x7F
            except:
                pass

        # 4. Unit Filter (Bit 16 + Bits 17-23)
        unit_val = params.get("unit") or params.get("unit_id") or params_upper.get("UNIT_ID")
        if not unit_val and "UNIT_ID=" in filter_str:
            m = re.search(r"UNIT_ID=(\d+)", filter_str)
            if m:
                unit_val = m.group(1)
        elif not unit_val and "UNIT_" in filter_str:
            m = re.search(r"UNIT_([A-Z0-9_]+)", filter_str)
            if m:
                unit_val = m.group(1)
        elif not unit_val and "UNIT_BIBI" in filter_str:
            unit_val = 2

        if unit_val:
            try:
                u_id = (
                    int(str(unit_val))
                    if str(unit_val).isdigit()
                    else int(Unit.from_japanese_name(str(unit_val).replace("_", " ")))
                )
                filter_obj["unit_enabled"] = True
                filter_obj["unit_id"] = u_id & 0x7F
            except:
                pass

        # 5. Cost Filter (Bit 24 + Bits 25-29 + Bit 30=Mode + Bit 31=Type=1)
        c_min = params.get("cost_ge")  # Only check explicit cost GE/LE params
        c_max = params.get("cost_le") or params.get("total_cost_le")

        if c_min is None and "COST_GE=" in filter_str:
            m = re.search(r"COST_GE=(\d+)", filter_str)
            if m:
                c_min = m.group(1)
        if c_max is None and "COST_LE=" in filter_str:
            m = re.search(r"COST_LE=(\d+)", filter_str)
            if m:
                c_max = m.group(1)

        if "COST_LT_TARGET_VAL" in filter_str:
            filter_obj["value_enabled"] = True
            filter_obj["is_le"] = True
            filter_obj["compare_accumulated"] = True
            filter_obj["is_cost_type"] = True
        elif c_min is not None:
            try:
                val_c = int(c_min)
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = val_c & 0x1F
                filter_obj["is_cost_type"] = True
                filter_obj["is_le"] = False
            except:
                pass
        elif c_max is not None:
            try:
                val_c = int(c_max)
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = val_c & 0x1F
                filter_obj["is_cost_type"] = True
                filter_obj["is_le"] = True
            except:
                pass

        # 5.1 Heart Sum Support
        sum_ge = params.get("sum_heart_total_ge") or params_upper.get("SUM_HEART_TOTAL_GE")
        sum_le = params.get("sum_heart_total_le") or params_upper.get("SUM_HEART_TOTAL_LE")
        # Also check filter_str for SUM_HEART_TOTAL_GE (e.g. "SUM_HEART_TOTAL_GE=8")
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
            filter_obj["is_cost_type"] = False  # Must be False for heart sum in engine
            filter_obj["is_le"] = False
        elif sum_le is not None:
            filter_obj["value_enabled"] = True
            filter_obj["value_threshold"] = int(sum_le) & 0x1F
            filter_obj["is_cost_type"] = False
            filter_obj["is_le"] = True

        # 6. Character Filter (IDs at 39-45, 46-52 in Revision 5)
        names = params.get("name") or params_upper.get("NAME")
        if not names and "NAME=" in filter_str:
            m = re.search(r"NAME=([^,]+)", filter_str)
            if m:
                names = m.group(1)

        if names:
            n_list = str(names).split("/")
            for i, n in enumerate(n_list[:3]):
                try:
                    n_norm = n.strip().replace(" ", "").replace("　", "")
                    c_id = 0
                    for k, cid in CHAR_MAP.items():
                        if k.replace(" ", "").replace("　", "") == n_norm:
                            c_id = cid
                            break
                    if c_id > 0:
                        filter_obj[f"char_id_{i + 1}"] = c_id & 0x7F
                except:
                    pass

        # 7. Heart Value and Color Filter (Bits 25-29 Threshold + Bit 31=Type=0 + Bits 32-38 Color Mask)
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
                except:
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
                except:
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
                        if c.isdigit():
                            c_idx = int(c)
                        else:
                            c_idx = int(HeartColor[c.upper()])
                    else:
                        c_idx = int(c)
                    color_mask |= 1 << c_idx
                except:
                    pass
            if color_mask > 0:
                filter_obj["color_mask"] = color_mask & 0x7F

        # 8. Meta Flags and Masks
        # Zone Mask (Bits 53-55)
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

        # Special ID (Bits 56-58)
        if not sid and "NOT_SELF" in filter_str:
            sid = 3
        elif not sid and "SAME_NAME_AS_REVEALED" in filter_str:
            sid = 4

        if sid:
            try:
                sid_int = int(sid)
                filter_obj["special_id"] = sid_int & 0x07
            except:
                pass

        # Setsuna (Bit 59)
        if names and any(s in str(names) for s in ["優木", "せつ菜"]):
            filter_obj["is_setsuna"] = True

        # Internal Flags
        if (
            getattr(source, "is_optional", False)
            or params.get("is_optional")
            or "(Optional)" in str(params.get("pseudocode", ""))
        ):
            filter_obj["is_optional"] = True

        # Keywords (Bits 62-63)
        keyword = str(params.get("keyword") or params.get("filter") or "").upper()
        if params.get("KEYWORD_ENERGY") or "ACTIVATED_ENERGY" in keyword or "DID_ACTIVATE_ENERGY" in keyword:
            filter_obj["keyword_energy"] = True
        if params.get("KEYWORD_MEMBER") or "ACTIVATED_MEMBER" in keyword or "DID_ACTIVATE_MEMBER" in keyword:
            filter_obj["keyword_member"] = True

        # Legacy flags (Bits 12-15)
        if params.get("is_tapped"):
            filter_obj["is_tapped"] = True
        bh = params.get("has_blade_heart")
        if bh is True:
            filter_obj["has_blade_heart"] = True
        elif bh is False:
            filter_obj["not_has_blade_heart"] = True
        if params.get("UNIQUE_NAMES") or params_upper.get("UNIQUE_NAMES"):
            filter_obj["unique_names"] = True

        self.filters.append(filter_obj)
        # Use generated packer to ensure bit parity with Rust
        return pack_a_standard(**filter_obj)

    def reconstruct_text(self, lang: str = "en") -> str:
        """Generate standardized text description."""
        parts = []
        is_jp = lang == "jp"
        e_desc_map = EFFECT_DESCRIPTIONS_JP if is_jp else EFFECT_DESCRIPTIONS

        t_name = getattr(self.trigger, "name", str(self.trigger))
        trigger_desc = t_desc_map.get(self.trigger, f"[{t_name}]")
        if self.trigger == TriggerType.ON_LEAVES:
            if "discard" not in trigger_desc.lower() and "控え室" not in trigger_desc:
                suffix = " (to discard)" if not is_jp else "(控え室へ)"
                trigger_desc += suffix
        parts.append(trigger_desc)

        for cost in self.costs:
            if is_jp:
                if cost.type == AbilityCostType.ENERGY:
                    parts.append(f"(コスト: エネ{cost.value}消費)")
                elif cost.type == AbilityCostType.TAP_SELF:
                    parts.append("(コスト: 自身ウェイト)")
                elif cost.type == AbilityCostType.DISCARD_HAND:
                    parts.append(f"(コスト: 手札{cost.value}枚捨て)")
                elif cost.type == AbilityCostType.SACRIFICE_SELF:
                    parts.append("(コスト: 自身退場)")
                else:
                    parts.append(f"(コスト: {cost.type.name} {cost.value})")
            else:
                if cost.type == AbilityCostType.ENERGY:
                    parts.append(f"(Cost: Pay {cost.value} Energy)")
                elif cost.type == AbilityCostType.TAP_SELF:
                    parts.append("(Cost: Rest Self)")
                elif cost.type == AbilityCostType.DISCARD_HAND:
                    parts.append(f"(Cost: Discard {cost.value} from hand)")
                elif cost.type == AbilityCostType.SACRIFICE_SELF:
                    parts.append("(Cost: Sacrifice Self)")
                else:
                    parts.append(f"(Cost: {cost.type.name} {cost.value})")

        for cond in self.conditions:
            if is_jp:
                neg = "NOT " if cond.is_negated else ""  # JP negation usually handles via suffix, but keeping simple
                cond_desc = f"{neg}{cond.type.name}"
                if cond.type == ConditionType.BATON:
                    cond_desc = "条件: バトンタッチ"
                    if "unit" in cond.params:
                        cond_desc += f" ({cond.params['unit']})"
                # ... (add more JP specific cond descs if needed, but for now fallback)
            else:
                neg = "NOT " if cond.is_negated else ""
                cond_desc = f"{neg}{cond.type.name}"
            # Add basic params
            if cond.params.get("type") == "score":
                cond_desc += " (Score)"
            if cond.type == ConditionType.SCORE_COMPARE:
                target_str = " (Opponent)" if cond.params.get("target") == "opponent" else ""
                cond_desc += f" (Score check{target_str})"
            if cond.type == ConditionType.OPPONENT_HAS:
                cond_desc += " (Opponent has)"
            if cond.type == ConditionType.OPPONENT_CHOICE:
                cond_desc += " (Opponent chooses)"
            if cond.type == ConditionType.OPPONENT_HAND_DIFF:
                cond_desc += " (Opponent hand check)"
            if cond.params.get("group") is not None:
                cond_desc += f"({cond.params['group']})"
            if cond.params.get("unit") is not None:
                cond_desc += f" ({cond.params['unit']})"
            if cond.params.get("zone"):
                cond_desc += f" (in {cond.params['zone']})"
            if cond.params.get("zone") == "SUCCESS_LIVE":
                cond_desc += " (in Live Area)"
            if cond.type == ConditionType.HAS_CHOICE:
                cond_desc = "Condition: Choose One"
            if cond.type == ConditionType.HAS_KEYWORD:
                cond_desc += f" (Has {cond.params.get('keyword', '?')})"
                if cond.params.get("context") == "heart_inclusion":
                    cond_desc += " (Heart check)"
            if cond.type == ConditionType.COUNT_BLADES:
                cond_desc += " (Blade count)"
            if cond.type == ConditionType.COUNT_HEARTS:
                cond_desc += " (Heart count)"
                if cond.params.get("context") == "excess":
                    cond_desc += " (Excess)"
            if cond.type == ConditionType.COUNT_ENERGY:
                cond_desc += " (Energy count)"
            if cond.type == ConditionType.COUNT_SUCCESS_LIVE:
                cond_desc += " (Success Live count)"
            if cond.type == ConditionType.HAS_LIVE_CARD:
                cond_desc += " (Live card check)"
                type_str = (
                    "Heart comparison"
                    if cond.params.get("type") == "heart"
                    else "Cheer comparison"
                    if cond.params.get("type") == "cheer_count"
                    else "Score check"
                )
                cond_desc += f" ({type_str}{target_str})"
            if cond.type == ConditionType.BATON:
                cond_desc = "Condition: Baton Pass"
                if "unit" in cond.params:
                    cond_desc += f" ({cond.params['unit']})"
            parts.append(cond_desc)

        for eff in self.effects:
            # Special handling for META_RULE which relies heavily on params
            desc = None
            if eff.effect_type == EffectType.META_RULE:
                if eff.params.get("type") == "opponent_trigger_allowed":
                    desc = "[Meta: Opponent effects trigger this]"
                elif eff.params.get("type") == "shuffle":
                    desc = "Shuffle Deck"
                elif eff.params.get("type") == "heart_rule":
                    src = eff.params.get("source", "")
                    src_text = "ALL Blades" if src == "all_blade" else "Blade" if src == "blade" else ""
                    desc = f"[Meta: Treat {src_text} as Heart]" if src_text else "[Meta: Treat as Heart]"
                elif eff.params.get("type") == "live":
                    desc = "[Meta: Live Rule]"
                elif eff.params.get("type") == "lose_blade_heart":
                    desc = "[Meta: Lose Blade Heart]"
                elif eff.params.get("type") == "re_cheer":
                    desc = "[Meta: Cheer Again]"
                elif eff.params.get("type") == "cheer_mod":
                    val = eff.value
                    desc = f"[Meta: Cheer Reveal Count {'+' if val > 0 else ''}{val}]"
                elif eff.effect_type == getattr(EffectType, "TAP_OPPONENT", -1):
                    desc = "Tap Opponent Member(s)"

            if desc is None:
                # Custom overrides for standard effects with params
                if eff.effect_type == EffectType.DRAW and eff.params.get("multiplier") == "energy":
                    req = eff.params.get("req_per_unit", 1)
                    desc = f"Draw {eff.value} card(s) per {req} Energy"
                elif eff.effect_type == EffectType.REDUCE_HEART_REQ and eff.value < 0:
                    # e.g. value -1 means reduce requirement. value +1 means increase requirement (opp).
                    pass

                if desc is None:
                    template = e_desc_map.get(eff.effect_type, getattr(eff.effect_type, "name", str(eff.effect_type)))
                    context = eff.params.copy()
                    context["value"] = eff.value

                    # Refine REDUCE_HEART_REQ
                    if eff.effect_type == EffectType.REDUCE_HEART_REQ:
                        if eff.params.get("mode") == "select_requirement":
                            desc = "Choose Heart Requirement (hearts) (choice)" if not is_jp else "ハート条件選択"
                        elif eff.value < 0:
                            desc = (
                                f"Reduce Heart Requirement by {abs(eff.value)} (Live)"
                                if not is_jp
                                else f"ハート条件-{abs(eff.value)}"
                            )
                        else:
                            desc = (
                                f"Increase Heart Requirement by {eff.value} (Live)"
                                if not is_jp
                                else f"ハート条件+{eff.value}"
                            )
                    elif eff.effect_type == EffectType.TRANSFORM_COLOR:
                        target_s = eff.params.get("target", "Color")
                        if target_s == "heart":
                            target_s = "Heart"
                        desc = f"Transform {target_s} Color" if not is_jp else f"{target_s}の色を変換"
                    elif eff.effect_type == EffectType.PLACE_UNDER:
                        type_s = f" {eff.params.get('type', '')}" if "type" in eff.params else ""
                        desc = f"Place{type_s} card under member" if not is_jp else f"メンバーの下に{type_s}置く"
                        if eff.params.get("type") == "energy":
                            desc = "Place Energy under member" if not is_jp else "メンバーの下にエネルギーを置く"
                    else:
                        try:
                            desc = template.format(**context)
                        except KeyError:
                            desc = template

            # Clean up descriptions
            if eff.params.get("live") and "live" not in desc.lower() and "meta" not in desc.lower():
                desc = f"{desc} (Live Rule)"

            # Contextual refinements without spamming "Interaction" tags
            if eff.params.get("per_energy"):
                desc += " per Energy"
            if eff.params.get("per_member"):
                desc += " per Member"
            if eff.params.get("per_live"):
                desc += " per Live"

            # Target Context
            if eff.target == TargetType.MEMBER_SELECT:
                desc += " (Choose member)"
            if eff.target == TargetType.OPPONENT or eff.target == TargetType.OPPONENT_HAND:
                if "opponent" not in desc.lower():
                    desc += " (Opponent)"

            # Trigger Remote Context
            if eff.effect_type == EffectType.TRIGGER_REMOTE:
                zone = eff.params.get("from", "unknown")
                desc += f" from {zone}"

            # Reveal Context
            if eff.effect_type == EffectType.REVEAL_CARDS:
                if "from" in eff.params and eff.params["from"] == "deck":
                    desc += " from Deck"
            if eff.effect_type == EffectType.MOVE_TO_DECK:
                if eff.params.get("to_energy_deck"):
                    desc = "Return to Energy Deck"
                elif eff.params.get("from") == "discard":
                    desc += " from Discard"

            if eff.params.get("rest") == "discard" or eff.params.get("on_fail") == "discard":
                if "discard" not in desc.lower():
                    desc += " (else Discard)"

            if eff.params.get("both_players"):
                desc += " (Both Players)" if not is_jp else " (両プレイヤー)"

            if eff.params.get("filter") == "live" and "live" not in desc.lower() and "ライブ" not in desc:
                desc += " (Live Card)" if not is_jp else " (ライブカード)"
            if eff.params.get("filter") == "energy" and "energy" not in desc.lower() and "エネ" not in desc:
                desc += " (Energy)" if not is_jp else " (エネルギー)"

            parts.append(f"→ {desc}")

            # Check for Effect-level modal options (e.g. from parser fix)
            if eff.modal_options:
                for i, option in enumerate(eff.modal_options):
                    opt_descs = []
                    for sub_eff in option:
                        template = e_desc_map.get(sub_eff.effect_type, sub_eff.effect_type.name)
                        context = sub_eff.params.copy()
                        context["value"] = sub_eff.value
                        try:
                            opt_descs.append(template.format(**context))
                        except KeyError:
                            opt_descs.append(template)
                    parts.append(
                        f"[Option {i + 1}: {' + '.join(opt_descs)}]"
                        if not is_jp
                        else f"[選択肢 {i + 1}: {' + '.join(opt_descs)}]"
                    )

        # Include modal options (Ability level - legacy/bullet points)
        if self.modal_options:
            for i, option in enumerate(self.modal_options):
                opt_descs = []
                for eff in option:
                    template = e_desc_map.get(eff.effect_type, eff.effect_type.name)
                    context = eff.params.copy()
                    context["value"] = eff.value
                    try:
                        opt_descs.append(template.format(**context))
                    except KeyError:
                        opt_descs.append(template)
                parts.append(
                    f"[Option {i + 1}: {' + '.join(opt_descs)}]"
                    if not is_jp
                    else f"[選択肢 {i + 1}: {' + '.join(opt_descs)}]"
                )

        return " ".join(parts)
