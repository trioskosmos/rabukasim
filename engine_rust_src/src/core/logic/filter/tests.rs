use super::*;
use crate::core::logic::card_db::{LiveCard, MemberCard};
use serde_json::json;

fn test_db_with_runtime_cards() -> CardDatabase {
    let mut db = CardDatabase::default();

    let mut muse_member = MemberCard::default();
    muse_member.card_id = 100;
    muse_member.name = "Muse Setsuna".to_string();
    muse_member.normalized_name = "MuseSetsuna".to_string();
    muse_member.cost = 3;
    muse_member.hearts = [1, 1, 0, 0, 0, 0, 0];
    muse_member.groups = vec![0];
    muse_member.units = vec![5];
    muse_member.char_mask = (1u128 << 27) | (1u128 << 32);
    muse_member.semantic_flags = 0x100;
    db.members.insert(100, muse_member.clone());

    let mut blade_live = LiveCard::default();
    blade_live.card_id = 200;
    blade_live.name = "Blade Live".to_string();
    blade_live.normalized_name = "BladeLive".to_string();
    blade_live.required_hearts = [2, 2, 0, 0, 0, 0, 0];
    blade_live.blade_hearts = [0, 0, 0, 0, 1, 0, 0];
    blade_live.groups = vec![1, 11];
    blade_live.units = vec![5];
    blade_live.char_mask = 1u128 << 32;
    db.lives.insert(200, blade_live.clone());

    db
}

#[test]
fn filter_parts_from_params_support_keyword_area_and_player_aliases() {
    let params = json!({
        "player": "OPPONENT",
        "area": "ANY_STAGE",
        "keyword": "COUNT_UNIQUE_NAMES"
    });

    let (filter, extras) = filter_parts_from_params(Some(&params)).unwrap();

    assert_eq!(filter.target_player, TARGET_PLAYER_OPPONENT as u8);
    assert!(filter.unique_names);
    assert_ne!(extras & FILTER_ANY_STAGE, 0);
}

#[test]
fn merge_filter_attr_with_params_preserves_passthrough_and_overlays_filter_bits() {
    let base_attr = FILTER_REVEALED_CONTEXT | TARGET_PLAYER_SELF as u64;
    let params = json!({
        "player": "OPPONENT",
        "keyword": "DID_ACTIVATE_MEMBER",
        "group_id": 3
    });

    let merged = merge_filter_attr_with_params(base_attr, Some(&params));
    let merged_filter = CardFilter::from_attr(merged);

    assert_eq!(merged_filter.target_player, TARGET_PLAYER_OPPONENT as u8);
    assert!(merged_filter.keyword_member);
    assert!(merged_filter.group_enabled);
    assert_eq!(merged_filter.group_id, 3);
    assert_ne!(merged & FILTER_REVEALED_CONTEXT, 0);
}

#[test]
fn filter_parts_from_params_support_character_name_lists() {
    let params = json!({
        "filter": "Umi/Yoshiko/Rina"
    });

    let (filter, extras) = filter_parts_from_params(Some(&params)).unwrap();

    assert_eq!(extras, 0);
    assert_eq!(filter.char_id_1, 4);
    assert_eq!(filter.char_id_2, 16);
    assert_eq!(filter.char_id_3, 29);
}

