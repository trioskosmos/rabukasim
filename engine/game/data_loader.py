import json
import os
from typing import Any, Dict, Tuple

from pydantic import TypeAdapter

from engine.models.card import EnergyCard, LiveCard, MemberCard


class CardDataLoader:
    def __init__(self, json_path: str):
        self.json_path = json_path

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

            # --- HOTFIXES REMOVED (Parser is now accurate) ---
            for l in lives.values():
                pass

        else:
            # Legacy raw format
            # Since we removed runtime parsing from the engine to separate concerns,
            # we cannot load raw cards anymore.
            raise RuntimeError(
                "Legacy cards.json format detected. Runtime parsing is disabled. "
                "Please run 'uv run compiler/main.py' to generate 'data/cards_compiled.json'."
            )

        return members, lives, energy
