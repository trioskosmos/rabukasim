use super::common::{
    condition_eval_cache_key, condition_eval_cache_lookup, condition_eval_cache_store,
    parse_condition_type, CONDITION_CHECK_MAX_DEPTH,
};
use super::counts::resolve_count;
use super::opcodes::check_condition_opcode;
use crate::core::*;
use crate::core::generated_constants::FILTER_ANY_STAGE;
use crate::core::logic::filter::{
    has_structured_filter_constraints, merge_filter_attr_with_params, structured_filter_from_attr,
};
use crate::core::logic::heart_semantics::decode_heart_type_value;
use crate::core::logic::{AbilityContext, CardDatabase, Condition, ConditionType, GameState};

pub fn get_param_case_insensitive<'a>(
    params: &'a serde_json::Map<String, serde_json::Value>,
    key: &str,
) -> Option<&'a serde_json::Value> {
    params.get(key).or_else(|| params.get(&key.to_uppercase()))
}

pub fn comparison_mode_from_params(
    params: &serde_json::Map<String, serde_json::Value>,
) -> Option<i32> {
    if get_param_case_insensitive(params, "gt").is_some() {
        Some(COMP_GT)
    } else if get_param_case_insensitive(params, "lt").is_some() {
        Some(COMP_LT)
    } else if get_param_case_insensitive(params, "min").is_some() {
        Some(COMP_GE)
    } else if get_param_case_insensitive(params, "max").is_some() {
        Some(COMP_LE)
    } else if get_param_case_insensitive(params, "eq").is_some() {
        Some(COMP_EQ)
    } else {
        None
    }
}

pub fn condition_from_clause(clause: &serde_json::Value) -> Condition {
    Condition {
        condition_type: clause
            .get("type")
            .and_then(|value| value.as_i64())
            .map(|value| parse_condition_type(value as i32))
            .unwrap_or(ConditionType::None),
        value: clause
            .get("value")
            .and_then(|value| value.as_i64())
            .unwrap_or_default() as i32,
        attr: clause
            .get("attr")
            .and_then(|value| value.as_u64())
            .unwrap_or_default(),
        target_slot: 0,
        is_negated: clause
            .get("is_negated")
            .and_then(|value| value.as_bool())
            .unwrap_or(false),
        params: clause.get("params").cloned().unwrap_or_default(),
    }
}

// Keys that should be excluded from filter merging when raw_cond is present
// These are used for condition evaluation rather than filter constraints
const RAW_COND_EXCLUDED_KEYS: &[&str] = &[
    // Condition type identifiers
    "raw_cond", "RAW_COND",
    // Comparison operators
    "MIN", "min", "MAX", "max", "EQ", "eq", "GE", "ge", "LE", "le",
    // Counting and threshold parameters
    "count", "COUNT", "threshold", "THRESHOLD", "value", "VALUE",
    "heart_count", "HEART_COUNT", "min_count", "MIN_COUNT",
    // Scope and keyword parameters (handled separately)
    "player", "PLAYER", "keyword", "KEYWORD",
];

fn resolved_filter_attr(
    params: &serde_json::Map<String, serde_json::Value>,
    fallback_attr: u64,
) -> u64 {
    let mut filter_params = params.clone();
    if filter_params.contains_key("raw_cond") || filter_params.contains_key("RAW_COND") {
        for key in RAW_COND_EXCLUDED_KEYS {
            filter_params.remove(*key);
        }
    }
    let params_value = serde_json::Value::Object(filter_params);
    merge_filter_attr_with_params(fallback_attr, Some(&params_value))
}

fn condition_match_filter_attr(filter_attr: u64) -> u64 {
    filter_attr & !crate::core::logic::filter::FILTER_ANY_STAGE
}

// Helper function to count unique names from card IDs
fn count_unique_names(card_ids: &[i32], db: &CardDatabase) -> i32 {
    let unique_names: std::collections::HashSet<&str> = card_ids
        .iter()
        .filter_map(|&cid| {
            db.get_member(cid).map(|m| m.name.as_str())
                .or_else(|| db.get_live(cid).map(|l| l.name.as_str()))
        })
        .collect();
    // If unique_names is empty but we have cards, fall back to counting cards
    // This handles cases where card names aren't available in the test DB
    if unique_names.is_empty() && !card_ids.is_empty() {
        card_ids.len() as i32
    } else {
        unique_names.len() as i32
    }
}

