from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
ENTRYPOINTS_PATH = ROOT / "data" / "ability_runtime_entrypoints.json"
METADATA_PATH = ROOT / "data" / "metadata.json"
REPORT_DIR = ROOT / "reports" / "ability_diagnostics"
REPORT_JSON_PATH = REPORT_DIR / "diagnostics.json"
INDEX_MD_PATH = REPORT_DIR / "index.md"
CARDS_DIR = REPORT_DIR / "cards"


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sanitize_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value or "unknown")


def normalize_card_no(card_no: str) -> str:
    return str(card_no or "").replace("・・", "+").strip()


def iter_entries(report: dict[str, Any]) -> list[dict[str, Any]]:
    entries = report.get("abilities", [])
    return [entry for entry in entries if isinstance(entry, dict)]


def entry_key(entry: dict[str, Any]) -> str:
    return f"{normalize_card_no(str(entry.get('card_no', '')))}#{int(entry.get('ability_index', 0) or 0)}"


def entry_title(entry: dict[str, Any]) -> str:
    return (
        f"{entry.get('card_no', 'Unknown')} "
        f"(card_id={entry.get('card_id', 0)}) "
        f"ab#{entry.get('ability_index', 0)} - {entry.get('card_name', '')}"
    )


def build_trigger_names(metadata: dict[str, Any]) -> dict[int, str]:
    triggers = metadata.get("triggers", {})
    result: dict[int, str] = {}
    if isinstance(triggers, dict):
        for name, value in triggers.items():
            try:
                result[int(value)] = name
            except (TypeError, ValueError):
                continue
    return result


def trigger_name(entry: dict[str, Any], trigger_names: dict[int, str]) -> str:
    trigger = entry.get("trigger")
    if isinstance(trigger, str):
        return trigger
    try:
        return trigger_names.get(int(trigger), str(trigger))
    except (TypeError, ValueError):
        return str(trigger)


def build_semantic_maps(metadata: dict[str, Any]) -> dict[str, Any]:
    def humanize(value: str) -> str:
        return str(value).replace("_", " ").lower()

    def reverse_numeric_map(mapping: dict[str, Any]) -> dict[int, str]:
        result: dict[int, str] = {}
        for name, value in mapping.items():
            try:
                result[int(value)] = str(name)
            except (TypeError, ValueError):
                continue
        return result

    def reverse_lang_map(mapping: dict[str, Any], language: str = "en") -> dict[int, str]:
        result: dict[int, str] = {}
        for key, value in mapping.items():
            try:
                idx = int(key)
            except (TypeError, ValueError):
                continue
            if isinstance(value, dict):
                result[idx] = str(value.get(language) or value.get("jp") or key)
            else:
                result[idx] = str(value)
        return result

    zone_names = reverse_numeric_map(metadata.get("zones", {}))
    card_types = reverse_numeric_map(metadata.get("card_types", {}))
    target_players = reverse_numeric_map(metadata.get("target_players", {}))
    slot_indices = reverse_numeric_map(metadata.get("slot_indices", {}))
    group_names = reverse_lang_map(metadata.get("group_names", {}))
    unit_names = reverse_lang_map(metadata.get("unit_names", {}))
    color_names = reverse_numeric_map(metadata.get("heart_color_map", {}))

    return {
        "zone_names": {key: humanize(value) for key, value in zone_names.items()},
        "card_types": {key: humanize(value) for key, value in card_types.items()},
        "target_players": {key: humanize(value) for key, value in target_players.items()},
        "slot_indices": slot_indices,
        "group_names": group_names,
        "unit_names": unit_names,
        "color_names": {key: humanize(value) for key, value in color_names.items()},
    }


def semantic_zone(value: Any, maps: dict[str, Any]) -> str:
    try:
        zone_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    zone_names = maps["zone_names"]
    return zone_names.get(zone_id, f"zone {zone_id}")


def semantic_target_player(value: Any, maps: dict[str, Any]) -> str:
    try:
        target_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return {
        0: "any player",
        1: "self",
        2: "opponent",
        3: "both players",
    }.get(target_id, maps["target_players"].get(target_id, f"target {target_id}"))


def semantic_card_type(value: Any, maps: dict[str, Any]) -> str:
    try:
        card_type_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return {
        0: "any type",
        **maps["card_types"],
    }.get(card_type_id, f"type {card_type_id}")


def semantic_group(value: Any, maps: dict[str, Any]) -> str:
    try:
        group_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return maps["group_names"].get(group_id, f"group {group_id}")


