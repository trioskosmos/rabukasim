use super::*;

pub fn handle_place_energy_under_member(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    p_idx: usize,
    instr: &BytecodeInstruction,
    a: i64,
) -> HandlerResult {
    let slot_info = instr.slot();
    let src_zone = slot_info.source_zone as u8;
    let slot = if ctx.area_idx >= 0 { ctx.area_idx as usize } else { 0 };

    let is_optional = (a as u64 & FILTER_IS_OPTIONAL) != 0;
    if src_zone == 3 {
        if is_optional && ctx.choice_index == -1 && ctx.v_remaining == -1 {
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_PLACE_ENERGY_UNDER_MEMBER,
                0,
                ChoiceType::Optional,
                &choice_text,
                a as u64,
                -1,
            ) {
                return HandlerResult::Suspend;
            }
        }

        if ctx.choice_index == 99 {
            return HandlerResult::SetCond(false);
        }

        let mut next_ctx = ctx.clone();
        if is_optional && ctx.choice_index != -1 && ctx.v_remaining == -1 {
            if ctx.choice_index == 1 {
                return HandlerResult::SetCond(false);
            }
            next_ctx.choice_index = -1;
            next_ctx.v_remaining = 1;
        }

        if next_ctx.choice_index == -1 {
            if state.players[p_idx].energy_zone.is_empty() {
                return HandlerResult::SetCond(false);
            }

            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                &next_ctx,
                instr_ip,
                O_PLACE_ENERGY_UNDER_MEMBER,
                0,
                ChoiceType::PayEnergy,
                &choice_text,
                a as u64,
                1,
            ) {
                return HandlerResult::Suspend;
            }
        }

        let idx = next_ctx.choice_index as usize;
        if idx >= state.players[p_idx].energy_zone.len() || slot >= 3 {
            return HandlerResult::SetCond(false);
        }

        let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
        state.players[p_idx].stage_energy[slot].push(energy_cid);
        return HandlerResult::SetCond(true);
    }

    if slot < 3 {
        match src_zone {
            7 => {
                if let Some(cid) = state.players[p_idx].pop_discard_card() {
                    state.players[p_idx].stage_energy[slot].push(cid);
                }
            }
            8 => {
                if let Some(cid) = state.players[p_idx].pop_deck_card() {
                    state.players[p_idx].stage_energy[slot].push(cid);
                }
            }
            0 => {
                if !state.players[p_idx].energy_zone.is_empty() {
                    let selected_idx = if ctx.choice_index >= 0 {
                        Some(ctx.choice_index as usize)
                    } else {
                        None
                    };

                    if let Some(idx) = selected_idx.filter(|&idx| idx < state.players[p_idx].energy_zone.len()) {
                        let energy_cid = state.players[p_idx].remove_energy_card(idx).unwrap();
                        state.players[p_idx].stage_energy[slot].push(energy_cid);
                    } else {
                        let energy_cid = state.players[p_idx].remove_energy_card(0).unwrap();
                        state.players[p_idx].stage_energy[slot].push(energy_cid);
                    }
                } else if let Some(cid) = state.players[p_idx].pop_deck_card() {
                    state.players[p_idx].stage_energy[slot].push(cid);
                }
            }
            _ => {
                if !state.players[p_idx].energy_zone.is_empty() {
                    for i in 0..state.players[p_idx].energy_zone.len() {
                        if !state.players[p_idx].is_energy_tapped(i) {
                            let energy_cid =
                                state.players[p_idx].remove_energy_card(i).unwrap();
                            state.players[p_idx].stage_energy[slot].push(energy_cid);
                            break;
                        }
                    }
                }
            }
        }
    }
    HandlerResult::Continue
}
