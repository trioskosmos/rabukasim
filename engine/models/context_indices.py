from enum import IntEnum


class ContextIndex(IntEnum):
    """
    Indices for the fixed-size NumPy context array (int32).
    Size should be enough to hold all standard context variables.
    Standard Size: 64 integers.
    """

    # Header / Meta
    TYPE = 0  # Context Type (Trigger, Effect, etc)
    PLAYER_ID = 1  # Owner/Active Player
    OPPONENT_ID = 2
    PHASE = 3
    TURN = 4

    # Source Info
    SOURCE_CARD_ID = 5
    SOURCE_ZONE = 6  # Zone Enum
    SOURCE_ZONE_IDX = 7
    SOURCE_TYPE = 8  # Member/Live

    # Target Info
    TARGET_CARD_ID = 10
    TARGET_ZONE = 11
    TARGET_ZONE_IDX = 12
    TARGET_PLAYER_ID = 13
    TARGET_COUNT = 14  # How many targets

    # Payload / Parameters
    VALUE = 20  # Generic Value (Amount, Score, etc)
    COST_PAID = 21  # Boolean/Chek
    ATTRIBUTE = 22  # Color/Attribute
    GROUP = 23  # Group Enum
    SUB_TYPE = 24  # Trigger Subtype / Effect Subtype

    # Mapped Params (Generic registers)
    PARAM_1 = 30
    PARAM_2 = 31
    PARAM_3 = 32
    PARAM_4 = 33

    # Flags (Bitmask)
    FLAGS = 50  # Optional, Negated, etc.

    # Execution State
    STEP_INDEX = 60
    TOTAL_STEPS = 61

    SIZE = 64
