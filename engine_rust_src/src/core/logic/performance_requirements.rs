use super::card_db::{CardDatabase, LiveCard};
use super::game::GameState;
use super::models::*;
use super::player::PlayerState;
use super::rules::calculate_board_aura;
use crate::core::enums::*;
use crate::core::hearts::*;
use super::interpreter::check_condition;
use serde_json::json; // Value removed

pub fn process_heart_modifiers_bytecode(
    bc: &[i32],
    req_board: &mut HeartBoard,
    adjustments: &mut Vec<serde_json::Value>,
    source_name: &str,
    source_id: i32,
) {
    let mut i = 0;
    while i + 4 < bc.len() {
        let op = bc[i];
        if op == O_SET_HEART_COST {
            let val = bc[i + 1];
            let attr = bc[i + 2];

            adjustments.push(json!({
                "source": source_name,
                "source_id": source_id,
                "type": "override",
                "desc": "Ability Override"
            }));

            for j in 0..6 {
                let count = ((val >> (j * 4)) & 0xF) as u8;
                if count > 0 {
                    req_board.set_color_count(j, count);
                }
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
            let idx = if attr == 0 || attr == 7 { 6 } else if attr <= 6 { attr - 1 } else { 99 };
            if idx < 7 {
                let old = req_board.get_color_count(idx);
                req_board.set_color_count(idx, old.saturating_add(val as u8));
                adjustments.push(json!({
                    "source": source_name,
                    "source_id": source_id,
                    "color": idx,
                    "value": -(val as i32),
                    "type": "addition"
                }));
            }
        } else if op == O_TRANSFORM_HEART {
            let from_attr = bc[i + 1] as usize;
            let to_attr = bc[i + 2] as usize;
            let from_idx = if from_attr == 7 { 6 } else if from_attr >= 1 && from_attr <= 6 { from_attr - 1 } else { 99 };
            let to_idx = if to_attr == 7 { 6 } else if to_attr >= 1 && to_attr <= 6 { to_attr - 1 } else { 99 };

            if from_idx < 7 && to_idx < 7 && from_idx != to_idx {
                let count = req_board.get_color_count(from_idx);
                if count > 0 {
                    req_board.set_color_count(from_idx, 0);
                    let old_to = req_board.get_color_count(to_idx);
                    req_board.set_color_count(to_idx, old_to.saturating_add(count));
                    adjustments.push(json!({
                        "source": source_name,
                        "source_id": source_id,
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

pub fn get_live_requirements(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    live: &LiveCard,
) -> (HeartBoard, Vec<serde_json::Value>) {
    let mut req_board = live.hearts_board;
    let mut adjustments = Vec::new();
    let mut aura = calculate_board_aura(state, p_idx, db);

    let opponent_idx = 1 - p_idx;
    for source_slot in 0..3 {
        let source_cid = state.players[opponent_idx].stage[source_slot];
        if source_cid < 0 {
            continue;
        }
        if let Some(member) = db.get_member(source_cid) {
            for ab in &member.abilities {
                if ab.trigger != TriggerType::Constant || !ab.raw_text.contains("OPPONENT_LIVE") {
                    continue;
                }
                let ctx = AbilityContext {
                    source_card_id: source_cid,
                    player_id: opponent_idx as u8,
                    activator_id: opponent_idx as u8,
                    area_idx: source_slot as i16,
                    ..Default::default()
                };
                if !ab
                    .conditions
                    .iter()
                    .all(|c| check_condition(state, db, opponent_idx, c, &ctx, 1))
                {
                    continue;
                }

                let mut i = 0;
                while i + 4 < ab.bytecode.len() {
                    let op = ab.bytecode[i];
                    if op == O_INCREASE_HEART_COST {
                        let val = ab.bytecode[i + 1];
                        let attr = ab.bytecode[i + 2] as usize;
                        let idx = if attr == 0 || attr == 7 {
                            6
                        } else if attr <= 6 {
                            attr - 1
                        } else {
                            99
                        };
                        if idx < 7 {
                            aura.heart_req_additions.add_to_color(idx, val as i32);
                        }
                    } else if op == O_SET_HEART_COST {
                        let mut override_board = HeartBoard::default();
                        process_heart_modifiers_bytecode(
                            &ab.bytecode[i..i + 5],
                            &mut override_board,
                            &mut Vec::new(),
                            &member.name,
                            source_cid,
                        );
                        aura.heart_req_additions = override_board;
                    }
                    i += 5;
                }
            }
        }
    }
    let use_cached_modifiers = state.players[p_idx].board_aura == aura;

    for ab in &live.abilities {
        if ab.trigger == TriggerType::Constant || ab.trigger == TriggerType::OnLiveStart {
            let ctx = AbilityContext {
                player_id: p_idx as u8,
                activator_id: p_idx as u8,
                ..Default::default()
            };
            if ab.conditions.iter().all(|c| check_condition(state, db, p_idx, c, &ctx, 1)) {
                process_heart_modifiers_bytecode(&ab.bytecode, &mut req_board, &mut adjustments, &live.name, live.card_id);
            }
        }
    }

    // Constant effects from stage members are now cached in BoardAura 
    // and applied via heart_req_reductions/additions below.

    if !use_cached_modifiers {
        for i in 0..7 {
            let red = aura.heart_req_reductions.get_color_count(i);
            if red > 0 {
                adjustments.push(json!({
                    "source": "Constant Effect",
                    "source_id": -1,
                    "color": i,
                    "value": red as i32,
                    "type": "reduction"
                }));
            }
            let add = aura.heart_req_additions.get_color_count(i);
            if add > 0 {
                adjustments.push(json!({
                    "source": "Constant Effect",
                    "source_id": -1,
                    "color": i,
                    "value": -(add as i32),
                    "type": "addition"
                }));
            }
        }
    }

    for &(src_id, col, val) in &state.players[p_idx].heart_req_reduction_logs {
        let name = db.get_name(src_id).unwrap_or_else(|| "Effect".to_string());
        adjustments.push(json!({
            "source": name,
            "source_id": src_id,
            "color": col as usize,
            "value": val as i32,
            "type": "reduction"
        }));
    }

    for &(src_id, col, val) in &state.players[p_idx].heart_req_addition_logs {
        let name = db.get_name(src_id).unwrap_or_else(|| "Effect".to_string());
        adjustments.push(json!({
            "source": name,
            "source_id": src_id,
            "color": col as usize,
            "value": -(val as i32),
            "type": "addition"
        }));
    }

    let mut heart_req_reductions = if use_cached_modifiers {
        state.players[p_idx].heart_req_reductions
    } else {
        aura.heart_req_reductions
    };
    let mut heart_req_additions = if use_cached_modifiers {
        state.players[p_idx].heart_req_additions
    } else {
        aura.heart_req_additions
    };

    if !use_cached_modifiers {
        heart_req_reductions.add(state.players[p_idx].heart_req_reductions);
        heart_req_additions.add(state.players[p_idx].heart_req_additions);
        for &(_, col, val) in &state.players[p_idx].heart_req_reduction_logs {
            heart_req_reductions.add_to_color(col as usize, val as i32);
        }
        for &(_, col, val) in &state.players[p_idx].heart_req_addition_logs {
            heart_req_additions.add_to_color(col as usize, val as i32);
        }
    }

    for i in 0..7 {
        let red = heart_req_reductions.get_color_count(i) as i32;
        let add = heart_req_additions.get_color_count(i) as i32;
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
    if state.players[p_idx].get_flag(PlayerState::FLAG_CANNOT_LIVE) {
        return false;
    }

    let (req_board, _) = get_live_requirements(state, db, p_idx, live);
    let total_board = HeartBoard::from_array(total_hearts);
    total_board.satisfies(req_board)
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
