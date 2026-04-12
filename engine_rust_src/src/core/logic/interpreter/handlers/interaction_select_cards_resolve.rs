use super::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    place_card_at_destination, remove_card_from_zone, target_slot_destination,
};
use crate::core::logic::interpreter::suspension::finish_pending_interaction;

#[allow(clippy::too_many_arguments)]
pub fn resolve_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &crate::core::logic::models::AbilityFrameComponents<'_>,
    frame_idx: usize,
    p_idx: usize,
    s: i32,
    v: i32,
    a: i64,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    _effective_zone: u8,
    _is_optional: bool,
) -> HandlerResult {
    let spec = frame_data.semantic_select_cards_spec();
    let choice = ctx.choice_index as i32;
    if choice == CHOICE_DONE as i32 {
        return HandlerResult::Continue;
    }

    let choice_type = spec.choice_type();
    let is_variable_selection = v < 0;

    if choice != CHOICE_DONE as i32
        && choice >= 0
        && (choice as usize) < state.players[p_idx].looked_cards.len()
    {
        let chosen = state.players[p_idx].looked_cards[choice as usize];
        ctx.selected_cards.push(chosen);

        let dest_zone = slot_info.dest_zone as u8;
        if dest_zone == 0 && !state.players[p_idx].revealed_cards.contains(&chosen) {
            state.players[p_idx].revealed_cards.push(chosen);
        }
        if dest_zone != 0 {
            let actual_source = spec.source_zone;
            let found = remove_card_from_zone(state, db, ctx, p_idx, actual_source, chosen);

            if found {
                if dest_zone == 4 {
                    let slot = choice as usize;
                    let play_card = ctx.selected_cards.last().copied().unwrap_or(chosen);
                    if slot < 3 && play_card >= 0 {
                        place_card_at_destination(
                            state,
                            db,
                            ctx,
                            p_idx,
                            play_card,
                            target_slot_destination(dest_zone),
                            Some(slot),
                            slot_info.is_wait,
                            false,
                            spec.source_zone,
                        );
                        finish_pending_interaction(state);
                    } else {
                        place_card_at_destination(
                            state,
                            db,
                            ctx,
                            p_idx,
                            play_card,
                            target_slot_destination(dest_zone),
                            None,
                            slot_info.is_wait,
                            false,
                            spec.source_zone,
                        );
                    }
                } else {
                    place_card_at_destination(
                        state,
                        db,
                        ctx,
                        p_idx,
                        chosen,
                        target_slot_destination(dest_zone),
                        None,
                        slot_info.is_wait,
                        false,
                        spec.source_zone,
                    );
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
                if matches!(
                    suspend_choice(
                        state,
                        db,
                        ctx,
                        ctx,
                        frame_idx,
                        O_SELECT_CARDS,
                        s,
                        choice_type,
                        a as u64,
                        0,
                    ),
                    HandlerResult::Suspend
                ) {
                    return HandlerResult::Suspend;
                }
            }
        } else if rem > 0 {
            state.players[p_idx].looked_cards.remove(choice as usize);
            ctx.v_remaining = rem;
            ctx.choice_index = -1;
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_SELECT_CARDS,
                    s,
                    choice_type,
                    a as u64,
                    rem,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else {
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
            finish_pending_interaction(state);
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
