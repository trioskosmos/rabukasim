use crate::core::logic::interpreter::suspension::resolve_target_player;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::models::AbilityContext;
use crate::core::enums::Zone;

use super::*;

use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO, CHOICE_YES, TARGET_SLOT_STAGE};

#[path = "flow_select_resolve.rs"]
mod flow_select_resolve;

fn cards_for_source_zone(state: &GameState, target_player: usize, source_zone: Zone) -> &[i32] {
    match source_zone {
        Zone::Hand => state.players[target_player].hand.as_slice(),
        Zone::Discard => state.players[target_player].discard.as_slice(),
        _ => state.players[target_player].stage.as_slice(),
    }
}

fn selected_target_key(source_zone: Zone, slot_idx: usize) -> i32 {
    ((source_zone as i32) << 8) | slot_idx as i32
}

fn resolve_select_member_target_player(
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    filter_attr: u64,
    p_idx: usize,
    is_targeted_select_member_cost: bool,
) -> usize {
    if is_targeted_select_member_cost {
        return p_idx;
    }

    resolve_target_player(slot_info, filter_attr, p_idx)
}

#[allow(clippy::too_many_arguments)]
pub fn handle_select_ops(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let partial_selection_prompt = -1000 - (v as i16);
    let frame_filter_attr = frame_data.filter.to_attr();
    let raw_filter_attr = if frame_filter_attr != 0 || frame_data.raw_attr != 0 {
        frame_data.resolved_filter_attr()
    } else {
        a as u64
    };
    let resolved_filter_attr = if op == O_SELECT_MEMBER {
        frame_data.normalized_select_member_filter_attr()
    } else {
        raw_filter_attr
    };
    let _real_op = if op == O_RECOVER_LIVE || op == O_RECOVER_MEMBER { op } else { frame_data.opcode };
    let next_frame = if op == O_SELECT_MEMBER {
        db.get_member(ctx.source_card_id)
            .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
            .or_else(|| {
                db.get_live(ctx.source_card_id)
                    .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
            })
            .and_then(|ability| ability.get_frame(frame_idx + 1))
    } else {
        None
    };
    let legacy_move_member_follow_up = next_frame
        .as_ref()
        .map(|next| {
            matches!(
                next.opcode(),
                O_MOVE_MEMBER | O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD
            )
        })
        .unwrap_or(false);
    let mut effective_slot_info = slot_info;
    if op == O_SELECT_MEMBER {
        if let Some(next) = next_frame.as_ref() {
            effective_slot_info.source_zone = match next.opcode() {
                O_PLAY_MEMBER_FROM_HAND => crate::core::enums::Zone::Hand,
                O_PLAY_MEMBER_FROM_DISCARD => crate::core::enums::Zone::Discard,
                _ => effective_slot_info.source_zone,
            };
        }
    }

    let supports_partial_completion =
        op == O_SELECT_MEMBER && v > 1 && !legacy_move_member_follow_up;

    if supports_partial_completion && ctx.v_remaining == partial_selection_prompt {
        if ctx.choice_index == CHOICE_YES || ctx.choice_index == CHOICE_NO || ctx.choice_index == CHOICE_DONE {
            ctx.choice_index = -1;

            ctx.v_remaining = -1;

            return HandlerResult::Continue;
        }
        // The following line is modified to allow continuation into normal suspension
        // instead of returning Main immediately.
    }

    if supports_partial_completion && ctx.choice_index == CHOICE_DONE {
        ctx.choice_index = -1;

        ctx.v_remaining = -1;
    }

    let is_targeted_select_member_cost = slot_info.target_slot == TARGET_SLOT_STAGE && resolved_filter_attr != 0;
    let filter_attr = if is_targeted_select_member_cost {
        frame_data.targeted_select_member_filter_attr()
    } else {
        resolved_filter_attr
    };

    if op == O_SELECT_MEMBER && v == 99 && ctx.choice_index == -1 {
        let target_player = resolve_select_member_target_player(
            effective_slot_info,
            filter_attr,
            p_idx,
            is_targeted_select_member_cost,
        );
        ctx.selected_cards.clear();
        ctx.selected_target_keys.clear();

        for (slot_idx, &cid) in
            cards_for_source_zone(state, target_player, effective_slot_info.source_zone)
                .iter()
                .enumerate()
        {
            if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                ctx.selected_cards.push(cid);
                ctx.selected_target_keys
                    .push(selected_target_key(Zone::Stage, slot_idx));
            }
        }

        return HandlerResult::Continue;
    }

    if ctx.choice_index == -1 {
        let choice_type = match op {
            O_SELECT_MEMBER => ChoiceType::SelectMember,

            O_SELECT_LIVE => ChoiceType::SelectLive,

            O_SELECT_PLAYER => ChoiceType::SelectPlayer,

            _ => ChoiceType::None,
        };

        let mut flip_ctx = ctx.clone();
        flip_ctx.player_id = match (filter_attr & 0x3) as u8 {
            2 => 1 - (p_idx as u8),
            3 => 1,
            _ => p_idx as u8,
        };

        let select_member_target_player = resolve_select_member_target_player(
            effective_slot_info,
            filter_attr,
            p_idx,
            is_targeted_select_member_cost,
        );
        let matching_cards = |target_player: usize| -> Vec<i32> {
            cards_for_source_zone(state, target_player, effective_slot_info.source_zone)
                .iter()
                .enumerate()
                .filter_map(|(_slot_idx, &cid)| {
                    if cid >= 0
                        && state.card_matches_filter_with_ctx(
                            db,
                            cid,
                            resolved_filter_attr,
                            ctx,
                        )
                    {
                        Some(cid)
                    } else {
                        None
                    }
                })
                .collect()
        };

        if state.debug.debug_mode && op == O_SELECT_MEMBER {
            eprintln!(
                "[SELECT_DBG] source={} player={} target_player={} source_zone={:?} raw_slot={} raw_attr=0x{:x} normalized_filter=0x{:x} targeted_cost={} choice_index={} v={} next_frame={:?}",
                ctx.source_card_id,
                p_idx,
                select_member_target_player,
                effective_slot_info.source_zone,
                s,
                a as u64,
                resolved_filter_attr,
                is_targeted_select_member_cost,
                ctx.choice_index,
                v,
                next_frame.as_ref().map(|frame| frame.opcode())
            );
        }

        if op == O_SELECT_MEMBER {
            let looked_cards = {
                let cards = matching_cards(select_member_target_player);
                if state.debug.debug_mode {
                    eprintln!(
                        "[SELECT_DBG] initial_candidates source={} target_player={} cards={:?}",
                        ctx.source_card_id,
                        select_member_target_player,
                        cards
                    );
                }
                cards
            };
            let looked_cards = looked_cards;
            if looked_cards.is_empty() {
                if state.debug.debug_mode {
                    eprintln!(
                        "[SELECT_DBG] no_candidates source={} target_player={} source_zone={:?} filter=0x{:x}",
                        ctx.source_card_id,
                        select_member_target_player,
                        effective_slot_info.source_zone,
                        resolved_filter_attr
                    );
                }
                return HandlerResult::Return;
            };

            if state.debug.debug_mode {
                eprintln!(
                    "[SELECT_DBG] suspending source={} target_player={} looked_cards={:?}",
                    ctx.source_card_id,
                    select_member_target_player,
                    looked_cards
                );
            }

            state.players[select_member_target_player].looked_cards = looked_cards.into();
        }

        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                &flip_ctx,
                frame_idx,
                op,
                s,
                choice_type,
                filter_attr,
                if op == O_SELECT_MEMBER && v > 0 {
                    v as i16
                } else {
                    -1
                },
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    } else {
        return flow_select_resolve::resolve_select_choice(
            state,
            db,
            ctx,
            frame_idx,
            op,
            v,
            a,
            s,
            p_idx,
                effective_slot_info,
                supports_partial_completion,
                partial_selection_prompt,
                legacy_move_member_follow_up,
        );
    }

    HandlerResult::Continue
}
