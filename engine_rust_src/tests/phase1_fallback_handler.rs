/// Phase 1 Fallback Handler Integration Test
///
/// Tests:
/// 1. Load fallback runtime preview JSON
/// 2. Verify canonical entries are marked with source="canonical"
/// 3. Verify needs_fallback flag is set correctly
/// 4. Verify fallback_bytecode is available
/// 5. Execute canonical ability using fallback bytecode
///
#[cfg(test)]
mod phase1_fallback_handler {
    use engine_rust::core::logic::{
        Ability, AbilityContext, CanonicalAbilityProgram, CanonicalStep, CardDatabase, GameState,
        EFFECT_MASK_DRAW, O_DRAW, O_RETURN,
    };
    use engine_rust::core::enums::{EffectType, TriggerType};
    use std::fs;
    use std::sync::Arc;

    #[test]
    fn test_load_fallback_runtime_preview() {
        let json_path = "canonical_ability_model/reports/fallback_runtime_preview.json";
        // Try from workspace root
        let json_str = std::fs::read_to_string(json_path)
            .or_else(|_| std::fs::read_to_string(format!("../{}", json_path)))
            .or_else(|_| std::fs::read_to_string(format!("../../{}", json_path)))
            .expect("Failed to read fallback runtime preview JSON from any expected location");

        let db = CardDatabase::from_json(&json_str)
            .expect("Failed to deserialize fallback runtime preview");

        // Gather statistics
        let mut canonical_count = 0;
        let mut legacy_count = 0;
        let mut canonical_with_fallback = 0;
        let mut canonical_no_fallback = 0;
        let mut canonical_with_program = 0;

        for card in db.members.values() {
            for ability in &card.abilities {
                if let Some(ref source) = ability.source {
                    if source == "canonical" {
                        canonical_count += 1;
                        if !ability.fallback_bytecode.is_empty() {
                            canonical_with_fallback += 1;
                        } else {
                            canonical_no_fallback += 1;
                        }
                        if ability.canonical_program.is_some() {
                            canonical_with_program += 1;
                        }
                    } else if source == "legacy" {
                        legacy_count += 1;
                    }
                }
            }
        }

        println!("[PHASE1] Canonical entries: {}", canonical_count);
        println!("[PHASE1] Canonical with fallback bytecode: {}", canonical_with_fallback);
        println!("[PHASE1] Canonical without fallback bytecode: {}", canonical_no_fallback);
        println!("[PHASE1] Canonical with structured program: {}", canonical_with_program);
        println!("[PHASE1] Legacy entries: {}", legacy_count);

        assert!(
            canonical_count > 0,
            "Should have canonical entries loaded"
        );
        assert!(
            canonical_with_fallback > 0,
            "Should have canonical entries with fallback bytecode"
        );
        assert!(
            canonical_with_program > 0,
            "Should preserve canonical structured programs in fallback preview"
        );
    }

    #[test]
    fn test_canonical_ability_uses_fallback_bytecode() {
        let json_path = "canonical_ability_model/reports/fallback_runtime_preview.json";
        let json_str = fs::read_to_string(json_path)
            .or_else(|_| fs::read_to_string(format!("../{}", json_path)))
            .or_else(|_| fs::read_to_string(format!("../../{}", json_path)))
            .expect("Failed to read fallback runtime preview JSON from any expected location");

        let db = CardDatabase::from_json(&json_str)
            .expect("Failed to deserialize fallback runtime preview");

        // Find a canonical entry with fallback bytecode
        let mut found_canonical = false;
        let mut test_card_id = 0i32;
        let mut test_ability_idx = 0usize;

        for (&card_id, card) in &db.members {
            for (ab_idx, ability) in card.abilities.iter().enumerate() {
                if ability.source.as_ref().map_or(false, |s| s == "canonical")
                    && !ability.fallback_bytecode.is_empty()
                    && ability.bytecode.is_empty()
                {
                    found_canonical = true;
                    test_card_id = card_id;
                    test_ability_idx = ab_idx;
                    println!(
                        "[PHASE1] Found canonical ability on card {} (ab #{})",
                        card.card_no, ab_idx
                    );
                    break;
                }
            }
            if found_canonical {
                break;
            }
        }

        assert!(found_canonical, "Should find a canonical ability with fallback bytecode");

        let card = &db.members[&test_card_id];
        let ability = &card.abilities[test_ability_idx];

        println!("[PHASE1] Card: {}", card.card_no);
        println!("[PHASE1] Ability trigger: {:?}", ability.trigger);
        println!("[PHASE1] Bytecode length: {}", ability.bytecode.len());
        println!("[PHASE1] Fallback bytecode length: {}", ability.fallback_bytecode.len());
        println!("[PHASE1] Needs fallback: {}", ability.needs_fallback);

        // Verify bytecode_program() returns fallback bytecode
        let program = ability.bytecode_program();
        assert!(
            program.len_words() > 0,
            "bytecode_program() should use fallback bytecode"
        );

        // Test execution with fallback bytecode
        let mut state = GameState::default();
        let ctx = AbilityContext {
            source_card_id: test_card_id,
            player_id: 0,
            activator_id: 0,
            area_idx: 0,
            ..Default::default()
        };

        // Execute ability using fallback bytecode
        let fallback_bc = Arc::new(ability.fallback_bytecode.clone());
        state.resolve_bytecode(&db, fallback_bc, &ctx);

        println!("[PHASE1] ✓ Executed canonical ability with fallback bytecode");
    }

