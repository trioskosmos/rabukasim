//! # Condition Checking Logic
//!
//! This module contains the logic for evaluating conditions and opcodes.

use crate::core::logic::{GameState, CardDatabase, AbilityContext, Condition, ConditionType};
use crate::core::enums::*;
use super::filter::map_filter_string_to_attr;
use super::suspension::resolve_target_slot;

pub fn check_condition(
    state: &GameState, 
    db: &CardDatabase, 
    _p_idx: usize, 
    cond: &Condition, 
    ctx: &AbilityContext, 
    depth: u32
) -> bool {
    if depth > 10 { return false; }

    let mut val = cond.value;
    let mut attr = cond.attr;

    if let Some(params) = cond.params.as_object() {
        if val == 0 {
            if let Some(min) = params.get("min").and_then(|v| v.as_i64()) {
                val = min as i32;
            } else if let Some(min) = params.get("value").and_then(|v| v.as_i64()) {
                val = min as i32;
            } else if let Some(v) = params.get("val").and_then(|v| v.as_i64()) {
                val = v as i32;
            }
        }
        
        let mut mapped_attr = 0;
        if let Some(filter_str) = params.get("filter").and_then(|v| v.as_str()) {
            mapped_attr = map_filter_string_to_attr(filter_str);
        }
        
        if let Some(area_str) = params.get("area").and_then(|v| v.as_str()) {
            if area_str == "ANY_STAGE" || area_str == "ALL_AREAS" {
                mapped_attr |= 1u64 << 40; // Bit 40 for ANY_STAGE/ALL_AREAS
            }
        }
        
        if let Some(p_val) = params.get("player").and_then(|v| v.as_i64()) {
            if p_val == 2 { // Opponent
                mapped_attr |= 1u64 << 41; // Bit 41 for explicitly checking opponent
            }
        }

        if attr == 0 {
            attr = mapped_attr;
        } else {
            attr |= mapped_attr;
        }
    }

    let result = if cond.condition_type != ConditionType::None {
        check_condition_opcode(state, db, cond.condition_type as i32, val, attr, 0, ctx, depth + 1)
    } else {
        true
    };

    let result = if cond.is_negated { !result } else { result };

    if !result && state.debug.debug_ignore_conditions {
        if let Ok(mut bypassed) = state.debug.bypassed_conditions.0.lock() {
            bypassed.push(format!("BYPASS Condition: Type {:?}, Value {}, Attr {}", cond.condition_type, cond.value, cond.attr));
        }
        return true;
    }
    result
}

