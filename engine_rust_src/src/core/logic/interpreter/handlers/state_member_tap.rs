use crate::core::enums::*;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

use crate::core::logic::interpreter::handlers::state_helpers::tap_opponent_chooser_player;
use crate::core::logic::interpreter::handlers::HandlerResult;

#[path = "state_member_activate.rs"]
mod state_member_activate;
pub use state_member_activate::handle_activate_member;

pub fn handle_set_tapped(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    p_idx: usize,
    resolved_slot: i32,
) -> HandlerResult {
    let is_optional = frame_data.filter.is_optional;

    if is_optional && ctx.v_remaining == -1 && ctx.choice_index == 1 {
        if let Some(execution_id) = state.ui.current_execution_id {
            state.ui.cancelled_execution_ids.insert(execution_id);
        }
        return HandlerResult::Continue;
    }

    if is_optional && ctx.v_remaining == -1 && ctx.choice_index == 0 {
        if resolved_slot >= 0 && resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        ctx.choice_index = -1;
        return HandlerResult::Continue;
    }

    if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                crate::core::O_SET_TAPPED,
                resolved_slot as i32,
                ChoiceType::Optional,
                frame_data.raw_attr,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    let should_tap = frame_data.value != 0;

    let tap_slot = if is_optional && ctx.v_remaining == -1 {
        if resolved_slot >= 0 && resolved_slot < 3 {
            Some(resolved_slot as usize)
        } else {
            None
        }
    } else if is_optional && ctx.choice_index >= 0 && ctx.choice_index < 3 {
        Some(ctx.choice_index as usize)
    } else if resolved_slot >= 0 && resolved_slot < 3 {
        Some(resolved_slot as usize)
    } else {
        None
    };

    if let Some(slot) = tap_slot {
        if !state.ui.silent {
            if should_tap {
                state.log(format!("Rule 5.1, Rule 5.1.1: [メンバーをアピール済みにする] (Tapping) Member at Player {} Slot {}.", p_idx, slot + 1));
            } else {
                state.log(format!("Rule 5.2, Rule 5.2.1: [メンバーをアピール済みから元に戻す] (Untapping) Member at Player {} Slot {}.", p_idx, slot + 1));
            }
        }
        state.players[p_idx].set_tapped(slot, should_tap);
    }

    HandlerResult::Continue
}

