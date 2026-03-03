use super::card_db::{CardDatabase, LiveCard};
use super::game::GameState;
use super::models::*;
use super::player::PlayerState;
use crate::core::enums::*;
use crate::core::hearts::*;
use serde_json::{json, Value};

pub type PerformanceResults = serde_json::Value;

pub fn do_yell(state: &mut GameState, db: &CardDatabase, count: u32) -> Vec<i32> {
    let p_idx = state.current_player as usize;
    let mut revealed = Vec::new();
    let reduction = state.core.players[p_idx].yell_count_reduction.max(0) as u32;
    let actual_count = count.saturating_sub(reduction);
    for _ in 0..actual_count {
        if state.core.players[p_idx].deck.is_empty() {
            state.resolve_deck_refresh(p_idx);
        }
        if let Some(card_id) = state.core.players[p_idx].deck.pop() {
            revealed.push(card_id);
            // Dispatch OnReveal trigger
            state.trigger_event(db, TriggerType::OnReveal, p_idx, card_id, -1, 0, -1);
        }
    }
    revealed
}

pub fn check_hearts_suitability(have: &[u8; 7], need: &[u8; 7]) -> bool {
    let mut have_u32 = [0u32; 7];
    let mut need_u32 = [0u32; 7];
    for i in 0..7 {
        have_u32[i] = have[i] as u32;
        need_u32[i] = need[i] as u32;
    }
    let (sat, tot) = crate::core::hearts::process_hearts(&mut have_u32, &need_u32);
    sat >= tot
}

pub fn consume_hearts_from_pool(pool: &mut [u8; 7], need: &[u8; 7]) {
    let mut pool_u32 = [0u32; 7];
    let mut need_u32 = [0u32; 7];
    for i in 0..7 {
        pool_u32[i] = pool[i] as u32;
        need_u32[i] = need[i] as u32;
    }

    crate::core::hearts::process_hearts(&mut pool_u32, &need_u32);

    for i in 0..7 {
        pool[i] = pool_u32[i] as u8;
    }
}

pub fn get_live_requirements(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    live: &LiveCard,
) -> (HeartBoard, Vec<serde_json::Value>) {
    let mut req_board = live.hearts_board;
    let mut adjustments = Vec::new();

    // Constant Ability Scan (O_SET_HEART_COST, O_INCREASE_HEART_COST, O_TRANSFORM_HEART)
    for ab in &live.abilities {
        if ab.trigger == TriggerType::Constant {
            let bc = &ab.bytecode;
            let mut i = 0;
            while i + 4 < bc.len() {
                let op = bc[i];
                if op == O_SET_HEART_COST {
                    let val = bc[i + 1];
                    let attr = bc[i + 2];

                    adjustments.push(json!({
                        "source": live.name,
                        "source_id": live.card_id,
                        "type": "override",
                        "desc": "Ability Override"
                    }));

                    for j in 0..6 {
                        let count = ((val >> (j * 4)) & 0xF) as u8;
                        req_board.set_color_count(j, count);
                    }
                    for j in 0..8 {
                        let c_code = ((attr >> (j * 4)) & 0xF) as usize;
                        if c_code == 0 {
                            break;
                        }
                        if c_code == 7 {
                            let old = req_board.get_color_count(6);
                            req_board.set_color_count(6, old.saturating_add(1));
                        } else if c_code >= 1 && c_code <= 6 {
                            let idx = c_code - 1;
                            let old = req_board.get_color_count(idx);
                            req_board.set_color_count(idx, old.saturating_add(1));
                        }
                    }
                } else if op == O_INCREASE_HEART_COST {
                    let val = bc[i + 1];
                    let attr = bc[i + 2] as usize;
                    if attr >= 1 && attr <= 7 {
                        let idx = if attr == 7 { 6 } else { attr - 1 };
                        let old = req_board.get_color_count(idx);
                        req_board.set_color_count(idx, old.saturating_add(val as u8));
                        adjustments.push(json!({
                            "source": live.name,
                            "source_id": live.card_id,
                            "color": idx,
                            "value": -(val as i32),
                            "type": "addition"
                        }));
                    }
                } else if op == O_TRANSFORM_HEART {
                    let from_attr = bc[i + 1] as usize;
                    let to_attr = bc[i + 2] as usize;
                    let from_idx = if from_attr == 7 {
                        6
                    } else if from_attr >= 1 && from_attr <= 6 {
                        from_attr - 1
                    } else {
                        99
                    };
                    let to_idx = if to_attr == 7 {
                        6
                    } else if to_attr >= 1 && to_attr <= 6 {
                        to_attr - 1
                    } else {
                        99
                    };

                    if from_idx < 7 && to_idx < 7 && from_idx != to_idx {
                        let count = req_board.get_color_count(from_idx);
                        if count > 0 {
                            req_board.set_color_count(from_idx, 0);
                            let old_to = req_board.get_color_count(to_idx);
                            req_board.set_color_count(to_idx, old_to.saturating_add(count));
                            adjustments.push(json!({
                                "source": live.name,
                                "source_id": live.card_id,
                                "from_color": from_idx,
                                "to_color": to_idx,
                                "value": count,
                                "type": "transform"
                            }));
                        }
                    }
                }
                i += 5;
            }
        }
    }

    // Player State Reductions
    for &(src_id, col, val) in &state.core.players[p_idx].heart_req_reduction_logs {
        let name = db.get_name(src_id).unwrap_or_else(|| "Effect".to_string());
        adjustments.push(json!({
            "source": name,
            "source_id": src_id,
            "color": col as usize,
            "value": val as i32,
            "type": "reduction"
        }));
    }

    // Player State Additions
    for &(src_id, col, val) in &state.core.players[p_idx].heart_req_addition_logs {
        let name = db.get_name(src_id).unwrap_or_else(|| "Effect".to_string());
        adjustments.push(json!({
            "source": name,
            "source_id": src_id,
            "color": col as usize,
            "value": -(val as i32),
            "type": "addition"
        }));
    }

    // Final board calculation mirroring PlayerState totals
    for i in 0..7 {
        let red = state.core.players[p_idx]
            .heart_req_reductions
            .get_color_count(i) as i32;
        let add = state.core.players[p_idx]
            .heart_req_additions
            .get_color_count(i) as i32;
        let val = (req_board.get_color_count(i) as i32 - red + add).max(0) as u8;
        req_board.set_color_count(i, val);
    }

    (req_board, adjustments)
}

