use crate::core::enums::*;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, Zone};

use super::super::super::HandlerResult;

#[allow(clippy::too_many_arguments)]
pub fn handle_selected_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
    target_player_idx: usize,
    source_zone: Zone,
    count: i32,
    is_optional: bool,
    filter_attr: u64,
    _v: i32,
    s: i32,
    choice_type: ChoiceType,
    next_ctx: &mut AbilityContext,
    moved_cards: &mut Vec<i32>,
) -> HandlerResult {
    super::movement_discard_resume::handle_discard_resume(
        state,
        db,
        ctx,
        instr,
        instr_ip,
        target_player_idx,
        source_zone,
        count,
        is_optional,
        filter_attr,
        s,
        choice_type,
        next_ctx,
        moved_cards,
    )
}
