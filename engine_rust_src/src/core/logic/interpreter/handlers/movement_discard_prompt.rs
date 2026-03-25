use crate::core::enums::*;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, Zone};
use crate::core::models::interpreter::HandlerResult;

#[allow(clippy::too_many_arguments)]
pub fn prepare_discard_prompt(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
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
    if is_optional
        && next_ctx.choice_index == -1
        && available_count < v
        && !matches!(
            source_zone,
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
        )
    {
        return false;
    }

    if available_count == 0 {
        return false;
    }

    if !is_optional && next_ctx.choice_index == -1 && count == 1 && available_count == 1 {
        next_ctx.choice_index = 0;
        return false;
    }

    if is_optional
        && next_ctx.choice_index == -1
        && matches!(
            source_zone,
            Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
        )
    {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                next_ctx,
                frame_idx,
                O_MOVE_TO_DISCARD,
                s,
                ChoiceType::Optional,
                filter_attr,
                count as i16,
            ),
            HandlerResult::Suspend
        ) {
            return true;
        }
    }

    if next_ctx.choice_index == -1
        && count > 0
        && source_zone != Zone::Default
        && source_zone != Zone::Deck
        && source_zone != Zone::DeckTop
        && source_zone != Zone::DeckBottom
    {
        if next_ctx.choice_index == -1 {
            let mut filter_obj = frame.filter();
            if source_zone == Zone::Stage {
                filter_obj.zone_mask = 4;
            } else if source_zone == Zone::Hand {
                filter_obj.zone_mask = 6;
            } else if source_zone == Zone::Discard {
                filter_obj.zone_mask = 7;
            }
            let filter_attr_with_mask = filter_obj.to_attr();

            let items_count = match source_zone {
                Zone::Hand => state.players[target_player_idx].hand.len(),
                _ => state
                    .get_card_ids_in_zone(target_player_idx as u8, source_zone as u8)
                    .len(),
            };

            if matches!(
                suspend_choice(
                    state,
                    db,
                    ctx,
                    next_ctx,
                    frame_idx,
                    O_MOVE_TO_DISCARD,
                    s,
                    choice_type,
                    filter_attr_with_mask,
                    v as i16,
                ),
                HandlerResult::Suspend
            ) {
                return true;
            }
        }
    }

    false
}
