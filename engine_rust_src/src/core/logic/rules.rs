use super::card_db::{CardDatabase, MemberCard};
use super::game::GameState;
use crate::core::logic::interpreter::check_condition;
use crate::core::logic::interpreter::conditions::resolve_count;

use crate::core::enums::*;
pub use crate::core::generated_constants::*;
use crate::core::hearts::*;
pub use crate::core::logic::models::*;

pub fn has_multi_baton(m: &MemberCard) -> u8 {
    let mut limit = 1;
    for ab in &m.abilities {
        if ab.trigger == TriggerType::Constant {
            let bc = &ab.bytecode;
            let mut i = 0;
            while i + 4 < bc.len() {
                if bc[i] == O_BATON_TOUCH_MOD {
                    limit = limit.max(bc[i + 1] as u8);
                }
                i += 5;
            }
        }
    }
    limit
}

pub fn get_effective_blades(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> u32 {
    if depth > 5 {
        return 0;
    }
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

    // Wave 1: Constant abilities from ALL members on stage (Global/Area buffs)
    for other_slot in 0..3 {
        let other_cid = state.players[player_idx].stage[other_slot];
        if other_cid < 0 {
            continue;
        }
        if let Some(other_m) = db.get_member(other_cid) {
            for ab in &other_m.abilities {
                if ab.trigger == TriggerType::Constant {
                    let ctx = AbilityContext {
                        source_card_id: other_cid,
                        player_id: player_idx as u8,
                        activator_id: player_idx as u8,
                        area_idx: other_slot as i16,
                        target_slot: slot_idx as i16, // The slot being evaluated
                        ..Default::default()
                    };
                    if ab
                        .conditions
                        .iter()
                        .all(|c| check_condition(state, db, player_idx, c, &ctx, depth + 1))
                    {
                        let bc = &ab.bytecode;
                        let mut i = 0;
                        while i + 4 < bc.len() {
                            let op = bc[i];
                            let v = bc[i + 1];
                            let s = bc[i + 4];
                            let target_area = s & 0xFF;

                            // Does this O_ADD_BLADES/O_BUFF_POWER target our slot?
                            // Target 1=All, 4=This Slot (if area_idx matching target_slot),
                            // 0=This Slot (often used as default)
                            let mut targets_us = false;
                            if target_area == 1 {
                                targets_us = true;
                            } else if (target_area == 4 || target_area == 0) && other_slot == slot_idx {
                                targets_us = true;
                            } else if target_area == 10 && slot_idx as i16 == ctx.target_slot {
                                targets_us = true;
                            }

                            if (op == O_ADD_BLADES || op == O_BUFF_POWER) && targets_us {
                                let a_low = bc[i + 2];
                                let a_high = bc[i + 3];
                                let a = ((a_high as u64) << 32) | (a_low as u64);

                                let mut multiplier = 1;
                                if (s & 0x10000) != 0 {
                                    // Dynamic multiplier: slot (bc[i+4]) bits 8-23 contains the count opcode
                                    let count_op = (s >> 8) & 0xFFFF;
                                    multiplier = resolve_count(state, db, count_op, a, s, &ctx, depth + 1);
                                } else if (a & 0x40) != 0 || a == ConditionType::SuccessPileCount as u64 {
                                    // SuccessPileCount (307)
                                    multiplier = state.players[player_idx].success_lives.len() as i32;
                                }

                                val += (v as i32) * multiplier;
                            }
                            i += 5;
                        }
                    }
                }
            }
        }
    }

    // --- Wave 2: Granted Abilities ---
    for &(target_cid, source_cid, ab_idx) in &state.players[player_idx].granted_abilities {
        if target_cid == cid {
            if let Some(src_m) = db.get_member(source_cid) {
                if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                    if ab.trigger == TriggerType::Constant {
                        let ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: player_idx as u8,
                            activator_id: player_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, player_idx, c, &ctx, depth + 1))
                        {
                            let bc = &ab.bytecode;
                            let mut i = 0;
                            while i + 4 < bc.len() {
                                let op = bc[i];
                                let v = bc[i + 1];
                                let s = bc[i + 4];
                                if op == O_ADD_BLADES {
                                    let a_low = bc[i + 2];
                                    let a_high = bc[i + 3];
                                    let a = ((a_high as u64) << 32) | (a_low as u64);

                                    let mut multiplier = 1;
                                    if (s & 0x10000) != 0 {
                                        let count_op = (s >> 8) & 0xFFFF;
                                        multiplier = resolve_count(state, db, count_op, a, s, &ctx, depth + 1);
                                    } else if (a & 0x40) != 0 || a == ConditionType::SuccessPileCount as u64 {
                                        multiplier = state.players[player_idx].success_lives.len() as i32;
                                    }
                                    val += (v as i32) * multiplier;
                                }
                                i += 5;
                            }
                        }
                    }
                }
            }
        }
    }

    let buff = state.players[player_idx].blade_buffs[slot_idx];
    if state.debug.debug_mode && !state.ui.silent {
        println!("[DEBUG] get_effective_blades: slot={}, base={}, override={:?}, val_accum={}, buff={}, total={}",
            slot_idx, m.blades, state.players[player_idx].blade_overrides[slot_idx], val, buff, (val + buff as i32).max(0));
    }
    (val + buff as i32).max(0) as u32
}

