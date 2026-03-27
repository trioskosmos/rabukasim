use super::*;
use crate::core::logic::interpreter::logging;
use crate::core::logic::models::AbilityFrame;

pub fn handle_activate_energy(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let mut count = 0;
    let mut group_bits = 0u32;
    if let Some(card) = db.get_member(ctx.source_card_id) {
        if state.debug.debug_mode {
            println!(
                "[ENERGY_DEBUG] source_card_id={} card_no={} groups={:?} {}",
                ctx.source_card_id,
                card.card_no,
                card.groups,
                logging::describe_context(ctx)
            );
        }
        for &g in &card.groups {
            if g < 32 {
                group_bits |= 1 << g;
            }
        }
    } else if state.debug.debug_mode {
        println!(
            "[ENERGY_DEBUG] card NOT FOUND for id={} {}",
            ctx.source_card_id,
            logging::describe_context(ctx)
        );
    }

    for i in 0..state.players[p_idx].energy_zone.len() {
        if count >= v {
            break;
        }
        if state.players[p_idx].is_energy_tapped(i) {
            if state.debug.debug_mode {
                println!(
                    "[DEBUG-ENERGY] Untapping energy card {} for player {} {}",
                    i,
                    p_idx,
                    logging::describe_context(ctx)
                );
            }
            state.players[p_idx].set_energy_tapped(i, false);
            state.players[p_idx].activated_energy_group_mask |= group_bits;
            count += 1;
        }
    }
    if state.debug.debug_mode {
        println!(
            "[DEBUG-ENERGY] O_ACTIVATE_ENERGY: Untapped {}/{} cards. Mask now: {:b} {}",
            count,
            v,
            state.players[p_idx].tapped_energy_mask,
            logging::describe_context(ctx)
        );
        println!(
            "[DEBUG-ENERGY] activation masks energy={:b} member={:b} played={:b} {}",
            state.players[p_idx].activated_energy_group_mask,
            state.players[p_idx].activated_member_group_mask,
            state.players[p_idx].played_group_mask,
            logging::describe_context(ctx)
        );
    }
    HandlerResult::Continue
}

pub fn handle_pay_energy_dynamic(state: &mut GameState, p_idx: usize, v: i32) -> HandlerResult {
    let base_score = state.players[p_idx].score as i32;
    let total_cost = (base_score + v) as usize;

    if state.debug.debug_mode {
        println!(
            "[DEBUG] O_PAY_ENERGY_DYNAMIC: base_score={} v={} total_cost={}",
            base_score,
            v,
            total_cost
        );
    }

    let available = (0..state.players[p_idx].energy_zone.len())
        .filter(|&i| !state.players[p_idx].is_energy_tapped(i))
        .count();

    if available < total_cost {
        return HandlerResult::SetCond(false);
    }

    let mut paid = 0;
    for i in 0..state.players[p_idx].energy_zone.len() {
        if paid >= total_cost {
            break;
        }
        if !state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, true);
            paid += 1;
        }
    }
    HandlerResult::SetCond(true)
}