pub fn check_live_success(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    live: &LiveCard,
    total_hearts: &[u8; 7],
) -> bool {
    // Rule: If player has FLAG_CANNOT_LIVE, performance always fails regardless of hearts.
    if state.core.players[p_idx].get_flag(PlayerState::FLAG_CANNOT_LIVE) {
        return false;
    }

    let (req_board, _) = get_live_requirements(state, db, p_idx, live);
    let total_board = HeartBoard::from_array(total_hearts);
    total_board.satisfies(req_board)
}

pub fn do_performance_phase(state: &mut GameState, db: &CardDatabase) {
    let p_idx = state.current_player as usize;

    // 8.3.4 Flip all cards in Live Zone
    if !state.performance_reveals_done[p_idx] {
        for i in 0..3 {
            if !state.core.players[p_idx].is_revealed(i) {
                let cid = state.core.players[p_idx].live_zone[i];
                state.core.players[p_idx].set_revealed(i, true);
                if cid >= 0 {
                    state.trigger_event(db, TriggerType::OnReveal, p_idx, cid, i as i16, 0, -1);
                    if state.phase == Phase::Response {
                        return;
                    }
                }
            }
        }
        state.performance_reveals_done[p_idx] = true;
    }

    // Discard non-live cards (Rule 8.3.4) BEFORE triggering OnLiveStart (Rule 11.4/8.3.8)
    for i in 0..3 {
        let cid = state.core.players[p_idx].live_zone[i];
        if cid >= 0 && db.get_live(cid).is_none() {
            if !state.ui.silent {
                state.log(format!(
                    "Rule 8.3.4: Discarding non-live card #{} from Live Zone.",
                    cid
                ));
            }
            state.core.players[p_idx].discard.push(cid);
            state.core.players[p_idx].live_zone[i] = -1;
        }
    }

    // Q68: If player has FLAG_CANNOT_LIVE, discard all live cards and skip live entirely
    // (No OnLiveStart triggers, no Yell)
    if state.core.players[p_idx].get_flag(PlayerState::FLAG_CANNOT_LIVE) {
        if !state.ui.silent {
            state.log(
                "Q68: Player cannot perform live. Discarding all cards from Live Zone.".to_string(),
            );
        }
        for i in 0..3 {
            let cid = state.core.players[p_idx].live_zone[i];
            if cid >= 0 {
                state.core.players[p_idx].discard.push(cid);
                state.core.players[p_idx].live_zone[i] = -1;
            }
        }
        state.live_start_triggers_done = true; // Mark as done to prevent future triggers
        advance_from_performance(state);
        return;
    }

    // Rule 11.4 [ライブ開始時] (Live Start)
    if !state.live_start_triggers_done {
        state.live_start_triggers_done = true;
        state.trigger_event(db, TriggerType::OnLiveStart, p_idx, -1, -1, 0, -1);
        if state.phase == Phase::Response {
            return;
        }
    }

    if state.core.players[p_idx].live_zone.iter().all(|&c| c < 0) {
        advance_from_performance(state);
        return;
    }

    // 8.3.10-11 Yell
    // Initialize breakdown logs Early to capture sources before they are moved by triggers
    let mut heart_breakdown = Vec::new();
    let mut blade_breakdown = Vec::new();
    let requirement_logs: Vec<serde_json::Value> = Vec::new();
    let mut transform_logs = Vec::new();
    // Temporary map for member_contributions summary
    let mut member_summary = std::collections::HashMap::new();
    for i in 0..3 {
        let cid = state.core.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                let key = format!("{}_{}", i, cid);
                member_summary.insert(
                    key,
                    json!({
                        "source": m.name,
                        "source_id": cid,
                        "slot": i,
                        "img": m.img_path,
                        "hearts": [0, 0, 0, 0, 0, 0, 0],
                        "base_hearts": m.hearts,
                        "bonus_hearts": [0, 0, 0, 0, 0, 0, 0],
                        "blades": 0,
                        "base_blades": m.blades,
                        "bonus_blades": 0,
                        "note_icons": 0,
                        "base_notes": m.note_icons,
                        "bonus_notes": 0,
                        "draw_icons": m.draw_icons,
                        "ability_blade_bonuses": [],
                        "ability_heart_bonuses": []
                    }),
                );
            }
        }
    }

    let mut total_blades = 0;
    // Apply Cheer Mod (Meta Rule)
    total_blades += state.core.players[p_idx].cheer_mod_count as u32;

    for i in 0..3 {
        let eff_b = state.get_effective_blades(p_idx, i, db, 0);
        let cid = state.core.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                if eff_b > 0 {
                    blade_breakdown.push(json!({
                        "source": m.name,
                        "source_id": cid,
                        "value": eff_b,
                        "type": "member"
                    }));
                }

                let key = format!("{}_{}", i, cid);
                if let Some(entry) = member_summary.get_mut(&key) {
                    let bonus_b = eff_b as i32 - m.blades as i32;
                    entry["blades"] = json!(eff_b);
                    entry["bonus_blades"] = json!(bonus_b);

                    // Collect Blade Buffs for this slot
                    let slot_blade_buffs: Vec<Value> = state.core.players[p_idx]
                        .blade_buff_logs
                        .iter()
                        .filter(|&&(_, _, slot)| slot == i as u8)
                        .map(|&(src_cid, amt, _)| {
                            let source_name =
                                db.get_name(src_cid).unwrap_or_else(|| "Effect".to_string());
                            json!({ "source": source_name, "amount": amt })
                        })
                        .collect();
                    entry["ability_blade_bonuses"] = json!(slot_blade_buffs);
                }
            }
        }
        total_blades += eff_b;
    }

    if !state.performance_yell_done[p_idx] {
        if !state.ui.silent {
            state.log(format!(
                "Rule 8.3.11: Player {} performs Yell ({} blades).",
                p_idx, total_blades
            ));
        }
        // Rule 8.3.11: Pops from main deck.
        let yell_count = total_blades;
        let yelled_cards = do_yell(state, db, yell_count);
        let mut yelled_names = Vec::new();
        for (idx, cid) in yelled_cards.into_iter().enumerate() {
            let cid_i32 = cid as i32;
            state.core.players[p_idx].yell_cards.push(cid_i32);
            // Rule 8.3.11: Place as energy. We distribute them across slots 0-2.
            let slot = idx % 3;
            state.core.players[p_idx].stage_energy[slot].push(cid_i32);
            state.core.players[p_idx].sync_stage_energy_count(slot);

            if let Some(m) = db.get_member(cid_i32) {
                yelled_names.push(format!("{} ({})", m.name, m.card_no));
            } else if let Some(l) = db.get_live(cid_i32) {
                yelled_names.push(format!("{} ({})", l.name, l.card_no));
            } else {
                yelled_names.push(format!("ID:{}", cid_i32));
            }
        }
        if !yelled_names.is_empty() {
            let msg = format!(
                "Yelled {} card(s): {}",
                yelled_names.len(),
                yelled_names.join(", ")
            );
            // Unified logging: YELL events now go to both turn_history and rule_log
            state.log_event("YELL", &msg, -1, -1, p_idx as u8, Some("Rule 8.3.11"), true);
        }
        state.performance_yell_done[p_idx] = true;
        if state.phase == Phase::Response {
            return;
        }
    }

    if !state.ui.silent {
        state.log(format!("--- PLAYER {} PERFORMANCE ---", p_idx));
        state.log(format!("  Blades: {}", total_blades));
    }

    // 8.3.14 Calculate Owned Hearts & Notes
    let mut total_hearts = [0u8; 7];
    let mut note_icons = 0;
    for i in 0..3 {
        let mut eff_h = state
            .get_effective_hearts(p_idx, i, db, 0)
            .to_array()
            .map(|h| h as u32);

        let cid = state.core.players[p_idx].stage[i];
        let mut true_bonus_h = [0i32; 7];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                for k in 0..7 {
                    true_bonus_h[k] = eff_h[k] as i32 - m.hearts[k] as i32;
                }
            }
        }

        // Apply color transforms to member hearts
        for &(src_cid, src_col, dst_col) in &state.core.players[p_idx].color_transforms {
            if src_col == 0 && (dst_col as usize) < 7 {
                let sum: u32 = eff_h.iter().sum();
                eff_h = [0u32; 7];
                eff_h[dst_col as usize] = sum;

                if transform_logs.is_empty() {
                    // Log once per transform type
                    let source_name = db.get_name(src_cid).unwrap_or_else(|| "Effect".to_string());
                    transform_logs.push(json!({
                        "source": source_name,
                        "desc": format!("All colors -> {}", dst_col),
                        "type": "transform"
                    }));
                }
            }
        }

        let cid = state.core.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                if eff_h.iter().any(|&v| v > 0) {
                    heart_breakdown.push(json!({
                        "source": m.name,
                        "source_id": cid,
                        "value": eff_h,
                        "type": "member"
                    }));
                }

                let key = format!("{}_{}", i, cid);
                if let Some(entry) = member_summary.get_mut(&key) {
                    entry["hearts"] = json!(eff_h);
                    entry["bonus_hearts"] = json!(true_bonus_h);
                    entry["note_icons"] = json!(m.note_icons);
                    entry["base_notes"] = json!(m.note_icons);

                    // Collect Heart Buffs for this slot
                    let slot_heart_buffs: Vec<Value> = state.core.players[p_idx]
                        .heart_buff_logs
                        .iter()
                        .filter(|&&(_, _, _, slot)| slot == i as u8)
                        .map(|&(src_cid, amt, color, _)| {
                            let source_name =
                                db.get_name(src_cid).unwrap_or_else(|| "Effect".to_string());
                            json!({ "source": source_name, "amount": amt, "color": color })
                        })
                        .collect();
                    entry["ability_heart_bonuses"] = json!(slot_heart_buffs);
                }
                note_icons += m.note_icons;
            }
        }
        for h in 0..7 {
            total_hearts[h] += eff_h[h] as u8;
        }
    }

    for &cid in state.core.players[p_idx].yell_cards.iter() {
        let (name, bh, ni) = if let Some(m) = db.get_member(cid) {
            (m.name.clone(), m.blade_hearts, m.note_icons)
        } else if let Some(l) = db.get_live(cid) {
            (l.name.clone(), l.blade_hearts, l.note_icons)
        } else {
            ("Unknown".to_string(), [0u8; 7], 0)
        };

        // Log yell card contributions
        let bh_sum: u32 = bh.iter().map(|&h| h as u32).sum();
        if bh_sum > 0 {
            heart_breakdown.push(json!({
                "source": format!("Yell: {}", name),
                "source_id": cid,
                "value": bh,
                "type": "yell"
            }));
        }
        if ni > 0 {
            blade_breakdown.push(json!({
                "source": format!("Yell: {}", name),
                "source_id": cid,
                "value": ni,
                "type": "yell"
            }));
        }

        // Yell cards are excluded from member_summary to focus on stage cards

        let mut adj_bh = [0u32; 7];
        for i in 0..7 {
            adj_bh[i] = bh[i] as u32;
        }

        for &(src_cid, src_col, dst_col) in &state.core.players[p_idx].color_transforms {
            if src_col == 0 && (dst_col as usize) < 7 {
                let mut sum = 0;
                for i in 0..7 {
                    if i != dst_col as usize {
                        sum += adj_bh[i];
                        adj_bh[i] = 0;
                    }
                }
                adj_bh[dst_col as usize] += sum;

                let source_name = if let Some(m) = db.get_member(src_cid) {
                    m.name.clone()
                } else if let Some(l) = db.get_live(src_cid) {
                    l.name.clone()
                } else {
                    "Effect".to_string()
                };

                transform_logs.push(json!({
                    "source": source_name,
                    "desc": format!("All colors -> {}", dst_col),
                    "type": "transform"
                }));
            }
        }
        for i in 0..7 {
            total_hearts[i] += adj_bh[i] as u8;
        }
        note_icons += ni;
    }
    state.core.players[p_idx].current_turn_notes = note_icons;

    if !state.ui.silent {
        state.log(format!("  Total Hearts: {:?}", total_hearts));
        state.log(format!("  Note Icons: {}", note_icons));
    }

    // 8.3.15-16 Check heart requirements
    let mut passed_flags = [false; 3];
    let mut sequential_passed = [false; 3]; // To track filling logic for UI even on failure
    let mut any_failed = false;

    // In this implementation, we consume hearts per live card (8.3.15.1.2)
    let mut remaining_hearts = total_hearts;
    for i in 0..3 {
        if let Some(cid) = state.core.players[p_idx]
            .live_zone
            .get(i)
            .copied()
            .filter(|&c| c >= 0)
        {
            if let Some(live) = db.get_live(cid) {
                state.log(format!(
                    "    Live {}: {} - Checking requirements...",
                    i, live.name
                ));

                let (req_board, _) = get_live_requirements(state, db, p_idx, live);
                if check_live_success(state, db, p_idx, live, &remaining_hearts) {
                    let mut remaining_hearts_u32 = remaining_hearts.map(|x| x as u32);
                    let (_, _) = crate::core::hearts::process_hearts(
                        &mut remaining_hearts_u32,
                        &req_board.to_array().map(|x| x as u32),
                    );
                    remaining_hearts = remaining_hearts_u32.map(|x| x as u8);
                    passed_flags[i] = true;
                    sequential_passed[i] = true;
                    state.log(format!("    -> SUCCESS for {}", live.name));
                } else {
                    state.log(format!(
                        "    -> FAILED for {} (Hearts or Restrictions)",
                        live.name
                    ));
                    any_failed = true;
                }
            }
        }
    }

    // Rule 8.3.16 covers this: if any fail, all are discarded.
    // We capture IDs here so we can still report them to UI even if discarded.
    let live_ids_before_discard: Vec<i32> = state.core.players[p_idx].live_zone.to_vec();

    // Rule 8.3.16: If ANY live card's requirements were not met, discard all live cards.
    if any_failed {
        state.log("  Rule 8.3.16: Performance FAILED. All live cards discarded.".to_string());
        for i in 0..3 {
            if state.core.players[p_idx].live_zone[i] >= 0 {
                state.core.players[p_idx]
                    .discard
                    .push(state.core.players[p_idx].live_zone[i]);
                state.core.players[p_idx].live_zone[i] = -1;
                passed_flags[i] = false; // Ensure UI reflects failure
            }
        }
    }

    let all_met = !any_failed
        && live_ids_before_discard
            .iter()
            .enumerate()
            .all(|(i, &cid)| cid < 0 || passed_flags[i]);

    if all_met {
        for i in 0..3 {
            if passed_flags[i] && (state.live_success_processed_mask[p_idx] >> i) & 1 == 0 {
                let cid = live_ids_before_discard[i];
                if cid >= 0 {
                    state.live_success_processed_mask[p_idx] |= 1 << i;
                    // Note: Actual OnLiveSuccess broadcast happens in do_live_result (Rule 8.4)
                    // This mask ensures we track which cards succeeded.
                }
            } else if !passed_flags[i] {
                state.live_success_processed_mask[p_idx] |= 1 << i;
            }
        }
        // Update excess hearts for Rule Q142
        state.core.players[p_idx].excess_hearts = remaining_hearts.iter().map(|&x| x as u32).sum();
    } else {
        state.core.players[p_idx].excess_hearts = 0;
    }

    // --- Store Performance Results for UI ---
    // Rule 8.4.10: Participants change to Rest state
    for i in 0..3 {
        if state.core.players[p_idx].stage[i] >= 0 {
            state.core.players[p_idx].set_tapped(i, true);
        }
    }

    let mut yell_cards_meta = Vec::new();
    for &cid in state.core.players[p_idx].yell_cards.iter() {
        if let Some(m) = db.get_member(cid) {
            yell_cards_meta.push(json!({
                "id": cid,
                "img": m.img_path,
                "blade_hearts": m.blade_hearts,
                "note_icons": m.note_icons,
                "draw_icons": m.draw_icons,
            }));
        } else if let Some(l) = db.get_live(cid) {
            yell_cards_meta.push(json!({
                "id": cid,
                "img": l.img_path,
                "blade_hearts": l.blade_hearts,
                "note_icons": l.note_icons,
            }));
        }
    }

    let mut lives_list = Vec::new();
    let mut temp_hearts_debug = total_hearts; // For simulating filling logic
    for i in 0..3 {
        let cid = live_ids_before_discard[i];
        if cid >= 0 {
            if let Some(l) = db.get_live(cid) {
                let (req_board, adjustments) = get_live_requirements(state, db, p_idx, l);

                // Calculate "filled" state for UI
                let mut filled = [0u8; 7];
                let mut sim_have = temp_hearts_debug;
                let mut wildcards = sim_have[6] as i32;

                // 1. Specific requirements
                for ci in 0..6 {
                    let need = req_board.get_color_count(ci);
                    // Match with same color first
                    let matching = sim_have[ci].min(need);
                    filled[ci] = matching;
                    sim_have[ci] -= matching;

                    // Then fill deficit with wildcards
                    let deficit = need.saturating_sub(matching);
                    if deficit > 0 {
                        let take_wild = wildcards.min(deficit as i32);
                        filled[ci] += take_wild as u8;
                        wildcards -= take_wild;
                    }
                }
                // 2. Any requirement
                let any_need = req_board.get_color_count(6);
                // Use remaining wildcards first
                let used_wild = wildcards.min(any_need as i32);
                filled[6] = used_wild as u8;
                let mut remaining_any = any_need.saturating_sub(used_wild as u8);

                // Then use remaining colored hearts
                if remaining_any > 0 {
                    for ci in 0..6 {
                        let take = (sim_have[ci] as i32).min(remaining_any as i32);
                        filled[6] += take as u8;
                        sim_have[ci] -= take as u8;
                        remaining_any -= take as u8;
                        if remaining_any == 0 {
                            break;
                        }
                    }
                }
                sim_have[6] = wildcards.max(0) as u8; // Update sim_have wildcard count for spare calculation

                lives_list.push(json!({
                    "id": cid,
                    "name": l.name,
                    "img": l.img_path,
                    "passed": passed_flags[i],
                    "score": l.score,
                    "required": req_board.to_array(),
                    "filled": filled,
                    "spare": sim_have,
                    "adjustments": adjustments,
                }));

                // If successfully passed in sequence, permanently consume for next live card UI check
                // We use sequential_passed because passed_flags might have been cleared by Rule 8.3.16
                if sequential_passed[i] {
                    consume_hearts_from_pool(&mut temp_hearts_debug, &req_board.to_array());
                }
            }
        }
    }

    // Calculate total_score as sum of live card scores for passed lives + volume icons
    let live_score: u32 = lives_list
        .iter()
        .filter_map(|l| {
            if l.get("passed").and_then(|v| v.as_bool()).unwrap_or(false) {
                l.get("score").and_then(|v| v.as_u64()).map(|s| s as u32)
            } else {
                None
            }
        })
        .sum();
    let total_score = live_score + note_icons as u32;

    let member_contributions: Vec<_> = member_summary.values().collect();
    state.ui.performance_results.insert(
        p_idx as u8,
        json!({
            "success": all_met,
            "total_hearts": total_hearts,
            "note_icons": note_icons,
            "yell_count": total_blades,
            "lives": lives_list,
            "yell_cards": yell_cards_meta,
            "member_contributions": member_contributions,
            "breakdown": {
                "blades": blade_breakdown,
                "hearts": heart_breakdown,
                "requirements": requirement_logs,
                "transforms": transform_logs,
                "score_bonus_logs": state.core.players[p_idx].live_score_bonus_logs,
            },
            "total_score_bonus": state.core.players[p_idx].live_score_bonus,
            "total_score": total_score
        }),
    );
    // state.yell_cards.clear(); // REMOVED: Now cleared in untap_all() for persistence
    advance_from_performance(state);
}