pub fn get_effective_hearts(
    state: &GameState,
    player_idx: usize,
    slot_idx: usize,
    db: &CardDatabase,
    depth: u32,
) -> HeartBoard {
    if depth > 5 {
        return HeartBoard::default();
    }
    let cid = state.players[player_idx].stage[slot_idx];
    if cid < 0 {
        // Even without a member, heart buffs for the slot might apply
        return state.players[player_idx].heart_buffs[slot_idx];
    }
    let base_id = cid;
    let m = if let Some(m) = db.get_member(base_id) {
        m
    } else {
        return state.players[player_idx].heart_buffs[slot_idx];
    };
    let mut board = m.hearts_board.clone();

    // Wave 1: Constant abilities from ALL members on stage (Global/Area buffs)
    for other_slot in 0..3 {
        let other_cid = state.players[player_idx].stage[other_slot];
        if other_cid < 0 {
            continue;
        }
        if let Some(other_m) = db.get_member(other_cid) {
            for ab in &other_m.abilities {
                if ab.trigger == TriggerType::Constant {
                    let ctx = AbilityContext {
                        source_card_id: other_cid,
                        player_id: player_idx as u8,
                        activator_id: player_idx as u8,
                        area_idx: other_slot as i16,
                        target_slot: slot_idx as i16,
                        ..Default::default()
                    };
                    if ab
                        .conditions
                        .iter()
                        .all(|c| check_condition(state, db, player_idx, c, &ctx, depth + 1))
                    {
                        let bc = &ab.bytecode;
                        let mut i = 0;
                        while i + 4 < bc.len() {
                            let op = bc[i];
                            let v = bc[i + 1];
                            let a_low = bc[i + 2];
                            let a_high = bc[i + 3];
                            let a = ((a_high as i64) << 32) | (a_low as i64);
                            let s = bc[i + 4];

                            let target_area = s & 0xFF;
                            let mut targets_us = false;
                            if target_area == 1 {
                                targets_us = true;
                            } else if (target_area == 4 || target_area == 0) && other_slot == slot_idx {
                                targets_us = true;
                            } else if target_area == 10 && slot_idx as i16 == ctx.target_slot {
                                targets_us = true;
                            }

                            if op == O_ADD_HEARTS && targets_us {
                                let mut multiplier = 1;
                                if (s & 0x10000) != 0 {
                                    let count_op = (s >> 8) & 0xFFFF;
                                    multiplier = resolve_count(state, db, count_op, a as u64, s, &ctx, depth + 1);
                                } else if (a & 0x02) != 0 {
                                    let count_op = (s >> 8) & 0xFF; // Legacy 8-bit
                                    multiplier = resolve_count(state, db, count_op, a as u64, count_op, &ctx, depth + 1);
                                }

                                let mut color = a as usize;
                                if color == 0 {
                                    color = ctx.selected_color as usize;
                                }
                                if color < 7 {
                                    board.add_to_color(color, (v as i32) * multiplier);
                                }
                            }
                            i += 5;
                        }
                    }
                }
            }
        }
    }

    // --- Wave 2: Granted Abilities ---
    for &(target_cid, source_cid, ab_idx) in &state.players[player_idx].granted_abilities {
        if target_cid == cid {
            if let Some(src_m) = db.get_member(source_cid) {
                if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                    if ab.trigger == TriggerType::Constant {
                        let ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: player_idx as u8,
                            activator_id: player_idx as u8,
                            area_idx: slot_idx as i16,
                            ..Default::default()
                        };
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, player_idx, c, &ctx, depth + 1))
                        {
                            let bc = &ab.bytecode;
                            let mut i = 0;
                            while i + 4 < bc.len() {
                                let op = bc[i];
                                let v = bc[i + 1];
                                let a_low = bc[i + 2];
                                let a_high = bc[i + 3];
                                let a = ((a_high as i64) << 32) | (a_low as i64);
                                let s = bc[i + 4];
                                if op == O_ADD_HEARTS {
                                    let mut multiplier = 1;
                                    if (s & 0x10000) != 0 {
                                        let count_op = (s >> 8) & 0xFF;
                                        multiplier = resolve_count(state, db, count_op, a as u64, s, &ctx, depth + 1);
                                    }

                                    let mut color = a as usize;
                                    if color == 0 {
                                        color = ctx.selected_color as usize;
                                    }
                                    if color < 7 {
                                        board.add_to_color(color, (v as i32) * multiplier);
                                    }
                                }
                                i += 5;
                            }
                        }
                    }
                }
            }
        }
    }

    // Add hearts from yelled cards (Rule 8.3.1)
    for &yid in &state.players[player_idx].stage_energy[slot_idx] {
        if let Some(ym) = db.get_member(yid) {
            board.add(ym.blade_hearts_board);
        }
    }

    board.add(state.players[player_idx].heart_buffs[slot_idx]);
    board
}

