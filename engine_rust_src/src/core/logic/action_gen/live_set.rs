use crate::core::logic::{ActionReceiver, CardDatabase, GameState};
use crate::core::logic::action_gen::ActionGenerator;

pub struct LiveSetGenerator;

impl ActionGenerator for LiveSetGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, _db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R) {
        let player = &state.core.players[p_idx];
        receiver.add_action(0);
        if player.live_zone.iter().any(|&cid| cid == -1) {
            for (i, &_cid) in player.hand.iter().enumerate() {
                // Rule 8.2.2: Any card can be placed in the live zone.
                receiver.add_action((crate::core::logic::ACTION_BASE_LIVESET + i as i32) as usize);
            }
        }
    }
}
