use super::super::HandlerResult;
use crate::core::enums::*;
use crate::core::generated_layout::S_STANDARD_IS_OPPONENT_SHIFT;
use crate::core::logic::interpreter::conditions::resolve_count_frame;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
pub fn handle_draw(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
) -> HandlerResult {
    let frame_data = frame.components();
    let op = frame_data.opcode;
    let v = frame_data.value;
    let p_idx = ctx.player_id as usize;
    let count = if frame_data.filter.compare_accumulated {
        resolve_count_frame(state, _db, &frame_data, ctx, 0) as u32
    } else {
        v as u32
    };
    let slot = frame_data.slot;
    let raw_is_opponent = ((frame_data.raw_slot as u32 >> S_STANDARD_IS_OPPONENT_SHIFT) & 1) != 0;
    let target_p = if slot.is_opponent || raw_is_opponent {
        1 - p_idx
    } else {
        p_idx
    };

    match op {
        O_DRAW => {
            // Draw to hand (or specified destination zone)
            if state.debug.debug_mode {
                state.trace_internal(&format!(
                    "FRAME_DRAW: target_p={} deck_before={} hand_before={} dest={:?} {}",
                    target_p,
                    state.players[target_p].deck.len(),
                    state.players[target_p].hand.len(),
                    slot.dest_zone,
                    crate::core::logic::interpreter::logging::describe_context(ctx)
                ));
            }
            for _ in 0..count {
                if state.players[target_p].deck.is_empty() {
                    state.resolve_deck_refresh(target_p);
                }
                if let Some(card_id) = state.players[target_p].pop_deck_card() {
                    let t = state.turn as i32;
                    // Route to destination zone based on slot.dest_zone
                    match slot.dest_zone {
                        Zone::Hand => {
                            state.players[target_p].draw_hand_card(card_id, t);
                        }
                        Zone::Discard => {
                            state.players[target_p].push_discard_card(card_id);
                        }
                        _ => {
                            // Default to hand if zone is not explicitly specified
                            state.players[target_p].draw_hand_card(card_id, t);
                        }
                    }
                }
            }
            if state.debug.debug_mode {
                state.trace_internal(&format!(
                    "FRAME_DRAW_DONE: deck_after={} hand_after={}",
                    state.players[target_p].deck.len(),
                    state.players[target_p].hand.len()
                ));
            }
            state.log_event(
                "EFFECT",
                &format!("Draw {} card(s)", count),
                ctx.source_card_id,
                ctx.ability_index,
                p_idx as u8,
                None,
                true,
            );
        }
        O_DRAW_UNTIL => {
            let target_hand_size = v as usize;
            let current_hand_size = state.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                let to_draw = (target_hand_size - current_hand_size) as u32;
                state.draw_cards(p_idx, to_draw);
            }
        }
        O_ADD_TO_HAND => {
            if frame_data.raw_slot == 90 || frame_data.raw_slot == 6 {
                for _ in 0..v as usize {
                    if !state.players[p_idx].looked_cards.is_empty() {
                        let cid = state.players[p_idx].looked_cards.remove(0);
                        state.players[p_idx].gain_hand_card(cid);
                    }
                }
            } else {
                state.draw_cards(p_idx, v as u32);
            }
        }
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
