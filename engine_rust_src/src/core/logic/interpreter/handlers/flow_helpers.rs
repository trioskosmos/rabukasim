use crate::core::logic::models::AbilityFrame;
use crate::core::logic::{AbilityContext, CardDatabase, Effect, GameState};

pub fn current_effect<'a>(
    db: &'a CardDatabase,
    ctx: &AbilityContext,
    frame: &AbilityFrame,
) -> Option<&'a Effect> {
    let ab_idx = usize::try_from(ctx.ability_index).ok()?;
    db.get_live(ctx.source_card_id)
        .and_then(|card| card.abilities.get(ab_idx))
        .or_else(|| {
            db.get_member(ctx.source_card_id)
                .and_then(|card| card.abilities.get(ab_idx))
        })
        .and_then(|ability| {
            ability.effects.iter().find(|effect| {
                effect.runtime_opcode == frame.raw_opcode()
                    && effect.runtime_value == frame.raw_value()
                    && effect.runtime_attr == frame.raw_attr()
                    && effect.runtime_slot == frame.raw_slot()
            })
        })
}

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
