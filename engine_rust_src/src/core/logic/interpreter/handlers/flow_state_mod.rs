use super::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::constants::{DYNAMIC_VALUE, FILTER_MASK_LOWER};
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::models::interpreter::resolve_target_slot;

#[allow(clippy::too_many_arguments)]
pub fn handle_state_modifiers(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame: &AbilityFrame,
    op: i32,
    v: i32,
    a: i64,
    s: i32,
    p_idx: usize,
    base_p: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: i32,
) -> HandlerResult {
    match op {
        O_LOSE_EXCESS_HEARTS => state.players[p_idx].excess_hearts = 0,
        O_DIV_VALUE => {
            if v > 1 {
                ctx.v_accumulated /= v as i16;
            }
        }
        O_RESTRICTION => {
            let restriction_id = (a as u64 & FILTER_MASK_LOWER) as u8;
            state.players[p_idx].restrictions.push(restriction_id);
            if restriction_id == 1 || v == 1 {
                state.players[p_idx].set_flag(crate::core::logic::player::PlayerState::FLAG_CANNOT_LIVE, true);
            }
        }
        O_PREVENT_ACTIVATE | O_PREVENT_BATON_TOUCH | O_PREVENT_SET_TO_SUCCESS_PILE | O_PREVENT_PLAY_TO_SLOT => {
            let filter_target = (a as u64) & 0x03;
            let target_p_idx = if filter_target == 2 || slot_info.is_opponent || target_slot == 2 {
                1 - base_p
            } else {
                base_p
            };
            match op {
                O_PREVENT_ACTIVATE => state.players[target_p_idx].set_prevent_activate(1),
                O_PREVENT_BATON_TOUCH => state.players[target_p_idx].set_prevent_baton_touch(1),
                O_PREVENT_SET_TO_SUCCESS_PILE => state.players[target_p_idx].set_prevent_success_pile_set(1),
                O_PREVENT_PLAY_TO_SLOT => {
                    let resolved_slot = if target_slot == 10 {
                        ctx.target_slot as i32
                    } else {
                        resolve_target_slot(target_slot, ctx) as i32
                    };
                    if resolved_slot >= 0 && resolved_slot < 3 {
                        let old = state.players[target_p_idx].prevent_play_to_slot_mask();
                        state.players[target_p_idx].set_prevent_play_to_slot_mask(old | (1 << resolved_slot) as u8);
                    }
                }
                _ => {}
            }
        }
        O_REDUCE_LIVE_SET_LIMIT => {
            let new_v = state.players[p_idx].prevent_success_pile_set().saturating_add(v as u8);
            state.players[p_idx].set_prevent_success_pile_set(new_v);
        }
        O_REDUCE_YELL_COUNT => {
            let final_v = if (a as u64 & DYNAMIC_VALUE) != 0 {
                resolve_count(state, db, s, a as u64 & !DYNAMIC_VALUE & FILTER_MASK_LOWER, p_idx as i32, ctx, 0)
            } else {
                v
            };
            state.players[p_idx].yell_count_reduction = state.players[p_idx].yell_count_reduction.saturating_add(final_v as i16);
        }
        O_BATON_TOUCH_MOD => state.players[p_idx].set_baton_touch_limit(v as u8),
        O_IMMUNITY => state.players[p_idx].set_flag(crate::core::logic::player::PlayerState::FLAG_IMMUNITY, v != 0),
        _ => {}
    }
    HandlerResult::Continue
}
