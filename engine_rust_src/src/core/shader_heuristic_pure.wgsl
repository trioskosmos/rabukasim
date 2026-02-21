fn select_rollout_action(p_idx: u32) -> u32 {
    return select_random_legal_action(p_idx);
}

fn evaluate_terminal(tactical_score: array<u32, 2>) -> f32 {
    let p0_lc = states[g_gid].player0.lives_cleared_count;
    let p1_lc = states[g_gid].player1.lives_cleared_count;
    if (p0_lc >= 3u) { return 1.0; }
    if (p1_lc >= 3u) { return 0.0; }
    return 0.5; // Unfinished game or draw
}
