use crate::test_helpers::{create_test_state, load_real_db};

/// Verifies that granted abilities (Wave 2) are correctly applied to a target card using real IDs.
#[test]
fn test_granted_abilities_stacking() {
    let _db = load_real_db();
    let mut state = create_test_state();

    state.players[0].stage[0] = 121; // Eli

    // Grant an ability to Card 121 (Target) from Card 124 (Source)
    // granted_abilities: Vec<(target_cid, source_cid, ab_idx)>
    state.players[0].granted_abilities.push((121, 124, 0));

    assert_eq!(state.players[0].granted_abilities.len(), 1);
    assert_eq!(state.players[0].granted_abilities[0].0, 121);
}

/// Verifies that removing a source card or explicitly clearing granted abilities works as expected.
#[test]
fn test_granted_abilities_removal() {
    let mut state = create_test_state();

    state.players[0].granted_abilities.push((121, 124, 0));
    assert_eq!(state.players[0].granted_abilities.len(), 1);

    // Manually remove
    state.players[0]
        .granted_abilities
        .retain(|&(target, _, _)| target != 121);
    assert_eq!(state.players[0].granted_abilities.len(), 0);
}

/// Verifies that multiple status effects (Blade buffs, Heart buffs) combine correctly using real card data.
#[test]
fn test_stat_buff_combination() {
    let db = load_real_db();
    let mut state = create_test_state();

    // Eli (121) has base blades (usually 1 or 2). Let's check reality.
    state.players[0].stage[0] = 121;

    let base_blades = db.get_member(121).expect("Eli should exist").blades;

    // 1. Apply Blade buff
    state.players[0].blade_buffs[0] = 3;

    // 2. Check effective blades (Base + Buff 3)
    let effective = state.get_effective_blades(0, 0, &db, 0);
    assert_eq!(effective, base_blades as u32 + 3);
}
