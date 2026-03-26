use super::movement_discard_helpers::{
    pop_card_from_zone, resolve_source_zone, zone_available_count, zone_card_count,
};
use crate::core::enums::*;
use crate::core::logic::constants::FILTER_IS_OPTIONAL;
use crate::core::logic::constants::FILTER_MASK_LOWER;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::handlers::state_helpers::source_ability;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState};
#[path = "movement_discard_prompt.rs"]
mod movement_discard_prompt;
#[path = "movement_discard_resume.rs"]
mod movement_discard_resume;
#[path = "movement_discard_select.rs"]
mod movement_discard_select;
use super::super::HandlerResult;
pub fn handle_move_to_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
) -> HandlerResult {
    let frame_data = frame.components();
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let v = if frame_data.filter.compare_accumulated {
        resolve_count(
            state,
            db,
            s,
            frame_data.raw_attr & FILTER_MASK_LOWER,
            p_idx as i32,
            ctx,
            0,
        ) as i32
    } else {
        frame_data.value
    };
    let base_p = ctx.activator_id as usize;
    let slot = frame_data.slot;
    let mut source_zone = resolve_source_zone(&slot);
    let target_player_idx = if slot.is_opponent { 1 - base_p } else { base_p };

    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = zone_card_count(state, target_player_idx, source_zone);
        (current_size - target_size).max(0)
    } else {
        v
    };
    if source_zone == Zone::Stage
        && frame_data
            .params
            .as_ref()
            .and_then(|params| params.get("operation").or_else(|| params.get("OPERATION")))
            .and_then(|value| value.as_str())
            .map(|value| value.eq_ignore_ascii_case("UNTIL_SIZE"))
            .unwrap_or(false)
    {
        source_zone = Zone::Hand;
    }
    if target_player_idx != p_idx
        && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY)
    {
        return HandlerResult::Continue;
    }

    let filter_attr = (a as u64) & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let is_optional = frame_data.filter.is_optional || (a as u64 & FILTER_IS_OPTIONAL) != 0;

    if state.debug.debug_mode {
        println!(
            "[DEBUG_MOV] h_m_t_d: cid={}, choice={}, optional={}, attr={:x}",
            ctx.source_card_id, ctx.choice_index, is_optional, a as u64
        );
    }

    let mut next_ctx = ctx.clone();
    let choice_type = if source_zone == Zone::Hand {
        ChoiceType::SelectHandDiscard
    } else {
        ChoiceType::SelectDiscard
    };
    let available_count = zone_available_count(state, target_player_idx, source_zone);
    if movement_discard_prompt::prepare_discard_prompt(
        state,
        db,
        ctx,
        frame,
        frame_idx,
        p_idx,
        source_zone,
        count,
        is_optional,
        filter_attr,
        v,
        s,
        choice_type,
        available_count,
        target_player_idx,
        &mut next_ctx,
    ) {
        return HandlerResult::Suspend;
    }

    if is_optional
        && matches!(
            source_zone,
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
        )
        && next_ctx.choice_index == 0
    {
        next_ctx.choice_index = -1;
    }

    let mut moved_cards = Vec::new();

    if next_ctx.choice_index != -1 {
        let selected_result = movement_discard_select::handle_selected_discard(
            state,
            db,
            ctx,
            frame,
            frame_idx,
            target_player_idx,
            source_zone,
            count,
            is_optional,
            filter_attr,
            v,
            s,
            choice_type,
            &mut next_ctx,
            &mut moved_cards,
        );
        if !matches!(selected_result, HandlerResult::Continue) {
            return selected_result;
        }
    } else {
        for _ in 0..count {
            if let Some(cid) = pop_card_from_zone(
                state,
                target_player_idx,
                source_zone,
                next_ctx.area_idx as i32,
                db,
                &next_ctx,
            ) {
                state.players[target_player_idx].push_discard_card(cid);
                moved_cards.push(cid);
                next_ctx.selected_cards.push(cid);
            }
        }
    }

    if next_ctx.selected_cards.is_empty() && !moved_cards.is_empty() {
        next_ctx.selected_cards.extend(moved_cards.iter().copied());
    }

    // Preserve the moved-card batch on the current execution context so
    // subsequent DISCARDED_CARDS conditions in the same ability can see it.
    if !next_ctx.selected_cards.is_empty() {
        ctx.selected_cards = next_ctx.selected_cards.clone();
    }

    if moved_cards.iter().any(|&cid| db.get_live(cid).is_some())
        && ctx.area_idx >= 0
        && ctx.area_idx < 3
        && source_ability(db, ctx)
            .map(|ability| {
                ability.effects.iter().any(|effect| {
                    effect.runtime_opcode == O_NOP
                        && effect
                            .params
                            .get("raw_effect")
                            .and_then(|value| value.as_str())
                            == Some("TAP_SELF")
                })
            })
            .unwrap_or(false)
    {
        state.players[p_idx].set_tapped(ctx.area_idx as usize, true);
    }

    // BATCH CONTEXT PRESERVATION: Use accumulated selected_cards from context, not local moved_cards
    // This ensures all cards accumulated across recursive calls are in the trigger batch
    if !next_ctx.selected_cards.is_empty() {
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &next_ctx.selected_cards);
    } else if !moved_cards.is_empty() {
        // Fallback for non-recursive (multi-pop) case
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &moved_cards);
    }

    if !state.ui.silent {
        if let Some(msg) = logging::get_opcode_log(O_MOVE_TO_DISCARD, v, a, s, 0) {
            state.log(msg);
        }
    }

    state.players[target_player_idx].hand.retain(|c| *c != -1);
    HandlerResult::Continue
}
