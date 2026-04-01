use crate::core::models::*;
use crate::test_helpers::*;

#[test]
fn test_card126_draw_repro() {
    let mut db = CardDatabase::default();

    let card126_id = 126;
    let live_card_id = 55001;
    let member_card_id = 3001;

    // Card 126: Move 5 from DeckTop to Discard. If Live card among them, Draw 1.
    let mut card126 = MemberCard::default();
    card126.card_id = card126_id;
    let mut ab = Ability::default();
    ab.trigger = TriggerType::OnPlay;
    ab.frame_program = Some(FrameProgram {
        frames: vec![
            AbilityFrame::new(58, 5, 1, 65540, false),
            AbilityFrame::new(309, 1, 8, 0, false),
            AbilityFrame::new(48, 10, 1, 0, false),
            AbilityFrame { opcode: O_DRAW, value: 1, ..Default::default() },
            AbilityFrame::new_return(),
        ],
        raw_program: None,
    });
    card126.abilities.push(ab);
    db.members.insert(card126_id, card126);

    // Mock Live Card
    let mut live_card = LiveCard::default();
    live_card.card_id = live_card_id;
    db.lives.insert(live_card_id, live_card);

    // Mock Member Card
    let mut member_card = MemberCard::default();
    member_card.card_id = member_card_id;
    db.members.insert(member_card_id, member_card);

    // Case 1: Live card at top of deck -> Draw should happen
    {
        let mut state = create_test_state();
        state.debug.debug_mode = true;
        let p1 = 0;

        // Setup deck: [Member, Member, Member, Member, Member, Member, Live]
        // pop() takes from the end, so these will be the "top" of the deck.
        state.players[p1].deck = vec![
            member_card_id,
            member_card_id,
            member_card_id,
            member_card_id,
            member_card_id,
            member_card_id,
            live_card_id,
        ]
        .into();
        state.players[p1].hand = vec![].into();

        let bytecode_frames = vec![
            AbilityFrame::new(58, 5, 1, 65540, false),
            AbilityFrame::new(309, 1, 8, 0, false),
            AbilityFrame::new(48, 10, 1, 0, false),
            AbilityFrame { opcode: O_DRAW, value: 1, ..Default::default() },
            AbilityFrame::new_return(),
        ];

        let ctx = AbilityContext {
            source_card_id: card126_id,
            player_id: p1 as u8,
            activator_id: p1 as u8,
            area_idx: 0,
            ..Default::default()
        };

        println!("--- Testing Card 126 with Live Card in Deck ---");
        println!("Frames to execute:");
        for (i, frame) in bytecode_frames.iter().enumerate() {
            println!("  Frame {}: {:?}", i, frame);
        }
        state.resolve_semantic_frames(&db, &bytecode_frames, &ctx);

        println!("Hand size: {}", state.players[p1].hand.len());
        println!("Discard size: {}", state.players[p1].discard.len());

        // Assertions
        assert_eq!(
            state.players[p1].discard.len(),
            5,
            "Card 126 should discard 5 cards"
        );
        assert_eq!(
            state.players[p1].hand.len(),
            1,
            "Card 126 should draw 1 when a Live card is revealed"
        );
    }

    // Case 2: No Live card at top of deck -> Draw should NOT happen
    {
        let mut state = create_test_state();
        state.debug.debug_mode = true;
        let p1 = 0;

        // Setup deck: [Member, Member, Member, Member, Member, ...]
        state.players[p1].deck = vec![member_card_id; 10].into();
        state.players[p1].hand = vec![].into();

        let ctx = AbilityContext {
            source_card_id: card126_id,
            player_id: p1 as u8,
            activator_id: p1 as u8,
            area_idx: 0,
            ..Default::default()
        };

        println!("--- Testing Card 126 with NO Live Card in Deck ---");
        state.resolve_ability(&db, &db.members[&card126_id].abilities[0], &ctx);

        println!("Hand size: {}", state.players[p1].hand.len());
        println!("Discard size: {}", state.players[p1].discard.len());

        // Assertions
        assert_eq!(
            state.players[p1].discard.len(),
            5,
            "Card 126 should discard 5 cards"
        );
        assert_eq!(
            state.players[p1].hand.len(),
            0,
            "Card 126 should not draw when no Live card is revealed"
        );
    }
}
