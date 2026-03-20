use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::enums::Zone;
use crate::core::logic::interpreter::handlers::interaction_zone::remove_card_from_zone;

#[allow(clippy::too_many_arguments)]
pub fn resolve_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _instr: &BytecodeInstruction,
    instr_ip: usize,
    p_idx: usize,
    s: i32,
    v: i32,
    a: i64,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    effective_zone: u8,
    is_optional: bool,
) -> HandlerResult {
    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 {
        return HandlerResult::Continue;
    }

    let choice_type = match effective_zone {
        6 => ChoiceType::SelectHandDiscard,
        7 => ChoiceType::SelectDiscardPlay,
        _ => ChoiceType::LookAndChoose,
    };
    let is_variable_selection = v < 0;

    if choice != CHOICE_DONE as i32
        && choice >= 0
        && (choice as usize) < state.players[p_idx].looked_cards.len()
    {
        let chosen = state.players[p_idx].looked_cards[choice as usize];
        ctx.selected_cards.push(chosen);

        let dest_zone = slot_info.dest_zone as u8;
        if dest_zone != 0 {
            let source_zone = slot_info.source_zone as u8;
            let actual_source = if source_zone != 0 { source_zone } else { 7 };

            let actual_source = match actual_source {
                4 => Zone::Stage,
                6 => Zone::Hand,
                7 => Zone::Discard,
                8 => Zone::Deck,
                15 => Zone::Yell,
                _ => Zone::Discard,
            };
            let found = remove_card_from_zone(state, db, ctx, p_idx, actual_source, chosen);

            if found {
                match dest_zone {
                    6 => state.players[p_idx].gain_hand_card(chosen),
                    7 => state.players[p_idx].push_discard_card(chosen),
                    8 | 0 => state.players[p_idx].push_deck_card(chosen),
                    13 => state.players[p_idx].success_lives.push(chosen),
                    _ => state.players[p_idx].push_hand_card(chosen),
                }
            }
        }

        let rem = if ctx.v_remaining > 0 {
            ctx.v_remaining - 1
        } else {
            (v as i16).saturating_sub(1)
        };
        if is_variable_selection {
            state.players[p_idx].looked_cards.remove(choice as usize);
            ctx.choice_index = -1;
            ctx.v_remaining = 0;
            if !state.players[p_idx].looked_cards.is_empty() {
                if matches!(suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    instr_ip,
                    O_SELECT_CARDS,
                    s,
                    choice_type,
                    a as u64,
                    0,
                ), HandlerResult::Suspend) {
                    return HandlerResult::Suspend;
                }
            }
        } else if rem > 0 {
            state.players[p_idx].looked_cards.remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            if matches!(suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                s,
                choice_type,
                a as u64,
                rem,
            ), HandlerResult::Suspend) {
                return HandlerResult::Suspend;
            }
        }
    }

    if state.players[p_idx].looked_cards.is_empty() {
        return HandlerResult::Continue;
    }

    let choice = ctx.choice_index as i32;
    if choice == 99 {
        let looked = std::mem::take(&mut state.players[p_idx].looked_cards);
        for &cid in looked.iter() {
            state.players[p_idx].push_deck_card(cid);
        }
    }

    HandlerResult::Continue
}
