use crate::core::enums::ChoiceType;
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

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    instr_ip: usize,
) -> HandlerResult {
    if state.debug.debug_mode {
        eprintln!(
            "[SELECT_CARDS_ENTRY] ip={} choice_index={} v_remaining={} trigger={:?} source_card_id={} ability_card_id={} frame_value={} frame_slot={:?} frame_filter={:#x}",
            instr_ip,
            ctx.choice_index,
            ctx.v_remaining,
            ctx.trigger_type,
            ctx.source_card_id,
            ctx.ability_card_id,
            frame_data.value,
            frame_data.slot,
            frame_data.resolved_filter_attr()
        );
    }
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
    let spec = frame_data.semantic_select_cards_spec();

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
            let p_idx = state.current_player as usize;
            if let Some(execution_id) = state.ui.current_execution_id {
                state.ui.cancelled_execution_ids.insert(execution_id);
            }
            state.players[p_idx].looked_cards.clear();
            finish_pending_interaction(state);
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
            let p_idx = state.current_player as usize;
            if let Some(execution_id) = state.ui.current_execution_id {
                state.ui.cancelled_execution_ids.insert(execution_id);
            }
            state.players[p_idx].looked_cards.clear();
            finish_pending_interaction(state);
            return HandlerResult::Continue;
        }

        if ctx.choice_index == CHOICE_NO {
            ctx.choice_index = -1;
            ctx.v_remaining = v as i16;
        }
    }

    if ctx.choice_index == -1 {
        state.players[p_idx].looked_cards.clear();
        let cards_to_filter = match spec.source_zone {
            crate::core::enums::Zone::Hand => state.players[p_idx].hand.to_vec(),
            crate::core::enums::Zone::Discard => state.players[p_idx].discard.to_vec(),
            crate::core::enums::Zone::Deck => state.players[p_idx].deck.to_vec(),
            crate::core::enums::Zone::Yell => state.players[p_idx].yell_cards.to_vec(),
            crate::core::enums::Zone::Stage => state.players[p_idx]
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
        if state.debug.debug_mode {
            eprintln!(
                "[SELECT_CARDS_DBG] opcode={} choice_type={:?} source_zone={:?} looked_cards={:?} optional={} variable={} v={} filter_attr={:#x}",
                frame_data.opcode,
                spec.choice_type(),
                spec.source_zone,
                state.players[p_idx].looked_cards,
                is_optional,
                is_variable_selection,
                v,
                a as u64
            );
        }

        if state.players[p_idx].looked_cards.is_empty() && !is_optional {
            return HandlerResult::Continue;
        }

        let suspended = suspend_choice(
                state,
                db,
                ctx,
                ctx,
                instr_ip,
                O_SELECT_CARDS,
                0,
                spec.choice_type(),
                a as u64,
                if ctx.v_remaining >= 0 {
                    ctx.v_remaining
                } else {
                    v as i16
                },
            );
        if state.debug.debug_mode {
            eprintln!(
                "[SELECT_CARDS_DBG] suspend_result={:?} phase_after={:?} cp_after={} looked_cards_after={:?}",
                suspended,
                state.phase,
                state.current_player,
                state.players[p_idx].looked_cards
            );
        }
        if matches!(suspended, HandlerResult::Suspend) {
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
        spec.source_zone as u8,
        is_optional,
    )
}
