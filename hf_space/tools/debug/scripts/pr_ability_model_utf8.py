?from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List


class TriggerType(IntEnum):
    NONE = 0
    ON_PLAY = 1  # �o���E    ON_LIVE_START = 2  # ���C�u�J�n��
    ON_LIVE_SUCCESS = 3  # ���C�u?E����
    TURN_START = 4
    TURN_END = 5
    CONSTANT = 6  # ���E    ACTIVATED = 7  # �N��E    ON_LEAVES = 8  # ����E- when member leaves stage/is discarded


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
    OPPONENT_HAND = 9  # ����?E��D
    MEMBER_SELECT = 10  # Select manual target
    MEMBER_NAMED = 11  # Specific named member implementation


class EffectType(IntEnum):
    DRAW = 0
    ADD_BLADES = 1
    ADD_HEARTS = 2
    REDUCE_COST = 3
    LOOK_DECK = 4
    RECOVER_LIVE = 5  # Recover Live from discard
    BOOST_SCORE = 6
    RECOVER_MEMBER = 7  # Recover Member from discard
    BUFF_POWER = 8  # Generic power/heart buff
    IMMUNITY = 9  # Cannot be targeted/chosen
    MOVE_MEMBER = 10  # Move member to different area
    SWAP_CARDS = 11  # Swap cards between zones
    SEARCH_DECK = 12  # Search deck for specific card
    ENERGY_CHARGE = 13  # Add cards to energy zone
    SET_BLADES = 31  # Layer 4: Set blades to fixed value
    SET_HEARTS = 32  # Layer 4: Set hearts to fixed value
    FORMATION_CHANGE = 33  # Rule 11.10: Rearrange all members
    NEGATE_EFFECT = 14  # Cancel/negate an effect
    ORDER_DECK = 15  # Reorder cards in deck
    META_RULE = 16  # Rule clarification text (no effect)
    SELECT_MODE = 17  # Choose one of the following effects
    MOVE_TO_DECK = 18  # Move card to top/bottom of deck
    TAP_OPPONENT = 19  # Tap opponent's member
    PLACE_UNDER = 20  # Place card under member
    FLAVOR_ACTION = 99  # "Ask opponent what they like", etc.
    RESTRICTION = 21  # Restriction on actions (Cannot Live, etc)
    BATON_TOUCH_MOD = 22  # Modify baton touch rules (e.g. 2 members)
    SET_SCORE = 23  # Set score to fixed value
    SWAP_ZONE = 24  # Swap between zones (e.g. Hand <-> Live)
    TRANSFORM_COLOR = 25  # Change all colors of type X to Y
    REVEAL_CARDS = 26  # ��?E- reveal cards from zone
    LOOK_AND_CHOOSE = 27  # ����A���̒����� - look at cards, choose from them
    CHEER_REVEAL = 28  # �G�[���ɂ���?E- cards revealed via cheer mechanic
    ACTIVATE_MEMBER = 29  # �A�N�`E??�u�ɂ��� - untap/make active a member
    ADD_TO_HAND = 30  # ��D�ɉ����� - add card to hand (from any zone)
    COLOR_SELECT = 31  # Specify a heart color
    REPLACE_EFFECT = 34  # Replacement effect (�����)
    TRIGGER_REMOTE = 35  # Trigger ability from another zone (Cluster 5)
    REDUCE_HEART_REQ = 36  # Need hearts reduced


class ConditionType(IntEnum):
    NONE = 0
    TURN_1 = 1  # Turn == 1
    HAS_MEMBER = 2  # Specific member on stage
    HAS_COLOR = 3  # Specific color on stage
    COUNT_STAGE = 4  # Count members >= X
    COUNT_HAND = 5
    COUNT_DISCARD = 6
    IS_CENTER = 7
    LIFE_LEAD = 8
    COUNT_GROUP = 9  # "3+ Aqours members"
    GROUP_FILTER = 10  # Filter by group name
    OPPONENT_HAS = 11  # Opponent has X
    SELF_IS_GROUP = 12  # This card is from group X
    MODAL_ANSWER = 13  # Choice/Answer branch (e.g. LL-PR-004-PR)
    COUNT_ENERGY = 14  # �G�l���M�[��X���Ȓ�E    HAS_LIVE_CARD = 15  # ���C�u�J�[�h��������E    COST_CHECK = 16  # �R�X�g��X�Ȓ�E�Ȓ�E    RARITY_CHECK = 17  # Rarity filter
    HAND_HAS_NO_LIVE = 18  # Hand contains no live cards (usually paired with reveal cost)
    COUNT_SUCCESS_LIVE = 19  # �������C�u�J�[�h�u�����X���Ȓ�E    OPPONENT_HAND_DIFF = 20  # Opponent has more/less/diff cards in hand


@dataclass
class Condition:
    type: ConditionType
    params: Dict[str, Any] = field(default_factory=dict)
    is_negated: bool = False  # "If NOT X" / "Except X"


@dataclass
class Effect:
    effect_type: EffectType
    value: int = 0
    target: TargetType = TargetType.SELF
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False  # ?E?�Ă��悟E

class AbilityCostType(IntEnum):
    NONE = 0
    ENERGY = 1
    TAP_SELF = 2  # �E�F�C�g�ɂ���
    DISCARD_HAND = 3  # ��D���̂Ă�E    RETURN_HAND = 4  # ��D�ɖ߂�E(Self bounce)
    SACRIFICE_SELF = 5  # ��?E�����o?E���T�����ɒu��E    REVEAL_HAND_ALL = 6  # ��D�����ׂČ��J����E    SACRIFICE_UNDER = 7  # ���ɒu����Ă�E??�J�[�h���T�����ɒu��E    DISCARD_ENERGY = 8  # �G�l���M�[���T�����ɒu��E

@dataclass
class Cost:
    type: AbilityCostType
    value: int = 0
    params: Dict[str, Any] = field(default_factory=dict)
    is_optional: bool = False


@dataclass
class Ability:
    raw_text: str
    trigger: TriggerType
    effects: List[Effect]
    conditions: List[Condition] = field(default_factory=list)
    costs: List[Cost] = field(default_factory=list)
    modal_options: List[List[Effect]] = field(default_factory=list)  # For SELECT_MODE
    is_once_per_turn: bool = False

    def __str__(self):
        c_str = f" [Cond:{len(self.conditions)}]" if self.conditions else ""
        cost_str = f" [Cost:{len(self.costs)}]" if self.costs else ""
        return f"[{self.trigger.name}]{c_str}{cost_str} {self.raw_text[:30]}..."
