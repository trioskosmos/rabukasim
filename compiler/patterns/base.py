"""Base pattern definitions for the ability parser."""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Match, Optional, Tuple


class PatternPhase(Enum):
    """Phases of parsing, executed in order."""

    TRIGGER = 1  # Determine when ability activates
    CONDITION = 2  # Extract gating conditions
    EFFECT = 3  # Extract effects/actions
    MODIFIER = 4  # Apply flags (optional, once per turn, duration)


@dataclass
class Pattern:
    """A declarative pattern definition for ability text parsing.

    Patterns are matched in priority order within each phase.
    Lower priority number = higher precedence.
    """

    name: str
    phase: PatternPhase
    priority: int = 100

    # Matching criteria (at least one must be specified)
    regex: Optional[str] = None  # Regex pattern to search for
    keywords: List[str] = field(default_factory=list)  # Must contain ALL keywords
    any_keywords: List[str] = field(default_factory=list)  # Must contain ANY keyword

    # Filter conditions
    requires: List[str] = field(default_factory=list)  # Context must contain ALL
    excludes: List[str] = field(default_factory=list)  # Context must NOT contain ANY
    look_ahead_excludes: List[str] = field(default_factory=list)  # Text after match must NOT contain

    # Behavior
    exclusive: bool = False  # If True, stops further matching in this phase
    consumes: bool = False  # If True, removes matched text from further processing

    # Output specification
    output_type: Optional[str] = None  # e.g., "TriggerType.ON_PLAY", "EffectType.DRAW"
    output_value: Optional[Any] = None  # Default value for effect
    output_params: Dict[str, Any] = field(default_factory=dict)  # Additional parameters

    # Custom extraction (for complex patterns)
    extractor: Optional[Callable[[str, Match], Dict[str, Any]]] = None

    def __post_init__(self):
        """Compile regex if provided."""
        self._compiled_regex = re.compile(self.regex) if self.regex else None

    def matches(self, text: str, context: Optional[str] = None) -> Optional[Match]:
        """Check if pattern matches the text.

        Args:
            text: The text to match against
            context: Full sentence context for requires/excludes checks

        Returns:
            Match object if pattern matches, None otherwise
        """
        ctx = context or text

        # Check requires
        if self.requires and not all(kw in ctx for kw in self.requires):
            return None

        # Check excludes
        if self.excludes and any(kw in ctx for kw in self.excludes):
            return None

        # Check keywords (must contain ALL)
        if self.keywords and not all(kw in text for kw in self.keywords):
            return None

        # Check any_keywords (must contain ANY)
        if self.any_keywords and not any(kw in text for kw in self.any_keywords):
            return None

        # Check regex
        if self._compiled_regex:
            m = self._compiled_regex.search(text)
            if m:
                # Check look-ahead excludes
                if self.look_ahead_excludes:
                    look_ahead = text[m.start() : m.start() + 20]
                    if any(kw in look_ahead for kw in self.look_ahead_excludes):
                        return None
                return m
            return None

        # If no regex but keywords matched, return a pseudo-match
        if self.keywords or self.any_keywords:
            # Find first keyword position
            for kw in self.keywords or self.any_keywords:
                if kw in text:
                    idx = text.find(kw)
                    # Create a fake match-like object
                    return _KeywordMatch(kw, idx)

        return None

    def extract(self, text: str, match: Match) -> Dict[str, Any]:
        """Extract structured data from a match.

        Returns dict with:
            - 'type': output_type if specified
            - 'value': extracted value or output_value
            - 'params': output_params merged with any extracted params
        """
        if self.extractor:
            return self.extractor(text, match)

        result = {}
        if self.output_type:
            result["type"] = self.output_type
        if self.output_value is not None:
            result["value"] = self.output_value
        if self.output_params:
            result["params"] = self.output_params.copy()

        # Try to extract numeric value from match groups
        if match.lastindex and match.lastindex >= 1:
            try:
                result["value"] = int(match.group(1))
            except (ValueError, TypeError):
                # Don't assign non-numeric strings to 'value' as it breaks bytecode compilation
                pass

        return result


class _KeywordMatch:
    """Fake match object for keyword-based patterns."""

    def __init__(self, keyword: str, start: int):
        self._keyword = keyword
        self._start = start
        self.lastindex = None

    def start(self) -> int:
        return self._start

    def end(self) -> int:
        return self._start + len(self._keyword)

    def span(self) -> Tuple[int, int]:
        return (self.start(), self.end())

    def group(self, n: int = 0) -> str:
        return self._keyword if n == 0 else ""

    def groups(self) -> Tuple:
        return ()
