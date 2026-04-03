use crate::core::enums::{ChoiceType, Phase, TriggerType};
use crate::test_helpers::*;

#[test]
fn test_repro_card_459_live_start_queues_member_selection() {
    let mut state = create_test_state();
    let db = load_real_db();
    state.ui.silent = true;

    let aqours_member = db
        .members
        .values()
        .find(|member| member.groups.contains(&1) && member.abilities.is_empty())
        .map(|member| member.card_id)
        .expect("Need a real Aqours member with no abilities");

    state.players[0].stage[0] = aqours_member;
    state.players[0].live_zone[0] = 459;

    state.trigger_event(&db, TriggerType::OnLiveStart, 0, -1, -1, 0, -1);
    state.process_trigger_queue(&db);

    assert_eq!(
        state.phase,
        Phase::Response,
        "card 459 should suspend for member selection before evaluating the blade threshold"
    );
    let pending = state
        .interaction_stack
        .last()
        .expect("card 459 should have a pending interaction");
    assert_eq!(pending.card_id, 459);
    assert_eq!(pending.ability_card_id, 459);
    assert_eq!(pending.ctx.source_card_id, 459);
    assert_eq!(pending.choice_type, ChoiceType::SelectMember);
}