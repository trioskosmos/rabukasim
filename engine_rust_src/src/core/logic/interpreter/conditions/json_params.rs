use crate::core::enums::*;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::{AbilityContext, CardDatabase, Condition, ConditionType, GameState};
use super::common::{parse_condition_type, MAX_CONDITION_CHECK_DEPTH};
use super::opcodes::check_condition_opcode;

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
                .any(|cid| cid >= 0 && (filter_attr == 0 || state.card_matches_filter(db, cid, filter_attr)));

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
                .or_else(|| state.ui.last_performance_results.get(&(ctx.player_id as u8)));

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
                .or_else(|| db.get_live(ctx.source_card_id).map(|live| live.score as i32))
                .unwrap_or_default();

            if let Some(eq) = get_param_case_insensitive(params, "EQ")
                .or_else(|| get_param_case_insensitive(params, "EQUAL"))
                .and_then(|v| v.as_i64())
            {
                live_score == eq as i32
            } else if let Some(min) = get_param_case_insensitive(params, "MIN")
                .and_then(|v| v.as_i64())
            {
                live_score >= min as i32
            } else if let Some(max) = get_param_case_insensitive(params, "MAX")
                .and_then(|v| v.as_i64())
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

            let heart_type = get_param_case_insensitive(params, "HEART_TYPE")
                .and_then(|v| v.as_u64())
                .map(|v| v as usize);
            let target_count = heart_type
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
        "REDUCE_YELL_COUNT" => {
            let player_yell_count = state.players[ctx.player_id as usize].yell_cards.len() as i32;
            let opponent_yell_count = state.players[1 - ctx.player_id as usize].yell_cards.len() as i32;

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
            let filter = get_param_case_insensitive(params, "FILTER").and_then(|v| v.as_str()).unwrap_or("");

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

            let matching_count = yell_cards.iter().copied().filter(|&cid| matches_filter(cid)).count() as i32;

            if filter.eq_ignore_ascii_case("HAS_ALL_BLADE") && 
               get_param_case_insensitive(params, "EQ").is_none() &&
               get_param_case_insensitive(params, "MIN").is_none() &&
               get_param_case_insensitive(params, "MAX").is_none()
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
            let mut name_pool = Vec::<String>::new();
            let mut stage_name_options = Vec::<Vec<usize>>::new();
            for &cid in &state.players[ctx.player_id as usize].stage {
                if cid < 0 { continue; }
                if let Some(member) = db.get_member(cid) {
                    let mut options = Vec::new();
                    for part in member.name.split(['&', '＆']) {
                        let normalized = part.trim();
                        if !normalized.is_empty() {
                            let name_index = if let Some(existing_index) = name_pool.iter().position(|existing| existing == normalized) {
                                existing_index
                            } else {
                                name_pool.push(normalized.to_string());
                                name_pool.len() - 1
                            };
                            if !options.contains(&name_index) { options.push(name_index); }
                        }
                    }
                    if !options.is_empty() { stage_name_options.push(options); }
                }
            }

            fn assign_name(card_index: usize, options: &[Vec<usize>], owner: &mut [Option<usize>], seen: &mut [bool]) -> bool {
                for &name_idx in &options[card_index] {
                    if seen[name_idx] { continue; }
                    seen[name_idx] = true;
                    if owner[name_idx].is_none() || assign_name(owner[name_idx].unwrap(), options, owner, seen) {
                        owner[name_idx] = Some(card_index);
                        return true;
                    }
                }
                false
            }

            let mut owner = vec![None; name_pool.len()];
            let mut count = 0;
            for i in 0..stage_name_options.len() {
                let mut seen = vec![false; name_pool.len()];
                if assign_name(i, &stage_name_options, &mut owner, &mut seen) { count += 1; }
            }

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
        "UNIQUE_HEART_TYPES" => {
            let mut color_mask: u8 = 0;
            for &cid in &state.players[ctx.player_id as usize].stage {
                if cid < 0 { continue; }
                if let Some(member) = db.get_member(cid) {
                    for (color_idx, &count) in member.hearts.iter().enumerate().take(6) {
                        if count > 0 { color_mask |= 1u8 << color_idx; }
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
            let filter_str = get_param_case_insensitive(params, "FILTER").and_then(|v| v.as_str()).unwrap_or("");
            let mut group_id: u8 = 0;
            let mut check_unique_names = false;
            for part in filter_str.split(',') {
                let part = part.trim();
                if part.starts_with("GROUP_ID=") {
                    if let Ok(gid) = part.strip_prefix("GROUP_ID=").unwrap_or("0").parse::<u8>() { group_id = gid; }
                } else if part == "UNIQUE_NAMES" || part == "unique_names" {
                    check_unique_names = true;
                }
            }
            let filtered_cards: Vec<i32> = yell_cards.iter().copied().filter(|&cid| {
                if group_id > 0 {
                    db.get_member(cid).map(|m| m.groups.contains(&group_id)).or_else(|| db.get_live(cid).map(|l| l.groups.contains(&group_id))).unwrap_or(false)
                } else { true }
            }).collect();
            let count = if check_unique_names {
                let mut names = std::collections::HashSet::new();
                for &cid in &filtered_cards {
                    if let Some(m) = db.get_member(cid) { names.insert(m.name.clone()); }
                    else if let Some(l) = db.get_live(cid) { names.insert(l.name.clone()); }
                }
                names.len() as i32
            } else { filtered_cards.len() as i32 };

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
    if state.debug.debug_ignore_conditions {
        return true;
    }
    if depth > MAX_CONDITION_CHECK_DEPTH {
        return false;
    }

    let mut val = cond.value;
    let mut attr = cond.attr;
    let mut slot = cond.target_slot as i32;

    if let Some(params) = cond.params.as_object() {
        let get_param = |key: &str| -> Option<&serde_json::Value> {
            get_param_case_insensitive(params, key)
        };

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
                x if x == TARGET_PLAYER_SELF as i64 => { mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_SELF as u64; }
                x if x == TARGET_PLAYER_OPPONENT as i64 => { mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_OPPONENT as u64; }
                x if x == TARGET_PLAYER_BOTH as i64 => { mapped_attr = (mapped_attr & !0x3) | TARGET_PLAYER_BOTH as u64; }
                _ => {}
            }
        }

        if let Some(kw) = get_param("keyword").and_then(|v| v.as_str()) {
            match kw {
                "PLAYED_THIS_TURN" | "COUNT_PLAYED_THIS_TURN" => { mapped_attr |= KEYWORD_PLAYED_THIS_TURN }
                "YELL_COUNT" | "COUNT_YELL_REVEALED" => mapped_attr |= KEYWORD_YELL_COUNT,
                "HAS_LIVE_SET" => mapped_attr |= KEYWORD_HAS_LIVE_SET,
                "UNIQUE_NAMES" | "COUNT_UNIQUE_NAMES" => mapped_attr |= FILTER_UNIQUE_NAMES,
                "DID_ACTIVATE_ENERGY" | "DID_ACTIVATE_ENERGY_BY_GROUP" | "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT" => { mapped_attr |= KEYWORD_ACTIVATED_ENERGY_BY_GROUP }
                "DID_ACTIVATE_MEMBER" | "DID_ACTIVATE_MEMBER_BY_GROUP" | "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT" => { mapped_attr |= KEYWORD_ACTIVATED_MEMBER_BY_GROUP }
                "REVEALED_CONTAINS" => {
                    mapped_attr |= FILTER_REVEALED_CONTEXT;
                    if let Some(val_str) = params.get("value").and_then(|v| v.as_str()) {
                        if val_str == "live" { val = CARD_TYPE_LIVE; }
                        else if val_str == "member" { val = CARD_TYPE_MEMBER; }
                    }
                }
                _ => {}
            }
        }

        if attr == 0 { attr = mapped_attr; } else { attr |= mapped_attr; }

        if cond.condition_type == ConditionType::GroupFilter || cond.condition_type == ConditionType::DiscardedCards {
            if params.get("all").and_then(|v| v.as_bool()).unwrap_or(false) { val |= 0x04; }
        }

        if ((slot >> 4) & 0x0F) == 0 {
            if let Some(mode) = comparison_mode_from_params(params) {
                slot = (slot & 0x0F) | ((mode as i32) << 4);
            }
        }
    }

    let raw_cond_result = cond.params.as_object().map(|p| evaluate_raw_condition(state, db, p_idx, cond, ctx, depth, p)).unwrap_or(true);

    let result = if cond.condition_type != ConditionType::None {
        check_condition_opcode(state, db, cond.condition_type as i32, val, attr, slot, ctx, depth + 1)
    } else { raw_cond_result };

    let result = if cond.is_negated { !result } else { result };

    if !result && state.debug.debug_ignore_conditions {
        if let Some(ref log) = state.debug.bypassed_conditions {
            if let Ok(mut bypassed) = log.0.lock() {
                bypassed.push(format!("BYPASS Condition: Type {:?}, Value {}, Attr {}", cond.condition_type, cond.value, cond.attr));
            }
        }
        return true;
    }
    result
}
