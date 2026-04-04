use super::card_db::{CardDatabase, MemberCard};
use super::game::GameState;
use crate::core::logic::interpreter::check_condition;
use crate::core::logic::interpreter::conditions::{check_condition_frame, resolve_count};
use std::cell::Cell;

use crate::core::enums::*;
pub use crate::core::generated_constants::*;
use crate::core::hearts::*;
pub use crate::core::logic::models::*;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;
use std::borrow::Cow;

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct CachedCostModifier {
    pub source_cid: i32,
    pub amount: i16,
    pub target_mask: u8,  // bitmask for slots 0, 1, 2
    pub filter_mask: u64, // simplified filter (type, color, etc) - for now we'll just store the ability index
    pub ability_idx: u16,
}

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq, Eq, Hash)]
#[serde(default)]
pub struct BoardAura {
    pub blades: [i32; 3],
    pub hearts: [HeartBoard; 3],
    pub slot_cost_modifiers: [i16; 3],
    pub cost_modifiers: SmallVec<[CachedCostModifier; 4]>,
    pub heart_req_reductions: HeartBoard,
    pub heart_req_additions: HeartBoard,
}

thread_local! {
    static ON_DEMAND_AURA_QUERY: Cell<bool> = const { Cell::new(false) };
}

fn stage_card_id(state: &GameState, player_idx: usize, slot_idx: usize) -> i32 {
    state.players[player_idx].stage[slot_idx]
}

fn iter_stage_cards(state: &GameState, player_idx: usize) -> impl Iterator<Item = (usize, i32)> + '_ {
    (0..3).map(move |slot_idx| (slot_idx, stage_card_id(state, player_idx, slot_idx)))
}

fn stage_has_cost_13_or_more(state: &GameState, db: &CardDatabase) -> bool {
    (0..2).any(|player_idx| {
        state.players[player_idx]
            .stage
            .iter()
            .copied()
            .any(|cid| cid >= 0 && db.get_member(cid).map(|m| m.cost >= 13).unwrap_or(false))
    })
}

fn source_text_requires_cost_13_stage_gate(text: &str) -> bool {
    text.contains("コスト13以上") && text.contains("ステージ") && text.contains("ブレード")
}

fn frame_uses_count_multiplier(
    frame_data: &AbilityFrameComponents<'_>,
    has_per_card: bool,
) -> bool {
    frame_data.uses_count_multiplier() || has_per_card
}

fn cost_scope_frames<'a>(ab: &'a Ability) -> Cow<'a, [AbilityFrame]> {
    ab.resolved_frames()
}

fn ability_text<'a>(ab: &'a Ability, fallback: &'a str) -> &'a str {
    if !ab.raw_text.is_empty() {
        ab.raw_text.as_str()
    } else if !ab.pseudocode.is_empty() {
        ab.pseudocode.as_str()
    } else {
        fallback
    }
}

fn self_cost_zone_text_hint(text: &str) -> Option<Zone> {
    if text.contains("手札にあるこのメンバー") && text.contains("コスト") {
        Some(Zone::Hand)
    } else if text.contains("ステージにいるこのメンバー") && text.contains("コスト") {
        Some(Zone::Stage)
    } else {
        None
    }
}

fn is_hand_only_self_cost_modifier(
    source_text: &str,
    frame_data: &AbilityFrameComponents<'_>,
    op: i32,
) -> bool {
    if op != O_REDUCE_COST && op != O_INCREASE_COST {
        return false;
    }

    match self_cost_zone_text_hint(source_text) {
        Some(Zone::Hand) => return true,
        Some(Zone::Stage) => return false,
        _ => {}
    }

    let has_per_card = frame_data
        .params
        .and_then(|value| value.as_object())
        .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
        .is_some();

    if !frame_uses_count_multiplier(frame_data, has_per_card) {
        return false;
    }

    let count_zone = match frame_data.scale_source() {
        SemanticScaleSource::CountZone(zone) => Some(zone),
        SemanticScaleSource::SuccessPile => Some(SemanticCountZone::SuccessPile),
        SemanticScaleSource::None => match frame_data.count_opcode_hint(op == O_REDUCE_COST) {
            Some(C_COUNT_HAND) => Some(SemanticCountZone::Hand),
            Some(C_COUNT_DISCARD) => Some(SemanticCountZone::Discard),
            Some(C_COUNT_STAGE) => Some(SemanticCountZone::Stage),
            Some(C_COUNT_SUCCESS_LIVE) => Some(SemanticCountZone::SuccessPile),
            _ => None,
        },
    };

    matches!(count_zone, Some(SemanticCountZone::Hand))
        && frame_data.filter.target_player == TARGET_PLAYER_SELF as u8
        && (frame_data.filter.special_id == 3 || frame_data.compare_accumulated())
}

fn is_generic_cost_area_slot(raw_slot: i32) -> bool {
    matches!((raw_slot as u32) & 0xFF, 0 | 1 | 4)
}

