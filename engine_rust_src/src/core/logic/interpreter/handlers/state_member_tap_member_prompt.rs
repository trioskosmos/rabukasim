use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;

#[allow(clippy::too_many_arguments)]
pub fn handle_tap_member_prompt(
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

    if is_optional || (a & 0x01) != 0 {
        if (a & 0x02) != 0 {
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_TAP_MEMBER,
                resolved_slot as i32,
                ChoiceType::TapMSelect,
                a as u64,
                instr.v as i16,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }

        if (a & 0x03) == 0 && resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
    } else {
        if resolved_slot < 3 {
            state.players[p_idx].set_tapped(resolved_slot as usize, true);
        }
        return HandlerResult::SetCond(true);
    }

    HandlerResult::Continue
}
