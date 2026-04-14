use crate::core::logic::constants::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::models::{AbilityFrameComponents, SemanticCountZone};
use crate::core::enums::TriggerType;
use crate::core::models::Zone;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

#[inline]
fn needs_card_scan(filter: &CardFilter) -> bool {
    filter.card_type != 0
        || filter.group_enabled
        || filter.unit_enabled
        || filter.is_tapped
        || filter.has_blade_heart
        || filter.not_has_blade_heart
        || filter.value_enabled
        || filter.color_mask != 0
        || filter.char_id_1 != 0
        || filter.char_id_2 != 0
        || filter.char_id_3 != 0
        || filter.special_id != 0
        || filter.is_setsuna
        || filter.compare_accumulated
        || filter.is_optional
        || filter.keyword_energy
        || filter.keyword_member
}

#[inline]
fn count_zone_len(cards: &[i32]) -> i32 {
    cards.iter().filter(|&&id| id >= 0).count() as i32
}

#[inline]
fn count_dense_zone_len(cards: &[i32]) -> i32 {
    cards.len() as i32
}

#[inline]
fn sum_matching_live_required_hearts(
    required_hearts: &[u8; 7],
    color_mask: u8,
    heart_req_reductions: &HeartBoard,
) -> i32 {
    let mut total = 0;
    for color_idx in 0..7 {
        if color_mask != 0 && (color_mask & (1u8 << color_idx)) == 0 {
            continue;
        }
        total += (required_hearts[color_idx] as i32
            - heart_req_reductions.get_color_count(color_idx) as i32)
            .max(0);
    }
    total
}

#[inline]
fn count_unique_groups_in_cards(
    state: &GameState,
    db: &CardDatabase,
    ids: impl IntoIterator<Item = (i32, Option<(u8, i16)>)>,
    filter: &CardFilter,
    count_ctx: &AbilityContext,
) -> i32 {
    let mut groups = std::collections::HashSet::<u8>::new();
    for (id, slot) in ids {
        if id < 0 {
            continue;
        }
        if state.card_matches_filter_with_struct(db, id, slot, filter, count_ctx) {
            if let Some(member) = db.get_member(id) {
                for group_id in member.groups.iter().copied() {
                    groups.insert(group_id);
                }
            } else if let Some(live) = db.get_live(id) {
                for group_id in live.groups.iter().copied() {
                    groups.insert(group_id);
                }
            }
        }
    }
    groups.len() as i32
}

#[inline]
fn zone_mask_blocks_simple_count(filter: &CardFilter, expected_mask: u8) -> bool {
    match filter.zone_mask as i32 {
        0 => false,
        ZONE_MASK_STAGE => expected_mask != Zone::Stage as u8,
        ZONE_MASK_HAND => expected_mask != Zone::Hand as u8,
        ZONE_MASK_DISCARD => expected_mask != Zone::Discard as u8,
        _ => false,
    }
}

