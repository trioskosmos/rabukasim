use super::common::{
    compare_i32, condition_eval_cache_key, condition_eval_cache_lookup,
    condition_eval_cache_store,
};
use super::counts::resolve_count;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::filter::{has_structured_filter_constraints, structured_filter_from_attr, CardFilter};
use crate::core::logic::interpreter::conditions::json_params::evaluate_raw_condition;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::suspension::resolve_target_slot;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::models::Condition;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

#[inline]
fn get_param_case_insensitive<'a>(
    params: &'a serde_json::Map<String, serde_json::Value>,
    key: &str,
) -> Option<&'a serde_json::Value> {
    params.get(key).or_else(|| params.get(&key.to_uppercase()))
}

#[inline]
fn check_count_threshold(count: i32, val: i32, slot: i32) -> bool {
    if val == 0 { count > 0 } else { compare_i32(count, val, slot) }
}

#[inline]
fn resolve_slot_index(area_val: u8, ctx_area_idx: i16) -> Option<usize> {
    if area_val >= 1 && area_val <= 3 {
        Some((area_val - 1) as usize)
    } else if ctx_area_idx >= 0 && (ctx_area_idx as usize) < 3 {
        Some(ctx_area_idx as usize)
    } else {
        None
    }
}

/// Unified parameters for condition checking to reduce parameter passing complexity
struct ConditionParams<'a> {
    state: &'a GameState,
    db: &'a CardDatabase,
    ctx: &'a AbilityContext,
    opcode: i32,
    value: i32,
    raw_attr: u64,
    raw_slot: i32,
    params: Option<&'a serde_json::Value>,
    filter: CardFilter,
    slot: DecodedSlot,
    depth: u32,
}

impl<'a> ConditionParams<'a> {
    fn from_frame(
        state: &'a GameState,
        db: &'a CardDatabase,
        frame: &'a AbilityFrameComponents<'_>,
        ctx: &'a AbilityContext,
        depth: u32,
    ) -> Self {
        Self {
            state,
            db,
            ctx,
            opcode: frame.opcode,
            value: frame.value,
            raw_attr: frame.filter.to_attr(),
            raw_slot: frame.raw_slot,
            params: frame.params,
            filter: frame.filter,
            slot: frame.slot,
            depth,
        }
    }
    
    fn from_opcode(
        state: &'a GameState,
        db: &'a CardDatabase,
        op: i32,
        val: i32,
        attr: u64,
        slot: i32,
        ctx: &'a AbilityContext,
        depth: u32,
    ) -> Self {
        Self {
            state,
            db,
            ctx,
            opcode: op,
            value: val,
            raw_attr: attr,
            raw_slot: slot,
            params: None,
            filter: structured_filter_from_attr(attr),
            slot: DecodedSlot::decode(slot),
            depth,
        }
    }
}

#[inline]
fn card_matches_group(db: &CardDatabase, cid: i32, group_id: u8) -> bool {
    db.get_member(cid)
        .map(|member| {
            member
                .groups
                .iter()
                .any(|&group| group == group_id || group.saturating_add(1) == group_id)
        })
        .or_else(|| {
            db.get_live(cid).map(|live| {
                live.groups
                    .iter()
                    .any(|&group| group == group_id || group.saturating_add(1) == group_id)
            })
        })
        .unwrap_or(false)
}

fn count_matching_selected_or_discarded_cards(
    state: &GameState,
    db: &CardDatabase,
    player: &crate::core::logic::player::PlayerState,
    ctx: &AbilityContext,
    attr: u64,
) -> (i32, i32) {
    if !ctx.selected_cards.is_empty() {
        let matching_count = ctx
            .selected_cards
            .iter()
            .copied()
            .filter(|&cid| attr == 0 || state.card_matches_filter(db, cid, attr))
            .count() as i32;
        (matching_count, ctx.selected_cards.len() as i32)
    } else {
        let matching_count = player
            .discard_ids_this_turn
            .iter()
            .copied()
            .filter(|&cid| attr == 0 || state.card_matches_filter(db, cid, attr))
            .count() as i32;
        (matching_count, player.discard_ids_this_turn.len() as i32)
    }
}

fn count_distinct_yell_heart_colors(player: &crate::core::logic::player::PlayerState, db: &CardDatabase) -> i32 {
    let mut seen = 0u8;
    let mut count = 0i32;

    for &cid in &player.yell_cards {
        if let Some(member) = db.get_member(cid) {
            for color_idx in 0..7 {
                if member.hearts[color_idx] > 0 && (seen & (1 << color_idx)) == 0 {
                    seen |= 1 << color_idx;
                    count += 1;
                }
            }
        }
    }

    count
}

