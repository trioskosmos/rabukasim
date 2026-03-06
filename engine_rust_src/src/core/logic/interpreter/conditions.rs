//! # Condition Checking Logic
//!
//! This module contains the logic for evaluating conditions and opcodes.

use super::suspension::resolve_target_slot;
use crate::core::enums::*;
use crate::core::generated_layout::*;
use crate::core::logic::constants::*;
use crate::core::logic::filter::CardFilter;
use crate::core::hearts::HeartBoard;
use crate::core::logic::filter::map_filter_string_to_attr;
use crate::core::logic::{AbilityContext, CardDatabase, Condition, ConditionType, GameState};

/// Compare an i32 value against a target with optional comparison mode from slot.
/// Slot encoding: 0 = equal, 1 = greater, 2 = less, 3 = greater-or-equal, 4 = less-or-equal
fn compare_i32(actual: i32, target: i32, slot: i32) -> bool {
    let mode = (slot >> 4) & 0x0F;
    if (slot & 0x0F) == 10 {
        // Log for visibility in tests
        // println!("[DEBUG] compare_i32: actual={}, target={}, mode={}, slot={}", actual, target, mode, slot);
    }
    match mode {
        COMP_GT => actual > target,
        COMP_LT => actual < target,
        COMP_GE => actual >= target,
        COMP_LE => actual <= target,
        _ => actual == target, // default: equal (COMP_EQ: 0)
    }
}

