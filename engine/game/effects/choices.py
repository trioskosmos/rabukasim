from typing import Any, Dict


def normalize_choice_metadata(params: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure choice metadata has the fields downstream code expects."""
    choice_metadata = params.copy()
    choice_metadata.setdefault("source_card_id", -1)
    choice_metadata.setdefault("step_progress", "?")
    return choice_metadata


def is_cost_payment_choice(game: Any, choice_type: str, params: Dict[str, Any]) -> bool:
    """Return True when the choice is part of a pending cost payment flow."""
    if params.get("reason") == "cost":
        return True
    if not getattr(game, "pending_activation", None):
        return False
    return choice_type in {
        "TARGET_HAND",
        "DISCARD_SELECT",
        "TARGET_MEMBER_SLOT",
        "TARGET_MEMBER",
        "TARGET_LIVE",
        "TARGET_DISCARD",
        "TARGET_DECK",
        "TARGET_REMOVED",
        "TARGET_SUCCESS_LIVES",
        "TARGET_ENERGY_ZONE",
        "TARGET_ENERGY_DECK",
        "PAY_COST_OPTIONAL",
    }


def store_choice_answer(game: Any, action: int) -> None:
    """Persist the last answer for MODAL_ANSWER conditions."""
    if 580 <= action < 586:
        game.last_choice_answer = action - 580
    elif 800 <= action < 810:
        game.last_choice_answer = action - 800
    else:
        game.last_choice_answer = action

