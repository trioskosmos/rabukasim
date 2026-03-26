use super::card_db::{CardDatabase, MemberCard};
use super::game::GameState;
use crate::core::logic::interpreter::check_condition;
use crate::core::logic::interpreter::conditions::{check_condition_frame, resolve_count};
use std::cell::Cell;

use crate::core::enums::*;
pub use crate::core::generated_constants::*;
use crate::core::hearts::*;
use crate::core::logic::heart_semantics::decode_heart_type_from_params;
pub use crate::core::logic::models::*;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

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

fn ability_conditions_met(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    ab: &Ability,
    ctx: &AbilityContext,
) -> bool {
    if !ab.conditions.is_empty() {
        return ab
            .conditions
            .iter()
            .all(|condition| check_condition(state, db, player_idx, condition, ctx, 1));
    }

    let frames = ab.frames();
    if frames.is_empty() {
        return true;
    }

    let mut saw_condition = false;
    for frame in &frames {
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
            if saw_condition {
                break;
            }
            continue;
        }

        saw_condition = true;
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

    let mut frame_idx = 0;
    let mut applied_any_frame = false;
    loop {
        let Some(frame) = ab.get_frame(frame_idx) else {
            break;
        };
        frame_idx += 1;

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

        let mut multiplier = 1;
        let per_card = params
            .and_then(|value| value.as_object())
            .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
            .and_then(|value| value.as_str())
            .map(|value| value.to_ascii_uppercase());

        if frame_data.slot.is_dynamic || frame_data.filter.compare_accumulated || per_card.is_some()
        {
            let count_op = if let Some(ref per_card) = per_card {
                match per_card.as_str() {
                    "HAND" => C_COUNT_HAND,
                    "DISCARD" | "DISCARD_COUNT" => C_COUNT_DISCARD,
                    "SUCCESS_LIVE" | "SUCCESS_PILE" | "COUNT" | "COUNT_VAL" => C_COUNT_SUCCESS_LIVE,
                    "STAGE" => C_COUNT_STAGE,
                    _ => 0,
                }
            } else {
                match frame_data.slot.source_zone {
                    Zone::Hand => C_COUNT_HAND,
                    Zone::Discard => C_COUNT_DISCARD,
                    Zone::Stage => C_COUNT_STAGE,
                    Zone::SuccessPile => C_COUNT_SUCCESS_LIVE,
                    _ => 0,
                }
            };

            if count_op != 0 {
                multiplier = resolve_count(
                    state,
                    db,
                    count_op,
                    frame_data.raw_attr,
                    frame_data.raw_slot,
                    ctx,
                    depth + 1,
                );
                if op == O_REDUCE_COST
                    && frame_data.filter.special_id == 0
                    && frame_data.raw_attr == 0
                    && multiplier > 0
                {
                    let owner_idx = if frame_data.slot.is_opponent {
                        1 - p_idx
                    } else {
                        p_idx
                    };
                    let source_card_id = ctx.source_card_id;
                    let source_is_counted = match frame_data.slot.source_zone {
                        Zone::Hand => state.players[owner_idx]
                            .hand
                            .iter()
                            .any(|&id| id == source_card_id),
                        Zone::Stage => state.players[owner_idx]
                            .stage
                            .iter()
                            .any(|&id| id == source_card_id),
                        Zone::Discard => state.players[owner_idx]
                            .discard
                            .iter()
                            .any(|&id| id == source_card_id),
                        Zone::SuccessPile => state.players[owner_idx]
                            .success_lives
                            .iter()
                            .any(|&id| id == source_card_id),
                        _ => false,
                    };
                    if source_is_counted {
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
    target_card_id: i32,
    _depth: u32,
) {
    if ab.filters.is_empty() || !ability_conditions_met(state, db, p_idx, ab, ctx) {
        return;
    }

    if !ab
        .filters
        .iter()
        .any(|filter| filter.matches(state, db, target_card_id, None, false, None, ctx))
    {
        return;
    }

    for pm in &ab.preparsed_modifiers {
        if pm.op == O_REDUCE_COST || pm.op == O_INCREASE_COST {
            if pm.op == O_REDUCE_COST {
                *cost -= pm.val;
            } else {
                *cost += pm.val;
            }
        }
    }

    if !ab.preparsed_modifiers.is_empty() {
        return;
    }

    for frame in ab.frames() {
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
    let mut cost = m.cost as i32;
    if state.debug.debug_mode && !state.ui.silent {
        println!(
            "[DEBUG] get_member_cost: card_id={}, base_cost={}",
            card_id, cost
        );
    }

    let query_aura = get_query_aura(state, p_idx, db, depth);
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
    cost -= state.players[p_idx].cost_reduction as i32;

    // 1b. Target card's own constant cost modifiers while it is in hand.
    // These are not part of the board aura because the source card is not on stage yet.
    if !state.players[p_idx].stage.iter().any(|&cid| cid == card_id) {
        if let Some(target_m) = db.get_member(card_id) {
            let ctx = AbilityContext {
                source_card_id: card_id,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: slot_idx,
                ..Default::default()
            };
            for ab in &target_m.abilities {
                if ab.trigger == TriggerType::Constant {
                    apply_reduce_cost_modifiers(&mut cost, ab, state, db, p_idx, &ctx, depth + 1);
                }
            }
        }
    }

    // 2. Baton Touch & Cached Position Modifiers (Rule 12 & Auras)
    if slot_idx >= 0 && slot_idx < STAGE_SLOT_COUNT as i16 {
        let aura_ref = query_aura
            .as_ref()
            .unwrap_or(&state.players[p_idx].board_aura);
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
                        ..Default::default()
                    };
                    if !state.card_matches_filter_with_ctx(db, card_id, modif.filter_mask, &src_ctx)
                    {
                        apply = false;
                    }
                } else if let Some(src_m) = db.get_member(modif.source_cid) {
                    if let Some(ab) = src_m.abilities.get(modif.ability_idx as usize) {
                        if !ab.filters.is_empty() {
                            let src_ctx = AbilityContext {
                                source_card_id: modif.source_cid,
                                player_id: p_idx as u8,
                                activator_id: p_idx as u8,
                                area_idx: -1, // Not used for constant card filters
                                ..Default::default()
                            };
                            if !ab.filters.iter().any(
                                |f: &crate::core::logic::filter::CardFilter| {
                                    f.matches(state, db, card_id, None, false, None, &src_ctx)
                                },
                            ) {
                                apply = false;
                            }
                        }
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
            fallback_aura.get_or_insert_with(|| calculate_board_aura(state, p_idx, db))
        };

        for modif in &aura_ref.cost_modifiers {
            let mut apply = true;
            if modif.filter_mask != 0 {
                let src_ctx = AbilityContext {
                    source_card_id: modif.source_cid,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: -1,
                    ..Default::default()
                };
                if !state.card_matches_filter_with_ctx(db, card_id, modif.filter_mask, &src_ctx) {
                    apply = false;
                }
            } else if let Some(src_m) = db.get_member(modif.source_cid) {
                if let Some(ab) = src_m.abilities.get(modif.ability_idx as usize) {
                    if !ab.filters.is_empty() {
                        let src_ctx = AbilityContext {
                            source_card_id: modif.source_cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: -1,
                            ..Default::default()
                        };
                        if !ab
                            .filters
                            .iter()
                            .any(|f: &crate::core::logic::filter::CardFilter| {
                                f.matches(state, db, card_id, None, false, None, &src_ctx)
                            })
                        {
                            apply = false;
                        }
                    }
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
        if target_cid != card_id {
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
            source_card_id: card_id,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: slot_idx,
            ..Default::default()
        };
        apply_reduce_cost_modifiers(&mut cost, ab, state, db, p_idx, &ctx, depth + 1);
    }

    // 5. Temporary cost modifiers (From Action Phase triggers)
    for (cond, amount) in &state.players[p_idx].cost_modifiers {
        let ctx = AbilityContext {
            source_card_id: card_id,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: slot_idx as i16,
            ..Default::default()
        };
        if check_condition(state, db, p_idx, cond, &ctx, depth + 1) {
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

    // Fast rejection via bitmask
    if (m.ability_opcodes_mask & (1u128 << (opcode as u32 % 128))) == 0 {
        return false;
    }

    // 1. Self constant abilities
    if (m.effect_mask & EFFECT_MASK_RULE) != 0 {
        for ab in &m.abilities {
            if ab.trigger == TriggerType::Constant {
                if (ab.opcodes_mask & (1u128 << (opcode as u32 % 128))) != 0 {
                    let ctx = AbilityContext {
                        source_card_id: cid,
                        player_id: p_idx as u8,
                        activator_id: p_idx as u8,
                        area_idx: slot_idx as i16,
                        ..Default::default()
                    };
                    if ab
                        .conditions
                        .iter()
                        .all(|c| check_condition(state, db, p_idx, c, &ctx, 0))
                    {
                        if let Some(frame_program) = ab.frame_program.as_ref() {
                            for frame in &frame_program.frames {
                                if frame.opcode() == opcode {
                                    return true;
                                }
                            }
                        }
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
                    if (ab.opcodes_mask & (1u128 << (opcode as u32 % 128))) != 0 {
                        let ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, p_idx, c, &ctx, 0))
                        {
                            if let Some(frame_program) = ab.frame_program.as_ref() {
                                for frame in &frame_program.frames {
                                    if frame.opcode() == opcode {
                                        return true;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    false
}

pub fn calculate_board_aura(state: &GameState, player_idx: usize, db: &CardDatabase) -> BoardAura {
    let mut aura = BoardAura::default();
    if db.is_truly_vanilla() {
        return aura;
    }

    // 1. Constant abilities from members on stage
    for source_slot in 0..3 {
        let cid = state.players[player_idx].stage[source_slot];
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

            if !ab.preparsed_modifiers.is_empty() {
                let effect_params = ab.effects.first().map(|effect| &effect.params);
                for pm in &ab.preparsed_modifiers {
                    let op = pm.op;
                    let v = pm.val;
                    let s = pm.slot;
                    let a = pm.attr;
                    let target_area = s & 0xFF;

                    let target_mask =
                        aura_target_mask(source_slot, target_area, a, !ab.filters.is_empty());

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
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
                                    effect_params,
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
            } else if let Some(frame_program) = ab.frame_program.as_ref() {
                for (frame_idx, frame) in frame_program.frames.iter().enumerate() {
                    let frame_data = frame.components();
                    let op = frame_data.opcode;
                    let v = frame_data.value;
                    let a = frame_data.raw_attr;
                    let s = frame_data.raw_slot;
                    let params = frame_data
                        .params
                        .or_else(|| ab.effects.get(frame_idx).map(|effect| &effect.params));

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
                        let target_area = s & 0xFF;
                        let target_mask =
                            aura_target_mask(source_slot, target_area, a, !ab.filters.is_empty());
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
                            source_slot,
                        );
                    }
                }
            }
        }
    }

    // 2. Granted constant abilities from members on stage or in live zone
    for slot_idx in 0..6 {
        let cid = if slot_idx < 3 {
            state.players[player_idx].stage[slot_idx]
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
                ..Default::default()
            };

            if !ability_conditions_met(state, db, player_idx, ab, &ctx) {
                continue;
            }

            let target_mask = if let Some(program) = ab.frame_program.as_ref() {
                if slot_idx < 3 && !program.frames.is_empty() {
                    let first_frame = &program.frames[0];
                    let target_area = first_frame.slot() & 0xFF;
                    let runtime_attr = first_frame.attr();
                    aura_target_mask(slot_idx, target_area, runtime_attr, !ab.filters.is_empty())
                } else if slot_idx < 3 {
                    0b111
                } else {
                    0
                }
            } else if slot_idx < 3 {
                0b111
            } else {
                0
            };

            if !ab.effects.is_empty() {
                for effect in &ab.effects {
                    let op = effect.runtime_opcode;
                    let v = effect.runtime_value;
                    let a = effect.runtime_attr;
                    let s = effect.runtime_slot;

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
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
                            Some(&effect.params),
                            &ctx,
                            state,
                            db,
                            player_idx,
                            slot_idx,
                        );
                    }
                }
            } else {
                let mut frame_idx = 0;
                loop {
                    let Some(frame) = ab.get_frame(frame_idx) else {
                        break;
                    };
                    frame_idx += 1;

                    let op = frame.opcode();
                    let v = frame.value();
                    let a = frame.attr();
                    let s = frame.slot();

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
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
                            &mut aura, op, v, s, a, None, &ctx, state, db, player_idx, slot_idx,
                        );
                    }
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
    let decode_heart_requirement_color =
        |raw_slot: i32, raw_attr: u64, params: Option<&serde_json::Value>| -> usize {
            if let Some(color) = decode_heart_type_from_params(params) {
                return color;
            }

            let color_mask = raw_attr as usize & FILTER_MASK_LOWER as usize;
            if color_mask != 0 {
                if color_mask == 0x7F {
                    6
                } else {
                    color_mask.trailing_zeros() as usize
                }
            } else {
                match raw_slot as usize {
                    4 | 7 => 6,
                    0..=6 => raw_slot as usize,
                    _ => 6,
                }
            }
        };

    let value = if v > 0xFFFF { v & 0xFFFF } else { v };
    let mut multiplier = 1;
    if (s & 0x10000) != 0 {
        let count_op = (s >> 8) & 0xFFFF;
        multiplier = resolve_count(state, db, count_op, a, s, ctx, 2);
    }

    if multiplier == 1 {
        if let Some(per_card) = params
            .and_then(|value| value.get("per_card"))
            .and_then(|value| value.as_str())
        {
            multiplier = match per_card.to_ascii_uppercase().as_str() {
                "HAND" => state.players[p_idx].hand.len() as i32,
                "DISCARD" | "DISCARD_COUNT" => state.players[p_idx].discard.len() as i32,
                "SUCCESS_LIVE" | "SUCCESS_PILE" | "COUNT" | "COUNT_VAL" => {
                    state.players[p_idx].success_lives.len() as i32
                }
                "STAGE" => state.players[p_idx]
                    .stage
                    .iter()
                    .copied()
                    .filter(|&cid| cid >= 0)
                    .count() as i32,
                _ => multiplier,
            };
        }
    }

    let decode_heart_color = |raw_attr: u64| -> usize {
        let color_mask = raw_attr as usize & FILTER_MASK_LOWER as usize;
        if color_mask != 0 {
            if color_mask.count_ones() == 1 {
                return color_mask.trailing_zeros() as usize;
            }
            if color_mask == 0x7F {
                return ctx.selected_color as usize;
            }
        }

        let mut color = raw_attr as usize & FILTER_MASK_LOWER as usize;
        if color == 7 {
            color = ctx.selected_color as usize;
        } else if (1..=6).contains(&color) {
            color -= 1;
        }
        color
    };

    match op {
        O_ADD_BLADES | O_BUFF_POWER => {
            if (a & 0x40) != 0 || a == ConditionType::SuccessPileCount as u64 {
                multiplier = state.players[p_idx].success_lives.len() as i32;
            } else if (a & 0xFFFFFFFF) == 1 && (a >> 32) > 0x00FFFFFF {
                multiplier = state.players[p_idx].success_lives.len() as i32;
            }
            aura.blades[target_slot] += value * multiplier;
        }
        O_ADD_HEARTS => {
            if (a & 0x02) != 0 && ((s >> 8) & 0xFF) != 0 {
                let count_op = (s >> 8) & 0xFF;
                multiplier = resolve_count(state, db, count_op, a, count_op, ctx, 2);
            }
            let color = decode_heart_color(a);
            if color < 7 {
                aura.hearts[target_slot].add_to_color(color, value * multiplier);
            }
        }
        O_REDUCE_COST => {
            if ((s as u32) & 0xFF) == 0 || ((s as u32) & 0xFF) == 4 || ((s as u32) & 0xFF) == 1 {
                // Generic slot/area reduction
                aura.slot_cost_modifiers[target_slot] -= value as i16 * multiplier as i16;
            }
        }
        O_INCREASE_COST => {
            if ((s as u32) & 0xFF) == 0 || ((s as u32) & 0xFF) == 4 || ((s as u32) & 0xFF) == 1 {
                aura.slot_cost_modifiers[target_slot] += value as i16 * multiplier as i16;
            }
        }
        O_REDUCE_HEART_REQ => {
            let color = decode_heart_requirement_color(s, a, params);
            if color < 7 {
                aura.heart_req_reductions
                    .add_to_color(color, value * multiplier);
            }
        }
        O_SET_HEART_COST => {
            // Unpack up to 8 values from A (each 4 bits)
            for i in 0..6 {
                let req_val = (a >> (i * 4)) & 0xF;
                if req_val > 0 {
                    aura.heart_req_reductions.add_to_color(i, -(req_val as i32));
                    // Negative reduction = addition
                }
            }
        }
        _ => {}
    }
}