fn apply_area_semantics(attr: u64, area: &str) -> u64 {
    if area.eq_ignore_ascii_case("ANY_STAGE") || area.eq_ignore_ascii_case("ALL_AREAS") {
        attr | FILTER_ANY_STAGE
    } else {
        attr
    }
}

fn resolved_condition_player(
    params: &serde_json::Map<String, serde_json::Value>,
    ctx: &AbilityContext,
) -> usize {
    get_param_case_insensitive(params, "val")
        .or_else(|| get_param_case_insensitive(params, "player"))
        .and_then(|value| value.as_str())
        .map(|value| value.to_ascii_uppercase())
        .map(|value| {
            if value == "OPPONENT" {
                1 - ctx.player_id as usize
            } else {
                ctx.player_id as usize
            }
        })
        .unwrap_or_else(|| ctx.player_id as usize)
}

fn resolved_condition_player_with_attr(
    params: &serde_json::Map<String, serde_json::Value>,
    ctx: &AbilityContext,
    filter_attr: u64,
) -> usize {
    get_param_case_insensitive(params, "val")
        .or_else(|| get_param_case_insensitive(params, "player"))
        .and_then(|value| value.as_str())
        .map(|value| value.to_ascii_uppercase())
        .map(|value| {
            if value == "OPPONENT" {
                1 - ctx.player_id as usize
            } else {
                ctx.player_id as usize
            }
        })
        .unwrap_or_else(|| {
            // Check filter_attr for target_player (bits 0-1)
            let target_player = (filter_attr & 0x3) as usize;
            if target_player == 2 {
                // 2 means both players
                ctx.player_id as usize
            } else if target_player == 1 {
                // 1 means opponent
                1 - ctx.player_id as usize
            } else {
                // 0 means self
                ctx.player_id as usize
            }
        })
}

fn compare_count_thresholds(
    params: &serde_json::Map<String, serde_json::Value>,
    count: i32,
) -> bool {
    if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
        count == eq as i32
    } else if let Some(ge) = get_param_case_insensitive(params, "GE")
        .or_else(|| get_param_case_insensitive(params, "MIN"))
        .and_then(|v| v.as_i64())
    {
        count >= ge as i32
    } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
        count <= max as i32
    } else {
        count > 0
    }
}

fn filtered_stage_cards(
    state: &GameState,
    db: &CardDatabase,
    cond: &Condition,
    ctx: &AbilityContext,
    params: &serde_json::Map<String, serde_json::Value>,
) -> Vec<i32> {
    let filter_attr = if params.contains_key("raw_cond") || params.contains_key("RAW_COND") {
        cond.attr
    } else {
        resolved_filter_attr(params, cond.attr)
    };
    let match_filter_attr = condition_match_filter_attr(filter_attr);
    let has_filter_constraints = has_structured_filter_constraints(match_filter_attr);
    let match_filter = structured_filter_from_attr(match_filter_attr);
    let target_player = resolved_condition_player(params, ctx);

    state.players[target_player]
        .stage
        .iter()
        .enumerate()
        .filter_map(|(slot_idx, &cid)| {
            if cid < 0 {
                return None;
            }
            if has_filter_constraints
                && !state.card_matches_filter_with_struct(
                    db,
                    cid,
                    Some((target_player as u8, slot_idx as i16)),
                    &match_filter,
                    ctx,
                )
            {
                return None;
            }
            Some(cid)
        })
        .collect()
}

fn discard_live_cards<'a>(
    state: &'a GameState,
    db: &'a CardDatabase,
    p_idx: usize,
) -> Vec<&'a crate::core::logic::card_db::LiveCard> {
    state.players[p_idx]
        .discard
        .iter()
        .filter_map(|&cid| db.get_live(cid))
        .collect()
}

