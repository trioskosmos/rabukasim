use crate::core::logic::{GameState};

#[inline]
pub fn discard_current_yell_pile(state: &mut GameState, p_idx: usize) -> usize {
    let current_yell = std::mem::take(&mut state.players[p_idx].yell_cards);
    let removed_count = current_yell.len();
    for cid in current_yell {
        for slot in 0..3 {
            if let Some(pos) = state.players[p_idx].stage_energy[slot]
                .iter()
                .position(|&energy_cid| energy_cid == cid)
            {
                state.players[p_idx].stage_energy[slot].remove(pos);
                state.players[p_idx].sync_stage_energy_count(slot);
                break;
            }
        }
        state.players[p_idx].push_discard_card(cid);
    }
    removed_count
}
