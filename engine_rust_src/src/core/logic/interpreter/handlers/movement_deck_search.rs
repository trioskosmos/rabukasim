use crate::core::logic::models::AbilityFrame;
use super::*;
use rand::seq::SliceRandom;
use rand::SeedableRng;
use rand_pcg::Pcg64;

#[allow(clippy::too_many_arguments)]
pub fn handle_search_deck(
    state: &mut GameState,
    db: &CardDatabase,
    ctx: &mut AbilityContext,
    p_idx: usize,
    s: i32,
    a: i64,
    resolved_slot: i32,
) -> HandlerResult {
    let search_target = ctx.target_slot as usize;
    if search_target < state.players[p_idx].deck.len() {
        let cid = state.players[p_idx].remove_deck_card(search_target).unwrap();
        match s {
            4 => {
                let slot = (a as u64 & FILTER_MASK_LOWER) as usize;
                if slot < 3 {
                    if let Some(old) = state.handle_member_leaves_stage(p_idx, slot, db, ctx) {
                        state.players[p_idx].push_discard_card(old);
                    }
                    state.players[p_idx].stage[slot] = cid;
                    state.players[p_idx].set_tapped(slot, false);
                    state.players[p_idx].set_moved(slot, true);
                    state.register_played_member(p_idx, cid, db);
                    let new_ctx = AbilityContext {
                        source_card_id: cid,
                        player_id: p_idx as u8,
                        activator_id: p_idx as u8,
                        area_idx: slot as i16,
                        ..Default::default()
                    };
                    state.trigger_abilities(db, TriggerType::OnPlay, &new_ctx);
                } else {
                    state.players[p_idx].gain_hand_card(cid);
                }
            }
            13 => {
                state.players[p_idx].success_lives.push(cid);
            }
            _ => {
                state.players[p_idx].gain_hand_card(cid);
            }
        }
        let mut rng = Pcg64::from_os_rng();
        state.players[p_idx].deck.shuffle(&mut rng);
    }

    let _ = resolved_slot;
    HandlerResult::Continue
}