def semantic_unit(value: Any, maps: dict[str, Any]) -> str:
    try:
        unit_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return maps["unit_names"].get(unit_id, f"unit {unit_id}")


def semantic_color_mask(mask: Any, maps: dict[str, Any]) -> str:
    try:
        color_mask = int(mask)
    except (TypeError, ValueError):
        return str(mask)
    if color_mask == 0:
        return "any color"
    colors = [name for bit, name in sorted(maps["color_names"].items()) if color_mask & (1 << bit)]
    return ", ".join(colors) if colors else f"color mask {color_mask}"


def semantic_zone_mask(mask: Any, maps: dict[str, Any]) -> str:
    try:
        zone_mask = int(mask)
    except (TypeError, ValueError):
        return str(mask)
    if zone_mask == 0:
        return "any zone"
    zone_map = {
        4: "stage",
        6: "hand",
        7: "discard",
    }
    return zone_map.get(zone_mask, semantic_zone(zone_mask, maps))


def semantic_special_id(value: Any) -> str:
    try:
        special_id = int(value)
    except (TypeError, ValueError):
        return str(value)
    return {
        1: "name contains character",
        2: "not setsuna",
        3: "not self",
        4: "same name",
        5: "base cost",
        6: "selected discard",
    }.get(special_id, f"special {special_id}")


def format_filter_semantics(filter_obj: Any, maps: dict[str, Any], include_target_player: bool = True) -> str:
    if not isinstance(filter_obj, dict) or not filter_obj.get("is_enabled"):
        return "any card"

    parts: list[str] = []
    target_player = int(filter_obj.get("target_player", 0) or 0)
    if include_target_player and target_player:
        parts.append(f"target={semantic_target_player(target_player, maps)}")

    card_type = int(filter_obj.get("card_type", 0) or 0)
    if card_type:
        parts.append(f"type={semantic_card_type(card_type, maps)}")

    if filter_obj.get("group_enabled"):
        parts.append(f"group={semantic_group(filter_obj.get('group_id', 0), maps)}")
    if filter_obj.get("unit_enabled"):
        parts.append(f"unit={semantic_unit(filter_obj.get('unit_id', 0), maps)}")

    if filter_obj.get("value_enabled"):
        threshold = filter_obj.get("value_threshold", 0)
        op = "<=" if filter_obj.get("is_le") else ">="
        if filter_obj.get("is_cost_type"):
            parts.append(f"cost{op}{threshold}")
        else:
            parts.append(f"value{op}{threshold}")

    if filter_obj.get("color_mask"):
        parts.append(f"color={semantic_color_mask(filter_obj.get('color_mask'), maps)}")
    if filter_obj.get("zone_mask"):
        parts.append(f"zone={semantic_zone_mask(filter_obj.get('zone_mask'), maps)}")
    if filter_obj.get("special_id"):
        parts.append(f"special={semantic_special_id(filter_obj.get('special_id'))}")
    if filter_obj.get("is_tapped"):
        parts.append("tapped")
    if filter_obj.get("has_blade_heart"):
        parts.append("has blade heart")
    if filter_obj.get("not_has_blade_heart"):
        parts.append("missing blade heart")
    if filter_obj.get("unique_names"):
        parts.append("unique names")
    if filter_obj.get("is_setsuna"):
        parts.append("setsuna")
    if filter_obj.get("compare_accumulated"):
        parts.append("compare accumulated")
    if filter_obj.get("keyword_member"):
        parts.append("member keyword")
    if filter_obj.get("keyword_energy"):
        parts.append("energy keyword")
    if filter_obj.get("is_optional"):
        parts.append("optional")

    return ", ".join(parts) if parts else "any card"


def semantic_slot_label(value: Any, maps: dict[str, Any]) -> str:
    try:
        slot_value = int(value)
    except (TypeError, ValueError):
        return str(value)

    if slot_value == 0:
        return "context / inherited"
    if slot_value == 4:
        return "context / stage area index"
    if slot_value in (6, 7, 8, 13, 14, 15, 20):
        labels = {
            6: "hand",
            7: "discard",
            8: "deck",
            13: "live set",
            14: "live slot 1",
            15: "live slot 2",
            20: "player select",
        }
        return labels[slot_value]

    return maps["slot_indices"].get(slot_value, f"slot {slot_value}")


