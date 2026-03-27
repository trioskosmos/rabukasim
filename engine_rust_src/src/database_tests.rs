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

#[test]
fn test_ability_manifest_covers_production_database() {
    let card_db =
        CardDatabase::from_json(DB_JSON).expect("Failed to parse production CardDatabase");
    let cards_payload: Value = serde_json::from_str(DB_JSON)
        .expect("Failed to parse production cards_compiled.json");
    let metadata: Value = serde_json::from_str(METADATA_JSON)
        .expect("Failed to parse metadata.json");

    let manifest = crate::core::logic::ability_manifest::AbilityManifest::build(
        &cards_payload,
        &metadata,
        "test-generated".to_string(),
        "data/cards_compiled.json".to_string(),
        "data/metadata.json".to_string(),
    );

    assert_eq!(manifest.schema, crate::core::logic::ability_manifest::MANIFEST_SCHEMA);

    let source_card_count = card_db
        .members
        .values()
        .filter(|card| !card.abilities.is_empty())
        .count()
        + card_db
            .lives
            .values()
            .filter(|card| !card.abilities.is_empty())
            .count();
    let source_ability_count = card_db
        .members
        .values()
        .map(|card| card.abilities.len())
        .sum::<usize>()
        + card_db
            .lives
            .values()
            .map(|card| card.abilities.len())
            .sum::<usize>();

    assert_eq!(manifest.summary.card_count, source_card_count);
    assert_eq!(manifest.summary.ability_count, source_ability_count);
    assert_eq!(manifest.summary.card_count, manifest.cards.len());

    let bp1 = manifest
        .card_by_no("LL-bp1-001-R+")
        .expect("LL-bp1-001-R+ should be present in the manifest");
    assert_eq!(bp1.ability_count, 2);

    let bp2 = manifest
        .card_by_no("LL-bp2-001-R+")
        .expect("LL-bp2-001-R+ should be present in the manifest");
    assert_eq!(bp2.ability_count, 3);
    assert!(bp2
        .abilities
        .iter()
        .any(|ability| ability.flow_pattern == "prompted_branching"));
}

