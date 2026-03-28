use super::HandlerResult;
use crate::core::logic::models::AbilityFrame;

#[path = "flow_context.rs"]
mod flow_context;
#[path = "flow_effects.rs"]
mod flow_effects;
#[path = "flow_select.rs"]
mod flow_select;
#[path = "flow_state_mod.rs"]
mod flow_state_mod;
#[path = "flow_swap.rs"]
mod flow_swap;
use crate::core::enums::*;
use crate::core::logic::constants::FILTER_MASK_LOWER;
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType};

use super::flow_helpers::discard_current_yell_pile;
pub fn handle_meta_control(
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
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    let slot_info = frame_data.slot;
    let target_slot = slot_info.target_slot as i32;

    match op {
        O_CALC_SUM_COST => {
            let mut sum = 0;
            for &cid in &ctx.selected_cards {
                if cid >= 0 {
                    if let Some(member) = db.get_member(cid) {
                        sum += member.cost as i32;
                    }
                }
            }
            if state.debug.debug_mode {
                let selected_names: Vec<String> = ctx
                    .selected_cards
                    .iter()
                    .filter_map(|cid| {
                        db.get_member(*cid)
                            .map(|card| card.name.clone())
                            .or_else(|| db.get_live(*cid).map(|card| card.name.clone()))
                    })
                    .collect();
                println!(
                    "[DEBUG] CALC_SUM_COST: total_sum={} cards={:?}",
                    sum, selected_names
                );
            }
            ctx.v_accumulated = sum as i16;
        }
        O_NEGATE_EFFECT => {
            let trigger_type = match v {
                1 => TriggerType::OnPlay,
                2 => TriggerType::OnLiveStart,
                3 => TriggerType::OnLiveSuccess,
                4 => TriggerType::TurnStart,
                5 => TriggerType::TurnEnd,
                6 => TriggerType::Constant,
                7 => TriggerType::Activated,
                8 => TriggerType::OnLeaves,
                9 => TriggerType::OnReveal,
                10 => TriggerType::OnPositionChange,
                _ => TriggerType::None,
            };
            if target_slot >= 0 && (target_slot as usize) < 3 {
                let cid = state.players[p_idx].stage[target_slot as usize];
                if cid >= 0 {
                    let count = (a as u64 & FILTER_MASK_LOWER).max(1) as i32;
                    if let Some(entry) = state.players[p_idx]
                        .negated_triggers
                        .iter_mut()
                        .find(|entry| entry.0 == cid && entry.1 == trigger_type)
                    {
                        entry.2 += count;
                    } else {
                        state.players[p_idx]
                            .negated_triggers
                            .push((cid, trigger_type, count));
                    }
                }
            }
        }
        O_LOSE_EXCESS_HEARTS
        | O_DIV_VALUE
        | O_RESTRICTION
        | O_PREVENT_ACTIVATE
        | O_PREVENT_BATON_TOUCH
        | O_PREVENT_SET_TO_SUCCESS_PILE
        | O_PREVENT_PLAY_TO_SLOT
        | O_REDUCE_LIVE_SET_LIMIT
        | O_REDUCE_YELL_COUNT
        | O_BATON_TOUCH_MOD
        | O_IMMUNITY => {
            return flow_state_mod::handle_state_modifiers(
                state,
                db,
                ctx,
                frame,
                op,
                v,
                a,
                s,
                p_idx,
                base_p,
                slot_info,
                target_slot,
            );
        }
        O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
            return flow_select::handle_select_ops(
                state, db, ctx, frame, frame_idx, op, v, a, s, p_idx, slot_info,
            );
        }
        O_OPPONENT_CHOOSE => {
            return flow_context::handle_opponent_choose(state, db, ctx, frame_idx);
        }
        O_TRIGGER_REMOTE => {
            return flow_effects::handle_trigger_remote(
                state, db, ctx, frame, frame_idx, v, p_idx, slot_info,
            );
        }
        O_META_RULE => {
            return flow_effects::handle_meta_rule(
                state,
                db,
                ctx,
                frame,
                frame_idx,
                a,
                v,
                p_idx,
                base_p,
                slot_info,
                target_slot,
            );
        }
        O_COLOR_SELECT => {
            return flow_context::handle_color_select(state, db, ctx, frame_idx);
        }
        O_SWAP_AREA => {
            return flow_swap::handle_swap_area(
                state,
                ctx,
                base_p,
                slot_info,
                target_slot,
                a,
                s,
                v,
            );
        }
        O_REPEAT_ABILITY => {
            return flow_context::handle_repeat_ability(ctx, v);
        }
        O_SET_TARGET_SELF => {
            flow_context::handle_set_target_self(ctx);
        }
        O_SET_TARGET_OPPONENT => {
            flow_context::handle_set_target_opponent(ctx);
        }
        O_FLAVOR_ACTION => {
            flow_context::handle_flavor_action(state, v, a, s);
        }
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
