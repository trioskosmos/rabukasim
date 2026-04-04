from __future__ import annotations

import argparse
import json
import re
from io import StringIO
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
CARDS_PATH = ROOT_DIR / "data" / "cards.json"
CONSOLIDATED_PATH = ROOT_DIR / "data" / "consolidated_abilities.json"

CARD_NO_RE = re.compile(r'^\s*"card_no":\s*"([^"]+)",\s*$')
BROKEN_NAME_RE = re.compile(r'^(\s*)"name":\s*"[^"]*,\s*$')
BROKEN_ENTRY_KEY_RE = re.compile(r'^(\s*)"(.*):\s*\{\s*$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair malformed card_ref name lines in consolidated_abilities.json"
    )
    parser.add_argument("--quiet", action="store_true", help="Only print final status")
    return parser.parse_args()


def load_card_names() -> dict[str, str]:
    with open(CARDS_PATH, "r", encoding="utf-8-sig") as handle:
        cards = json.load(handle)
    return {
        card_no: data.get("name", "")
        for card_no, data in cards.items()
        if isinstance(data, dict) and isinstance(data.get("name"), str)
    }


def detect_newline(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def encode_json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def sanitize_json_text(text: str) -> str:
    sanitized = StringIO()
    in_string = False
    escaped = False

    for ch in text:
        if in_string:
            if escaped:
                sanitized.write(ch)
                escaped = False
                continue

            if ch == "\\":
                sanitized.write(ch)
                escaped = True
            elif ch == '"':
                sanitized.write(ch)
                in_string = False
            elif ord(ch) < 0x20:
                sanitized.write(f"\\u{ord(ch):04x}")
            else:
                sanitized.write(ch)
        else:
            if ch == '"':
                sanitized.write(ch)
                in_string = True
            elif ord(ch) < 0x20 and ch not in "\n\r\t":
                continue
            else:
                sanitized.write(ch)

    return sanitized.getvalue()


def repair_text(text: str, card_names: dict[str, str]) -> tuple[str, int]:
    newline = detect_newline(text)
    lines = text.splitlines()
    repaired_lines: list[str] = []
    current_card_no: str | None = None
    repairs = 0

    for line in lines:
        card_match = CARD_NO_RE.match(line)
        if card_match:
            current_card_no = card_match.group(1)
            repaired_lines.append(line)
            continue

        if BROKEN_NAME_RE.match(line) and current_card_no:
            replacement_name = card_names.get(current_card_no)
            if replacement_name:
                indent = line[: len(line) - len(line.lstrip())]
                repaired_lines.append(f'{indent}"name": {encode_json_string(replacement_name)},')
                repairs += 1
                continue

        key_match = BROKEN_ENTRY_KEY_RE.match(line)
        if key_match and not line.rstrip().endswith('": {'):
            indent, key_text = key_match.groups()
            repaired_lines.append(f'{indent}"{key_text}": {{')
            repairs += 1
            continue

        repaired_lines.append(line)

    return newline.join(repaired_lines) + newline, repairs


def main() -> int:
    args = parse_args()
    card_names = load_card_names()
    raw_bytes = CONSOLIDATED_PATH.read_bytes()
    has_bom = raw_bytes.startswith(b"\xef\xbb\xbf")
    text = raw_bytes.decode("utf-8-sig")

    repaired_text, repairs = repair_text(text, card_names)
    repaired_text = sanitize_json_text(repaired_text)

    try:
        json.loads(repaired_text)
    except json.JSONDecodeError as error:
        print(
            f"ERROR: consolidated_abilities.json is still invalid after {repairs} repair(s): "
            f"line {error.lineno} column {error.colno}: {error.msg}"
        )
        return 1

    if repairs > 0:
        encoded = repaired_text.encode("utf-8")
        if has_bom:
            encoded = b"\xef\xbb\xbf" + encoded
        CONSOLIDATED_PATH.write_bytes(encoded)

    if args.quiet:
        print(f"repaired_card_ref_names={repairs}")
    else:
        if repairs > 0:
            print(f"[repair] Fixed {repairs} malformed card_ref name line(s).")
        else:
            print("[repair] consolidated_abilities.json card_ref names are already valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())