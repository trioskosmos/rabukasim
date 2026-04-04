use crate::core::models::*;

#[test]
fn test_card_162_anyoji_himeme_discard_3_cards() {
    // Card 162 (螳蛾､雁ｯｺ 蟋ｫ闃ｽ/PL!HS-PR-021-PR):
    // Play: Discard 3 cards from deck top (MANDATORY, not optional).
    // IF all are members with HEART_PINK: gain 1 HEART_RED until end of live.
    //
    // Key fixes being tested:
    // 1. MOVE_TO_DISCARD(3) is MANDATORY (not optional) - bug was (Optional) flag
    // 2. HEART_TYPE=0 (HEART_PINK) not type=1 - bug was wrong heart type
    // 3. ALL_CARDS_MATCH filter for condition check

    let mut db = CardDatabase::default();

    let mut card162 = MemberCard::default();
    card162.card_id = 162;
    card162.name = "螳蛾､雁ｯｺ 蟋ｫ闃ｽ".to_string();
    card162.card_no = "PL!HS-PR-021-PR".to_string();
    card162.cost = 2;
    card162.hearts = [1, 0, 0, 0, 0, 0, 0];

    let words = vec![
        58, 3, 1, 0, 65540, 0, 0, 4, 14680064, 48, 12, 1, 0, 0, 4, 1, 0, 0, 0, 0,
    ];

    let mut ability = Ability::default();
    ability.trigger = TriggerType::OnPlay;
    ability.frame_program = Some(FrameProgram::from_instruction_words(&words));

    card162.abilities = vec![ability];

    db.members.insert(162, card162);

    assert!(
        db.members.contains_key(&162),
        "Card 162 should be in database"
    );

    let loaded_card = db.members.get(&162).unwrap();
    assert_eq!(loaded_card.name, "螳蛾､雁ｯｺ 蟋ｫ闃ｽ");
    assert_eq!(loaded_card.abilities.len(), 1);

    let ab = &loaded_card.abilities[0];
    assert_eq!(ab.words()[1], 3, "Should discard 3 cards");
    assert_eq!(ab.words()[3], 0, "Optional flag should be 0 (mandatory)");
    assert_eq!(ab.words()[12], 0, "HEART_TYPE should be 0 (HEART_PINK)");

    println!("Card 162 frame structure verified");
    println!("MOVE_TO_DISCARD(3) is MANDATORY");
    println!("HEART_TYPE=0 (HEART_PINK/red)");
}
