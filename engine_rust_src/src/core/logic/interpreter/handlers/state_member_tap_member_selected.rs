use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[allow(clippy::too_many_arguments)]
pub fn handle_tap_member_selected(
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
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::Optional,
                a as u64,
                -1,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
        if is_optional && (a & 0x02) != 0 && ctx.v_remaining == -1 {
            if is_choice_done || ctx.choice_index == 1 {
                return HandlerResult::SetCond(false);
            }
            if ctx.choice_index == 0 {
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    O_TAP_MEMBER,
                    0,
                    ChoiceType::TapMSelect,
                    a as u64,
                    instr.v as i16,
                ), HandlerResult::Suspend) {
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
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::Optional,
                a as u64,
                -1,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        }

        if is_choice_done || ctx.choice_index == 1 {
            return HandlerResult::SetCond(false);
        }

        if resolved_slot == 4 && (a & 0x02) == 0 {
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                0,
                ChoiceType::TapMSelect,
                (a | 0x02) as u64,
                instr.v as i16,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }

        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    } else {
        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    }
}
