use super::card_db::{CardDatabase, MemberCard};
use super::game::GameState;
use crate::core::logic::interpreter::check_condition;
use crate::core::logic::interpreter::conditions::resolve_count;
use std::cell::Cell;

use crate::core::enums::*;
pub use crate::core::generated_constants::*;
use crate::core::hearts::*;
pub use crate::core::logic::models::*;

#[derive(Debug, Clone, Default, PartialEq, Eq, Hash, serde::Serialize, serde::Deserialize)]
pub struct BoardAura {
    pub blades: [i32; 3],
    pub hearts: [HeartBoard; 3],
    pub slot_cost_modifiers: [i16; 3],
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
    if depth != 0 {
        return None;
    }

    ON_DEMAND_AURA_QUERY.with(|flag| {
        if flag.get() {
            return None;
        }
        flag.set(true);
        let aura = calculate_board_aura(state, player_idx, db);
        flag.set(false);
        Some(aura)
    })
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
    board.add(state.players[player_idx].yell_heart_bonus[slot_idx]);
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

    for chunk in ab.bytecode.chunks(5) {
        let op = chunk[0];
        if chunk.len() != 5 || (op != O_REDUCE_COST && op != O_INCREASE_COST) {
            continue;
        }

        let val = chunk[1];
        let attr_low = chunk[2] as u32;
        let attr_high = chunk[3] as u32;
        let attr = ((attr_high as u64) << 32) | attr_low as u64;
        let slot = chunk[4];

        if ((slot as u32) & 0xFF) != 0 && ((slot as u32) & 0xFF) != 4 {
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
    }
}

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

