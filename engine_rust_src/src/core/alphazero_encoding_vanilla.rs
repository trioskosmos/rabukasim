use crate::core::logic::ai_encoding::GameStateEncoding;
use crate::core::logic::{CardDatabase, GameState};

pub trait AlphaZeroVanillaEncoding {
    fn to_vanilla_tensor(&self, db: &CardDatabase) -> Vec<f32>;
}

impl AlphaZeroVanillaEncoding for GameState {
    fn to_vanilla_tensor(&self, db: &CardDatabase) -> Vec<f32> {
        self.encode_state(db)
    }
}