pub fn check_condition_opcode(
    state: &GameState, 
    db: &CardDatabase, 
    op: i32, 
    val: i32, 
    attr: u64, 
    slot: i32, 
    ctx: &AbilityContext, 
    depth: u32
) -> bool {
    let p_idx = ctx.player_id as usize;
    let player = &state.core.players[p_idx];
    let opponent = &state.core.players[1 - p_idx];
    
    let get_cid = || {
        if ctx.source_card_id >= 0 { ctx.source_card_id }
        else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 { player.stage[ctx.area_idx as usize] }
        else { -1 }
    };

    if state.debug.debug_mode {
        println!("[DEBUG] Condition Opcode: {}, Value: {}, Attr: {}, Slot: {}, Source: {:?}", op, val, attr, slot, get_cid());
    }

    let result = match op {
        C_TURN_1 => state.turn == 1,
        C_HAS_MEMBER => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            let check_self = (attr & (1u64 << 41)) == 0;
            let check_opp = (attr & (1u64 << 40)) != 0 || (attr & (1u64 << 41)) != 0;
            
            if check_self && player.stage.iter().filter(|&&id| id >= 0).any(|&id| {
                (id == val || id == (attr as i32)) || (filter_attr != 0 && state.card_matches_filter(db, id, filter_attr))
            }) { true }
            else if check_opp && opponent.stage.iter().filter(|&&id| id >= 0).any(|&id| {
                (id == val || id == (attr as i32)) || (filter_attr != 0 && state.card_matches_filter(db, id, filter_attr))
            }) { true }
            else { false }
        },
        C_HAS_COLOR => {
            let color_mask = (attr >> 32) & 0x7F;
            if color_mask != 0 {
                player.stage.iter().filter(|&&cid| cid >= 0).any(|&cid| {
                     if let Some(m) = db.get_member(cid) {
                         for i in 0..7 {
                             if (color_mask & (1 << i)) != 0 && m.hearts[i] > 0 { return true; }
                         }
                     }
                     false
                })
            } else {
                let color_idx = if attr != 0 { attr as usize } else { val as usize };
                if state.debug.debug_mode { println!("DEBUG [C_HAS_COLOR]: color_idx={}, stage={:?}", color_idx, player.stage); }
                if color_idx < 7 {
                    player.stage.iter().filter(|&&c| c >= 0).any(|&c| {
                         if let Some(m) = db.get_member(c) {
                             let has_heart = m.hearts[color_idx] > 0;
                             if state.debug.debug_mode { println!("DEBUG [C_HAS_COLOR]: cid={}, hearts={:?}, color_idx={}, result={}", c, m.hearts, color_idx, has_heart); }
                             has_heart
                         } else {
                             if state.debug.debug_mode { println!("DEBUG [C_HAS_COLOR]: cid={} NOT FOUND IN DB", c); }
                             false
                         }
                    })
                } else { false }
            }
        },
        C_COUNT_STAGE => {
            let filter_attr = attr & 0x00000000FFFFFFFF; 
            let include_opponent = (attr & (1u64 << 40)) != 0 || (attr & (1u64 << 41)) != 0;
            let only_opponent = (attr & (1u64 << 41)) != 0 && (attr & (1u64 << 40)) == 0;

            let mut ids = Vec::new();
            if !only_opponent { ids.extend(player.stage.iter().filter(|&&id| id >= 0)); }
            if include_opponent { ids.extend(opponent.stage.iter().filter(|&&id| id >= 0)); }

            let count = if (attr & 0x8000) != 0 { // UNIQUE_NAMES
                let mut names = std::collections::HashSet::new();
                for &&id in &ids {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(m) = db.get_member(id) { names.insert(&m.name); }
                        else if let Some(l) = db.get_live(id) { names.insert(&l.name); }
                    }
                }
                names.len() as i32
            } else {
                ids.into_iter().filter(|&&id| state.card_matches_filter(db, id, filter_attr)).count() as i32
            };
            count >= val
        },
        C_IS_CENTER => ctx.area_idx == 1,
        C_COUNT_HAND => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            let count = if (attr & 0x8000) != 0 {
                let mut names = std::collections::HashSet::new();
                for &id in player.hand.iter().filter(|&&id| id >= 0) {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(m) = db.get_member(id) { names.insert(&m.name); }
                    }
                }
                names.len() as i32
            } else {
                player.hand.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
            };
            count >= val
        },
        C_COUNT_DISCARD => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            let count = if (attr & 0x8000) != 0 {
                let mut names = std::collections::HashSet::new();
                for &id in player.discard.iter().filter(|&&id| id >= 0) {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(m) = db.get_member(id) { names.insert(&m.name); }
                    }
                }
                names.len() as i32
            } else {
                player.discard.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
            };
            count >= val
        },
        C_COUNT_ENERGY => player.energy_zone.len() as i32 >= val,
        C_HAS_LIVE_CARD => player.live_zone.iter().any(|&cid| cid >= 0),
        COST_ENERGY => {
            let cost_delta = state.calculate_cost_delta(db, ctx.source_card_id, p_idx);
            let total_cost = (val + cost_delta).max(0);
            player.energy_zone.len() as i32 >= total_cost
        },
        COST_TAP_SELF => {
            let slot = resolve_target_slot(slot, ctx);
            slot < 3 && !player.is_tapped(slot)
        },
        COST_DISCARD_HAND => player.hand.len() as i32 >= val,
        COST_RETURN_HAND => player.stage.iter().filter(|&&id| id >= 0).count() as i32 >= val,
        COST_SACRIFICE_SELF => {
            let slot = resolve_target_slot(slot, ctx);
            slot < 3 && player.stage[slot] >= 0
        },
        COST_TAP_MEMBER => {
            player.stage.iter().enumerate().any(|(i, &cid)| cid >= 0 && !player.is_tapped(i))
        },
        COST_TAP_ENERGY => {
             (player.energy_zone.len() as u32 - player.tapped_energy_mask.count_ones()) as i32 >= val
        },
        COST_DISCARD_ENERGY => player.energy_zone.len() as i32 >= val,
        COST_PLACE_MEMBER_FROM_HAND => player.hand.len() as i32 >= val,
        C_RARITY_CHECK => {
             let cid = get_cid();
             if cid >= 0 {
                  db.get_member(cid).map_or(false, |m| m.rarity == val as u8)
             } else { false }
        },
        C_COUNT_SUCCESS_LIVE => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            let count = if (attr & 0x8000) != 0 {
                let mut names = std::collections::HashSet::new();
                for &id in player.success_lives.iter().filter(|&&id| id >= 0) {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(m) = db.get_member(id) { names.insert(&m.name); }
                        else if let Some(l) = db.get_live(id) { names.insert(&l.name); }
                    }
                }
                names.len() as i32
            } else {
                player.success_lives.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
            };
            count >= val
        },
        C_OPPONENT_HAS => {
             let filter_attr = attr & 0x00000000FFFFFFFF;
             opponent.stage.iter().filter(|&&id| id >= 0).any(|&cid| cid == val || (filter_attr != 0 && state.card_matches_filter(db, cid, filter_attr)))
        },
        C_LIFE_LEAD => {
            let my_lives = player.success_lives.len() as i32;
            let opp_lives = opponent.success_lives.len() as i32;
            (my_lives - opp_lives) >= val
        },
        C_COUNT_GROUP => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            player.stage.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32 >= val
        },
        C_GROUP_FILTER => {
            let lower_attr = attr & 0x00000000FFFFFFFF;
            let filter = if (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 { 
                0x10 | (lower_attr << 5) 
            } else if (lower_attr & 0x10) == 0 && val != 0 {
                // val might contain flags in higher bits. Filter group ID is restricted to 7 bits (0-127).
                0x10 | (((val & 0x7F) as u64) << 5)
            } else { lower_attr };

            // Bit 2 of val (0x04) flags "Check ALL members on stage"
            if (val & 0x04) != 0 {
                player.stage.iter().filter(|&&cid| cid >= 0).all(|&cid| state.card_matches_filter(db, cid, filter))
            } else if let Some(cid) = state.get_context_card_id(ctx) {
                state.card_matches_filter(db, cid, filter)
            } else { false }
        },
        C_SELF_IS_GROUP => {
            let cid = if ctx.source_card_id >= 0 { ctx.source_card_id }
                      else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 { player.stage[ctx.area_idx as usize] }
                      else { -1 };
            if cid >= 0 {
                let lower_attr = attr & 0x00000000FFFFFFFF;
                let filter = if (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 { 
                    0x10 | (lower_attr << 5) 
                } else if (lower_attr & 0x10) == 0 && val != 0 {
                    0x10 | ((val as u64) << 5)
                } else { lower_attr };
                state.card_matches_filter(db, cid, filter)
            } else { false }
        },
        C_MODAL_ANSWER => ctx.choice_index == (val as i16),
        C_COST_CHECK => {
            if let Some(cid) = state.get_context_card_id(ctx) {
                if let Some(m) = db.get_member(cid) { m.cost as i32 >= val } else { false }
            } else { false }
        },
        C_HAND_HAS_NO_LIVE => {
            !player.hand.iter().filter(|&&id| id >= 0).any(|&id| db.get_live(id).is_some())
        },
        C_OPPONENT_HAND_DIFF => {
            let my_hand = player.hand.len() as i32;
            let opp_hand = opponent.hand.len() as i32;
            (opp_hand - my_hand) >= val
        },
        C_SCORE_COMPARE => {
            let my_score = player.score as i32;
            let target_score = if (attr & 0x20) != 0 { val } else { opponent.score as i32 };
            let op_type = (slot >> 4) & 0x0F;
            match op_type {
                0 => my_score >= target_score,
                1 => my_score <= target_score,
                2 => my_score > target_score,
                _ => my_score >= target_score,
            }
        },
        C_HAS_CHOICE => !state.interaction_stack.is_empty(),
        C_OPPONENT_CHOICE => state.interaction_stack.iter().any(|p| p.ctx.player_id != p_idx as u8),
        C_COUNT_HEARTS => {
            let mut total = 0;
            for i in 0..3 { total += state.get_effective_hearts(p_idx, i, db, depth + 1).get_total_count(); }
            total as i32 >= val
        },
        C_COUNT_BLADES => {
            let mut total = 0;
            for i in 0..3 { total += state.get_effective_blades(p_idx, i, db, depth + 1); }
            total as i32 >= val
        },
        C_OPPONENT_ENERGY_DIFF => {
            let my_energy = player.energy_zone.len() as i32;
            let opp_energy = opponent.energy_zone.len() as i32;
            (opp_energy - my_energy) >= val
        },
        C_HAS_KEYWORD => false,
        C_DECK_REFRESHED => player.get_flag(crate::core::logic::player::PlayerState::FLAG_DECK_REFRESHED),
        C_HAS_MOVED => ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize),
        C_HAND_INCREASED => player.hand_increased_this_turn > 0,
        C_BATON => state.prev_card_id != -1 || player.baton_touch_count > 0,
        C_COUNT_LIVE_ZONE => {
             let filter_attr = attr & 0x00000000FFFFFFFF;
             let count = if (attr & 0x8000) != 0 {
                let mut names = std::collections::HashSet::new();
                for &id in player.live_zone.iter().filter(|&&id| id >= 0) {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(l) = db.get_live(id) { names.insert(&l.name); }
                    }
                }
                names.len() as i32
             } else {
                player.live_zone.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
             };
             count >= val
        },
        C_TYPE_CHECK => {
            let check_val = if val == 0 && (attr & 0x00000000FFFFFFFF) != 0 { (attr & 0x00000000FFFFFFFF) as i32 } else { val };
            if let Some(card_id) = state.get_context_card_id(ctx) {
                if check_val == 1 { db.get_live(card_id).is_some() }
                else { db.get_member(card_id).is_some() }
            } else { false }
        },
        C_IS_IN_DISCARD => {
            let cid = ctx.source_card_id;
            if cid >= 0 { player.discard.contains(&(cid as i32)) } else { false }
        },
        C_AREA_CHECK => ctx.area_idx == (val - 1) as i16,
        C_COST_LEAD => {
            // 自分の場のコスト合計 vs 相手
            let self_cost: i32 = player.stage.iter()
                .filter(|&&id| id >= 0)
                .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                .sum();
            let opp_cost: i32 = opponent.stage.iter()
                .filter(|&&id| id >= 0)
                .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                .sum();
            let reversed = (attr & 0x01) != 0;
            if reversed { opp_cost > self_cost } else { self_cost > opp_cost }
        },
        C_SCORE_LEAD => {
            let self_score = player.score as i32;
            let opp_score = opponent.score as i32;
            let reversed = (attr & 0x01) != 0;
            if reversed { opp_score > self_score } else { self_score > opp_score }
        },
        C_HEART_LEAD => {
            let self_hearts = state.get_total_hearts(p_idx, db, depth + 1);
            let opp_hearts = state.get_total_hearts(1 - p_idx, db, depth + 1);
            let self_total = self_hearts.to_array().iter().map(|&x| x as i32).sum::<i32>();
            let opp_total = opp_hearts.to_array().iter().map(|&x| x as i32).sum::<i32>();
            let reversed = (attr & 0x01) != 0;
            if reversed { opp_total > self_total } else { self_total > opp_total }
        },
        C_HAS_EXCESS_HEART => {
            // ライブ成功後の余剰ハートチェック
            player.excess_hearts > 0
        },
        C_NOT_HAS_EXCESS_HEART => {
            player.excess_hearts == 0
        },
        C_TOTAL_BLADES => {
            let total = state.get_total_blades(p_idx, db, depth + 1);
            total >= val as u32
        },
        C_COST_COMPARE => {
            let cid = if ctx.source_card_id >= 0 { ctx.source_card_id }
                      else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 { player.stage[ctx.area_idx as usize] }
                      else { -1 };
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    let threshold = val;
                    let is_le = (attr & 0x40000000) != 0;
                    if is_le { m.cost as i32 <= threshold } else { m.cost as i32 >= threshold }
                } else { false }
            } else { false }
        },
        C_BLADE_COMPARE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 { ctx.area_idx as usize } else { 0 };
            let blades = state.get_effective_blades(p_idx, slot, db, depth + 1);
            let threshold = val as u32;
            let is_le = (attr & 0x40000000) != 0;
            if is_le { blades <= threshold } else { blades >= threshold }
        },
        C_HEART_COMPARE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 { ctx.area_idx as usize } else { 0 };
            let hearts = state.get_effective_hearts(p_idx, slot, db, depth + 1);
            let color_idx = (attr & 0x7F) as usize;
            let count = if color_idx < 7 { hearts.to_array()[color_idx] as i32 } else { hearts.get_total_count() as i32 };
            let threshold = val;
            let is_le = (attr & 0x40000000) != 0;
            if is_le { count <= threshold } else { count >= threshold }
        },
        C_OPPONENT_HAS_WAIT => {
            // 相手の場にWAIT（タップ状態）のメンバーがいるか
            (0..3).any(|i| opponent.stage[i] >= 0 && opponent.is_tapped(i))
        },
        _ => {
            false
        }
    };

    if !result && state.debug.debug_ignore_conditions {
        if let Ok(mut bypassed) = state.debug.bypassed_conditions.0.lock() {
            bypassed.push(format!("BYPASS Opcode: {}, Value {}, Attr {}", op, val, attr));
        }
        return true;
    }
    if state.debug.debug_mode {
        println!("[DEBUG] Condition Result: {} (Negated: {})", result, state.debug.debug_ignore_conditions);
    }
    result
}