fn compare_sync_cost(
    state: &GameState,
    db: &CardDatabase,
    player: &crate::core::logic::player::PlayerState,
    opponent: &crate::core::logic::player::PlayerState,
    p_idx: usize,
    ctx: &AbilityContext,
    attr: u64,
    val: i32,
    area_val: u8,
    slot_info: DecodedSlot,
    params: Option<&serde_json::Value>,
) -> bool {
    let filter = CardFilter::from_attr(attr);
    let area_override = params
        .and_then(|value| value.as_object())
        .and_then(|params| get_param_case_insensitive(params, "area"))
        .and_then(|value| value.as_str())
        .map(|value| value.to_ascii_uppercase())
        .and_then(|value| match value.as_str() {
            "LEFT_SIDE" | "LEFT" => Some(0usize),
            "CENTER" => Some(1usize),
            "RIGHT_SIDE" | "RIGHT" => Some(2usize),
            _ => None,
        });

    let get_slot_index = || -> Option<usize> {
        area_override.or_else(|| resolve_slot_index(area_val, ctx.area_idx))
    };

    let compare_slot_cost = |cards: &[i32], idx: usize| -> i32 {
        cards
            .get(idx)
            .copied()
            .filter(|&cid| cid >= 0)
            .and_then(|cid| db.get_member(cid))
            .map(|member| member.cost as i32)
            .unwrap_or(0)
    };

    let sum_filtered_costs = |target: &crate::core::logic::player::PlayerState, target_idx: usize| -> i32 {
        target
            .stage
            .iter()
            .enumerate()
            .filter(|(idx, &id)| {
                id >= 0 && state.card_matches_filter_with_struct(
                    db,
                    id,
                    Some((target_idx as u8, *idx as i16)),
                    &filter,
                    ctx,
                )
            })
            .map(|(_, &id)| db.get_member(id).map_or(0, |member| member.cost as i32))
            .sum()
    };

    let (self_cost, opp_cost) = if let Some(idx) = get_slot_index() {
        (compare_slot_cost(&player.stage, idx), compare_slot_cost(&opponent.stage, idx))
    } else {
        (sum_filtered_costs(player, p_idx), sum_filtered_costs(opponent, 1 - p_idx))
    };

    if state.debug.debug_mode {
        eprintln!(
            "[DEBUG_SYNC_COST] area_val={}, area_override={:?}, ctx.area_idx={}, self_cost={}, opp_cost={}, val={}",
            area_val,
            area_override,
            ctx.area_idx,
            self_cost,
            opp_cost,
            val
        );
    }

    let comparison_mode = if slot_info.comparison == 0 { 1 } else { slot_info.comparison };
    compare_i32(self_cost, opp_cost + val, (comparison_mode as i32) << 4)
}

pub fn check_condition_frame(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    let params = ConditionParams::from_frame(state, db, frame, ctx, depth);
    
    // Handle raw condition parameters
    if let Some(raw_params) = frame.params.and_then(|value| value.as_object()) {
        if raw_params.get("raw_cond").is_some() || raw_params.get("RAW_COND").is_some() {
            let cond = Condition {
                condition_type: ConditionType::None,
                value: frame.value,
                attr: frame.filter.to_attr(),
                target_slot: 0,
                is_negated: frame.is_negated,
                params: frame.params.cloned().unwrap_or_default(),
            };
            let raw_result = evaluate_raw_condition(state, db, 0, &cond, ctx, depth, raw_params);
            return if frame.is_negated {
                !raw_result
            } else {
                raw_result
            };
        }
    }

    check_condition_with_parts_internal(params)
}

pub fn check_condition_opcode(
    state: &GameState,
    db: &CardDatabase,
    op: i32,
    val: i32,
    attr: u64,
    slot: i32,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    let params = ConditionParams::from_opcode(state, db, op, val, attr, slot, ctx, depth);
    check_condition_with_parts_internal(params)
}

/// Internal condition checking with unified parameter structure
fn check_condition_with_parts_internal(params: ConditionParams) -> bool {
    check_condition_with_parts(
        params.state,
        params.db,
        params.opcode,
        params.value,
        params.raw_attr,
        params.raw_slot,
        params.params,
        params.filter,
        params.slot,
        params.ctx,
        params.depth,
    )
}

