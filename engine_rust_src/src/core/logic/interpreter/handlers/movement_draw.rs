use crate::core::logic::models::AbilityFrame;
use crate::core::enums::*;
use crate::core::logic::constants::FILTER_MASK_LOWER;
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use super::super::HandlerResult;
pub fn handle_draw(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &mut AbilityContext,
    frame: &AbilityFrame,
) -> HandlerResult {
    let op = frame.opcode();
    let v = frame.value();
    let s = frame.slot();
    let p_idx = ctx.player_id as usize;
    let count = if frame.filter().compare_accumulated {
        resolve_count(
            state,
            _db,
            s,
            (frame.filter().to_attr() & FILTER_MASK_LOWER) as u64,
            p_idx as i32,
            ctx,
            0,
        ) as u32
    } else {
        v as u32
    };
    let slot = frame.dslot();
    let target_p = if slot.is_opponent { 1 - p_idx } else { p_idx };

    match op {
        O_DRAW => {
            // Draw to hand (or specified destination zone)
            for _ in 0..count {
                if state.core.players[target_p].deck.is_empty() {
                    state.resolve_deck_refresh(target_p);
                }
                if let Some(card_id) = state.core.players[target_p].pop_deck_card() {
                    let t = state.turn as i32;
                    // Route to destination zone based on slot.dest_zone
                    match slot.dest_zone {
                        Zone::Hand => {
                            state.core.players[target_p].draw_hand_card(card_id, t);
                        }
                        Zone::Discard => {
                            state.core.players[target_p].push_discard_card(card_id);
                        }
                        _ => {
                            // Default to hand if zone is not explicitly specified
                            state.core.players[target_p].draw_hand_card(card_id, t);
                        }
                    }
                }
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
            if s == 90 || s == 6 {
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



