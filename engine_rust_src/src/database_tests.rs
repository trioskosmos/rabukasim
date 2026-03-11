// use crate::test_helpers::{Action, TestUtils, create_test_db, create_test_state, p_state};
use crate::core::logic::*;
// use crate::core::models::*;
// use crate::core::enums::*;
use serde_json::Value;
use std::collections::HashSet;

const DB_JSON: &str = include_str!("../../data/cards_compiled.json");
const METADATA_JSON: &str = include_str!("../../data/metadata.json");
const GENERATED_CONSTANTS_RS: &str = include_str!("core/generated_constants.rs");
const GENERATED_ENUMS_RS: &str = include_str!("core/enums.rs");

#[test]
fn test_database_integrity() {
    let card_db =
        CardDatabase::from_json(DB_JSON).expect("Failed to parse production CardDatabase");

    let mut member_ids = HashSet::new();
    let mut card_nos = HashSet::new();

    for (id, member) in &card_db.members {
        assert!(member_ids.insert(id), "Duplicate Member ID found: {}", id);
        assert!(!member.card_no.is_empty(), "Empty CardNo for ID: {}", id);
        card_nos.insert(member.card_no.clone());
    }

    let mut live_ids = HashSet::new();
    for (id, live) in &card_db.lives {
        assert!(live_ids.insert(id), "Duplicate Live ID found: {}", id);
        assert!(!live.card_no.is_empty(), "Empty CardNo for ID: {}", id);
        card_nos.insert(live.card_no.clone());
    }

    println!(
        "Database Integrity Check Passed: {} members, {} lives",
        card_db.members.len(),
        card_db.lives.len()
    );
}

#[test]
fn test_bytecode_sanity_all_cards() {
    let card_db =
        CardDatabase::from_json(DB_JSON).expect("Failed to parse production CardDatabase");
    let mut total_abilities = 0;
    let mut opcodes_seen = HashSet::new();

    for member in card_db.members.values() {
        for (idx, ab) in member.abilities.iter().enumerate() {
            total_abilities += 1;
            verify_ability_bytecode(&member.card_no, idx, ab, &mut opcodes_seen);
        }
    }

    for live in card_db.lives.values() {
        for (idx, ab) in live.abilities.iter().enumerate() {
            total_abilities += 1;
            verify_ability_bytecode(&live.card_no, idx, ab, &mut opcodes_seen);
        }
    }

    println!("Bytecode Sanity Passed for {} abilities.", total_abilities);
    println!(
        "Unique Opcodes Found in Production: {:?}",
        opcodes_seen.len()
    );
}

fn verify_ability_bytecode(card_no: &str, ab_idx: usize, ab: &Ability, opcodes: &mut HashSet<i32>) {
    if ab.bytecode.is_empty() {
        return;
    }

    // Rule 1: Bytecode block must contain O_RETURN (10)
    assert!(
        ab.bytecode.contains(&O_RETURN),
        "Ability {} [{}] does not contain O_RETURN",
        card_no,
        ab_idx
    );

    // Rule 2: Bytecode length should generally be a multiple of 5 (5-word extended format)
    // Note: Some jump targets or complex opcodes might vary, but O_RETURN is always at the end.
    // In our compiler, almost all are 5-word aligned.
    assert!(
        ab.bytecode.len() % 5 == 0,
        "Ability {} [{}] bytecode length {} is not multiple of 5",
        card_no,
        ab_idx,
        ab.bytecode.len()
    );

    for chunk in ab.bytecode.chunks(5) {
        if !chunk.is_empty() {
            opcodes.insert(chunk[0]);
        }
    }
}

#[test]
fn test_dry_run_all_cards() {
    let card_db =
        CardDatabase::from_json(DB_JSON).expect("Failed to parse production CardDatabase");
    let mut state = GameState::default();
    // Basic setup for dry run
    state.players[0].player_id = 0;
    state.players[1].player_id = 1;

    for member in card_db.members.values() {
        for (idx, ab) in member.abilities.iter().enumerate() {
            if ab.bytecode.is_empty() || ab.trigger == TriggerType::Constant {
                continue;
            }

            let ctx = AbilityContext {
                player_id: 0,
                area_idx: 0,
                source_card_id: member.card_id,
                ability_index: idx.try_into().expect("ability_index out of i16 range"),
                ..Default::default()
            };

            // Dry run execution (this should NOT panic)
            // We use a clone of state to keep it clean
            let mut test_state = state.clone();
            test_state.resolve_bytecode_cref(&card_db, &ab.bytecode, &ctx);
        }
    }
}

#[test]
fn test_generated_metadata_stays_in_sync() {
    let metadata: Value = serde_json::from_str(METADATA_JSON).expect("Failed to parse metadata.json");

    assert_generated_constants_match(&metadata, "opcodes", "O_");
    assert_generated_constants_match(&metadata, "action_bases", "ACTION_BASE_");
    assert_generated_constants_match(&metadata, "conditions", "C_");
    assert_generated_constants_match(&metadata, "costs", "COST_");

    assert_generated_enum_match(&metadata, "triggers", enum_variant_name, GENERATED_ENUMS_RS);
    assert_generated_enum_match(&metadata, "targets", target_variant_name, GENERATED_ENUMS_RS);
    assert_generated_enum_match(&metadata, "phases", enum_variant_name, GENERATED_ENUMS_RS);
}

fn assert_generated_constants_match(metadata: &Value, section: &str, prefix: &str) {
    for (key, value) in metadata_section(metadata, section) {
        let expected = value.as_i64().unwrap_or_else(|| panic!("{section}.{key} is not numeric"));
        let expected_line = format!("pub const {prefix}{key}: i32 = {expected};");
        assert!(
            GENERATED_CONSTANTS_RS
                .lines()
                .any(|line| line.trim_start().starts_with(&expected_line)),
            "generated_constants.rs is out of sync for {section}.{key}={expected}"
        );
    }
}

fn assert_generated_enum_match(
    metadata: &Value,
    section: &str,
    variant_name: fn(&str) -> String,
    source: &str,
) {
    for (key, value) in metadata_section(metadata, section) {
        let expected = value.as_i64().unwrap_or_else(|| panic!("{section}.{key} is not numeric"));
        let variant = variant_name(key);
        let expected_line = format!("{variant} = {expected},");
        assert!(
            source
                .lines()
                .any(|line| line.trim_start().starts_with(&expected_line)),
            "enums.rs is out of sync for {section}.{key}={expected}"
        );
    }
}

fn metadata_section<'a>(metadata: &'a Value, section: &str) -> &'a serde_json::Map<String, Value> {
    metadata[section]
        .as_object()
        .unwrap_or_else(|| panic!("metadata section {section} is missing or not an object"))
}

fn enum_variant_name(raw: &str) -> String {
    if raw == "NONE" {
        return "None".to_string();
    }

    raw.to_ascii_lowercase()
        .split('_')
        .filter(|part| !part.is_empty())
        .map(|part| {
            let mut chars = part.chars();
            match chars.next() {
                Some(first) => first.to_ascii_uppercase().to_string() + chars.as_str(),
                None => String::new(),
            }
        })
        .collect::<String>()
}

fn target_variant_name(raw: &str) -> String {
    if raw == "SELF" {
        return "Self_".to_string();
    }
    enum_variant_name(raw)
}
