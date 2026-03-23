from typing import TYPE_CHECKING, Any, Dict, Optional

if TYPE_CHECKING:
    from engine.models.ability import Ability


def _describe_ability(ability: "Ability") -> str:
    sparse = getattr(ability, "frame_program", None) or getattr(ability, "sparse_frame_index", None)
    if isinstance(sparse, dict):
        pseudocode = sparse.get("pseudocode")
        if pseudocode:
            return str(pseudocode)

        frames = sparse.get("frames")
        if isinstance(frames, list) and frames:
            parts = []
            for frame in frames[:4]:
                if isinstance(frame, dict):
                    decoded = frame.get("decoded") or frame.get("opcode")
                    if decoded:
                        parts.append(str(decoded))
            if parts:
                return " | ".join(parts)

    semantic = getattr(ability, "semantic_form", None)
    if isinstance(semantic, dict):
        text = semantic.get("text") or semantic.get("pseudocode")
        if text:
            return str(text)

    return getattr(ability, "raw_text", "")


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
            "source_ability": _describe_ability(ability),
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
            "source_ability": _describe_ability(ability),
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
            "source_ability": _describe_ability(ability),
            "step_progress": "?",
            "reason": reason,
        }

    return {
        "source_card_id": source_card_id,
        "source_img": "",
        "source_member": f"Card {source_card_id}",
        "source_ability": _describe_ability(ability),
        "step_progress": "?",
        "reason": reason,
    }

