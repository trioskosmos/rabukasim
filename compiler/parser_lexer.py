# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class StructuredEffect:
    """Represents a structurally parsed effect before type resolution."""

    name: str = ""
    value: str = ""
    params: Dict[str, Any] = field(default_factory=dict)
    target: str = ""
    raw: str = ""

    def __repr__(self):
        return (
            f"StructuredEffect(name={self.name!r}, value={self.value!r}, params={self.params}, target={self.target!r})"
        )


class StructuralLexer:
    """Balanced-brace scanner for pseudocode parsing."""

    PAREN_OPEN = "("
    PAREN_CLOSE = ")"
    BRACE_OPEN = "{"
    BRACE_CLOSE = "}"

    @staticmethod
    def extract_balanced(text: str, start_pos: int, open_char: str, close_char: str) -> Tuple[str, int]:
        if start_pos >= len(text) or text[start_pos] != open_char:
            return "", start_pos

        depth = 1
        pos = start_pos + 1
        content_start = pos

        while pos < len(text) and depth > 0:
            char = text[pos]
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
            elif char == '"':
                pos += 1
                while pos < len(text) and text[pos] != '"':
                    if text[pos] == "\\" and pos + 1 < len(text):
                        pos += 1
                    pos += 1
            elif char == "'":
                pos += 1
                while pos < len(text) and text[pos] != "'":
                    if text[pos] == "\\" and pos + 1 < len(text):
                        pos += 1
                    pos += 1
            pos += 1

        if depth == 0:
            return text[content_start : pos - 1], pos
        return text[content_start:], pos

    @classmethod
    def parse_effect(cls, text: str) -> StructuredEffect:
        result = StructuredEffect(raw=text)
        text = text.strip()

        paren_pos = cls._find_delimiter(text, cls.PAREN_OPEN)
        if paren_pos != -1:
            result.name = text[:paren_pos].strip()
            value_content, end_pos = cls.extract_balanced(text, paren_pos, cls.PAREN_OPEN, cls.PAREN_CLOSE)
            result.value = value_content.strip()
            remaining = text[end_pos:].strip()
        else:
            remaining = text
            result.name = ""

        brace_pos = cls._find_delimiter(remaining, cls.BRACE_OPEN)
        if brace_pos != -1:
            if not result.name:
                result.name = remaining[:brace_pos].strip()
            params_content, end_pos = cls.extract_balanced(remaining, brace_pos, cls.BRACE_OPEN, cls.BRACE_CLOSE)
            result.params = cls._parse_params_content(params_content)
            remaining = remaining[end_pos:].strip()
        elif not result.name:
            arrow_pos = remaining.find("->")
            if arrow_pos != -1:
                result.name = remaining[:arrow_pos].strip()
                remaining = remaining[arrow_pos:].strip()
            else:
                result.name = remaining.strip()
                remaining = ""

        arrow_pos = remaining.find("->")
        if arrow_pos != -1:
            target_part = remaining[arrow_pos + 2 :].strip()
            target_parts = target_part.split()
            if target_parts:
                result.target = target_parts[0].strip(",")
            if arrow_pos > 0 and not result.name:
                result.name = remaining[:arrow_pos].strip()

        result.name = result.name.strip(" ,;")
        return result

    @classmethod
    def _find_delimiter(cls, text: str, delimiter: str) -> int:
        in_double_quote = False
        in_single_quote = False

        for i, char in enumerate(text):
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == delimiter and not in_double_quote and not in_single_quote:
                return i

        return -1

    @classmethod
    def _parse_params_content(cls, content: str) -> Dict[str, Any]:
        params: Dict[str, Any] = {}
        if not content.strip():
            return params

        parts = []
        current = ""
        depth = 0
        in_double_quote = False
        in_single_quote = False

        for char in content:
            if char == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
            elif char == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
            elif char == "{" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == "}" and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == "," and not in_double_quote and not in_single_quote and depth == 0:
                parts.append(current.strip())
                current = ""
                continue
            current += char

        if current.strip():
            parts.append(current.strip())

        for part in parts:
            if "=" in part:
                eq_pos = part.index("=")
                key = part[:eq_pos].strip().upper()
                val: Any = part[eq_pos + 1 :].strip()

                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]

                if isinstance(val, str) and val.isdigit():
                    val = int(val)
                elif isinstance(val, str) and val.upper() == "TRUE":
                    val = True
                elif isinstance(val, str) and val.upper() == "FALSE":
                    val = False

                params[key] = val

        return params

    @classmethod
    def split_effects(cls, text: str) -> List[str]:
        return cls.split_respecting_nesting(text, delimiter=";")

    @staticmethod
    def split_respecting_nesting(
        text: str, delimiter: str = ";", extra_delimiters: Optional[List[str]] = None
    ) -> List[str]:
        parts = []
        current = ""
        depth = 0
        in_double_quote = False
        in_single_quote = False
        all_delimiters = [delimiter] + (extra_delimiters or [])
        i = 0

        while i < len(text):
            char = text[i]

            if char == '"':
                in_double_quote = not in_double_quote
            elif char == "'":
                in_single_quote = not in_single_quote
            elif char == "{" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == "}" and not in_double_quote and not in_single_quote:
                depth -= 1
            elif char == "(" and not in_double_quote and not in_single_quote:
                depth += 1
            elif char == ")" and not in_double_quote and not in_single_quote:
                depth -= 1

            if depth == 0 and not in_double_quote and not in_single_quote:
                matched = False
                for delim in all_delimiters:
                    if text[i : i + len(delim)] == delim:
                        if current.strip():
                            parts.append(current.strip())
                        current = ""
                        i += len(delim)
                        matched = True
                        break
                if matched:
                    continue

            current += char
            i += 1

        if current.strip():
            parts.append(current.strip())

        return parts


__all__ = ["StructuredEffect", "StructuralLexer"]