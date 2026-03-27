use crate::core::enums::*;
use crate::core::logic::constants::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

fn target_player_pair(filter: &CardFilter, p_idx: usize) -> (usize, Option<usize>) {
    match filter.target_player {
        2 => (1 - p_idx, None),
        3 => (p_idx, Some(1 - p_idx)),
        _ => (p_idx, None),
    }
}

pub fn resolve_count_frame(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    depth: u32,
) -> i32 {
    resolve_count(
        state,
        db,
        frame.opcode,
        frame.raw_attr,
        frame.raw_slot,
        ctx,
        depth,
    )
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

    if op == C_COUNT_STAGE
        || op == C_COUNT_HAND
        || op == C_COUNT_DISCARD
        || op == C_COUNT_SUCCESS_LIVE
        || op == C_COUNT_GROUP
        || op == 307
        || op == 13
        || (op >= 400 && op < 500)
        || crate::core::logic::interpreter::instruction::DecodedSlot::decode(slot).is_dynamic
    {
        let filter = CardFilter::from_attr(attr as i64);
        let include_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8
            || filter.target_player == TARGET_PLAYER_BOTH as u8;
        let only_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8;

        let zone_mask = filter.zone_mask as u64;
        let has_zone_mask = zone_mask != 0;

        let slot_decoded = crate::core::logic::interpreter::instruction::DecodedSlot::decode(slot);
        let s_zone = slot_decoded.source_zone;

        let is_explicit_success_count = op == C_COUNT_SUCCESS_LIVE || op == 307 || op == 405;

        let check_stage = if is_explicit_success_count {
            false
        } else if op >= 400 && op < 500 {
            op == 401
                || (has_zone_mask && zone_mask == ZONE_STAGE as u64)
                || (!has_zone_mask && s_zone == Zone::Stage)
        } else if has_zone_mask {
            zone_mask == ZONE_STAGE as u64
        } else {
            op == C_COUNT_STAGE || op == C_COUNT_GROUP || s_zone == Zone::Stage
        };
        let check_discard = if is_explicit_success_count {
            false
        } else if op >= 400 && op < 500 {
            op == 403
                || (has_zone_mask && zone_mask == ZONE_DISCARD as u64)
                || (!has_zone_mask && s_zone == Zone::Discard)
        } else if has_zone_mask {
            zone_mask == ZONE_DISCARD as u64
        } else {
            op == C_COUNT_DISCARD || s_zone == Zone::Discard
        };
        let check_hand = if is_explicit_success_count {
            false
        } else if op >= 400 && op < 500 {
            op == 402
                || (has_zone_mask && zone_mask == ZONE_HAND as u64)
                || (!has_zone_mask && s_zone == Zone::Hand)
        } else if has_zone_mask {
            zone_mask == ZONE_HAND as u64
        } else {
            op == C_COUNT_HAND || s_zone == Zone::Hand
        };
        let check_success = is_explicit_success_count || s_zone == Zone::SuccessPile;

        use smallvec::SmallVec;
        let mut ids = SmallVec::<[(i32, Option<(u8, i16)>); 32]>::new();

        fn extend_with_slot(
            ids: &mut SmallVec<[(i32, Option<(u8, i16)>); 32]>,
            cards: &[i32],
            p_idx: u8,
            base_slot: i16,
        ) {
            for (i, &id) in cards.iter().enumerate() {
                if id >= 0 {
                    let s_idx = if base_slot >= 0 { base_slot + i as i16 } else { -1 };
                    ids.push((id, if s_idx >= 0 { Some((p_idx, s_idx)) } else { None }));
                }
            }
        }

        if !only_opponent {
            if check_stage {
                extend_with_slot(&mut ids, &player.stage, p_idx as u8, 0);
            }
            if check_discard {
                extend_with_slot(&mut ids, &player.discard, p_idx as u8, 100);
            }
            if check_hand {
                extend_with_slot(&mut ids, &player.hand, p_idx as u8, 200);
            }
            if check_success {
                extend_with_slot(&mut ids, &player.success_lives, p_idx as u8, -1);
            }
        }
        if include_opponent {
            if check_stage {
                extend_with_slot(&mut ids, &opponent.stage, (1 - p_idx) as u8, 0);
            }
            if check_discard {
                extend_with_slot(&mut ids, &opponent.discard, (1 - p_idx) as u8, 100);
            }
            if check_hand {
                extend_with_slot(&mut ids, &opponent.hand, (1 - p_idx) as u8, 200);
            }
            if check_success {
                extend_with_slot(&mut ids, &opponent.success_lives, (1 - p_idx) as u8, -1);
            }
        }

        let is_packed_r5 = (attr & 0xFFFFFFFF00000000) != 0;
        let group_id_bits = (attr & 0x00000000FFFFFFFF) & !FILTER_UNIQUE_NAMES;
        let should_auto_encode_group = (op == C_COUNT_GROUP)
            && !is_packed_r5
            && (attr & FILTER_GROUP_ENABLE) == 0
            && group_id_bits > 0
            && group_id_bits < 300;

        let mut filter_attr = attr;
        if should_auto_encode_group {
            let gid = group_id_bits;
            let group_mask = 0xFFF;
            let new_group_bits = 0x10 | (gid << 5);
            filter_attr = (filter_attr & !group_mask) | new_group_bits;
        }

        let has_value_enabled = (filter_attr & FILTER_VALUE_ENABLE_FLAG) != 0;
        let is_cost_type = (filter_attr & FILTER_VALUE_TYPE_FLAG) != 0;
        let has_color_mask = ((filter_attr >> FILTER_COLOR_SHIFT_R5) & 0x7F) != 0;
        if has_value_enabled && !is_cost_type && !has_color_mask && !is_packed_r5 {
            filter_attr &= !FILTER_VALUE_ENABLE_FLAG;
        }

        if check_success {
            filter_attr &= !0x0C;
        }

        let filter = CardFilter::from_attr(filter_attr as i64);

        let filter = CardFilter::from_attr(filter_attr as i64);

        if (attr & FILTER_UNIQUE_NAMES) != 0 {
            let mut names = std::collections::HashSet::new();
            for (id, slot) in ids {
                let matched = state.card_matches_filter_with_struct(db, id, slot, &filter, ctx);
                if matched {
                    if let Some(m) = db.get_member(id) {
                        names.insert(m.name.clone());
                    } else if let Some(l) = db.get_live(id) {
                        names.insert(l.name.clone());
                    }
                }
            }
            names.len() as i32
        } else {
            let mut res = 0;
            for (id, slot) in ids {
                let matched = state.card_matches_filter_with_struct(db, id, slot, &filter, ctx);
                if matched {
                    res += 1;
                }
            }
            res
        }
    } else {
        match op {
            C_COUNT_ENERGY => {
                let filter = CardFilter::from_attr(attr as i64);
                let (primary_player, secondary_player) = target_player_pair(&filter, p_idx);
                let mut total = state.players[primary_player].energy_zone.len() as i32;
                if let Some(other_player) = secondary_player {
                    total += state.players[other_player].energy_zone.len() as i32;
                }
                total
            }
            C_COUNT_BLADES | C_COUNT_HEARTS | C_COUNT_STAGE | C_COUNT_GROUP => {
                let target_slot = slot & 0x0F;
                let resolved_slot = if target_slot == 10 {
                    (ctx.target_slot as i32).max(0) as usize
                } else if target_slot > 0 && target_slot <= 3 {
                    (target_slot - 1) as usize
                } else {
                    99
                };

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
                    let color_mask = (attr >> FILTER_COLOR_SHIFT_R5) & 0x7F;

                    if resolved_slot < 3 {
                        let h = state.get_effective_hearts(p_idx, resolved_slot, db, depth);
                        if color_mask == 0 {
                            h.get_total_count() as i32
                        } else {
                            if color_mask.count_ones() == 1 {
                                let color = color_mask.trailing_zeros() as usize;
                                if color < 7 {
                                    return h.get_color_count(color) as i32;
                                }
                            }
                            let mut sum = 0;
                            let h_arr = h.to_array();
                            for i in 0..6 {
                                if (color_mask & (1 << i)) != 0 {
                                    sum += h_arr[i] as i32;
                                }
                            }
                            sum
                        }
                    } else {
                        let hearts = state.get_total_hearts(p_idx, db, depth).to_array();
                        if color_mask == 0 {
                            hearts.iter().map(|&x| x as i32).sum()
                        } else {
                            let mut sum = 0;
                            for i in 0..6 {
                                if (color_mask & (1 << i)) != 0 {
                                    sum += hearts.get(i).copied().unwrap_or(0) as i32;
                                }
                            }
                            sum
                        }
                    }
                } else {
                    0
                }
            }
            250 => {
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
    let filter = CardFilter::from_attr(filter_attr as i64);
    let (primary_player, secondary_player) = target_player_pair(&filter, p_idx);

    let count_zone = |cards: &[i32]| -> i32 {
        cards
            .iter()
            .filter(|&&id| id >= 0 && state.card_matches_filter(db, id, filter_attr))
            .count() as i32
    };

    match cond_id {
        C_COUNT_STAGE => {
            let mut total = count_zone(&state.players[primary_player].stage);
            if let Some(other_player) = secondary_player {
                total += count_zone(&state.players[other_player].stage);
            }
            total
        }
        C_COUNT_HAND => {
            let mut total = count_zone(&state.players[primary_player].hand);
            if let Some(other_player) = secondary_player {
                total += count_zone(&state.players[other_player].hand);
            }
            total
        }
        C_COUNT_DISCARD => {
            let mut total = count_zone(&state.players[primary_player].discard);
            if let Some(other_player) = secondary_player {
                total += count_zone(&state.players[other_player].discard);
            }
            total
        }
        C_COUNT_ENERGY => {
            let mut total = state.players[primary_player].energy_zone.len() as i32;
            if let Some(other_player) = secondary_player {
                total += state.players[other_player].energy_zone.len() as i32;
            }
            total
        }
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
