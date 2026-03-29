use super::*;
use crate::core::hearts::HeartBoard;
use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn handle_formation_change(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    _frame: &AbilityFrame,
    frame_idx: usize,
    p_idx: usize,
    a: i64,
    s: i32,
    resolved_slot: i32,
) -> HandlerResult {
    let direct_dst_slot = if a >= 0 && a < 3 {
        Some(a as usize)
    } else if ctx.target_slot >= 0 && ctx.target_slot < 3 {
        Some(ctx.target_slot as usize)
    } else {
        None
    };

    if let Some(dst_slot) = direct_dst_slot {
        let src_slot = if ctx.area_idx >= 0 {
            ctx.area_idx as usize
        } else {
            resolved_slot as usize
        };

        if src_slot < 3 && dst_slot < 3 && src_slot != dst_slot {
            if state.players[p_idx].stage[dst_slot] == -1 {
                state.players[p_idx].move_slot_data(src_slot, dst_slot);
            } else {
                state.players[p_idx].swap_slot_data(src_slot, dst_slot);
            }

            for &slot in &[src_slot, dst_slot] {
                let cid = state.players[p_idx].stage[slot];
                if cid >= 0 {
                    let mut pos_ctx = ctx.clone();
                    pos_ctx.source_card_id = cid;
                    pos_ctx.area_idx = slot as i16;
                    state.trigger_abilities(db, TriggerType::OnPositionChange, &pos_ctx);
                }
            }
        }
    } else if ctx.choice_index == -1 {
        if matches!(
            suspend_choice(
                state,
                db,
                ctx,
                ctx,
                frame_idx,
                O_FORMATION_CHANGE,
                s,
                ChoiceType::RearrangeFormation,
                0,
                -1,
            ),
            HandlerResult::Suspend
        ) {
            return HandlerResult::Suspend;
        }
    } else {
        let perm_idx = ctx.choice_index as usize;
        ctx.choice_index = -1;

        if !state.ui.silent {
            state.log("Rule 11.10, Rule 11.10.1, Rule 11.10.2: Performing [フォーメーションチェンジ] (Formation Change).".to_string());
        }

        if perm_idx < 6 {
            let perms = [
                [0, 1, 2],
                [0, 2, 1],
                [1, 0, 2],
                [1, 2, 0],
                [2, 0, 1],
                [2, 1, 0],
            ];
            let p = perms[perm_idx];

            let old_data: Vec<_> = (0..3)
                .map(|i| {
                    (
                        state.players[p_idx].stage[i],
                        state.players[p_idx].is_tapped(i),
                        state.players[p_idx].stage_energy[i].clone(),
                    )
                })
                .collect();

            for (new_idx, &old_idx) in p.iter().enumerate() {
                state.players[p_idx].stage[new_idx] = old_data[old_idx].0;
                state.players[p_idx].set_tapped(new_idx, old_data[old_idx].1);
                state.players[p_idx].stage_energy[new_idx] = old_data[old_idx].2.clone();
                state.players[p_idx].set_moved(new_idx, true);
            }
        }
    }

    HandlerResult::Continue
}
