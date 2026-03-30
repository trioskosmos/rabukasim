use super::common::{parse_condition_type, CONDITION_CHECK_MAX_DEPTH};
use super::opcodes::check_condition_opcode;
use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
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
    if get_param_case_insensitive(params, "gt")
        .or_else(|| get_param_case_insensitive(params, "greater_than"))
        .is_some()
    {
        Some(COMP_GT)
    } else if get_param_case_insensitive(params, "lt")
        .or_else(|| get_param_case_insensitive(params, "less_than"))
        .is_some()
    {
        Some(COMP_LT)
    } else if get_param_case_insensitive(params, "min").is_some() {
        Some(COMP_GE)
    } else if get_param_case_insensitive(params, "max").is_some() {
        Some(COMP_LE)
    } else if get_param_case_insensitive(params, "eq")
        .or_else(|| get_param_case_insensitive(params, "equal"))
        .is_some()
    {
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
        .or_else(|| get_param_case_insensitive(params, "RAW_COND"))
        .and_then(|v| v.as_str())
    else {
        return true;
    };
    match raw_cond {
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
            let filter_attr = get_param_case_insensitive(params, "FILTER")
                .or_else(|| get_param_case_insensitive(params, "filter"))
                .and_then(|value| value.as_str())
                .map(map_filter_string_to_attr)
                .filter(|&attr| attr != 0)
                .unwrap_or(cond.attr);

            let target_player = get_param_case_insensitive(params, "val")
                .or_else(|| get_param_case_insensitive(params, "player"))
                .and_then(|value| value.as_str())
                .map(|value| value.to_ascii_uppercase())
                .map(|value| match value.as_str() {
                    "OPPONENT" => 1 - ctx.player_id as usize,
                    "BOTH" | "ALL" | "PLAYER" | "SELF" => ctx.player_id as usize,
                    _ => ctx.player_id as usize,
                })
                .unwrap_or(ctx.player_id as usize);

            let count = state.players[target_player]
                .stage
                .iter()
                .copied()
                .filter(|&cid| cid >= 0)
                .filter(|&cid| {
                    filter_attr == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
                })
                .count() as i32;

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                count == eq as i32
            } else if let Some(ge) =
                get_param_case_insensitive(params, "GE").and_then(|v| v.as_i64())
            {
                count >= ge as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                count <= max as i32
            } else {
                count > 0
            }
        }
        "COUNT_STAGE" => {
            let mut filter_attr = get_param_case_insensitive(params, "FILTER")
                .or_else(|| get_param_case_insensitive(params, "filter"))
                .and_then(|value| value.as_str())
                .map(map_filter_string_to_attr)
                .filter(|&attr| attr != 0)
                .unwrap_or(cond.attr);

            if let Some(area) = get_param_case_insensitive(params, "AREA")
                .or_else(|| get_param_case_insensitive(params, "area"))
                .and_then(|v| v.as_str())
            {
                if area.eq_ignore_ascii_case("ANY_STAGE") || area.eq_ignore_ascii_case("ALL_AREAS")
                {
                    filter_attr = (filter_attr & !0x3) | (TARGET_PLAYER_BOTH as u64);
                }
            }

            let mut value = cond.value;
            if value == 0 {
                if let Some(min) =
                    get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
                {
                    value = min as i32;
                } else if let Some(eq) =
                    get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64())
                {
                    value = eq as i32;
                } else if let Some(max) =
                    get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
                {
                    value = max as i32;
                }
            }

            check_condition_opcode(
                state,
                db,
                203,
                value,
                filter_attr,
                cond.target_slot as i32,
                ctx,
                depth + 1,
            )
        }
        "ALL_MEMBERS" => {
            let filter_attr = get_param_case_insensitive(params, "FILTER")
                .or_else(|| get_param_case_insensitive(params, "filter"))
                .and_then(|value| value.as_str())
                .map(map_filter_string_to_attr)
                .filter(|&attr| attr != 0)
                .unwrap_or(cond.attr);

            let target_player = get_param_case_insensitive(params, "val")
                .or_else(|| get_param_case_insensitive(params, "player"))
                .and_then(|value| value.as_str())
                .map(|value| value.to_ascii_uppercase())
                .map(|value| match value.as_str() {
                    "OPPONENT" => 1 - ctx.player_id as usize,
                    "BOTH" | "ALL" | "PLAYER" | "SELF" => ctx.player_id as usize,
                    _ => ctx.player_id as usize,
                })
                .unwrap_or(ctx.player_id as usize);

            let stage = &state.players[target_player].stage;
            let total = stage.iter().copied().filter(|&cid| cid >= 0).count() as i32;
            let matching = stage
                .iter()
                .copied()
                .filter(|&cid| cid >= 0)
                .filter(|&cid| {
                    filter_attr == 0
                        || state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
                })
                .count() as i32;

            if total == 0 {
                false
            } else if let Some(eq) =
                get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64())
            {
                matching == eq as i32
            } else if let Some(ge) =
                get_param_case_insensitive(params, "GE").and_then(|v| v.as_i64())
            {
                matching >= ge as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                matching >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                matching <= max as i32
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
            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                energy_count == eq as i32
            } else if let Some(ge) =
                get_param_case_insensitive(params, "GE").and_then(|v| v.as_i64())
            {
                energy_count >= ge as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                energy_count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                energy_count <= max as i32
            } else {
                energy_count > 0
            }
        }
        "DID_ACTIVATE_ENERGY"
        | "DID_ACTIVATE_ENERGY_BY_GROUP"
        | "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT"
        | "DID_ACTIVATE_MEMBER"
        | "DID_ACTIVATE_MEMBER_BY_GROUP"
        | "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT" => check_condition_opcode(
            state,
            db,
            C_HAS_KEYWORD,
            cond.value,
            cond.attr,
            cond.target_slot as i32,
            ctx,
            depth + 1,
        ),
        "ALL_CARDS_MATCH" => {
            let filter_attr = get_param_case_insensitive(params, "FILTER")
                .or_else(|| get_param_case_insensitive(params, "filter"))
                .and_then(|value| value.as_str())
                .map(map_filter_string_to_attr)
                .filter(|&attr| attr != 0)
                .unwrap_or(cond.attr);

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
            let filter_attr = get_param_case_insensitive(params, "FILTER")
                .or_else(|| get_param_case_insensitive(params, "filter"))
                .and_then(|value| value.as_str())
                .map(map_filter_string_to_attr)
                .filter(|&attr| attr != 0)
                .unwrap_or(cond.attr);

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

            if let Some(eq) = get_param_case_insensitive(params, "EQ")
                .or_else(|| get_param_case_insensitive(params, "EQUAL"))
                .and_then(|v| v.as_i64())
            {
                live_score == eq as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                live_score >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
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

            let target_count = params
                .get("heart_type")
                .or_else(|| params.get("HEART_TYPE"))
                .and_then(decode_heart_type_value)
                .filter(|&heart_type| heart_type < 7)
                .map(|heart_type| target_player.excess_hearts_by_color[heart_type] as i32)
                .unwrap_or_else(|| target_player.excess_hearts as i32);

            if let Some(eq) = get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64()) {
                target_count == eq as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                target_count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
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
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                target_hearts >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                target_hearts <= max as i32
            } else {
                target_hearts > 0
            }
        }
        "HEARTS_COUNT" => {
            let target_is_opponent = get_param_case_insensitive(params, "target")
                .or_else(|| get_param_case_insensitive(params, "val"))
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
                Some("GE") | Some("GTE") => lhs >= rhs,
                Some("LT") => lhs < rhs,
                Some("LE") | Some("LTE") => lhs <= rhs,
                Some("EQ") | Some("EQUAL") => lhs == rhs,
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
            } else if let Some(eq) =
                get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64())
            {
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
            } else if let Some(eq) =
                get_param_case_insensitive(params, "EQ").and_then(|v| v.as_i64())
            {
                matching_count == eq as i32
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                matching_count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                matching_count <= max as i32
            } else {
                matching_count > 0
            }
        }
        "UNIQUE_NAMES_COUNT" => {
            let mut names = std::collections::HashSet::<String>::new();
            for &cid in &state.players[ctx.player_id as usize].stage {
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
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
                count <= max as i32
            } else {
                count > 0
            }
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
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                unique_colors >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
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
                } else if part == "UNIQUE_NAMES" || part == "unique_names" {
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
            } else if let Some(min) =
                get_param_case_insensitive(params, "MIN").and_then(|v| v.as_i64())
            {
                count >= min as i32
            } else if let Some(max) =
                get_param_case_insensitive(params, "MAX").and_then(|v| v.as_i64())
            {
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
    
    let mut val = cond.value;
    let mut attr = cond.attr;
    let mut slot = cond.target_slot as i32;

    if let Some(params) = cond.params.as_object() {
        let get_param =
            |key: &str| -> Option<&serde_json::Value> { get_param_case_insensitive(params, key) };

        if val == 0 {
            if let Some(min) = get_param("min").and_then(|v| v.as_i64()) {
                val = min as i32;
            } else if let Some(min) = get_param("value").and_then(|v| v.as_i64()) {
                val = min as i32;
            } else if let Some(v) = get_param("val").and_then(|v| v.as_i64()) {
                val = v as i32;
            }
        }

        let mut mapped_attr = 0;
        if let Some(filter_str) = get_param("filter").and_then(|v| v.as_str()) {
            mapped_attr = map_filter_string_to_attr(filter_str);
        }

        if let Some(area_str) = get_param("area").and_then(|v| v.as_str()) {
            if area_str == "ANY_STAGE" || area_str == "ALL_AREAS" {
                mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_BOTH as u64;
            }
        }

        if let Some(p_val) = get_param("player").and_then(|v| v.as_i64()) {
            match p_val {
                x if x == TARGET_PLAYER_SELF as i64 => {
                    mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_SELF as u64;
                }
                x if x == TARGET_PLAYER_OPPONENT as i64 => {
                    mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_OPPONENT as u64;
                }
                x if x == TARGET_PLAYER_BOTH as i64 => {
                    mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_BOTH as u64;
                }
                _ => {}
            }
        }

        if let Some(kw) = get_param("keyword").and_then(|v| v.as_str()) {
            match kw {
                "PLAYED_THIS_TURN" | "COUNT_PLAYED_THIS_TURN" => {
                    mapped_attr |= KEYWORD_PLAYED_THIS_TURN
                }
                "YELL_COUNT" | "COUNT_YELL_REVEALED" => mapped_attr |= KEYWORD_YELL_COUNT,
                "HAS_LIVE_SET" => mapped_attr |= KEYWORD_HAS_LIVE_SET,
                "UNIQUE_NAMES" | "COUNT_UNIQUE_NAMES" => mapped_attr |= FILTER_UNIQUE_NAMES,
                "DID_ACTIVATE_ENERGY"
                | "DID_ACTIVATE_ENERGY_BY_GROUP"
                | "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT" => {
                    mapped_attr |= KEYWORD_ACTIVATED_ENERGY_BY_GROUP;
                    // Also set group info if present in params
                    if let Some(group_id) = params.get("group_id").and_then(|v| v.as_u64()) {
                        mapped_attr |= FILTER_GROUP_ENABLE;
                        mapped_attr |= (group_id & 0x7F) << FILTER_GROUP_SHIFT;
                    }
                }
                "DID_ACTIVATE_MEMBER"
                | "DID_ACTIVATE_MEMBER_BY_GROUP"
                | "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT" => {
                    mapped_attr |= KEYWORD_ACTIVATED_MEMBER_BY_GROUP;
                    // Also set group info if present in params
                    if let Some(group_id) = params.get("group_id").and_then(|v| v.as_u64()) {
                        mapped_attr |= FILTER_GROUP_ENABLE;
                        mapped_attr |= (group_id & 0x7F) << FILTER_GROUP_SHIFT;
                    }
                }
                "REVEALED_CONTAINS" => {
                    mapped_attr |= FILTER_REVEALED_CONTEXT;
                    if let Some(val_str) = params.get("value").and_then(|v| v.as_str()) {
                        if val_str == "live" {
                            val = CARD_TYPE_LIVE;
                        } else if val_str == "member" {
                            val = CARD_TYPE_MEMBER;
                        }
                    }
                }
                _ => {}
            }
        }

        if attr == 0 {
            attr = mapped_attr;
        } else {
            attr |= mapped_attr;
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
    result
}
