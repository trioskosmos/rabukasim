# -*- coding: utf-8 -*-
import re

from .aliases import (
    CONDITION_ALIASES,
    EFFECT_ALIASES,
    EFFECT_ALIASES_WITH_PARAMS,
    IGNORED_CONDITIONS,
    KEYWORD_CONDITIONS,
    MAX_SELECT_ALL,
    TRIGGER_ALIASES,
)

_RE_CONDITION_NAME = re.compile(r"(\w+)(?:\s*\{(.*)\})?")
_RE_CONDITION_PARENS = re.compile(r"\((.*?)\)")
_RE_CONDITION_EQUALS = re.compile(r"=\s*[\"']?(.*?)[\"']?$")

_RE_EFFECT_FULL = re.compile(r"^([\w_]+)(?:\((.*?)\))?\s*(?:(\{.*?\})\s*)?(?:->\s*([\w, _]+))?(.*)$")
_RE_EFFECT_COMPACT = re.compile(r"(\w+)\((.*?)\)\s*->\s*(\w+)(.*)")
_RE_GRANT_ABILITY = re.compile(r"GRANT_ABILITY\((.*?),\s*\"(.*?)\"\)")

_RE_COST_FORMAT = re.compile(r"(\w+)(?:\((.*?)\))?(.*)")

_RE_TRIGGER_KEYWORD = re.compile(r"TRIGGER:", re.I)
_RE_TRIGGER_PARENS = re.compile(r"\(.*?\)")

_RE_COST_GE = re.compile(r"COST_GE=(\d+)")
_RE_COST_COMPARISON = re.compile(r"COST_(GE|LE|GT|LT|EQ)=(\d+)")

__all__ = [
    "CONDITION_ALIASES",
    "EFFECT_ALIASES",
    "EFFECT_ALIASES_WITH_PARAMS",
    "IGNORED_CONDITIONS",
    "KEYWORD_CONDITIONS",
    "MAX_SELECT_ALL",
    "TRIGGER_ALIASES",
    "_RE_CONDITION_EQUALS",
    "_RE_CONDITION_NAME",
    "_RE_CONDITION_PARENS",
    "_RE_COST_COMPARISON",
    "_RE_COST_FORMAT",
    "_RE_COST_GE",
    "_RE_EFFECT_COMPACT",
    "_RE_EFFECT_FULL",
    "_RE_GRANT_ABILITY",
    "_RE_TRIGGER_KEYWORD",
    "_RE_TRIGGER_PARENS",
]