fn inferred_tapped_group_requirement(ab: &Ability) -> Option<u8> {
    if !ab.conditions.is_empty() {
        return None;
    }

    if !ab.resolved_frames().iter().any(|frame| frame.opcode() == O_REDUCE_COST) {
        return None;
    }

    let text = if !ab.raw_text.is_empty() {
        ab.raw_text.as_str()
    } else {
        ab.pseudocode.as_str()
    };

    if text.contains("ウェイト状態")
        && (text.contains("虹ヶ咲") || text.contains("Nijigasaki"))
    {
        Some(GROUP_NIJIGASAKI as u8)
    } else {
        None
    }
}

fn stage_has_tapped_group_member(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    group_id: u8,
) -> bool {
    iter_stage_cards(state, player_idx).any(|(slot_idx, cid)| {
        cid >= 0
            && state.players[player_idx].is_tapped(slot_idx)
            && db.get_member(cid)
                .map(|member| member.groups.contains(&group_id))
                .unwrap_or(false)
    })
}

fn ability_conditions_met(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    ab: &Ability,
    ctx: &AbilityContext,
) -> bool {
    if let Some(group_id) = inferred_tapped_group_requirement(ab) {
        if !stage_has_tapped_group_member(state, db, player_idx, group_id) {
            return false;
        }
    }

    if !ab.conditions.is_empty()
        && !ab
            .conditions
            .iter()
            .all(|condition| check_condition(state, db, player_idx, condition, ctx, 1))
    {
        return false;
    }

    let frames = ab.resolved_frames();
    if frames.is_empty() {
        return true;
    }

    for frame in frames.iter() {
        let frame_data = frame.components();
        let has_raw_condition = frame_data
            .params
            .and_then(|value| value.as_object())
            .map(|params| params.get("raw_cond").is_some() || params.get("RAW_COND").is_some())
            .unwrap_or(false);
        let is_condition = has_raw_condition
            || (frame_data.opcode >= CONDITION_START_1 && frame_data.opcode <= CONDITION_END_1)
            || (frame_data.opcode >= CONDITION_START_2 && frame_data.opcode <= CONDITION_END_2);

        if !is_condition {
            continue;
        }

        if !check_condition_frame(state, db, &frame_data, ctx, 1) {
            return false;
        }
    }

    true
}

fn aura_target_mask(source_slot: usize, target_area: i32, attr: u64, has_filters: bool) -> u8 {
    if target_area == 1 {
        0b111
    } else if target_area == 4 {
        1 << source_slot
    } else if attr != 0 || has_filters {
        0b111
    } else {
        1 << source_slot
    }
}