pub fn check_condition(
    state: &GameState,
    db: &CardDatabase,
    _p_idx: usize,
    cond: &Condition,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    if state.debug.debug_ignore_conditions {
        return true;
    }
    if depth > 10 {
        return false;
    }

    let mut val = cond.value;
    let mut attr = cond.attr;

    if let Some(params) = cond.params.as_object() {
        // Helper: case-insensitive param getter (compiled JSON uses UPPERCASE keys)
        let get_param = |key: &str| -> Option<&serde_json::Value> {
            params.get(key).or_else(|| params.get(&key.to_uppercase()))
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
                mapped_attr |= FILTER_ANY_STAGE;
            }
        }

        if let Some(p_val) = get_param("player").and_then(|v| v.as_i64()) {
            if p_val == TARGET_PLAYER_OPPONENT as i64 {
                // Opponent
                mapped_attr |= FILTER_OPPONENT;
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
                    mapped_attr |= KEYWORD_ACTIVATED_ENERGY_BY_GROUP
                }
                "DID_ACTIVATE_MEMBER"
                | "DID_ACTIVATE_MEMBER_BY_GROUP"
                | "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT" => {
                    mapped_attr |= KEYWORD_ACTIVATED_MEMBER_BY_GROUP
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

        // Extract 'all' flag for GROUP_FILTER conditions
        if cond.condition_type == ConditionType::GroupFilter {
            if params.get("all").and_then(|v| v.as_bool()).unwrap_or(false) {
                val |= 0x04; // Bit 2: ALL_MEMBERS
            }
        }
    }

    let result = if cond.condition_type != ConditionType::None {
        check_condition_opcode(
            state,
            db,
            cond.condition_type as i32,
            val,
            attr,
            0,
            ctx,
            depth + 1,
        )
    } else {
        true
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

pub fn resolve_count(
    state: &GameState,
    db: &CardDatabase,
    op: i32,
    attr: u64,
    slot: i32,
    ctx: &AbilityContext,
    depth: u32,
) -> i32 {
    let p_idx = ctx.player_id as usize;
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];

    // Basic count opcodes (Stage, Hand, Discard, Success Live)
    if op == C_COUNT_STAGE
        || op == C_COUNT_HAND
        || op == C_COUNT_DISCARD
        || op == C_COUNT_SUCCESS_LIVE
        || op == C_COUNT_GROUP
        || op == 307
        || (op >= 400 && op < 500)
    {
        let filter = CardFilter::from_attr(attr as i64);
        let include_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8 || filter.target_player == TARGET_PLAYER_BOTH as u8;
        let only_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8;

        // Bitmask logic for zones (relocated to bits 53-55 in R5)
        let zone_mask = filter.zone_mask as u64;
        let has_zone_mask = zone_mask != 0;

        // NEW: Detect zone from slot if it's an action opcode (e.g. MOVE_TO_DISCARD)
        let slot_decoded = crate::core::logic::interpreter::instruction::DecodedSlot::decode(slot);
        let s_zone = slot_decoded.source_zone;

        // Mask bindings: 4=Stage, 7=Discard, 6=Hand (matching Zone enum)
        let check_stage = if op >= 400 && op < 500 {
            op == 401 || (has_zone_mask && zone_mask == ZONE_STAGE as u64) || (!has_zone_mask && s_zone == Zone::Stage)
        } else if has_zone_mask {
            zone_mask == ZONE_STAGE as u64
        } else {
            op == C_COUNT_STAGE || op == C_COUNT_GROUP || s_zone == Zone::Stage
        };
        let check_discard = if op >= 400 && op < 500 {
            op == 403 || (has_zone_mask && zone_mask == ZONE_DISCARD as u64) || (!has_zone_mask && s_zone == Zone::Discard)
        } else if has_zone_mask {
            zone_mask == ZONE_DISCARD as u64
        } else {
            op == C_COUNT_DISCARD || s_zone == Zone::Discard
        };
        let check_hand = if op >= 400 && op < 500 {
            op == 402 || (has_zone_mask && zone_mask == ZONE_HAND as u64) || (!has_zone_mask && s_zone == Zone::Hand)
        } else if has_zone_mask {
            zone_mask == ZONE_HAND as u64
        } else {
            op == C_COUNT_HAND || s_zone == Zone::Hand
        };
        let check_success = op == C_COUNT_SUCCESS_LIVE || op == 307 || op == 405 || s_zone == Zone::SuccessPile;

        let mut ids = Vec::new();

        if !only_opponent {
            if check_stage {
                ids.extend(player.stage.iter().copied().filter(|&id| id >= 0));
            }
            if check_discard {
                ids.extend(player.discard.iter().copied().filter(|&id| id >= 0));
            }
            if check_hand {
                ids.extend(player.hand.iter().copied().filter(|&id| id >= 0));
            }
            if check_success {
                ids.extend(player.success_lives.iter().copied().filter(|&id| id >= 0));
            }
        }
        if include_opponent {
            if check_stage {
                ids.extend(opponent.stage.iter().copied().filter(|&id| id >= 0));
            }
            if check_discard {
                ids.extend(opponent.discard.iter().copied().filter(|&id| id >= 0));
            }
            if check_hand {
                ids.extend(opponent.hand.iter().copied().filter(|&id| id >= 0));
            }
            if check_success {
                ids.extend(opponent.success_lives.iter().copied().filter(|&id| id >= 0));
            }
        }

        // Special Group ID auto-encoding for C_COUNT_GROUP if not enabled (Legacy Support)
        // CRITICAL: Disable if any high-bits are set (Revision 5) or if it looks like a packed attribute
        let is_packed_r5 = (attr & 0xFFFFFFFF00000000) != 0 || (attr & 0xF) != 0; 
        let group_id_bits = (attr & 0x00000000FFFFFFFF) & !FILTER_UNIQUE_NAMES;
        let should_auto_encode_group = (op == C_COUNT_GROUP)
            && !is_packed_r5
            && (attr & FILTER_GROUP_ENABLE) == 0
            && group_id_bits > 0
            && group_id_bits < 300;

        let mut filter_attr = attr;
        if should_auto_encode_group {
            let gid = group_id_bits;
            // Clear bits 0-11 and insert new group flag+id (bit 4 + bits 5-11)
            let group_mask = 0xFFF; 
            let new_group_bits = 0x10 | (gid << 5);
            filter_attr = (filter_attr & !group_mask) | new_group_bits;
        }

        // CRITICAL FIX: Python compiler sometimes leaks the condition `val` (e.g. "needs >= 2 CatChu members")
        // into the filter's `value_threshold` as a heart requirement because they share the same params dict!
        // If value_threshold is set but there's no color_mask and it's NOT a cost type, clear the value_threshold bit!
        let has_value_enabled = (filter_attr & FILTER_VALUE_ENABLE_FLAG) != 0; // Bit 24
        let is_cost_type = (filter_attr & FILTER_VALUE_TYPE_FLAG) != 0;  // Bit 31
        let has_color_mask = ((filter_attr >> FILTER_COLOR_SHIFT_R5) & 0x7F) != 0; // Bits 32-38
        if has_value_enabled && !is_cost_type && !has_color_mask {
            // Nullify the value_enabled bit (bit 24) since it's an errant cross-contamination from the count target
            filter_attr &= !FILTER_VALUE_ENABLE_FLAG;
        }

        // REMOVED: Invalid Revision 4 metadata mask that was corrupting Revision 5 character IDs (Bit 39-52)
        // let metadata_mask = (1u64 << 40) | (1u64 << 41) | (1u64 << 43) | (1u64 << 50) | (0x7u64 << 53);
        // filter_attr &= !metadata_mask;

        if check_success {
            filter_attr &= !0x0C; // Clear Member (0x04) and Live (0x08) bits
        }

        if (attr & FILTER_UNIQUE_NAMES) != 0 {
            let mut names = std::collections::HashSet::new();
            for id in ids {
                if if state.debug.debug_mode { state.card_matches_filter_with_ctx_logs(db, id, filter_attr, ctx) } else { state.card_matches_filter_with_ctx(db, id, filter_attr, ctx) } {
                    if let Some(m) = db.get_member(id) {
                        names.insert(m.name.clone());
                    } else if let Some(l) = db.get_live(id) {
                        names.insert(l.name.clone());
                    }
                }
            }
            names.len() as i32
        } else {


            // Handle "Other than Self" (NOT_SELF=2, NOT_ACTIVATOR=3) by subtraction
            // This allows counting other instances of the same card ID.
            let special_id = (filter_attr >> 56) & 0x7;
            let mut final_filter = filter_attr;
            let mut do_subtraction = false;
            if special_id == 2 || special_id == 3 {
                do_subtraction = true;
                final_filter &= !(0x7u64 << 56); // Stripping Special ID bits
            }

            let raw_count = ids.iter()
                .filter(|&&id| {
                    let m = if state.debug.debug_mode { state.card_matches_filter_with_ctx_logs(db, id, final_filter, ctx) } else { state.card_matches_filter_with_ctx(db, id, final_filter, ctx) };
                    if state.debug.debug_mode && (id == 10 || id == 4433) {
                        // println!("[DEBUG]   ID {} matches filter? {}", id, m);
                    }
                    m
                })
                .count() as i32;

            let mut res = raw_count;
            if ctx.player_id == 0 && ids.contains(&4632) {
                 println!("[DEBUG_COND] resolve_count: raw={}, filter=0x{:x}, ids={:?}, source_id={}", raw_count, final_filter, ids, ctx.source_card_id);
            }
            if do_subtraction {
                let target_id = if special_id == 3 { ctx.source_card_id } else if special_id == 2 { ctx.activator_id as i32 } else { -2 };
                if ids.contains(&target_id) && if state.debug.debug_mode { state.card_matches_filter_with_ctx_logs(db, target_id, final_filter, ctx) } else { state.card_matches_filter_with_ctx(db, target_id, final_filter, ctx) } {
                    res = (res - 1).max(0);
                }
            }

            if state.debug.debug_mode {
                println!("[DEBUG] resolve_count result: {} (raw was {})", res, raw_count);
            }
            res
        }
    } else {
        match op {
            C_COUNT_ENERGY => player.energy_zone.len() as i32,
            C_COUNT_BLADES | C_COUNT_HEARTS | C_COUNT_STAGE | C_COUNT_GROUP => {
                let target_slot = slot & 0x0F;
                let resolved_slot = if target_slot == 10 {
                    (ctx.target_slot as i32).max(0) as usize
                } else if target_slot > 0 && target_slot <= 3 {
                    (target_slot - 1) as usize
                } else {
                    99
                }; // 99 means "sum all"

                if op == C_COUNT_BLADES {
                    if resolved_slot < 3 {
                        state.get_effective_blades(p_idx, resolved_slot, db, depth) as i32
                    } else {
                        let mut sum = 0;
                        for i in 0..3 {
                            sum += state.get_effective_blades(p_idx, i, db, depth) as i32;
                        }
                        sum
                    }
                } else if op == C_COUNT_HEARTS {
                    let color_idx = (attr >> 8) & 0x0F;
                    if resolved_slot < 3 {
                        let h = state.get_effective_hearts(p_idx, resolved_slot, db, depth);
                        if color_idx == 0 || color_idx > 7 {
                            h.get_total_count() as i32
                        } else {
                            h.to_array()[color_idx as usize - 1] as i32
                        }
                    } else {
                        let hearts = state.get_total_hearts(p_idx, db, depth).to_array();
                        if color_idx == 0 || color_idx > 7 {
                            hearts.iter().map(|&x| x as i32).sum()
                        } else {
                            hearts.get(color_idx as usize - 1).copied().unwrap_or(0) as i32
                        }
                    }
                } else {
                    // Stage/Group count logic already handled via the ids vector above
                    // This branch is just a fallback for match exhaustiveness
                    0
                }
            }
            250 => {
                // C_COUNT_UNIQUE_COLORS
                let mut count = 0;
                let mut seen = 0u8;
                for i in 0..3 {
                    let h = state.get_effective_hearts(p_idx, i, db, depth + 1);
                    for c in 0..7 {
                        if h.get_color_count(c) > 0 && (seen & (1 << c)) == 0 {
                            seen |= 1 << c;
                            count += 1;
                        }
                    }
                }
                count as i32
            }
            _ => 0,
        }
    }
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
    if state.debug.debug_ignore_conditions {
        return true;
    }
    let p_idx = ctx.player_id as usize;
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];

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
    let area_val = ((slot as u32 >> S_STANDARD_AREA_IDX_SHIFT) & S_STANDARD_AREA_IDX_MASK) as u8; 
    let real_slot = slot & 0xFF;

    if state.debug.debug_mode {
        // Use println for test visibility
        println!(
            "[DEBUG] Condition Opcode: {}, Value: {}, Attr: {}, Slot: {} (Area: {}), Source: {:?}",
            op, val, attr, real_slot, area_val, cid
        );
    }

    let result = match op {
        0 => {
            // Opcode 0: NOP/UNKNOWN (Systemic Fix)
            // Always pass but log if debugging.
            true
        }
        C_TURN_1 => state.turn == 1,
        C_HAS_MEMBER => {
            let filter = CardFilter::from_attr(attr as i64);
            let p_target = if filter.target_player == 2 { 1 - p_idx } else { p_idx };
            let target_player = &state.players[p_target as usize];
            
            target_player.stage.iter().filter(|&&id| id >= 0).any(|&id| {
                (id == val || id == (attr as i32))
                    || (attr != 0 && state.card_matches_filter(db, id, attr))
            })
        }
        C_HAS_COLOR => {
            let color_mask = (attr >> 32) & 0x7F;
            if color_mask != 0 {
                player.stage.iter().filter(|&&cid| cid >= 0).any(|&cid| {
                    if let Some(m) = db.get_member(cid) {
                        for i in 0..7 {
                            if (color_mask & (1 << i)) != 0 && m.hearts[i] > 0 {
                                return true;
                            }
                        }
                    }
                    false
                })
            } else {
                let color_idx = if attr != 0 {
                    attr as usize
                } else {
                    val as usize
                };
                if state.debug.debug_mode {
                    println!(
                        "DEBUG [C_HAS_COLOR]: color_idx={}, stage={:?}",
                        color_idx, player.stage
                    );
                }
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
                } else {
                    false
                }
            }
        }
        C_COUNT_STAGE => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_IS_CENTER => ctx.area_idx == 1,
        C_COUNT_HAND => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_COUNT_DISCARD => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_COUNT_ENERGY => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
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
        C_COUNT_SUCCESS_LIVE => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_OPPONENT_HAS => {
            let filter = CardFilter::from_attr(attr as i64);
            let _p_target = if filter.target_player == 1 { 1 - p_idx } else { 1 - p_idx }; // Usually opponent
            // Actually, Revision 5 target_player=2 is OPPT. 
            // If the opcode is explicitly C_OPPONENT_HAS, we force opponent.
            let p_opp = 1 - p_idx;
            state.players[p_opp].stage.iter().filter(|&&id| id >= 0).any(|&cid| {
                cid == val || (attr != 0 && state.card_matches_filter(db, cid, attr))
            })
        }
        C_LIFE_LEAD => {
            let my_lives = player.success_lives.len() as i32;
            let opp_lives = opponent.success_lives.len() as i32;
            let reversed = (attr & 0x01) != 0;
            let diff = if reversed { opp_lives - my_lives } else { my_lives - opp_lives };
            if val == 0 { diff > 0 } else { diff >= val }
        }
        C_COUNT_GROUP => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_GROUP_FILTER => {
            let lower_attr = attr & 0x00000000FFFFFFFF;
            // Revision 5: If any high bits are set or type bits [0..4] are non-zero, it's packed.
            let is_packed_r5 = (attr & 0xFFFFFFFF00000000) != 0 || (attr & 0xF) != 0;
            let filter = if !is_packed_r5 && (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 {
                0x10 | (lower_attr << 5)
            } else if !is_packed_r5 && (lower_attr & 0x10) == 0 && val != 0 {
                // val might contain flags in higher bits. Filter group ID is restricted to 7 bits (0-127).
                0x10 | (((val & 0x7F) as u64) << 5)
            } else {
                lower_attr
            };

            // Bit 2 of val (0x04) flags "Check ALL members on stage"
            if (val & 0x04) != 0 {
                player
                    .stage
                    .iter()
                    .filter(|&&cid| cid >= 0)
                    .all(|&cid| state.card_matches_filter(db, cid, filter))
            } else if let Some(cid) = state.get_context_card_id(ctx) {
                state.card_matches_filter(db, cid, filter)
            } else {
                false
            }
        }
        C_SELF_IS_GROUP => {
            let cid = if ctx.source_card_id >= 0 {
                ctx.source_card_id
            } else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                player.stage[ctx.area_idx as usize]
            } else {
                -1
            };
            if cid >= 0 {
                let lower_attr = attr & 0x00000000FFFFFFFF;
                let filter = if (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300 {
                    0x10 | (lower_attr << 5)
                } else if (lower_attr & 0x10) == 0 && val != 0 {
                    0x10 | ((val as u64) << 5)
                } else {
                    lower_attr
                };
                state.card_matches_filter(db, cid, filter)
            } else {
                false
            }
        }
        C_MODAL_ANSWER => ctx.choice_index == (val as i16),
        C_COST_CHECK => {
            if let Some(cid) = state.get_context_card_id(ctx) {
                if let Some(m) = db.get_member(cid) {
                    // Pack comparison into high bits of slot? (Already done via packed_slot at bit 4-7)
                    let _mode = (slot >> 4) & 0x0F;
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
            let target_score = if (attr & 0x20) != 0 || (val > 0 && opponent.score == 0) {
                val
            } else if val > 0 {
                opponent.score as i32 + val
            } else {
                opponent.score as i32
            };
            compare_i32(my_score, target_score, slot)
        }
        C_HAS_CHOICE => !state.interaction_stack.is_empty(),
        C_OPPONENT_CHOICE => state
            .interaction_stack
            .iter()
            .any(|p| p.ctx.player_id != p_idx as u8),
        C_COUNT_HEARTS => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth + 1),
            val,
            slot,
        ),
        C_COUNT_BLADES => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth + 1),
            val,
            slot,
        ),
        C_OPPONENT_ENERGY_DIFF => {
            let my_energy = player.energy_zone.len() as i32;
            let opp_energy = opponent.energy_zone.len() as i32;
            (opp_energy - my_energy) >= val
        }
        C_HAS_KEYWORD => {
            let mut res = false;
            if (attr & KEYWORD_PLAYED_THIS_TURN) != 0 || attr == 0 {
                if (attr & FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_SHIFT) & 0x7F;
                    res = (player.played_group_mask & (1 << group_id)) != 0;
                } else {
                    res = compare_i32(player.play_count_this_turn as i32, val, slot);
                }
            }
            if (attr & KEYWORD_YELL_COUNT) != 0 {
                res = compare_i32(player.yell_cards.len() as i32, val, slot);
            }
            if (attr & KEYWORD_HAS_LIVE_SET) != 0 {
                res = player.live_zone.iter().any(|&c| c >= 0);
            }
            if (attr & FILTER_REVEALED_CONTEXT) != 0 {
                // val=1 is live, val=2 is member
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
            if (attr & KEYWORD_ACTIVATED_ENERGY_BY_GROUP) != 0 {
                if (attr & crate::core::logic::constants::FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_SHIFT) & 0x7F;
                    let bit = 1 << group_id;
                    let matches = (player.activated_energy_group_mask & bit) != 0;
                    if state.debug.debug_mode {
                        println!("[KEYWORD-DEBUG] Energy Check: group_id={}, mask={:b}, bit={:b}, matches={}", group_id, player.activated_energy_group_mask, bit, matches);
                    }
                    if matches {
                        res = true;
                    }
                }
            }
            if (attr & KEYWORD_ACTIVATED_MEMBER_BY_GROUP) != 0 {
                if (attr & crate::core::logic::constants::FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_SHIFT) & 0x7F;
                    let bit = 1 << group_id;
                    let matches = (player.activated_member_group_mask & bit) != 0;
                    if state.debug.debug_mode {
                        println!("[KEYWORD-DEBUG] Member Check: group_id={}, mask={:b}, bit={:b}, matches={}", group_id, player.activated_member_group_mask, bit, matches);
                    }
                    if matches {
                        res = true;
                    }
                }
            }
            res
        }
        C_DECK_REFRESHED => {
            player.get_flag(crate::core::logic::player::PlayerState::FLAG_DECK_REFRESHED)
        }
        C_HAS_MOVED => ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize),
        C_HAND_INCREASED => player.hand_increased_this_turn > 0,
        C_BATON => {
            // val = expected baton touch count (0 means any > 0)
            // attr = filter for baton source cards (GROUP_ID filter encoded in lower 32 bits)
            let count_ok = if val > 0 {
                player.baton_touch_count == val as u8
            } else {
                player.baton_touch_count > 0 || state.prev_card_id != -1
            };

            // If filter is specified in attr, check if prev_card matches
            // Note: For double baton, we only track the last replaced card (prev_card_id)
            // A complete solution would track all baton source cards
            let filter_attr = attr & 0x00000000FFFFFFFF;
            if count_ok && filter_attr != 0 && state.prev_card_id >= 0 {
                state.card_matches_filter(db, state.prev_card_id, filter_attr)
            } else {
                count_ok
            }
        }
        C_COUNT_LIVE_ZONE => {
            let filter_attr = attr & 0x00000000FFFFFFFF;
            let count = if (attr & 0x8000) != 0 {
                let mut names = std::collections::HashSet::new();
                for &id in player.live_zone.iter().filter(|&&id| id >= 0) {
                    if state.card_matches_filter(db, id, filter_attr) {
                        if let Some(l) = db.get_live(id) {
                            names.insert(&l.name);
                        }
                    }
                }
                names.len() as i32
            } else {
                player
                    .live_zone
                    .iter()
                    .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr))
                    .count() as i32
            };
            compare_i32(count, val, slot)
        }
        C_TYPE_CHECK => {
            let check_val = if val == 0 && (attr & 0x00000000FFFFFFFF) != 0 {
                (attr & 0x00000000FFFFFFFF) as i32
            } else {
                val
            };
            if let Some(card_id) = state.get_context_card_id(ctx) {
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
            if cid >= 0 {
                player.discard.contains(&(cid as i32))
            } else {
                false
            }
        }
        C_AREA_CHECK => ctx.area_idx == (val - 1) as i16,
        C_COST_LEAD => {
            // 自分の場のコスト合計 vs 相手
            let self_cost: i32 = player
                .stage
                .iter()
                .filter(|&&id| id >= 0)
                .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                .sum();
            let opp_cost: i32 = opponent
                .stage
                .iter()
                .filter(|&&id| id >= 0)
                .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                .sum();
            let reversed = (attr & 0x01) != 0;
            let diff = if reversed { opp_cost - self_cost } else { self_cost - opp_cost };
            if val == 0 { diff > 0 } else { diff >= val }
        }
        C_SCORE_LEAD => {
            let self_score = player.score as i32;
            let opp_score = opponent.score as i32;
            let reversed = (attr & 0x01) != 0;
            let diff = if reversed { opp_score - self_score } else { self_score - opp_score };
            if val == 0 { diff > 0 } else { diff >= val }
        }
        C_HEART_LEAD => {
            let self_hearts = state.get_total_hearts(p_idx, db, depth + 1);
            let opp_hearts = state.get_total_hearts(1 - p_idx, db, depth + 1);
            let self_total = self_hearts
                .to_array()
                .iter()
                .map(|&x| x as i32)
                .sum::<i32>();
            let opp_total = opp_hearts.to_array().iter().map(|&x| x as i32).sum::<i32>();
            let reversed = (attr & 0x01) != 0;
            let diff = if reversed { opp_total - self_total } else { self_total - opp_total };
            if val == 0 { diff > 0 } else { diff >= val }
        }
        C_HAS_EXCESS_HEART => {
            // ライブ成功後の余剰ハートチェック
            player.excess_hearts > 0
        }
        C_NOT_HAS_EXCESS_HEART => player.excess_hearts == 0,
        C_TOTAL_BLADES => {
            let total = state.get_total_blades(p_idx, db, depth + 1);
            total >= val as u32
        }
        C_COST_COMPARE => {
            let cid = if ctx.source_card_id >= 0 {
                ctx.source_card_id
            } else if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                player.stage[ctx.area_idx as usize]
            } else {
                -1
            };
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    let threshold = val;
                    let is_le = (attr & 0x40000000) != 0;
                    if is_le {
                        m.cost as i32 <= threshold
                    } else {
                        m.cost as i32 >= threshold
                    }
                } else {
                    false
                }
            } else {
                false
            }
        }
        C_BLADE_COMPARE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            let blades = state.get_effective_blades(p_idx, slot, db, depth + 1);
            let threshold = val as u32;
            let is_le = (attr & 0x40000000) != 0;
            if is_le {
                blades <= threshold
            } else {
                blades >= threshold
            }
        }
        C_HEART_COMPARE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            let hearts = state.get_effective_hearts(p_idx, slot, db, depth + 1);
            let color_idx = (attr & 0x7F) as usize;
            let count = if color_idx < 7 {
                hearts.to_array()[color_idx] as i32
            } else {
                hearts.get_total_count() as i32
            };
            let threshold = val;
            let is_le = (attr & 0x40000000) != 0;
            if is_le {
                count <= threshold
            } else {
                count >= threshold
            }
        }
        C_OPPONENT_HAS_WAIT => {
            // 相手の場にWAIT（タップ状態）のメンバーがいるか
            (0..3).any(|i| opponent.stage[i] >= 0 && opponent.is_tapped(i))
        }
        C_IS_TAPPED => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            player.is_tapped(slot)
        }
        C_IS_ACTIVE => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            !player.is_tapped(slot)
        }
        C_LIVE_PERFORMED => state.obtained_success_live[p_idx],
        C_IS_PLAYER => p_idx == state.current_player as usize,
        C_IS_OPPONENT => p_idx != state.current_player as usize,
        // New BP05 conditions (301-304)
        C_COUNT_ENERGY_EXACT => {
            // "All energy is active" is compiled as C_COUNT_ENERGY_EXACT with val=0.
            // This means we are counting how much energy is NOT active (i.e. tapped).
            let count = player.tapped_energy_mask.count_ones() as i32;
            compare_i32(count, val, slot)
        }
        C_COUNT_BLADE_HEART_TYPES => {
            // Count unique blade/heart types among cards revealed by yell
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
        C_OPPONENT_HAS_EXCESS_HEART => {
            // Check if opponent has excess hearts
            // This would naturally be >= 1 if checking "has"
            opponent.excess_hearts > 0
        }
        C_SCORE_TOTAL_CHECK => {
            // Check total score of cards in success live zone (physical sum)
            let mut sum = 0;
            for &cid in &player.success_lives {
                if let Some(l) = db.get_live(cid) {
                    sum += l.score;
                }
            }
            compare_i32(sum as i32, val, slot)
        }
        305 => {
            // MAIN_PHASE
            // Usually checks if the player is in their active main phase
            state.current_player == (p_idx as u8) && state.phase == Phase::Main
        }
        306 => {
            // SELECT_MEMBER
            // If used as condition, check if target selection is valid/exists
            if ctx.target_card_id >= 0 {
                return true;
            }

            // Systemic Fix: If no target, check if a card matching 'attr' exists in 'area_val'
            let mut check_ids = Vec::new();
            if area_val == 0 {
                // Default: Stage
                for p in 0..2 {
                    let player_idx = if (attr & (1u64 << 40)) != 0 {
                        1 - p_idx
                    } else {
                        p_idx
                    };
                    if p == 1 && (attr & (1u64 << 40)) == 0 {
                        continue;
                    } // Don't check opponent unless flagged
                    check_ids.extend(
                        state.players[player_idx]
                            .stage
                            .iter()
                            .filter(|&&id| id >= 0),
                    );
                }
            } else if area_val >= 1 && area_val <= 3 {
                // Check specific slot
                let slot_idx = (area_val - 1) as usize;
                check_ids.push(&player.stage[slot_idx]);
            }

            check_ids
                .into_iter()
                .any(|&cid| cid >= 0 && state.card_matches_filter(db, cid, attr))
        }
        307 => {
            // SUCCESS_PILE_COUNT
            compare_i32(
                resolve_count(state, db, op, attr, slot, ctx, depth),
                val,
                slot,
            )
        }
        308 => {
            // IS_SELF_MOVE
            ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize)
        }
        309 => {
            // DISCARDED_CARDS
            // Count cards discarded this turn
            compare_i32(player.discarded_this_turn as i32, val, slot)
        }
        310 => {
            // YELL_REVEALED_UNIQUE_COLORS
            let mut seen = 0u8;
            let mut count = 0;
            for &cid in &player.yell_cards {
                if let Some(m) = db.get_member(cid) {
                    for i in 0..7 {
                        if m.hearts[i] > 0 && (seen & (1 << i)) == 0 {
                            seen |= 1 << i;
                            count += 1;
                        }
                    }
                }
            }
            compare_i32(count, val, slot)
        }
        311 => {
            // SYNC_COST (aka PLAYER_CENTER_COST_GT_OPPONENT_CENTER_COST)
            // 自分のメンバーと相手のメンバーのコスト合計比較
            // Fix: If area_val is set (e.g. Center=2), only compare the card at that slot.
            let (self_cost, opp_cost) = if area_val >= 1 && area_val <= 3 {
                let idx = (area_val - 1) as usize;
                let s_cid = player.stage[idx];
                let o_cid = opponent.stage[idx];

                let s_cost =
                    if s_cid >= 0 && (attr == 0 || state.card_matches_filter(db, s_cid, attr)) {
                        db.get_member(s_cid).map_or(0, |m| m.cost as i32)
                    } else {
                        0
                    };

                let o_cost =
                    if o_cid >= 0 && (attr == 0 || state.card_matches_filter(db, o_cid, attr)) {
                        db.get_member(o_cid).map_or(0, |m| m.cost as i32)
                    } else {
                        0
                    };
                (s_cost, o_cost)
            } else {
                let s_cost: i32 = player
                    .stage
                    .iter()
                    .filter(|&&id| {
                        id >= 0 && (attr == 0 || state.card_matches_filter(db, id, attr))
                    })
                    .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                    .sum();
                let o_cost: i32 = opponent
                    .stage
                    .iter()
                    .filter(|&&id| {
                        id >= 0 && (attr == 0 || state.card_matches_filter(db, id, attr))
                    })
                    .map(|&id| db.get_member(id).map_or(0, |m| m.cost as i32))
                    .sum();
                (s_cost, o_cost)
            };
            compare_i32(self_cost, opp_cost + val, slot)
        }
        312 => {
            // SUM_VALUE
            // If v_accumulated is set (e.g. by CALC_SUM_COST), compare against it.
            // Otherwise fallback to hand size difference (legacy behavior).
            let val_to_compare = if ctx.v_accumulated != 0 {
                ctx.v_accumulated as i32
            } else {
                let my_hand = player.hand.len() as i32;
                let opp_hand = opponent.hand.len() as i32;
                opp_hand - my_hand
            };
            compare_i32(val_to_compare, val, slot)
        }
        313 => {
            // IS_WAIT
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            player.is_tapped(slot)
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
    if state.debug.debug_mode {
        // if state.debug.debug_mode {
        //     println!("[DEBUG] Condition Result: {} (Negated: {})", result, state.debug.debug_ignore_conditions);
        // }
    }
    result
}

