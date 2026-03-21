use super::card_db::{CardDatabase, MemberCard};
use super::game::GameState;
use crate::core::logic::interpreter::check_condition;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::instruction::BytecodeProgram;
use std::cell::Cell;

use crate::core::enums::*;
pub use crate::core::generated_constants::*;
use crate::core::hearts::*;
pub use crate::core::logic::models::*;
use smallvec::SmallVec;
use serde::{Serialize, Deserialize};

#[derive(Clone, Debug, Default, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct CachedCostModifier {
    pub source_cid: i32,
    pub amount: i16,
    pub target_mask: u8, // bitmask for slots 0, 1, 2
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

fn get_effective_blades_with_aura(
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

fn get_effective_hearts_with_aura(
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
    if m.has_multi_baton { 2 } else { 1 }
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
    if !ab
        .conditions
        .iter()
        .all(|c| check_condition(state, db, p_idx, c, ctx, depth + 1))
    {
        return;
    }

    if !ab.preparsed_modifiers.is_empty() {
        for pm in &ab.preparsed_modifiers {
            if (pm.op == O_REDUCE_COST || pm.op == O_INCREASE_COST) && ((pm.slot as u32) & 0xFF == 0 || (pm.slot as u32) & 0xFF == 4) {
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
        return;
    }

    let program = BytecodeProgram::from_slice(&ab.bytecode);
    let mut ip = 0;
    while let Some(instr) = program.instruction_at(ip) {
        let op = instr.op;
        if op != O_REDUCE_COST && op != O_INCREASE_COST {
            ip = program.next_ip(ip);
            continue;
        }

        let val = instr.v;
        let attr = instr.a as u64;
        let slot = instr.raw_s;

        if ((slot as u32) & 0xFF) != 0 && ((slot as u32) & 0xFF) != 4 {
            ip = program.next_ip(ip);
            continue;
        }

        let mut multiplier = 1;
        if (attr & DYNAMIC_VALUE) != 0 {
            let count_op = (slot >> 8) & 0xFFFF;
            multiplier = resolve_count(
                state,
                db,
                count_op as i32,
                attr & !DYNAMIC_VALUE,
                slot,
                ctx,
                depth + 1,
            );
        }
        if op == O_REDUCE_COST {
            *cost -= val * multiplier;
        } else {
            *cost += val * multiplier;
        }
        ip = program.next_ip(ip);
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
    depth: u32,
) {
    if ab.filters.is_empty()
        || !ab
            .conditions
            .iter()
            .all(|c| check_condition(state, db, p_idx, c, ctx, depth + 1))
    {
        return;
    }

    if !ab.filters.iter().any(|filter| {
        filter.matches(state, db, target_card_id, None, false, None, ctx)
    }) {
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

    let program = BytecodeProgram::from_slice(&ab.bytecode);
    let mut ip = 0;
    while let Some(instr) = program.instruction_at(ip) {
        let op = instr.op;
        if op == O_REDUCE_COST {
            *cost -= instr.v;
        } else if op == O_INCREASE_COST {
            *cost += instr.v;
        }
        ip = program.next_ip(ip);
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

pub fn calculate_cost_delta(state: &GameState, db: &CardDatabase, card_id: i32, p_idx: usize) -> i32 {
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
        let aura_ref = query_aura.as_ref().unwrap_or(&state.players[p_idx].board_aura);
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
                                area_idx: -1, // Not used for constant card filters
                                ..Default::default()
                            };
                            if !ab.filters.iter().any(|f: &crate::core::logic::filter::CardFilter| f.matches(state, db, card_id, None, false, None, &src_ctx)) {
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
                        if !ab.filters.iter().any(|f: &crate::core::logic::filter::CardFilter| f.matches(state, db, card_id, None, false, None, &src_ctx)) {
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
                        let bc = &ab.bytecode;
                        let mut i = 0;
                        while i + 4 < bc.len() {
                            if bc[i] == opcode {
                                return true;
                            }
                            i += 5;
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
                            let bc = &ab.bytecode;
                            let mut i = 0;
                            while i + 4 < bc.len() {
                                if bc[i] == opcode {
                                    return true;
                                }
                                i += 5;
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
            println!("[DEBUG] calculate_board_aura: player={}, source_slot={}, cid={}", player_idx, source_slot, cid);
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

            if !ab
                .conditions
                .iter()
                .all(|c| check_condition(state, db, player_idx, c, &ctx, 1))
            {
                if state.debug.debug_mode && !state.ui.silent {
                    println!("[DEBUG] calculate_board_aura: ability {} on cid {} failed conditions", ab_idx, cid);
                }
                continue;
            }

            if !ab.preparsed_modifiers.is_empty() {
                for pm in &ab.preparsed_modifiers {
                    let op = pm.op;
                    let v = pm.val;
                    let s = pm.slot;
                    let a = pm.attr;
                    let target_area = s & 0xFF;

                    let mut target_mask = 0u8;
                    if target_area == 1 || target_area == 4 || a != 0 || !ab.filters.is_empty() {
                        target_mask = 0b111;
                    } else if target_area == 0 {
                        target_mask = 1 << source_slot;
                    }

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
                        aura.cost_modifiers.push(CachedCostModifier {
                            source_cid: cid,
                            amount: if op == O_REDUCE_COST { v as i16 } else { -(v as i16) },
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
            } else {
                let program = BytecodeProgram::from_slice(&ab.bytecode);
                let mut ip = 0;
                while let Some(instr) = program.instruction_at(ip) {
                    let op = instr.op;
                    let v = instr.v;
                    let a = instr.a as u64;
                    let s = instr.raw_s;

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
                        let target_area = s & 0xFF;
                        let target_mask = if target_area == 1 || target_area == 4 || a != 0 || !ab.filters.is_empty() {
                            0b111
                        } else {
                            1 << source_slot
                        };
                        aura.cost_modifiers.push(CachedCostModifier {
                            source_cid: cid,
                            amount: if op == O_REDUCE_COST { v as i16 } else { -(v as i16) },
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
                            &ctx,
                            state,
                            db,
                            player_idx,
                            source_slot,
                        );
                    }
                    ip = program.next_ip(ip);
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

                if !ab
                    .conditions
                    .iter()
                    .all(|c| check_condition(state, db, player_idx, c, &ctx, 1))
                {
                    continue;
                }

                let target_mask = if slot_idx < 3 && !ab.bytecode.is_empty() {
                    let target_area = ab.bytecode.get(4).copied().unwrap_or(0);
                    let runtime_attr = ab.bytecode.get(2).copied().unwrap_or(0) as u64;
                    if target_area == 4 || runtime_attr != 0 || !ab.filters.is_empty() {
                        0b111
                    } else {
                        1 << slot_idx
                    }
                } else if slot_idx < 3 {
                    0b111
                } else {
                    0
                };

                let program = BytecodeProgram::from_slice(&ab.bytecode);
                let mut ip = 0;
                while let Some(instr) = program.instruction_at(ip) {
                    let op = instr.op;
                    let v = instr.v;
                    let a = instr.a as u64;
                    let s = instr.raw_s;

                    if op == O_REDUCE_COST || op == O_INCREASE_COST {
                        aura.cost_modifiers.push(CachedCostModifier {
                            source_cid,
                            amount: if op == O_REDUCE_COST { v as i16 } else { -(v as i16) },
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
                            &ctx,
                            state,
                            db,
                            player_idx,
                            slot_idx,
                        );
                    }
                    ip = program.next_ip(ip);
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
    ctx: &AbilityContext,
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    target_slot: usize,
) {
    let value = if v > 0xFFFF { v & 0xFFFF } else { v };
    let mut multiplier = 1;
    if (s & 0x10000) != 0 {
        let count_op = (s >> 8) & 0xFFFF;
        multiplier = resolve_count(state, db, count_op, a, s, ctx, 2);
    }

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
            let mut color = a as usize;
            if color == 0 {
                color = ctx.selected_color as usize;
            }
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
             // Implementation for heart requirement reductions
             let mut color = a as usize;
             if color == 0 { color = ctx.selected_color as usize; }
             if color < 7 {
                 aura.heart_req_reductions.add_to_color(color, value * multiplier);
             }
        }
        O_SET_HEART_COST => {
            // Unpack up to 8 values from A (each 4 bits)
            for i in 0..6 {
                let req_val = (a >> (i * 4)) & 0xF;
                if req_val > 0 {
                    aura.heart_req_reductions.add_to_color(i, -(req_val as i32)); // Negative reduction = addition
                }
            }
        }
        _ => {}
    }
}