fn get_query_aura(
    state: &GameState,
    player_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> Option<BoardAura> {
    if depth > MAX_BLADE_CALC_DEPTH {
        return None;
    }

    if ON_DEMAND_AURA_QUERY.with(|flag| flag.get()) {
        return None;
    }

    ON_DEMAND_AURA_QUERY.with(|flag| flag.set(true));
    let aura = calculate_board_aura(state, player_idx, db);
    ON_DEMAND_AURA_QUERY.with(|flag| flag.set(false));
    Some(aura)
}

pub fn get_effective_blades_with_aura(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    aura: &BoardAura,
) -> u32 {
    let cid = state.players[player_idx].stage[slot_idx];
    if cid < 0 || state.players[player_idx].is_tapped(slot_idx) {
        return 0;
    }
    let base_id = cid;
    let m = if let Some(m) = db.get_member(base_id) {
        m
    } else {
        return 0;
    };
    let mut val = if state.players[player_idx].blade_overrides[slot_idx] != -1 {
        state.players[player_idx].blade_overrides[slot_idx] as i32
    } else {
        m.blades as i32
    };

    val += aura.blades[slot_idx];

    let buff = state.players[player_idx].blade_buffs[slot_idx];
    if state.debug.debug_mode && !state.ui.silent {
        println!("[DEBUG] get_effective_blades: slot={}, base={}, override={:?}, val_accum={}, buff={}, total={}",
            slot_idx, m.blades, state.players[player_idx].blade_overrides[slot_idx], val, buff, (val + buff as i32).max(0));
    }
    (val + buff as i32).max(0) as u32
}

pub fn get_effective_hearts_with_aura(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    aura: &BoardAura,
) -> HeartBoard {
    let cid = state.players[player_idx].stage[slot_idx];
    if cid < 0 {
        return state.players[player_idx].heart_buffs[slot_idx];
    }
    let base_id = cid;
    let m = if let Some(m) = db.get_member(base_id) {
        m
    } else {
        return state.players[player_idx].heart_buffs[slot_idx];
    };
    let mut board = m.hearts_board.clone();

    board.add(aura.hearts[slot_idx]);
    board.add(state.players[player_idx].heart_buffs[slot_idx]);
    board
}

pub fn has_multi_baton(m: &MemberCard) -> u8 {
    if m.has_multi_baton {
        2
    } else {
        1
    }
}

fn apply_reduce_cost_modifiers(
    cost: &mut i32,
    ab: &Ability,
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    ctx: &AbilityContext,
    depth: u32,
) {
    if !ability_conditions_met(state, db, p_idx, ab, ctx) {
        return;
    }

    let mut applied_any_frame = false;
    let frames = cost_scope_frames(ab);
    for (frame_idx, frame) in frames.iter().enumerate() {

        let op = frame.opcode();
        if op != O_REDUCE_COST && op != O_INCREASE_COST {
            continue;
        }

        applied_any_frame = true;
        let val = frame.value();
        let frame_data = frame.components();
        let params = frame_data
            .params
            .or_else(|| ab.effects.get(frame_idx).map(|effect| &effect.params));
        let semantic = AbilityFrameComponents::from_raw_parts(
            frame_data.raw_opcode,
            frame_data.value,
            frame_data.raw_attr,
            frame_data.raw_slot,
            frame_data.is_cost,
            params,
        );

        let mut multiplier = 1;
        let per_card = params
            .and_then(|value| value.as_object())
            .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
            .and_then(|value| value.as_str())
            .map(|value| value.to_ascii_uppercase());
        if frame_uses_count_multiplier(&frame_data, per_card.is_some()) {
            if let Some(count_op) = semantic.count_opcode_hint(op == O_REDUCE_COST) {
                if state.debug.debug_mode && !state.ui.silent {
                    println!("[DEBUG] apply_reduce_cost_modifiers: count_op={}", count_op);
                }
                multiplier = resolve_count(
                    state,
                    db,
                    count_op,
                    frame_data.raw_attr,
                    frame_data.raw_slot,
                    ctx,
                    depth + 1,
                );
                if op == O_REDUCE_COST && multiplier > 0 {
                    let owner_idx = if frame_data.slot.is_opponent {
                        1 - p_idx
                    } else {
                        p_idx
                    };
                    let source_card_id = ctx.source_card_id;
                    let source_is_counted = match semantic.inferred_count_zone() {
                        Some(SemanticCountZone::Hand) => state.players[owner_idx]
                            .hand
                            .iter()
                            .any(|&id| id == source_card_id),
                        Some(SemanticCountZone::Discard) => state.players[owner_idx]
                            .discard
                            .iter()
                            .any(|&id| id == source_card_id),
                        Some(SemanticCountZone::Stage) => state.players[owner_idx]
                            .stage
                            .iter()
                            .any(|&id| id == source_card_id),
                        Some(SemanticCountZone::SuccessPile) => state.players[owner_idx]
                            .success_lives
                            .iter()
                            .any(|&id| id == source_card_id),
                        None if op == O_REDUCE_COST => state.players[owner_idx]
                            .hand
                            .iter()
                            .any(|&id| id == source_card_id),
                        None => false,
                    };
                    let source_checked_slot = match semantic.inferred_count_zone() {
                        Some(SemanticCountZone::Hand) => state.players[owner_idx]
                            .hand
                            .iter()
                            .position(|&id| id == source_card_id)
                            .map(|idx| (owner_idx as u8, 200 + idx as i16)),
                        Some(SemanticCountZone::Discard) => state.players[owner_idx]
                            .discard
                            .iter()
                            .position(|&id| id == source_card_id)
                            .map(|idx| (owner_idx as u8, 100 + idx as i16)),
                        Some(SemanticCountZone::Stage) => state.players[owner_idx]
                            .stage
                            .iter()
                            .position(|&id| id == source_card_id)
                            .map(|idx| (owner_idx as u8, idx as i16)),
                        Some(SemanticCountZone::SuccessPile) | None => None,
                    };
                    let source_matches_filter = if semantic.raw_attr == 0 {
                        true
                    } else if let Some(slot) = source_checked_slot {
                        state.card_matches_filter_with_struct(
                            db,
                            source_card_id,
                            Some(slot),
                            &semantic.filter,
                            ctx,
                        )
                    } else {
                        state.card_matches_filter_with_ctx(
                            db,
                            source_card_id,
                            semantic.raw_attr,
                            ctx,
                        )
                    };
                    let should_exclude_source = source_is_counted
                        && source_matches_filter
                        && (semantic.slot.source_zone != Zone::Default
                            || semantic.compare_accumulated()
                            || per_card.is_some());
                    if should_exclude_source {
                        multiplier -= 1;
                    }
                }
            }
        }
        if op == O_REDUCE_COST {
            *cost -= val * multiplier;
        } else {
            *cost += val * multiplier;
        }
    }

    if !applied_any_frame && !ab.preparsed_modifiers.is_empty() {
        for pm in &ab.preparsed_modifiers {
            if (pm.op == O_REDUCE_COST || pm.op == O_INCREASE_COST)
                && ((pm.slot as u32) & 0xFF == 0 || (pm.slot as u32) & 0xFF == 4)
            {
                let mut multiplier = 1;
                if (pm.attr & DYNAMIC_VALUE) != 0 {
                    let count_op = (pm.slot >> 8) & 0xFFFF;
                    multiplier = resolve_count(
                        state,
                        db,
                        count_op as i32,
                        pm.attr & !DYNAMIC_VALUE,
                        pm.slot,
                        ctx,
                        depth + 1,
                    );
                }
                if pm.op == O_REDUCE_COST {
                    *cost -= pm.val * multiplier;
                } else {
                    *cost += pm.val * multiplier;
                }
            }
        }
    }
}

#[allow(dead_code)]
fn apply_external_reduce_cost_modifiers(
    cost: &mut i32,
    ab: &Ability,
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    ctx: &AbilityContext,
    _target_card_id: i32,
    _depth: u32,
) {
    if !ab.has_resolved_frames() || !ability_conditions_met(state, db, p_idx, ab, ctx) {
        return;
    }

    let frames = cost_scope_frames(ab);
    for frame in frames.iter() {
        let op = frame.opcode();
        if op == O_REDUCE_COST {
            *cost -= frame.value();
        } else if op == O_INCREASE_COST {
            *cost += frame.value();
        }
    }
}

pub fn get_effective_blades(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> u32 {
    if depth > MAX_BLADE_CALC_DEPTH {
        return 0;
    }
    let query_aura = get_query_aura(state, player_idx, db, depth);
    let aura = query_aura
        .as_ref()
        .unwrap_or(&state.players[player_idx].board_aura);
    get_effective_blades_with_aura(state, player_idx, slot_idx, db, aura)
}

pub fn get_effective_hearts(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> HeartBoard {
    if depth > MAX_BLADE_CALC_DEPTH {
        return HeartBoard::default();
    }
    let query_aura = get_query_aura(state, player_idx, db, depth);
    let aura = query_aura
        .as_ref()
        .unwrap_or(&state.players[player_idx].board_aura);
    get_effective_hearts_with_aura(state, player_idx, slot_idx, db, aura)
}

pub fn get_total_blades(state: &GameState, p_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
    if let Some(aura) = get_query_aura(state, p_idx, db, depth) {
        let mut total = 0u32;
        for i in 0..3 {
            total += get_effective_blades_with_aura(state, p_idx, i, db, &aura);
        }
        return total;
    }
    let mut total = 0u32;
    for i in 0..3 {
        total += get_effective_blades(state, p_idx, i, db, depth + 1);
    }
    total
}

pub fn get_total_hearts(
    state: &GameState,
    p_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> HeartBoard {
    if let Some(aura) = get_query_aura(state, p_idx, db, depth) {
        let mut total = HeartBoard::default();
        for i in 0..3 {
            total.add(get_effective_hearts_with_aura(state, p_idx, i, db, &aura));
        }
        return total;
    }
    let mut total = HeartBoard::default();
    for i in 0..3 {
        total.add(get_effective_hearts(state, p_idx, i, db, depth + 1));
    }
    total
}

pub fn get_effective_member_hearts(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> HeartBoard {
    get_effective_hearts(state, player_idx, slot_idx, db, depth + 1)
}

pub fn get_total_member_hearts(
    state: &GameState,
    p_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> HeartBoard {
    let mut total = HeartBoard::default();
    for i in 0..3 {
        total.add(get_effective_member_hearts(state, p_idx, i, db, depth + 1));
    }
    total
}

pub fn calculate_cost_delta(
    state: &GameState,
    db: &CardDatabase,
    card_id: i32,
    p_idx: usize,
) -> i32 {
    let effective = get_member_cost(state, p_idx, card_id, -1, -1, db, 0);
    if let Some(m) = db.get_member(card_id) {
        effective - (m.cost as i32)
    } else {
        0
    }
}

pub fn get_member_cost(
    state: &GameState,
    p_idx: usize,
    card_id: i32,
    slot_idx: i16,
    secondary_slot_idx: i16,
    db: &CardDatabase,
    depth: u32,
) -> i32 {
    if depth > MAX_BLADE_CALC_DEPTH {
        return 0;
    } // Recursion limit
    let base_id = card_id;
    let m = if let Some(m) = db.get_member(base_id) {
        m
    } else {
        return 0;
    };
    let has_baton_source = [slot_idx, secondary_slot_idx].into_iter().any(|candidate_slot| {
        candidate_slot >= 0
            && candidate_slot < STAGE_SLOT_COUNT as i16
            && state.players[p_idx].stage[candidate_slot as usize] >= 0
    });
    let projected_state = has_baton_source.then(|| {
        let mut projected = state.clone();
        for candidate_slot in [slot_idx, secondary_slot_idx] {
            if candidate_slot >= 0 && candidate_slot < STAGE_SLOT_COUNT as i16 {
                projected.players[p_idx].stage[candidate_slot as usize] = -1;
            }
        }
        projected
    });
    let cost_state = projected_state.as_ref().unwrap_or(state);
    let mut cost = m.cost as i32;
    if state.debug.debug_mode && !state.ui.silent {
        println!(
            "[DEBUG] get_member_cost: card_id={}, base_cost={}",
            card_id, cost
        );
    }
    let query_aura = get_query_aura(cost_state, p_idx, db, depth);
    let mut fallback_aura: Option<BoardAura> = None;
    if state.debug.debug_mode && !state.ui.silent {
        println!(
            "[DEBUG] get_member_cost aura query: slot_idx={}, query_aura_present={}, cached_modifiers={}",
            slot_idx,
            query_aura.is_some(),
            state.players[p_idx].board_aura.cost_modifiers.len()
        );
    }

    // 1. Global reduction
    cost -= cost_state.players[p_idx].cost_reduction as i32;
    // 1b. Target card's own constant cost modifiers while it is in hand.
    // These are not part of the board aura because the source card is not on stage yet.
    if let Some(hand_idx) = cost_state.players[p_idx].hand.iter().position(|&id| id == card_id) {
        if let Some(target_m) = db.get_member(card_id) {
            let ctx = AbilityContext {
                source_card_id: card_id,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: 200 + hand_idx as i16,
                is_static_eval: true,
                ..Default::default()
            };
            for (idx, ab) in target_m.abilities.iter().enumerate() {
                if state.debug.debug_mode && !state.ui.silent {
                    println!("[DEBUG] get_member_cost: Checking ab#{}, trigger={:?}", idx, ab.trigger);
                }
                if matches!(ab.trigger, TriggerType::Constant | TriggerType::TurnStart) {
                    let source_text = ability_text(ab, target_m.original_text.as_str());
                    let applies_while_in_hand = cost_scope_frames(ab).iter().any(|frame| {
                        let frame_data = frame.components();
                        is_hand_only_self_cost_modifier(
                            source_text,
                            &frame_data,
                            frame_data.opcode,
                        )
                    });
                    if !applies_while_in_hand {
                        continue;
                    }
                    if state.debug.debug_mode && !state.ui.silent {
                        println!("[DEBUG] get_member_cost: Applying cost modifier ab#{}", idx);
                    }
                    // Evaluate the source card's own constant cost modifiers against the
                    // real board state. Baton Touch still needs the tapped source member
                    // present here so card-specific reductions can see it before the slot
                    // replacement is applied.
                    apply_reduce_cost_modifiers(&mut cost, ab, state, db, p_idx, &ctx, depth + 1);
                }
            }
        }
    }

    // 2. Baton Touch & Cached Position Modifiers (Rule 12 & Auras)
    if slot_idx >= 0 && slot_idx < STAGE_SLOT_COUNT as i16 {
        let aura_ref = query_aura
            .as_ref()
            .unwrap_or(&cost_state.players[p_idx].board_aura);
        cost += aura_ref.slot_cost_modifiers[slot_idx as usize] as i32;

        for modif in &aura_ref.cost_modifiers {
            if (modif.target_mask & (1 << slot_idx)) != 0 {
                // Check filters if any
                let mut apply = true;
                if modif.filter_mask != 0 {
                    let src_ctx = AbilityContext {
                        source_card_id: modif.source_cid,
                        player_id: p_idx as u8,
                        activator_id: p_idx as u8,
                        area_idx: -1,
                        is_static_eval: true,
                        ..Default::default()
                    };
                    if !cost_state.card_matches_filter_with_ctx(db, card_id, modif.filter_mask, &src_ctx)
                    {
                        apply = false;
                    }
                } else if let Some(src_m) = db.get_member(modif.source_cid) {
                    if let Some(ab) = src_m.abilities.get(modif.ability_idx as usize) {
                        // Filters are now in frame_program, skip filter check for now
                        let _ = ab;
                    }
                }
                if apply {
                    cost -= modif.amount as i32;
                }
            }
        }

        let old_cid = state.players[p_idx].stage[slot_idx as usize];
        if old_cid >= 0 {
            if let Some(old_m) = db.get_member(old_cid) {
                cost -= old_m.cost as i32;
            }
        }

    } else {
        let aura_ref = if let Some(aura) = query_aura.as_ref() {
            aura
        } else {
            fallback_aura.get_or_insert_with(|| calculate_board_aura(cost_state, p_idx, db))
        };

        for modif in &aura_ref.cost_modifiers {
            let mut apply = true;
            if modif.filter_mask != 0 {
                let src_ctx = AbilityContext {
                    source_card_id: modif.source_cid,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: -1,
                    is_static_eval: true,
                    ..Default::default()
                };
                if !cost_state.card_matches_filter_with_ctx(db, card_id, modif.filter_mask, &src_ctx) {
                    apply = false;
                }
            } else if let Some(src_m) = db.get_member(modif.source_cid) {
                if let Some(ab) = src_m.abilities.get(modif.ability_idx as usize) {
                    // Filters are now in frame_program, skip filter check for now
                    let _ = ab;
                }
            }
            if apply {
                cost -= modif.amount as i32;
            }
        }
    }

    if secondary_slot_idx >= 0 && secondary_slot_idx < STAGE_SLOT_COUNT as i16 {
        let old_cid = state.players[p_idx].stage[secondary_slot_idx as usize];
        if old_cid >= 0 {
            if let Some(old_m) = db.get_member(old_cid) {
                cost -= old_m.cost as i32;
            }
        }
    }

    // VANILLA MODE: Skip constant ability cost reductions in abilityless mode
    if db.is_truly_vanilla() {
        return cost.max(0);
    }

    // Phase 2 Optimization: Constant ability cost reductions are now pre-calculated in BoardAura.
    // We no longer need to iterate over source slots or granted abilities here.

    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities {
        if state.debug.debug_mode && !state.ui.silent {
            println!("[DEBUG] get_member_cost: checking granted ability target={} source={} ab_idx={} for card_id={}", target_cid, source_cid, ab_idx, card_id);
        }
        if target_cid != card_id {
            continue;
        }

        let Some(src_m) = db.get_member(source_cid) else {
            if state.debug.debug_mode && !state.ui.silent {
                println!("[DEBUG] get_member_cost: source card {} not found", source_cid);
            }
            continue;
        };
        let Some(ab) = src_m.abilities.get(ab_idx as usize) else {
            if state.debug.debug_mode && !state.ui.silent {
                println!("[DEBUG] get_member_cost: ability {} not found on source {}", ab_idx, source_cid);
            }
            continue;
        };
        if ab.trigger != TriggerType::Constant {
            if state.debug.debug_mode && !state.ui.silent {
                println!("[DEBUG] get_member_cost: ability trigger is {:?}, not Constant", ab.trigger);
            }
            continue;
        }

        if state.debug.debug_mode && !state.ui.silent {
            println!("[DEBUG] get_member_cost: applying granted ability from {} ab#{}", source_cid, ab_idx);
        }
        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: slot_idx,
            is_static_eval: true,
            ..Default::default()
        };
        apply_reduce_cost_modifiers(&mut cost, ab, cost_state, db, p_idx, &ctx, depth + 1);
        if state.debug.debug_mode && !state.ui.silent {
            println!("[DEBUG] get_member_cost: after granted ability, cost={}", cost);
        }
    }

    // 5. Temporary cost modifiers (From Action Phase triggers)
    for (cond, amount) in &state.players[p_idx].cost_modifiers {
        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: slot_idx as i16,
            is_static_eval: true,
            ..Default::default()
        };
        if check_condition(cost_state, db, p_idx, cond, &ctx, depth + 1) {
            cost += *amount;
        }
    }

    cost.max(0)
}

pub fn has_restriction(
    state: &GameState,
    p_idx: usize,
    slot_idx: usize,
    opcode: i32,
    db: &CardDatabase,
) -> bool {
    // VANILLA MODE: No restrictions from abilities in abilityless mode
    if db.is_truly_vanilla() {
        return false;
    }

    let cid = state.players[p_idx].stage[slot_idx];
    if cid < 0 {
        return false;
    }
    let m = if let Some(m) = db.get_member(cid) {
        m
    } else {
        return false;
    };

    let opcode_bit = 1u128 << (opcode as u32 % 128);
    let has_fast_opcode = (m.ability_opcodes_mask & opcode_bit) != 0;

    // 1. Self constant abilities
    for ab in &m.abilities {
        if ab.trigger == TriggerType::Constant {
            let frames = ab.resolved_frames();
            let has_opcode = (ab.opcodes_mask & opcode_bit) != 0
                || frames.iter().any(|frame| frame.opcode() == opcode)
                || ab.effects.iter().any(|effect| {
                    let effect_opcode = if effect.runtime_opcode != 0 {
                        effect.runtime_opcode
                    } else {
                        AbilityFrame::opcode_from_effect_type(effect.effect_type)
                    };
                    effect_opcode == opcode
                });
            if has_opcode {
                let ctx = AbilityContext {
                    source_card_id: cid,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: slot_idx as i16,
                    is_static_eval: true,
                    ..Default::default()
                };
                if ab
                    .conditions
                    .iter()
                    .all(|c| check_condition(state, db, p_idx, c, &ctx, 0))
                {
                    if frames.iter().any(|frame| frame.opcode() == opcode)
                        || ab.effects.iter().any(|effect| {
                            let effect_opcode = if effect.runtime_opcode != 0 {
                                effect.runtime_opcode
                            } else {
                                AbilityFrame::opcode_from_effect_type(effect.effect_type)
                            };
                            effect_opcode == opcode
                        })
                    {
                        return true;
                    }
                }
            }
        }
    }

    // 2. Granted constant abilities
    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities {
        if target_cid != cid {
            continue;
        }
        if let Some(src_m) = db.get_member(source_cid) {
            if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                if ab.trigger == TriggerType::Constant {
                    let frames = ab.resolved_frames();
                    let has_opcode = (ab.opcodes_mask & opcode_bit) != 0
                        || frames.iter().any(|frame| frame.opcode() == opcode)
                        || ab.effects.iter().any(|effect| {
                            let effect_opcode = if effect.runtime_opcode != 0 {
                                effect.runtime_opcode
                            } else {
                                AbilityFrame::opcode_from_effect_type(effect.effect_type)
                            };
                            effect_opcode == opcode
                        });
                    if has_opcode {
                        let ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            is_static_eval: true,
                            ..Default::default()
                        };
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, p_idx, c, &ctx, 0))
                        {
                            if frames.iter().any(|frame| frame.opcode() == opcode)
                                || ab.effects.iter().any(|effect| {
                                    let effect_opcode = if effect.runtime_opcode != 0 {
                                        effect.runtime_opcode
                                    } else {
                                        AbilityFrame::opcode_from_effect_type(effect.effect_type)
                                    };
                                    effect_opcode == opcode
                                })
                            {
                                return true;
                            }
                        }
                    }
                }
            }
        }
    }

    if !has_fast_opcode {
        return false;
    }

    false
}

