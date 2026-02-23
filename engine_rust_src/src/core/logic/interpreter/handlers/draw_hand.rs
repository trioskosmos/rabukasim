use crate::core::logic::{GameState, CardDatabase, AbilityContext};
use crate::core::enums::*;
use super::HandlerResult;

pub fn handle_draw(state: &mut GameState, _db: &CardDatabase, ctx: &mut AbilityContext, op: i32, v: i32, _a: i32, s: i32) -> HandlerResult {
    let p_idx = ctx.player_id as usize;
    let count = v as u32;
    let target_p = if s == 2 { 1 - p_idx } else if s == 3 { 0 } else { p_idx };
    
    match op {
        O_DRAW => {
            if s == 3 {
                state.draw_cards(0, count);
                state.draw_cards(1, count);
            } else {
                state.draw_cards(target_p, count);
            }
            state.log_turn_event("EFFECT", ctx.source_card_id, ctx.ability_index, p_idx as u8, &format!("Draw {} card(s)", count));
        },
        O_DRAW_UNTIL => {
            let target_hand_size = v as usize;
            let current_hand_size = state.core.players[p_idx].hand.len();
            if current_hand_size < target_hand_size {
                let to_draw = (target_hand_size - current_hand_size) as u32;
                state.draw_cards(p_idx, to_draw);
            }
        },
        O_ADD_TO_HAND => {
            // Special case: Adding from looked cards (s=90 or s=6)
            if s == 90 || s == 6 {
                for _ in 0..v as usize {
                    if !state.core.players[p_idx].looked_cards.is_empty() {
                        let cid = state.core.players[p_idx].looked_cards.remove(0);
                        state.core.players[p_idx].hand.push(cid);
                        state.core.players[p_idx].hand_increased_this_turn = state.core.players[p_idx].hand_increased_this_turn.saturating_add(1);
                    }
                }
            } else {
                state.draw_cards(p_idx, v as u32);
            }
        },
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
