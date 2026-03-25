use super::common::compare_i32;
use super::counts::resolve_count;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::constants::*;
use crate::core::logic::interpreter::conditions::json_params::evaluate_raw_condition;
use crate::core::logic::interpreter::instruction::{DecodedFilterAttr, DecodedSlot};
use crate::core::logic::interpreter::suspension::resolve_target_slot;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::models::Condition;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

pub fn check_condition_frame(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    depth: u32,
) -> bool {
    if let Some(params) = frame.params.and_then(|value| value.as_object()) {
        if params.get("raw_cond").is_some() || params.get("RAW_COND").is_some() {
            let cond = Condition {
                condition_type: ConditionType::None,
                value: frame.value,
                attr: frame.raw_attr,
                target_slot: 0,
                is_negated: frame.is_negated,
                params: frame.params.cloned().unwrap_or_default(),
            };
            let raw_result = evaluate_raw_condition(state, db, 0, &cond, ctx, depth, params);
            return if frame.is_negated {
                !raw_result
            } else {
                raw_result
            };
        }
    }

    check_condition_with_parts(
        state,
        db,
        frame.opcode,
        frame.value,
        frame.raw_attr,
        frame.raw_slot,
        frame.params,
        frame.filter,
        frame.slot,
        ctx,
        depth,
    )
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
    check_condition_with_parts(
        state,
        db,
        op,
        val,
        attr,
        slot,
        None,
        DecodedFilterAttr::decode(attr as i64),
        DecodedSlot::decode(slot),
        ctx,
        depth,
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
    filter: DecodedFilterAttr,
    slot_info: DecodedSlot,
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
    let area_val = slot_info.area_idx;
    let real_slot = slot & 0xFF;

    if state.debug.debug_mode {
        if !state.ui.silent {
            println!(
                "[DEBUG] Condition Opcode: {}, Value: {}, Attr: {}, Slot: {} (Area: {}), Source: {:?}",
                op, val, attr, real_slot, area_val, cid
            );
        }
    }

    let result = match op {
        0 => true,
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
                .filter(|&&id| id >= 0)
                .any(|&id| {
                    (id == val || id == (attr as i32))
                        || (attr != 0 && state.card_matches_filter(db, id, attr))
                })
        }
        C_HAS_COLOR => {
            let color_mask = filter.color_mask as u64;
            if color_mask != 0 {
                player.stage.iter().filter(|&&cid| cid >= 0).any(|&cid| {
                    if let Some(_m) = db.get_member(cid) {
                        let eff_h = state.get_effective_hearts(
                            p_idx,
                            player.get_slot_of(cid).unwrap_or(0),
                            db,
                            depth + 1,
                        );
                        return (eff_h.get_color_mask() as u64 & color_mask) != 0;
                    }
                    false
                })
            } else {
                let color_idx = if attr != 0 {
                    attr as usize
                } else {
                    val as usize
                };
                if color_idx < 7 {
                    player.stage.iter().filter(|&&c| c >= 0).any(|&c| {
                        if let Some(m) = db.get_member(c) {
                            m.hearts[color_idx] > 0
                        } else {
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
            let p_opp = 1 - p_idx;
            state.players[p_opp]
                .stage
                .iter()
                .filter(|&&id| id >= 0)
                .any(|&cid| cid == val || (attr != 0 && state.card_matches_filter(db, cid, attr)))
        }
        C_LIFE_LEAD => {
            let my_lives = player.success_lives.len() as i32;
            let opp_lives = opponent.success_lives.len() as i32;
            let reversed = (attr & 0x01) != 0;
            let diff = if reversed {
                opp_lives - my_lives
            } else {
                my_lives - opp_lives
            };
            if val == 0 {
                diff > 0
            } else {
                diff >= val
            }
        }
        C_COUNT_GROUP => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        C_GROUP_FILTER => {
            let lower_attr = attr & 0x00000000FFFFFFFF;
            let is_packed_r5 = (attr & 0xFFFFFFFF00000000) != 0;
            let filter =
                if !is_packed_r5 && (lower_attr & 0x10) == 0 && lower_attr != 0 && lower_attr < 300
                {
                    0x10 | (lower_attr << 5)
                } else if !is_packed_r5 && (lower_attr & 0x10) == 0 && val != 0 {
                    0x10 | (((val & 0x7F) as u64) << 5)
                } else {
                    lower_attr
                };

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
            let cid = get_cid();
            if cid >= 0 {
                let lower_attr = attr & 0x00000000FFFFFFFF;
                let is_packed_r5 = (attr & 0xFFFFFFFF00000000) != 0;
                let filter = if !is_packed_r5
                    && (lower_attr & 0x10) == 0
                    && lower_attr != 0
                    && lower_attr < 300
                {
                    0x10 | (lower_attr << 5)
                } else if !is_packed_r5 && (lower_attr & 0x10) == 0 && val != 0 {
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
            if (attr & KEYWORD_ACTIVATED_ENERGY_BY_GROUP) != 0 {
                if (attr & FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_ID_SHIFT) & 0x7F;
                    return (player.activated_energy_group_mask & (1 << group_id)) != 0;
                }
                return player.activated_energy_group_mask != 0;
            }
            if (attr & KEYWORD_ACTIVATED_MEMBER_BY_GROUP) != 0 {
                if (attr & FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_ID_SHIFT) & 0x7F;
                    return (player.activated_member_group_mask & (1 << group_id)) != 0;
                }
                return player.activated_member_group_mask != 0;
            }

            let mut res = false;
            if (attr & KEYWORD_PLAYED_THIS_TURN) != 0 || attr == 0 {
                if (attr & FILTER_GROUP_ENABLE) != 0 {
                    let group_id = (attr >> FILTER_GROUP_ID_SHIFT) & 0x7F;
                    res = (player.played_group_mask & (1 << group_id)) != 0;
                } else if val == 0 && ((attr & KEYWORD_PLAYED_THIS_TURN) != 0 || attr == 0) {
                    res = player.play_count_this_turn() > 0;
                } else {
                    res = compare_i32(player.play_count_this_turn() as i32, val, slot);
                }
            }
            if (attr & KEYWORD_YELL_COUNT) != 0 {
                res = compare_i32(player.yell_cards.len() as i32, val, slot);
            }
            if (attr & KEYWORD_HAS_LIVE_SET) != 0 {
                res = player.live_zone.iter().any(|&c| c >= 0);
            }
            if (attr & FILTER_REVEALED_CONTEXT) != 0 {
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
        C_HAS_MOVED => ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize),
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
            let filter_attr = if (attr & 0xFFFFFFFF00000000) == 0
                && (attr & 0x1F) == 0
                && attr != 0
                && attr < 300
            {
                0x10 | (attr << 5)
            } else {
                attr
            };
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
        C_AREA_CHECK => ctx.area_idx == (val - 1) as i16,
        C_COST_LEAD => {
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
            let reversed = (attr & 0x01) != 0;
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
            let reversed = (attr & 0x01) != 0;
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
        C_HAS_EXCESS_HEART => player.excess_hearts > 0,
        C_NOT_HAS_EXCESS_HEART => player.excess_hearts == 0,
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
            let cid = get_cid();
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    let is_le = (attr & 0x40000000) != 0;
                    if is_le {
                        m.cost as i32 <= val
                    } else {
                        m.cost as i32 >= val
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
            let is_le = (attr & 0x40000000) != 0;
            if is_le {
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
            let color_idx = (attr & 0x7F) as usize;
            let count = if color_idx < 7 {
                hearts.to_array()[color_idx] as i32
            } else {
                hearts.get_total_count() as i32
            };
            let is_le = (attr & 0x40000000) != 0;
            if is_le {
                count <= val
            } else {
                count >= val
            }
        }
        C_OPPONENT_HAS_WAIT => (0..3).any(|i| opponent.stage[i] >= 0 && opponent.is_tapped(i)),
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
            let mut check_ids = Vec::new();
            if area_val == 0 {
                for p in 0..2 {
                    let player_idx = if (attr & (1u64 << 40)) != 0 {
                        1 - p_idx
                    } else {
                        p_idx
                    };
                    if p == 1 && (attr & (1u64 << 40)) == 0 {
                        continue;
                    }
                    check_ids.extend(
                        state.players[player_idx]
                            .stage
                            .iter()
                            .filter(|&&id| id >= 0),
                    );
                }
            } else if area_val >= 1 && area_val <= 3 {
                check_ids.push(&player.stage[(area_val - 1) as usize]);
            }
            check_ids
                .into_iter()
                .any(|&cid| cid >= 0 && state.card_matches_filter(db, cid, attr))
        }
        307 => compare_i32(
            resolve_count(state, db, op, attr, slot, ctx, depth),
            val,
            slot,
        ),
        308 => ctx.area_idx >= 0 && player.is_moved(ctx.area_idx as usize),
        309 => {
            let matching_count = if !ctx.selected_cards.is_empty() {
                ctx.selected_cards
                    .iter()
                    .copied()
                    .filter(|&cid| attr == 0 || state.card_matches_filter(db, cid, attr))
                    .count() as i32
            } else {
                player
                    .discard_ids_this_turn
                    .iter()
                    .copied()
                    .filter(|&cid| attr == 0 || state.card_matches_filter(db, cid, attr))
                    .count() as i32
            };
            if (val & 0x04) != 0 {
                // "all=true" logic
                let source_count = if !ctx.selected_cards.is_empty() {
                    ctx.selected_cards.len() as i32
                } else {
                    player.discard_ids_this_turn.len() as i32
                };
                source_count > 0 && matching_count == source_count
            } else {
                compare_i32(matching_count, val, slot)
            }
        }
        310 => {
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
            let area_override = params
                .and_then(|value| value.as_object())
                .and_then(|params| params.get("area").or_else(|| params.get("AREA")))
                .and_then(|value| value.as_str())
                .map(|value| value.to_ascii_uppercase())
                .and_then(|value| match value.as_str() {
                    "LEFT_SIDE" | "LEFT" => Some(0usize),
                    "CENTER" => Some(1usize),
                    "RIGHT_SIDE" | "RIGHT" => Some(2usize),
                    _ => None,
                });

            let (self_cost, opp_cost) = if let Some(idx) = area_override {
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
            } else if area_val >= 1 && area_val <= 3 {
                let idx = area_val as usize;
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
        312 => compare_i32(ctx.v_accumulated as i32, val, slot),
        313 => {
            let slot = if ctx.area_idx >= 0 && (ctx.area_idx as usize) < 3 {
                ctx.area_idx as usize
            } else {
                0
            };
            player.is_tapped(slot)
        }
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
    result
}