pub fn calculate_board_aura(state: &GameState, player_idx: usize, db: &CardDatabase) -> BoardAura {
    let mut aura = BoardAura::default();
    if db.is_truly_vanilla() {
        return aura;
    }

    // 1. Constant abilities from members on stage
    for (source_slot, cid) in iter_stage_cards(state, player_idx) {
        if cid < 0 {
            continue;
        }
        if state.debug.debug_mode && !state.ui.silent {
            println!(
                "[DEBUG] calculate_board_aura: player={}, source_slot={}, cid={}",
                player_idx, source_slot, cid
            );
        }
        let Some(m) = db.get_member(cid) else {
            continue;
        };

        for (ab_idx, ab) in m.abilities.iter().enumerate() {
            if ab.trigger != TriggerType::Constant {
                continue;
            }

            let ctx = AbilityContext {
                source_card_id: cid,
                player_id: player_idx as u8,
                activator_id: player_idx as u8,
                area_idx: source_slot as i16,
                is_static_eval: true,
                ..Default::default()
            };

            if !ability_conditions_met(state, db, player_idx, ab, &ctx) {
                if state.debug.debug_mode && !state.ui.silent {
                    println!(
                        "[DEBUG] calculate_board_aura: ability {} on cid {} failed conditions",
                        ab_idx, cid
                    );
                }
                continue;
            }

            let frames = cost_scope_frames(ab);
            let has_filters = !frames.is_empty();
            let source_text = ability_text(ab, m.original_text.as_str());

            for frame in frames.iter() {
                let frame_data = frame.components();
                let op = frame_data.opcode;
                let v = frame_data.value;
                let a = frame_data.resolved_filter_attr();
                let s = frame_data.raw_slot;
                let params = frame_data.params;
                let target_area = frame_data.target_area();
                let target_mask = aura_target_mask(source_slot, target_area, a, has_filters);

                if op == O_REDUCE_COST || op == O_INCREASE_COST {
                    if is_hand_only_self_cost_modifier(source_text, &frame_data, op) {
                        continue;
                    }
                    aura.cost_modifiers.push(CachedCostModifier {
                        source_cid: cid,
                        amount: if op == O_REDUCE_COST {
                            v as i16
                        } else {
                            -(v as i16)
                        },
                        target_mask,
                        filter_mask: a & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK,
                        ability_idx: ab_idx as u16,
                    });
                } else {
                    for target_slot in 0..3 {
                        if (target_mask & (1 << target_slot)) != 0 {
                            apply_aura_modifier(
                                &mut aura,
                                op,
                                v,
                                s,
                                a,
                                params,
                                &ctx,
                                state,
                                db,
                                player_idx,
                                target_slot,
                            );
                        }
                    }
                }
            }
        }
    }

    // 2. Granted constant abilities from members on stage or in live zone
    for slot_idx in 0..6 {
        let cid = if slot_idx < 3 {
            stage_card_id(state, player_idx, slot_idx)
        } else {
            state.players[player_idx].live_zone[slot_idx - 3]
        };
        if cid < 0 {
            continue;
        }

        for &(target_cid, source_cid, ab_idx) in &state.players[player_idx].granted_abilities {
            if target_cid != cid {
                continue;
            }

            let Some(src_m) = db.get_member(source_cid) else {
                continue;
            };

            let Some(ab) = src_m.abilities.get(ab_idx as usize) else {
                continue;
            };

            if ab.trigger != TriggerType::Constant {
                continue;
            }

            let ctx = AbilityContext {
                source_card_id: cid,
                player_id: player_idx as u8,
                activator_id: player_idx as u8,
                area_idx: if slot_idx < 3 { slot_idx as i16 } else { -1 },
                is_static_eval: true,
                ..Default::default()
            };

            if !ability_conditions_met(state, db, player_idx, ab, &ctx) {
                continue;
            }

            let frames = cost_scope_frames(ab);
            let source_text = ability_text(ab, src_m.original_text.as_str());
            let target_mask = if slot_idx < 3 {
                if let Some(first_frame) = frames.first() {
                    let first_frame_data = first_frame.components();
                    let target_area = first_frame_data.target_area();
                    let runtime_attr = first_frame_data.resolved_filter_attr();
                    aura_target_mask(slot_idx, target_area, runtime_attr, !frames.is_empty())
                } else {
                    0b111
                }
            } else {
                0
            };

            for frame in frames.iter() {
                let frame_data = frame.components();
                let op = frame_data.opcode;
                let v = frame_data.value;
                let a = frame_data.resolved_filter_attr();
                let s = frame_data.raw_slot;

                if op == O_REDUCE_COST || op == O_INCREASE_COST {
                    if is_hand_only_self_cost_modifier(source_text, &frame_data, op) {
                        continue;
                    }
                    aura.cost_modifiers.push(CachedCostModifier {
                        source_cid,
                        amount: if op == O_REDUCE_COST {
                            v as i16
                        } else {
                            -(v as i16)
                        },
                        target_mask,
                        filter_mask: a & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK,
                        ability_idx: ab_idx as u16,
                    });
                } else if slot_idx < 3 {
                    apply_aura_modifier(
                        &mut aura,
                        op,
                        v,
                        s,
                        a,
                        frame_data.params,
                        &ctx,
                        state,
                        db,
                        player_idx,
                        slot_idx,
                    );
                }
            }
        }
    }

    aura
}

