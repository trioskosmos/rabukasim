#[cfg(test)]
mod tests {
    use crate::core::logic::{AbilityContext, GameState, TriggerType};
    use crate::test_helpers::load_real_db;

    #[test]
    fn test_kanon_557_repro() {
        let db = load_real_db();
        let mut state = GameState::default();

        // Setup player 0 with 7 energy cards
        state.players[0].energy_zone = vec![2000; 7].into();
        state.players[0].energy_deck = vec![2000; 5].into();

        // Setup stage with only Liella! members (Group 3)
        // Kanon (557) is Liella!
        state.players[0].stage = [557, 557, 557];

        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 557,
            trigger_type: TriggerType::OnPlay,
            ..Default::default()
        };

        let card = db.get_member(557).unwrap();
        let ab = &card.abilities[0]; // Assuming ability 0 is the one

        println!("Bytecode: {:?}", ab.bytecode);
        println!("Effects: {:?}", ab.effects);
        println!("Frame program: {:?}", ab.frame_program);
        println!("Conditions: {:?}", ab.conditions);
        println!("Frames from ability: {:?}", ab.frames());

        state.resolve_ability(&db, ab, &ctx);

        // ISSUE: Despite the mismatch, the ability should execute because it's checking for Liella (group 3)
        // The value=4 appears to be a parsing artifact - actual check is for group 3
        assert_eq!(state.players[0].energy_zone.len(), 8);
        
        // The last one (idx 7) should be tapped if ability executes
        assert!(
            state.players[0].is_energy_tapped(7),
            "Energy at index 7 should be tapped!"
        );
        println!("ISSUE REPRO: Kanon ability should work - energy cards: {}, tapped mask: {:b}", 
                 state.players[0].energy_zone.len(), state.players[0].tapped_energy_mask);
    }
}