fn check_condition_with_parts(
    state: &GameState,
    db: &CardDatabase,
    op: i32,
    val: i32,
    attr: u64,
    slot: i32,
    params: Option<&serde_json::Value>,
    filter: CardFilter,
    slot_info: DecodedSlot,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    if state.debug.debug_ignore_conditions {
        return true;
    }
    let p_idx = ctx.activator_id as usize;
    let cache_key = condition_eval_cache_key(op, val, attr, slot, p_idx, params, ctx, depth);
    if let Some(hit) = condition_eval_cache_lookup(&cache_key) {
        return hit;
    }
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];
    let semantic = AbilityFrameComponents::from_raw_parts(op, val, crate::core::logic::filter::CardFilter::from_attr(attr), slot, false, params);
    let get_cid = || {
        if ctx.source_card_id >= 0 {
            ctx.source_card_id
        } else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
            player.stage[ctx.area_idx as usize]
        } else {
            -1
        }
    };

    let cid = get_cid();
    let area_val = slot_info.area_idx;
    let real_slot = semantic.debug_slot_value();
    if state.debug.debug_mode {
        if !state.ui.silent {
            let attr_desc = logging::describe_filter_bits(attr);
            println!(
                "[DEBUG] Condition Opcode: {} | {} | attr=[{}] | slot={} (area={}), source={:?}",
                op,
                logging::describe_condition(op, val, attr),
                attr_desc,
                real_slot,
                area_val,
                cid
            );
        }
    }

    let result = match op {
        // Q230 Fix: SUCCESS_LIVE_COUNT_EQUAL_OPPONENT needs to compare both players' success lives
        0 => {
            let my_lives = player.success_lives.len() as i32;
            let opp_lives = opponent.success_lives.len() as i32;
            compare_i32(my_lives, opp_lives, real_slot)
        }
        C_TURN_1 => state.turn == 1,
        C_HAS_MEMBER => {
            let p_target = if filter.target_player == 2 {
                1 - p_idx
            } else {
                p_idx
            };
            let target_player = &state.players[p_target as usize];

            target_player
                .stage
                .iter()
                .enumerate()
                .filter(|(_, &id)| id >= 0)
                .any(|(slot_idx, &id)| {
                    (val != 0 && id == val)
                        || (attr != 0
                            && state.card_matches_filter_with_ctx_at_slot(
                                db,
                                id,
                                attr,
                                (p_target as u8, slot_idx as i16),
                                ctx,
                            ))
                })
        }
        C_HAS_COLOR => {
            let color_mask = filter.color_mask as u64;
            if color_mask != 0 {
                player
                    .stage
                    .iter()
                    .enumerate()
                    .filter(|(_, &cid)| cid >= 0)
                    .any(|(slot_idx, &cid)| {
                        if let Some(_m) = db.get_member(cid) {
                        let eff_h = state.get_effective_hearts(
                            p_idx,
                            slot_idx,
                            db,
                            depth + 1,
                        );
                        return (eff_h.get_color_mask() as u64 & color_mask) != 0;
                    }
                        false
                    })
            } else {
                let color_idx = semantic.resolved_filter_value(val) as usize;
                if color_idx < 7 {
                    player.stage.iter().any(|&c| {
                        if c >= 0 {
                            if let Some(m) = db.get_member(c) {
                            m.hearts[color_idx] > 0
                            } else {
                                false
                            }
                        } else {
                            false
                        }
                    })
                } else {
                    false
                }
            }
        }
        C_COUNT_STAGE => {
            let count = if (attr & FILTER_ANY_STAGE) != 0 {
                let has_filter_constraints = has_structured_filter_constraints(attr);
                let count_for_player = |player_idx: usize| {
                    state.players[player_idx]
                        .stage
                        .iter()
                        .enumerate()
                        .filter(|(_, &cid)| cid >= 0)
                        .filter(|(slot_idx, &cid)| {
                            !has_filter_constraints
                                || state.card_matches_filter_with_struct(
                                    db,
                                    cid,
                                    Some((player_idx as u8, *slot_idx as i16)),
                                    &filter,
                                    ctx,
                                )
                        })
                        .count() as i32
                };
                count_for_player(p_idx) + count_for_player(1 - p_idx)
            } else {
                resolve_count(state, db, op, attr, slot, ctx, depth)
            };
            check_count_threshold(count, val, slot)
        }
        C_IS_CENTER => {
            if !state.ui.silent {
                eprintln!("Rule 11.6, Rule 11.6.1, Rule 11.6.2, Rule 11.6.3, Rule 11.6.4: Checking [センター] (Center) slot restriction.");
            }
            ctx.area_idx == 1
        }
        C_COUNT_HAND => {
            let count = if slot == 48 || semantic.slot.target_slot == Zone::Yell as u8 || semantic.slot.source_zone == Zone::Yell {
                state.players[p_idx]
                    .yell_cards
                    .iter()
                    .filter(|&&cid| {
                        cid >= 0
                            && state.card_matches_filter_with_struct(
                                db,
                                cid,
                                None,
                                &semantic.filter,
                                ctx,
                            )
                    })
                    .count() as i32
            } else {
                resolve_count(state, db, op, attr, slot, ctx, depth)
            };
            check_count_threshold(count, val, slot)
        }
        C_COUNT_DISCARD => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_COUNT_ENERGY => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_HAS_LIVE_CARD => player.live_zone.iter().any(|&cid| cid >= 0),
        COST_ENERGY => {
            let cost_delta = state.calculate_cost_delta(db, ctx.source_card_id, p_idx);
            let total_cost = (val + cost_delta).max(0);
            (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32
                >= total_cost
        }
        COST_TAP_SELF => {
            let slot = resolve_target_slot(slot, ctx);
            slot < 3 && !player.is_tapped(slot)
        }
        COST_DISCARD_HAND => player.hand.len() as i32 >= val,
        COST_RETURN_HAND => player.stage.iter().filter(|&&id| id >= 0).count() as i32 >= val,
        COST_SACRIFICE_SELF => {
            let slot = resolve_target_slot(slot, ctx);
            slot < 3 && player.stage[slot] >= 0
        }
        COST_TAP_MEMBER => player
            .stage
            .iter()
            .enumerate()
            .any(|(i, &cid)| cid >= 0 && !player.is_tapped(i)),
        COST_TAP_ENERGY => {
            (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32 >= val
        }
        COST_DISCARD_ENERGY => player.energy_zone.len() as i32 >= val,
        COST_PLACE_MEMBER_FROM_HAND => player.hand.len() as i32 >= val,
        C_RARITY_CHECK => {
            let cid = get_cid();
            if cid >= 0 {
                db.get_member(cid).map_or(false, |m| m.rarity == val as u8)
            } else {
                false
            }
        }
        C_COUNT_SUCCESS_LIVE => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_OPPONENT_HAS => {
            let p_opp = 1 - p_idx;
            state.players[p_opp]
                .stage
                .iter()
                .enumerate()
                .filter(|(_, &id)| id >= 0)
                .any(|(slot_idx, &cid)| {
                    cid == val
                        || (attr != 0
                            && state.card_matches_filter_with_ctx_at_slot(
                                db,
                                cid,
                                attr,
                                (p_opp as u8, slot_idx as i16),
                                ctx,
                            ))
                })
        }
        C_LIFE_LEAD => {
            let my_lives = player.success_lives.len() as i32;
            let opp_lives = opponent.success_lives.len() as i32;
            let reversed = semantic.slot.comparison == 2;
            let diff = if reversed {
                opp_lives - my_lives
            } else {
                my_lives - opp_lives
            };
            if val == 0 {
                diff >= 0
            } else {
                diff >= val
            }
        }
        C_COUNT_GROUP => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_GROUP_FILTER => {
            let group_id = semantic.semantic_group_id(val);

            if (val & 0x04) != 0 {
                group_id.map_or(false, |group_id| {
                    player
                        .stage
                        .iter()
                        .filter(|&&cid| cid >= 0)
                        .all(|&cid| card_matches_group(db, cid, group_id))
                })
            } else {
                let cid = state.get_context_card_id(ctx).or(Some(ctx.source_card_id));
                if let (Some(cid), Some(group_id)) = (cid, group_id) {
                    card_matches_group(db, cid, group_id)
                } else {
                    false
                }
            }
        }
        C_SELF_IS_GROUP => {
            let cid = get_cid();
            if cid >= 0 {
                semantic
                    .semantic_group_id(val)
                    .map(|group_id| card_matches_group(db, cid, group_id))
                    .unwrap_or(false)
            } else {
                false
            }
        }
        C_MODAL_ANSWER => ctx.choice_index == (val as i16),
        C_COST_CHECK => {
            if let Some(cid) = state.get_context_card_id(ctx) {
                if let Some(m) = db.get_member(cid) {
                    compare_i32(m.cost as i32, val, slot)
                } else {
                    false
                }
            } else {
                false
            }
        }
        C_HAND_HAS_NO_LIVE => !player
            .hand
            .iter()
            .filter(|&&id| id >= 0)
            .any(|&id| db.get_live(id).is_some()),
        C_OPPONENT_HAND_DIFF => {
            let my_hand = player.hand.len() as i32;
            let opp_hand = opponent.hand.len() as i32;
            (opp_hand - my_hand) >= val
        }
        C_SCORE_COMPARE => {
            let my_score = player.score as i32;
            let opp_score = opponent.score as i32;
            compare_i32(my_score, opp_score + val, slot)
        }
        C_HAS_CHOICE => !state.interaction_stack.is_empty(),
        C_OPPONENT_CHOICE => state
            .interaction_stack
            .iter()
            .any(|p| p.ctx.player_id != p_idx as u8),
        C_COUNT_HEARTS => {
            let count = resolve_count(state, db, op, attr, slot, ctx, depth + 1);
            if val == 0 { count > 0 } else { compare_i32(count, val, slot) }
        }
        C_COUNT_BLADES => {
            let count = resolve_count(state, db, op, attr, slot, ctx, depth + 1);
            if val == 0 { count > 0 } else { compare_i32(count, val, slot) }
        }
        C_OPPONENT_ENERGY_DIFF => {
            let my_energy = player.energy_zone.len() as i32;
            let opp_energy = opponent.energy_zone.len() as i32;
            (opp_energy - my_energy) >= val
        }
        C_HAS_KEYWORD => {
            if semantic.requests_keyword_energy() {
                if let Some(group_id) = semantic.semantic_group_id(val) {
                    let group_id = group_id as u64;
                    let mask = player.activated_energy_group_mask;
                    let passed = (mask & (1 << group_id)) != 0;
                    if state.debug.debug_mode {
                        eprintln!(
                            "[COND_HAS_KEYWORD] kind=energy group={} mask={:#x} passed={}",
                            group_id,
                            mask,
                            passed
                        );
                    }
                    return passed;
                }
                let passed = player.activated_energy_group_mask != 0;
                if state.debug.debug_mode {
                    eprintln!(
                        "[COND_HAS_KEYWORD] kind=energy group=any mask={:#x} passed={}",
                        player.activated_energy_group_mask,
                        passed
                    );
                }
                return passed;
            }
            if semantic.requests_keyword_member() {
                if let Some(group_id) = semantic.semantic_group_id(val) {
                    let group_id = group_id as u64;
                    let passed = (player.activated_member_group_mask & (1 << group_id)) != 0;
                    if state.debug.debug_mode {
                        eprintln!(
                            "[COND_HAS_KEYWORD] kind=member group={} mask={:#x} passed={}",
                            group_id,
                            player.activated_member_group_mask,
                            passed
                        );
                    }
                    return passed;
                }
                let passed = player.activated_member_group_mask != 0;
                if state.debug.debug_mode {
                    eprintln!(
                        "[COND_HAS_KEYWORD] kind=member group=any mask={:#x} passed={}",
                        player.activated_member_group_mask,
                        passed
                    );
                }
                return passed;
            }

            let mut res = false;
            if state.phase == Phase::LiveResult && !player.yell_cards.is_empty() {
                res = compare_i32(player.yell_cards.len() as i32, val, slot);
            }
            if !res && semantic.requests_played_this_turn_keyword() {
                if let Some(group_id) = semantic.semantic_group_id(val) {
                    let group_id = group_id as u64;
                    res = (player.played_group_mask & (1 << group_id)) != 0;
                } else if val == 0 && semantic.requests_played_this_turn_keyword() {
                    res = player.play_count_this_turn() > 0;
                } else {
                    res = compare_i32(player.play_count_this_turn() as i32, val, slot);
                }
            }
            // Fallback: if no specific keyword is requested but value is set, check play_count
            if !res && !semantic.requests_keyword_energy() && !semantic.requests_keyword_member() && !semantic.requests_yell_count_keyword() && !semantic.requests_has_live_set_keyword() {
                let play_count = player.play_count_this_turn();
                // Only use group_id if the filter actually has group_enabled set
                if semantic.filter.group_enabled {
                    if let Some(group_id) = semantic.semantic_group_id(val) {
                        let group_id = group_id as u64;
                        res = (player.played_group_mask & (1 << group_id)) != 0;
                    }
                } else if val == 0 {
                    res = play_count > 0;
                } else {
                    res = compare_i32(play_count as i32, val, slot);
                }
            }
            if semantic.requests_yell_count_keyword() {
                res = compare_i32(player.yell_cards.len() as i32, val, slot);
            }
            if semantic.requests_has_live_set_keyword() {
                res = player.live_zone.iter().any(|&c| c >= 0);
            }
            if semantic.has_revealed_context_passthrough() {
                if val == 1 {
                    res = player
                        .looked_cards
                        .iter()
                        .any(|&cid| db.get_live(cid).is_some());
                } else if val == 2 {
                    res = player
                        .looked_cards
                        .iter()
                        .any(|&cid| db.get_member(cid).is_some());
                }
            }
            res
        }
        C_DECK_REFRESHED => {
            player.get_flag(crate::core::logic::player::PlayerState::FLAG_DECK_REFRESHED)
        }
        C_HAS_MOVED => {
            let slot_idx = if semantic.slot.area_idx < 3 {
                Some(semantic.slot.area_idx as usize)
            } else if ctx.area_idx >= 0 && ctx.area_idx < 3 {
                Some(ctx.area_idx as usize)
            } else {
                None
            };
            slot_idx
                .map(|slot_idx| player.is_moved(slot_idx))
                .unwrap_or(false)
        }
        C_HAND_INCREASED => player.hand_increased_this_turn > 0,
        C_BATON => {
            let count_ok = if val > 0 {
                player.baton_touch_count() == val as u8
            } else {
                player.baton_touch_count() > 0 || state.prev_card_id != -1
            };
            if !count_ok {
                return false;
            }
            let filter_attr = semantic.resolved_filter_attr();
            if filter_attr != 0 {
                player
                    .baton_source_ids
                    .iter()
                    .any(|&bid| state.card_matches_filter(db, bid, filter_attr))
                    || (state.prev_card_id >= 0
                        && state.card_matches_filter(db, state.prev_card_id, filter_attr))
            } else {
                count_ok
            }
        }
        C_COUNT_LIVE_ZONE => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_COUNT_LIVE_HEARTS => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_COUNT_SUCCESS_LIVE_SCORE => check_count_threshold(resolve_count(state, db, op, attr, slot, ctx, depth), val, slot),
        C_TYPE_CHECK => {
            let check_val = semantic.resolved_filter_value(val);
            let card_id = player
                .looked_cards
                .first()
                .copied()
                .filter(|&cid| cid >= 0)
                .or_else(|| state.get_context_card_id(ctx));
            if let Some(card_id) = card_id {
                if check_val == 1 {
                    db.get_live(card_id).is_some()
                } else {
                    db.get_member(card_id).is_some()
                }
            } else {
                false
            }
        }
        C_IS_IN_DISCARD => {
            let cid = ctx.source_card_id;
            cid >= 0 && player.discard.contains(&(cid as i32))
        }
        C_AREA_CHECK => {
            if !state.ui.silent && state.debug.debug_mode {
                if val == 1 {
                    eprintln!("Rule 11.7, Rule 11.7.1, Rule 11.7.2, Rule 11.7.3, Rule 11.7.4: Checking [左サイド] (Left Side) slot restriction.");
                } else if val == 3 {
                    eprintln!("Rule 11.8, Rule 11.8.1, Rule 11.8.2, Rule 11.8.3, Rule 11.8.4: Checking [右サイド] (Right Side) slot restriction.");
                } else if val == 2 {
                    eprintln!(
                        "Rule 11.6: Checking [センター] (Center) slot restriction via AreaCheck."
                    );
                }
            }
            ctx.area_idx == (val - 1) as i16
        }
        C_COST_LEAD => {
            let self_cost = player
                .stage
                .get(1)
                .copied()
                .filter(|&id| id >= 0)
                .and_then(|id| db.get_member(id))
                .map(|m| m.cost as i32)
                .unwrap_or(0);
            let opp_cost = opponent
                .stage
                .get(1)
                .copied()
                .filter(|&id| id >= 0)
                .and_then(|id| db.get_member(id))
                .map(|m| m.cost as i32)
                .unwrap_or(0);
            let reversed = semantic.slot.comparison == 2;
            let diff = if reversed {
                opp_cost - self_cost
            } else {
                self_cost - opp_cost
            };
            if val == 0 {
                diff > 0
            } else {
                diff >= val
            }
        }
        C_SCORE_LEAD => {
            let self_score = player.score as i32;
            let opp_score = opponent.score as i32;
            let reversed = semantic.slot.comparison == 2;
            let diff = if reversed {
                opp_score - self_score
            } else {
                self_score - opp_score
            };
            if val == 0 {
                diff > 0
            } else {
                diff >= val
            }
        }
        C_HEART_LEAD => {
            let self_hearts = state.get_total_member_hearts(p_idx, db, depth + 1);
            let opp_hearts = state.get_total_member_hearts(1 - p_idx, db, depth + 1);
            let self_total = self_hearts
                .to_array()
                .iter()
                .map(|&x| x as i32)
                .sum::<i32>();
            let opp_total = opp_hearts.to_array().iter().map(|&x| x as i32).sum::<i32>();
            let reversed = semantic.slot.comparison == 2;
            let diff = if reversed {
                opp_total - self_total
            } else {
                self_total - opp_total
            };
            if val == 0 {
                diff > 0
            } else {
                diff >= val
            }
        }
        C_HAS_EXCESS_HEART => match filter.target_player {
            1 => player.excess_hearts > 0,
            2 => opponent.excess_hearts > 0,
            3 => player.excess_hearts > 0 || opponent.excess_hearts > 0,
            _ => player.excess_hearts > 0,
        },
        C_NOT_HAS_EXCESS_HEART => match filter.target_player {
            1 => player.excess_hearts == 0,
            2 => opponent.excess_hearts == 0,
            3 => player.excess_hearts == 0 && opponent.excess_hearts == 0,
            _ => player.excess_hearts == 0,
        },
        C_TOTAL_BLADES => {
            let mut total = 0u32;
            for slot_idx in 0..3 {
                let cid = player.stage[slot_idx];
                if cid < 0 {
                    continue;
                }
                if let Some(member) = db.get_member(cid) {
                    let mut slot_total = if player.blade_overrides[slot_idx] != -1 {
                        player.blade_overrides[slot_idx] as i32
                    } else {
                        member.blades as i32
                    };
                    slot_total += player.blade_buffs[slot_idx] as i32;
                    if slot_total > 0 {
                        total = total.saturating_add(slot_total as u32);
                    }
                }
            }
            total >= val as u32
        }
        C_COST_COMPARE => {
            let compare_slot = |cards: &[i32], idx: usize| -> i32 {
                cards
                    .get(idx)
                    .copied()
                    .filter(|&cid| cid >= 0)
                    .and_then(|cid| db.get_member(cid))
                    .map(|m| m.cost as i32)
                    .unwrap_or(0)
            };

            let (self_cost, opp_cost) = if area_val >= 1 && area_val <= 3 {
                let idx = (area_val - 1) as usize;
                (compare_slot(&player.stage, idx), compare_slot(&opponent.stage, idx))
            } else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                let idx = ctx.area_idx as usize;
                (compare_slot(&player.stage, idx), compare_slot(&opponent.stage, idx))
            } else {
                let self_total = player
                    .stage
                    .iter()
                    .enumerate()
                    .map(|(idx, _)| compare_slot(&player.stage, idx))
                    .sum::<i32>();
                let opp_total = opponent
                    .stage
                    .iter()
                    .enumerate()
                    .map(|(idx, _)| compare_slot(&opponent.stage, idx))
                    .sum::<i32>();
                (self_total, opp_total)
            };

            self_cost > opp_cost
        }
        C_BLADE_COMPARE => {
            let slot = resolve_slot_index(area_val, ctx.area_idx).unwrap_or(0);
            let blades = state.get_effective_blades(p_idx, slot, db, depth + 1);
            if semantic.filter.is_le {
                blades <= val as u32
            } else {
                blades >= val as u32
            }
        }
        C_HEART_COMPARE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            let hearts = state.get_effective_hearts(p_idx, slot, db, depth + 1);
            let color_idx = semantic.heart_compare_color_index();
            let count = if color_idx < 7 {
                hearts.to_array()[color_idx] as i32
            } else {
                hearts.get_total_count() as i32
            };
            if state.debug.debug_mode || std::env::var("TRACE_HEART_COMPARE").is_ok() {
                eprintln!(
                    "[DEBUG_HEART_COMPARE] slot={}, color_idx={}, hearts={:?}, count={}, val={}, is_le={}",
                    slot,
                    color_idx,
                    hearts.to_array(),
                    count,
                    val,
                    semantic.filter.is_le
                );
            }
            if semantic.filter.is_le {
                count <= val
            } else {
                count >= val
            }
        }
        C_OPPONENT_HAS_WAIT => (0..3).any(|i| opponent.stage[i] >= 0 && opponent.is_tapped(i)),
        C_IS_TAPPED => player.is_tapped(resolve_slot_index(area_val, ctx.area_idx).unwrap_or(0)),
        C_IS_ACTIVE => !player.is_tapped(resolve_slot_index(area_val, ctx.area_idx).unwrap_or(0)),
        C_LIVE_PERFORMED => state.obtained_success_live[p_idx],
        C_IS_PLAYER => p_idx == state.current_player as usize,
        C_IS_OPPONENT => p_idx != state.current_player as usize,
        C_COUNT_ENERGY_EXACT => {
            compare_i32(player.tapped_energy_mask.count_ones() as i32, val, slot)
        }
        C_COUNT_BLADE_HEART_TYPES => {
            let mut combined = HeartBoard::from_array(&[0; 7]);
            for &cid in &player.yell_cards {
                if let Some(m) = db.get_member(cid) {
                    combined.add(HeartBoard::from_array(&m.blade_hearts));
                } else if let Some(l) = db.get_live(cid) {
                    combined.add(HeartBoard::from_array(&l.blade_hearts));
                }
            }
            let mut types = 0;
            for i in 0..7 {
                if combined.get_color_count(i) > 0 {
                    types += 1;
                }
            }
            compare_i32(types, val, slot)
        }
        C_OPPONENT_HAS_EXCESS_HEART => opponent.excess_hearts > 0,
        C_SCORE_TOTAL_CHECK => {
            let mut sum = 0;
            for &cid in &player.success_lives {
                if let Some(l) = db.get_live(cid) {
                    sum += l.score;
                }
            }
            compare_i32(sum as i32, val, slot)
        }
        305 => state.current_player == (p_idx as u8) && state.phase == Phase::Main,
        306 => {
            if ctx.target_card_id >= 0 {
                return true;
            }
            let has_filter_constraints = has_structured_filter_constraints(attr);
            let mut check_ids = Vec::new();
            if area_val == 0 {
                let (player_idx, other_player_idx) = semantic.stage_player_scope(p_idx);
                for player_idx in std::iter::once(player_idx).chain(other_player_idx.into_iter()) {
                    for (slot_idx, &stage_cid) in state.players[player_idx].stage.iter().enumerate() {
                        if stage_cid < 0 {
                            continue;
                        }
                        if !has_filter_constraints
                            || state.card_matches_filter_with_struct(
                                db,
                                stage_cid,
                                Some((player_idx as u8, slot_idx as i16)),
                                &filter,
                                ctx,
                            )
                        {
                            check_ids.push(stage_cid);
                        }
                    }
                }
            } else if area_val >= 1 && area_val <= 3 {
                check_ids.push(player.stage[(area_val - 1) as usize]);
            }
            check_ids
                .into_iter()
                .any(|cid| cid >= 0)
        }
        307 => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        308 => ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize),
        309 => {
            let (matching_count, source_count) =
                count_matching_selected_or_discarded_cards(state, db, player, ctx, attr);
            if (val & 0x04) != 0 {
                source_count > 0 && matching_count == source_count
            } else {
                compare_i32(matching_count, val, slot)
            }
        }
        310 => compare_i32(count_distinct_yell_heart_colors(player, db), val, slot),
        311 => compare_sync_cost(
            state,
            db,
            player,
            opponent,
            p_idx,
            ctx,
            attr,
            val,
            area_val,
            slot_info,
            params,
        ),
        312 => {
            if val == 0 && slot == 0 {
                ctx.v_accumulated as i32 >= 0
            } else {
                compare_i32(ctx.v_accumulated as i32, val, slot)
            }
        }
        313 => player.is_tapped(resolve_slot_index(area_val, ctx.area_idx).unwrap_or(0)),
        C_ON_ABILITY_RESOLVE => true,
        C_TARGET_MEMBER_HAS_NO_HEARTS => {
            let target_id = ctx.target_card_id;
            if target_id >= 0 {
                if let Some(slot_idx) = player.stage.iter().position(|&id| id == target_id) {
                    state
                        .get_effective_hearts(p_idx, slot_idx, db, depth + 1)
                        .get_color_count(6)
                        == 0
                } else {
                    false
                }
            } else {
                false
            }
        }
        _ => false,
    };

    if !result && state.debug.debug_ignore_conditions {
        if let Some(ref log) = state.debug.bypassed_conditions {
            if let Ok(mut bypassed) = log.0.lock() {
                bypassed.push(format!(
                    "BYPASS Opcode: {}, Value {}, Attr {}",
                    op, val, attr
                ));
            }
        }
        return true;
    }
    condition_eval_cache_store(cache_key, result);
    result
}
