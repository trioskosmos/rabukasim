use super::*;

pub fn handle_energy_charge(
    state: &mut GameState,
    p_idx: usize,
    slot: crate::core::logic::interpreter::instruction::DecodedSlot,
    v: i32,
) -> HandlerResult {
    let target_p = if slot.is_opponent { 1 - p_idx } else { p_idx };
    let is_wait = slot.is_wait;
    for _ in 0..v {
        if let Some(cid) = state.players[target_p].energy_deck.pop() {
            state.players[target_p].push_energy_card(cid, is_wait);
        }
    }
    HandlerResult::Continue
}

pub fn handle_pay_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    instr_ip: usize,
    p_idx: usize,
    instr: &BytecodeInstruction,
    v: i32,
) -> HandlerResult {
    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count() as i32;

    let is_optional = instr.filter_attr().is_optional;
    if is_optional && ctx.choice_index == -1 {
        if available < v {
            if state.debug.debug_mode && !state.ui.silent {
                println!("[DEBUG] O_PAY_ENERGY: cannot afford optional cost.");
            }
            return HandlerResult::SetCond(false);
        } else {
            if state.debug.debug_mode {
                println!(
                    "[DEBUG] O_PAY_ENERGY: attempting optional suspension (instr_ip={}).",
                    instr_ip
                );
            }
            let choice_text = get_choice_text(db, ctx);
            if suspend_interaction(
                state,
                db,
                ctx,
                instr_ip,
                O_PAY_ENERGY,
                0,
                ChoiceType::Optional,
                &choice_text,
                instr.filter_attr().to_attr(),
                -1,
            ) {
                return HandlerResult::Suspend;
            }
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
        next_ctx.v_remaining = v as i16;
    }

    if next_ctx.choice_index == 99 {
        return HandlerResult::SetCond(false);
    } else if available < v {
        return HandlerResult::SetCond(false);
    } else if next_ctx.choice_index != -1 {
        let idx = next_ctx.choice_index as usize;
        if idx < state.players[p_idx].energy_zone.len() && !state.players[p_idx].is_energy_tapped(idx)
        {
            state.players[p_idx].set_energy_tapped(idx, true);
            next_ctx.v_remaining -= 1;
            if next_ctx.v_remaining > 0 {
                next_ctx.choice_index = -1;
                if suspend_interaction(
                    state,
                    db,
                    &next_ctx,
                    instr_ip,
                    O_PAY_ENERGY,
                    0,
                    ChoiceType::PayEnergy,
                    "",
                    0,
                    next_ctx.v_remaining,
                ) {
                    return HandlerResult::Suspend;
                }
            }
        }
    } else {
        let mut paid = 0;
        let player = &mut state.players[p_idx];
        for i in 0..player.energy_zone.len() {
            if paid >= v {
                break;
            }
            if !player.is_energy_tapped(i) {
                player.set_energy_tapped(i, true);
                paid += 1;
            }
        }
    }
    HandlerResult::SetCond(true)
}
