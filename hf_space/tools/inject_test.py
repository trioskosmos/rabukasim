file_path = "engine_rust_src/src/semantic_assertions.rs"
test_code = r"""
    #[test]
    fn trace_sd1_001_diagnostic() {
        let engine = SemanticAssertionEngine::load();
        let card_id_str = "PL!-sd1-001-SD";
        let ab_idx = 0;

        let mut state = create_test_state();
        state.silent = true;
        let real_id = engine.find_real_id(card_id_str).unwrap();

        println!("--- Trace sd1-001 ---");
        SemanticAssertionEngine::setup_oracle_environment(&mut state, &engine.db, real_id);
        let snap0 = ZoneSnapshot::capture(&state.players[0]);
        println!("Baseline Hand: {} ({:?})", snap0.hand_len, state.players[0].hand);

        let actx = AbilityContext {
            source_card_id: real_id,
            player_id: 0,
            area_idx: 0,
            trigger_type: TriggerType::OnPlay,
            ability_index: ab_idx as i16,
            ..Default::default()
        };
        let is_live = engine.db.get_live(real_id as u16).is_some();
        state.trigger_queue.push_back((real_id as u16, ab_idx as u16, actx, is_live, TriggerType::OnPlay));

        println!("Triggering...");
        state.process_trigger_queue(&engine.db);
        state.step(&engine.db, 0).ok();

        let snap1 = ZoneSnapshot::capture(&state.players[0]);
        println!("After OnPlay Hand: {} ({:?})", snap1.hand_len, state.players[0].hand);

        let mut safety = 0;
        while (!state.interaction_stack.is_empty()) && safety < 10 {
            engine.resolve_interaction(&mut state).ok();
            let snap_i = ZoneSnapshot::capture(&state.players[0]);
            println!("Interaction Step {}: Hand={} ({:?})", safety, snap_i.hand_len, state.players[0].hand);
            safety += 1;
        }
    }
"""

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Find the last closing brace
last_brace_idx = -1
for i in range(len(lines) - 1, -1, -1):
    if lines[i].strip() == "}":
        last_brace_idx = i
        break

if last_brace_idx != -1:
    lines.insert(last_brace_idx, test_code + "\n")
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print("Successfully injected test.")
else:
    print("Could not find closing brace.")
