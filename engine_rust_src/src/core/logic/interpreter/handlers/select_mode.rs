use super::HandlerResult;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::enums::ChoiceType;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::instruction::BytecodeInstruction;

#[allow(clippy::too_many_arguments)]
pub fn handle_select_mode(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    bc: &[i32],
) -> HandlerResult {
    let v = instr.v;
    if ctx.choice_index == -1 {
        // nit: Auto-pick shortcut for single-option mandatory choices (e.g. Q55 discard)
        if ctx.auto_pick && v == 1 {
            ctx.choice_index = 0;
            // fall through to choice resolution below
            } else {
                let slot = instr.slot();
                let is_opponent = slot.is_opponent || slot.target_slot == 2;
                let choice_type = if is_opponent {
                    ChoiceType::OpponentChoose
                } else {
                    ChoiceType::SelectMode
                };

                let mut flip_ctx = ctx.clone();
                if is_opponent {
                    flip_ctx.player_id = 1 - (ctx.player_id as u8);
                }

                let suspended = suspend_choice(
                    state,
                    db,
                    ctx,
                    if is_opponent { &flip_ctx } else { ctx },
                    instr_ip,
                    crate::core::enums::O_SELECT_MODE,
                    0,
                    choice_type,
                    0,
                    v as i16,
                );

                if matches!(suspended, HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            return HandlerResult::Branch(instr_ip + 5);
        }
    }

    let choice = ctx.choice_index as usize;
    if choice >= v as usize {
        ctx.choice_index = -1;
        return HandlerResult::Branch(instr_ip + 5 + ((v as usize).saturating_sub(1)) * 5);
    }

    let jump_instr_offset = instr_ip + 5 + (choice * 5);
    let target = jump_instr_offset as i32 + 5 + (bc[jump_instr_offset + 1] * 5);

    ctx.choice_index = -1;
    HandlerResult::Branch(target as usize)
}