fn apply_aura_modifier(
    aura: &mut BoardAura,
    op: i32,
    v: i32,
    s: i32,
    a: u64,
    params: Option<&serde_json::Value>,
    ctx: &AbilityContext,
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    target_slot: usize,
) {
    let semantic = AbilityFrameComponents::from_raw_parts(op, v, a, s, false, params);
    let source_text = db
        .get_member(ctx.source_card_id)
        .map(|member| member.original_text.as_str())
        .unwrap_or("");

    let value = if v > 0xFFFF { v & 0xFFFF } else { v };
    let mut multiplier = 1;
    if let Some(count_op) = semantic.embedded_count_opcode() {
        multiplier = resolve_count(state, db, count_op, a, s, ctx, 2);
    }

    if multiplier == 1 {
        multiplier = match semantic.scale_source() {
            SemanticScaleSource::None => multiplier,
            SemanticScaleSource::SuccessPile => state.players[p_idx].success_lives.len() as i32,
            SemanticScaleSource::CountZone(SemanticCountZone::Hand) => {
                state.players[p_idx].hand.len() as i32
            }
            SemanticScaleSource::CountZone(SemanticCountZone::Discard) => {
                state.players[p_idx].discard.len() as i32
            }
            SemanticScaleSource::CountZone(SemanticCountZone::Stage) => state.players[p_idx]
                .stage
                .iter()
                .copied()
                .filter(|&cid| cid >= 0)
                .count() as i32,
            SemanticScaleSource::CountZone(SemanticCountZone::SuccessPile) => {
                state.players[p_idx].success_lives.len() as i32
            }
        };
    }

    match op {
        O_ADD_BLADES | O_BUFF_POWER => {
            if op == O_ADD_BLADES
                && source_text_requires_cost_13_stage_gate(source_text)
                && !stage_has_cost_13_or_more(state, db)
            {
                return;
            }
            if semantic.scale_source() == SemanticScaleSource::SuccessPile {
                multiplier = state.players[p_idx].success_lives.len() as i32;
            }
            aura.blades[target_slot] += value * multiplier;
        }
        O_ADD_HEARTS => {
            if (a & 0x02) != 0 {
                let count_op = semantic.embedded_count_opcode().unwrap_or(0) & 0xFF;
                if count_op != 0 {
                    multiplier = resolve_count(state, db, count_op, a, count_op, ctx, 2);
                }
            }
            let color = semantic.resolved_color_index(ctx.selected_color as usize, 6);
            if color < 7 {
                aura.hearts[target_slot].add_to_color(color, value * multiplier);
            }
        }
        O_REDUCE_COST => {
            if is_generic_cost_area_slot(s) {
                aura.slot_cost_modifiers[target_slot] -= value as i16 * multiplier as i16;
            }
        }
        O_INCREASE_COST => {
            if is_generic_cost_area_slot(s) {
                aura.slot_cost_modifiers[target_slot] += value as i16 * multiplier as i16;
            }
        }
        O_REDUCE_HEART_REQ => {
            let color = semantic.resolved_color_index(6, 6);
            if color < 7 {
                aura.heart_req_reductions
                    .add_to_color(color, value * multiplier);
            }
        }
        O_INCREASE_HEART_COST => {
            let color = semantic.resolved_color_index(6, 6);
            if color < 7 {
                aura.heart_req_additions
                    .add_to_color(color, value * multiplier);
            }
        }
        O_SET_HEART_COST => {
            for i in 0..6 {
                let req_val = (a >> (i * 4)) & 0xF;
                if req_val > 0 {
                    aura.heart_req_reductions.add_to_color(i, -(req_val as i32));
                }
            }
            if value > 0 {
                let color = semantic.resolved_color_index(ctx.selected_color as usize, 6);
                if color < 7 {
                    aura.hearts[target_slot].add_to_color(color, value);
                }
            }
        }
        _ => {}
    }
}
