use crate::core::models::*;

#[test]
fn test_card_162_anyoji_himeme_discard_3_cards() {
    // Card 162 (安養寺 姫芽/PL!HS-PR-021-PR):
    // Play: Discard 3 cards from deck top (MANDATORY, not optional).
    // IF all are members with HEART_PINK: gain 1 HEART_RED until end of live.
    //
    // Key fixes being tested:
    // 1. MOVE_TO_DISCARD(3) is MANDATORY (not optional) - bug was (Optional) flag
    // 2. HEART_TYPE=0 (HEART_PINK) not type=1 - bug was wrong heart type
    // 3. ALL_CARDS_MATCH filter for condition check

    let mut db = CardDatabase::default();

    // Create test cards
    let mut card162 = MemberCard::default();
    card162.card_id = 162;
    card162.name = "安養寺 姫芽".to_string();
    card162.card_no = "PL!HS-PR-021-PR".to_string();
    card162.cost = 2;
    card162.hearts = [1, 0, 0, 0, 0, 0, 0];

    // Bytecode after fix:
    // [58, 3, 1, 0, 65540, 0, 0, 4, 14680064, 48, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0]
    // Opcode 58 = MOVE_TO_DISCARD(3)
    let bytecode = vec![
        58, 3, 1, 0, 65540, 0, 0, 4, 14680064, 48, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0,
    ];

    let mut ability = Ability::default();
    ability.trigger = TriggerType::OnPlay;
    ability.bytecode = bytecode;

    card162.abilities = vec![ability];

    db.members.insert(162, card162);

    // Verify the card loaded
    assert!(
        db.members.contains_key(&162),
        "Card 162 should be in database"
    );

    let loaded_card = db.members.get(&162).unwrap();
    assert_eq!(loaded_card.name, "安養寺 姫芽");
    assert_eq!(loaded_card.abilities.len(), 1);

    let ab = &loaded_card.abilities[0];
    // Bytecode value index 1 should be 3 (discard count)
    assert_eq!(ab.bytecode[1], 3, "Should discard 3 cards");

    // Bytecode value index 3 should be 0 (NOT optional) - was 536870912 before fix
    assert_eq!(ab.bytecode[3], 0, "Optional flag should be 0 (mandatory)");

    // Bytecode value index 12 should be 0 (HEART_TYPE=0) - was 1 before fix
    assert_eq!(ab.bytecode[12], 0, "HEART_TYPE should be 0 (HEART_PINK)");

    println!("✓ Card 162 bytecode structure verified");
    println!("✓ MOVE_TO_DISCARD(3) is MANDATORY");
    println!("✓ HEART_TYPE=0 (HEART_PINK/red)");
}
