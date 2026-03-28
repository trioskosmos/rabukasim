use super::*;
use crate::core::logic::constants::{CHOICE_DONE, TARGET_SLOT_STAGE, ZONE_DISCARD, ZONE_HAND};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::logging;
use crate::core::logic::interpreter::suspension::resolve_target_player;

#[allow(clippy::too_many_arguments)]
pub fn resolve_select_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    _p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    supports_partial_completion: bool,
    partial_selection_prompt: i16,
    is_move_member_follow_up: bool,
) -> HandlerResult {
    let choice = ctx.choice_index as i32;
    let source_zone = slot_info.source_zone as u8;
    
    // Simplified filter attr recovery - just use interaction stack or fall back to a
    let filter_attr = state
        .interaction_stack
        .last()
        .map(|i| i.filter_attr)
        .unwrap_or(a as u64);
    
    let is_targeted_select_member_cost = state
        .interaction_stack
        .last()
        .map(|i| i.target_slot == TARGET_SLOT_STAGE as i32 && (i.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK) != 0)
        .unwrap_or(false);

    if supports_partial_completion && choice == CHOICE_DONE as i32 {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
        return HandlerResult::Continue;
    }

    let target_player = if is_targeted_select_member_cost {
        ctx.player_id as usize
    } else {
        resolve_target_player(slot_info, filter_attr, ctx.player_id as usize)
    };
    
    let selected_cid = {
        let source_cards = cards_for_source_zone(state, target_player, source_zone);
        let idx = if source_zone == ZONE_HAND as u8 || source_zone == ZONE_DISCARD as u8 {
            choice.saturating_sub(1) as usize
        } else {
            choice as usize
        };
        source_cards.get(idx).copied().unwrap_or(-1)
    };
    
    if source_zone == ZONE_HAND as u8 || source_zone == ZONE_DISCARD as u8 {
        ctx.selected_hand_idx = if choice > 0 { choice - 1 } else { choice } as i16;
        ctx.target_card_id = selected_cid;
    } else {
        ctx.target_slot = choice as i16;
        ctx.area_idx = choice as i16;
    }
    
    if selected_cid >= 0 && !ctx.selected_cards.contains(&selected_cid) {
        ctx.selected_cards.push(selected_cid);
    }
    
    if is_targeted_select_member_cost && choice >= 0 && choice < 3 {
        state.players[target_player].set_tapped(choice as usize, true);
    }
    
    // Inline: selected_target_key
    let selected_key = ((source_zone as i32) << 8) | (choice & 0xFF);
    if !ctx.selected_target_keys.contains(&selected_key) {
        ctx.selected_target_keys.push(selected_key);
    }

    if is_move_member_follow_up {
        ctx.target_slot = choice as i16;
        ctx.choice_index = -1;
        return HandlerResult::Continue;
    }

    if supports_partial_completion && !ctx.selected_cards.is_empty() {
        let cards = cards_for_source_zone(state, target_player, source_zone);
        
        // Inline: count_selected_targets
        let current_selection_count = cards
            .iter()
            .enumerate()
            .filter(|(idx, cid)| **cid >= 0 && ctx.selected_target_keys.contains(&(((source_zone as i32) << 8) | (*idx as i32 & 0xFF))))
            .count();
            
        // Inline: count_remaining_targets  
        let remaining_candidates = cards
            .iter()
            .enumerate()
            .filter(|(idx, cid)| {
                **cid >= 0
                    && !ctx.selected_target_keys.contains(&(((source_zone as i32) << 8) | (*idx as i32 & 0xFF)))
                    && state.card_matches_filter_with_ctx(db, **cid, filter_attr, ctx)
            })
            .count();

        let remaining_picks = (v as usize).saturating_sub(current_selection_count);

        if remaining_picks > 0 && remaining_candidates > 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = remaining_picks as i16;
            if matches!(
                suspend_choice(
                    state, db, ctx, ctx, instr_ip, op, s,
                    ChoiceType::SelectMember, filter_attr, remaining_picks as i16,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if remaining_picks > 0 && current_selection_count == 1 && remaining_candidates > 0 {
            if matches!(
                suspend_choice(
                    state, db, ctx, ctx, instr_ip, op, s,
                    ChoiceType::Optional, 0, partial_selection_prompt,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
        } else if remaining_picks > 0 && remaining_candidates == 0 {
            ctx.choice_index = -1;
            ctx.v_remaining = -1;
        }
    }

    if !supports_partial_completion && !is_move_member_follow_up {
        ctx.choice_index = -1;
        ctx.v_remaining = -1;
    }

    HandlerResult::Continue
}
