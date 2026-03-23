use super::super::interaction::*;
use super::super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::constants::{
    CHOICE_ALL, CHOICE_DONE, FILTER_MASK_LOWER, FLAG_REVEAL_UNTIL_IS_LIVE,
};
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, PlayerState, TriggerType};
use crate::core::models::interpreter::{check_condition_opcode, resolve_target_slot};

#[path = "movement_deck_look.rs"]
mod movement_deck_look;
#[path = "movement_deck_move.rs"]
mod movement_deck_move;
#[path = "movement_deck_search.rs"]
mod movement_deck_search;
pub fn handle_deck_zones(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
    frame_idx: usize,
) -> HandlerResult {
    let frame_data = frame.components();
    let op = frame_data.opcode;
    let v = frame_data.value;
    let a = frame_data.raw_attr as i64;
    let s = frame_data.raw_slot;
    let p_idx = ctx.player_id as usize;
    let slot = frame_data.slot;
    let target_slot = slot.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };
    let look_resolved_slot = if op == O_REVEAL_CARDS {
        if s == 6 || slot.source_zone as i32 == 6 || resolved_slot == 6 {
            6
        } else {
            resolved_slot
        }
    } else {
        resolved_slot
    };

    match op {
        O_SEARCH_DECK => {
            return movement_deck_search::handle_search_deck(
                state,
                db,
                ctx,
                p_idx,
                s,
                a,
                resolved_slot,
            );
        }
        O_ORDER_DECK => {
            return super::handle_order_deck(state, db, ctx, p_idx, v, a, frame_idx);
        }
        O_LOOK_REORDER_DISCARD => {
            return super::handle_look_reorder_discard(state, db, ctx, p_idx, v, a, frame_idx);
        }
        O_MOVE_TO_DECK => {
            return movement_deck_move::handle_move_to_deck(
                state,
                db,
                ctx,
                p_idx,
                v,
                slot.remainder_zone as i32,
                a,
                slot.target_slot as i32,
            );
        }
        O_SWAP_CARDS => {
            return movement_deck_move::handle_swap_cards(state, p_idx, v, resolved_slot);
        }
        O_REVEAL_UNTIL => {
            return movement_deck_look::handle_reveal_until(
                state,
                db,
                ctx,
                p_idx,
                v,
                a,
                s,
                resolved_slot,
            );
        }
        O_LOOK_DECK | O_REVEAL_CARDS | O_CHEER_REVEAL => {
            return movement_deck_look::handle_look_cards(
                state,
                db,
                ctx,
                p_idx,
                op,
                v,
                a,
                frame_idx,
                look_resolved_slot,
            );
        }
        O_LOOK_DECK_DYNAMIC => {
            return movement_deck_look::handle_look_deck_dynamic(state, ctx, p_idx, v);
        }
        O_MOVE_TO_DISCARD => {
            return super::handle_move_to_discard(state, db, ctx, frame, frame_idx);
        }
        O_LOOK_AND_CHOOSE => {
            return handle_look_and_choose(state, db, ctx, frame, frame_idx);
        }
        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
            return handle_recovery(state, db, ctx, frame, frame_idx, op);
        }
        O_PLAY_LIVE_FROM_DISCARD => {
            return handle_play_live_from_discard(state, db, ctx, frame, frame_idx);
        }
        O_SELECT_CARDS => {
            return handle_select_cards(state, db, ctx, frame, frame_idx);
        }
        O_SWAP_ZONE => return super::handle_swap_zone(state, db, ctx, frame, frame_idx),
        _ => return HandlerResult::Continue,
    }
}
