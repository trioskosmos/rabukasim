"""Legacy compatibility wrapper around the parser v2 implementation.

The newer parser lives in :mod:`compiler.parser_v2`; this module remains as a
stable import surface for older callers that still reference
``compiler.parser``.
"""

from .parser_v2 import AbilityParserV2
from .parser_v2 import parse_ability_text as _parse_ability_text

parse_ability_text = _parse_ability_text

__all__ = ["AbilityParser", "AbilityParserV2", "parse_ability_text"]


class AbilityParser(AbilityParserV2):
    @staticmethod
    def parse_ability_text(text: str):
        return _parse_ability_text(text)
