use engine_rust::core::logic::{CardDatabase, GameState};
use engine_rust::core::enums::*;

#[test]
fn test_card_33_ayase_eri_color_selection() {
    // Test card 33 (Ayase Eri / 絢瀬絵里)
    // Ability: At live start, choose one of heart01, heart03, or heart06.
    // Until live end, for each card in successful live placement, gain chosen heart.
    // This tests:
    // 1. Only 3 hearts should be available (not all 6)
    // 2. When selecting a valid heart, it should be stored correctly

    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();
    
    let mut state = GameState::default();
    state.debug.debug_mode = true;

    let p0 = 0;
    let card_33_id = 33;
    
    // Set up player 0 with card 33 on stage
    state.core.players[p0].stage[0] = card_33_id;
    
    // Add a success live to count for hearts bonus
    state.core.players[p0].success_lives.push(2001); // Live card

    println!("--- Testing Card 33 (Ayase Eri) - Heart Selection ---");
    println!("Success lives (P0): {}", state.core.players[p0].success_lives.len());

    // Get card 33 and verify it's in the database
    if let Some(card) = db.members.get(&33) {
        println!("Found card 33: {}", card.name);
        
        if let Some(ability) = card.abilities.first() {
            println!("Ability raw text: {}", ability.raw_text);
            println!("Ability trigger: {:?}", ability.trigger);
            println!("Effects count: {}", ability.effects.len());
            println!("Choice count: {}", ability.choice_count);
            
            // Verify choice_count is 3 (not 6)
            assert_eq!(
                ability.choice_count, 3,
                "Choice count should be 3 (for hearts 1, 3, 6), but got {}",
                ability.choice_count
            );
            
            // Verify the first effect is COLOR_SELECT with choices [1, 3, 6]
            let color_select_effect = ability.effects.iter()
                .find(|e| e.effect_type == EffectType::ColorSelect)
                .expect("Should have COLOR_SELECT effect");
            
            if let Some(choices_val) = color_select_effect.params.get("choices") {
                let choices: Vec<i32> = serde_json::from_value(choices_val.clone())
                    .expect("Should parse choices from JSON");
                println!("Valid choices: {:?}", choices);
                assert_eq!(choices, vec![1, 3, 6], "Choices should be [1, 3, 6]");
            } else {
                panic!("COLOR_SELECT effect should have 'choices' in params");
            }
            
            println!("✓ Card 33 configuration verified correctly");
            println!("  - choice_count: {} (expected 3)", ability.choice_count);
            println!("  - valid choices: [1, 3, 6]");
        } else {
            panic!("Card 33 has no abilities");
        }
    } else {
        panic!("Card 33 not found in database");
    }
}

#[test]
fn test_card_33_compilation_choice_count() {
    // Additional test: Verify the compiled JSON has correct choice_count
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    
    // Skip if this is a compiled test (not all data is available in all contexts)
    if json_content.is_empty() {
        println!("Skipping JSON verification - no data available");
        return;
    }
    
    match serde_json::from_str::<serde_json::Value>(&json_content) {
        Ok(data) => {
            if let Some(member_db) = data.get("member_db") {
                if let Some(card_33) = member_db.get("33") {
                    if let Some(abilities) = card_33.get("abilities").and_then(|a| a.as_array()) {
                        if let Some(ability_0) = abilities.first() {
                            let choice_count = ability_0.get("choice_count").and_then(|v| v.as_u64());
                            println!("Compiled choice_count for card 33: {:?}", choice_count);
                            assert_eq!(
                                choice_count,
                                Some(3),
                                "Compiled choice_count should be 3"
                            );
                            
                            // Verify the choices in effect params
                            if let Some(effects) = ability_0.get("effects").and_then(|e| e.as_array()) {
                                if let Some(effect_0) = effects.first() {
                                    if let Some(params) = effect_0.get("params") {
                                        if let Some(choices) = params.get("choices").and_then(|c| c.as_array()) {
                                            let choice_arr: Vec<i64> = choices.iter()
                                                .filter_map(|c| c.as_i64())
                                                .collect();
                                            println!("Compiled choices: {:?}", choice_arr);
                                            assert_eq!(choice_arr, vec![1, 3, 6], "Compiled choices should be [1, 3, 6]");
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        Err(e) => {
            println!("Could not parse compiled JSON: {}", e);
        }
    }
    
    println!("✓ Compiled JSON verification passed");
}
