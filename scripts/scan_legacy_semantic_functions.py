#!/usr/bin/env python3
"""Scan Rust logic code for functions still recovering semantics from packed fields."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


FUNCTION_RE = re.compile(
    r"^(?P<indent>\s*)(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*\((?P<params>[^)]*)\)",
    re.MULTILINE,
)

REASON_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("raw_attr_param", re.compile(r"\braw_attr\b")),
    ("raw_slot_param", re.compile(r"\braw_slot\b")),
    ("raw_attr_use", re.compile(r"\b(?:self\.)?raw_attr\b")),
    ("raw_slot_use", re.compile(r"\b(?:self\.)?raw_slot\b")),
    ("compare_accumulated", re.compile(r"\bcompare_accumulated\b")),
    ("revealed_context", re.compile(r"FILTER_REVEALED_CONTEXT")),
    ("total_cost", re.compile(r"FILTER_TOTAL_COST")),
    ("legacy_constant", re.compile(r"\bconst\s+LEGACY_[A-Z0-9_]+")),
    ("hex_mask", re.compile(r"0x[0-9A-Fa-f_]{3,}")),
    ("bit_shift", re.compile(r"<<|>>")),
    ("bit_mask", re.compile(r"&\s*\(|&\s*[A-Za-z0-9_]+|\|\||\btrailing_zeros\b")),
    ("group_logic", re.compile(r"group_id|GROUP_|played_group_mask|activated_(?:energy|member)_group_mask")),
    ("heart_color", re.compile(r"color_mask|heart|V_HEART|selected_color")),
    ("zone_slot", re.compile(r"source_zone|dest_zone|target_slot|remainder_zone|ZONE_")),
    ("looked_revealed", re.compile(r"looked_cards|revealed")),
    ("success_pile", re.compile(r"SuccessPile|SUCCESS_PILE|success_lives|per_card")),
]


@dataclass
class FunctionHit:
    file: str
    line: int
    name: str
    bucket: str
    reasons: list[str]
    signature: str


def iter_rust_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.rs")):
        if any(part == "target" for part in path.parts):
            continue
        if "test" in path.name:
            continue
        yield path


def is_runtime_priority_hit(hit: FunctionHit) -> bool:
    lower_file = hit.file.lower()
    lower_name = hit.name.lower()

    semantic_boundary_helpers = {
        "resolved_filter_attr",
        "semantic_group_id",
        "counts_unique_names",
        "compare_accumulated",
        "uses_total_cost_budget",
        "context_mode",
        "has_revealed_context_passthrough",
        "comparison_mode",
        "comparison_reversed",
        "requests_keyword_energy",
        "requests_keyword_member",
        "requests_played_this_turn_keyword",
        "requests_yell_count_keyword",
        "requests_has_live_set_keyword",
        "inferred_count_zone",
        "count_opcode_hint",
        "scale_source",
        "embedded_count_opcode",
        "uses_count_multiplier",
        "resolved_color_index",
        "normalized_baton_filter_attr",
        "discard_source_zone",
        "requests_success_pile_multiplier",
    }

    if any(
        marker in lower_file
        for marker in (
            "/legacy_codec.rs",
            "/card_db.rs",
            "/filter_attr_compat.rs",
            "/interpreter/logging.rs",
            "/interpreter/instruction.rs",
        )
    ):
        return False

    if "/core/logic/models.rs" in lower_file and lower_name in semantic_boundary_helpers:
        return False

    if "/core/logic/rules.rs" in lower_file and lower_name in semantic_boundary_helpers:
        return False

    if hit.bucket in {"adapter_codec", "generic_raw_semantics"}:
        return False

    if lower_name.startswith(("encode_", "decode_")):
        return False

    return True


def extract_block(text: str, open_brace_index: int) -> str:
    depth = 0
    started = False
    for index in range(open_brace_index, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
            started = True
        elif char == "}":
            depth -= 1
            if started and depth == 0:
                return text[open_brace_index : index + 1]
    return text[open_brace_index:]


def classify_bucket(file_path: Path, name: str, body: str) -> str:
    lower_name = name.lower()
    lower_body = body.lower()
    lower_file = file_path.as_posix().lower()

    if "legacy_codec" in lower_file or lower_name.startswith(("encode_", "decode_")):
        return "adapter_codec"
    if "success_pile" in lower_name or "success_pile" in lower_body or "per_card" in lower_body:
        return "success_pile_multiplier"
    if "filter_total_cost" in lower_body or ("compare_accumulated" in lower_body and "discard" in lower_file):
        return "total_cost_budget"
    if "filter_revealed_context" in lower_body or "looked_cards" in lower_body:
        return "revealed_context"
    if "group_id" in lower_body or "played_group_mask" in lower_body or "activated_member_group_mask" in lower_body:
        return "group_resolution"
    if "color_mask" in lower_body or "v_heart" in lower_body or "selected_color" in lower_body:
        return "heart_color"
    if "source_zone" in lower_body or "dest_zone" in lower_body or "target_slot" in lower_body:
        return "zone_selection"
    if "keyword_" in lower_body:
        return "keyword_flags"
    return "generic_raw_semantics"


def find_hits(file_path: Path) -> list[FunctionHit]:
    text = file_path.read_text(encoding="utf-8")
    hits: list[FunctionHit] = []

    for match in FUNCTION_RE.finditer(text):
        brace_index = text.find("{", match.end())
        if brace_index == -1:
            continue

        signature = match.group(0).strip()
        params = match.group("params")
        body = extract_block(text, brace_index)
        scan_text = f"{params}\n{body}"

        reasons = [label for label, pattern in REASON_PATTERNS if pattern.search(scan_text)]
        if not reasons:
            continue

        if not any(
            reason in reasons
            for reason in (
                "raw_attr_param",
                "raw_slot_param",
                "raw_attr_use",
                "raw_slot_use",
                "compare_accumulated",
                "revealed_context",
                "total_cost",
                "legacy_constant",
                "hex_mask",
                "bit_shift",
            )
        ):
            continue

        line = text.count("\n", 0, match.start()) + 1
        hits.append(
            FunctionHit(
                file=str(file_path.as_posix()),
                line=line,
                name=match.group("name"),
                bucket=classify_bucket(file_path, match.group("name"), body),
                reasons=reasons,
                signature=signature,
            )
        )

    return hits


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        default="engine_rust_src/src/core/logic",
        help="Rust source root to scan relative to the repo root.",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json", "markdown"),
        default="text",
        help="Output format.",
    )
    parser.add_argument(
        "--bucket",
        help="Only print hits for a single semantic bucket.",
    )
    parser.add_argument(
        "--min-reasons",
        type=int,
        default=2,
        help="Minimum number of matched reasons required to keep a function.",
    )
    parser.add_argument(
        "--runtime-priority",
        action="store_true",
        help="Restrict output to runtime migration targets and suppress compatibility/metadata hits.",
    )
    return parser.parse_args()


def render_text(hits: list[FunctionHit]) -> str:
    lines: list[str] = []
    bucket_counts: dict[str, int] = {}
    for hit in hits:
        bucket_counts[hit.bucket] = bucket_counts.get(hit.bucket, 0) + 1

    lines.append("Semantic legacy function scan")
    lines.append(f"Total hits: {len(hits)}")
    lines.append("Buckets:")
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"  - {bucket}: {count}")

    for hit in hits:
        reason_text = ", ".join(hit.reasons)
        lines.append("")
        lines.append(f"{hit.file}:{hit.line}")
        lines.append(f"  fn: {hit.name}")
        lines.append(f"  bucket: {hit.bucket}")
        lines.append(f"  reasons: {reason_text}")
        lines.append(f"  signature: {hit.signature}")

    return "\n".join(lines)


def render_markdown(hits: list[FunctionHit]) -> str:
    bucket_counts = Counter(hit.bucket for hit in hits)
    lines = ["# Semantic Legacy Function Scan", "", f"Total hits: {len(hits)}", "", "## Bucket Counts", ""]

    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: {count}")

    grouped: dict[str, list[FunctionHit]] = {}
    for hit in hits:
        grouped.setdefault(hit.bucket, []).append(hit)

    for bucket in sorted(grouped):
        lines.extend(["", f"## {bucket}", ""])
        for hit in grouped[bucket]:
            reason_text = ", ".join(hit.reasons)
            rel_file = hit.file.replace(str(Path(__file__).resolve().parent.parent.as_posix()) + "/", "")
            lines.append(f"- `{rel_file}:{hit.line}` `{hit.name}`")
            lines.append(f"  reasons: {reason_text}")

    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parent.parent
    scan_root = (repo_root / args.root).resolve()

    hits: list[FunctionHit] = []
    for rust_file in iter_rust_files(scan_root):
        for hit in find_hits(rust_file):
            if len(hit.reasons) < args.min_reasons:
                continue
            if args.bucket and hit.bucket != args.bucket:
                continue
            if args.runtime_priority and not is_runtime_priority_hit(hit):
                continue
            hits.append(hit)

    if args.format == "json":
        print(json.dumps([asdict(hit) for hit in hits], indent=2))
    elif args.format == "markdown":
        print(render_markdown(hits))
    else:
        print(render_text(hits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())