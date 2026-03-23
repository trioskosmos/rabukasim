use super::*;
use crate::core::logic::models::AbilityFrame;
use smallvec::SmallVec;

#[allow(clippy::too_many_arguments)]
pub fn finalize_look_choice(
    state: &mut GameState,
    _db: &CardDatabase,
    _ctx: &mut AbilityContext,
    p_idx: usize,
    _slot_info: crate::core::logic::interpreter::instruction::DecodedSlot,
    _target_slot: u8,
    rem_dest: u8,
    source_zone: i32,
    _reveal_flag: bool,
    dest_discard_v: bool,
    _a: i64,
    _s: i32,
    revealed: &mut SmallVec<[i32; 16]>,
) -> HandlerResult {
    revealed.retain(|c| *c != -1);
    if !revealed.is_empty() {
        let dest = if dest_discard_v {
            7
        } else if rem_dest > 0 {
            rem_dest as i32
        } else {
            source_zone
        };
        match dest {
            6 => {
                for cid in revealed.drain(..) {
                    state.players[p_idx].push_hand_card(cid);
                }
            }
            7 => state.players[p_idx].discard.extend(revealed.drain(..)),
            15 => state.players[p_idx].yell_cards.extend(revealed.drain(..)),
            0 | 8 => {
                state.players[p_idx].deck.extend(revealed.drain(..));
                let mut rng = Pcg64::from_os_rng();
                state.players[p_idx].deck.shuffle(&mut rng);
            }
            _ => state.players[p_idx].discard.extend(revealed.drain(..)),
        }
    }

    HandlerResult::Continue
}