def format_slot_semantics(slot_obj: Any, maps: dict[str, Any]) -> str:
    if not isinstance(slot_obj, dict):
        return str(slot_obj)

    parts: list[str] = []
    source_zone = slot_obj.get("source_zone")
    dest_zone = slot_obj.get("dest_zone")
    remainder_zone = slot_obj.get("remainder_zone")
    target_slot = slot_obj.get("target_slot")
    area_idx = slot_obj.get("area_idx")

    if source_zone is not None:
        parts.append(f"source={semantic_zone(source_zone, maps)}")
    if dest_zone is not None:
        parts.append(f"dest={semantic_zone(dest_zone, maps)}")
    if remainder_zone is not None and int(remainder_zone) != 0:
        parts.append(f"remainder={semantic_zone(remainder_zone, maps)}")
    if target_slot is not None:
        parts.append(f"target={semantic_slot_label(target_slot, maps)}")
    if area_idx is not None and int(area_idx) != 0:
        parts.append(f"area_idx={area_idx}")
    if slot_obj.get("is_opponent"):
        parts.append("opponent")
    if slot_obj.get("is_reveal_until_live"):
        parts.append("reveal-until-live")
    if slot_obj.get("is_baton_slot"):
        parts.append("baton")
    if slot_obj.get("is_empty_slot"):
        parts.append("empty-only")
    if slot_obj.get("is_wait"):
        parts.append("wait")
    if slot_obj.get("is_dynamic"):
        parts.append("dynamic")

    return ", ".join(parts) if parts else "unrestricted slot"


def runtime_target_semantics(step: dict[str, Any], maps: dict[str, Any]) -> str:
    slot = step.get("slot")
    if isinstance(slot, dict):
        if slot.get("is_opponent"):
            return "opponent"
        return "self"

    filter_obj = step.get("filter")
    if isinstance(filter_obj, dict):
        target_player = int(filter_obj.get("target_player", 0) or 0)
        if target_player:
            return semantic_target_player(target_player, maps)
    return "self"


def trace_diagnostics(entry: dict[str, Any]) -> dict[str, Any]:
    trace_view = entry.get("trace_view", {})
    diagnostics = trace_view.get("diagnostics", {}) if isinstance(trace_view, dict) else {}
    if not isinstance(diagnostics, dict):
        diagnostics = {}
    return {
        "source_paths": diagnostics.get("source_paths", []),
        "action_routes": entry.get("action_routes", []) or diagnostics.get("action_routes", []),
        "serialization_paths": entry.get("serialization_paths", []) or diagnostics.get("serialization_paths", []),
        "serialization_fields": entry.get("serialization_fields", []) or diagnostics.get("serialization_fields", []),
        "warnings": entry.get("warnings", []) or diagnostics.get("warnings", []),
    }


def build_card_record(entry: dict[str, Any], semantic_maps: dict[str, Any]) -> dict[str, Any]:
    trace_view = entry.get("trace_view", {})
    diagnostics = trace_diagnostics(entry)
    frames = entry.get("resolved_frames", [])
    raw_steps = trace_view.get("steps", []) if isinstance(trace_view, dict) else []
    steps: list[dict[str, Any]] = []
    for step in raw_steps:
        if not isinstance(step, dict):
            continue
        semantic_step = dict(step)
        semantic_step["target_semantic"] = runtime_target_semantics(step, semantic_maps)
        semantic_step["filter_semantic"] = format_filter_semantics(
            step.get("filter"),
            semantic_maps,
            include_target_player=not isinstance(step.get("slot"), dict),
        )
        semantic_step["slot_semantic"] = format_slot_semantics(step.get("slot"), semantic_maps)
        if step.get("source_zone") is not None:
            semantic_step["source_zone_semantic"] = semantic_zone(step.get("source_zone"), semantic_maps)
        if step.get("dest_zone") is not None:
            semantic_step["dest_zone_semantic"] = semantic_zone(step.get("dest_zone"), semantic_maps)
        if step.get("target_slot") is not None:
            semantic_step["target_slot_semantic"] = semantic_slot_label(step.get("target_slot"), semantic_maps)
        steps.append(semantic_step)

    return {
        "key": entry_key(entry),
        "card_no": entry.get("card_no", ""),
        "card_id": entry.get("card_id", 0),
        "card_name": entry.get("card_name", ""),
        "card_kind": entry.get("card_kind", ""),
        "ability_index": entry.get("ability_index", 0),
        "trigger": trigger_name(entry, {}),
        "frame_source": trace_view.get("frame_source", entry.get("frame_source", "")),
        "choice_count": trace_view.get("choice_count", entry.get("choice_count", 0)),
        "raw_text": trace_view.get("raw_text", entry.get("raw_text", "")),
        "pseudocode": entry.get("pseudocode", ""),
        "effect_count": entry.get("effect_count", 0),
        "condition_count": entry.get("condition_count", 0),
        "cost_count": entry.get("cost_count", 0),
        "frame_count": len(frames),
        "steps": steps,
        "diagnostics": diagnostics,
    }


