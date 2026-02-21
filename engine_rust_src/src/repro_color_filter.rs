#[cfg(test)]
mod tests {
    use crate::core::logic::*;
    
    use crate::core::logic::card_db::*;
    
    use crate::test_helpers::*;

    #[test]
    fn test_look_and_choose_color_filter_parity() {
        let mut db = CardDatabase::default();
        
        // Mock Cards for the deck
        // enums.py mapping: 0=PINK, 1=RED, 2=YELLOW, 3=GREEN, 4=BLUE, 5=PURPLE
        // ability.py color_map (for mask bits): 0=PINK, 1=GREEN, 2=BLUE, 3=RED, 4=YELLOW, 5=PURPLE, 6=STAR
        
        let colors = [0, 1, 2, 3, 4, 5]; // PINK, RED, YELLOW, GREEN, BLUE, PURPLE (enum indices)
        // Bit mapping (from ability.py color_map):
        // PINK(0) -> bit 0
        // RED(1) -> bit 3
        // YELLOW(2) -> bit 4
        // GREEN(3) -> bit 1
        // BLUE(4) -> bit 2
        // PURPLE(5) -> bit 5
        
        let mut deck_cids = Vec::new();
        for (i, &c_idx) in colors.iter().enumerate() {
            let cid = 5000 + i as i32;
            let mut hearts = [0u8; 7];
            hearts[c_idx] = 1;
            let m = MemberCard {
                card_id: cid,
                card_no: format!("GEN-{}", cid),
                name: format!("Color {}", c_idx),
                cost: 1,
                hearts,
                groups: vec![1],
                ..Default::default()
            };
            db.members.insert(cid, m.clone());
            let lid = (cid & LOGIC_ID_MASK) as usize;
            if lid < db.members_vec.len() { db.members_vec[lid] = Some(m); }
            deck_cids.push(cid);
        }

        // The card with the ability: PL!S-bp2-005-P style
        // TRIGGER: ON_PLAY
        // EFFECT: LOOK_AND_CHOOSE_REVEAL(7, choose_count=3) {COLOR_FILTER="RED/GREEN/BLUE", TYPE_MEMBER, TARGET=HAND, SOURCE=DECK, REMAINDER="DISCARD"}
        // v = 7 | (3 << 8) | (26 << 23) (RED=bit1, GREEN=bit3, BLUE=bit4 -> 2+8+16=26)
        // v = 218104583
        // a = 1 << 31 (Color Enable) | 8 << 12 (Source Deck) | 1 << 2 (Type Member) = -2147450876
        // s = 7 << 8 (Remainder Discard) | 6? No, target is hand (6), but actually target for LAC is in bytecode v or separate? 
        // In LAC, source is 'a' bits 12-15. Target is 'a' bits 0-1 (Choice type). 
        // Bytecode s for LAC: bits 0-7: Target Slot. bits 8-15: Remainder Destination (7=Discard).
        let bytecode = vec![41, 218104583, -2147450876, 1798, 1, 0, 0, 0];
        let ability_cid = 1000;
        add_card(&mut db, ability_cid, "BP2-005", vec![1], vec![(TriggerType::OnPlay, bytecode, vec![])]);

        let mut state = create_test_state();
        state.core.players[0].deck = deck_cids.into();
        state.core.players[0].hand = vec![ability_cid].into();

        // 1. Play the card
        let mut receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut receiver);
        
        let play_action = Action::PlayMember { hand_idx: 0, slot_idx: 0 }.id();
        state.step(&db, play_action).unwrap();
        
        // Phase should be Response (Choice)
        assert_eq!(state.phase, Phase::Response);
        let interaction = state.interaction_stack.last().expect("Interaction expected");
        assert_eq!(interaction.choice_type, "LOOK_AND_CHOOSE");
        
        // Verify Legal Actions (Filtered cards)
        let mut choice_receiver = TestActionReceiver::default();
        state.generate_legal_actions(&db, 0, &mut choice_receiver);
        
        // Deck was [5000, 5001, 5002, 5003, 5004, 5005], so popped order is [5005, 5004, 5003, 5002, 5001, 5000]
        // Indices in looked_cards (popped order):
        // 0: 5005 (PURPLE, idx 5) - NO (bit 5 of 26 is 0)
        // 1: 5004 (BLUE, idx 4)   - MATCH (bit 4 of 26 is 1) -> Action 8001
        // 2: 5003 (GREEN, idx 3)  - MATCH (bit 3 of 26 is 1) -> Action 8002
        // 3: 5002 (YELLOW, idx 2) - NO (bit 2 of 26 is 0)
        // 4: 5001 (RED, idx 1)    - MATCH (bit 1 of 26 is 1) -> Action 8004
        // 5: 5000 (PINK, idx 0)   - NO (bit 0 of 26 is 0)
        
        let choice_actions: Vec<i32> = choice_receiver.actions.iter().filter(|&&a| a >= 8000).cloned().collect();
        println!("Legal Choice Actions: {:?}", choice_actions);
        
        assert!(choice_actions.contains(&8001), "Should contain BLUE card choice (Action 8001)");
        assert!(choice_actions.contains(&8002), "Should contain GREEN card choice (Action 8002)");
        assert!(choice_actions.contains(&8004), "Should contain RED card choice (Action 8004)");
        
        assert!(!choice_actions.contains(&8000), "Should NOT contain PURPLE card choice");
        assert!(!choice_actions.contains(&8003), "Should NOT contain YELLOW card choice");
        assert!(!choice_actions.contains(&8005), "Should NOT contain PINK card choice");
    }
}
