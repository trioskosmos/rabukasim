use crate::core::logic::{ActionReceiver, CardDatabase, GameState};
use crate::core::logic::action_gen::ActionGenerator;

pub struct MulliganGenerator;

impl ActionGenerator for MulliganGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, _db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R) {
        let player = &state.core.players[p_idx];
        // Action 0: Confirm
        receiver.add_action(0);
        // Actions 300-359: Toggle (One-way for AI to avoid loops)
        let hand_len = player.hand.len().min(60);
        for i in 0..hand_len {
            // Only legal if NOT already selected
            if (player.mulligan_selection >> i) & 1 == 0 {
                receiver.add_action((crate::core::logic::ACTION_BASE_MULLIGAN + i as i32) as usize);
            }
        }
    }
}
