use crate::core::enums::ChoiceType;
use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO, CHOICE_YES, FILTER_IS_OPTIONAL};
use crate::core::logic::filter::filter_attr_from_params;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::O_SELECT_CARDS;

#[path = "interaction_select_cards_resolve.rs"]
mod interaction_select_cards_resolve;

const VARIABLE_SELECT_CARDS_OPTIONAL_PROMPT: i16 = -32000;

fn cancel_optional_selection(state: &mut GameState) {
    let p_idx = state.current_player as usize;
    if let Some(execution_id) = state.ui.current_execution_id {
        state.ui.cancelled_execution_ids.insert(execution_id);
    }
    state.players[p_idx].looked_cards.clear();
    finish_pending_interaction(state);
}

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    instr_ip: usize,
) -> HandlerResult {
    let v = frame_data.value;
    let mut a = filter_attr_from_params(frame_data.params).unwrap_or(0) as i64;
    a |= frame_data.filter.to_attr() as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
    let optional_prompt_marker = -((v as i16) + 2);
    let is_variable_selection = v < 0;

    let slot_info = frame_data.slot;
    let source_zone = slot_info.source_zone as u8;
    let ts = slot_info.target_slot;
    let effective_zone = if source_zone != 0 {
        source_zone
    } else if ts != 0 {
        ts
    } else {
        7
    };
    let effective_zone = if ctx.source_card_id == 537 { 7 } else { effective_zone };

    let is_victorious_road = ctx.source_card_id == 10;

    if is_optional
        && is_variable_selection
        && ctx.choice_index == -1
        && ctx.v_remaining == -1
        && !is_victorious_road
    {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                0,
                ChoiceType::SelectCards,
                a as u64,
                VARIABLE_SELECT_CARDS_OPTIONAL_PROMPT,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional
        && is_variable_selection
        && ctx.v_remaining == VARIABLE_SELECT_CARDS_OPTIONAL_PROMPT
    {
        if ctx.choice_index == CHOICE_YES || ctx.choice_index == CHOICE_DONE {
            cancel_optional_selection(state);
            return HandlerResult::Continue;
        }

        if ctx.choice_index == CHOICE_NO {
            ctx.choice_index = -1;
            ctx.v_remaining = 0;
        }
    }

    if is_optional && v == 99 && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                0,
                ChoiceType::SelectCards,
                a as u64,
                optional_prompt_marker,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && v == 99 && ctx.v_remaining == optional_prompt_marker {
        if ctx.choice_index == CHOICE_YES || ctx.choice_index == CHOICE_DONE {
            cancel_optional_selection(state);
            return HandlerResult::Continue;
        }

        if ctx.choice_index == CHOICE_NO {
            ctx.choice_index = -1;
            ctx.v_remaining = v as i16;
        }
    }

    if ctx.choice_index == -1 {
        state.players[p_idx].looked_cards.clear();
        let cards_to_filter = match effective_zone {
            6 => state.players[p_idx].hand.to_vec(),
            7 => state.players[p_idx].discard.to_vec(),
            4 => state.players[p_idx]
                .stage
                .iter()
                .cloned()
                .filter(|&c| c >= 0)
                .collect(),
            _ => state.players[p_idx].discard.to_vec(),
        };

        // Debug: Print filtering info for card 537
        if ctx.source_card_id == 537 {
            println!("DEBUG: Card 537 filtering from zone {}: cards={:?}", effective_zone, cards_to_filter);
            println!("DEBUG: filter_attr = 0x{:x}", a as u64);
        }

        let filter_attr = a as u64;
        for cid in cards_to_filter {
            let matches = state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx);
            if ctx.source_card_id == 537 {
                println!("DEBUG: Card {} matches filter: {}", cid, matches);
            }
            if matches {
                state.players[p_idx].looked_cards.push(cid);
            }
        }

        if ctx.source_card_id == 537 {
            println!("DEBUG: Final looked_cards: {:?}", state.players[p_idx].looked_cards);
        }

        if state.players[p_idx].looked_cards.is_empty() && !is_optional {
            return HandlerResult::Continue;
        }

        if is_victorious_road && is_optional && is_variable_selection {
            ctx.choice_index = 0;
            return interaction_select_cards_resolve::resolve_select_cards(
                state,
                db,
                ctx,
                frame_data,
                instr_ip,
                p_idx,
                s,
                v,
                a,
                slot_info,
                effective_zone,
                is_optional,
            );
        }

        let choice_type = match effective_zone {
            6 => ChoiceType::SelectHandDiscard,
            7 => ChoiceType::SelectDiscardPlay,
            _ if ctx.source_card_id == 537 => ChoiceType::SelectDiscardPlay,
            _ => ChoiceType::LookAndChoose,
        };
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                0,
                choice_type,
                a as u64,
                if ctx.v_remaining >= 0 {
                    ctx.v_remaining
                } else {
                    v as i16
                },
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    interaction_select_cards_resolve::resolve_select_cards(
        state,
        db,
        ctx,
        frame_data,
        instr_ip,
        p_idx,
        s,
        v,
        a,
        slot_info,
        effective_zone,
        is_optional,
    )
}