pub fn advance_from_performance(state: &mut GameState) {
    // We do NOT reset performance_reveals_done/yell_done here as they are per-player in the arrays.
    // They should be reset at the start of next turn.
    if state.current_player == state.first_player {
        state.current_player = 1 - state.first_player;
        // Phase stays the same or moves to P2?
        // My enum uses PerformanceP1 and PerformanceP2.
        if state.phase == Phase::PerformanceP1 {
            state.phase = Phase::PerformanceP2;
        } else {
            state.phase = Phase::PerformanceP1; // Error path
        }
    } else {
        state.phase = Phase::LiveResult;
        state.current_player = state.first_player;
        state.live_start_triggers_done = false;
    }
}

pub fn do_live_result(state: &mut GameState, db: &CardDatabase) {
    // Early bail-out: if win condition already met, skip straight to finalization
    if state.phase == Phase::Terminal {
        return;
    }
    state.check_win_condition();
    if state.phase == Phase::Terminal {
        return;
    }

    if !state.ui.silent {
        state.log("Rule 8.4: --- LIVE RESULT PHASE ---".to_string());
    }

    // 0. Trigger ON_LIVE_SUCCESS for successful performances (Rule 8.3.15 sequence completion)
    // 0. Trigger ON_LIVE_SUCCESS for successful performances (Rule 8.3.15 sequence completion)
    // We iterate through players and slots, using a mask to track which cards have already triggered
    // This allows us to resume correctly if an ability (like Kimi no Kokoro) pauses for input.
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;
        if let Some(res) = state.ui.performance_results.get(&(p as u8)) {
            if res
                .get("success")
                .and_then(|v| v.as_bool())
                .unwrap_or(false)
            {
                // Use bit 7 for "broad trigger done"
                if (state.live_result_processed_mask[p] & 0x80) == 0 {
                    state.live_result_processed_mask[p] |= 0x80;

                    state.trigger_event(db, TriggerType::OnLiveSuccess, p, -1, -1, 0, -1);
                    if state.phase == Phase::Response {
                        return;
                    }
                }
            }
        }
    }
    // We no longer use a single boolean, as we track per-slot.
    // If we reach here, all triggers are done.

    let mut scores = [0u32; 2];
    let mut has_success = [false; 2];

    // 1. Judgment Phase: Calculate scores based on SUCCESSFUL lives (still in zone)
    // IMPORTANT: We trust the snapshot from check_performance_requirements, not re-check hearts
    for p in 0..2 {
        let mut live_score = 0;
        let mut player_has_success = false;
        let mut has_live = false;
        let mut p_score = 0;

        // Check snapshot from check_performance_requirements first
        let snapshot_success = state
            .ui
            .performance_results
            .get(&(p as u8))
            .and_then(|res| res.get("success"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);

        for i in 0..3 {
            let cid = state.core.players[p].live_zone[i];
            if cid >= 0 {
                has_live = true;
                if let Some(card) = db.get_live(cid) {
                    // Use snapshot score if available (from check_performance_requirements)
                    let snapshot_score = state
                        .ui
                        .performance_results
                        .get(&(p as u8))
                        .and_then(|res| res.get("lives"))
                        .and_then(|l| l.as_array())
                        .and_then(|lives| lives.get(i))
                        .and_then(|l_res| l_res.get("score"))
                        .and_then(|s| s.as_u64());

                    // Check if this specific live passed in the snapshot
                    let snapshot_passed = state
                        .ui
                        .performance_results
                        .get(&(p as u8))
                        .and_then(|res| res.get("lives"))
                        .and_then(|l| l.as_array())
                        .and_then(|lives| lives.get(i))
                        .and_then(|l_res| l_res.get("passed"))
                        .and_then(|v| v.as_bool())
                        .unwrap_or(false);

                    if snapshot_passed || snapshot_score.is_some() {
                        p_score += snapshot_score.unwrap_or(card.score as u64) as u32;
                    }
                }
            }
        }

        // Trust the snapshot success flag instead of re-checking hearts
        if has_live && snapshot_success {
            live_score = p_score;
            player_has_success = true;
        } else if has_live {
            // Rule 8.3.16: Clear zone if snapshot indicates failure
            if !state.ui.silent {
                state.log(format!("Rule 8.3.16: P{} performance FAILED (unsatisfied requirements). Clearing live zone.", p));
            }
            for i in 0..3 {
                if state.core.players[p].live_zone[i] >= 0 {
                    state.core.players[p]
                        .discard
                        .push(state.core.players[p].live_zone[i]);
                    state.core.players[p].live_zone[i] = -1;
                }
            }
        }

        if player_has_success {
            if let Some(res) = state.ui.performance_results.get(&(p as u8)) {
                if let Some(vol) = res
                    .get("yell_score_bonus")
                    .and_then(|v| v.as_u64())
                    .or_else(|| res.get("note_icons").and_then(|v| v.as_u64()))
                {
                    live_score += vol as u32;
                }
            }
            has_success[p] = true;
        }

        // Pool O_BOOST_SCORE from constant abilities
        let mut constant_bonuses = std::collections::HashMap::new();
        for slot in 0..3 {
            let cid = state.core.players[p].stage[slot];
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    for ab in &m.abilities {
                        if ab.trigger == TriggerType::Constant {
                            let ctx = AbilityContext {
                                source_card_id: cid,
                                player_id: p as u8,
                                activator_id: p as u8,
                                area_idx: slot as i16,
                                ..Default::default()
                            };
                            if ab
                                .conditions
                                .iter()
                                .all(|c| state.check_condition(db, p, c, &ctx, 1))
                            {
                                let bc = &ab.bytecode;
                                let mut i = 0;
                                while i + 4 < bc.len() {
                                    if bc[i] == O_BOOST_SCORE {
                                        *constant_bonuses.entry(cid).or_insert(0) += bc[i + 1];
                                    }
                                    i += 5;
                                }
                            }
                        }
                    }
                }
            }
        }
        // Pool O_BOOST_SCORE from granted constant abilities
        for &(t_cid, s_cid, ab_idx) in &state.core.players[p].granted_abilities {
            if let Some(slot) = state.core.players[p]
                .stage
                .iter()
                .position(|&cid| cid == t_cid)
            {
                if let Some(src_m) = db.get_member(s_cid) {
                    if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                        if ab.trigger == TriggerType::Constant {
                            let ctx = AbilityContext {
                                source_card_id: t_cid,
                                player_id: p as u8,
                                activator_id: p as u8,
                                area_idx: slot as i16,
                                ..Default::default()
                            };
                            if ab
                                .conditions
                                .iter()
                                .all(|c| state.check_condition(db, p, c, &ctx, 1))
                            {
                                let bc = &ab.bytecode;
                                let mut i = 0;
                                while i + 4 < bc.len() {
                                    if bc[i] == O_BOOST_SCORE {
                                        *constant_bonuses.entry(s_cid).or_insert(0) += bc[i + 1];
                                    }
                                    i += 5;
                                }
                            }
                        }
                    }
                }
            }
        }

        let mut total_constant_bonus = 0;
        let mut score_breakdown = Vec::new();

        // 1. Base Score (Lives)
        score_breakdown.push(json!({
            "source": "Base (Lives)",
            "value": live_score.saturating_sub(state.core.players[p].current_turn_notes),
            "type": "base"
        }));

        // 2. Note Bonus
        if state.core.players[p].current_turn_notes > 0 {
            score_breakdown.push(json!({
                "source": "Note Bonus",
                "value": state.core.players[p].current_turn_notes,
                "type": "note"
            }));
        }

        // 3. Constant Bonuses
        for (cid, bonus) in constant_bonuses {
            total_constant_bonus += bonus;
            let name = db
                .get_member(cid)
                .map(|m| m.name.clone())
                .unwrap_or_else(|| format!("Card {}", cid));
            score_breakdown.push(json!({
                "source": name,
                "source_id": cid,
                "value": bonus,
                "type": "constant_ability"
            }));
        }

        // 4. Triggered/Activated Bonuses (live_score_bonus_logs)
        for &(cid, bonus) in &state.core.players[p].live_score_bonus_logs {
            let name = if cid >= 0 {
                db.get_member(cid)
                    .map(|m| m.name.clone())
                    .or_else(|| db.get_live(cid).map(|l| l.name.clone()))
                    .unwrap_or_else(|| format!("Card {}", cid))
            } else {
                "Ability Effect".to_string()
            };
            score_breakdown.push(json!({
                "source": name,
                "source_id": cid,
                "value": bonus,
                "type": "triggered_ability"
            }));
        }

        scores[p] = live_score
            + total_constant_bonus.max(0) as u32
            + state.core.players[p].live_score_bonus.max(0) as u32;

        if let Some(res) = state.ui.performance_results.get_mut(&(p as u8)) {
            if let serde_json::Value::Object(ref mut map) = res {
                if let Some(serde_json::Value::Object(ref mut b_map)) = map.get_mut("breakdown") {
                    b_map.insert("scores".to_string(), json!(score_breakdown));
                }
            }
        }
    }

    // 8.4.6 Compare
    let p0_wins = has_success[0] && (!has_success[1] || scores[0] >= scores[1]);
    let p1_wins = has_success[1] && (!has_success[0] || scores[1] >= scores[0]);
    let is_comparative_tie = p0_wins && p1_wins;

    // Update results with final scores
    for p in 0..2 {
        if let Some(res) = state.ui.performance_results.get_mut(&(p as u8)) {
            if let serde_json::Value::Object(ref mut map) = res {
                map.insert("total_score".to_string(), json!(scores[p]));
            }
        }
    }

    // Save current results to history only if a performance actually occurred
    if !state.ui.performance_results.is_empty() {
        for p in 0..2u8 {
            let mut map = if let Some(serde_json::Value::Object(m)) =
                state.ui.performance_results.get(&p).cloned()
            {
                m
            } else {
                let mut m = serde_json::Map::new();
                m.insert("total_score".to_string(), json!(scores[p as usize]));
                m
            };
            map.insert("turn".to_string(), json!(state.turn));
            map.insert("player_id".to_string(), json!(p));
            state
                .ui
                .performance_history
                .push(serde_json::Value::Object(map));
        }
    }

    state.ui.last_performance_results = state.ui.performance_results.clone();

    if !state.ui.silent {
        state.log(format!(
            "Rule 8.4.6: P0 Score: {} (Success: {} wins: {})",
            scores[0], has_success[0], p0_wins
        ));
        state.log(format!(
            "Rule 8.4.6: P1 Score: {} (Success: {} wins: {})",
            scores[1], has_success[1], p1_wins
        ));
    }

    // 2. Handling Winners (Rule 8.4.7)
    let mut choices_pending = false;
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;
        let wins = if p == 0 { p0_wins } else { p1_wins };
        if wins && !state.obtained_success_live[p] {
            let cards_in_zone: Vec<usize> = state.core.players[p]
                .live_zone
                .iter()
                .enumerate()
                .filter(|(_, &c)| c >= 0)
                .map(|(i, _)| i)
                .collect();

            // Use performance_results snapshot instead of re-checking hearts
            // Rule 8.3.15-16: Cards that passed are still in live_zone, failed cards were already discarded
            let perf_res = state.ui.performance_results.get(&(p as u8));
            let valid_candidates: Vec<usize> = cards_in_zone
                .iter()
                .cloned()
                .filter(|&i| {
                    let cid = state.core.players[p].live_zone[i];
                    if let Some(card) = db.get_live(cid) {
                        // Check for prevention effects
                        if state.core.players[p].prevent_success_pile_set != 0 {
                            return false;
                        }
                        if card.abilities.iter().any(|a| {
                            a.effects
                                .iter()
                                .any(|e| e.effect_type == EffectType::PreventSetToSuccessPile)
                        }) {
                            return false;
                        }

                        // Use the "passed" flag from performance_results snapshot
                        // This is the authoritative record from the performance phase (Rule 8.3.15)
                        if let Some(res) = perf_res {
                            if let Some(lives) = res.get("lives").and_then(|l| l.as_array()) {
                                if let Some(live_res) = lives.get(i) {
                                    return live_res
                                        .get("passed")
                                        .and_then(|v| v.as_bool())
                                        .unwrap_or(false);
                                }
                            }
                        }

                        // Fallback: if card is still in live_zone after performance phase,
                        // it passed the requirements (Rule 8.3.16 already discarded failed cards)
                        true
                    } else {
                        false
                    }
                })
                .collect();

            // Rule 8.4.7.1:
            // If scores are tied (Both Win), a player who ALREADY has 2+ success lives
            // does NOT move a card to success. (Catch-up mechanic).
            let is_at_limit = state.core.players[p].success_lives.len() >= 2;
            let is_tie_capped = is_comparative_tie && is_at_limit;

            if is_tie_capped {
                if !state.ui.silent {
                    state.log(format!(
                        "  Rule 8.4.7.1: Tie Penalty - P{} already at 2 lives. No move.",
                        p
                    ));
                }
            } else if state.core.players[p].success_lives.len() >= 3 {
                // Strict limit check to prevent scoring > 3
                if !state.ui.silent {
                    state.log(format!(
                        "  P{} already has 3 success lives. No more cards move to success pile.",
                        p
                    ));
                }
            } else if valid_candidates.len() == 1 {
                // Auto-move if exactly one card meets requirements
                let target_idx = valid_candidates[0];
                let cid = state.core.players[p].live_zone[target_idx];

                state.core.players[p].success_lives.push(cid as i32);
                state.check_win_condition(); // NEW: Immediate win check
                state.core.players[p].live_zone[target_idx] = -1;
                state.obtained_success_live[p] = true;
                if !state.ui.silent {
                    state.log(format!(
                        "Rule 8.4.7: P{} obtained Success Live: Card ID {}",
                        p, cid
                    ));
                }
            } else if valid_candidates.len() > 1 {
                // Physical choice needed among valid candidates
                if !choices_pending {
                    state.current_player = p as u8;
                    choices_pending = true;
                    if !state.ui.silent {
                        state.log(format!(
                            "Rule 8.4.7.3: P{} must SELECT a success live card.",
                            p
                        ));
                    }
                }
            }
        }
    }

    if choices_pending {
        // Stay in LiveResult phase, wait for 600-602
        state.live_result_selection_pending = true;
        return;
    }

    // 3. Finalization (Cleanup and Turn Advance)
    // Rule 8.4.10: Trigger [Turn End] abilities for BOTH players
    // FIX: Guard with live_result_triggers_done to prevent re-triggering on phase re-entry
    if !state.live_result_triggers_done {
        state.live_result_triggers_done = true;
        for i in 0..2 {
            let p = (state.first_player as usize + i) % 2;
            let ctx = AbilityContext {
                player_id: p as u8,
                activator_id: p as u8,
                source_card_id: -1,
                area_idx: -1,
                ..Default::default()
            };
            if !state.ui.silent {
                state.log(format!(
                    "Rule 8.4.10: Triggering [Turn End] abilities for Player {}.",
                    p
                ));
            }
            state.trigger_abilities(db, TriggerType::TurnEnd, &ctx);
            if state.phase == Phase::Response {
                return;
            }
        }
    }

    finalize_live_result(state);
}

