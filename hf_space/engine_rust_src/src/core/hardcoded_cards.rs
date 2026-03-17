//! Hardcoded card IDs and ability indices for special rule handling
//! 
//! These are extracted from the hardcoded_abilities() match statement.
//! Cards listed here have special-case implementations rather than being
//! decoded from compiled bytecode.

// Card IDs with hardcoded rule implementations
pub const CARD_HARDCODED_ENERGY_PAY_1: &[i32] = &[
    64,      // Nikoniko smile
    159,     // Another outfit
    682,     // Summer costume
    163,     // Member-specific
    688,     // Member-specific
    234,     // Member-specific
    4330,    // Member-specific
    309,     // Member-specific
    472,     // Member-specific
    473,     // Member-specific
    474,     // Member-specific
    501,     // Member-specific
    4597,    // Member-specific
    542,     // Member-specific
    545,     // Member-specific
];

pub const CARD_HARDCODED_ENERGY_PAY_0: &[i32] = &[
    577,     // Special case (no energy cost)
];

pub const CARD_HARDCODED_ENERGY_PAY_1_AB_1: &[i32] = &[
    722,     // Member-specific ability 1
    873,     // Member-specific ability 1
    882,     // Member-specific ability 1
    4978,    // Member-specific ability 1
];

// Ability indices
pub const ABILITY_IDX_0: usize = 0;
pub const ABILITY_IDX_1: usize = 1;

/// Get the energy cost for a hardcoded ability, if one exists
/// Returns `Some(energy_cost)` if the card/ability pair is hardcoded, or `None`
pub fn get_hardcoded_energy_cost(card_id: i32, ability_idx: usize) -> Option<i32> {
    // Ability 0 with 1 energy cost
    if ability_idx == ABILITY_IDX_0 && CARD_HARDCODED_ENERGY_PAY_1.contains(&card_id) {
        return Some(1);
    }
    
    // Ability 0 with 0 energy cost
    if ability_idx == ABILITY_IDX_0 && CARD_HARDCODED_ENERGY_PAY_0.contains(&card_id) {
        return Some(0);
    }
    
    // Ability 1 with 1 energy cost
    if ability_idx == ABILITY_IDX_1 && CARD_HARDCODED_ENERGY_PAY_1_AB_1.contains(&card_id) {
        return Some(1);
    }
    
    None
}
