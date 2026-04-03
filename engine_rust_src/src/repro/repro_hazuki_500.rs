use crate::core::enums::*;
use crate::test_helpers::*;

fn find_vanilla_member_excluding(db: &crate::core::logic::CardDatabase, excluded: &[i32]) -> i32 {
    db.members
        .values()
        .find(|member| !excluded.contains(&member.card_id) && member.abilities.is_empty())
        .map(|member| member.card_id)
        .expect("Need a real vanilla member in the database")
}

#[test]
fn test_hazuki_500_looks_at_five_cards_after_optional_discard() {
    let mut state = create_test_state();
    let db = load_real_db();
    state.ui.silent = true;

    let p_idx = 0usize;
    state.current_player = p_idx as u8;

    let hazuki_id = 500;
    let liella_cards: Vec<i32> = db
        .members
        .values()
        .filter(|member| {
            member.card_id != hazuki_id && member.groups.contains(&3) && member.abilities.is_empty()
        })
        .map(|member| member.card_id)
        .take(5)
        .collect();
    assert_eq!(liella_cards.len(), 5, "Need five real Liella! cards in the deck");

    let hand_filler = find_vanilla_member_excluding(&db, &[hazuki_id]);

    state.players[p_idx].hand = vec![hazuki_id, hand_filler].into();
    state.players[p_idx].deck = liella_cards.clone().into();
    state.phase = Phase::Main;

    state
        .step(
            &db,
            Action::PlayMember {
                hand_idx: 0,
                slot_idx: 0,
            }
            .id(),
        )
        .expect("play should succeed");

    let discard_prompt = state
        .interaction_stack
        .last()
        .expect("Ren's optional discard prompt should be pending");
    assert_eq!(discard_prompt.choice_type, ChoiceType::SelectHandDiscard);

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, p_idx, &mut actions);
    let discard_action = actions
        .actions
        .iter()
        .copied()
        .find(|action| *action >= crate::core::generated_constants::ACTION_BASE_HAND_SELECT)
        .expect("expected a hand card to discard");

    state
        .step(&db, discard_action as i32)
        .expect("discard choice should resolve");
    state.process_trigger_queue(&db);

    let look_prompt = state
        .interaction_stack
        .last()
        .expect("Ren's look-and-choose prompt should be pending");
    assert_eq!(look_prompt.card_id, hazuki_id);
    assert_eq!(look_prompt.ctx.source_card_id, hazuki_id);
    assert_eq!(look_prompt.choice_type, ChoiceType::LookAndChoose);
    assert_eq!(look_prompt.ctx.v_remaining, 1);

    let mut actions = TestActionReceiver::default();
    state.generate_legal_actions(&db, p_idx, &mut actions);
    let choose_action = actions
        .actions
        .iter()
        .copied()
        .find(|action| *action > 0)
        .expect("expected an actionable look-and-choose resolution");

    state
        .step(&db, choose_action as i32)
        .expect("look-and-choose resolution should succeed");
    state.process_trigger_queue(&db);

    assert_eq!(state.phase, Phase::Main);
    assert_eq!(state.players[p_idx].looked_cards.len(), 0);
    assert_eq!(state.players[p_idx].hand.len(), 1);
    assert_eq!(state.players[p_idx].discard.len(), 5);
    assert!(state.players[p_idx].deck.is_empty());
    assert!(
        state.players[p_idx]
            .hand
            .iter()
            .all(|cid| liella_cards.contains(cid)),
        "the resolved choice should add one of the looked Liella cards to hand"
    );
}
