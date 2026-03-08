#[cfg(test)]
mod vanilla_encoding_tests {
    use crate::core::alphazero_encoding_vanilla::{AlphaZeroVanillaEncoding, AZ_VANILLA_TOTAL_INPUT};

    #[test]
    fn test_vanilla_encoding_size() {
        let game = crate::test_helpers::create_test_state();
        let db = crate::test_helpers::load_real_db();
        let tensor = game.to_vanilla_tensor(&db);
        assert_eq!(tensor.len(), AZ_VANILLA_TOTAL_INPUT, "Vanilla tensor size mismatch");
        assert_eq!(tensor.len(), 800, "Expected exactly 800 floats");
    }

    #[test]
    fn test_vanilla_encoding_content() {
        let game = crate::test_helpers::create_test_state();
        let db = crate::test_helpers::load_real_db();
        let tensor = game.to_vanilla_tensor(&db);
        
        // Index 0: Phase
        assert_eq!(tensor[0], game.phase as i32 as f32);
        // Index 2: Current Player
        assert_eq!(tensor[2], game.current_player as f32);
    }

    #[test]
    fn test_portfolio_oracle_logic() {
        let mut game = crate::test_helpers::create_test_state();
        let db = crate::test_helpers::load_real_db();
        
        // 1. Find some actual live cards in the real DB
        let mut real_lives = Vec::new();
        for (&id, _l) in &db.lives {
            real_lives.push(id);
            if real_lives.len() >= 12 { break; }
        }
        game.core.players[0].initial_deck = real_lives.clone().into();

        // 2. Force a 'Power State' 
        game.core.players[0].blade_buffs = [10, 10, 10]; 
        let high_hearts = crate::core::hearts::HeartBoard::from_array(&[10, 10, 10, 10, 10, 10, 10]);
        for i in 0..3 {
            game.core.players[0].heart_buffs[i] = high_hearts;
        }

        println!("\n--- Portfolio Oracle Proof of Life (Real DB) ---");
        let tensor = game.to_vanilla_tensor(&db);
        
        // Global Synergy Stats are at indices 10-17
        println!("Best 1-Card Raw EV: {:.2}", tensor[10]);
        println!("Best 2-Card Raw EV: {:.2}", tensor[11]);
        println!("Best 3-Card Raw EV: {:.2}", tensor[12]);
        println!("Best 1-Card RA-EV:  {:.2}", tensor[13]);
        println!("Best 2-Card RA-EV:  {:.2}", tensor[14]);
        println!("Best 3-Card RA-EV:  {:.2}", tensor[15]);
        
        // Ensure we actually found something
        assert!(tensor[10] > 0.0, "With real cards and 30 hearts, Raw EV must be positive!");
    }
}
