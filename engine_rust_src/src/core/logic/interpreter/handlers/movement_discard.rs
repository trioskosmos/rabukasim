use super::movement_discard_helpers::{
    pop_card_from_zone, resolve_source_zone, zone_available_count, zone_card_count,
    remove_card_by_index,
};
use crate::core::enums::*;
use crate::core::logic::constants::FILTER_IS_OPTIONAL;
use crate::core::logic::constants::FILTER_MASK_LOWER;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::state_helpers::source_ability;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::suspension::finish_pending_interaction;
use crate::core::logic::models::{AbilityFrame, AbilityFrameComponents};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, Zone};
use crate::core::models::CHOICE_DONE;
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
    
    // Resolve count (handle compare_accumulated and UNTIL_SIZE)
    let v = if frame_data.filter.compare_accumulated {
        resolve_count(state, db, s, frame_data.raw_attr & FILTER_MASK_LOWER, p_idx as i32, ctx, 0) as i32
    } else {
        frame_data.value
    };
    
    let base_p = ctx.activator_id as usize;
    let slot = frame_data.slot;
    let mut source_zone = resolve_source_zone(&slot);
    let target_player_idx = if slot.is_opponent { 1 - base_p } else { base_p };

    // Handle UNTIL_SIZE operation (discard down to N cards)
    let count = if (v as u32 & (1 << 31)) != 0 {
        let target_size = v & 0x7FFFFFFF;
        let current_size = zone_card_count(state, target_player_idx, source_zone);
        (current_size - target_size).max(0)
    } else {
        v
    };
    
    // Special case: Stage UNTIL_SIZE means Hand
    if source_zone == Zone::Stage && is_until_size_op(&frame_data) {
        source_zone = Zone::Hand;
    }

    // Immunity check
    if target_player_idx != p_idx && state.players[target_player_idx].get_flag(PlayerState::FLAG_IMMUNITY) {
        return HandlerResult::Continue;
    }

    let filter_attr = (a as u64) & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK;
    let is_optional = frame_data.filter.is_optional || (a as u64 & FILTER_IS_OPTIONAL) != 0;

    // Handle skip of optional discard (CHOICE_DONE = user declined)
    if is_optional && ctx.choice_index == CHOICE_DONE {
        return HandlerResult::Return;
    }

    let mut next_ctx = ctx.clone();
    let choice_type = if source_zone == Zone::Hand { ChoiceType::SelectHandDiscard } else { ChoiceType::SelectDiscard };
    let available_count = zone_available_count(state, target_player_idx, source_zone);

    // Prompt phase: check if we need player input
    if prepare_discard_prompt(
        state, db, ctx, frame, frame_idx, p_idx, source_zone, count, is_optional,
        filter_attr, v, s, choice_type, available_count, target_player_idx, &mut next_ctx,
    ) {
        return HandlerResult::Suspend;
    }

    // Handle optional deck discard "no" choice
    if is_optional && is_deck_zone(source_zone) && next_ctx.choice_index == 0 {
        next_ctx.choice_index = -1;
    }

    // Execute the discard
    let mut moved_cards = Vec::new();

    if next_ctx.choice_index != -1 {
        let result = handle_selected_discard(
            state, db, ctx, frame, frame_idx, target_player_idx, source_zone, count,
            is_optional, filter_attr, s, choice_type, &mut next_ctx, &mut moved_cards,
        );
        if !matches!(result, HandlerResult::Continue) {
            return result;
        }
    } else {
        for _ in 0..count {
            if let Some(cid) = pop_card_from_zone(state, target_player_idx, source_zone, next_ctx.area_idx as i32, db, &next_ctx) {
                state.players[target_player_idx].push_discard_card(cid);
                moved_cards.push(cid);
                next_ctx.selected_cards.push(cid);
            }
        }
    }

    // Finalization
    if next_ctx.selected_cards.is_empty() && !moved_cards.is_empty() {
        next_ctx.selected_cards.extend(moved_cards.iter().copied());
    }
    if !next_ctx.selected_cards.is_empty() {
        ctx.selected_cards = next_ctx.selected_cards.clone();
    }

    // TAP_SELF check - inline simple version
    let should_tap_self = moved_cards.iter().any(|&cid| db.get_live(cid).is_some())
        && ctx.area_idx >= 0 && ctx.area_idx < 3
        && source_ability(db, ctx).map(|ability| {
            ability.effects.iter().any(|effect| {
                effect.runtime_opcode == O_NOP
                    && effect.params.get("raw_effect").and_then(|v| v.as_str()) == Some("TAP_SELF")
            })
        }).unwrap_or(false);
    
    if should_tap_self {
        state.players[p_idx].set_tapped(ctx.area_idx as usize, true);
    }

    // Fire triggers
    if !next_ctx.selected_cards.is_empty() {
        state.trigger_move_to_discard(db, target_player_idx, &next_ctx, &next_ctx.selected_cards);
    } else if !moved_cards.is_empty() {
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

// === Inlined helper functions ===

fn is_until_size_op(frame_data: &AbilityFrameComponents<'_>) -> bool {
    frame_data.params.as_ref()
        .and_then(|p| p.get("operation").or_else(|| p.get("OPERATION")))
        .and_then(|v| v.as_str())
        .map(|s| s.eq_ignore_ascii_case("UNTIL_SIZE"))
        .unwrap_or(false)
}

fn is_deck_zone(zone: Zone) -> bool {
    matches!(zone, Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default)
}

/// Check if more cards are available for selection
fn has_available_filtered(
    state: &GameState,
    db: &CardDatabase,
    player_idx: usize,
    zone: Zone,
    filter_attr: u64,
    ctx: &AbilityContext,
) -> bool {
    match zone {
        Zone::Hand => state.players[player_idx].hand.iter().any(|&c| {
            CardFilter::from_attr(filter_attr as i64).matches(state, db, c, None, false, None, ctx)
        }),
        Zone::Stage => state.players[player_idx].stage.iter().any(|&c| {
            if c < 0 { return false; }
            CardFilter::from_attr(filter_attr as i64).matches(state, db, c, None, false, None, ctx)
        }),
        _ => true,
    }
}

/// Prepare discard prompt - returns true if suspended for player input
#[allow(clippy::too_many_arguments)]
fn prepare_discard_prompt(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    _p_idx: usize,
    source_zone: Zone,
    count: i32,
    is_optional: bool,
    filter_attr: u64,
    v: i32,
    s: i32,
    choice_type: ChoiceType,
    available_count: i32,
    target_player_idx: usize,
    next_ctx: &mut AbilityContext,
) -> bool {
    if next_ctx.choice_index == -1 && available_count < v {
        return false;
    }
    if available_count == 0 {
        return false;
    }

    // Auto-pick when forced (only 1 valid choice)
    if !is_optional && next_ctx.choice_index == -1 && count == 1 && available_count == 1 {
        next_ctx.choice_index = 0;
        return false;
    }

    // Optional deck discard - ask yes/no
    if is_optional && next_ctx.choice_index == -1 && is_deck_zone(source_zone) {
        return matches!(
            suspend_choice(state, db, ctx, next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, ChoiceType::Optional, filter_attr, count as i16),
            HandlerResult::Suspend
        );
    }

    // Need specific card selection from hand/stage/discard
    if next_ctx.choice_index == -1 && count > 0 && !is_deck_zone(source_zone) {
        let mut filter_obj = frame.filter();
        match source_zone {
            Zone::Stage => filter_obj.zone_mask = 4,
            Zone::Hand => filter_obj.zone_mask = 6,
            Zone::Discard => filter_obj.zone_mask = 7,
            _ => {}
        }
        let filter_attr_with_mask = filter_obj.to_attr();

        return matches!(
            suspend_choice(state, db, ctx, next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr_with_mask as u64, v as i16),
            HandlerResult::Suspend
        );
    }

    false
}

/// Handle selected discard with multi-select support
#[allow(clippy::too_many_arguments)]
fn handle_selected_discard(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    target_player_idx: usize,
    source_zone: Zone,
    count: i32,
    is_optional: bool,
    filter_attr: u64,
    s: i32,
    choice_type: ChoiceType,
    next_ctx: &mut AbilityContext,
    moved_cards: &mut Vec<i32>,
) -> HandlerResult {
    // Handle optional skip
    if is_optional && next_ctx.choice_index == CHOICE_DONE {
        finish_pending_interaction(state);
        return HandlerResult::Return;
    }

    // Handle CHOICE_DONE with remaining cards
    if next_ctx.choice_index == CHOICE_DONE {
        if next_ctx.v_remaining > 0 || (next_ctx.v_remaining == -1 && count > 0) {
            let remaining = if next_ctx.v_remaining > 0 { next_ctx.v_remaining } else { count as i16 };
            if matches!(
                suspend_choice(state, db, ctx, next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr, remaining),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        }
        return HandlerResult::Continue;
    }

    // Remove selected card
    let idx = next_ctx.choice_index as usize;
    let removed_cid = remove_card_by_index(
        state, db, ctx, target_player_idx, source_zone, idx, next_ctx.area_idx as i32, (s & (1 << 25)) != 0,
    ).unwrap_or(-1);
    
    if removed_cid < 0 {
        return HandlerResult::Continue;
    }

    state.players[target_player_idx].push_discard_card(removed_cid as i32);
    moved_cards.push(removed_cid as i32);
    
    next_ctx.v_remaining = if next_ctx.v_remaining > 0 {
        next_ctx.v_remaining - 1
    } else {
        (count as i16) - 1
    };
    
    if !next_ctx.selected_cards.contains(&removed_cid) {
        next_ctx.selected_cards.push(removed_cid);
    }

    // Check if more cards needed
    if next_ctx.v_remaining > 0 {
        let still_available = has_available_filtered(state, db, target_player_idx, source_zone, filter_attr, next_ctx);

        if !still_available {
            finish_pending_interaction(state);
            return HandlerResult::Continue;
        }

        next_ctx.choice_index = -1;

        // Auto-pick for forced discards
        let is_forced = !is_optional && (count as usize) >= state.players[target_player_idx].hand.len();
        if (ctx.auto_pick || is_forced) && !is_optional {
            let has_cards = match source_zone {
                Zone::Hand => !state.players[target_player_idx].hand.is_empty(),
                Zone::Stage => state.players[target_player_idx].stage.iter().any(|&c| c >= 0),
                _ => true,
            };

            if has_cards {
                next_ctx.choice_index = 0;
                return handle_move_to_discard(state, db, next_ctx, frame, frame_idx);
            }
        }

        if matches!(
            suspend_choice(state, db, ctx, next_ctx, frame_idx, O_MOVE_TO_DISCARD, s, choice_type, filter_attr, next_ctx.v_remaining),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    HandlerResult::Continue
}
