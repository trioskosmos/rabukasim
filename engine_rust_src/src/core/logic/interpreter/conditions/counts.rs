use crate::core::logic::constants::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::models::{AbilityFrameComponents, SemanticCountZone};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

fn decode_count_filter(attr: u64) -> CardFilter {
    let mut filter = CardFilter::from_attr(attr);
    if (attr & crate::core::generated_constants::FILTER_ANY_STAGE) != 0 && filter.target_player == 0 {
        filter.target_player = TARGET_PLAYER_BOTH as u8;
    }
    if filter.value_enabled {
        filter.value_enabled = false;
        filter.value_threshold = 0;
        filter.is_le = false;
        filter.is_cost_type = false;
    }
    filter
}

fn target_player_pair(filter: &CardFilter, p_idx: usize) -> (usize, Option<usize>) {
    match filter.target_player {
        2 => (1 - p_idx, None),
        3 => (p_idx, Some(1 - p_idx)),
        _ => (p_idx, None),
    }
}

fn count_components(op: i32, attr: u64, slot: i32) -> AbilityFrameComponents<'static> {
    let is_negated = op >= OPCODE_NEGATION_OFFSET;
    AbilityFrameComponents {
        raw_opcode: op,
        opcode: if is_negated {
            op - OPCODE_NEGATION_OFFSET
        } else {
            op
        },
        value: 0,
        filter: decode_count_filter(attr),
        slot: crate::core::logic::interpreter::instruction::DecodedSlot::decode(slot),
        raw_attr: attr,
        raw_slot: slot,
        is_negated,
        is_cost: false,
        params: None,
    }
}

fn is_structured_zone_count(frame: &AbilityFrameComponents<'_>) -> bool {
    let op = frame.opcode;
    op == C_COUNT_STAGE
        || op == C_COUNT_HAND
        || op == C_COUNT_DISCARD
        || op == C_COUNT_SUCCESS_LIVE
        || op == C_COUNT_GROUP
        || op == C_SUCCESS_PILE_COUNT
        || op == 13
        || (op >= 400 && op < 500)
        || frame.slot.is_dynamic
}

fn extend_with_slot(
    ids: &mut smallvec::SmallVec<[(i32, Option<(u8, i16)>); 32]>,
    cards: &[i32],
    p_idx: u8,
    base_slot: i16,
) {
    for (i, &id) in cards.iter().enumerate() {
        if id >= 0 {
            let s_idx = if base_slot >= 0 {
                base_slot + i as i16
            } else {
                -1
            };
            ids.push((
                id,
                if s_idx >= 0 {
                    Some((p_idx, s_idx))
                } else {
                    None
                },
            ));
        }
    }
}

