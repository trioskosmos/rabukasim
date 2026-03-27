import copy
import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

from pydantic import TypeAdapter

from engine.models.ability import AbilityCostType, Cost
from engine.models.card import EnergyCard, LiveCard, MemberCard

import re as _re

_SPARSE_INDEX_CACHE: Dict[str, Dict[str, Any]] | None = None
_CARD_REF_RE = _re.compile(
    r"^(?P<card_no>[^|]+?)\s*\|.*?\(ab#(?P<idx>\d+)(?:[\s\u3000)]|$)"
)


def _load_sparse_ability_index() -> Dict[str, Dict[str, Any]]:
    """Load ability_frame_index.json keyed by 'card_no#ab_idx'.

    This matches the lookup format used in card_db.rs and is robust to the
    sparse index not carrying a top-level ``bytecode`` field per entry.
    """
    global _SPARSE_INDEX_CACHE
    if _SPARSE_INDEX_CACHE is not None:
        return _SPARSE_INDEX_CACHE

    index_path = Path(os.getcwd()) / "data" / "ability_frame_index.json"
    cache: Dict[str, Dict[str, Any]] = {}
    if index_path.exists():
        try:
            with index_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            for entry in payload.get("abilities", []):
                for card_ref in entry.get("cards", []):
                    if isinstance(card_ref, dict):
                        card_no = str(card_ref.get("card_no", "")).strip()
                        ab_idx = card_ref.get("ability_index", card_ref.get("ab_idx"))
                        if card_no and ab_idx is not None:
                            cache[f"{card_no}#{ab_idx}"] = entry
                    elif isinstance(card_ref, str):
                        m = _CARD_REF_RE.match(card_ref.strip())
                        if m:
                            cache[f"{m.group('card_no').strip()}#{m.group('idx')}"] = entry
        except Exception:
            cache = {}

    _SPARSE_INDEX_CACHE = cache
    return cache


class CardDataLoader:
    def __init__(self, json_path: str):
        self.json_path = json_path

    def _repair_stale_optional_energy_deck_costs(self, cards: Dict[int, Any]) -> None:
        """Normalize legacy compiled abilities that lost PLACE_ENERGY_WAIT costs.

        Some older compiled card files encoded
        `COST: PLACE_ENERGY_WAIT(1) (Optional)` as an empty-cost ability with only
        the follow-up effect preserved. Rehydrate those into a real deck-to-energy
        cost so the runtime prompt and resolution path stay consistent.
        """

        for card in cards.values():
            for ability in getattr(card, "abilities", []):
                text = f"{getattr(ability, 'pseudocode', '')}\n{getattr(ability, 'raw_text', '')}".upper()
                if "COST: PLACE_ENERGY_WAIT" not in text:
                    continue
                if getattr(ability, "costs", None):
                    continue

                is_optional = "(OPTIONAL)" in text
                ability.costs = [
                    Cost(
                        AbilityCostType.PLACE_ENERGY_FROM_DECK,
                        1,
                        params={"wait": True},
                        is_optional=is_optional,
                    )
                ]
                semantic = getattr(ability, "semantic_form", None)
                if isinstance(semantic, dict):
                    semantic["costs"] = [
                        {
                            "type": "PLACE_ENERGY_FROM_DECK",
                            "value": 1,
                            "target": "PLAYER",
                            "params": {"wait": True},
                            "optional": is_optional,
                        }
                    ]

    def _attach_sparse_frame_index(self, cards: Dict[int, Any]) -> None:
        sparse_index = _load_sparse_ability_index()
        if not sparse_index:
            return

        for card in cards.values():
            card_no = getattr(card, "card_no", "")
            for ab_idx, ability in enumerate(getattr(card, "abilities", [])):
                key = f"{card_no}#{ab_idx}"
                entry = sparse_index.get(key)
                if entry is not None:
                    ability.sparse_frame_index = entry
                    instructions = entry.get("instructions", entry.get("frames", [])) if isinstance(entry, dict) else []
                    if isinstance(instructions, list) and instructions and not getattr(ability, "frame_program", None):
                        ability.frame_program = {"instructions": copy.deepcopy(instructions)}

    def load(self) -> Tuple[Dict[int, MemberCard], Dict[int, LiveCard], Dict[int, Any]]:
        # Auto-detect compiled file
        target_path = self.json_path
        if target_path.endswith("cards.json"):
            # Check for compiled file in the same directory, or in data/
            compiled_path = target_path.replace("cards.json", "cards_compiled.json")
            if os.path.exists(compiled_path):
                target_path = compiled_path
            else:
                root_path = os.path.join(os.getcwd(), "data", "cards_compiled.json")
                if os.path.exists(root_path):
                    target_path = root_path

        # Fallback to relative path search if absolute fails (common in tests)
        if not os.path.exists(target_path):
            # Try assuming path is relative to project root
            # But we don't know project root easily.
            pass

        # print(f"Loading card data from {target_path}...")
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        members = {}
        lives = {}
        energy = {}

        if "member_db" in data:
            # Compiled format (v1.0)
            m_adapter = TypeAdapter(MemberCard)
            l_adapter = TypeAdapter(LiveCard)
            e_adapter = TypeAdapter(EnergyCard)

            for k, v in data["member_db"].items():
                members[int(k)] = m_adapter.validate_python(v)

            for k, v in data["live_db"].items():
                # print(f"Loading live {k}")
                lives[int(k)] = l_adapter.validate_python(v)
            # print(f"DEBUG: Internal live_db keys: {len(data['live_db'])}, loaded: {len(lives)}")

            for k, v in data["energy_db"].items():
                energy[int(k)] = e_adapter.validate_python(v)

            self._repair_stale_optional_energy_deck_costs(lives)
            self._repair_stale_optional_energy_deck_costs(members)
            self._attach_sparse_frame_index(members)
            self._attach_sparse_frame_index(lives)

        else:
            # Legacy raw format
            # Since we removed runtime parsing from the engine to separate concerns,
            # we cannot load raw cards anymore.
            raise RuntimeError(
                "Legacy cards.json format detected. Runtime parsing is disabled. "
                "Please run 'uv run compiler/main.py' to generate 'data/cards_compiled.json'."
            )

        return members, lives, energy
