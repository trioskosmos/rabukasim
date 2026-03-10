use crate::core::enums::*;
use crate::core::logic::constants::{FILTER_MASK_LOWER, DYNAMIC_VALUE};
use crate::core::logic::{AbilityContext, CardDatabase, GameState, TriggerType};
use crate::core::logic::interpreter::conditions::resolve_count;
use crate::core::models::interpreter::{resolve_target_slot, get_choice_text};
use crate::core::models::suspend_interaction;
use super::HandlerResult;

pub fn handle_meta_control(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr: &super::super::instruction::BytecodeInstruction,
    instr_ip: usize,
) -> HandlerResult {
    let op = instr.op;
    let v = instr.v;
    let a = instr.a;
    let s = instr.raw_s;
    let base_p = ctx.activator_id as usize;
    let p_idx = ctx.player_id as usize;
    let target_slot = instr.s.target_slot as i32;

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
                println!("[DEBUG] CALC_SUM_COST: total_sum={}, cards={:?}", sum, ctx.selected_cards);
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
                    state.players[p_idx].negated_triggers.push((
                        cid,
                        trigger_type,
                        (a as u64 & FILTER_MASK_LOWER).max(1) as i32,
                    ));
                }
            }
        }
        O_LOSE_EXCESS_HEARTS => {
            state.players[p_idx].excess_hearts = 0;
        }
        O_DIV_VALUE => {
            if v > 1 {
                ctx.v_accumulated /= v as i16;
            }
        }
        O_RESTRICTION => {
            state.players[p_idx]
                .restrictions
                .push((a as u64 & FILTER_MASK_LOWER) as u8);
            if (a as u64 & FILTER_MASK_LOWER) == 1 {
                state.players[p_idx].set_flag(
                    crate::core::logic::player::PlayerState::FLAG_CANNOT_LIVE,
                    true,
                );
            }
        }
        O_SELECT_MEMBER | O_SELECT_LIVE | O_SELECT_PLAYER => {
            let area_val = (s >> 29) & 0x07;
            if area_val >= 1 && area_val <= 3 {
                let auto_slot = (area_val - 1) as i16;
                ctx.choice_index = auto_slot;
                ctx.area_idx = auto_slot;
                if state.debug.debug_mode {
                    println!(
                        "[DEBUG] O_SELECT_MEMBER: Auto-selecting slot {} based on area bits",
                        auto_slot
                    );
                }
            } else if ctx.choice_index == -1 {
                let choice_type = match op {
                    O_SELECT_MEMBER => ChoiceType::SelectMember,
                    O_SELECT_LIVE => ChoiceType::SelectLive,
                    O_SELECT_PLAYER => ChoiceType::SelectPlayer,
                    _ => ChoiceType::None,
                };
                let mut flip_ctx = ctx.clone();
                if s == 2 {
                    flip_ctx.player_id = 1 - (p_idx as u8);
                } else if s == 3 {
                    flip_ctx.player_id = 1;
                }
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    &flip_ctx,
                    instr_ip,
                    op,
                    s,
                    choice_type,
                    &choice_text,
                    a as u64,
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
            } else {
                let choice = ctx.choice_index as i32;
                let source_zone = instr.s.source_zone as u8;

                if source_zone == 6 || source_zone == 7 {
                    ctx.target_slot = choice as i16;
                } else {
                    ctx.target_slot = choice as i16;
                    ctx.area_idx = choice as i16;
                }
            }
        }
        O_OPPONENT_CHOOSE => {
            if ctx.choice_index == -1 {
                // Flip player_id BEFORE suspension so that the interaction is attributed to the opponent
                ctx.player_id = 1 - ctx.player_id;

                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_OPPONENT_CHOOSE,
                    0,
                    ChoiceType::OpponentChoose,
                    &choice_text,
                    0,
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
            } else {
                // On resumption, the player_id is already flipped
            }
        }
        O_PREVENT_ACTIVATE | O_PREVENT_BATON_TOUCH | O_PREVENT_SET_TO_SUCCESS_PILE
        | O_PREVENT_PLAY_TO_SLOT => {
            // These opcodes typically use bit 24 of s for opponent targeting in legacy,
            // or TargetType in some other variants.
            // We use standardized target_p_idx for these specifically.
            let filter_target = (a as u64) & 0x03;
            let target_p_idx = if filter_target == 2 || instr.s.is_opponent || target_slot == 2 {
                1 - base_p
            } else {
                base_p
            };

            if op == O_PREVENT_ACTIVATE {
                state.players[target_p_idx].prevent_activate = 1;
            } else if op == O_PREVENT_BATON_TOUCH {
                state.players[target_p_idx].prevent_baton_touch = 1;
            } else if op == O_PREVENT_SET_TO_SUCCESS_PILE {
                state.players[target_p_idx].prevent_success_pile_set = 1;
            } else if op == O_PREVENT_PLAY_TO_SLOT {
                let resolved_slot = if target_slot == 10 {
                    ctx.target_slot as i32
                } else {
                    resolve_target_slot(target_slot, ctx) as i32
                };
                if resolved_slot >= 0 && resolved_slot < 3 {
                    state.players[target_p_idx].prevent_play_to_slot_mask |= 1 << (resolved_slot as u8);
                }
            }
        }
        O_TRIGGER_REMOTE => {
            let target_cid = if target_slot >= 0 && target_slot < 3 {
                state.players[p_idx].stage[target_slot as usize]
            } else {
                -1
            };
            if target_cid >= 0 {
                if let Some(m) = db.get_member(target_cid as i32) {
                    if (v as usize) < m.abilities.len() {
                        return HandlerResult::BranchToBytecode(std::sync::Arc::new(
                            m.abilities[v as usize].bytecode.clone(),
                        ));
                    }
                }
            }
        }
        O_REDUCE_LIVE_SET_LIMIT => {
            state.players[p_idx].prevent_success_pile_set = state.players[p_idx]
                .prevent_success_pile_set
                .saturating_add(v as u8);
        }
        O_REDUCE_YELL_COUNT => {
            let mut final_v = v;
            if (a as u64 & DYNAMIC_VALUE) != 0 {
                final_v = resolve_count(
                    state,
                    db,
                    s,
                    a as u64 & !DYNAMIC_VALUE & FILTER_MASK_LOWER,
                    p_idx as i32,
                    ctx,
                    0,
                );
            }
            state.players[p_idx].yell_count_reduction = state.players[p_idx]
                .yell_count_reduction
                .saturating_add(final_v as i16);
        }
        O_META_RULE => {
            let target_p_idx = if instr.s.is_opponent || target_slot == 2 {
                1 - base_p
            } else {
                base_p
            };
            if a == 0 || a == 10 {
                state.players[target_p_idx].cheer_mod_count = state.players[target_p_idx]
                    .cheer_mod_count
                    .saturating_add(v as u16);
            } else if a == 8 {
                if v == 1 {
                    let all_active = state.players[p_idx].tapped_energy_count() == 0;
                    return HandlerResult::SetCond(all_active);
                }
            }
        }
        O_BATON_TOUCH_MOD => state.players[p_idx].baton_touch_limit = v as u8,
        O_IMMUNITY => state.players[p_idx].set_flag(
            crate::core::logic::player::PlayerState::FLAG_IMMUNITY,
            v != 0,
        ),
        O_COLOR_SELECT => {
            if ctx.choice_index == -1 {
                let choice_text = get_choice_text(db, ctx);
                if suspend_interaction(
                    state,
                    db,
                    ctx,
                    instr_ip,
                    O_COLOR_SELECT,
                    0,
                    ChoiceType::ColorSelect,
                    &choice_text,
                    0,
                    -1,
                ) {
                    return HandlerResult::Suspend;
                }
            } else {
                ctx.selected_color = ctx.choice_index;
            }
        }
        O_SWAP_AREA => {
            let target_p_idx = if instr.s.is_opponent || target_slot == 2 {
                1 - base_p
            } else {
                base_p
            };
            let p = &mut state.players[target_p_idx];
            let temp_stage = p.stage;
            let temp_energy = p.stage_energy_count;
            let temp_tapped = [p.is_tapped(0), p.is_tapped(1), p.is_tapped(2)];
            let temp_moved = [p.is_moved(0), p.is_moved(1), p.is_moved(2)];
            if v == 2 || (a == 1 && s == 0) {
                let src = ctx.area_idx as usize;
                let dst = a as usize;
                if src < 3 && dst < 3 {
                    p.stage[src] = temp_stage[dst];
                    p.stage[dst] = temp_stage[src];
                    p.stage_energy_count[src] = temp_energy[dst];
                    p.stage_energy_count[dst] = temp_energy[src];
                    p.set_tapped(src, temp_tapped[dst]);
                    p.set_tapped(dst, temp_tapped[src]);
                    p.set_moved(src, temp_moved[dst]);
                    p.set_moved(dst, temp_moved[src]);
                }
            } else {
                if s == 4 {
                    p.stage[0] = temp_stage[1];
                    p.stage[1] = temp_stage[2];
                    p.stage[2] = temp_stage[0];
                    p.stage_energy_count[0] = temp_energy[1];
                    p.stage_energy_count[1] = temp_energy[2];
                    p.stage_energy_count[2] = temp_energy[0];
                    p.set_tapped(0, temp_tapped[1]);
                    p.set_tapped(1, temp_tapped[2]);
                    p.set_tapped(2, temp_tapped[0]);
                    p.set_moved(0, temp_moved[1]);
                    p.set_moved(1, temp_moved[2]);
                    p.set_moved(2, temp_moved[0]);
                } else {
                    p.stage[0] = temp_stage[2];
                    p.stage[1] = temp_stage[0];
                    p.stage[2] = temp_stage[1];
                    p.stage_energy_count[0] = temp_energy[2];
                    p.stage_energy_count[1] = temp_energy[0];
                    p.stage_energy_count[2] = temp_energy[1];
                    p.set_tapped(0, temp_tapped[2]);
                    p.set_tapped(1, temp_tapped[0]);
                    p.set_tapped(2, temp_tapped[1]);
                    p.set_moved(0, temp_moved[2]);
                    p.set_moved(1, temp_moved[0]);
                    p.set_moved(2, temp_moved[1]);
                }
            }
        }
        O_REPEAT_ABILITY => {
            let max_repeats = v;
            if max_repeats == 0 || ctx.repeat_count < max_repeats as i16 {
                ctx.repeat_count = ctx.repeat_count.saturating_add(1);
                return HandlerResult::Branch(0);
            }
        }
        O_SET_TARGET_SELF => {
            ctx.player_id = ctx.activator_id;
        }
        O_SET_TARGET_OPPONENT => {
            ctx.player_id = 1 - ctx.activator_id ;
        }
        O_FLAVOR_ACTION => {
             if state.debug.debug_mode {
                println!("[DEBUG] FLAVOR_ACTION: v={}, a={}, s={}", v, a, s);
            }
        }
        _ => return HandlerResult::Continue,
    }
    HandlerResult::Continue
}
