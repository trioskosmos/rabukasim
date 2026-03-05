import re
import re
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Union
import pydantic
from pydantic import ConfigDict
from engine.models.enums import CHAR_MAP
from engine.models.opcodes import Opcode

from .generated_metadata import EXTRA_CONSTANTS
from .generated_packer import (
    pack_a_standard, pack_a_heart_cost, pack_a_look_choose,
    pack_v_heart_counts, pack_v_look_choose, pack_s_standard
)


def to_signed_32(x):
    """Utility to convert an integer to a signed 32-bit integer."""
    x = int(x) & 0xFFFFFFFF
    return x - 0x100000000 if x >= 0x80000000 else x


class TriggerType(IntEnum):
    NONE = 0
    ON_PLAY = 1  # 登場時
    ON_LIVE_START = 2  # ライブ開始時
    ON_LIVE_SUCCESS = 3  # ライブ成功時
    TURN_START = 4
    TURN_END = 5
    CONSTANT = 6  # 常時
    ACTIVATED = 7  # 起動
    ON_LEAVES = 8  # 自動 - when member leaves stage/is discarded
    ON_REVEAL = 9  # エールにより公開、公開されたとき
    ON_POSITION_CHANGE = 10  # エリアを移動するたび
    ON_ACTIVATE = 7  # Alias for ACTIVATED


class TargetType(IntEnum):
    SELF = 0
    PLAYER = 1
    OPPONENT = 2
    ALL_PLAYERS = 3
    MEMBER_SELF = 4
    MEMBER_OTHER = 5
    CARD_HAND = 6
    CARD_DISCARD = 7
    CARD_DECK_TOP = 8
    OPPONENT_HAND = 9  # 相手の手札
    MEMBER_SELECT = 10  # Select manual target
    MEMBER_NAMED = 11  # Specific named member implementation
    OPPONENT_MEMBER = 12  # Specific opponent member target
    PLAYER_SELECT = 13  # 自分か相手を選ぶ


class EffectType(IntEnum):
    DRAW = 10
    ADD_BLADES = 11
    ADD_HEARTS = 12
    REDUCE_COST = 13
    LOOK_DECK = 14
    RECOVER_LIVE = 15
    BOOST_SCORE = 16
    RECOVER_MEMBER = 17
    BUFF_POWER = 18
    IMMUNITY = 19
    MOVE_MEMBER = 20
    SWAP_CARDS = 21
    SEARCH_DECK = 22  # [UNUSED]
    ENERGY_CHARGE = 23
    SET_BLADES = 24
    SET_HEARTS = 25
    FORMATION_CHANGE = 26  # [UNUSED]
    NEGATE_EFFECT = 27
    ORDER_DECK = 28
    META_RULE = 29
    SELECT_MODE = 30
    MOVE_TO_DECK = 31
    TAP_OPPONENT = 32
    PLACE_UNDER = 33
    FLAVOR_ACTION = 34  # [UNUSED]
    RESTRICTION = 35
    BATON_TOUCH_MOD = 36
    SET_SCORE = 37
    SWAP_ZONE = 38  # [UNUSED]
    TRANSFORM_COLOR = 39
    REVEAL_CARDS = 40
    LOOK_AND_CHOOSE = 41
    CHEER_REVEAL = 42
    ACTIVATE_MEMBER = 43
    ADD_TO_HAND = 44
    COLOR_SELECT = 45
    REPLACE_EFFECT = 46  # [UNUSED]
    TRIGGER_REMOTE = 47
    REDUCE_HEART_REQ = 48
    MODIFY_SCORE_RULE = 49
    TAP_MEMBER = 53
    PLAY_MEMBER_FROM_HAND = 57
    MOVE_TO_DISCARD = 58
    GRANT_ABILITY = 60
    INCREASE_HEART_COST = 61
    REDUCE_YELL_COUNT = 62
    PLAY_MEMBER_FROM_DISCARD = 63
    PAY_ENERGY = 64
    SELECT_MEMBER = 65
    DRAW_UNTIL = 66
    SELECT_PLAYER = 67
    SELECT_LIVE = 68
    REVEAL_UNTIL = 69
    INCREASE_COST = 70
    PREVENT_PLAY_TO_SLOT = 71
    SWAP_AREA = 72
    TRANSFORM_HEART = 73
    SELECT_CARDS = 74
    OPPONENT_CHOOSE = 75
    PLAY_LIVE_FROM_DISCARD = 76
    REDUCE_LIVE_SET_LIMIT = 77
    LOOK_REORDER_DISCARD = 125
    DIV_VALUE = 126
    PREVENT_ACTIVATE = 82
    ACTIVATE_ENERGY = 81
    PREVENT_SET_TO_SUCCESS_PILE = 80  # [UNUSED]
    SET_HEART_COST = 83  # [UNUSED] (Fixed from 84 for parity)
    PREVENT_BATON_TOUCH = 90
    # New opcodes for BP05
    LOOK_DECK_DYNAMIC = 91
    REDUCE_SCORE = 92
    REPEAT_ABILITY = 93
    LOSE_EXCESS_HEARTS = 94
    SKIP_ACTIVATE_PHASE = 95
    PAY_ENERGY_DYNAMIC = 96
    PLACE_ENERGY_UNDER_MEMBER = 97
    CALC_SUM_COST = 106


class ConditionType(IntEnum):
    NONE = 0  # [UNUSED]
    TURN_1 = 200
    HAS_MEMBER = 201
    HAS_COLOR = 202  # [UNUSED]
    COUNT_STAGE = 203
    COUNT_HAND = 204
    COUNT_DISCARD = 205
    IS_CENTER = 206
    LIFE_LEAD = 207  # [UNUSED]
    COUNT_GROUP = 208
    GROUP_FILTER = 209
    OPPONENT_HAS = 210  # [UNUSED]
    SELF_IS_GROUP = 211  # [UNUSED]
    MODAL_ANSWER = 212
    COUNT_ENERGY = 213
    HAS_LIVE_CARD = 214
    COST_CHECK = 215
    RARITY_CHECK = 216  # [UNUSED]
    HAND_HAS_NO_LIVE = 217  # [UNUSED]
    COUNT_SUCCESS_LIVE = 218
    OPPONENT_HAND_DIFF = 219
    SCORE_COMPARE = 220
    HAS_CHOICE = 221  # [UNUSED]
    OPPONENT_CHOICE = 222  # [UNUSED]
    COUNT_HEARTS = 223
    COUNT_BLADES = 224
    OPPONENT_ENERGY_DIFF = 225
    HAS_KEYWORD = 226
    DECK_REFRESHED = 227
    HAS_MOVED = 228  # [UNUSED]
    HAND_INCREASED = 229  # [UNUSED]
    COUNT_LIVE_ZONE = 230
    BATON = 231
    TYPE_CHECK = 232
    IS_IN_DISCARD = 233  # [UNUSED]
    AREA_CHECK = 234
    COST_LEAD = 235
    SCORE_LEAD = 236
    HEART_LEAD = 237
    HAS_EXCESS_HEART = 238
    NOT_HAS_EXCESS_HEART = 239
    TOTAL_BLADES = 240
    COST_COMPARE = 241
    BLADE_COMPARE = 242
    HEART_COMPARE = 243
    OPPONENT_HAS_WAIT = 244
    IS_TAPPED = 245
    IS_ACTIVE = 246
    LIVE_PERFORMED = 247
    IS_PLAYER = 248
    IS_OPPONENT = 249
    # New conditions for BP05 (300-399 range)
    COUNT_ENERGY_EXACT = 301
    COUNT_BLADE_HEART_TYPES = 302
    OPPONENT_HAS_EXCESS_HEART = 303
    SCORE_TOTAL_CHECK = 304
    MAIN_PHASE = 305
    SELECT_MEMBER = 306
    SUCCESS_PILE_COUNT = 307
    IS_SELF_MOVE = 308
    DISCARDED_CARDS = 309
    YELL_REVEALED_UNIQUE_COLORS = 310
    SYNC_COST = 311
    SUM_VALUE = 312
    IS_WAIT = 313


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
    EffectType.FLAVOR_ACTION: "Flavor Action",  # [UNUSED]
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
    EffectType.FLAVOR_ACTION: "フレーバーアクション",  # [UNUSED]
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