pub fn get_condition_count(
    state: &GameState,
    db: &CardDatabase,
    cond_id: i32,
    attr: i32,
    ctx: &AbilityContext
) -> i32 {
    let p_idx = ctx.player_id as usize;
    let player = &state.core.players[p_idx];
    let opponent = &state.core.players[1 - p_idx];
    
    let filter_attr = (attr as u64) & 0x00000000FFFFFFFF;

    match cond_id {
        C_COUNT_STAGE => {
            let mut ids = Vec::new();
            ids.extend(player.stage.iter().filter(|&&id| id >= 0));
            // Note: C_COUNT_STAGE in bytecode usually only counts self unless flagged, 
            // but for count interpolation we assume player's perspective unless attr specifies otherwise.
            ids.into_iter().filter(|&&id| state.card_matches_filter(db, id, filter_attr)).count() as i32
        },
        C_COUNT_HAND => {
            player.hand.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
        },
        C_COUNT_DISCARD => {
            player.discard.iter().filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr)).count() as i32
        },
        C_COUNT_ENERGY => player.energy_zone.len() as i32,
        C_COUNT_HEARTS => {
            let mut total = 0;
            for i in 0..3 { total += state.get_effective_hearts(p_idx, i, db, 0).get_total_count(); }
            total as i32
        },
        C_COUNT_BLADES => {
            let mut total = 0;
            for i in 0..3 { total += state.get_effective_blades(p_idx, i, db, 0); }
            total as i32
        },
        C_OPPONENT_ENERGY_DIFF => {
             (opponent.energy_zone.len() as i32 - player.energy_zone.len() as i32).max(0)
        },
        C_TOTAL_BLADES => {
            state.get_total_blades(p_idx, db, 0) as i32
        },
        _ => 0
    }
}
