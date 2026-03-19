from __future__ import annotations

from typing import Dict


def resolve_play_member_source(name_up: str, params: Dict[str, object], p: str, full_text: str) -> str:
    is_from_discard = (
        params.get("zone") == "DISCARD"
        or "DISCARD" in p.upper()
        or "(IN DISCARD)" in full_text.upper()
        or "TRIGGER: ACTIVATED_FROM_DISCARD" in full_text.upper()
    )
    if is_from_discard:
        return "PLAY_MEMBER_FROM_DISCARD"
    return "PLAY_MEMBER_FROM_HAND"