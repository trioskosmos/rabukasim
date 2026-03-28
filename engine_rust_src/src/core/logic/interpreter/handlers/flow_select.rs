use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::suspension::resolve_target_player;
use crate::core::logic::models::AbilityFrame;

use super::*;

use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO, CHOICE_YES, TARGET_SLOT_STAGE};

#[path = "flow_select_resolve.rs"]
mod flow_select_resolve;

fn cards_for_source_zone(state: &GameState, target_player: usize, source_zone: u8) -> &[i32] {
    match source_zone {
        6 => state.players[target_player].hand.as_slice(),
        7 => state.players[target_player].discard.as_slice(),
        _ => state.players[target_player].stage.as_slice(),
    }
}

#[allow(clippy::too_many_arguments)]
pub fn handle_select_ops(
    state: &mut GameState,

    db: &CardDatabase,

    ctx: &mut AbilityContext,

    _frame: &AbilityFrame,

    frame_idx: usize,

    op: i32,

    v: i32,

    a: i64,

    s: i32,

    p_idx: usize,

    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let partial_selection_prompt = -1000 - (v as i16);
    let frame_components = _frame.components();
    let frame_filter_attr = frame_components.filter.to_attr();
    let structured_filter = {
        let mut filter = frame_components.filter;
        filter.is_enabled = true;
        filter
    };
    let resolved_filter_attr = filter_attr_from_params(frame_components.params)
        .map(|attr| attr | frame_filter_attr)
        .unwrap_or_else(|| {
            if frame_filter_attr != 0 {
                frame_filter_attr
            } else {
                a as u64
            }
        });
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
        if ctx.choice_index == CHOICE_YES
            || ctx.choice_index == CHOICE_NO
            || ctx.choice_index == CHOICE_DONE
        {
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

    let is_targeted_select_member_cost =
        slot_info.target_slot == TARGET_SLOT_STAGE && resolved_filter_attr != 0;
    let filter_attr = if is_targeted_select_member_cost {
        (resolved_filter_attr & !0x3) | 1
    } else {
        resolved_filter_attr
    };

    if state.debug.debug_mode && op == O_SELECT_MEMBER {
        state.trace_internal(&format!(
            "FRAME_SELECT_MEMBER: [phase={:?}] source_zone={} filter=[{}] {}",
            state.phase,
            effective_slot_info.source_zone as u8,
            logging::describe_filter_attr(
                crate::core::logic::interpreter::instruction::DecodedFilterAttr::decode(
                    filter_attr as i64
                )
            ),
            logging::describe_context(ctx)
        ));
    }

    if op == O_SELECT_MEMBER && v == 99 && ctx.choice_index == -1 {
        let target_player = if is_targeted_select_member_cost { p_idx } else { resolve_target_player(effective_slot_info, filter_attr, p_idx) };
        ctx.selected_cards.clear();
        ctx.selected_target_keys.clear();

        for (slot_idx, &cid) in
            cards_for_source_zone(state, target_player, effective_slot_info.source_zone as u8)
                .iter()
                .enumerate()
        {
            if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                ctx.selected_cards.push(cid);
                ctx.selected_target_keys
                    .push(((4_i32) << 8) | (slot_idx as i32 & 0xFF));
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

        let select_member_target_player = if is_targeted_select_member_cost { p_idx } else { resolve_target_player(effective_slot_info, filter_attr, p_idx) };
        let matching_cards: Vec<i32> = cards_for_source_zone(state, select_member_target_player, effective_slot_info.source_zone as u8)
            .iter()
            .enumerate()
            .filter_map(|(slot_idx, &cid)| {
                if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, resolved_filter_attr, ctx) {
                    Some(cid)
                } else {
                    None
                }
            })
            .collect();

        if op == O_SELECT_MEMBER {
            let looked_cards = if matching_cards.is_empty() {
                state.players[select_member_target_player]
                    .stage
                    .iter()
                    .enumerate()
                    .filter_map(|(slot_idx, &cid)| {
                        if cid >= 0
                            && state.card_matches_filter_with_struct(
                                db,
                                cid,
                                Some((select_member_target_player as u8, slot_idx as i16)),
                                &structured_filter,
                                ctx,
                            )
                        {
                            Some(cid)
                        } else {
                            None
                        }
                    })
                    .collect::<Vec<i32>>()
            } else {
                matching_cards
            };
            if looked_cards.is_empty() {
                return HandlerResult::Continue;
            };

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
