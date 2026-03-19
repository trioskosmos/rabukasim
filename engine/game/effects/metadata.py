from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from engine.models.ability import Ability


def resolve_source_metadata(
    game: Any, source_card_id: Optional[int], ability: "Ability", reason: str = "effect"
) -> Dict[str, Any]:
    """Helper to resolve standardized source metadata for UI/Logs."""
    if source_card_id is None:
        # Fallback if no specific source ID provided
        return {
            "source_card_id": -1,
            "source_img": "",
            "source_member": "Unknown Source",
            "source_ability": ability.raw_text,
            "step_progress": "?",
            "reason": reason,
        }

    # Try member DB
    if source_card_id in game.member_db:
        card = game.member_db[source_card_id]
        return {
            "source_card_id": source_card_id,
            "source_card_no": getattr(card, "card_no", "Unknown"),
            "source_img": getattr(card, "img_path", ""),
            "source_member": card.name,
            "source_ability": ability.raw_text,
            "step_progress": "?",
            "reason": reason,
        }

    # Try live DB
    if source_card_id in game.live_db:
        card = game.live_db[source_card_id]
        return {
            "source_card_id": source_card_id,
            "source_card_no": getattr(card, "card_no", "Unknown"),
            "source_img": getattr(card, "img_path", ""),
            "source_member": card.name,
            "source_ability": ability.raw_text,
            "step_progress": "?",
            "reason": reason,
        }

    return {
        "source_card_id": source_card_id,
        "source_img": "",
        "source_member": f"Card {source_card_id}",
        "source_ability": ability.raw_text,
        "step_progress": "?",
        "reason": reason,
    }

