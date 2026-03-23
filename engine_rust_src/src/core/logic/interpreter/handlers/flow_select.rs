use crate::core::logic::models::AbilityFrame;

use super::*;

use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

use crate::core::models::CHOICE_DONE;

#[path = "flow_select_resolve.rs"]
mod flow_select_resolve;

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

    let legacy_move_member_follow_up = if op == O_SELECT_MEMBER {
        let source_ability = db
            .get_member(ctx.source_card_id)
            .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
            .or_else(|| {
                db.get_live(ctx.source_card_id)
                    .and_then(|card| card.abilities.get(ctx.ability_index.max(0) as usize))
            });

        let next_frame = source_ability.and_then(|ability| ability.get_frame(frame_idx + 1));

        next_frame
            .map(|next| {
                matches!(
                    next.opcode(),
                    O_MOVE_MEMBER | O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD
                )
            })
            .unwrap_or(false)
    } else {
        false
    };

    let supports_partial_completion =
        op == O_SELECT_MEMBER && v > 1 && !legacy_move_member_follow_up;

    let is_optional = op == O_SELECT_MEMBER
        && (a as u64 & crate::core::logic::constants::FILTER_IS_OPTIONAL) != 0;

    if supports_partial_completion && ctx.v_remaining == partial_selection_prompt {
        if ctx.choice_index == 0 || ctx.choice_index == 1 || ctx.choice_index == CHOICE_DONE {
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

    if is_optional && ctx.choice_index == CHOICE_DONE {
        ctx.choice_index = -1;

        return HandlerResult::Continue;
    }

    if op == O_SELECT_MEMBER && v == 99 && ctx.choice_index == -1 {
        let filter_attr = a as u64;

        let target_player = match (filter_attr & 0x3) as u8 {
            2 => 1 - p_idx,

            3 => 1,

            _ => p_idx,
        };

        ctx.selected_cards.clear();

        for &cid in &state.players[target_player].stage {
            if cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
                ctx.selected_cards.push(cid);
            }
        }

        return HandlerResult::Continue;
    }

    let area_val = (s >> 29) & 0x07;

    if area_val >= 1 && area_val <= 3 {
        let auto_slot = (area_val - 1) as i16;

        ctx.area_idx = auto_slot;

        if legacy_move_member_follow_up {
            ctx.choice_index = -1;
        } else {
            ctx.choice_index = auto_slot;
        }

        if state.debug.debug_mode {
            println!(
                "[DEBUG] O_SELECT_MEMBER: Auto-selecting slot {} based on area bits",
                auto_slot
            );
        }
    } else if ctx.choice_index == -1 {
        let choice_type = match op {
            O_SELECT_MEMBER => ChoiceType::SelectMember,

            O_SELECT_LIVE => ChoiceType::SelectLive,

            O_SELECT_PLAYER => ChoiceType::SelectPlayer,

            _ => ChoiceType::None,
        };

        let mut flip_ctx = ctx.clone();

        if s == 2 {
            flip_ctx.player_id = 1 - (p_idx as u8);
        } else if s == 3 {
            flip_ctx.player_id = 1;
        }

        if is_optional && op == O_SELECT_MEMBER {
            let source_zone = slot_info.source_zone as u8;

            let target_player = match (a as u64 & 0x3) as u8 {
                2 => 1 - (flip_ctx.player_id as usize),

                3 => 1,

                _ => flip_ctx.player_id as usize,
            };

            let has_legal_target = match source_zone {
                6 => state.players[target_player]
                    .hand
                    .iter()
                    .copied()
                    .any(|cid| {
                        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)
                    }),

                7 => state.players[target_player]
                    .discard
                    .iter()
                    .copied()
                    .any(|cid| {
                        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)
                    }),

                _ => state.players[target_player]
                    .stage
                    .iter()
                    .copied()
                    .any(|cid| {
                        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, a as u64, ctx)
                    }),
            };

            if !has_legal_target {
                return HandlerResult::Continue;
            }
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
                a as u64,
                -1,
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
            slot_info,
            supports_partial_completion,
            partial_selection_prompt,
            legacy_move_member_follow_up,
        );
    }

    HandlerResult::Continue
}
