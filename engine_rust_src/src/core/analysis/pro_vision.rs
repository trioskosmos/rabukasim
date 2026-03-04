use crate::core::logic::{CardDatabase, GameState, PlayerState};

/// AlphaZero Analysis Utilities
/// 
/// Contains mathematical and statistical logic for generating AlphaZero analytical hints (Pro Vision).
/// Keeps AI-specific calculations out of the core GameState logic.

pub struct ProVisionHints {
    pub win_probabilities: [f32; 3], // Slots 70-72
    pub deck_distribution: [f32; 7], // Slots 73-79
    pub energy_projection: f32,       // Slot 80
}

impl ProVisionHints {
    pub fn calculate(state: &GameState, db: &CardDatabase, player_idx: usize) -> Self {
        let player = &state.core.players[player_idx];
        
        Self {
            win_probabilities: calculate_win_probabilities(state, db, player_idx),
            deck_distribution: calculate_deck_distribution(player, db),
            energy_projection: project_energy(state, player_idx),
        }
    }
}

/// Calculate win probability for current live slots.
/// Currently a baseline placeholder for a future exact PerformanceProbabilitySolver.
fn calculate_win_probabilities(_state: &GameState, _db: &CardDatabase, _player_idx: usize) -> [f32; 3] {
    // TODO: Integrate exact PerformanceProbabilitySolver logic
    [0.5, 0.5, 0.5]
}

/// Calculate distribution of heart colors in the remaining deck.
fn calculate_deck_distribution(player: &PlayerState, db: &CardDatabase) -> [f32; 7] {
    let mut counts = [0.0; 7];
    let deck_size = player.deck.len();
    
    if deck_size == 0 {
        return counts;
    }

    for &cid in &player.deck {
        if let Some(member) = db.get_member(cid) {
            for i in 0..7 {
                if member.hearts[i] > 0 {
                    counts[i] += 1.0;
                }
            }
        }
    }

    for i in 0..7 {
        counts[i] /= deck_size as f32;
    }
    
    counts
}

/// Project next turn energy.
/// Normalizes to max energy 12.
fn project_energy(state: &GameState, player_idx: usize) -> f32 {
    let player = &state.core.players[player_idx];
    let energy_deck_count = player.energy_deck.len();
    let current_energy = player.energy_zone.len();
    
    if energy_deck_count > 0 {
        ((current_energy + 1) as f32 / 12.0).min(1.0)
    } else {
        (current_energy as f32 / 12.0).min(1.0)
    }
}
