"""Legacy compatibility shim for the old compiler entrypoint."""

from __future__ import annotations

from typing import Any, List


class AbilityCompiler:
    """Minimal compatibility wrapper used by the backend tests."""

    def compile_to_bytecode(self, ability: Any) -> List[int]:
        """Return existing bytecode if present, otherwise an empty sequence."""
        bytecode = getattr(ability, "bytecode", None)
        return list(bytecode) if isinstance(bytecode, list) else []

    def compile_to_frames(self, ability: Any) -> list:
        """Prefer authored frame_program instructions over bytecode compilation."""
        if hasattr(ability, "to_frame_program"):
            frames = ability.to_frame_program()
            if isinstance(frames, list) and frames:
                return frames
        if hasattr(ability, "frame_program") and isinstance(ability.frame_program, dict):
            frames = ability.frame_program.get("instructions")
            if isinstance(frames, list):
                return frames
        _ = self.compile_to_bytecode(ability)
        return []