    for chunk in ab.bytecode.chunks(5) {
        if chunk.len() != 5 {
            continue;
        }
        let op = chunk[0];
        if op == O_REDUCE_COST {
            *cost -= chunk[1];
        } else if op == O_INCREASE_COST {
            *cost += chunk[1];
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
    let mut board = get_effective_hearts(state, player_idx, slot_idx, db, depth + 1);
    let yell_bonus = state.players[player_idx].yell_heart_bonus[slot_idx].to_array();
    for (color, &count) in yell_bonus.iter().enumerate() {
        if count > 0 {
            board.add_to_color(color, -(count as i32));
        }
    }
    board
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

    // 1. Global reduction
    cost -= state.players[p_idx].cost_reduction as i32;

    // 2. Baton Touch & Cached Position Modifiers (Rule 12 & Auras)
    if slot_idx >= 0 && slot_idx < STAGE_SLOT_COUNT as i16 {
        let slot_modifier = query_aura
            .as_ref()
            .map(|aura| aura.slot_cost_modifiers[slot_idx as usize])
            .unwrap_or(state.players[p_idx].slot_cost_modifiers[slot_idx as usize]);
        cost += slot_modifier as i32;

        let old_cid = state.players[p_idx].stage[slot_idx as usize];
        if old_cid >= 0 {
            if let Some(old_m) = db.get_member(old_cid) {
                cost -= old_m.cost as i32;
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

    for source_slot in 0..3 {
        let source_cid = state.players[p_idx].stage[source_slot];
        if source_cid < 0 || source_cid == card_id {
            continue;
        }
        if let Some(source_member) = db.get_member(source_cid) {
            let source_ctx = AbilityContext {
                source_card_id: source_cid,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: source_slot as i16,
                ..Default::default()
            };
            for ab in &source_member.abilities {
                if ab.trigger == TriggerType::Constant {
                    apply_external_reduce_cost_modifiers(
                        &mut cost,
                        ab,
                        state,
                        db,
                        p_idx,
                        &source_ctx,
                        card_id,
                        depth,
                    );
                }
            }
        }
    }

    // 3. Self constant abilities that reduce own cost
    for ab in &m.abilities {
        if ab.trigger == TriggerType::Constant {
            let ctx = AbilityContext {
                source_card_id: card_id,
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                area_idx: slot_idx as i16,
                ..Default::default()
            };

            apply_reduce_cost_modifiers(&mut cost, ab, state, db, p_idx, &ctx, depth);
        }
    }

    // 4. Granted constant abilities that reduce own cost
    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities {
        if target_cid != card_id {
            if let Some(src_m) = db.get_member(source_cid) {
                if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                    if ab.trigger == TriggerType::Constant {
                        let ctx = AbilityContext {
                            source_card_id: source_cid,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        apply_external_reduce_cost_modifiers(
                            &mut cost,
                            ab,
                            state,
                            db,
                            p_idx,
                            &ctx,
                            card_id,
                            depth,
                        );
                    }
                }
            }
        }
        if target_cid == card_id {
            if let Some(src_m) = db.get_member(source_cid) {
                if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                    if ab.trigger == TriggerType::Constant {
                        let ctx = AbilityContext {
                            source_card_id: card_id,
                            player_id: p_idx as u8,
                            activator_id: p_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        apply_reduce_cost_modifiers(&mut cost, ab, state, db, p_idx, &ctx, depth);
                    }
                }
            }
        }
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
        if target_cid == cid {
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
        if let Some(m) = db.get_member(cid) {
            for ab in &m.abilities {
                if ab.trigger == TriggerType::Constant {
                    let ctx = AbilityContext {
                        source_card_id: cid,
                        player_id: player_idx as u8,
                        activator_id: player_idx as u8,
                        area_idx: source_slot as i16,
                        ..Default::default()
                    };
                    if ab
                        .conditions
                        .iter()
                        .all(|c| check_condition(state, db, player_idx, c, &ctx, 1))
                    {
                        for pm in &ab.preparsed_modifiers {
                            let op = pm.op;
                            let v = pm.val;
                            let s = pm.slot;
                            let a = pm.attr;
                            let target_area = s & 0xFF;

                            // Determine target slots
                            let mut target_mask = 0u8;
                            if target_area == 1 {
                                target_mask = 0b111;
                            } else if target_area == 4 || target_area == 0 {
                                target_mask = 1 << source_slot;
                            } else if target_area == 10 {
                                // This usually depends on target_slot in ctx, which is for triggers.
                                // Constant area-targeting "10" is rare but we handle it if possible.
                            }

                            for target_slot in 0..3 {
                                if (target_mask & (1 << target_slot)) != 0 {
                                    apply_aura_modifier(&mut aura, op, v, s, a, &ctx, state, db, player_idx, target_slot);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // 2. Granted abilities
    for &(target_cid, source_cid, ab_idx) in &state.players[player_idx].granted_abilities {
        if let Some(src_m) = db.get_member(source_cid) {
            if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                if ab.trigger == TriggerType::Constant {
                    // Check if target is on stage
                    let mut target_slot_opt = None;
                    for s in 0..3 {
                        if state.players[player_idx].stage[s] == target_cid {
                            target_slot_opt = Some(s);
                            break;
                        }
                    }

                    if let Some(target_slot) = target_slot_opt {
                        let ctx = AbilityContext {
                            source_card_id: target_cid,
                            player_id: player_idx as u8,
                            activator_id: player_idx as u8,
                            area_idx: target_slot as i16,
                            ..Default::default()
                        };
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, player_idx, c, &ctx, 1))
                        {
                            let bc = &ab.bytecode;
                            let mut i = 0;
                            while i + 4 < bc.len() {
                                let op = bc[i];
                                let v = bc[i + 1];
                                let a_low = bc[i + 2];
                                let a_high = bc[i + 3];
                                let a = ((a_high as u64) << 32) | (a_low as u64);
                                let s = bc[i + 4];

                                apply_aura_modifier(&mut aura, op, v, s, a, &ctx, state, db, player_idx, target_slot);
                                i += 5;
                            }
                        }
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
    ctx: &AbilityContext,
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    target_slot: usize,
) {
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
            aura.blades[target_slot] += v * multiplier;
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
                aura.hearts[target_slot].add_to_color(color, v * multiplier);
            }
        }
        O_REDUCE_COST => {
            aura.slot_cost_modifiers[target_slot] -= v as i16 * multiplier as i16;
        }
        O_INCREASE_COST => {
            aura.slot_cost_modifiers[target_slot] += v as i16 * multiplier as i16;
        }
        O_REDUCE_HEART_REQ => {
             // Implementation for heart requirement reductions
             let mut color = a as usize;
             if color == 0 { color = ctx.selected_color as usize; }
             if color < 7 {
                 aura.heart_req_reductions.add_to_color(color, v * multiplier);
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