#[test]
fn matches_enforces_group_char_zone_and_flag_filters() {
    let db = test_db_with_runtime_cards();
    let mut state = GameState::default();
    state.players[0].stage[0] = 100;
    state.players[0].discard.push(200);

    let ctx = AbilityContext {
        player_id: 0,
        source_card_id: 999,
        selected_cards: vec![200].into(),
        ..AbilityContext::default()
    };

    let muse_group = CardFilter {
        is_enabled: true,
        group_enabled: true,
        group_id: 0,
        ..CardFilter::default()
    };
    assert!(muse_group.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

    let char_filter = CardFilter {
        is_enabled: true,
        char_id_1: 27,
        ..CardFilter::default()
    };
    assert!(char_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
    assert!(!char_filter.matches(&state, &db, 200, None, false, None, &ctx));

    let setsuna_filter = CardFilter {
        is_enabled: true,
        is_setsuna: true,
        ..CardFilter::default()
    };
    assert!(setsuna_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
    assert!(!setsuna_filter.matches(&state, &db, 200, None, false, None, &ctx));

    let discard_zone_filter = CardFilter {
        is_enabled: true,
        zone_mask: ZONE_DISCARD as u8,
        ..CardFilter::default()
    };
    assert!(discard_zone_filter.matches(&state, &db, 200, None, false, None, &ctx));
    assert!(!discard_zone_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

    let selected_discard_filter = CardFilter {
        is_enabled: true,
        special_id: 6,
        ..CardFilter::default()
    };
    assert!(selected_discard_filter.matches(&state, &db, 200, None, false, None, &ctx));
    assert!(!selected_discard_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

    let blade_filter = CardFilter {
        is_enabled: true,
        has_blade_heart: true,
        ..CardFilter::default()
    };
    assert!(blade_filter.matches(&state, &db, 200, None, false, None, &ctx));
    assert!(!blade_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

    let selected_group_filter = CardFilter {
        is_enabled: true,
        special_id: 7,
        ..CardFilter::default()
    };
    assert!(selected_group_filter.matches(&state, &db, 200, None, false, None, &ctx));
    assert!(!selected_group_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
}

#[test]
fn matches_uses_member_cost_even_with_effective_hearts() {
    let mut db = CardDatabase::default();
    let mut member = MemberCard::default();
    member.card_id = 300;
    member.cost = 4;
    member.hearts = [0, 0, 0, 0, 0, 0, 0];
    db.members.insert(300, member);

    let state = GameState::default();
    let ctx = AbilityContext::default();
    let filter = CardFilter {
        is_enabled: true,
        value_enabled: true,
        value_threshold: 4,
        is_cost_type: true,
        ..CardFilter::default()
    };
    let inflated_hearts = [9, 9, 9, 9, 9, 9, 9];

    assert!(filter.matches(&state, &db, 300, None, false, Some(&inflated_hearts), &ctx));

    let strict_filter = CardFilter {
        value_threshold: 3,
        is_le: true,
        ..filter
    };
    assert!(!strict_filter.matches(&state, &db, 300, None, false, Some(&inflated_hearts), &ctx));
}

#[test]
fn filter_parts_from_params_parse_string_special_and_zone_masks() {
    let params = json!({
        "special_id": "Selected Discard Group",
        "zone_mask": "DISCARD",
        "player": "OPPONENT"
    });

    let (filter, _) = filter_parts_from_params(Some(&params)).unwrap();

    assert_eq!(filter.special_id, 7);
    assert_eq!(filter.zone_mask, ZONE_DISCARD as u8);
    assert_eq!(filter.target_player, TARGET_PLAYER_OPPONENT as u8);
}

#[test]
fn filter_parts_from_params_parse_named_group_unit_character_and_color_values() {
    let params = json!({
        "group_id": "HASUNOSORA",
        "unit_id": "DOLLCHESTRA",
        "char_id_1": "RURINO",
        "color_mask": "RED|BLUE|ANY"
    });

    let (filter, _) = filter_parts_from_params(Some(&params)).unwrap();

    assert_eq!(filter.group_id, 4);
    assert_eq!(filter.unit_id, 14);
    assert_eq!(filter.char_id_1, 65);
    assert_eq!(filter.color_mask, (1 << 1) | (1 << 4) | (1 << 6));
}

#[test]
fn unknown_string_enums_are_ignored_instead_of_falling_back_to_zero() {
    assert_eq!(parse_target_player_value(&json!("not-a-player")), None);
    assert_eq!(parse_card_type_value(&json!("not-a-type")), None);
    assert_eq!(parse_special_id_value(&json!("not-a-special")), None);
}
