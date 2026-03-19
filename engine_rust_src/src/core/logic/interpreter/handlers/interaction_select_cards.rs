use crate::core::enums::ChoiceType;
use crate::core::logic::constants::{CHOICE_DONE, FILTER_IS_OPTIONAL};
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::{O_SELECT_CARDS};

#[path = "interaction_select_cards_resolve.rs"]
mod interaction_select_cards_resolve;

pub fn handle_select_cards(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
    let optional_prompt_marker = -((v as i16) + 2);

    let slot_info = instr.slot();
    let source_zone = slot_info.source_zone as u8;
    let ts = slot_info.target_slot;
    let effective_zone = if source_zone != 0 {
        source_zone
    } else if ts != 0 {
        ts
    } else {
        7
    };

    if is_optional && v == 99 && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(suspend_choice(
            state,
            db,
            ctx,
            ctx,
            instr_ip,
            O_SELECT_CARDS,
            0,
            ChoiceType::Optional,
            a as u64,
            optional_prompt_marker,
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && v == 99 && ctx.v_remaining == optional_prompt_marker {
        if ctx.choice_index == 1 || ctx.choice_index == CHOICE_DONE {
            if let Some(execution_id) = state.ui.current_execution_id {
                state.ui.cancelled_execution_ids.insert(execution_id);
            }
            return HandlerResult::Continue;
        }

        if ctx.choice_index == 0 {
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

        let filter_attr = a as u64;
        for cid in cards_to_filter {
            if state.card_matches_filter_with_ctx(db, cid, filter_attr, ctx) {
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
        if matches!(suspend_choice(
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
        ), HandlerResult::Suspend) {
            return HandlerResult::Suspend;
        }
    }

    interaction_select_cards_resolve::resolve_select_cards(
        state,
        db,
        ctx,
        instr,
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