pub fn handle_tap_opponent(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    a: i64,
    v: i32,
) -> HandlerResult {
    let target_p_idx = 1 - (ctx.activator_id as usize);
    let count = if ctx.v_remaining == -1 {
        v as i16
    } else {
        ctx.v_remaining
    };
    if count <= 0 {
        return HandlerResult::Continue;
    }

    if ctx.choice_index == -1 {
        let occupied_slots: Vec<usize> = state.players[target_p_idx]
            .stage
            .iter()
            .enumerate()
            .filter_map(|(idx, &cid)| (cid >= 0).then_some(idx))
            .collect();

        if occupied_slots.len() == 1 {
            state.set_member_tapped(target_p_idx, occupied_slots[0], true, db);
            return HandlerResult::Continue;
        }

        let mut choice_ctx = ctx.clone();
        choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);
        let suspended = suspend_choice(
            state,
            db,
            &choice_ctx,
            &choice_ctx,
            frame_idx,
            crate::core::O_TAP_OPPONENT,
            0,
            ChoiceType::TapO,
            a as u64,
            count,
        );

        if matches!(suspended, HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    } else {
        let slot_idx = ctx.choice_index as usize;
        if slot_idx < 3 {
            state.set_member_tapped(target_p_idx, slot_idx, true, db);
            ctx.v_remaining = count - 1;
            ctx.choice_index = -1;
            if ctx.v_remaining > 0 {
                let mut choice_ctx = ctx.clone();
                choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);
                let suspended = suspend_choice(
                    state,
                    db,
                    &choice_ctx,
                    &choice_ctx,
                    frame_idx,
                    crate::core::O_TAP_OPPONENT,
                    0,
                    ChoiceType::TapO,
                    a as u64,
                    ctx.v_remaining,
                );

                if matches!(suspended, HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
        }
    }

    HandlerResult::Continue
}

// Consolidated handle_tap_member - inlined from state_member_tap_member_*.rs
#[allow(clippy::too_many_arguments)]
pub fn handle_tap_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let is_optional = frame_data.filter.is_optional;
    let is_select_member_choice = frame_data.params.map(|params| {
        params.get("FILTER").is_some()
            || params.get("filter").is_some()
            || params.get("destination")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("target"))
                .unwrap_or(false)
            || params.get("cost_type_name")
                .and_then(|v| v.as_str())
                .map(|v| v.eq_ignore_ascii_case("SELECT_MEMBER"))
                .unwrap_or(false)
    }).unwrap_or(false);
    let self_source_is_on_stage = ctx.area_idx >= 0 && ctx.area_idx < 3;
    let filter_attr = filter_attr_from_params(frame_data.params)
        .unwrap_or(frame_data.raw_attr.max(frame_data.filter.to_attr()))
        & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let fixed_slot_matches = if resolved_slot >= 0 && resolved_slot < 3 {
        let cid = state.players[p_idx].stage[resolved_slot as usize];
        cid >= 0 && state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx)
    } else {
        false
    };
    let needs_selection = is_select_member_choice || (a & 0x02) != 0 || (!fixed_slot_matches && filter_attr != 0);
    let is_choice_done = ctx.choice_index == CHOICE_DONE;
    let active_optional_prompt = state.interaction_stack.last()
        .map(|i| i.choice_type == ChoiceType::Optional)
        .unwrap_or(false);

    // Initial prompt phase
    if ctx.choice_index == -1 {
        if is_optional && ctx.v_remaining != -1 && !active_optional_prompt {
            ctx.v_remaining = -1;
        }
        if !self_source_is_on_stage && resolved_slot == 4 && !needs_selection {
            return HandlerResult::SetCond(false);
        }
        if is_optional && ctx.v_remaining == -1 {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot as i32, ChoiceType::Optional, filter_attr, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        }
        if needs_selection {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot as i32, ChoiceType::TapMSelect, filter_attr, frame_data.value as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        }
        if is_optional || (a & 0x01) != 0 {
            if (a & 0x03) == 0 && resolved_slot < 3 {
                state.players[p_idx].set_tapped(resolved_slot as usize, true);
                return HandlerResult::SetCond(true);
            }
        } else if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
            return HandlerResult::SetCond(true);
        }
        return HandlerResult::Continue;
    }

    // Post-choice phase
    if is_optional && ctx.v_remaining != -1 && !active_optional_prompt {
        ctx.v_remaining = -1;
    }
    if !self_source_is_on_stage && resolved_slot == 4 && !needs_selection {
        return HandlerResult::SetCond(false);
    }
    if is_optional && !needs_selection && ctx.v_remaining == -1 {
        return HandlerResult::SetCond(false);
    }

    if is_optional || (a & 0x01) != 0 {
        if is_optional && ctx.v_remaining == -1 {
            if is_choice_done || ctx.choice_index == 1 {
                return HandlerResult::SetCond(false);
            }
            if ctx.choice_index == 0 {
                ctx.choice_index = -1;
                if needs_selection {
                    ctx.v_remaining = frame_data.value as i16;
                    if matches!(
                        suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot as i32, ChoiceType::TapMSelect, filter_attr, frame_data.value as i16),
                        HandlerResult::Suspend
                    ) {
                        return HandlerResult::Suspend;
                    }
                    return HandlerResult::Continue;
                }
                if resolved_slot < 3 {
                    state.players[p_idx].set_tapped(resolved_slot as usize, true);
                }
                return HandlerResult::Continue;
            }
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, resolved_slot as i32, ChoiceType::Optional, filter_attr, -1),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        }
        if is_optional && ctx.v_remaining != -1 && ctx.choice_index >= 0 && ctx.choice_index < 3 {
            state.players[p_idx].set_tapped(ctx.choice_index as usize, true);
            return HandlerResult::SetCond(true);
        }
        if is_choice_done || (ctx.v_remaining == -1 && ctx.choice_index == 1) {
            return HandlerResult::SetCond(false);
        }
        if needs_selection && ctx.choice_index == -1 {
            if matches!(
                suspend_choice(state, db, ctx, ctx, frame_idx, O_TAP_MEMBER, 0, ChoiceType::TapMSelect, filter_attr, frame_data.value as i16),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    }

    if resolved_slot < 3 {
        state.players[p_idx].set_tapped(resolved_slot as usize, true);
    }
    HandlerResult::SetCond(true)
}
