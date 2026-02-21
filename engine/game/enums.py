from enum import IntEnum


class Phase(IntEnum):
    """Game phases within a turn (Rule 7).

    Flow: MULLIGAN_P1 -> MULLIGAN_P2 -> ACTIVE -> ENERGY -> DRAW -> MAIN
          -> LIVE_SET -> PERFORMANCE_P1 -> PERFORMANCE_P2 -> LIVE_RESULT
          -> ACTIVE (next turn)

    Note: SETUP (-2) is reserved for potential future use (pregame setup).
    Games currently start directly at MULLIGAN_P1.
    """

    SETUP = -4
    RPS = -3
    TurnChoice = -2
    MULLIGAN_P1 = -1
    MULLIGAN_P2 = 0
    ACTIVE = 1
    ENERGY = 2
    DRAW = 3
    MAIN = 4
    LIVE_SET = 5
    PERFORMANCE_P1 = 6
    PERFORMANCE_P2 = 7
    LIVE_RESULT = 8
    TERMINAL = 9
    RESPONSE = 10
