const W_VOL_ICON: f32 = 50.0;
const W_VOLUME: f32 = 10.0;
const W_BOARD_BLADE: f32 = 100.0;
const W_LIVE_SCORE: f32 = 10000.0;
const W_ENERGY: f32 = 200.0;
const W_HAND: f32 = 300.0;

fn calculate_card_potential(cid: u32) -> f32 {
    if (cid == 0u || cid >= arrayLength(&card_stats)) { return 0.0; }
    let s = card_stats[cid];
    var score = f32(s.volume_icons) * W_VOL_ICON;
    score += f32(s.blades) * W_BOARD_BLADE;
    
    // Simple synergy check
    if ((s.synergy_flags & 0x1u) != 0u) { score += 500.0; }
    return score;
}

fn select_random_biased_action(p_idx: u32) -> u32 {
    let base_action = select_random_legal_action(p_idx);
    if (base_action == 0u) { return 0u; }
    
    var h_len = 0u;
    if (p_idx == 0u) { h_len = states[g_gid].players[0].hand_len; }
    else { h_len = states[g_gid].players[1].hand_len; }

    var best_score = -1.0;
    var best_action = base_action;

    for (var i = 0u; i < 5u; i = i + 1u) {
        let action = select_random_legal_action(p_idx);
        if (action == 0u) { continue; }
        
        var score = 0.0;
        if (action >= 1u && action <= 180u) {
            let adj = action - 1u;
            let h_idx = adj / 3u;
            let cid = get_hand_card(p_idx, h_idx);
            score = calculate_card_potential(cid);
        } else if (action == 0u) {
            score = 100.0; // Prefer ending turn over illegal moves
        }
        
        if (score > best_score) {
            best_score = score;
            best_action = action;
        }
    }
    return best_action;
}

fn select_rollout_action(p_idx: u32) -> u32 {
    return select_random_biased_action(p_idx);
}

fn evaluate_terminal(tactical_score: array<u32, 2>) -> f32 {
    var p0_lc = states[g_gid].players[0].lives_cleared_count;
    var p1_lc = states[g_gid].players[1].lives_cleared_count;
    
    var final_scores = array<f32, 2>(0.0, 0.0);
    for (var p = 0u; p < 2u; p = p + 1u) {
        var score = f32(states[g_gid].players[p].score);
        score += f32(states[g_gid].players[p].lives_cleared_count) * 1000.0;
        score += f32(states[g_gid].players[p].board_blades) * 100.0;
        score += f32(states[g_gid].players[p].energy_count) * 20.0;
        score += f32(states[g_gid].players[p].hand_len) * 50.0;
        score += f32(tactical_score[p]);
        final_scores[p] = score;
    }
    
    var reward = clamp(0.5 + (final_scores[0] - final_scores[1]) * 0.005, 0.01, 0.99);
    
    if (p0_lc >= 3u) { reward = 1.0; }
    else if (p1_lc >= 3u) { reward = 0.0; }
    
    return reward;
}
