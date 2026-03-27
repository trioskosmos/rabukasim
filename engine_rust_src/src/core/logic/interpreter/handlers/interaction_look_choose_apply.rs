use super::*;
use crate::core::logic::models::AbilityFrame;

#[allow(clippy::too_many_arguments)]
pub fn apply_look_choice(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    target_slot: u8,
    source_zone: i32,
    reveal_flag: bool,
    chosen: i32,
) {
    let destination = if target_slot > 0 {
        target_slot as i32
    } else {
        6
    };
    match destination {
        7 => state.players[p_idx].push_discard_card(chosen),
        8 => state.players[p_idx].push_deck_card(chosen),
        4 => {
            let slot = slot_info.target_slot as usize;
            if slot < 3 {
                if let Some(cid) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                    state.players[p_idx].push_discard_card(cid as i32);
                }
                state.players[p_idx].stage[slot] = chosen;
                if slot_info.is_wait {
                    state.players[p_idx].set_tapped(slot, true);
                }
                state.players[p_idx].set_moved(slot, true);
                state.register_played_member(p_idx, chosen, db);
                let new_ctx = AbilityContext {
                    source_card_id: chosen,
                    player_id: p_idx as u8,
                    activator_id: p_idx as u8,
                    area_idx: slot as i16,
                    ..Default::default()
                };
                state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
            } else {
                state.players[p_idx].gain_hand_card(chosen);
            }
        }
        13 => state.players[p_idx].success_lives.push(chosen),
        _ => state.players[p_idx].push_hand_card(chosen),
    }

    if reveal_flag {
        if !state.players[p_idx].revealed_cards.contains(&chosen) {
            state.players[p_idx].revealed_cards.push(chosen);
        }
        let new_ctx = AbilityContext {
            source_card_id: chosen,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            ..Default::default()
        };
        state.trigger_abilities(db, TriggerType::OnReveal, &new_ctx);
    }

    if source_zone == 15 {
        for slot in 0..3 {
            if let Some(pos) = state.players[p_idx].stage_energy[slot]
                .iter()
                .position(|&c| c == chosen)
            {
                state.players[p_idx].stage_energy[slot].remove(pos);
                state.players[p_idx].sync_stage_energy_count(slot);
                break;
            }
        }
    }
}
