use crate::core::enums::*;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};

use crate::core::logic::interpreter::handlers::state_helpers::tap_opponent_chooser_player;
use crate::core::logic::interpreter::handlers::HandlerResult;
#[path = "state_member_activate.rs"]
mod state_member_activate;
#[path = "state_member_tap_member.rs"]
mod state_member_tap_member;
pub use state_member_activate::handle_activate_member;
pub use state_member_tap_member::handle_tap_member;

pub fn handle_set_tapped(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    resolved_slot: i32,
) -> HandlerResult {
    let frame_data = frame.components();
    let is_optional = frame_data.filter.is_optional;

    if !state.ui.silent {
        eprintln!(
            "[TRACE] SET_TAPPED: p_idx={}, resolved_slot={}, v={}, optional={}, choice_index={}, v_remaining={}",
            p_idx,
            resolved_slot,
            frame_data.value,
            is_optional,
            ctx.choice_index,
            ctx.v_remaining,
        );
    }

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
                O_SET_TAPPED,
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
        state.players[p_idx].set_tapped(slot, should_tap);
    }

    HandlerResult::Continue
}

pub fn handle_tap_opponent(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _instr: &AbilityFrame,
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
        if !state.ui.silent && state.debug.debug_mode {
            println!("[DEBUG] O_TAP_OPPONENT: Suspending for opponent.");
        }
        let mut choice_ctx = ctx.clone();
        choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);
        let suspended = suspend_choice(
            state,
            db,
            &choice_ctx,
            &choice_ctx,
            frame_idx,
            O_TAP_OPPONENT,
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
                    O_TAP_OPPONENT,
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
