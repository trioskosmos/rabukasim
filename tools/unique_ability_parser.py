"""Standalone parser for unique ability text in the authored frame index.

This module is intentionally separate from runtime wiring. It reads the
normalized ability-frame source, extracts a structured view of the Japanese
ability text, and reports likely mismatches between text and frame metadata.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any

from tools.frame_codec import load_json


TRIGGER_HINTS = {
    "登場": "ON_PLAY",
    "起動": "ACTIVATED",
    "ライブ開始時": "ON_LIVE_START",
    "ライブ成功時": "ON_LIVE_SUCCESS",
    "ターンの始めに": "TURN_START",
    "ターンの終わりに": "TURN_END",
    "常時": "CONSTANT",
    "控え室に置かれたとき": "ON_LEAVES",
    "ポジションチェンジしたとき": "ON_POSITION_CHANGE",
}

OPTIONAL_RE = re.compile(r"(もよい|でもよい|してもよい|選んでもよい)")
CHOICE_RE = re.compile(r"(以下から\d+つを選ぶ|\d+つを選ぶ|好きな枚数|まで選ぶ|まで見る|まで置く)")
TURN_LIMIT_RE = re.compile(r"(?:\{\{turn([12])\.png\|ターン([12])回\}\}|ターン([12])回)")


@dataclass
class AbilityClause:
    text: str
    kind: str
    optional: bool = False
    is_choice: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class ParsedAbility:
    signature: str
    signature_hash: str
    card_no: str
    card_name: str
    ability_index: int
    trigger: str
    raw_text: str
    clauses: list[AbilityClause] = field(default_factory=list)
    has_optional_text: bool = False
    has_optional_frames: bool = False
    has_choice_text: bool = False
    has_turn_limit_text: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class ParseReport:
    source_entry_count: int
    abilities: list[ParsedAbility]
    issues: list[str]

    def summary(self) -> dict[str, int]:
        return {
            "source_entry_count": self.source_entry_count,
            "ability_count": len(self.abilities),
            "unique_ability_count": len(self.abilities),
            "issue_count": len(self.issues),
            "optional_mismatch_count": sum(
                1 for ability in self.abilities if ability.has_optional_text != ability.has_optional_frames
            ),
            "choice_text_count": sum(1 for ability in self.abilities if ability.has_choice_text),
            "turn_limit_text_count": sum(1 for ability in self.abilities if ability.has_turn_limit_text),
        }


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _frame_is_optional(frame: dict[str, Any]) -> bool:
    if bool(frame.get("is_optional", False)) or bool(frame.get("optional", False)):
        return True

    attr = frame.get("attr")
    if isinstance(attr, dict) and bool(attr.get("is_optional", False)):
        return True

    filter_data = frame.get("filter")
    if isinstance(filter_data, dict) and bool(filter_data.get("is_optional", False)):
        return True

    options = frame.get("options")
    if isinstance(options, dict) and bool(options.get("optional", False)):
        return True

    return False


def _frame_has_choice(frame: dict[str, Any]) -> bool:
    opcode = str(frame.get("opcode", frame.get("op", ""))).upper()
    return opcode in {
        "SELECT_MODE",
        "SELECT_MEMBER",
        "SELECT_CARDS",
        "LOOK_AND_CHOOSE",
        "SELECT_PLAYER",
        "SELECT_LIVE",
        "OPPONENT_CHOOSE",
    }


def _trigger_from_text(text: str) -> str:
    for hint, trigger in TRIGGER_HINTS.items():
        if hint in text:
            return trigger
    if "{{kidou.png" in text:
        return "ACTIVATED"
    if "{{toujyou.png" in text:
        return "ON_PLAY"
    if "{{live_start.png" in text:
        return "ON_LIVE_START"
    if "{{jyouji.png" in text:
        return "CONSTANT"
    return "UNKNOWN"


def _split_clauses(text: str) -> list[str]:
    cleaned = _normalize_whitespace(text)
    if not cleaned:
        return []

    parts: list[str] = []
    for line in cleaned.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("・"):
            line = line[1:].strip()
        segments = [segment.strip() for segment in re.split(r"[。．]\s*", line) if segment.strip()]
        if not segments:
            segments = [line]
        parts.extend(segments)
    return parts


def _clause_kind(text: str) -> str:
    if "：" in text:
        return "cost_effect"
    if "以下から" in text or "選ぶ" in text:
        return "choice"
    if "控え室に置く" in text or "手札に加える" in text:
        return "resolution"
    return "statement"


def _card_ref_from_entry(entry: dict[str, Any]) -> tuple[str, str]:
    cards = entry.get("cards", [])
    if isinstance(cards, list) and cards:
        label = str(cards[0])
        if " | " in label:
            card_no, rest = label.split(" | ", 1)
            card_name = rest.split(" [", 1)[0].strip()
            return card_no.strip(), card_name
        return label.strip(), ""
    return "", ""


def _ability_label(ability: ParsedAbility) -> str:
    parts = []
    if ability.card_no:
        parts.append(ability.card_no)
    if ability.card_name:
        parts.append(ability.card_name)
    label = " | ".join(parts) if parts else (ability.signature or "unknown")
    return f"{label} (ab#{ability.ability_index})"


def _parse_ability_entry(entry: dict[str, Any]) -> ParsedAbility:
    raw_text = str(entry.get("primary_text_jp") or entry.get("source_text") or entry.get("raw_text") or "")
    clauses: list[AbilityClause] = []

    optional_text = False
    choice_text = False
    turn_limit_text = False

    for clause_text in _split_clauses(raw_text):
        clause_optional = bool(OPTIONAL_RE.search(clause_text))
        clause_choice = bool(CHOICE_RE.search(clause_text))
        clause_turn_limit = bool(TURN_LIMIT_RE.search(clause_text))

        optional_text = optional_text or clause_optional
        choice_text = choice_text or clause_choice
        turn_limit_text = turn_limit_text or clause_turn_limit

        notes: list[str] = []
        if clause_turn_limit:
            notes.append("turn_limit")
        if clause_optional:
            notes.append("optional")
        if clause_choice:
            notes.append("choice")

        clauses.append(
            AbilityClause(
                text=clause_text,
                kind=_clause_kind(clause_text),
                optional=clause_optional,
                is_choice=clause_choice,
                notes=notes,
            )
        )

    frames = entry.get("frames", [])
    has_optional_frames = any(isinstance(frame, dict) and _frame_is_optional(frame) for frame in frames)
    has_choice_frames = any(isinstance(frame, dict) and _frame_has_choice(frame) for frame in frames)

    issues: list[str] = []
    if optional_text != has_optional_frames:
        issues.append("optional_text_frame_mismatch")
    if choice_text and not has_choice_frames:
        issues.append("choice_text_without_choice_frame")
    if turn_limit_text and not bool(entry.get("is_once_per_turn", False)):
        issues.append("turn_limit_text_without_once_per_turn_flag")

    card_no, card_name = _card_ref_from_entry(entry)

    return ParsedAbility(
        signature=str(entry.get("signature", "")),
        signature_hash=str(entry.get("signature_hash", "")),
        card_no=card_no,
        card_name=card_name,
        ability_index=int(entry.get("ability_index", 0)),
        trigger=str(entry.get("trigger", _trigger_from_text(raw_text))),
        raw_text=raw_text,
        clauses=clauses,
        has_optional_text=optional_text,
        has_optional_frames=has_optional_frames,
        has_choice_text=choice_text,
        has_turn_limit_text=turn_limit_text,
        issues=issues,
    )


def parse_unique_abilities(payload: dict[str, Any]) -> ParseReport:
    abilities = payload.get("abilities", [])
    parsed: list[ParsedAbility] = []
    report_issues: list[str] = []
    seen_signatures: set[str] = set()

    if not isinstance(abilities, list):
        return ParseReport(source_entry_count=0, abilities=[], issues=["payload_missing_abilities_list"])

    for entry in abilities:
        if not isinstance(entry, dict):
            continue
        parsed_entry = _parse_ability_entry(entry)
        signature_key = parsed_entry.signature_hash or parsed_entry.signature
        if signature_key and signature_key in seen_signatures:
            continue
        if signature_key:
            seen_signatures.add(signature_key)
        parsed.append(parsed_entry)
        for issue in parsed_entry.issues:
            report_issues.append(f"{_ability_label(parsed_entry)} [{parsed_entry.signature or parsed_entry.signature_hash}]:{issue}")

    return ParseReport(source_entry_count=len(abilities), abilities=parsed, issues=report_issues)


def load_unique_ability_report(path: str | Path) -> ParseReport:
    payload = load_json(path)
    return parse_unique_abilities(payload)


def format_report(report: ParseReport, limit: int = 20) -> str:
    summary = report.summary()
    lines = [
        f"source_entries={summary['source_entry_count']}",
        f"abilities={summary['ability_count']}",
        f"issues={summary['issue_count']}",
        f"optional_mismatches={summary['optional_mismatch_count']}",
        f"choice_text={summary['choice_text_count']}",
        f"turn_limit_text={summary['turn_limit_text_count']}",
    ]

    for issue in report.issues[:limit]:
        lines.append(f"issue: {issue}")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Parse unique abilities from an authored frame index.")
    parser.add_argument("path", nargs="?", default="data/ability_frame_source.json")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    report = load_unique_ability_report(args.path)
    if args.json:
        print(
            json.dumps(
                {
                    "summary": report.summary(),
                    "issues": report.issues[: args.limit],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        print(format_report(report, limit=args.limit))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())