def step_summary(step: dict[str, Any]) -> str:
    parts = [str(step.get("summary", step.get("opcode", "step")))]
    family = step.get("family")
    if family:
        parts.append(f"[{family}]")
    if step.get("is_cost"):
        parts.append("(cost)")
    return " ".join(parts)


def format_json_inline(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def render_card_markdown(record: dict[str, Any]) -> str:
    diagnostics = record["diagnostics"]
    japanese_text = str(record.get("raw_text", "") or "").strip()
    lines: list[str] = []
    lines.append(f"# {entry_title(record)}")
    lines.append("")
    lines.append("## Japanese Text")
    if japanese_text:
        lines.append(f"> {japanese_text.replace(chr(10), ' ')}")
    else:
        lines.append("> (not available)")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Key: `{record['key']}`")
    lines.append(f"- Trigger: `{record['trigger']}`")
    lines.append(f"- Frame source: `{record['frame_source']}`")
    lines.append(f"- Frames: `{record['frame_count']}`")
    lines.append(f"- Costs / Conditions / Effects: `{record['cost_count']}` / `{record['condition_count']}` / `{record['effect_count']}`")
    lines.append(f"- Choice count: `{record['choice_count']}`")
    if diagnostics["warnings"]:
        lines.append(f"- Warnings: {', '.join(f'`{warning}`' for warning in diagnostics['warnings'])}")
    else:
        lines.append("- Warnings: none")

    lines.append("")
    lines.append("## Source And Runtime Paths")
    for path in diagnostics["source_paths"]:
        lines.append(f"- `{path}`")

    lines.append("")
    lines.append("## Action Generator Routes")
    if diagnostics["action_routes"]:
        for path in diagnostics["action_routes"]:
            lines.append(f"- `{path}`")
    else:
        lines.append("- none detected")

    lines.append("")
    lines.append("## Serialization Surface")
    if diagnostics["serialization_fields"]:
        for field in diagnostics["serialization_fields"]:
            lines.append(f"- `{field}`")
    if diagnostics["serialization_paths"]:
        for path in diagnostics["serialization_paths"]:
            lines.append(f"- `{path}`")

    lines.append("")
    lines.append("## Steps")
    for idx, step in enumerate(record["steps"]):
        lines.append(f"### Step {idx}")
        lines.append(f"- Summary: `{step_summary(step)}`")
        if step.get("family"):
            lines.append(f"- Family: `{step['family']}`")
        if step.get("target_semantic"):
            lines.append(f"- Target: `{step['target_semantic']}`")
        if step.get("filter_semantic"):
            lines.append(f"- Filter: {step['filter_semantic']}")
        if step.get("filter") is not None:
            lines.append(f"- Filter raw: `{format_json_inline(step['filter'])}`")
        if step.get("slot_semantic"):
            lines.append(f"- Slot: {step['slot_semantic']}")
        if step.get("slot") is not None:
            lines.append(f"- Slot raw: `{format_json_inline(step['slot'])}`")
        if step.get("consumer_paths"):
            lines.append("- Consumer paths:")
            for path in step["consumer_paths"]:
                lines.append(f"  - `{path}`")
        if step.get("serialization_fields"):
            lines.append("- Serialized fields:")
            for field in step["serialization_fields"]:
                lines.append(f"  - `{field}`")
        if step.get("value") is not None:
            lines.append(f"- Value: `{step['value']}`")
        if step.get("source_zone_semantic") is not None:
            lines.append(f"- Source zone: `{step['source_zone_semantic']}`")
        if step.get("dest_zone_semantic") is not None:
            lines.append(f"- Destination zone: `{step['dest_zone_semantic']}`")
        if step.get("target_slot_semantic") is not None:
            lines.append(f"- Target slot: `{step['target_slot_semantic']}`")
        if step.get("choose_count") is not None:
            lines.append(f"- Choose count: `{step['choose_count']}`")
        if step.get("params") not in (None, {}, []):
            lines.append(f"- Params: `{step['params']}`")

    return "\n".join(lines)


def render_index(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Ability Diagnostics")
    lines.append("")
    lines.append("This report explains each ability from source intent through hydrated frames, action-generation routes, and serialized runtime fields.")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Generated by: `{report['generated_by']}`")
    lines.append(f"- Generated at: `{report['generated_at']}`")
    lines.append(f"- Entries: `{report['summary']['entry_count']}`")
    lines.append(f"- Cards: `{report['summary']['card_count']}`")
    lines.append(f"- Abilities with warnings: `{report['summary']['warning_count']}`")
    lines.append(f"- Abilities with action routes: `{report['summary']['routed_count']}`")
    lines.append("")
    lines.append("## Top Warnings")
    if report["summary"]["top_warnings"]:
        for warning, count in report["summary"]["top_warnings"]:
            lines.append(f"- `{warning}`: `{count}`")
    else:
        lines.append("- none")

    lines.append("")
    lines.append("## Index")
    lines.append("| Card | Card ID | Trigger | Source | Frames | Routes | Warnings | Drilldown |")
    lines.append("| --- | ---: | --- | --- | ---: | ---: | ---: | --- |")
    for record in report["abilities"]:
        drilldown = (
            f"[open](./cards/{record['card_id']}_{sanitize_name(record['card_no'])}"
            f"_ab{record['ability_index']}.md)"
        )
        lines.append(
            f"| `{record['card_no']}` | `{record['card_id']}` | `{record['trigger']}` | `{record['frame_source']}` | "
            f"{record['frame_count']} | {len(record['diagnostics']['action_routes'])} | "
            f"{len(record['diagnostics']['warnings'])} | {drilldown} |"
        )

    return "\n".join(lines)


def build_report() -> dict[str, Any]:
    metadata = read_json(METADATA_PATH)
    semantic_maps = build_semantic_maps(metadata)
    trigger_names = build_trigger_names(metadata)
    entrypoints = read_json(ENTRYPOINTS_PATH)
    entries = []
    for entry in iter_entries(entrypoints):
        record = build_card_record(entry, semantic_maps)
        record["trigger"] = trigger_name(entry, trigger_names)
        entries.append(record)
    card_count = len({normalize_card_no(entry["card_no"]) for entry in entries})
    warnings: dict[str, int] = {}
    routed_count = 0

    for record in entries:
        diagnostics = record["diagnostics"]
        if diagnostics["action_routes"]:
            routed_count += 1
        for warning in diagnostics["warnings"]:
            warnings[warning] = warnings.get(warning, 0) + 1

    top_warnings = sorted(warnings.items(), key=lambda item: (-item[1], item[0]))[:20]

    return {
        "generated_by": str(Path(__file__).relative_to(ROOT)),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": str(ENTRYPOINTS_PATH),
        "metadata_source": str(METADATA_PATH),
        "summary": {
            "entry_count": len(entries),
            "card_count": card_count,
            "warning_count": sum(1 for entry in entries if entry["diagnostics"]["warnings"]),
            "routed_count": routed_count,
            "top_warnings": top_warnings,
        },
        "abilities": entries,
    }


def write_outputs(report: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    write_json(REPORT_JSON_PATH, report)
    write_text(INDEX_MD_PATH, render_index(report))

    for record in report["abilities"]:
        card_path = CARDS_DIR / (
            f"{record['card_id']}_{sanitize_name(record['card_no'])}_ab{record['ability_index']}.md"
        )
        write_text(card_path, render_card_markdown(record))


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate ability diagnostics report.")
    parser.add_argument("--card", help="Only render one card_no drilldown", default=None)
    args = parser.parse_args()

    report = build_report()
    if args.card:
        needle = normalize_card_no(args.card)
        abilities = [entry for entry in report["abilities"] if normalize_card_no(entry["card_no"]) == needle]
        warnings: dict[str, int] = {}
        routed_count = 0
        for record in abilities:
            diagnostics = record["diagnostics"]
            if diagnostics["action_routes"]:
                routed_count += 1
            for warning in diagnostics["warnings"]:
                warnings[warning] = warnings.get(warning, 0) + 1

        report = {
            **report,
            "abilities": abilities,
            "summary": {
                "entry_count": len(abilities),
                "card_count": len({normalize_card_no(entry["card_no"]) for entry in abilities}),
                "warning_count": sum(1 for entry in abilities if entry["diagnostics"]["warnings"]),
                "routed_count": routed_count,
                "top_warnings": sorted(warnings.items(), key=lambda item: (-item[1], item[0]))[:20],
            },
        }

    write_outputs(report)
    print(f"Wrote {len(report['abilities'])} ability diagnostics entries to {REPORT_DIR}")


if __name__ == "__main__":
    main()
