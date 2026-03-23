use crate::core::enums::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, Zone};
use crate::core::models::CHOICE_DONE;

use super::super::super::HandlerResult;
use super::super::movement_discard_helpers::remove_card_by_index;

#[allow(clippy::too_many_arguments)]
pub fn handle_discard_resume(
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
    if is_optional
        && matches!(
            source_zone,
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
        )
        && next_ctx.choice_index == 1
    {
        return HandlerResult::SetCond(false);
    }

    if next_ctx.choice_index == CHOICE_DONE {
        if is_optional {
            return HandlerResult::SetCond(false);
        }

        if (next_ctx.v_remaining > 0) || (next_ctx.v_remaining == -1 && count > 0) {
            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    &*next_ctx,
                    frame_idx,
                    O_MOVE_TO_DISCARD,
                    s,
                    choice_type,
                    filter_attr,
                    if next_ctx.v_remaining > 0 {
                        next_ctx.v_remaining
                    } else {
                        count as i16
                    },
                ),
                HandlerResult::Suspend
            ) {
                return HandlerResult::Suspend;
            }
            return HandlerResult::Continue;
        }
    }

    let idx = next_ctx.choice_index as usize;
    let mut removed_cid = -1;
    if let Some(cid) = remove_card_by_index(
        state,
        db,
        ctx,
        target_player_idx,
        source_zone,
        idx,
        next_ctx.area_idx as i32,
        (s & (1 << 25)) != 0,
    ) {
        removed_cid = cid;
    }
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
    if next_ctx.v_remaining > 0 {
        let still_available = match source_zone {
            Zone::Hand => state.players[target_player_idx].hand.iter().any(|&c| {
                let cf = CardFilter::from_attr(filter_attr as i64);
                cf.matches(state, db, c, None, false, None, next_ctx)
            }),
            Zone::Stage => state.players[target_player_idx].stage.iter().any(|&c| {
                if c < 0 {
                    return false;
                }
                let cf = CardFilter::from_attr(filter_attr as i64);
                cf.matches(state, db, c, None, false, None, next_ctx)
            }),
            _ => true,
        };

        if !still_available {
            return HandlerResult::Continue;
        }

        next_ctx.choice_index = -1;
        next_ctx.selected_cards.push(removed_cid);

        let is_forced_pick =
            !is_optional && (count as usize) >= (state.players[target_player_idx].hand.len());
        if (ctx.auto_pick || is_forced_pick) && !is_optional {
            let still_available = match source_zone {
                Zone::Hand => !state.players[target_player_idx].hand.is_empty(),
                Zone::Stage => state.players[target_player_idx]
                    .stage
                    .iter()
                    .any(|&c| c >= 0),
                _ => true,
            };

            if still_available {
                next_ctx.choice_index = 0;
                return crate::core::logic::interpreter::handlers::movement::handle_move_to_discard(
                    state, db, next_ctx, frame, frame_idx,
                );
            }
        }

        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                &*next_ctx,
                frame_idx,
                O_MOVE_TO_DISCARD,
                s,
                choice_type,
                filter_attr,
                next_ctx.v_remaining,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    HandlerResult::Continue
}
