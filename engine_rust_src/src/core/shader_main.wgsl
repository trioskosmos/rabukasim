@compute @workgroup_size(64)
fn main(@builtin(global_invocation_id) gid: vec3<u32>) {
    g_gid = gid.x;
    if (g_gid >= arrayLength(&states)) { return; }
    
    // Initialize RNG state
    g_rng = vec2<u32>(states[g_gid].rng_state_lo, states[g_gid].rng_state_hi);
    if (g_rng.x == 0u && g_rng.y == 0u) { g_rng.x = g_gid + 1u; }
    
    let phase = states[g_gid].phase;
    if (phase == PHASE_TERMINAL) { return; }
    
    // Single Rollout Step
    var action = 0u;
    if (states[g_gid].forced_action != -1) {
        action = u32(states[g_gid].forced_action);
        states[g_gid].forced_action = -1; // Consume it
    } else {
        if (phase == PHASE_MAIN || phase == PHASE_LIVESET || phase == PHASE_RESPONSE || phase == PHASE_MULLIGAN_P1 || phase == PHASE_MULLIGAN_P2) {
            action = select_random_legal_action(states[g_gid].current_player);
        } else {
            action = 0u;
        }
    }
    
    let res = step_state(action);
    
    // Update step count telemetry (stored in _pad_game[0])
    if (res != 0u) {
        states[g_gid]._pad_game[0] = states[g_gid]._pad_game[0] + 1u;
    }
    
    // AUTO-PHASE ADVANCE: Continue stepping through non-interactive phases
    // This mirrors CPU's step() which auto-advances Active→Energy→Draw→Main
    var current_phase = states[g_gid].phase;
    var safety = 0u;
    while (current_phase != PHASE_TERMINAL && 
           current_phase != PHASE_MAIN && 
           current_phase != PHASE_LIVESET && 
           current_phase != PHASE_RESPONSE && 
           current_phase != PHASE_MULLIGAN_P1 && 
           current_phase != PHASE_MULLIGAN_P2 &&
           current_phase != PHASE_LIVE_RESULT &&
           current_phase != PHASE_ENERGY &&
           safety < 10u) {
        let auto_res = step_state(0u);
        if (auto_res == 0u) { break; }
        current_phase = states[g_gid].phase;
        safety += 1u;
    }
    
    // Final evaluation if we just hit terminal
    if (states[g_gid].phase == PHASE_TERMINAL) {
        let p0_lc = states[g_gid].player0.lives_cleared_count;
        let p1_lc = states[g_gid].player1.lives_cleared_count;
        var score = 0.5;
        if (p0_lc >= 3u) { score = 1.0; }
        else if (p1_lc >= 3u) { score = 0.0; }
        else { score = 0.5 + f32(p0_lc) * 0.1 - f32(p1_lc) * 0.1; }
        scores[g_gid] = score;
    }

    // Persist RNG state for next dispatch
    states[g_gid].rng_state_lo = g_rng.x;
    states[g_gid].rng_state_hi = g_rng.y;
}
