#[cfg(test)]
mod tests {
    use crate::core::logic::{GameState, CardDatabase, AbilityContext, TriggerType};
    use crate::core::logic::interpreter::resolve_bytecode;
    use std::sync::Arc;

    #[test]
    fn test_kanon_557_repro() {
        let json = std::fs::read_to_string("../data/cards_compiled.json").unwrap();
        let db = CardDatabase::from_json(&json).unwrap();
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
        
        resolve_bytecode(&mut state, &db, Arc::new(ab.bytecode.clone()), &ctx);
        
        // Should have 8 energy cards now
        assert_eq!(state.players[0].energy_zone.len(), 8);
        
        // The last one (idx 7) should be tapped
        assert!(state.players[0].is_energy_tapped(7), "Energy at index 7 should be tapped!");
        println!("Tapped mask: {:b}", state.players[0].tapped_energy_mask);
    }
}
