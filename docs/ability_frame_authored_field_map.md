# Authored Ability Frame Field Map

This file lists the authored JSON fields used in `data/ability_frame_source.json`, where they land at runtime, and whether they should stay numeric or be authored as words.

## Top-level entry fields

| Field | Runtime destination | Kind |
| --- | --- | --- |
| `trigger_id` | Rust `AbilityFrame` trigger dispatch | quantity/code |
| `trigger` | Human-readable trigger label only | word |
| `frame_count` | Derived summary only | quantity |
| `opcode_sequence` | Derived summary only | words |
| `frames` | Rust `AbilityFrame::from_json_value()` | structured |
| `cards` | Authored traceability only | words |
| `card_refs.card_no` | Card lookup / audit trace | word |
| `card_refs.ability_index` | Ability lookup on the card | quantity |
| `card_refs.db` | Source database label | word |
| `card_refs.card_id` | Database card id | quantity |
| `card_refs.name` | Audit trace only | word |
| `card_refs.trigger` | Trace copy of trigger id/name | quantity |
| `signature`, `signature_hash`, `signature_source` | Derived canonical signature from trigger + frames | derived |
| `pseudocode`, `primary_text_jp`, `primary_text_en`, `source_ability_texts`, `source_mode` | Audit/documentation only | words |

## Frame fields

| Field | Runtime destination | Kind |
| --- | --- | --- |
| `op` | Rust opcode enum / runtime handler selection | word |
| `frame_index` | Execution order within the authored program | quantity |
| `value` | Frame payload amount/count/threshold, or structured sub-payload | quantity/structured |
| `params.scalar_dynamic.base_value` | Dynamic value base | quantity |
| `params.scalar_dynamic.divisor` | Dynamic value divisor | quantity |
| `options.value` | Choice/select payload count | quantity |
| `options.slot.*` | Same slot mapping as `slot.*` | mixed |
| `attr.*` | Rust filter overlay via `filter_parts_from_params()` | mixed |
| `slot.*` | Rust decoded slot via `DecodedSlotStructuredRaw` | mixed |

## Named categorical fields

These are identifiers. They should be authored as words, not numeric ids.

| Field | Runtime mapping |
| --- | --- |
| `slot.target_slot` | `parse_target_slot_value()` in `engine_rust_src/src/core/logic/interpreter/instruction.rs` |
| `slot.comparison` | `parse_comparison_value()` |
| `slot.source_zone` | `parse_zone_text()` |
| `slot.dest_zone` | `parse_zone_text()` |
| `slot.remainder_zone` | `parse_remainder_zone_value()` |
| `attr.target_player` | `CardFilter.target_player` via `filter_parts_from_params()` |
| `attr.card_type` | `CardFilter.card_type` |
| `attr.group_id` | `parse_group_id_value()` / `group_id_from_name()` |
| `attr.unit_id` | `parse_unit_id_value()` / `unit_id_from_name()` |
| `attr.char_id_1`, `attr.char_id_2`, `attr.char_id_3` | `parse_character_id_value()` / `character_id_from_name()` |
| `attr.color_mask` | `parse_color_mask_value()` |
| `attr.zone_mask` | `parse_zone_mask_text()` style handling in filter parsing |
| `attr.special_id` | special selector parsing in filter overlay |
| `attr.keyword` | keyword extras in `apply_keyword_param()` |

## Quantity fields

These represent counts, thresholds, offsets, or control flow, so numeric values are correct.

| Field | Meaning |
| --- | --- |
| `value` | count, amount, blade/heart delta, score delta, or jump offset |
| `value.count` | look/search/reveal count |
| `value.choose_count` | number of cards the user may choose |
| `value.dest_discard` | numeric flag payload in structured values |
| `value.reveal` | numeric reveal flag payload |
| `value_threshold` | filter threshold such as cost <= 4 or count >= 3 |
| `choice_count` | number of options in a choice program |
| `choice_flags` | packed runtime choice flags |
| `frame_index` | per-frame order |
| `trigger_id` | trigger opcode id |
| `ability_index` | ability ordinal on the source card |
| `card_id` | numeric database id |

## Practical rule

If a field selects from a roster, group, unit, zone, slot, comparison, keyword, or other enum-like bucket, author it as a word.

If a field measures how many, how much, which step to jump to, or which database row/card/ability is being referenced, keep it numeric.