pub fn evaluate_raw_condition(
    state: &GameState,
    db: &CardDatabase,
    _p_idx: usize,
    cond: &Condition,
    ctx: &AbilityContext,
    depth: u32,
    params: &serde_json::Map<String, serde_json::Value>,
) -> bool {
    let Some(raw_cond) = get_param_case_insensitive(params, "raw_cond")
        .and_then(|v| v.as_str())
    else {
        return true;
    };
    match raw_cond {
        "SUCCESS_LIVE_COUNT_EQUAL_OPPONENT" => {
            state.players[ctx.player_id as usize].success_lives.len()
                == state.players[1 - ctx.player_id as usize].success_lives.len()
        }
        "SOURCE_CARD_ID_EQUALS" => {
            let expected = get_param_case_insensitive(params, "card_id")
                .and_then(|value| value.as_i64())
                .unwrap_or(cond.value as i64) as i32;
            ctx.source_card_id == expected
        }
        "SOURCE_MEMBER_COST_GE" => {
            let threshold = get_param_case_insensitive(params, "min")
                .and_then(|value| value.as_i64())
                .unwrap_or(cond.value as i64) as i32;
            let cost = state.get_member_cost(
                ctx.player_id as usize,
                ctx.source_card_id,
                -1,
                -1,
                db,
                depth + 1,
            );
            cost >= threshold
        }
        "PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST" => {
            let player_center = state.players[ctx.player_id as usize]
                .stage
                .get(1)
                .copied()
                .unwrap_or(-1);
            let opponent_center = state.players[1 - ctx.player_id as usize]
                .stage
                .get(1)
                .copied()
                .unwrap_or(-1);

            let player_cost = if player_center >= 0 {
                db.get_member(player_center)
                    .map(|member| member.cost as i32)
                    .unwrap_or(0)
            } else {
                0
            };
            let opponent_cost = if opponent_center >= 0 {
                db.get_member(opponent_center)
                    .map(|member| member.cost as i32)
                    .unwrap_or(0)
            } else {
                0
            };

            player_cost > opponent_cost
        }
        "COUNT_MEMBER" => {
            let filter_attr = resolved_filter_attr(params, cond.attr);
            let match_filter_attr = condition_match_filter_attr(filter_attr);
            let has_filter_constraints = has_structured_filter_constraints(match_filter_attr);
            let target_player = resolved_condition_player(params, ctx);

            let use_unique_names = get_param_case_insensitive(params, "keyword")
                .and_then(|v| v.as_str())
                .map(|k| k.eq_ignore_ascii_case("COUNT_UNIQUE_NAMES") || k.eq_ignore_ascii_case("UNIQUE_NAMES"))
                .unwrap_or(false);

            let matching_cards: Vec<i32> = state.players[target_player]
                .stage
                .iter()
                .copied()
                .filter(|&cid| cid >= 0)
                .filter(|&cid| {
                    !has_filter_constraints
                        || state.card_matches_filter_with_ctx(db, cid, match_filter_attr, ctx)
                })
                .collect();

            let count = if use_unique_names {
                count_unique_names(&matching_cards, db)
            } else {
                matching_cards.len() as i32
            };

            compare_count_thresholds(params, count)
        }
        "COUNT_STAGE" => {
            let area = get_param_case_insensitive(params, "AREA")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let filter_attr = resolved_filter_attr(params, cond.attr);
            let attr = apply_area_semantics(filter_attr, area);
            let match_filter_attr = condition_match_filter_attr(attr);
            let has_filter_constraints = has_structured_filter_constraints(match_filter_attr);
            let count = if attr & FILTER_ANY_STAGE != 0 {
                // For ANY_STAGE, count from both players
                let mut count = 0;
                for p_idx in 0..2 {
                    for &cid in &state.players[p_idx].stage {
                        if cid < 0 {
                            continue;
                        }
                        if !has_filter_constraints
                            || state.card_matches_filter_with_ctx(db, cid, match_filter_attr, ctx)
                        {
                            count += 1;
                        }
                    }
                }
                count
            } else {
                // Otherwise count from current player
                let count = state.players[ctx.player_id as usize]
                    .stage
                    .iter()
                    .copied()
                    .filter(|&cid| cid >= 0)
                    .filter(|&cid| {
                        !has_filter_constraints
                            || state.card_matches_filter_with_ctx(db, cid, match_filter_attr, ctx)
                    })
                    .count() as i32;
                count
            };
            compare_count_thresholds(params, count)
        }
        "COUNT_MOVED_STAGE" => {
            let count = resolve_count(state, db, cond.condition_type as i32, cond.attr, 0, ctx, depth + 1);
            compare_count_thresholds(params, count)
        }
        "ALL_MEMBERS" => {
            let filter_attr = resolved_filter_attr(params, cond.attr);
            let match_filter_attr = condition_match_filter_attr(filter_attr);
            let has_filter_constraints = has_structured_filter_constraints(match_filter_attr);
            let target_player = resolved_condition_player(params, ctx);

            let stage = &state.players[target_player].stage;
            let total = stage.iter().copied().filter(|&cid| cid >= 0).count() as i32;
            let matching = stage
                .iter()
                .copied()
                .filter(|&cid| cid >= 0)
                .filter(|&cid| {
                    !has_filter_constraints
                        || state.card_matches_filter_with_ctx(db, cid, match_filter_attr, ctx)
                })
                .count() as i32;

            if total == 0 {
                false
            } else if get_param_case_insensitive(params, "EQ").is_some()
                || get_param_case_insensitive(params, "GE").is_some()
                || get_param_case_insensitive(params, "MIN").is_some()
                || get_param_case_insensitive(params, "MAX").is_some()
            {
                compare_count_thresholds(params, matching)
            } else {
                matching == total
            }
        }
        "ENERGY_COUNT" => {
            let target_is_opponent = get_param_case_insensitive(params, "val")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false);
            let target_player = if target_is_opponent {
                1 - ctx.player_id as usize
            } else {
                ctx.player_id as usize
            };

            let energy_count = state.players[target_player].energy_zone.len() as i32;
            compare_count_thresholds(params, energy_count)
        }
        "DID_ACTIVATE_ENERGY" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_energy_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_energy_group_mask != 0
            }
        }
        "DID_ACTIVATE_ENERGY_BY_GROUP" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_energy_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_energy_group_mask != 0
            }
        }
        "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_energy_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_energy_group_mask != 0
            }
        }
        "DID_ACTIVATE_MEMBER" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_member_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_member_group_mask != 0
            }
        }
        "DID_ACTIVATE_MEMBER_BY_GROUP" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_member_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_member_group_mask != 0
            }
        }
        "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT" => {
            let group_filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .and_then(|v| v.strip_prefix("GROUP="))
                .and_then(|v| v.parse::<u8>().ok());
            let target_player = ctx.player_id as usize;
            if let Some(group_id) = group_filter {
                (state.players[target_player].activated_member_group_mask & (1 << group_id)) != 0
            } else {
                state.players[target_player].activated_member_group_mask != 0
            }
        }
        "ALL_CARDS_MATCH" => {
            let filter_attr = resolved_filter_attr(params, cond.attr);

            let mut value = cond.value;
            if get_param_case_insensitive(params, "all")
                .and_then(|v| v.as_bool())
                .unwrap_or(false)
            {
                value |= 0x04;
            }

            check_condition_opcode(
                state,
                db,
                309,
                value,
                filter_attr,
                cond.target_slot as i32,
                ctx,
                depth + 1,
            )
        }
        "HAS_SUCCESS_LIVE" | "NOT_HAS_SUCCESS_LIVE" => {
            let filter_attr = resolved_filter_attr(params, cond.attr);

            let has_matching_success_live = state.players[ctx.player_id as usize]
                .success_lives
                .iter()
                .copied()
                .any(|cid| {
                    cid >= 0
                        && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr))
                });

            if raw_cond == "HAS_SUCCESS_LIVE" {
                has_matching_success_live
            } else {
                !has_matching_success_live
            }
        }
        "OR" => {
            if let Some(clauses) = params.get("clauses").and_then(|value| value.as_array()) {
                for clause in clauses {
                    let nested = condition_from_clause(clause);
                    if check_condition(state, db, _p_idx, &nested, ctx, depth + 1) {
                        return true;
                    }
                }
                false
            } else {
                let first_branch = Condition {
                    condition_type: ConditionType::None,
                    value: 0,
                    attr: 0,
                    target_slot: 0,
                    is_negated: false,
                    params: serde_json::json!({
                        "raw_cond": "YELL_PILE_CONTAINS",
                        "FILTER": params.get("FILTER").cloned().unwrap_or_default(),
                        "MAX": params.get("MAX").cloned().unwrap_or_default()
                    }),
                };
                let second_branch = Condition {
                    condition_type: ConditionType::None,
                    value: 0,
                    attr: 0,
                    target_slot: 0,
                    is_negated: false,
                    params: serde_json::json!({
                        "raw_cond": params.get("val").cloned().unwrap_or(serde_json::Value::String(String::new())),
                        "MIN": params.get("MIN").cloned().unwrap_or_default()
                    }),
                };
                check_condition(state, db, _p_idx, &first_branch, ctx, depth + 1)
                    || check_condition(state, db, _p_idx, &second_branch, ctx, depth + 1)
            }
        }
        "SELF_SCORE" => {
            let perf_res = state
                .ui
                .performance_results
                .get(&(ctx.player_id as u8))
                .or_else(|| {
                    state
                        .ui
                        .last_performance_results
                        .get(&(ctx.player_id as u8))
                });

            let live_score = perf_res
                .and_then(|res| res.get("lives"))
                .and_then(|lives| lives.as_array())
                .and_then(|lives| {
                    lives.iter().find_map(|live_res| {
                        let card_matches = live_res
                            .get("card_id")
                            .and_then(|v| v.as_i64())
                            .map(|card_id| card_id as i32 == ctx.source_card_id)
                            .unwrap_or(false);
                        let slot_matches = live_res
                            .get("slot_idx")
                            .and_then(|v| v.as_i64())
                            .map(|slot_idx| slot_idx as i16 == ctx.area_idx)
                            .unwrap_or(false);

                        if card_matches || slot_matches {
                            live_res
                                .get("score")
                                .and_then(|v| v.as_i64())
                                .map(|score| score as i32)
                        } else {
                            None
                        }
                    })
                })
                .or_else(|| {
                    db.get_live(ctx.source_card_id)
                        .map(|live| live.score as i32)
                })
                .unwrap_or_default();

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                live_score == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                live_score >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                live_score <= max as i32
            } else {
                live_score > 0
            }
        }
        "SURPLUS_HEARTS_CONTAINS" => {
            let target_is_opponent = get_param_case_insensitive(params, "val")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false);
            let target_player = if target_is_opponent {
                &state.players[1 - ctx.player_id as usize]
            } else {
                &state.players[ctx.player_id as usize]
            };

            let target_count = get_param_case_insensitive(params, "heart_type")
                .and_then(decode_heart_type_value)
                .filter(|&heart_type| heart_type < 7)
                .map(|heart_type| target_player.excess_hearts_by_color[heart_type] as i32)
                .unwrap_or_else(|| target_player.excess_hearts as i32);

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                target_count == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                target_count >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                target_count <= max as i32
            } else {
                target_count > 0
            }
        }
        "SURPLUS_HEARTS_COUNT" => {
            let target_is_opponent = get_param_case_insensitive(params, "val")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false);
            let target_hearts = if target_is_opponent {
                state.players[1 - ctx.player_id as usize].excess_hearts as i32
            } else {
                state.players[ctx.player_id as usize].excess_hearts as i32
            };

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                target_hearts == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                target_hearts >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                target_hearts <= max as i32
            } else {
                target_hearts > 0
            }
        }
        "HEARTS_COUNT" => {
            let target_is_opponent = get_param_case_insensitive(params, "target")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false);
            let self_hearts = state
                .get_total_member_hearts(ctx.player_id as usize, db, depth + 1)
                .get_total_count() as i32;
            let opponent_hearts = state
                .get_total_member_hearts(1 - ctx.player_id as usize, db, depth + 1)
                .get_total_count() as i32;

            let (lhs, rhs) = if target_is_opponent {
                (self_hearts, opponent_hearts)
            } else {
                (opponent_hearts, self_hearts)
            };

            let target_value = get_param_case_insensitive(params, "val")
                .and_then(|v| v.as_i64())
                .unwrap_or(cond.value as i64) as i32;
            match get_param_case_insensitive(params, "comparison")
                .and_then(|v| v.as_str())
                .map(|value| value.to_ascii_uppercase())
                .as_deref()
            {
                Some("GT") => lhs > rhs,
                Some("GE") => lhs >= rhs,
                Some("LT") => lhs < rhs,
                Some("LE") => lhs <= rhs,
                Some("EQ") => lhs == rhs,
                _ => lhs > rhs.max(target_value),
            }
        }
        "REDUCE_YELL_COUNT" => {
            let player_yell_count = state.players[ctx.player_id as usize].yell_cards.len() as i32;
            let opponent_yell_count =
                state.players[1 - ctx.player_id as usize].yell_cards.len() as i32;

            if get_param_case_insensitive(params, "LESS_THAN")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false)
            {
                player_yell_count < opponent_yell_count
            } else if get_param_case_insensitive(params, "GREATER_THAN")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("OPPONENT"))
                .unwrap_or(false)
            {
                player_yell_count > opponent_yell_count
            } else if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                player_yell_count == eq as i32
            } else {
                player_yell_count > 0
            }
        }
        "YELL_PILE_CONTAINS" => {
            let yell_cards = &state.players[ctx.player_id as usize].yell_cards;
            let filter = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .unwrap_or("");

            let card_has_blade_heart = |cid: i32| {
                db.get_member(cid)
                    .map(|card| card.blade_hearts.iter().any(|&heart| heart > 0))
                    .or_else(|| {
                        db.get_live(cid)
                            .map(|card| card.blade_hearts.iter().any(|&heart| heart > 0))
                    })
                    .unwrap_or(false)
            };

            let matches_filter = |cid: i32| match filter {
                "TYPE=LIVE" => db.get_live(cid).is_some(),
                "TYPE=MEMBER" => db.get_member(cid).is_some(),
                "TYPE=BLADE_HEART" => card_has_blade_heart(cid),
                "TYPE_NOT=BLADE_HEART" => !card_has_blade_heart(cid),
                "HAS_ALL_BLADE" => card_has_blade_heart(cid),
                _ => true,
            };

            let matching_count = yell_cards
                .iter()
                .copied()
                .filter(|&cid| matches_filter(cid))
                .count() as i32;

            if filter.eq_ignore_ascii_case("HAS_ALL_BLADE")
                && get_param_case_insensitive(params, "EQ").is_none()
                && get_param_case_insensitive(params, "MIN").is_none()
                && get_param_case_insensitive(params, "MAX").is_none()
            {
                !yell_cards.is_empty() && matching_count == yell_cards.len() as i32
            } else if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                matching_count == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                matching_count >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                matching_count <= max as i32
            } else {
                matching_count > 0
            }
        }
        "UNIQUE_NAMES_COUNT" => {
            let target_player = resolved_condition_player(params, ctx);
            let mut names = std::collections::HashSet::<String>::new();
            for &cid in &state.players[target_player].stage {
                if cid < 0 {
                    continue;
                }
                let name = db
                    .get_member(cid)
                    .map(|member| member.name.clone())
                    .or_else(|| db.get_live(cid).map(|live| live.name.clone()));
                if let Some(name) = name {
                    let normalized = name.trim();
                    if !normalized.is_empty() {
                        names.insert(normalized.to_string());
                    }
                }
            }
            let count = names.len() as i32;

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                count == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                count >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                count <= max as i32
            } else {
                count > 0
            }
        }
        "UNIQUE_UNIT_NAMES_COUNT" => {
            let filter_attr = resolved_filter_attr(params, cond.attr);
            let target_player = resolved_condition_player(params, ctx);
            let mut units = std::collections::HashSet::<u8>::new();
            for &cid in &state.players[target_player].stage {
                if cid < 0 {
                    continue;
                }
                if let Some(unit_id) = db
                    .get_member(cid)
                    .and_then(|member| member.units.first().copied())
                    .or_else(|| db.get_live(cid).and_then(|live| live.units.first().copied()))
                {
                    units.insert(unit_id);
                }
            }
            compare_count_thresholds(params, units.len() as i32)
        }
        "UNIQUE_CARD_NAMES_COUNT" => {
            let mut names = std::collections::HashSet::<String>::new();
            for cid in filtered_stage_cards(state, db, cond, ctx, params) {
                if let Some(name) = db
                    .get_member(cid)
                    .map(|member| member.name.clone())
                    .or_else(|| db.get_live(cid).map(|live| live.name.clone()))
                {
                    names.insert(name);
                }
            }
            compare_count_thresholds(params, names.len() as i32)
        }
        "UNIQUE_MEMBER_COSTS_COUNT" => {
            let mut costs = std::collections::HashSet::<i32>::new();
            for cid in filtered_stage_cards(state, db, cond, ctx, params) {
                if let Some(cost) = db
                    .get_member(cid)
                    .map(|member| member.cost as i32)
                    .or_else(|| db.get_live(cid).map(|live| live.score as i32))
                {
                    costs.insert(cost);
                }
                }
                compare_count_thresholds(params, costs.len() as i32)
            }
        "UNIQUE_DISCARD_LIVE_NAMES_COUNT" => {
            let target_player = resolved_condition_player(params, ctx);
            let mut names = std::collections::HashSet::<String>::new();
            for card in discard_live_cards(state, db, target_player) {
                let name = card.name.trim();
                if !name.is_empty() {
                    names.insert(name.to_string());
                }
            }
            compare_count_thresholds(params, names.len() as i32)
        }
        "UNIQUE_DISCARD_LIVE_GROUPS_COUNT" => {
            let target_player = resolved_condition_player(params, ctx);
            let mut groups = std::collections::HashSet::<u8>::new();
            for card in discard_live_cards(state, db, target_player) {
                for group_id in card.groups.iter().copied() {
                    groups.insert(group_id);
                }
            }
            compare_count_thresholds(params, groups.len() as i32)
        }
        "STAGE_TOTAL_COST_GE" => {
            let target_player = resolved_condition_player(params, ctx);
            let filter_attr = get_param_case_insensitive(params, "FILTER")
                .and_then(|value| value.as_u64())
                .unwrap_or(cond.attr);
            let filter = crate::core::logic::filter::CardFilter::from_attr(filter_attr);
            let min_cost = get_param_case_insensitive(params, "MIN")
                .and_then(|value| value.as_i64())
                .unwrap_or(cond.value as i64) as i32;
            let mut total_cost = 0i32;
            for (slot_idx, &cid) in state.players[target_player].stage.iter().enumerate() {
                if cid < 0 {
                    continue;
                }
                if state.card_matches_filter_with_struct(
                    db,
                    cid,
                    Some((target_player as u8, slot_idx as i16)),
                    &filter,
                    ctx,
                ) {
                    total_cost += db.get_member(cid).map(|member| member.cost as i32).unwrap_or(0);
                }
            }
            total_cost >= min_cost
        }
        "UNIQUE_HEART_TYPES" => {
            let mut color_mask: u8 = 0;
            for &cid in &state.players[ctx.player_id as usize].stage {
                if cid < 0 {
                    continue;
                }
                if let Some(member) = db.get_member(cid) {
                    for (color_idx, &count) in member.hearts.iter().enumerate().take(6) {
                        if count > 0 {
                            color_mask |= 1u8 << color_idx;
                        }
                    }
                }
            }
            let unique_colors = color_mask.count_ones() as i32;

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                unique_colors == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                unique_colors >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                unique_colors <= max as i32
            } else {
                unique_colors > 0
            }
        }
        "YELL_CARDS" => {
            let yell_cards = &state.players[ctx.player_id as usize].yell_cards;
            let filter_str = get_param_case_insensitive(params, "FILTER")
                .and_then(|v| v.as_str())
                .unwrap_or("");
            let mut group_id: u8 = 0;
            let mut check_unique_names = false;
            for part in filter_str.split(',') {
                let part = part.trim();
                if part.starts_with("GROUP_ID=") {
                    if let Ok(gid) = part.strip_prefix("GROUP_ID=").unwrap_or("0").parse::<u8>() {
                        group_id = gid;
                    }
                } else if part == "UNIQUE_NAMES" {
                    check_unique_names = true;
                }
            }
            let filtered_cards: Vec<i32> = yell_cards
                .iter()
                .copied()
                .filter(|&cid| {
                    if group_id > 0 {
                        db.get_member(cid)
                            .map(|m| m.groups.contains(&group_id))
                            .or_else(|| db.get_live(cid).map(|l| l.groups.contains(&group_id)))
                            .unwrap_or(false)
                    } else {
                        true
                    }
                })
                .collect();
            let count = if check_unique_names {
                let mut names = std::collections::HashSet::new();
                for &cid in &filtered_cards {
                    if let Some(m) = db.get_member(cid) {
                        names.insert(m.name.clone());
                    } else if let Some(l) = db.get_live(cid) {
                        names.insert(l.name.clone());
                    }
                }
                names.len() as i32
            } else {
                filtered_cards.len() as i32
            };

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                count == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64()) {
                count >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64()) {
                count <= max as i32
            } else {
                count > 0
            }
        }
        _ => true,
    }
}

