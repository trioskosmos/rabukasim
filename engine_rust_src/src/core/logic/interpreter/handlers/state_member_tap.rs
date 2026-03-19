use crate::core::enums::*;
use crate::core::logic::constants::CHOICE_DONE;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::get_choice_text;
use crate::core::models::suspend_interaction;

use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::handlers::state_helpers::tap_opponent_chooser_player;

pub fn handle_tap_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction,
    instr_ip: usize,
    p_idx: usize,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let is_optional = instr.filter_attr().is_optional;

    if ctx.choice_index == -1 {
        if is_optional || (a & 0x01) != 0 {
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::Optional,
                &choice_text,
                instr.filter_attr().to_attr(),
                -1,
            ) {
                return HandlerResult::Suspend;
            }
        }
        if (a & 0x02) != 0 {
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::TapMSelect,
                &choice_text,
                a as u64,
                instr.v as i16,
            ) {
                return HandlerResult::Suspend;
            }
        }

        if (a & 0x03) == 0 && resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
    } else {
        let is_choice_done = ctx.choice_index == CHOICE_DONE;
        let stale_select_member_choice = is_optional
            && ctx.v_remaining == -1
            && ctx.choice_index >= 0
            && ctx.choice_index < 3
            && ctx
                .selected_cards
                .last()
                .copied()
                .map(|selected_cid| {
                    state.players[p_idx]
                        .stage
                        .get(ctx.choice_index as usize)
                        .copied()
                        .unwrap_or(-1)
                        == selected_cid
                })
                .unwrap_or(false);

        if is_optional || (a & 0x01) != 0 {
            if stale_select_member_choice {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_TAP_MEMBER,
                    resolved_slot as i32,
                    ChoiceType::Optional,
                    &choice_text,
                    a as u64,
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
            }
            if is_optional && (a & 0x02) != 0 && ctx.v_remaining == -1 {
                if is_choice_done || ctx.choice_index == 1 {
                    return HandlerResult::SetCond(false);
                }
                if ctx.choice_index == 0 {
                    let choice_text = get_choice_text(db, ctx);
                    if suspend_interaction(
                        state,
                        db,
                        ctx,
                        instr_ip,
                        O_TAP_MEMBER,
                        0,
                        ChoiceType::TapMSelect,
                        &choice_text,
                        a as u64,
                        instr.v as i16,
                    ) {
                        return HandlerResult::Suspend;
                    }
                }
            }

            if is_optional && (a & 0x02) == 0 && ctx.v_remaining != -1 {
                if ctx.choice_index >= 0 && ctx.choice_index < 3 {
                    state.players[p_idx].set_tapped(ctx.choice_index as usize, true);
                    return HandlerResult::SetCond(true);
                }
            }

            if ctx.choice_index != 0 && ctx.choice_index != 1 && !is_choice_done {
                if state.debug.debug_mode && !state.ui.silent {
                    println!(
                        "[DEBUG] TAP_MEMBER: Ignoring choice {} for Optional prompt",
                        ctx.choice_index
                    );
                }
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_TAP_MEMBER,
                    resolved_slot as i32,
                    ChoiceType::Optional,
                    "",
                    a as u64,
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
                return HandlerResult::Continue;
            }

            if is_choice_done || ctx.choice_index == 1 {
                return HandlerResult::SetCond(false);
            }

            if resolved_slot == 4 && (a & 0x02) == 0 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_TAP_MEMBER,
                    0,
                    ChoiceType::TapMSelect,
                    &choice_text,
                    (a | 0x02) as u64,
                    instr.v as i16,
                ) {
                    return HandlerResult::Suspend;
                }
            }

            if resolved_slot < 3 {
                state.players[p_idx].set_tapped(resolved_slot as usize, true);
            }
            return HandlerResult::SetCond(true);
        } else {
            let _slot = ctx.choice_index as usize;
            if resolved_slot < 3 {
                state.players[p_idx].set_tapped(resolved_slot as usize, true);
            }
            return HandlerResult::SetCond(true);
        }
    }

    HandlerResult::Continue
}

pub fn handle_tap_opponent(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction,
    instr_ip: usize,
    a: i64,
    v: i32,
) -> HandlerResult {
    let target_p_idx = 1 - (ctx.activator_id as usize);
    let count = if ctx.v_remaining == -1 { v as i16 } else { ctx.v_remaining };
    if count <= 0 {
        return HandlerResult::Continue;
    }

    if ctx.choice_index == -1 {
        let choice_text = get_choice_text(db, ctx);
        if !state.ui.silent && state.debug.debug_mode {
            println!("[DEBUG] O_TAP_OPPONENT: Suspending for opponent.");
        }
        let mut choice_ctx = ctx.clone();
        choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);
        let suspended = suspend_interaction(
            state,
            db,
            &choice_ctx,
            instr_ip,
            O_TAP_OPPONENT,
            0,
            ChoiceType::TapO,
            &choice_text,
            a as u64,
            count,
        );

        if suspended {
            return HandlerResult::Suspend;
        }
    } else {
        let slot_idx = ctx.choice_index as usize;
        if slot_idx < 3 {
            state.set_member_tapped(target_p_idx, slot_idx, true, db);
            ctx.v_remaining = count - 1;
            ctx.choice_index = -1;
            if ctx.v_remaining > 0 {
                let choice_text = get_choice_text(db, ctx);
                let mut choice_ctx = ctx.clone();
                choice_ctx.player_id = tap_opponent_chooser_player(db, ctx);
                let suspended = suspend_interaction(
                    state,
                    db,
                    &choice_ctx,
                    instr_ip,
                    O_TAP_OPPONENT,
                    0,
                    ChoiceType::TapO,
                    &choice_text,
                    a as u64,
                    ctx.v_remaining,
                );

                if suspended {
                    return HandlerResult::Suspend;
                }
            }
        }
    }

    HandlerResult::Continue
}
