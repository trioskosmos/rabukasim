use super::*;
#[path = "state_member_tap_member_selected.rs"]
mod state_member_tap_member_selected;
#[path = "state_member_tap_member_prompt.rs"]
mod state_member_tap_member_prompt;

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
    if ctx.choice_index == -1 {
        return state_member_tap_member_prompt::handle_tap_member_prompt(
            state,
            db,
            ctx,
            instr,
            instr_ip,
            p_idx,
            a,
            resolved_slot,
        );
    } else {
        return state_member_tap_member_selected::handle_tap_member_selected(
            state,
            db,
            ctx,
            instr,
            instr_ip,
            p_idx,
            a,
            resolved_slot,
        );
    }
}
