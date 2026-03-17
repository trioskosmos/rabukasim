from .parser_v2 import AbilityParserV2
from .parser_v2 import parse_ability_text as _parse_ability_text


class AbilityParser(AbilityParserV2):
    @staticmethod
    def parse_ability_text(text: str):
        return _parse_ability_text(text)