class AbilityCostType(IntEnum):
    NONE = 0
    ENERGY = 1
    TAP_SELF = 2  # ウェイトにする
    DISCARD_HAND = 3  # 手札を捨てる
    RETURN_HAND = 4  # 手札に戻す (Self bounce)
    SACRIFICE_SELF = 5  # このメンバーを控え室に置く
    REVEAL_HAND_ALL = 6  # 手札をすべて公開する
    SACRIFICE_UNDER = 7  # 下に置かれているカードを控え室に置く
    DISCARD_ENERGY = 8  # エネルギーを控え室に置く
    REVEAL_HAND = 9  # 手札を公開する
    TAP_PLAYER = 2  # Alias for TAP_SELF (ウェイトにする)

    # Missing aliases/members inferred from usage
    TAP_MEMBER = 20
    TAP_ENERGY = 21
    PAY_ENERGY = 1  # Alias for ENERGY
    REST_MEMBER = 22
    RETURN_MEMBER_TO_HAND = 23
    DISCARD_MEMBER = 24
    DISCARD_LIVE = 25
    REMOVE_LIVE = 26
    REMOVE_MEMBER = 27
    RETURN_LIVE_TO_HAND = 28
    RETURN_LIVE_TO_DECK = 29
    RETURN_MEMBER_TO_DECK = 30
    PLACE_MEMBER_FROM_HAND = 31
    PLACE_LIVE_FROM_HAND = 32
    PLACE_ENERGY_FROM_HAND = 33
    PLACE_MEMBER_FROM_DISCARD = 34
    PLACE_LIVE_FROM_DISCARD = 35
    PLACE_ENERGY_FROM_DISCARD = 36
    PLACE_MEMBER_FROM_DECK = 37
    PLACE_LIVE_FROM_DECK = 38
    PLACE_ENERGY_FROM_DECK = 39
    # REVEAL_HAND = 40  # Moved to 9
    SHUFFLE_DECK = 41
    DRAW_CARD = 42
    DISCARD_TOP_DECK = 43
    REMOVE_TOP_DECK = 44
    RETURN_DISCARD_TO_DECK = 45
    RETURN_REMOVED_TO_DECK = 46
    RETURN_REMOVED_TO_HAND = 47
    RETURN_REMOVED_TO_DISCARD = 48
    PLACE_ENERGY_FROM_SUCCESS = 49
    DISCARD_SUCCESS_LIVE = 50
    REMOVE_SUCCESS_LIVE = 51
    RETURN_SUCCESS_LIVE_TO_HAND = 52
    RETURN_SUCCESS_LIVE_TO_DECK = 53
    RETURN_SUCCESS_LIVE_TO_DISCARD = 54
    PLACE_MEMBER_FROM_SUCCESS = 55
    PLACE_LIVE_FROM_SUCCESS = 56
    PLACE_ENERGY_FROM_REMOVED = 57
    PLACE_MEMBER_FROM_REMOVED = 58
    PLACE_LIVE_FROM_REMOVED = 59
    RETURN_ENERGY_TO_DECK = 60
    RETURN_ENERGY_TO_HAND = 61
    REMOVE_ENERGY = 62
    RETURN_STAGE_ENERGY_TO_HAND = 64
    DISCARD_STAGE_ENERGY = 65
    REMOVE_STAGE_ENERGY = 66
    DISCARD_STAGE = 65  # Alias for DISCARD_STAGE_ENERGY (often used for members/energy)
    MOVE_TO_DISCARD = 5  # Common alias for sacrifice/discard
    PLACE_ENERGY_FROM_STAGE_ENERGY = 67
    PLACE_MEMBER_FROM_STAGE_ENERGY = 68
    PLACE_LIVE_FROM_STAGE_ENERGY = 69
    PLACE_ENERGY_FROM_HAND_TO_STAGE_ENERGY = 70
    PLACE_MEMBER_FROM_HAND_TO_STAGE_ENERGY = 71
    PLACE_LIVE_FROM_HAND_TO_STAGE_ENERGY = 72
    PLACE_ENERGY_FROM_DISCARD_TO_STAGE_ENERGY = 73
    PLACE_MEMBER_FROM_DISCARD_TO_STAGE_ENERGY = 74
    PLACE_LIVE_FROM_DISCARD_TO_STAGE_ENERGY = 75
    PLACE_ENERGY_FROM_DECK_TO_STAGE_ENERGY = 76
    PLACE_MEMBER_FROM_DECK_TO_STAGE_ENERGY = 77
    PLACE_LIVE_FROM_DECK_TO_STAGE_ENERGY = 78
    PLACE_ENERGY_FROM_SUCCESS_TO_STAGE_ENERGY = 79
    PLACE_MEMBER_FROM_SUCCESS_TO_STAGE_ENERGY = 80
    PLACE_LIVE_FROM_SUCCESS_TO_STAGE_ENERGY = 81
    PLACE_ENERGY_FROM_REMOVED_TO_STAGE_ENERGY = 82
    PLACE_MEMBER_FROM_REMOVED_TO_STAGE_ENERGY = 83
    PLACE_LIVE_FROM_REMOVED_TO_STAGE_ENERGY = 84
    RETURN_LIVE_TO_DISCARD = 85
    RETURN_LIVE_TO_REMOVED = 86
    RETURN_LIVE_TO_SUCCESS = 87
    RETURN_MEMBER_TO_DISCARD = 88
    RETURN_MEMBER_TO_REMOVED = 89
    RETURN_MEMBER_TO_SUCCESS = 90
    RETURN_ENERGY_TO_DISCARD = 91
    RETURN_ENERGY_TO_REMOVED = 92
    RETURN_ENERGY_TO_SUCCESS = 93
    RETURN_SUCCESS_LIVE_TO_REMOVED = 94
    RETURN_REMOVED_TO_SUCCESS = 95
    RETURN_STAGE_ENERGY_TO_DISCARD = 96
    RETURN_STAGE_ENERGY_TO_REMOVED = 97
    RETURN_STAGE_ENERGY_TO_SUCCESS = 98
    RETURN_DISCARD_TO_HAND = 99
    RETURN_DISCARD_TO_REMOVED = 100
    RETURN_DISCARD_TO_SUCCESS = 101
    RETURN_DECK_TO_DISCARD = 102
    RETURN_DECK_TO_HAND = 103
    RETURN_DECK_TO_REMOVED = 104
    RETURN_DECK_TO_SUCCESS = 105
    RETURN_ENERGY_DECK_TO_DISCARD = 106
    RETURN_ENERGY_DECK_TO_HAND = 107
    RETURN_ENERGY_DECK_TO_REMOVED = 108
    RETURN_ENERGY_DECK_TO_SUCCESS = 109

    # Auto-generated missing members for effect_mixin.py compatibility
    PLACE_ENERGY_FROM_DECK_TO_DISCARD = 110
    PLACE_ENERGY_FROM_DECK_TO_HAND = 111
    PLACE_ENERGY_FROM_DECK_TO_REMOVED = 112
    PLACE_ENERGY_FROM_DECK_TO_SUCCESS = 113
    PLACE_ENERGY_FROM_DISCARD_TO_HAND = 114
    PLACE_ENERGY_FROM_DISCARD_TO_REMOVED = 115
    PLACE_ENERGY_FROM_DISCARD_TO_SUCCESS = 116
    PLACE_ENERGY_FROM_ENERGY_DECK = 117
    PLACE_ENERGY_FROM_ENERGY_DECK_TO_DISCARD = 118
    PLACE_ENERGY_FROM_ENERGY_DECK_TO_HAND = 119
    PLACE_ENERGY_FROM_ENERGY_DECK_TO_REMOVED = 120
    PLACE_ENERGY_FROM_ENERGY_DECK_TO_STAGE_ENERGY = 121
    PLACE_ENERGY_FROM_ENERGY_DECK_TO_SUCCESS = 122
    PLACE_ENERGY_FROM_ENERGY_ZONE_TO_DISCARD = 123
    PLACE_ENERGY_FROM_ENERGY_ZONE_TO_HAND = 124
    PLACE_ENERGY_FROM_ENERGY_ZONE_TO_REMOVED = 125
    PLACE_ENERGY_FROM_ENERGY_ZONE_TO_SUCCESS = 126
    PLACE_ENERGY_FROM_HAND_TO_DISCARD = 127
    PLACE_ENERGY_FROM_HAND_TO_REMOVED = 128
    PLACE_ENERGY_FROM_HAND_TO_SUCCESS = 129
    PLACE_ENERGY_FROM_REMOVED_TO_DISCARD = 130
    PLACE_ENERGY_FROM_REMOVED_TO_HAND = 131
    PLACE_ENERGY_FROM_REMOVED_TO_SUCCESS = 132
    PLACE_ENERGY_FROM_STAGE_ENERGY_TO_DISCARD = 133
    PLACE_ENERGY_FROM_STAGE_ENERGY_TO_HAND = 134
    PLACE_ENERGY_FROM_STAGE_ENERGY_TO_REMOVED = 135
    PLACE_ENERGY_FROM_STAGE_ENERGY_TO_SUCCESS = 136
    PLACE_ENERGY_FROM_SUCCESS_TO_DISCARD = 137
    PLACE_ENERGY_FROM_SUCCESS_TO_HAND = 138
    PLACE_ENERGY_FROM_SUCCESS_TO_REMOVED = 139
    PLACE_LIVE_FROM_DECK_TO_DISCARD = 140
    PLACE_LIVE_FROM_DECK_TO_HAND = 141
    PLACE_LIVE_FROM_DECK_TO_REMOVED = 142
    PLACE_LIVE_FROM_DECK_TO_SUCCESS = 143
    PLACE_LIVE_FROM_DISCARD_TO_HAND = 144
    PLACE_LIVE_FROM_DISCARD_TO_REMOVED = 145
    PLACE_LIVE_FROM_DISCARD_TO_SUCCESS = 146
    PLACE_LIVE_FROM_ENERGY_DECK = 147
    PLACE_LIVE_FROM_ENERGY_DECK_TO_DISCARD = 148
    PLACE_LIVE_FROM_ENERGY_DECK_TO_HAND = 149
    PLACE_LIVE_FROM_ENERGY_DECK_TO_REMOVED = 150
    PLACE_LIVE_FROM_ENERGY_DECK_TO_STAGE_ENERGY = 151
    PLACE_LIVE_FROM_ENERGY_DECK_TO_SUCCESS = 152
    PLACE_LIVE_FROM_ENERGY_ZONE_TO_DISCARD = 153
    PLACE_LIVE_FROM_ENERGY_ZONE_TO_HAND = 154
    PLACE_LIVE_FROM_ENERGY_ZONE_TO_REMOVED = 155
    PLACE_LIVE_FROM_ENERGY_ZONE_TO_SUCCESS = 156
    PLACE_LIVE_FROM_HAND_TO_DISCARD = 157
    PLACE_LIVE_FROM_HAND_TO_REMOVED = 158
    PLACE_LIVE_FROM_HAND_TO_SUCCESS = 159
    PLACE_LIVE_FROM_REMOVED_TO_DISCARD = 160
    PLACE_LIVE_FROM_REMOVED_TO_HAND = 161
    PLACE_LIVE_FROM_REMOVED_TO_SUCCESS = 162
    PLACE_LIVE_FROM_STAGE_ENERGY_TO_DISCARD = 163
    PLACE_LIVE_FROM_STAGE_ENERGY_TO_HAND = 164
    PLACE_LIVE_FROM_STAGE_ENERGY_TO_REMOVED = 165
    PLACE_LIVE_FROM_STAGE_ENERGY_TO_SUCCESS = 166
    PLACE_LIVE_FROM_SUCCESS_TO_DISCARD = 167
    PLACE_LIVE_FROM_SUCCESS_TO_HAND = 168
    PLACE_LIVE_FROM_SUCCESS_TO_REMOVED = 169
    PLACE_MEMBER_FROM_DECK_TO_DISCARD = 170
    PLACE_MEMBER_FROM_DECK_TO_HAND = 171
    PLACE_MEMBER_FROM_DECK_TO_REMOVED = 172
    PLACE_MEMBER_FROM_DECK_TO_SUCCESS = 173
    PLACE_MEMBER_FROM_DISCARD_TO_HAND = 174
    PLACE_MEMBER_FROM_DISCARD_TO_REMOVED = 175
    PLACE_MEMBER_FROM_DISCARD_TO_SUCCESS = 176
    PLACE_MEMBER_FROM_ENERGY_DECK = 177
    PLACE_MEMBER_FROM_ENERGY_DECK_TO_DISCARD = 178
    PLACE_MEMBER_FROM_ENERGY_DECK_TO_HAND = 179
    PLACE_MEMBER_FROM_ENERGY_DECK_TO_REMOVED = 180
    PLACE_MEMBER_FROM_ENERGY_DECK_TO_STAGE_ENERGY = 181
    PLACE_MEMBER_FROM_ENERGY_DECK_TO_SUCCESS = 182
    PLACE_MEMBER_FROM_ENERGY_ZONE_TO_DISCARD = 183
    PLACE_MEMBER_FROM_ENERGY_ZONE_TO_HAND = 184
    PLACE_MEMBER_FROM_ENERGY_ZONE_TO_REMOVED = 185
    PLACE_MEMBER_FROM_ENERGY_ZONE_TO_SUCCESS = 186
    PLACE_MEMBER_FROM_HAND_TO_DISCARD = 187
    PLACE_MEMBER_FROM_HAND_TO_REMOVED = 188
    PLACE_MEMBER_FROM_HAND_TO_SUCCESS = 189
    PLACE_MEMBER_FROM_REMOVED_TO_DISCARD = 190
    PLACE_MEMBER_FROM_REMOVED_TO_HAND = 191
    PLACE_MEMBER_FROM_REMOVED_TO_SUCCESS = 192
    PLACE_MEMBER_FROM_STAGE_ENERGY_TO_DISCARD = 193
    PLACE_MEMBER_FROM_STAGE_ENERGY_TO_HAND = 194
    PLACE_MEMBER_FROM_STAGE_ENERGY_TO_REMOVED = 195
    PLACE_MEMBER_FROM_STAGE_ENERGY_TO_SUCCESS = 196
    PLACE_MEMBER_FROM_SUCCESS_TO_DISCARD = 197
    PLACE_MEMBER_FROM_SUCCESS_TO_HAND = 198
    PLACE_MEMBER_FROM_SUCCESS_TO_REMOVED = 199


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
    card_no: str = "" # Metadata for debugging/tracing
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
        self.filters = [] # Reset filters for this compilation

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
                        AbilityCostType.NONE: Opcode.SELECT_CARDS, # Fallback for named costs
                    }
                    if instr.is_optional or instr.type in mapping or instr.params.get("cost_type_name") in ["CALC_SUM_COST", "SELECT_CARDS", "SELECT_MEMBER"]:
                        self._compile_single_cost(instr, temp_bc)
                instr_bytecodes.append(temp_bc)

            # Pass 2: Emit bytecode with accurate jump targets
            for i, instr in enumerate(self.instructions):
                bc_chunk = instr_bytecodes[i]
                bytecode.extend(bc_chunk)
                
                if isinstance(instr, Cost) and instr.is_optional:
                    # Calculate jump target based on BYTECODE size, not instruction count
                    # skip_size = sum of lengths of remaining bytecode chunks / 5
                    remaining_bc_sum = sum(len(c) for c in instr_bytecodes[i+1:])
                    # Add 1 for the implicit RETURN at the end
                    skip_count = (remaining_bc_sum // 5) + 1
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
                bytecode.extend([int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
                for e in block:
                    # Create a copy with target=PLAYER (Self)
                    e_self = Effect(e.effect_type, e.value, e.value_cond, TargetType.PLAYER, e.params)
                    e_self.is_optional = e.is_optional
                    self._compile_effect_wrapper(e_self, bytecode)

                # Emit block for OPPONENT
                bytecode.extend([int(Opcode.SET_TARGET_OPPONENT), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
                for e in block:
                    # Create a copy with target=OPPONENT
                    e_opp = Effect(e.effect_type, e.value, e.value_cond, TargetType.OPPONENT, e.params)
                    e_opp.is_optional = e.is_optional
                    self._compile_effect_wrapper(e_opp, bytecode)

                # Reset context
                bytecode.extend([int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])

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
                count_eq = cond.params.get("count_eq") or params_upper.get("COUNT_EQ")
                if count_eq:
                    try:
                        val = int(count_eq)
                    except (ValueError, TypeError):
                        val = 0

                # Attr: Standardized packing for filters
                attr = self._pack_filter_attr(cond)

                bytecode.extend([
                    int(Opcode.CHECK_BATON), 
                    to_signed_32(val), 
                    to_signed_32(attr & 0xFFFFFFFF), 
                    to_signed_32((attr >> 32) & 0xFFFFFFFF), 
                    to_signed_32(0)
                ])
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
            if op == 226: # CHECK_HAS_KEYWORD (Opcode 226)
                attr = 0
                kw = str(cond.params.get("keyword") or "").upper()
                if "PLAYED_THIS_TURN" in kw: 
                    attr |= (1 << 44)
                elif "YELL_COUNT" in kw: 
                    attr |= (1 << 45)
                elif "HAS_LIVE_SET" in kw: 
                    attr |= (1 << 46)
                elif "ENERGY" in kw: 
                    attr |= (1 << 62)
                    attr |= self._pack_filter_attr(cond)
                elif "MEMBER" in kw: 
                    attr |= (1 << 63)
                    attr |= self._pack_filter_attr(cond)
                else: 
                     # Fallback for implicit keywords
                     if cond.type == ConditionType.HAS_KEYWORD:
                         cond.params["keyword"] = "PLAYED_THIS_TURN"
                         attr |= (1 << 44)
            elif op == 65: # CHECK_HEART_COMPARE (Opcode 65)
                # Heart compare uses raw color index in bits 0-6
                from engine.models.enums import HeartColor
                color_name = str(cond.params.get("color") or "").upper()
                try:
                    attr = int(HeartColor[color_name])
                except:
                    # Fallback: try to extract from filter string if directly missing
                    f_str = str(cond.params.get("filter", "")).upper()
                    if "YELLOW" in f_str: attr = 2
                    elif "RED" in f_str: attr = 1
                    elif "PINK" in f_str: attr = 0
                    elif "BLUE" in f_str: attr = 4
                    elif "GREEN" in f_str: attr = 3
                    elif "PURPLE" in f_str: attr = 5
                    else: attr = 7 # Total count fallback
            else:
                attr = self._pack_filter_attr(cond)
            
            # Persist back to the Condition object for JSON serialization
            cond.value = val
            cond.attr = attr

            # Comparison and Slot Mapping
            comp_str = str(cond.params.get("comparison") or params_upper.get("COMPARISON") or "GE").upper()
            comp_map = {"EQ": 0, "GT": 1, "LT": 2, "GE": 3, "LE": 4}
            comp_val = comp_map.get(comp_str, 0)

            slot = 0
            zone = str(cond.params.get("zone") or params_upper.get("ZONE") or "").upper()
            if zone == "LIVE_ZONE": slot = 1
            elif zone == "STAGE": slot = 0
            elif zone == "YELL" or zone == "YELL_REVEALED": slot = 15
            elif str(cond.params.get("context", "")).lower() == "excess": slot = 2
            else:
                slot_raw = cond.params.get("TargetSlot") or params_upper.get("TARGETSLOT") or 0
                slot = int(slot_raw)

            area_val = cond.params.get("area") or params_upper.get("AREA")
            if area_val:
                a_str = str(area_val).upper()
                if "LEFT" in a_str: slot |= (1 << 28)
                elif "CENTER" in a_str: slot |= (2 << 28)
                elif "RIGHT" in a_str: slot |= (3 << 28)

            packed_slot = (slot & 0x0F) | ((comp_val & 0x0F) << 4) | (slot & 0x7FFFFF00)

            bytecode.extend([
                to_signed_32(int(op) + (1000 if cond.is_negated else 0)),
                to_signed_32(val),
                to_signed_32(attr & 0xFFFFFFFF),
                to_signed_32((attr >> 32) & 0xFFFFFFFF),
                to_signed_32(packed_slot)
            ])

        elif cond.type == ConditionType.TYPE_CHECK:
            if hasattr(Opcode, "CHECK_TYPE_CHECK"):
                # card_type: "live" = 1, "member" = 0
                ctype = 1 if str(cond.params.get("card_type", "")).lower() == "live" else 0
                bytecode.extend([int(Opcode.CHECK_TYPE_CHECK), to_signed_32(ctype), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
        elif cond.type == ConditionType.SELECT_MEMBER:
            # Format: SELECT_MEMBER(1) {FILTER="HAS_HEART_02_X3", AREA="LEFT"}
            attr = self._pack_filter_attr(cond)
            slot = self._pack_filter_slot(str(cond.params.get("area", "")).upper())
            bytecode.extend([int(Opcode.SELECT_MEMBER), to_signed_32(1), to_signed_32(attr & 0xFFFFFFFF), to_signed_32((attr >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
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
            AbilityCostType.RETURN_SUCCESS_LIVE_TO_DECK: Opcode.MOVE_TO_DECK,
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
            slot = 0

            # --- Resolve Slot (Source) ---
            if cost.type in [
                AbilityCostType.DISCARD_HAND,
                AbilityCostType.RETURN_HAND,
                AbilityCostType.REVEAL_HAND,
                AbilityCostType.REVEAL_HAND_ALL,
            ]:
                slot = int(TargetType.CARD_HAND)
            elif cost.type in [AbilityCostType.TAP_SELF, AbilityCostType.TAP_MEMBER, AbilityCostType.SACRIFICE_SELF]:
                slot = int(TargetType.MEMBER_SELF)
            elif cost.type == AbilityCostType.DISCARD_ENERGY:
                slot = int(TargetType.SELF)  # Energy usually tied to player/self zone
            elif cost.type in [AbilityCostType.RETURN_DISCARD_TO_DECK]:
                slot = int(TargetType.CARD_DISCARD)
            elif cost.type in [AbilityCostType.RETURN_SUCCESS_LIVE_TO_DECK, AbilityCostType.DISCARD_SUCCESS_LIVE]:
                # Special Target for success pile? (Not explicitly in TargetType but engine handles)
                slot = 2  # Success area
            else:
                slot = int(TargetType.SELF)

            # --- Resolve Attr (Params/Destination) ---
            params_upper = {k.upper(): v for k, v in cost.params.items() if isinstance(k, str)}

            if op == Opcode.MOVE_TO_DECK:
                # 0=Discard, 1=Top, 2=Bottom
                to = str(cost.params.get("to") or params_upper.get("TO") or "top").lower()
                if to == "bottom":
                    attr = 2
                elif to == "top":
                    attr = 1

            # NEW: Packed Filter Logic for Selection/Manipulation Opcodes
            # Bits 4-7: Comparison (0:GE, 1:LE, 2:GT, 3:LT, 4:EQ)
            # Bits 8-15: Cost Limit (0-255)
            # Bits 16+: Packed Name Bits or Filter Flags

            # O_SELECT_MEMBER / O_PLAY_MEMBER_FROM_HAND / MOVE_TO_DISCARD, encode filters into 'attr' (a)
            if op in [Opcode.SELECT_MEMBER, Opcode.PLAY_MEMBER_FROM_HAND, Opcode.PLAY_MEMBER_FROM_DISCARD, Opcode.MOVE_TO_DISCARD]:
                # Value capture flag (Bit 25 of slot)
                if cost.params.get("destination") == "target_val" or params_upper.get("DESTINATION") == "TARGET_VAL":
                    slot |= (1 << 25)

                # Cost LE filter
                cle_raw = cost.params.get("cost_le") or params_upper.get("COST_LE")
                if cle_raw is not None:
                    cle = int(cle_raw)
                    attr |= 1 << 4  # Comparison = LE (1)
                    attr |= cle << 8

                # Name filter (Setsuna = 1 if using CHAR_MAP indices, or specialized bits)
                name_filter = cost.params.get("name") or params_upper.get("NAME")
                if name_filter:
                    from engine.models.enums import CHAR_MAP

                    char_id = CHAR_MAP.get(str(name_filter), 0)
                    if char_id > 0:
                        attr |= char_id << 16

            if cost.is_optional:
                attr |= (1 << 61)  # Bit 61 = Optional (Revised Project Standard)

            # Use value from cost params if available (max/count)
            value = cost.value
            count_raw = cost.params.get("count") or params_upper.get("COUNT")
            if not value and count_raw is not None:
                value = int(count_raw)
            
            # Fix: Default MOVE_TO_DISCARD for members to 1
            if op == Opcode.MOVE_TO_DISCARD and value == 0 and slot in (int(TargetType.MEMBER_SELF), int(TargetType.MEMBER_OTHER), int(TargetType.MEMBER_SELECT)):
                value = 1

            bytecode.extend([int(op), to_signed_32(int(value)), to_signed_32(attr & 0xFFFFFFFF), to_signed_32((attr >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
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

            bytecode.extend([int(Opcode.LOOK_DECK), to_signed_32(eff.value), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
            bytecode.extend([int(Opcode.ORDER_DECK), to_signed_32(eff.value), to_signed_32(attr & 0xFFFFFFFF), to_signed_32((attr >> 32) & 0xFFFFFFFF), to_signed_32(0)])
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
                bytecode.extend([int(Opcode.SELECT_MODE), to_signed_32(num_options), to_signed_32(0), to_signed_32(0), to_signed_32(slot)])

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
                bytecode.extend([int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
                # 2. Compile for SELF
                eff_self = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.PLAYER, eff.params)
                eff_self.is_optional = eff.is_optional
                self._compile_single_effect(eff_self, bytecode)

                # 3. SET_TARGET_OPPONENT
                bytecode.extend([int(Opcode.SET_TARGET_OPPONENT), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
                # 4. Compile for OPPONENT
                eff_opp = Effect(eff.effect_type, eff.value, eff.value_cond, TargetType.OPPONENT, eff.params)
                eff_opp.is_optional = eff.is_optional
                self._compile_single_effect(eff_opp, bytecode)

                # 5. Restore context to SELF (optional safety)
                bytecode.extend([int(Opcode.SET_TARGET_SELF), to_signed_32(0), to_signed_32(0), to_signed_32(0), to_signed_32(0)])
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
                attr = eff.params.get("color", 0) if isinstance(eff.params.get("color"), int) else 0

            # --- Target Resolution from Params ---
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

            slot_params = {
                "target_slot": eff.target.value if hasattr(eff.target, "value") else int(eff.target),
                "remainder_zone": 0,
                "source_zone": 0,
                "dest_zone": 0,
                "is_opponent": False,
                "is_reveal_until_live": False,
                "is_empty_slot": False,
                "is_wait": False,
                "area_idx": 0
            }

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

            # --- Zone Relocation ---
            src_val = 0
            if eff.effect_type in (
                EffectType.RECOVER_MEMBER, EffectType.RECOVER_LIVE,
                EffectType.PLAY_MEMBER_FROM_DISCARD, EffectType.PLAY_LIVE_FROM_DISCARD,
            ):
                source = str(eff.params.get("source", "discard")).lower()
                src_val = 7 if source == "discard" else 0
                if source == "yell": src_val = 15
                elif source in ("deck", "deck_top"): src_val = 8
                slot_params["source_zone"] = src_val

            # TAP/Interactive selection
            if eff.effect_type in (EffectType.TAP_OPPONENT, EffectType.TAP_MEMBER):
                attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.TAP_MEMBER:
                    attr |= 0x02  # Bit 1: Selection mode
                slot_params["source_zone"] = src_val

            # PLACE_UNDER params
            if eff.effect_type == EffectType.PLACE_UNDER:
                source = str(eff.params.get("from") or eff.params.get("source") or "").lower()
                u_src_val = 0
                if source == "energy": u_src_val = 1
                elif source == "discard": u_src_val = 2
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
                char_ids = []
                # Simple extraction of up to 3 character IDs
                raw_names = str(eff.params.get("group") or eff.params.get("target_name") or "")
                if raw_names:
                    parts = raw_names.replace(",", "/").split("/")
                    for p in parts[:3]:
                        p = p.strip()
                        if p in CHAR_MAP: char_ids.append(CHAR_MAP[p])

                attr = self._pack_filter_attr(eff)
                look_v = {"count": val, "char_id_1": char_ids[0] if char_ids else 0}
                look_a = {
                    "char_id_2": char_ids[1] if len(char_ids) > 1 else 0,
                    "char_id_3": char_ids[2] if len(char_ids) > 2 else 0,
                    "dest_discard": 1 if eff.params.get("destination") == "discard" else 0
                }
                val = pack_v_look_choose(**look_v)
                attr = attr | pack_a_look_choose(**look_a)

                src = str(eff.params.get("source") or eff.params.get("zone") or "DECK").upper()
                src_val = 8
                if src == "HAND": src_val = 6
                elif src == "DISCARD": src_val = 7
                elif src in ("YELL", "REVEALED", "CHEER"): src_val = 15
                elif src == "ENERGY": src_val = 3
                slot_params["source_zone"] = src_val

                rem_dest_str = str(eff.params.get("remainder") or eff.params.get("destination") or "").upper()
                rem_val = 0
                if rem_dest_str == "DISCARD": rem_val = 7
                elif rem_dest_str == "DECK": rem_val = 8
                elif rem_dest_str == "HAND": rem_val = 6
                elif rem_dest_str == "DECK_TOP": rem_val = 1
                elif rem_dest_str == "DECK_BOTTOM": rem_val = 2
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type in (EffectType.SELECT_CARDS, EffectType.SELECT_MEMBER, EffectType.SELECT_LIVE, EffectType.MOVE_TO_DISCARD, EffectType.MOVE_MEMBER):
                attr = self._pack_filter_attr(eff)
                src_zone_str = str(eff.params.get("source") or eff.params.get("zone") or "DECK").upper()
                if "," not in src_zone_str:
                    src_val = 8
                    if src_zone_str == "HAND": src_val = 6
                    elif src_zone_str == "DISCARD": src_val = 7
                    elif src_zone_str in ("YELL", "REVEALED", "CHEER"): src_val = 15
                    slot_params["source_zone"] = src_val

                rem_val = eff.params.get("remainder_zone", 0)
                if isinstance(rem_val, str):
                    rem_map = {"DISCARD": 7, "DECK": 8, "HAND": 6, "DECK_TOP": 1, "DECK_BOTTOM": 2}
                    rem_val = rem_map.get(rem_val.upper(), 0)
                slot_params["remainder_zone"] = rem_val

            if eff.effect_type == EffectType.SET_HEART_COST:
                colors = ["pink", "red", "yellow", "green", "blue", "purple"]
                v_params = {c: int(eff.params.get(c, 0)) for c in colors}
                val = pack_v_heart_counts(**v_params)

                color_map = {"PINK": 1, "RED": 2, "YELLOW": 3, "GREEN": 4, "BLUE": 5, "PURPLE": 6, "ANY": 7, "STAR": 7, "ALL": 7, "ANY_HEART": 7}
                req_list = []
                add_val = eff.params.get("add")
                if isinstance(add_val, (str, list)):
                    parts = add_val.replace(",", "/").split("/") if isinstance(add_val, str) else add_val
                    req_list = [color_map.get(str(p).strip().upper(), 0) for p in parts[:8]]
                
                any_count = int(eff.params.get("any", 0))
                for _ in range(any_count):
                    if len(req_list) < 8: req_list.append(7)
                
                a_params = {f"req_{i+1}": req_list[i] if i < len(req_list) else 0 for i in range(8)}
                unit_val = eff.params.get("unit")
                if unit_val:
                    try:
                        from engine.models.enums import Unit

                        u_id = int(str(unit_val)) if str(unit_val).isdigit() else int(Unit.from_japanese_name(str(unit_val)))
                        a_params["unit_enabled"] = True
                        a_params["unit_id"] = u_id & 0x7F
                    except: pass
                attr = pack_a_heart_cost(**a_params)

            if eff.effect_type == EffectType.REVEAL_UNTIL:
                attr = self._pack_filter_attr(eff)
                if eff.value_cond == ConditionType.TYPE_CHECK and str(eff.params.get("card_type", "")).lower() == "live":
                    slot_params["is_reveal_until_live"] = True
                elif eff.value_cond == ConditionType.COST_CHECK:
                    attr = int(eff.params.get("min", 0))

            if eff.effect_type == EffectType.META_RULE:
                m_type = str(eff.params.get("type", "") or eff.params.get("meta_type", "") or "CHEER_MOD").upper()
                mapping = {
                    "CHEER_MOD": 0, "HEART_RULE": 1, "ALL_BLADE_AS_ANY_HEART": 1, "LIVE": 2,
                    "SHUFFLE": 3, "OPPONENT_TRIGGER_ALLOWED": 4, "LOSE_BLADE_HEART": 5,
                    "RE_CHEER": 6, "GROUP_ALIAS": 7, "SCORE_RULE": 8, "PREVENT_SET_TO_SUCCESS_PILE": 9,
                    "ACTION_YELL_MULLIGAN": 10, "TRIGGER_YELL_AGAIN": 11, "MOVE_SUCCESS": 12, "RESET_YELL_HEARTS": 13,
                }
                attr = mapping.get(m_type, 0)
                if attr == 1:
                    src = str(eff.params.get("source", "")).lower()
                    if src == "all_blade" or m_type == "ALL_BLADE_AS_ANY_HEART": val = 1
                    elif src == "blade": val = 2

            if eff.effect_type in (EffectType.MOVE_TO_DISCARD, EffectType.COLOR_SELECT, EffectType.TRANSFORM_HEART, EffectType.TRANSFORM_COLOR):
                attr = self._pack_filter_attr(eff)
                if eff.effect_type == EffectType.MOVE_TO_DISCARD and eff.params.get("operation") == "UNTIL_SIZE":
                    val = (int(val) & 0x7FFFFFFF) | (1 << 31)

            # --- Multiplier Support (Dynamic Value) ---
            if eff.params.get("per_card") or eff.params.get("per_member") or eff.params.get("has_multiplier"):
                count_src = str(eff.params.get("per_card", "")).upper()
                if count_src == "COUNT" and hasattr(self, "_last_counted_zone") and self._last_counted_zone:
                    count_src = self._last_counted_zone
                
                count_op_map = {
                    "HAND": int(ConditionType.COUNT_HAND),
                    "DISCARD": int(ConditionType.COUNT_DISCARD),
                    "ENERGY": int(ConditionType.COUNT_ENERGY),
                    "COLOR": 250, # C_COUNT_UNIQUE_COLORS
                    "SUCCESS_LIVE": 218, "LIVE_AREA": 218, "SUCCESS_PILE": 218, "SUCCESS_PILE_COUNT": 218
                }
                count_op = count_op_map.get(count_src, int(ConditionType.COUNT_STAGE))
                slot_params["remainder_zone"] = count_op
                slot_params["is_dynamic"] = True
                attr |= self._pack_filter_attr(eff)

            # Default to Choice (slot 4) if target is generic
            is_non_stage_discard = eff.effect_type == EffectType.MOVE_TO_DISCARD and slot_params["source_zone"] in (6, 8)
            if eff.target in (TargetType.SELF, TargetType.PLAYER) and not is_non_stage_discard and not slot_params.get("is_dynamic", False):
                slot_params["target_slot"] = 4

            slot = pack_s_standard(**slot_params)

            # Special encoding for LOOK_AND_CHOOSE: val = look_count | (pick_count << 8) | (color_mask << 23)
            if eff.effect_type == EffectType.LOOK_AND_CHOOSE:
                look_count = int(val)
                # Note: pick_count is handled by v_remaining/choice loop in engine
                char_ids = [int(CHAR_MAP.get(c.upper(), 0)) for c in str(eff.params.get("character", "")).split("/") if c.strip()]
                
                look_v = {
                    "count": look_count, 
                    "char_id_1": char_ids[0] if char_ids else 0,
                    "reveal": 1 if eff.params.get("reveal") else 0
                }
                look_a = {
                    "char_id_2": char_ids[1] if len(char_ids) > 1 else 0,
                    "char_id_3": char_ids[2] if len(char_ids) > 2 else 0,
                    "dest_discard": 1 if eff.params.get("destination") == "discard" else 0
                }
                val = pack_v_look_choose(**look_v)
                attr = (attr & 0x00000000FFFFFFFF) | pack_a_look_choose(**look_a)
                attr |= self._pack_filter_attr(eff)

            # Redundant setting for PREVENT_PLAY_TO_SLOT (relies on slot bit 24)
            if eff.effect_type == EffectType.PREVENT_PLAY_TO_SLOT:
                pass # Target opponent bit 24 handles this generically


            # ENSURE OPTIONAL BIT 61 SET FOR ALL OPCODES
            if eff.is_optional or eff.params.get("is_optional"):
                attr |= (1 << 61)

            attr_val = attr if not eff.params.get("all") else (attr | 0x80)

            # --- SYSTEMIC FIX: Ensure Opcode Mapping for all types ---
            if eff.effect_type == EffectType.LOOK_REORDER_DISCARD:
                op = Opcode.LOOK_REORDER_DISCARD
                v = int(val)
                bytecode.extend([int(op), to_signed_32(v), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            elif eff.effect_type == EffectType.DIV_VALUE:
                op = Opcode.DIV_VALUE
                v = int(eff.params.get("divisor") or eff.value or 2)
                bytecode.extend([int(op), to_signed_32(v), 0, 0, 0])
            elif eff.effect_type == EffectType.REVEAL_UNTIL:
                op = Opcode.REVEAL_UNTIL
                v = int(val)
                bytecode.extend([int(op), to_signed_32(v), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            elif eff.effect_type == EffectType.CALC_SUM_COST:
                op = Opcode.CALC_SUM_COST
                bytecode.extend([int(op), to_signed_32(val), to_signed_32(attr_val & 0xFFFFFFFF), to_signed_32((attr_val >> 32) & 0xFFFFFFFF), to_signed_32(slot)])
            else:
                # Fix: Default MOVE_TO_DISCARD for members to 1
                if op == Opcode.MOVE_TO_DISCARD and val == 0 and slot in (int(TargetType.MEMBER_SELF), int(TargetType.MEMBER_OTHER), int(TargetType.MEMBER_SELECT)):
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

    def _pack_filter_slot(self, area_str: str) -> int:
        """Helper to pack area strings into slot bits (28-30)."""
        slot = 0
        a_str = area_str.upper()
        if "LEFT" in a_str:
            slot |= (1 << 28)
        elif "CENTER" in a_str:
            slot |= (2 << 28)
        elif "RIGHT" in a_str:
            slot |= (3 << 28)
        return slot


    def _pack_filter_attr(self, source: Any) -> int:
        """
        Standardized packing for all filter parameters (Revision 5, 64-bit).
        'source' can be an Effect, Condition, or direct Dict params.
        """
        attr = 0
        from engine.models.enums import Group, Unit, HeartColor, CHAR_MAP
        import re
        
        # 0. Initialize params from various sources
        if hasattr(source, "params"):
            params = source.params
        elif isinstance(source, dict):
            params = source
        else:
            params = {}
            
        params_upper = {str(k).upper(): v for k, v in params.items() if isinstance(k, str)}
        
        # Extract filter string and other parameters
        filter_str = str(params.get("filter") or params_upper.get("FILTER") 
                        or params.get("player_center_filter") or params_upper.get("PLAYER_CENTER_FILTER")
                        or params.get("opponent_center_filter") or params_upper.get("OPPONENT_CENTER_FILTER")
                        or "").upper()
        
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
            "keyword_member": False
        }
        
        raw_val = params.get("val") or params.get("value") or params_upper.get("VAL") or params_upper.get("VALUE") or 0
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            val = 0
        colors = params.get("colors") or params.get("choices") or ([params.get("color")] if "color" in params else [])
        
        # 1. Target Player (Bits 0-1)
        if hasattr(source, "target"):
            if source.target == TargetType.OPPONENT: 
                filter_obj["target_player"] = 2
            else: 
                filter_obj["target_player"] = 1
        elif "OPPONENT" in filter_str:
            filter_obj["target_player"] = 2
        else:
            filter_obj["target_player"] = 1

        # 2. Card Type (Bits 2-3)
        ctype = str(params.get("type") or params.get("card_type") or "").lower()
        if not ctype and "TYPE=" in filter_str:
            m = re.search(r"TYPE=(\w+)", filter_str)
            if m: ctype = m.group(1).lower()
        
        if "live" in ctype: 
            filter_obj["card_type"] = 2
        elif "member" in ctype: 
            filter_obj["card_type"] = 1

        # 3. Group Filter (Bit 4 + Bits 5-11)
        group_val = params.get("group") or params.get("group_id") or params_upper.get("GROUP_ID")
        if not group_val and "GROUP_ID=" in filter_str:
            m = re.search(r"GROUP_ID=(\d+)", filter_str)
            if m: group_val = m.group(1)
        elif not group_val and "GROUP_" in filter_str:
            m = re.search(r"GROUP_([A-Z]+)", filter_str)
            if m: group_val = m.group(1)
        elif not group_val and "NIJIGASAKI" in filter_str: group_val = 2
        elif not group_val and "LIELLA" in filter_str: group_val = 3
        elif not group_val and "HASUNOSORA" in filter_str: group_val = 4

        if group_val:
            try:
                g_id = int(str(group_val)) if str(group_val).isdigit() else int(Group.from_japanese_name(str(group_val).replace("_", " ")))
                filter_obj["group_enabled"] = True
                filter_obj["group_id"] = g_id & 0x7F
            except: pass

        # 4. Unit Filter (Bit 16 + Bits 17-23)
        unit_val = params.get("unit") or params.get("unit_id") or params_upper.get("UNIT_ID")
        if not unit_val and "UNIT_ID=" in filter_str:
            m = re.search(r"UNIT_ID=(\d+)", filter_str)
            if m: unit_val = m.group(1)
        elif not unit_val and "UNIT_" in filter_str:
            m = re.search(r"UNIT_([A-Z0-9_]+)", filter_str)
            if m: unit_val = m.group(1)
        elif not unit_val and "UNIT_BIBI" in filter_str: unit_val = 2

        if unit_val:
            try:
                u_id = int(str(unit_val)) if str(unit_val).isdigit() else int(Unit.from_japanese_name(str(unit_val).replace("_", " ")))
                filter_obj["unit_enabled"] = True
                filter_obj["unit_id"] = u_id & 0x7F
            except: pass

        # 5. Cost Filter (Bit 24 + Bits 25-29 + Bit 30=Mode + Bit 31=Type=1)
        c_min = params.get("cost_min") or params.get("cost_ge")
        c_max = params.get("cost_max") or params.get("cost_le") or params.get("total_cost_le")
        
        if c_min is None and "COST_GE=" in filter_str:
            m = re.search(r"COST_GE=(\d+)", filter_str)
            if m: c_min = m.group(1)
        if c_max is None and "COST_LE=" in filter_str:
            m = re.search(r"COST_LE=(\d+)", filter_str)
            if m: c_max = m.group(1)

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
            except: pass
        elif c_max is not None:
            try:
                val_c = int(c_max)
                filter_obj["value_enabled"] = True
                filter_obj["value_threshold"] = val_c & 0x1F
                filter_obj["is_cost_type"] = True
                filter_obj["is_le"] = True
            except: pass

        # 6. Character Filter (IDs at 39-45, 46-52 in Revision 5)
        names = params.get("name") or params_upper.get("NAME")
        if not names and "NAME=" in filter_str:
            m = re.search(r"NAME=([^,]+)", filter_str)
            if m: names = m.group(1)

        if names:
            n_list = str(names).split("/")
            for i, n in enumerate(n_list[:2]):
                try:
                    n_norm = n.strip().replace(" ", "").replace("　", "")
                    c_id = 0
                    for k, cid in CHAR_MAP.items():
                        if k.replace(" ", "").replace("　", "") == n_norm:
                            c_id = cid
                            break
                    if c_id > 0:
                        filter_obj[f"char_id_{i+1}"] = c_id & 0x7F
                except: pass

        # 7. Heart Value and Color Filter (Bits 25-29 Threshold + Bit 31=Type=0 + Bits 32-38 Color Mask)
        if "HAS_HEART_" in filter_str:
            match = re.search(r"HAS_HEART_(\d+)(?:_X(\d+))?", filter_str)
            if match:
                color_code = match.group(1)
                count = match.group(2)
                try:
                    c_idx = int(color_code)
                    if not colors: colors = [c_idx]
                    if count: val = int(count)
                except: pass
        elif "HAS_COLOR_" in filter_str:
            match = re.search(r"HAS_COLOR_([A-Z]+)(?:_X(\d+))?", filter_str)
            if match:
                color_name = match.group(1).upper()
                count = match.group(2)
                try:
                    c_idx = int(HeartColor[color_name])
                    if not colors: colors = [c_idx]
                    if count: val = int(count)
                except: pass

        if val > 0:
            filter_obj["value_enabled"] = True
            filter_obj["value_threshold"] = val & 0x1F
            filter_obj["is_cost_type"] = False
            
        if colors or "COLOR=" in filter_str:
            color_mask = 0
            for c in (colors if isinstance(colors, list) else [colors]):
                if c is None: continue
                try:
                    if isinstance(c, str):
                        if c.isdigit(): c_idx = int(c)
                        else: c_idx = int(HeartColor[c.upper()])
                    else:
                        c_idx = int(c)
                    color_mask |= 1 << c_idx
                except: pass
            if color_mask > 0:
                filter_obj["color_mask"] = color_mask & 0x7F

        # 8. Meta Flags and Masks
        # Zone Mask (Bits 53-55)
        zone_val = params.get("zone") or params.get("source") or params_upper.get("ZONE")
        if zone_val:
            z_str = str(zone_val).upper()
            z_mask = 0
            if "STAGE" in z_str: z_mask = 4
            elif "HAND" in z_str: z_mask = 6
            elif "DISCARD" in z_str: z_mask = 7
            if z_mask > 0:
                filter_obj["zone_mask"] = z_mask & 0x07

        # Special ID (Bits 56-58)
        sid = params.get("special_id", 0)
        if sid:
            try:
                sid_int = int(sid)
                filter_obj["special_id"] = sid_int & 0x07
            except: pass

        # Setsuna (Bit 59)
        if names and any(s in str(names) for s in ["優木", "せつ菜"]):
            filter_obj["is_setsuna"] = True

        # Internal Flags
        if params.get("is_optional") or "(Optional)" in str(params.get("pseudocode", "")):
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
            if cond.params.get("group"):
                cond_desc += f"({cond.params['group']})"
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