pub fn get_total_blades(state: &GameState, p_idx: usize, db: &CardDatabase, depth: u32) -> u32 {
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
    let mut total = HeartBoard::default();
    for i in 0..3 {
        total.add(get_effective_hearts(state, p_idx, i, db, depth + 1));
    }
    total
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
    if depth > 5 {
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

    // 1. Global reduction
    cost -= state.players[p_idx].cost_reduction as i32;

    // 2. Baton Touch & Cached Position Modifiers (Rule 12 & Auras)
    if slot_idx >= 0 && slot_idx < 3 {
        // Apply cached slot modifiers (from other members & granted abilities)
        cost += state.players[p_idx].slot_cost_modifiers[slot_idx as usize] as i32;

        let old_cid = state.players[p_idx].stage[slot_idx as usize];
        if old_cid >= 0 {
            if let Some(old_m) = db.get_member(old_cid) {
                cost -= old_m.cost as i32;
            }
        }
    }

    if secondary_slot_idx >= 0 && secondary_slot_idx < 3 {
        let old_cid = state.players[p_idx].stage[secondary_slot_idx as usize];
        if old_cid >= 0 {
            if let Some(old_m) = db.get_member(old_cid) {
                cost -= old_m.cost as i32;
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
                if state.debug.debug_mode && !state.ui.silent {
                    println!("[DEBUG] Checking ability: trigger={:?}, conditions_len={}", ab.trigger, ab.conditions.len());
                }
                let mut cond_match = true;
                for c in &ab.conditions {
                    if !check_condition(state, db, p_idx, c, &ctx, depth + 1) {
                        if state.debug.debug_mode && !state.ui.silent {
                           println!("[DEBUG] Condition failed: type={:?}, value={}", c.condition_type, c.value);
                        }
                        cond_match = false;
                        break;
                    }
                }

            if cond_match {
                let bc = &ab.bytecode;
                let mut i = 0;
                if state.debug.debug_mode && !state.ui.silent {
                    println!("[DEBUG] Conditions PASSED. Running bytecode loop, len={}", bc.len());
                }
                while i + 4 < bc.len() {
                    let op = bc[i];
                    let v = bc[i + 1];
                    let _target_type = bc[i + 4];

                        if op == O_REDUCE_COST && ((bc[i + 4] as u32) & 0xFF == 0 || (bc[i + 4] as u32) & 0xFF == 4) {
                            let a_low = bc[i + 2] as u32;
                            let a_high = bc[i + 3] as u32;
                            let a = ((a_high as u64) << 32) | (a_low as u64);
                            let s = bc[i + 4] as u32;

                            let mut multiplier = 1;
                            if (a & DYNAMIC_VALUE) != 0 {
                                // DYNAMIC_VALUE bit set
                                let count_op = (s >> 8) & 0xFFFF;
                                multiplier = resolve_count(state, db, count_op as i32, a & !DYNAMIC_VALUE, s as i32, &ctx, depth + 1);
                                if state.debug.debug_mode && !state.ui.silent {
                                    println!("[DEBUG] resolve_count returned: {}, for op: {}, a: {:X}", multiplier, count_op, a);
                                }
                            }
                            cost -= (v as i32) * multiplier;
                            if state.debug.debug_mode && !state.ui.silent {
                                println!("[DEBUG] Applied REDUCE_COST: v={}, multiplier={}, new_cost={}", v, multiplier, cost);
                            }
                        }
                    i += 5;
                }
            }
        }
    }

    // 4. Granted constant abilities that reduce own cost
    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities {
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
                        if ab
                            .conditions
                            .iter()
                            .all(|c| check_condition(state, db, p_idx, c, &ctx, depth + 1))
                        {
                            let bc = &ab.bytecode;
                            let mut i = 0;
                            while i + 4 < bc.len() {
                                let op = bc[i];
                                let v = bc[i + 1];
                                if op == O_REDUCE_COST && ((bc[i + 4] as u32) & 0xFF == 0 || (bc[i + 4] as u32) & 0xFF == 4) {
                                    let a_low = bc[i + 2] as u32;
                                    let a_high = bc[i + 3] as u32;
                                    let a = ((a_high as u64) << 32) | (a_low as u64);
                                    let s = bc[i + 4] as u32;

                                    let mut multiplier = 1;
                                    if (a & DYNAMIC_VALUE) != 0 {
                                        // DYNAMIC_VALUE bit set
                                        let count_op = (s >> 8) & 0xFFFF;
                                        multiplier = resolve_count(state, db, count_op as i32, a & !DYNAMIC_VALUE, s as i32, &ctx, depth + 1);
                                    }
                                    cost -= (v as i32) * multiplier;
                                }
                                i += 5;
                            }
                        }
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
    let cid = state.players[p_idx].stage[slot_idx];
    if cid < 0 {
        return false;
    }
    let m = if let Some(m) = db.get_member(cid) {
        m
    } else {
        return false;
    };

    // 1. Self constant abilities
    for ab in &m.abilities {
        if ab.trigger == TriggerType::Constant {
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

    // 2. Granted abilities
    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities {
        if target_cid == cid {
            if let Some(src_m) = db.get_member(source_cid) {
                if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                    if ab.trigger == TriggerType::Constant {
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
