use crate::core::enums::ChoiceType;
use crate::core::enums::Zone;
use crate::core::logic::constants::{CHOICE_DONE, CHOICE_NO, CHOICE_YES};
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::O_SELECT_CARDS;

#[path = "interaction_select_cards_resolve.rs"]
mod interaction_select_cards_resolve;

const VARIABLE_SELECT_CARDS_OPTIONAL_PROMPT: i16 = -32000;

fn resolved_select_cards_zone(slot_info: crate::core::logic::interpreter::instruction::DecodedSlot) -> u8 {
    let source_zone = slot_info.source_zone as u8;
    if source_zone != 0 {
        return source_zone;
    }

    match slot_info.target_slot as u8 {
        zone if zone == Zone::Hand as u8 => Zone::Hand as u8,
        zone if zone == Zone::Discard as u8 => Zone::Discard as u8,
        zone if zone == Zone::Deck as u8 => Zone::Deck as u8,
        zone if zone == Zone::Yell as u8 => Zone::Yell as u8,
        _ => Zone::Discard as u8,
    }
}

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
    let filter = frame_data
        .params
        .and_then(CardFilter::from_json_value)
        .map(|extra_filter| frame_data.filter.with_overlay(&extra_filter))
        .unwrap_or(frame_data.filter);
    let a = filter.to_attr() as i64;
    let s = frame_data.slot.to_raw();
    let p_idx = ctx.player_id as usize;
    let is_optional = filter.is_optional;
    let optional_prompt_marker = -((v as i16) + 2);
    let is_variable_selection = v < 0;

    let slot_info = frame_data.slot;
    let effective_zone = resolved_select_cards_zone(slot_info);

    if is_optional
        && is_variable_selection
        && ctx.choice_index == -1
        && ctx.v_remaining == -1
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

        for cid in cards_to_filter {
            let matches = state.card_matches_filter_with_ctx(db, cid, a as u64, ctx);
            if matches {
                state.players[p_idx].looked_cards.push(cid);
            }
        }

        if state.players[p_idx].looked_cards.is_empty() && !is_optional {
            return HandlerResult::Continue;
        }

        let choice_type = match effective_zone {
            6 => ChoiceType::SelectHandDiscard,
            7 => ChoiceType::SelectDiscardPlay,
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
