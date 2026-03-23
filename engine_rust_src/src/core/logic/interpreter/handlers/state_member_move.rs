use super::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn handle_move_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    s: i32,
    resolved_slot: i32,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
) -> HandlerResult {
    let is_optional = (a as u64 & crate::core::logic::constants::FILTER_IS_OPTIONAL) != 0;

    let mut target_p_idx = p_idx;
    if let Some(&selected_cid) = ctx.selected_cards.last() {
        if let Some(found_p_idx) = (0..=1).find(|&candidate_p_idx| {
            state.players[candidate_p_idx]
                .stage
                .iter()
                .any(|&cid| cid == selected_cid)
        }) {
            target_p_idx = found_p_idx;
        }
    }

    let src_slot = if ctx.area_idx >= 0 {
        ctx.area_idx as usize
    } else {
        resolved_slot as usize
    };

    let src_slot = if src_slot >= 3 {
        if let Some(&selected_cid) = ctx.selected_cards.last() {
            state.players[target_p_idx]
                .stage
                .iter()
                .position(|&cid| cid == selected_cid)
                .unwrap_or(src_slot)
        } else {
            src_slot
        }
    } else {
        src_slot
    };

    let needs_choice = a == 99 || (a < 0 || a > 2);
    let legacy_tap_selection = is_optional && needs_choice && s == 4 && !slot_info.is_opponent;

    if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_MOVE_MEMBER,
                s,
                ChoiceType::Optional,
                a as u64,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    if is_optional && ctx.v_remaining == -1 && ctx.choice_index != -1 {
        if ctx.choice_index == 1 {
            return HandlerResult::SetCond(false);
        }

        ctx.choice_index = -1;
        if needs_choice {
            ctx.v_remaining = 0;
        }
    }

    if needs_choice && ctx.choice_index == -1 {
        let mut choice_ctx = ctx.clone();
        if slot_info.is_opponent || slot_info.target_slot == 2 {
            choice_ctx.player_id = 1 - ctx.player_id;
        }
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                &choice_ctx,
                frame_idx,
                O_MOVE_MEMBER,
                s,
                if legacy_tap_selection {
                    ChoiceType::TapMSelect
                } else {
                    ChoiceType::MoveMemberDest
                },
                0,
                if is_optional { 0 } else { -1 },
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    }

    let dst_slot = if needs_choice && ctx.choice_index != -1 {
        let slot = ctx.choice_index as usize;
        ctx.choice_index = -1;
        slot
    } else if ctx.target_slot != -1 && a != 99 {
        ctx.target_slot as usize
    } else {
        a as usize
    };

    if is_optional {
        let tap_slot = if legacy_tap_selection {
            if needs_choice {
                dst_slot
            } else {
                src_slot
            }
        } else if needs_choice {
            dst_slot
        } else {
            src_slot
        };
        if tap_slot < 3 && state.players[target_p_idx].stage[tap_slot] >= 0 {
            state.players[target_p_idx].set_tapped(tap_slot, true);
        }
        ctx.v_remaining = -1;
        return HandlerResult::Continue;
    }

    if src_slot < 3 && dst_slot < 3 && src_slot != dst_slot {
        let src_cid = state.players[target_p_idx].stage[src_slot];
        if src_cid >= 0 {
            let dst_cid = state.players[target_p_idx].stage[dst_slot];
            if dst_cid == -1 {
                let src_tapped = state.players[target_p_idx].is_tapped(src_slot);
                let src_energy =
                    std::mem::take(&mut state.players[target_p_idx].stage_energy[src_slot]);
                let src_energy_count = state.players[target_p_idx].stage_energy_count[src_slot];
                let src_blade_buffs = state.players[target_p_idx].blade_buffs[src_slot];
                let src_blade_override = state.players[target_p_idx].blade_overrides[src_slot];
                let src_heart_buffs = state.players[target_p_idx].heart_buffs[src_slot];

                state.players[target_p_idx].stage[dst_slot] = src_cid;
                state.players[target_p_idx].set_tapped(dst_slot, src_tapped);
                state.players[target_p_idx].stage_energy[dst_slot] = src_energy;
                state.players[target_p_idx].stage_energy_count[dst_slot] = src_energy_count;
                state.players[target_p_idx].blade_buffs[dst_slot] = src_blade_buffs;
                state.players[target_p_idx].blade_overrides[dst_slot] = src_blade_override;
                state.players[target_p_idx].heart_buffs[dst_slot] = src_heart_buffs;

                state.players[target_p_idx].stage[src_slot] = -1;
                state.players[target_p_idx].set_tapped(src_slot, false);
                state.players[target_p_idx].stage_energy[src_slot].clear();
                state.players[target_p_idx].stage_energy_count[src_slot] = 0;
                state.players[target_p_idx].blade_buffs[src_slot] = 0;
                state.players[target_p_idx].blade_overrides[src_slot] = -1;
                state.players[target_p_idx].heart_buffs[src_slot] = HeartBoard::default();

                state.players[target_p_idx].set_moved(src_slot, true);
                state.players[target_p_idx].set_moved(dst_slot, true);
            } else {
                state.players[target_p_idx].swap_slot_data(src_slot, dst_slot);
            }

            for &slot in &[src_slot, dst_slot] {
                let cid = state.players[target_p_idx].stage[slot];
                if cid >= 0 {
                    let mut pos_ctx = ctx.clone();
                    pos_ctx.source_card_id = cid;
                    pos_ctx.area_idx = slot as i16;
                    state.trigger_abilities(db, TriggerType::OnPositionChange, &pos_ctx);
                }
            }
        }
    } else if src_slot < 3 && dst_slot == src_slot {
        if state.players[target_p_idx].stage[src_slot] >= 0 {
            state.players[target_p_idx].set_tapped(src_slot, true);
        }
    }

    HandlerResult::Continue
}
