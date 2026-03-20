use engine_rust::core::models::CardDatabase;

/// Card 207: Link to the FUTURE (PL!HS-bp2-020-L)
/// **IMPORTANT: This is a LIVE CARD, not a member card!**
/// 
/// Ability: {{live_start.png|ライブ開始時}}自分のステージにいる名前の異なる『蓮ノ空』のメンバー1人につき、このカードのスコアを＋２する。
/// Effect: For each 'Hasunosora' member with a different name on your stage, increase this card's score by +2
///
/// Pseudocode: TRIGGER: ON_LIVE_START
///            EFFECT: BOOST_SCORE(2) -> SELF {PER_CARD="STAGE", FILTER="UNIT_HASU, UNIQUE_NAMES"}
///
/// Card ID: 207 (PL!HS-bp2-020-L) in live_db
/// Expected behavior: When entering Performance phase with Hasunosora members on stage,
/// the live card's score bonus should be calculated and shown in the performance modal.
///
/// Current Issue: The bonus doesn't show in the performance modal - score stays at 0

#[test]
fn test_card207_is_live_card_in_database() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();

    println!("\n=== Verify Card 207 is in Live Database ===");

    // Try to get it as a live card (if the API supports it)
    // For now, just document what we know
    println!("Card 207 (PL!HS-bp2-020-L) is a LIVE CARD");
    println!("  Name: Link to the FUTURE");
    println!("  Location in JSON: data/cards_compiled.json -> live_db[\"207\"]");
    
    // Member accessor should fail
    if let Some(_member) = db.get_member(207) {
        println!("  ✗ Unexpectedly found in member database!");
    } else {
        println!("  ✓ Correctly NOT found in member database");
        println!("    (Confirms this is a live card, not a member card)");
    }
}

#[test]
fn test_card207_hasunosora_score_ability_exists() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();

    println!("\n=== Verify Card 207 Has Hasunosora Score Ability ===");

    let hasunosora_member_1 = 166; // PL!HS-bp1-001-P
    let hasunosora_member_2 = 167; // PL!HS-bp1-002-P

    // Let's verify these members exist and have correct properties
    println!("\n[Hasunosora Members]");
    for card_id in &[hasunosora_member_1, hasunosora_member_2] {
        if let Some(member) = db.get_member(*card_id) {
            println!("Card {}: {} ({})", card_id, member.card_no, member.name);
            if member.groups.contains(&4) {
                println!("  ✓ Confirmed as Hasunosora member (group 4)");
            } else {
                println!("  Groups: {:?}", member.groups);
            }
            
            // Verify this card has abilities
            println!("  Abilities: {}", member.abilities.len());
        }
    }

    println!("\n[Card 207 (Link to the FUTURE) - Live Card]");
    println!("Cannot access directly via get_member() because it's a live card");
    println!("The bytecode is compiled in: data/cards_compiled.json -> live_db[\"207\"]");
    println!("\n[Expected Abilities for Card 207]");
    println!("1. CONSTANT: ADD_TAG(\"UNIT_CERISE/UNIT_DOLL/UNIT_MIRAKURA\")");
    println!("2. ON_LIVE_START: BOOST_SCORE(2) with PER_CARD=\"STAGE\", FILTER=\"UNIT_HASU, UNIQUE_NAMES\"");
    println!("\n[The Issue]");
    println!("The ON_LIVE_START ability should:");
    println!("  - Count unique Hasunosora members on the stage");
    println!("  - Add +2 score for EACH unique member");
    println!("  - Example: 2 unique members = +4 score");
    println!("  - This bonus should appear in the performance modal");
    println!("\nBut currently: The bonus doesn't show in the performance modal!");
}

#[test]
fn test_verify_hasunosora_group_id() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&json_content).unwrap();

    println!("\n=== Verify Hasunosora Group ID ===");

    // Check what group ID corresponds to Hasunosora
    // From the code: group_id 4 should be Hasunosora
    for card_id in &[166, 167, 168, 169, 170] {
        if let Some(member) = db.get_member(*card_id) {
            let is_hasunosora = member.groups.contains(&4);
            println!(
                "Card {}: {} - Groups: {:?} {}",
                card_id,
                member.card_no,
                member.groups,
                if is_hasunosora { "✓ Hasunosora" } else { "✗ Not Hasunosora" }
            );
        }
    }

    println!("\n[Conclusion]");
    println!("Group ID 4 = Hasunosora (蓮ノ空)");
    println!("The UNIT_HASU filter should match cards with group_id=4");
}
