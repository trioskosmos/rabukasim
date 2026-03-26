use engine_rust::core::logic::*;
use engine_rust::test_helpers::load_real_db;

#[test]
fn test_sumire_8752_repro() {
    let db = load_real_db();
    let sumire_id = 8752;
    let card = db.get_member(sumire_id).expect("Sumire 8752 not in DB");

    assert_eq!(card.abilities.len(), 2);

    let on_play = &card.abilities[1];
    assert_eq!(on_play.trigger, TriggerType::OnPlay);

    assert_eq!(on_play.conditions.len(), 2);
    assert_eq!(
        on_play.conditions[0].condition_type,
        ConditionType::HasKeyword
    );
    assert_eq!(on_play.conditions[1].condition_type, ConditionType::Baton);
    assert_eq!(
        on_play.conditions[1].params["FILTER"].as_str(),
        Some("GROUP_ID=3")
    );
    assert_eq!(on_play.conditions[1].params["COUNT_EQ"].as_i64(), Some(2));

    assert_eq!(on_play.effects.len(), 2);
    assert_eq!(on_play.effects[0].effect_type, EffectType::Draw);
    assert_eq!(on_play.effects[0].value, 2);
    assert_eq!(
        on_play.effects[1].effect_type,
        EffectType::PlayMemberFromDiscard
    );
    assert_eq!(on_play.effects[1].value, 1);
    assert_eq!(
        on_play.effects[1].params["FILTER"].as_str(),
        Some("GROUP_ID=3, COST_LE_4")
    );
    assert_eq!(
        on_play.effects[1].params["DESTINATION"].as_str(),
        Some("BATON_TOUCHED")
    );

    let frame_program = on_play
        .frame_program
        .as_ref()
        .expect("Sumire 8752 should have a frame program");

    assert_eq!(frame_program.frames.len(), 3);
    assert_eq!(frame_program.frames[0].opcode(), O_DRAW);
    assert_eq!(frame_program.frames[0].value(), 2);
    assert_eq!(frame_program.frames[1].opcode(), O_PLAY_MEMBER_FROM_DISCARD);
    assert_eq!(frame_program.frames[1].value(), 1);
    assert_eq!(frame_program.frames[2].opcode(), O_RETURN);
}
