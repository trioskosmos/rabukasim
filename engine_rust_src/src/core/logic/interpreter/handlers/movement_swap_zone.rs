use crate::core::enums::{ChoiceType, Zone};
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::interpreter::handlers::interaction_zone::{
    collect_zone_cards, place_card_at_destination, remove_card_from_zone,
};
use crate::core::logic::models::AbilityFrameComponents;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::generated_constants::ACTION_BASE_CHOICE;
use crate::core::O_SWAP_ZONE;

use crate::core::logic::interpreter::handlers::HandlerResult;

fn normalized_source_zone(frame_data: &AbilityFrameComponents<'_>) -> Zone {
    match frame_data.slot.source_zone {
        Zone::Default => Zone::SuccessPile,
        other => other,
    }
}

fn normalized_dest_zone(frame_data: &AbilityFrameComponents<'_>) -> Zone {
    match frame_data.slot.dest_zone {
        Zone::Default => Zone::Discard,
        other => other,
    }
}

fn prompt_cards(
    state: &GameState,
    p_idx: usize,
    zone: Zone,
) -> Vec<i32> {
    collect_zone_cards(state, p_idx, zone)
        .into_iter()
        .filter(|cid| *cid >= 0)
        .collect()
}

fn action_index_to_card_index(choice_index: i32) -> Option<usize> {
    if choice_index >= ACTION_BASE_CHOICE {
        Some((choice_index - ACTION_BASE_CHOICE) as usize)
    } else {
        None
    }
}

#[allow(clippy::too_many_arguments)]
pub fn handle_swap_zone(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame_data: &AbilityFrameComponents<'_>,
    frame_idx: usize,
) -> HandlerResult {
    let p_idx = ctx.player_id as usize;
    let source_zone = normalized_source_zone(frame_data);
    let dest_zone = normalized_dest_zone(frame_data);
    let is_optional = frame_data.filter.is_optional || frame_data.is_optional();

    if is_optional && ctx.selected_cards.is_empty() && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_SWAP_ZONE,
                frame_data.raw_slot,
                ChoiceType::Optional,
                frame_data.resolved_filter_attr(),
                frame_data.value as i16,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && ctx.selected_cards.is_empty() && ctx.v_remaining == -1 && ctx.choice_index != -1 {
        if ctx.choice_index == 1 {
            return HandlerResult::Continue;
        }
        ctx.choice_index = -1;
    }

    if ctx.selected_cards.is_empty() {
        if ctx.choice_index == -1 {
            let cards = prompt_cards(state, p_idx, source_zone);
            if cards.is_empty() {
                return HandlerResult::Continue;
            }
            state.players[p_idx].looked_cards = cards.into();
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    ctx,
                    frame_idx,
                    O_SWAP_ZONE,
                    frame_data.raw_slot,
                    ChoiceType::SelectSwapSource,
                    frame_data.resolved_filter_attr(),
                    frame_data.value as i16,
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            if ctx.choice_index == -1 {
                return HandlerResult::Continue;
            }
        }

        let Some(source_idx) = action_index_to_card_index(ctx.choice_index as i32) else {
            return HandlerResult::Continue;
        };
        let Some(&source_cid) = state.players[p_idx].looked_cards.get(source_idx) else {
            return HandlerResult::Continue;
        };

        ctx.selected_cards.push(source_cid);
        state.players[p_idx].looked_cards = prompt_cards(state, p_idx, dest_zone).into();
        ctx.choice_index = -1;

        if state.players[p_idx].looked_cards.is_empty() {
            return HandlerResult::Continue;
        }

        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_SWAP_ZONE,
                frame_data.raw_slot,
                ChoiceType::SelectSwapTarget,
                frame_data.resolved_filter_attr(),
                0,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
        if ctx.choice_index == -1 {
            return HandlerResult::Continue;
        }
    }

    let Some(target_idx) = action_index_to_card_index(ctx.choice_index as i32) else {
        return HandlerResult::Continue;
    };
    let Some(&source_cid) = ctx.selected_cards.last() else {
        return HandlerResult::Continue;
    };
    let Some(&target_cid) = state.players[p_idx].looked_cards.get(target_idx) else {
        return HandlerResult::Continue;
    };

    if source_cid >= 0 && target_cid >= 0 {
        let _ = remove_card_from_zone(state, db, ctx, p_idx, source_zone, source_cid);
        let _ = remove_card_from_zone(state, db, ctx, p_idx, dest_zone, target_cid);
        place_card_at_destination(
            state,
            db,
            ctx,
            p_idx,
            source_cid,
            dest_zone,
            None,
            frame_data.slot.is_wait,
            false,
            source_zone,
        );
        place_card_at_destination(
            state,
            db,
            ctx,
            p_idx,
            target_cid,
            source_zone,
            None,
            frame_data.slot.is_wait,
            false,
            dest_zone,
        );
    }

    ctx.choice_index = -1;
    ctx.v_remaining = -1;
    ctx.selected_cards.clear();
    state.players[p_idx].looked_cards.clear();
    HandlerResult::Continue
}