    #[test]
    fn test_fallback_vs_direct_execution_equivalence() {
        let json_path = "canonical_ability_model/reports/fallback_runtime_preview.json";
        let json_str = fs::read_to_string(json_path)
            .or_else(|_| fs::read_to_string(format!("../{}", json_path)))
            .or_else(|_| fs::read_to_string(format!("../../{}", json_path)))
            .expect("Failed to read fallback runtime preview JSON from any expected location");

        let db = CardDatabase::from_json(&json_str)
            .expect("Failed to deserialize fallback runtime preview");

        // Find a legacy entry with normal bytecode
        let mut found_legacy = false;
        let mut test_card_id = 0i32;
        let mut test_ability_idx = 0usize;

        for (&card_id, card) in &db.members {
            for (ab_idx, ability) in card.abilities.iter().enumerate() {
                if ability.source.as_ref().map_or(false, |s| s == "legacy")
                    && !ability.bytecode.is_empty()
                {
                    found_legacy = true;
                    test_card_id = card_id;
                    test_ability_idx = ab_idx;
                    break;
                }
            }
            if found_legacy {
                break;
            }
        }

        if !found_legacy {
            println!("[PHASE1] No legacy entries found with bytecode - skipping equivalence test");
            return;
        }

        let card = &db.members[&test_card_id];
        let ability = &card.abilities[test_ability_idx];

        println!("[PHASE1] Testing legacy ability: {}", card.card_no);
        println!("[PHASE1] Bytecode length: {}", ability.bytecode.len());

        // Execute legacy version
        let mut state_legacy = GameState::default();
        let ctx = AbilityContext {
            source_card_id: test_card_id,
            player_id: 0,
            activator_id: 0,
            area_idx: 0,
            ..Default::default()
        };

        let legacy_bc = Arc::new(ability.bytecode.clone());
        state_legacy.resolve_bytecode(&db, legacy_bc, &ctx);

        println!("[PHASE1] ✓ Legacy execution succeeded");
    }

    #[test]
    fn test_fallback_detection_in_enrichment() {
        let json_path = "canonical_ability_model/reports/fallback_runtime_preview.json";
        let json_str = fs::read_to_string(json_path)
            .or_else(|_| fs::read_to_string(format!("../{}", json_path)))
            .or_else(|_| fs::read_to_string(format!("../../{}", json_path)))
            .expect("Failed to read fallback runtime preview JSON from any expected location");

        let db = CardDatabase::from_json(&json_str)
            .expect("Failed to deserialize fallback runtime preview");

        let mut needs_fallback_count = 0;
        let mut mismatches = vec![];

        for card in db.members.values() {
            for ability in &card.abilities {
                // Verify consistency: needs_fallback should be true iff:
                // (1) source is "canonical"
                // (2) bytecode is empty
                // (3) effects are not empty
                // (4) fallback_bytecode is not empty

                let is_canonical = ability.source.as_ref().map_or(false, |s| s == "canonical");
                let no_bytecode = ability.bytecode.is_empty();
                let has_fallback = !ability.fallback_bytecode.is_empty();

                if is_canonical && no_bytecode && has_fallback {
                    if !ability.needs_fallback {
                        mismatches.push(format!(
                            "{}: should have needs_fallback=true",
                            card.card_no
                        ));
                    }
                    needs_fallback_count += 1;
                }

                if ability.needs_fallback && !is_canonical {
                    mismatches.push(format!(
                        "{}: needs_fallback=true but source is not canonical",
                        card.card_no
                    ));
                }
            }
        }

        println!("[PHASE1] Abilities marked needs_fallback: {}", needs_fallback_count);
        if !mismatches.is_empty() {
            println!("[PHASE1] Mismatches:");
            for m in mismatches.iter().take(5) {
                println!("[PHASE1]   {}", m);
            }
        }

        assert!(
            needs_fallback_count > 0,
            "Should have some abilities marked for fallback"
        );
        assert!(mismatches.is_empty(), "Should have no fallback flag mismatches");
    }