#[test]
fn test_ability_manifest_round_trips_and_represents_real_cards() {
    let cards_payload: Value = serde_json::from_str(DB_JSON)
        .expect("Failed to parse production cards_compiled.json");
    let metadata: Value = serde_json::from_str(METADATA_JSON)
        .expect("Failed to parse metadata.json");

    let manifest = crate::core::logic::ability_manifest::AbilityManifest::build(
        &cards_payload,
        &metadata,
        "test-generated".to_string(),
        "data/cards_compiled.json".to_string(),
        "data/metadata.json".to_string(),
    );

    let serialized = serde_json::to_value(&manifest).expect("manifest should serialize to JSON");
    let round_trip: crate::core::logic::ability_manifest::AbilityManifest = serde_json::from_value(serialized)
        .expect("manifest should deserialize from JSON");

    let bp1 = round_trip
        .card_by_no("LL-bp1-001-R+")
        .expect("LL-bp1-001-R+ should survive a round trip");
    assert_eq!(bp1.abilities[0].trigger, "ON_PLAY");
    assert_eq!(bp1.abilities[0].flow_pattern, "optional_effect");
    assert_eq!(bp1.abilities[0].frame_count, 2);
    assert_eq!(bp1.abilities[0].opcode_sequence, vec!["RECOVER_MEMBER", "RETURN"]);
    assert_eq!(bp1.abilities[0].frames[0].role, "cost");

    assert_eq!(bp1.abilities[1].trigger, "ON_LIVE_START");
    assert_eq!(bp1.abilities[1].flow_pattern, "optional_branching");
    assert_eq!(bp1.abilities[1].opcode_sequence, vec!["MOVE_TO_DISCARD", "JUMP_IF_FALSE", "BOOST_SCORE", "RETURN"]);
    assert_eq!(bp1.abilities[1].frames[0].role, "cost");
    assert_eq!(bp1.abilities[1].frames[1].role, "control");
    assert_eq!(bp1.abilities[1].frames[2].role, "effect");
    assert!(bp1.abilities[1].summary.starts_with("Optional cost:"));

    let bp2 = round_trip
        .card_by_no("LL-bp2-001-R+")
        .expect("LL-bp2-001-R+ should survive a round trip");
    assert_eq!(bp2.abilities[2].trigger, "ON_LIVE_START");
    assert_eq!(bp2.abilities[2].flow_pattern, "prompted_branching");
    assert_eq!(bp2.abilities[2].frames[0].role, "prompt");
    assert_eq!(bp2.abilities[2].frames[1].role, "control");
    assert_eq!(bp2.abilities[2].frames[2].role, "effect");
    assert!(bp2.abilities[2].summary.contains("Choose"));

    let first_frame_value = serde_json::to_value(&bp1.abilities[0].frames[0])
        .expect("frame should serialize");
    let first_frame: crate::core::logic::ability_manifest::AbilityManifestFrame =
        serde_json::from_value(first_frame_value).expect("frame should deserialize");
    assert_eq!(first_frame.opcode, "RECOVER_MEMBER");

    let raw_member = card_db_lookup_member(&cards_payload, 9).expect("production card 9 should exist");
    let ability = raw_member
        .get("abilities")
        .and_then(|value| value.as_array())
        .and_then(|abilities| abilities.first())
        .expect("card 9 should have at least one ability");
    let raw_program = ability
        .get("frame_program")
        .expect("card 9 ability should have a frame program");
    let round_program: FrameProgram = serde_json::from_value(raw_program.clone())
        .expect("frame program should deserialize");
    let round_program_value = serde_json::to_value(&round_program)
        .expect("frame program should serialize");
    let round_program_again: FrameProgram = serde_json::from_value(round_program_value)
        .expect("frame program should deserialize again");
    assert_eq!(round_program.frames.len(), round_program_again.frames.len());

    let ability_value = db_member_ability(&cards_payload, 9, 1);
    let ability_round_trip: Ability = serde_json::from_value(ability_value.clone())
        .expect("ability should deserialize into Ability");
    let ability_round_trip_json = serde_json::to_value(&ability_round_trip)
        .expect("ability should serialize back to JSON");
    let ability_round_trip_again: Ability = serde_json::from_value(ability_round_trip_json)
        .expect("ability should round trip again");
    assert_eq!(ability_round_trip.trigger, ability_round_trip_again.trigger);
    assert!(ability_round_trip_again.frame_program.is_some());
}

fn card_db_lookup_member(cards_payload: &Value, card_id: i32) -> Option<&Value> {
    cards_payload
        .get("member_db")
        .and_then(|db| db.get(card_id.to_string()))
}

fn db_member_ability(cards_payload: &Value, card_id: i32, ability_index: usize) -> Value {
    card_db_lookup_member(cards_payload, card_id)
        .and_then(|card| card.get("abilities"))
        .and_then(|abilities| abilities.as_array())
        .and_then(|abilities| abilities.get(ability_index))
        .cloned()
        .expect("ability should exist")
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
    let metadata: Value =
        serde_json::from_str(METADATA_JSON).expect("Failed to parse metadata.json");

    assert_generated_constants_match(&metadata, "opcodes", "O_");
    assert_generated_constants_match(&metadata, "action_bases", "ACTION_BASE_");
    assert_generated_constants_match(&metadata, "conditions", "C_");
    assert_generated_constants_match(&metadata, "costs", "COST_");

    assert_generated_enum_match(&metadata, "triggers", enum_variant_name, GENERATED_ENUMS_RS);
    assert_generated_enum_match(
        &metadata,
        "targets",
        target_variant_name,
        GENERATED_ENUMS_RS,
    );
    assert_generated_enum_match(&metadata, "phases", enum_variant_name, GENERATED_ENUMS_RS);
}

fn assert_generated_constants_match(metadata: &Value, section: &str, prefix: &str) {
    for (key, value) in metadata_section(metadata, section) {
        let expected = value
            .as_i64()
            .unwrap_or_else(|| panic!("{section}.{key} is not numeric"));
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
        let expected = value
            .as_i64()
            .unwrap_or_else(|| panic!("{section}.{key} is not numeric"));
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
