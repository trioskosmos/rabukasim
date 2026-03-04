use engine_rust::core::enums::ChoiceType;
use engine_rust::core::enums::*;
use engine_rust::core::logic::{AbilityContext, GameState, PendingInteraction};
// Removed unused VecDeque

fn main() {
    println!("--- Testing GameState Serialization Robustness ---");

    let mut gs = GameState::default();
    gs.turn = 5;
    gs.phase = Phase::Response;
    gs.current_player = 1;

    // Simulate a pending interaction (The "Logic Stack")
    let pending = PendingInteraction {
        effect_opcode: 41, // LOOK_AND_CHOOSE
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

    // Simulate a triggered ability in the queue
    let trigger = (
        456, // cid
        1,   // ab_idx
        AbilityContext {
            player_id: 0,
            ..Default::default()
        },
        false, // is_optional
        TriggerType::OnPlay,
    );
    gs.trigger_queue.push_back(trigger);

    // 1. Serialize to JSON
    let serialized = serde_json::to_string_pretty(&gs).expect("Failed to serialize GameState");
    println!("FULL_JSON_START\n{}\nFULL_JSON_END", serialized);

    // 2. Deserialize back
    let deserialized: GameState =
        serde_json::from_str(&serialized).expect("Failed to deserialize GameState");

    // 3. Verify critical fields
    assert_eq!(deserialized.turn, 5);
    assert_eq!(deserialized.phase, Phase::Response);
    assert_eq!(deserialized.interaction_stack.len(), 1);
    assert_eq!(deserialized.interaction_stack[0].effect_opcode, 41);
    assert_eq!(deserialized.trigger_queue.len(), 1);
    assert_eq!(deserialized.trigger_queue[0].0, 456);

    println!("\n✅ VERIFICATION SUCCESS: All internal engine state preserved!");
}
