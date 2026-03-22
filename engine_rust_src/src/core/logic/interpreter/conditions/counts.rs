use crate::core::enums::*;
use crate::core::logic::constants::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::hearts::HeartBoard;

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
        || (op >= 400 && op < 500)
    {
        let filter = CardFilter::from_attr(attr as i64);
        let include_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8 || filter.target_player == TARGET_PLAYER_BOTH as u8;
        let only_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8;

        let zone_mask = filter.zone_mask as u64;
        let has_zone_mask = zone_mask != 0;

        let slot_decoded = crate::core::logic::interpreter::instruction::DecodedSlot::decode(slot);
        let s_zone = slot_decoded.source_zone;

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

        use smallvec::SmallVec;
        let mut ids = SmallVec::<[i32; 32]>::new();

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

        if (attr & FILTER_UNIQUE_NAMES) != 0 {
            let mut names = std::collections::HashSet::new();
            for id in ids {
                let matched = if state.debug.debug_mode {
                    state.card_matches_filter_with_ctx_logs(db, id, filter_attr, ctx)
                } else {
                    state.card_matches_filter_with_struct(db, id, &filter, ctx)
                };
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
            let special_id = (filter_attr >> 56) & 0x7;
            let mut final_filter_struct = filter.clone();
            let mut final_filter_attr = filter_attr;
            if special_id == 2 || special_id == 3 {
                final_filter_struct.special_id = 0;
                final_filter_attr &= !(0x7u64 << 56);
            }

            let raw_count = ids.iter()
                .filter(|&&id| {
                    if state.debug.debug_mode {
                        state.card_matches_filter_with_ctx_logs(db, id, final_filter_attr, ctx)
                    } else {
                        state.card_matches_filter_with_struct(db, id, &final_filter_struct, ctx)
                    }
                })
                .count() as i32;

            let mut res = raw_count;
            if special_id == 2 || special_id == 3 {
                let target_id = if special_id == 3 { ctx.source_card_id } else { ctx.activator_id as i32 };
                let target_matched = if state.debug.debug_mode {
                    state.card_matches_filter_with_ctx_logs(db, target_id, final_filter_attr, ctx)
                } else {
                    state.card_matches_filter_with_struct(db, target_id, &final_filter_struct, ctx)
                };
                if ids.contains(&target_id) && target_matched {
                    res = (res - 1).max(0);
                }
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

    match cond_id {
        C_COUNT_STAGE => {
            let mut ids = Vec::new();
            ids.extend(player.stage.iter().filter(|&&id| id >= 0));
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