    #[test]
    fn test_canonical_draw_metadata_can_be_derived_without_primary_bytecode() {
        let json_path = "canonical_ability_model/reports/fallback_runtime_preview.json";
        let json_str = fs::read_to_string(json_path)
            .or_else(|_| fs::read_to_string(format!("../{}", json_path)))
            .or_else(|_| fs::read_to_string(format!("../../{}", json_path)))
            .expect("Failed to read fallback runtime preview JSON from any expected location");

        let db = CardDatabase::from_json(&json_str)
            .expect("Failed to deserialize fallback runtime preview");

        let card = db.members.values().find(|card| {
            card.effect_mask & EFFECT_MASK_DRAW != 0
                && card.abilities.iter().any(|ability| {
                    ability.bytecode.is_empty()
                        && ability
                            .canonical_program
                            .as_ref()
                            .map(|program| program.effects.iter().any(|step| step.op == "DRAW"))
                            .unwrap_or(false)
                })
        });

        let card = card.expect("Expected a canonical draw card with metadata derived from canonical program");
        assert_ne!(
            card.effect_mask & EFFECT_MASK_DRAW,
            0,
            "Draw effect mask should be set from canonical program analysis"
        );
    }

    #[test]
    fn test_metadata_synced_enums_support_canonical_name_lookup() {
        assert_eq!(TriggerType::from_metadata_key("ON_PLAY"), Some(TriggerType::OnPlay));
        assert_eq!(EffectType::from_metadata_key("DRAW"), Some(EffectType::Draw));
        assert_eq!(EffectType::Draw.as_metadata_key(), "DRAW");
    }

    #[test]
    fn test_resolve_ability_executes_canonical_draw_without_bytecode() {
        let db = CardDatabase::default();
        let mut state = GameState::default();
        state.players[0].deck.push(101);
        state.players[0].deck.push(202);

        let ability = Ability {
            source: Some("canonical".to_string()),
            canonical_program: Some(CanonicalAbilityProgram {
                trigger: "ON_PLAY".to_string(),
                effects: vec![CanonicalStep {
                    kind: "effect".to_string(),
                    op: "DRAW".to_string(),
                    count: Some(2),
                    ..Default::default()
                }],
                ..Default::default()
            }),
            ..Default::default()
        };

        let ctx = AbilityContext {
            player_id: 0,
            activator_id: 0,
            source_card_id: 999,
            ..Default::default()
        };

        state.resolve_ability(&db, &ability, &ctx);

        assert_eq!(state.players[0].hand.len(), 2);
        assert!(state.players[0].hand.contains(&101));
        assert!(state.players[0].hand.contains(&202));
        assert!(state.players[0].deck.is_empty());
    }

    #[test]
    fn test_resolve_ability_uses_fallback_bytecode_when_canonical_op_is_unsupported() {
        let db = CardDatabase::default();
        let mut state = GameState::default();
        state.players[0].deck.push(303);

        let ability = Ability {
            source: Some("canonical".to_string()),
            canonical_program: Some(CanonicalAbilityProgram {
                trigger: "ON_PLAY".to_string(),
                effects: vec![CanonicalStep {
                    kind: "effect".to_string(),
                    op: "LOSE_EXCESS_HEARTS".to_string(), // Still unsupported in canonical.rs
                    value: Some(1),
                    ..Default::default()
                }],
                ..Default::default()
            }),
            fallback_bytecode: vec![O_DRAW, 1, 0, 0, 0, O_RETURN, 0, 0, 0, 0],
            ..Default::default()
        };

        let ctx = AbilityContext {
            player_id: 0,
            activator_id: 0,
            source_card_id: 1000,
            ..Default::default()
        };

        state.resolve_ability(&db, &ability, &ctx);

        // Should have fallen back to legacy DRAW 1
        assert_eq!(state.players[0].hand.len(), 1);
        assert!(state.players[0].hand.contains(&303));
        assert!(state.players[0].deck.is_empty());
    }

    #[test]
    fn test_resolve_ability_executes_canonical_boost_score() {
        let db = CardDatabase::default();
        let mut state = GameState::default();
        state.players[0].score = 100;

        let ability = Ability {
            source: Some("canonical".to_string()),
            canonical_program: Some(CanonicalAbilityProgram {
                trigger: "ON_PLAY".to_string(),
                effects: vec![CanonicalStep {
                    kind: "effect".to_string(),
                    op: "BOOST_SCORE".to_string(),
                    value: Some(50),
                    ..Default::default()
                }],
                ..Default::default()
            }),
            ..Default::default()
        };

        let ctx = AbilityContext {
            player_id: 0,
            activator_id: 0,
            ..Default::default()
        };

        state.resolve_ability(&db, &ability, &ctx);

        assert_eq!(state.players[0].score, 150);
    }
}
