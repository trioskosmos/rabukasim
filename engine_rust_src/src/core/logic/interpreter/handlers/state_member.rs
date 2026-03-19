use crate::core::logic::interpreter::handlers::HandlerResult;
use crate::core::enums::*;
use crate::core::logic::{AbilityContext, CardDatabase, GameState};
use crate::core::logic::interpreter::instruction::BytecodeInstruction;
use crate::core::models::interpreter::{get_choice_text, resolve_target_slot};
use crate::core::models::suspend_interaction;

#[path = "state_member_play.rs"]
mod state_member_play;
#[path = "state_member_position.rs"]
mod state_member_position;
#[path = "state_member_tap.rs"]
mod state_member_tap;
pub fn handle_member_state(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    #[allow(unused_variables)]
    let s = instr.raw_s;
    let p_idx = ctx.player_id as usize;
    let slot_info = instr.slot();
    let target_slot = slot_info.target_slot as i32;
    let resolved_slot = if target_slot == 10 {
        ctx.target_slot as i32
    } else {
        resolve_target_slot(target_slot, ctx) as i32
    };

    match op {
        O_ACTIVATE_MEMBER => {
            let mut group_bits = 0u32;
            if let Some(card) = db.get_member(ctx.source_card_id) {
                for &g in &card.groups {
                    if g < 32 {
                        group_bits |= 1 << g;
                    }
                }
            }

            if v == 99 || (a != 0 && resolved_slot >= 3) {
                for i in 0..3 {
                    let cid = state.players[p_idx].stage[i];
                    if cid < 0 {
                        continue;
                    }
                    if a != 0 && !state.card_matches_filter_with_ctx(db, cid, a as u64, ctx) {
                        continue;
                    }
                    if state.players[p_idx].is_tapped(i) {
                        state.players[p_idx].set_tapped(i, false);
                        state.players[p_idx].activated_member_group_mask |= group_bits;
                    }
                }
            } else if target_slot == 1 {
                for i in 0..3 {
                    if state.players[p_idx].is_tapped(i) {
                        state.players[p_idx].set_tapped(i, false);
                        state.players[p_idx].activated_member_group_mask |= group_bits;
                    }
                }
            } else if resolved_slot < 3 {
                if state.players[p_idx].is_tapped(resolved_slot as usize) {
                    state.players[p_idx].set_tapped(resolved_slot as usize, false);
                    state.players[p_idx].activated_member_group_mask |= group_bits;
                }
            }
        }
        O_SET_TAPPED => {
            let is_optional = instr.filter_attr().is_optional;

            // First: If optional and this is the first interaction, ask player to confirm
            if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_SET_TAPPED,
                    resolved_slot as i32,
                    ChoiceType::Optional,
                    &choice_text,
                    instr.filter_attr().to_attr(),
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
            }

            // Second: Handle optional response
            if is_optional && ctx.v_remaining == -1 && ctx.choice_index != -1 {
                // If player chose to skip (choice_index == 1), mark execution as cancelled
                if ctx.choice_index == 1 {
                    if let Some(execution_id) = state.ui.current_execution_id {
                        state.ui.cancelled_execution_ids.insert(execution_id);
                    }
                    return HandlerResult::Continue;
                }
                // If player chose to proceed (choice_index == 0), reset and continue
                if ctx.choice_index == 0 {
                    ctx.choice_index = -1;
                }
            }

            // Finally: Execute the set_tapped action
            if resolved_slot < 3 {
                state.players[p_idx].set_tapped(resolved_slot as usize, v != 0);
            }
        }
        O_TAP_MEMBER => {
            let mut resolved_slot = resolve_target_slot(target_slot, ctx);
            let filter_target = (a as u64 & 0x3) as u8;
            let mut target_p_idx = match filter_target {
                2 => 1 - (ctx.player_id as usize),
                3 => 1,
                _ if slot_info.is_opponent || slot_info.target_slot == 2 => {
                    1 - (ctx.player_id as usize)
                }
                _ => ctx.player_id as usize,
            };
            if let Some(&selected_cid) = ctx.selected_cards.last() {
                for candidate_p_idx in 0..=1 {
                    if let Some(slot) = state.players[candidate_p_idx]
                        .stage
                        .iter()
                        .position(|&cid| cid == selected_cid)
                    {
                        target_p_idx = candidate_p_idx;
                        resolved_slot = slot;
                        break;
                    }
                }
            }

            if v == 0 && resolved_slot == 4 && a & 0x02 == 0 && (a & 0x01 != 0 || a & 0x80 != 0) {
                let mod_a = a | 0x02;
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_TAP_MEMBER,
                    0,
                    ChoiceType::TapMSelect,
                    &choice_text,
                    mod_a as u64,
                    v as i16,
                ) {
                    return HandlerResult::Suspend;
                }
            }

            return state_member_tap::handle_tap_member(
                state,
                db,
                ctx,
                instr,
                instr_ip,
                target_p_idx,
                a,
                resolved_slot as i32,
            );
        }
        O_TAP_OPPONENT => {
            return state_member_tap::handle_tap_opponent(state, db, ctx, instr, instr_ip, a, v);
        }
        O_MOVE_MEMBER => {
            return state_member_position::handle_move_member(
                state, db, ctx, instr, instr_ip, p_idx, a, s, resolved_slot, slot_info,
            );
        }
        O_FORMATION_CHANGE => {
            return state_member_position::handle_formation_change(
                state, db, ctx, instr, instr_ip, p_idx, a, s, resolved_slot,
            );
        }
        O_PLACE_UNDER => {
            return state_member_position::handle_place_under(
                state, db, ctx, p_idx, a, resolved_slot,
            );
        }
        O_ADD_STAGE_ENERGY => {
            return state_member_position::handle_add_stage_energy(state, p_idx, v, resolved_slot);
        }
        O_GRANT_ABILITY => {
            return state_member_position::handle_grant_ability(
                state, p_idx, ctx.source_card_id, v, target_slot, resolved_slot,
            );
        }
        O_PLAY_MEMBER_FROM_HAND => {
            return state_member_play::handle_play_member_from_hand(
                state, db, ctx, instr, instr_ip, p_idx, v, a, s,
            );
        }
        O_PLAY_MEMBER_FROM_DISCARD => {
            return state_member_play::handle_play_member_from_discard(
                state,
                db,
                ctx,
                instr,
                instr_ip,
                p_idx,
                v,
                a,
                s,
                target_slot,
                resolved_slot,
            );
        }
        O_INCREASE_COST => {
            state.players[p_idx].cost_modifiers.push((
                crate::core::logic::Condition {
                    condition_type: ConditionType::None,
                    value: 0,
                    attr: 0,
                    target_slot: 0,
                    is_negated: false,
                    params: serde_json::Value::Null,
                },
                v,
            ));
        }
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}


