"""Pattern registry for managing and matching patterns."""

from typing import Any, Dict, List, Match, Optional, Tuple

from .base import Pattern, PatternPhase


class PatternRegistry:
    """Central registry for all parsing patterns.

    Patterns are organized by phase and sorted by priority.
    Lower priority number = higher precedence.
    """

    def __init__(self):
        self._patterns: Dict[PatternPhase, List[Pattern]] = {phase: [] for phase in PatternPhase}
        self._frozen = False

    def register(self, pattern: Pattern) -> "PatternRegistry":
        """Register a pattern. Returns self for chaining."""
        if self._frozen:
            raise RuntimeError("Cannot register patterns after registry is frozen")
        self._patterns[pattern.phase].append(pattern)
        return self

    def register_all(self, patterns: List[Pattern]) -> "PatternRegistry":
        """Register multiple patterns. Returns self for chaining."""
        for p in patterns:
            self.register(p)
        return self

    def freeze(self) -> "PatternRegistry":
        """Freeze the registry and sort patterns by priority."""
        for phase in PatternPhase:
            self._patterns[phase].sort(key=lambda p: p.priority)
        self._frozen = True
        return self

    def match_all(
        self, text: str, phase: PatternPhase, context: Optional[str] = None
    ) -> List[Tuple[Pattern, Match, Dict[str, Any]]]:
        """Find all matching patterns for a phase.

        Args:
            text: Text to match against
            phase: Which parsing phase to match
            context: Full sentence context for requires/excludes

        Returns:
            List of (pattern, match, extracted_data) tuples
        """
        results = []
        working_text = text

        for pattern in self._patterns[phase]:
            # Loop to find all matches for this pattern
            while True:
                # Always check against original context but match against working_text
                m = pattern.matches(working_text, context or text)
                if not m:
                    break

                data = pattern.extract(working_text, m)
                results.append((pattern, m, data))

                # If pattern consumes, mask out the matched text
                if pattern.consumes:
                    start, end = m.start(), m.end()
                    working_text = working_text[:start] + " " * (end - start) + working_text[end:]
                    # Continue looking for more matches of this pattern
                    continue

                # If pattern doesn't consume, we stop after first match to prevent infinite loop
                break

            if pattern.exclusive and any(r[0] == pattern for r in results):
                break

        # Sort results by match position to maintain text order
        results.sort(key=lambda x: x[1].start())
        return results

    def match_first(
        self, text: str, phase: PatternPhase, context: Optional[str] = None
    ) -> Optional[Tuple[Pattern, Match, Dict[str, Any]]]:
        """Find the first (highest priority) matching pattern.

        Returns:
            (pattern, match, extracted_data) tuple or None
        """
        for pattern in self._patterns[phase]:
            if m := pattern.matches(text, context):
                data = pattern.extract(text, m)
                return (pattern, m, data)
        return None

    def get_patterns(self, phase: PatternPhase) -> List[Pattern]:
        """Get all patterns for a phase (for debugging/testing)."""
        return list(self._patterns[phase])

    def stats(self) -> Dict[str, int]:
        """Get pattern counts per phase."""
        return {phase.name: len(patterns) for phase, patterns in self._patterns.items()}


# Global registry instance
_global_registry: Optional[PatternRegistry] = None


def get_registry() -> PatternRegistry:
    """Get the global pattern registry, creating if needed."""
    global _global_registry
    if _global_registry is None:
        _global_registry = PatternRegistry()
        _load_all_patterns(_global_registry)
        _global_registry.freeze()
    return _global_registry


def _load_all_patterns(registry: PatternRegistry):
    """Load all patterns from pattern definition modules."""
    from .conditions import CONDITION_PATTERNS
    from .effects import EFFECT_PATTERNS
    from .modifiers import MODIFIER_PATTERNS
    from .triggers import TRIGGER_PATTERNS

    registry.register_all(TRIGGER_PATTERNS)
    registry.register_all(CONDITION_PATTERNS)
    registry.register_all(EFFECT_PATTERNS)
    registry.register_all(MODIFIER_PATTERNS)
