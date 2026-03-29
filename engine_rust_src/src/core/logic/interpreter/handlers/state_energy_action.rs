use super::*;
use crate::core::logic::models::AbilityFrame;

pub fn handle_activate_energy(
    state: &mut GameState,
    _db: &CardDatabase,
    ctx: &AbilityContext,
    p_idx: usize,
    v: i32,
) -> HandlerResult {
    let mut count = 0;
    let mut group_bits = 0u32;
    if let Some(card) = _db.get_member(ctx.source_card_id) {
        for &g in &card.groups {
            if g < 32 {
                group_bits |= 1 << g;
            }
        }
    }

    for i in 0..state.players[p_idx].energy_zone.len() {
        if count >= v {
            break;
        }
        if state.players[p_idx].is_energy_tapped(i) {
            state.players[p_idx].set_energy_tapped(i, false);
            state.players[p_idx].activated_energy_group_mask |= group_bits;
            count += 1;
        }
    }
    HandlerResult::Continue
}

pub fn handle_pay_energy_dynamic(state: &mut GameState, p_idx: usize, v: i32) -> HandlerResult {
    let base_score = state.players[p_idx].score as i32;
    let total_cost = (base_score + v) as usize;

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
