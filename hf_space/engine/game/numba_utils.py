"""
Numba Utils for Love Live Card Game
JIT-compiled functions for high-performance game logic.
"""

try:
    from numba import njit

    JIT_AVAILABLE = True
except ImportError:
    # Fallback to python decorator if numba is missing (for safety)
    JIT_AVAILABLE = False

    def njit(func):
        return func


import numpy as np


@njit
def calc_main_phase_masks(
    hand: np.ndarray,
    stage: np.ndarray,
    available_energy: int,
    total_reduction: int,
    baton_touch_allowed: bool,
    members_played_this_turn: np.ndarray,
    member_costs: np.ndarray,  # Direct lookup array: cost = member_costs[card_id]
    mask: np.ndarray,
) -> None:
    """
    JIT-compiled Main Phase legal action calculation.
    """
    # Iterate through hand to find playable members
    hand_len = len(hand)
    for i in range(hand_len):
        card_id = hand[i]

        # Check if valid card ID for array lookup
        if card_id < 0 or card_id >= len(member_costs):
            continue

        base_cost = member_costs[card_id]
        if base_cost == -1:  # Not a member
            continue

        # Check each of the 3 stage areas
        for area in range(3):
            if members_played_this_turn[area]:
                continue

            active_cost = base_cost - total_reduction
            if active_cost < 0:
                active_cost = 0

            # Baton Touch Rule
            stage_card_id = stage[area]
            if baton_touch_allowed and stage_card_id != -1:
                if stage_card_id < len(member_costs):
                    existing_cost = member_costs[stage_card_id]
                    if existing_cost != -1:
                        active_cost = active_cost - existing_cost
                        if active_cost < 0:
                            active_cost = 0

            # Check affordability
            if active_cost <= available_energy:
                action_idx = 1 + (i * 3) + area
                if action_idx < 1000:
                    mask[action_idx] = 1