pub fn get_condition_count(
    state: &GameState,
    db: &CardDatabase,
    cond_id: i32,
    attr: u64,
    ctx: &AbilityContext,
) -> i32 {
    let p_idx = ctx.player_id as usize;
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];

    let filter_attr = (attr as u64) & 0x00000000FFFFFFFF;

    match cond_id {
        C_COUNT_STAGE => {
            let mut ids = Vec::new();
            ids.extend(player.stage.iter().filter(|&&id| id >= 0));
            // Note: C_COUNT_STAGE in bytecode usually only counts self unless flagged,
            // but for count interpolation we assume player's perspective unless attr specifies otherwise.
            ids.into_iter()
                .filter(|&&id| state.card_matches_filter(db, id, filter_attr))
                .count() as i32
        }
        C_COUNT_HAND => player
            .hand
            .iter()
            .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr))
            .count() as i32,
        C_COUNT_DISCARD => player
            .discard
            .iter()
            .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr))
            .count() as i32,
        C_COUNT_ENERGY => player.energy_zone.len() as i32,
        C_COUNT_HEARTS => {
            let mut total = 0;
            for i in 0..3 {
                total += state
                    .get_effective_hearts(p_idx, i, db, 0)
                    .get_total_count();
            }
            total as i32
        }
        C_COUNT_BLADES => {
            let mut total = 0;
            for i in 0..3 {
                total += state.get_effective_blades(p_idx, i, db, 0);
            }
            total as i32
        }
        C_OPPONENT_ENERGY_DIFF => {
            (opponent.energy_zone.len() as i32 - player.energy_zone.len() as i32).max(0)
        }
        C_TOTAL_BLADES => state.get_total_blades(p_idx, db, 0) as i32,
        _ => 0,
    }
}
