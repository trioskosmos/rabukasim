
use crate::core::logic::*;

#[test]
fn test_opcode_meta_rule() {
        let mut state = GameState::default();
        let db = CardDatabase {
            members: std::collections::HashMap::new(),
            lives: std::collections::HashMap::new(),
            ..CardDatabase::default()
        };
        let ctx = AbilityContext { player_id: 0, ..AbilityContext::default() };

        // O_META_RULE (29), Value 0 (cheer_mod), Attr 0, Target 0
        let bytecode = vec![O_META_RULE, 0, 0, 0, O_RETURN, 0, 0, 0];

        // Capture state before
        let initial_flags = state.core.players[0].flags;
        let initial_restrictions = state.core.players[0].restrictions.clone();

        // Execute
        state.resolve_bytecode(&db, &bytecode, &ctx);

        // Verify it did NOTHING (as per current implementation)
        assert_eq!(state.core.players[0].flags, initial_flags);
        assert_eq!(state.core.players[0].restrictions, initial_restrictions);
    }
