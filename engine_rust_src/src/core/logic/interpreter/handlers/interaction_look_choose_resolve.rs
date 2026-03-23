use crate::core::logic::models::AbilityFrame;
use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use super::interaction_look_choose_apply::apply_look_choice;
use super::interaction_look_choose_finalize::finalize_look_choice;

#[allow(clippy::too_many_arguments)]
pub fn resolve_look_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: u8,
    rem_dest: u8,
    source_zone: i32,
    reveal_flag: bool,
    dest_discard_v: bool,
    a: i64,
    s: i32,
) -> HandlerResult {
    let choice = ctx.choice_index as i32;
    let mut revealed = std::mem::take(&mut state.players[p_idx].looked_cards);
    if choice == CHOICE_DONE as i32 {
        state.players[p_idx].looked_cards.retain(|c| *c != -1);
        return HandlerResult::Continue;
    }

    if choice != CHOICE_DONE as i32 {
        if choice >= 0 && (choice as usize) < revealed.len() && choice != CHOICE_ALL as i32 {
            let chosen = revealed[choice as usize];
            if chosen != -1 {
                revealed[choice as usize] = -1;
                apply_look_choice(
                    state,
                    db,
                    ctx,
                    p_idx,
                    slot_info,
                    target_slot,
                    source_zone,
                    reveal_flag,
                    chosen,
                );

                let rem = if ctx.v_remaining > 0 { ctx.v_remaining - 1 } else { 0 };
                if rem > 0 && revealed.iter().any(|&c| c != -1) {
                    state.players[p_idx].looked_cards = revealed.clone();
                    let choice_type = if source_zone == 6 {
                        ChoiceType::SelectHandDiscard
                    } else if source_zone == 7 {
                        ChoiceType::SelectDiscardPlay
                    } else {
                        ChoiceType::LookAndChoose
                    };
                    if matches!(suspend_choice(
                        state,
                        db,
                        ctx,
                        ctx,
                        frame_idx,
                        O_LOOK_AND_CHOOSE,
                        s,
                        choice_type,
                        a as u64,
                        rem,
                    ), HandlerResult::Suspend) {
                        return HandlerResult::Suspend;
                    }
                }
            }
        }
    }
    finalize_look_choice(
        state,
        db,
        ctx,
        p_idx,
        slot_info,
        target_slot,
        rem_dest,
        source_zone,
        reveal_flag,
        dest_discard_v,
        a,
        s,
        &mut revealed,
    )
}
