use crate::core::logic::{GameState, CardDatabase, ActionReceiver, Phase};

pub mod active_draw;
pub mod live_set;
pub mod main_phase;
pub mod mulligan;
pub mod response;

pub trait ActionGenerator {
    fn generate<R: ActionReceiver + ?Sized>(&self, db: &CardDatabase, p_idx: usize, state: &GameState, receiver: &mut R);
}

pub struct ActionGeneratorFactory;

impl ActionGeneratorFactory {
    pub fn generate_actions<R: ActionReceiver + ?Sized>(state: &GameState, db: &CardDatabase, p_idx: usize, receiver: &mut R) {
        receiver.reset();

        if state.phase == Phase::Rps {
            if state.rps_choices[p_idx] == -1 {
                let offset = if p_idx == 0 { 10000 } else { 11000 };
                receiver.add_action(offset + 0); // Rock
                receiver.add_action(offset + 1); // Paper
                receiver.add_action(offset + 2); // Scissors
            }
            return;
        }

        if state.phase == Phase::TurnChoice {
            if p_idx == state.current_player as usize {
                receiver.add_action(GameState::ACTION_TURN_CHOICE_FIRST as usize);
                receiver.add_action(GameState::ACTION_TURN_CHOICE_SECOND as usize);
            }
            return;
        }

        match state.phase {
            Phase::Main => main_phase::MainPhaseGenerator.generate(db, p_idx, state, receiver),
            Phase::LiveSet => live_set::LiveSetGenerator.generate(db, p_idx, state, receiver),
            Phase::MulliganP1 | Phase::MulliganP2 => mulligan::MulliganGenerator.generate(db, p_idx, state, receiver),
            Phase::Active | Phase::Draw | Phase::LiveResult => active_draw::ActiveDrawGenerator.generate(db, p_idx, state, receiver),
            Phase::Response => response::ResponseGenerator.generate(db, p_idx, state, receiver),
            Phase::Energy => receiver.add_action(0),
            Phase::PerformanceP1 | Phase::PerformanceP2 | Phase::Terminal => receiver.add_action(0),
            _ => receiver.add_action(0),
        }
    }
}