pub fn finalize_live_result(state: &mut GameState) {
    // 8.4.8 Cleanup all live zones
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;
        for i in 0..3 {
            if state.core.players[p].live_zone[i] >= 0 {
                state.core.players[p]
                    .discard
                    .push(state.core.players[p].live_zone[i]);
                state.core.players[p].live_zone[i] = -1;
            }
        }

        // Rule 8.4.8: Cleanup all cards from stage energy and move to discard
        for i in 0..3 {
            while let Some(cid) = state.core.players[p].stage_energy[i].pop() {
                state.core.players[p].discard.push(cid);
            }
            state.core.players[p].sync_stage_energy_count(i);
        }

        // Player Score (persistent win condition) is the count of success lives
        state.core.players[p].score = state.core.players[p].success_lives.len() as u32;

        state.core.players[p].current_turn_notes = 0;
    }
    state.live_result_selection_pending = false;
    state.live_result_triggers_done = false;
    state.live_result_processed_mask = [0, 0];
    // phase will be set to Active below (or Terminal if game over)

    // 8.4.13 Determine next first player (Winner of judgement goes first)
    // Note: Simple logic for now, winner of judgement or host stays

    state.check_win_condition();
    if state.phase != Phase::Terminal {
        state.turn += 1;

        // Rule 8.4.13 Winner becomes next first player (if only one player got a success live)
        let s0 = state.obtained_success_live[0];
        let s1 = state.obtained_success_live[1];
        if s0 && !s1 {
            state.first_player = 0;
            if !state.ui.silent {
                state.log("Rule 8.4.13: P0 obtained Success Live. Now First Player.".to_string());
            }
        } else if s1 && !s0 {
            state.first_player = 1;
            if !state.ui.silent {
                state.log("Rule 8.4.13: P1 obtained Success Live. Now First Player.".to_string());
            }
        } else {
            // Keep current first player if both or neither obtained a success live
            if !state.ui.silent {
                state.log("Rule 8.4.13: Turn order unchanged.".to_string());
            }
        }

        state.current_player = state.first_player;
        state.phase = Phase::Active;
        state.obtained_success_live = [false, false];
    }
    state.ui.performance_results.clear();
    state.performance_reveals_done = [false; 2];
    state.performance_yell_done = [false; 2];
    state.live_result_triggers_done = false;
    state.live_result_processed_mask = [0; 2];
    state.live_start_processed_mask = [0; 2];
    state.live_success_processed_mask = [0; 2];
}
