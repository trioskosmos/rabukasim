use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::{ActionReceiver, CardDatabase, GameState};

pub struct MulliganGenerator;

impl ActionGenerator for MulliganGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        _db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let player = &state.players[p_idx];
        // Action 0: Confirm
        receiver.add_action(0);
        // Actions 300+i: Toggle card at hand position i
        for (i, &_cid) in player.hand.iter().enumerate() {
            // Only legal if NOT already selected
            if (player.mulligan_selection >> i) & 1 == 0 {
                receiver.add_action((crate::core::logic::ACTION_BASE_MULLIGAN + i as i32) as usize);
            }
        }
    }
}