#[inline]
fn decode_count_filter(attr: u64) -> CardFilter {
    let mut filter = CardFilter::from_attr(attr);
    if (attr & crate::core::generated_constants::FILTER_ANY_STAGE) != 0 && filter.target_player == 0 {
        filter.target_player = TARGET_PLAYER_BOTH as u8;
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

fn collect_zone_ids(
    check_stage: bool,
    check_discard: bool,
    check_hand: bool,
    check_success: bool,
    state: &GameState,
    p_idx: usize,
    stage_primary_player: usize,
    stage_secondary_player: Option<usize>,
    include_opponent: bool,
    only_opponent: bool,
) -> smallvec::SmallVec<[(i32, Option<(u8, i16)>); 32]> {
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
            extend_with_slot(&mut ids, &state.players[p_idx].discard, p_idx as u8, 100);
        }
        if check_hand {
            extend_with_slot(&mut ids, &state.players[p_idx].hand, p_idx as u8, 200);
        }
        if check_success {
            extend_with_slot(&mut ids, &state.players[p_idx].success_lives, p_idx as u8, -1);
        }
    }
    if include_opponent {
        if check_discard {
            extend_with_slot(&mut ids, &state.players[1 - p_idx].discard, (1 - p_idx) as u8, 100);
        }
        if check_hand {
            extend_with_slot(&mut ids, &state.players[1 - p_idx].hand, (1 - p_idx) as u8, 200);
        }
        if check_success {
            extend_with_slot(&mut ids, &state.players[1 - p_idx].success_lives, (1 - p_idx) as u8, -1);
        }
    }

    ids
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
    let can_use_simple_len =
        !frame.counts_unique_names() && !frame.counts_unique_groups() && !needs_card_scan(&filter);

    if can_use_simple_len {
        if check_stage {
            if zone_mask_blocks_simple_count(&filter, Zone::Stage as u8) {
                return 0;
            }
            let mut total = count_zone_len(&state.players[stage_primary_player].stage);
            if let Some(other_player) = stage_secondary_player {
                total += count_zone_len(&state.players[other_player].stage);
            }
            return total;
        }
        if check_discard {
            if zone_mask_blocks_simple_count(&filter, Zone::Discard as u8) {
                return 0;
            }
            let mut total = count_dense_zone_len(&state.players[p_idx].discard);
            if include_opponent {
                total += count_dense_zone_len(&state.players[1 - p_idx].discard);
            }
            return total;
        }
        if check_hand {
            if zone_mask_blocks_simple_count(&filter, Zone::Hand as u8) {
                return 0;
            }
            let mut total = count_dense_zone_len(&state.players[p_idx].hand);
            if include_opponent {
                total += count_dense_zone_len(&state.players[1 - p_idx].hand);
            }
            return total;
        }
        if check_success {
            let mut total = state.players[p_idx].success_lives.len() as i32;
            if include_opponent {
                total += state.players[1 - p_idx].success_lives.len() as i32;
            }
            return total;
        }
    }

    if frame.counts_unique_groups() {
        if check_stage {
            if zone_mask_blocks_simple_count(&filter, Zone::Stage as u8) {
                return 0;
            }
            let ids = collect_zone_ids(true, false, false, false, state, p_idx, stage_primary_player, stage_secondary_player, include_opponent, only_opponent);
            return count_unique_groups_in_cards(state, db, ids, &filter, &count_ctx);
        }
        if check_discard {
            if zone_mask_blocks_simple_count(&filter, Zone::Discard as u8) {
                return 0;
            }
            let ids = collect_zone_ids(false, true, false, false, state, p_idx, p_idx, None, include_opponent, only_opponent);
            return count_unique_groups_in_cards(state, db, ids, &filter, &count_ctx);
        }
        if check_hand {
            if zone_mask_blocks_simple_count(&filter, Zone::Hand as u8) {
                return 0;
            }
            let ids = collect_zone_ids(false, false, true, false, state, p_idx, p_idx, None, include_opponent, only_opponent);
            return count_unique_groups_in_cards(state, db, ids, &filter, &count_ctx);
        }
        if check_success {
            let ids = collect_zone_ids(false, false, false, true, state, p_idx, p_idx, None, include_opponent, only_opponent);
            return count_unique_groups_in_cards(state, db, ids, &filter, &count_ctx);
        }
    }

    let ids = collect_zone_ids(
        check_stage,
        check_discard,
        check_hand,
        check_success,
        state,
        p_idx,
        stage_primary_player,
        stage_secondary_player,
        include_opponent,
        only_opponent,
    );

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
    } else if frame.counts_unique_groups() {
        let mut groups = std::collections::HashSet::<u8>::new();
        for (id, slot) in ids {
            let matched = state.card_matches_filter_with_struct(db, id, slot, &filter, &count_ctx);
            if matched {
                if let Some(m) = db.get_member(id) {
                    for group_id in m.groups.iter().copied() {
                        groups.insert(group_id);
                    }
                } else if let Some(l) = db.get_live(id) {
                    for group_id in l.groups.iter().copied() {
                        groups.insert(group_id);
                    }
                }
            }
        }
        groups.len() as i32
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

    if !frame.counts_unique_names() && !frame.counts_unique_groups() && !needs_card_scan(&filter) {
        return count_zone_len(&player.live_zone);
    }

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
    } else if frame.counts_unique_groups() {
        let mut groups = std::collections::HashSet::<u8>::new();
        for (slot_idx, &id) in player.live_zone.iter().enumerate().filter(|(_, &id)| id >= 0) {
            if state.card_matches_filter_with_struct(
                db,
                id,
                Some((p_idx as u8, slot_idx as i16)),
                &filter,
                ctx,
            ) {
                if let Some(member) = db.get_member(id) {
                    for group_id in member.groups.iter().copied() {
                        groups.insert(group_id);
                    }
                } else if let Some(live) = db.get_live(id) {
                    for group_id in live.groups.iter().copied() {
                        groups.insert(group_id);
                    }
                }
            }
        }
        groups.len() as i32
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
    let player = &state.players[p_idx];

    if frame.opcode == C_COUNT_LIVE_ZONE {
        resolve_live_zone_count(state, db, frame, ctx)
    } else if frame.opcode == C_COUNT_LIVE_HEARTS {
        let color_mask = frame.filter.color_mask;
        let mut total = 0;
        for (slot_idx, &id) in player.live_zone.iter().enumerate().filter(|(_, &id)| id >= 0) {
            if state.card_matches_filter_with_struct(
                db,
                id,
                Some((p_idx as u8, slot_idx as i16)),
                &frame.filter,
                ctx,
            ) {
                if let Some(live) = db.get_live(id) {
                    total += sum_matching_live_required_hearts(
                        &live.required_hearts,
                        color_mask,
                        &player.heart_req_reductions,
                    );
                }
            }
        }
        total
    } else if frame.opcode == C_COUNT_SUCCESS_LIVE_SCORE {
        let mut total = 0;
        for &cid in &player.success_lives {
            if let Some(live) = db.get_live(cid) {
                if live.score as i32 == frame.value {
                    total += 1;
                }
            }
        }
        total
    } else if is_structured_zone_count(frame) {
        resolve_structured_zone_count(state, db, frame, ctx)
    } else {
        match frame.opcode {
            C_COUNT_STAGE => {
                let (primary_player, secondary_player) = target_player_pair(&frame.filter, p_idx);
                let count_zone = |cards: &[i32]| {
                    cards
                        .iter()
                        .enumerate()
                        .filter(|(_, &id)| id >= 0)
                        .filter(|(_, &id)| {
                            state.card_matches_filter_with_struct(
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
                let count_from_yell = frame.slot.target_slot == Zone::Yell as u8
                    || frame.slot.source_zone == Zone::Yell;
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
                let yell_cards = |player_idx: usize| -> i32 {
                    state.players[player_idx]
                        .yell_cards
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
                let mut total = if count_from_yell {
                    yell_cards(primary_player)
                } else {
                    count_zone(&state.players[primary_player].hand)
                };
                if let Some(other_player) = secondary_player {
                    total += if count_from_yell {
                        yell_cards(other_player)
                    } else {
                        count_zone(&state.players[other_player].hand)
                    };
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
                let count_energy = |player_idx: usize| -> i32 {
                    if ctx.trigger_type == TriggerType::OnPlay {
                        state.players[player_idx].energy_zone.len() as i32
                    } else {
                        (state.players[player_idx].energy_zone.len()
                            - state.players[player_idx].tapped_energy_count() as usize)
                            as i32
                    }
                };
                let mut total = count_energy(primary_player);
                if let Some(other_player) = secondary_player {
                    total += count_energy(other_player);
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
            if !filter.unique_names && !needs_card_scan(&filter) {
                if zone_mask_blocks_simple_count(&filter, Zone::Stage as u8) {
                    0
                } else {
                    let mut total = count_dense_zone_len(&state.players[primary_player].stage);
                    if let Some(other_player) = secondary_player {
                        total += count_dense_zone_len(&state.players[other_player].stage);
                    }
                    total
                }
            } else {
                let mut total = count_zone(&state.players[primary_player].stage);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].stage);
                }
                total
            }
        }
        C_COUNT_HAND => {
            if !filter.unique_names && !needs_card_scan(&filter) {
                if zone_mask_blocks_simple_count(&filter, Zone::Hand as u8) {
                    0
                } else {
                    let mut total = count_dense_zone_len(&state.players[primary_player].hand);
                    if let Some(other_player) = secondary_player {
                        total += count_dense_zone_len(&state.players[other_player].hand);
                    }
                    total
                }
            } else {
                let mut total = count_zone(&state.players[primary_player].hand);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].hand);
                }
                total
            }
        }
        C_COUNT_DISCARD => {
            if !filter.unique_names && !needs_card_scan(&filter) {
                if zone_mask_blocks_simple_count(&filter, Zone::Discard as u8) {
                    0
                } else {
                    let mut total = count_dense_zone_len(&state.players[primary_player].discard);
                    if let Some(other_player) = secondary_player {
                        total += count_dense_zone_len(&state.players[other_player].discard);
                    }
                    total
                }
            } else {
                let mut total = count_zone(&state.players[primary_player].discard);
                if let Some(other_player) = secondary_player {
                    total += count_zone(&state.players[other_player].discard);
                }
                total
            }
        }
        C_COUNT_ENERGY => {
            let mut total = (state.players[primary_player].energy_zone.len()
                - state.players[primary_player].tapped_energy_count() as usize) as i32;
            if let Some(other_player) = secondary_player {
                total += (state.players[other_player].energy_zone.len()
                    - state.players[other_player].tapped_energy_count() as usize) as i32;
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
