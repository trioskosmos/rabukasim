from typing import Any, Dict


def normalize_choice_metadata(params: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure choice metadata has the fields downstream code expects."""
    choice_metadata = params.copy()
    choice_metadata.setdefault("source_card_id", -1)
    choice_metadata.setdefault("step_progress", "?")
    return choice_metadata


def queue_target_hand_choice(
    game: Any,
    choice_metadata: Dict[str, Any],
    effect: str,
    effect_description: str,
    params: Dict[str, Any],
    is_optional: bool = False,
) -> None:
    """Queue a hand-target choice with an explicit effect meaning."""
    game.pending_choices.append(
        (
            "TARGET_HAND",
            {
                **choice_metadata,
                "effect": effect,
                "effect_description": effect_description,
                "is_optional": is_optional,
                **params,
            },
        )
    )


def queue_select_from_list_choice(
    game: Any,
    choice_metadata: Dict[str, Any],
    cards: list,
    count: int,
    reason: str,
    effect_description: str,
    target_player_id: int,
    is_optional: bool = False,
    extra_params: Dict[str, Any] | None = None,
) -> None:
    """Queue a list-selection choice with explicit destination context."""
    payload = {
        **choice_metadata,
        "cards": cards,
        "count": count,
        "reason": reason,
        "effect_description": effect_description,
        "target_player_id": target_player_id,
        "is_optional": is_optional,
    }
    if extra_params:
        payload.update(extra_params)
    game.pending_choices.append(("SELECT_FROM_LIST", payload))


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

