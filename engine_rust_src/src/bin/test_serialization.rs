
use engine_rust::core::enums::ChoiceType;
use engine_rust::core::enums::*;
use engine_rust::core::logic::{AbilityContext, GameState, PendingInteraction};

fn main() {
    println!("--- Testing GameState Serialization Robustness ---");

    let mut gs = GameState::default();
    gs.turn = 5;
    gs.phase = Phase::Response;
    gs.current_player = 1;

    let pending = PendingInteraction {
        effect_opcode: 41,
        card_id: 123,
        ability_index: 0,
        ctx: AbilityContext {
            player_id: 1,
            ..Default::default()
        },
        choice_type: ChoiceType::LookAndChoose,
        ..Default::default()
    };
    gs.interaction_stack.push(pending);

    let serialized = serde_json::to_string(&gs).expect("Failed to serialize");
    println!("Serialized length: {}", serialized.len());

    let deserialized: GameState = serde_json::from_str(&serialized).expect("Failed to deserialize");
    assert_eq!(deserialized.turn, 5);
    
    println!("Serialization test passed!");
}