fn resolve_structured_zone_count(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
) -> i32 {
    let p_idx = ctx.activator_id as usize;
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];
    let mut count_ctx = ctx.clone();
    count_ctx.player_id = ctx.activator_id;

    let mut filter = frame.filter;
    if frame.opcode == C_COUNT_GROUP {
        if let Some(group_id) = frame.semantic_group_id(frame.raw_attr as i32) {
            filter.group_enabled = true;
            filter.group_id = group_id;
        }
    }
    let include_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8
        || filter.target_player == TARGET_PLAYER_BOTH as u8;
    let only_opponent = filter.target_player == TARGET_PLAYER_OPPONENT as u8;
    let (stage_primary_player, stage_secondary_player) = frame.stage_player_scope(p_idx);

    let zone_mask = filter.zone_mask as u64;
    let has_zone_mask = zone_mask != 0;
    let inferred_zone = frame.inferred_count_zone();

    let is_explicit_success_count =
        frame.opcode == C_COUNT_SUCCESS_LIVE || frame.opcode == 307 || frame.opcode == 405;

    let check_stage = if is_explicit_success_count {
        false
    } else if frame.opcode >= 400 && frame.opcode < 500 {
        frame.opcode == 401
            || (has_zone_mask && zone_mask == ZONE_STAGE as u64)
            || (!has_zone_mask && inferred_zone == Some(SemanticCountZone::Stage))
    } else if has_zone_mask {
        zone_mask == ZONE_STAGE as u64
    } else {
        frame.opcode == C_COUNT_STAGE
            || frame.opcode == C_COUNT_GROUP
            || inferred_zone == Some(SemanticCountZone::Stage)
    };
    let check_discard = if is_explicit_success_count {
        false
    } else if frame.opcode >= 400 && frame.opcode < 500 {
        frame.opcode == 403
            || (has_zone_mask && zone_mask == ZONE_DISCARD as u64)
            || (!has_zone_mask && inferred_zone == Some(SemanticCountZone::Discard))
    } else if has_zone_mask {
        zone_mask == ZONE_DISCARD as u64
    } else {
        frame.opcode == C_COUNT_DISCARD || inferred_zone == Some(SemanticCountZone::Discard)
    };
    let check_hand = if is_explicit_success_count {
        false
    } else if frame.opcode >= 400 && frame.opcode < 500 {
        frame.opcode == 402
            || (has_zone_mask && zone_mask == ZONE_HAND as u64)
            || (!has_zone_mask && inferred_zone == Some(SemanticCountZone::Hand))
    } else if has_zone_mask {
        zone_mask == ZONE_HAND as u64
    } else {
        frame.opcode == C_COUNT_HAND || inferred_zone == Some(SemanticCountZone::Hand)
    };
    let check_success =
        is_explicit_success_count || inferred_zone == Some(SemanticCountZone::SuccessPile);

    let mut ids = smallvec::SmallVec::<[(i32, Option<(u8, i16)>); 32]>::new();

    if check_stage {
        extend_with_slot(
            &mut ids,
            &state.players[stage_primary_player].stage,
            stage_primary_player as u8,
            0,
        );
        if let Some(other_player) = stage_secondary_player {
            extend_with_slot(
                &mut ids,
                &state.players[other_player].stage,
                other_player as u8,
                0,
            );
        }
    }

    if !only_opponent {
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

    if frame.counts_unique_names() {
        let mut names = std::collections::HashSet::new();
        for (id, slot) in ids {
            let matched = state.card_matches_filter_with_struct(db, id, slot, &filter, &count_ctx);
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
            let matched = state.card_matches_filter_with_struct(db, id, slot, &filter, &count_ctx);
            if matched {
                res += 1;
            }
        }
        res
    }
}

fn resolve_live_zone_count(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
) -> i32 {
    let p_idx = ctx.activator_id as usize;
    let player = &state.players[p_idx];
    let filter = frame.filter;

    if frame.counts_unique_names() {
        let mut names = std::collections::HashSet::new();
        for (slot_idx, &id) in player.live_zone.iter().enumerate().filter(|(_, &id)| id >= 0) {
            if state.card_matches_filter_with_struct(
                db,
                id,
                Some((p_idx as u8, slot_idx as i16)),
                &filter,
                ctx,
            ) {
                if let Some(live) = db.get_live(id) {
                    names.insert(live.name.clone());
                }
            }
        }
        names.len() as i32
    } else {
        player
            .live_zone
            .iter()
            .enumerate()
            .filter(|(slot_idx, &id)| {
                id >= 0
                    && state.card_matches_filter_with_struct(
                        db,
                        id,
                        Some((p_idx as u8, *slot_idx as i16)),
                        &filter,
                        ctx,
                    )
            })
            .count() as i32
    }
}