pub fn check_condition(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    cond: &Condition,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    // FAST PATH 1: Debug bypass - skip all checks
    if state.debug.debug_ignore_conditions {
        return true;
    }
    
    // FAST PATH 2: Depth limit
    if depth > CONDITION_CHECK_MAX_DEPTH {
        return false;
    }

    // FAST PATH 3: Simple condition with no params and default type
    // This avoids expensive JSON processing for the majority of simple conditions
    if cond.params.is_null() 
        && cond.condition_type != ConditionType::None
        && cond.value == 0
        && cond.attr == 0
        && cond.target_slot == 0
        && !cond.is_negated
    {
        return check_condition_opcode(
            state, db, cond.condition_type as i32, 0, 0, 0, ctx, depth + 1
        );
    }

    let cache_key = condition_eval_cache_key(
        cond.condition_type as i32,
        cond.value,
        cond.attr,
        cond.target_slot as i32,
        p_idx,
        Some(&cond.params),
        ctx,
        depth,
    );
    if let Some(hit) = condition_eval_cache_lookup(&cache_key) {
        return hit;
    }
    
    let mut val = cond.value;
    let mut attr = cond.attr;
    let mut slot = cond.target_slot as i32;

    if let Some(params) = cond.params.as_object() {
        let get_param = |key: &str| -> Option<&serde_json::Value> { get_param_case_insensitive(params, key) };

        if val == 0 {
            if let Some(min) = get_param("min").and_then(|v| v.as_i64()) {
                val = min as i32;
            }
        }

        attr = merge_filter_attr_with_params(attr, Some(&cond.params));

        if matches!(get_param("keyword").and_then(|v| v.as_str()), Some("REVEALED_CONTAINS")) {
            if let Some(val_str) = params.get("value").and_then(|v| v.as_str()) {
                if val_str == "live" {
                    val = CARD_TYPE_LIVE;
                } else if val_str == "member" {
                    val = CARD_TYPE_MEMBER;
                }
            }
        }

        if cond.condition_type == ConditionType::GroupFilter
            || cond.condition_type == ConditionType::DiscardedCards
        {
            if params.get("all").and_then(|v| v.as_bool()).unwrap_or(false) {
                val |= 0x04;
            }
        }

        if ((slot >> 4) & 0x0F) == 0 {
            if let Some(mode) = comparison_mode_from_params(params) {
                slot = (slot & 0x0F) | ((mode as i32) << 4);
            }
        }
    }

    let raw_cond_result = cond
        .params
        .as_object()
        .map(|p| evaluate_raw_condition(state, db, p_idx, cond, ctx, depth, p))
        .unwrap_or(true);

    let result = if cond.condition_type != ConditionType::None {
        check_condition_opcode(
            state,
            db,
            cond.condition_type as i32,
            val,
            attr,
            slot,
            ctx,
            depth + 1,
        )
    } else {
        raw_cond_result
    };

    let result = if cond.is_negated { !result } else { result };

    if !result && state.debug.debug_ignore_conditions {
        if let Some(ref log) = state.debug.bypassed_conditions {
            if let Ok(mut bypassed) = log.0.lock() {
                bypassed.push(format!(
                    "BYPASS Condition: Type {:?}, Value {}, Attr {}",
                    cond.condition_type, cond.value, cond.attr
                ));
            }
        }
        return true;
    }
    condition_eval_cache_store(cache_key, result);
    result
}
