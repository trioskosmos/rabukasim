# -*- coding: utf-8 -*-
from typing import List

from engine.models.ability import Ability


def parse_ability_text(text: str) -> List[Ability]:
    from .parser_v2 import AbilityParserV2

    parser = AbilityParserV2()
    return parser.parse(text)


__all__ = ["parse_ability_text"]