fn resolve_count_components(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    depth: u32,
) -> i32 {
    let p_idx = ctx.activator_id as usize;

    if frame.opcode == C_COUNT_LIVE_ZONE {
        resolve_live_zone_count(state, db, frame, ctx)
    } else if is_structured_zone_count(frame) {
        resolve_structured_zone_count(state, db, frame, ctx)
    } else {
        match frame.opcode {
            C_COUNT_STAGE => {
                let (primary_player, secondary_player) = target_player_pair(&frame.filter, p_idx);
                let count_zone = |cards: &[i32]| {
                    cards
                        .iter()
                        .filter(|&&id| {
                            id >= 0
                                && state.card_matches_filter_with_struct(
                                    db,
                                    id,
                                    None,
                                    &frame.filter,
                                    ctx,
                                )
                        })
                        .count() as i32
                };
                let mut total = count_zone(&state.players[primary_player].stage);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].stage);
                }
                total
            }
            C_COUNT_HAND => {
                let (primary_player, secondary_player) = target_player_pair(&frame.filter, p_idx);
                let count_zone = |cards: &[i32]| {
                    cards
                        .iter()
                        .filter(|&&id| {
                            id >= 0
                                && state.card_matches_filter_with_struct(
                                    db,
                                    id,
                                    None,
                                    &frame.filter,
                                    ctx,
                                )
                        })
                        .count() as i32
                };
                let mut total = count_zone(&state.players[primary_player].hand);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].hand);
                }
                total
            }
            C_COUNT_DISCARD => {
                let (primary_player, secondary_player) = target_player_pair(&frame.filter, p_idx);
                let count_zone = |cards: &[i32]| {
                    cards
                        .iter()
                        .filter(|&&id| {
                            id >= 0
                                && state.card_matches_filter_with_struct(
                                    db,
                                    id,
                                    None,
                                    &frame.filter,
                                    ctx,
                                )
                        })
                        .count() as i32
                };
                let mut total = count_zone(&state.players[primary_player].discard);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].discard);
                }
                total
            }
            C_COUNT_ENERGY => {
                let (primary_player, secondary_player) = target_player_pair(&frame.filter, p_idx);
                let mut total = state.players[primary_player].energy_zone.len() as i32;
                if let Some(other_player) = secondary_player {
                    total += state.players[other_player].energy_zone.len() as i32;
                }
                total
            }
            C_COUNT_BLADES | C_COUNT_HEARTS => {
                let target_slot = frame.slot.target_slot;
                let resolved_slot = if target_slot == 10 {
                    (ctx.target_slot as i32).max(0) as usize
                } else if target_slot > 0 && target_slot <= 3 {
                    (target_slot - 1) as usize
                } else {
                    99
                };

                if frame.opcode == C_COUNT_BLADES {
                    if resolved_slot < 3 {
                        state.get_effective_blades(p_idx, resolved_slot, db, depth) as i32
                    } else {
                        let mut sum = 0;
                        for i in 0..3 {
                            sum += state.get_effective_blades(p_idx, i, db, depth) as i32;
                        }
                        sum
                    }
                } else {
                    let color_mask = frame.filter.color_mask as u64;

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

pub fn resolve_count_frame(
    state: &GameState,
    db: &CardDatabase,
    frame: &AbilityFrameComponents<'_>,
    ctx: &AbilityContext,
    depth: u32,
) -> i32 {
    resolve_count_components(state, db, frame, ctx, depth)
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
    let frame = count_components(op, attr, slot);
    resolve_count_components(state, db, &frame, ctx, depth)
}

pub fn get_condition_count(
    state: &GameState,
    db: &CardDatabase,
    cond_id: i32,
    attr: u64,
    ctx: &AbilityContext,
) -> i32 {
    let p_idx = ctx.activator_id as usize;
    let mut count_ctx = ctx.clone();
    count_ctx.player_id = ctx.activator_id;
    let player = &state.players[p_idx];
    let opponent = &state.players[1 - p_idx];

    let filter = decode_count_filter(attr);
    let (primary_player, secondary_player) = target_player_pair(&filter, p_idx);

    let count_zone = |cards: &[i32]| -> i32 {
        cards
            .iter()
            .filter(|&&id| id >= 0 && state.card_matches_filter_with_struct(db, id, None, &filter, &count_ctx))
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
