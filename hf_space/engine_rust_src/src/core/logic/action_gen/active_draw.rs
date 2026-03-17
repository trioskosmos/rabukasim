use crate::core::logic::action_gen::ActionGenerator;
use crate::core::logic::{ActionReceiver, CardDatabase, GameState, Phase};

pub struct ActiveDrawGenerator;

impl ActionGenerator for ActiveDrawGenerator {
    fn generate<R: ActionReceiver + ?Sized>(
        &self,
        _db: &CardDatabase,
        p_idx: usize,
        state: &GameState,
        receiver: &mut R,
    ) {
        let player = &state.players[p_idx];
        if state.phase == Phase::LiveResult && state.live_result_selection_pending {
            // Hide Action 0 if mandatory choice is active
        } else {
            receiver.add_action(0);
        }
        if state.phase == Phase::LiveResult {
            // Selection choices (600-602)
            for i in 0..3 {
                if player.live_zone[i] >= 0 {
                    receiver.add_action(600 + i);
                }
            }
        }
    }
}
