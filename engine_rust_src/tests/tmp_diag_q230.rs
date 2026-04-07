use engine_rust::core::enums::TriggerType;
use engine_rust::core::logic::{AbilityContext, rules::get_effective_hearts};
use engine_rust::test_helpers::{create_test_state, load_real_db};

#[test]
fn tmp_diag_q230_loaded_frames() {
    let db = load_real_db();
    let member = db.get_member(4853).expect("expected Setsuna 4853");
    let ability = &member.abilities[0];
    eprintln!("RAW_TEXT={}", ability.raw_text);
    eprintln!("CONDITIONS={:?}", ability.conditions);
    for frame in ability.resolved_frames() {
        eprintln!("FRAME op={} value={} attr={} slot={} params={}", frame.opcode, frame.value, frame.attr, frame.slot, frame.params);
    }

    let mut state = create_test_state();
    state.debug.debug_mode = true;
    state.ui.silent = false;
    state.players[0].stage[0] = 4853;
    state.players[0].success_lives = vec![].into();
    state.players[1].success_lives = vec![].into();

    let ctx = AbilityContext {
        source_card_id: 4853,
        player_id: 0,
        activator_id: 0,
        area_idx: 0,
        trigger_type: TriggerType::OnLiveStart,
        ..Default::default()
    };
    state.trigger_abilities(db, TriggerType::OnLiveStart, &ctx);
    state.process_trigger_queue(db);

    let hearts = get_effective_hearts(&state, 0, 0, db, 0);
    eprintln!("HEARTS={:?}", hearts.to_array());
    panic!("diag done");
}