use serde_json::json;
use crate::core::hearts::*;

#[derive(Clone, Debug)]
pub struct SourceInfo {
    pub id: i32,
    pub slot: i16,
    pub name: String,
    pub hearts: [u8; 7],
    pub base_hearts: [u8; 7], // Track original card hearts for separation
    pub is_yell: bool,
}

pub fn allocate_hearts_for_live(
    live_id: i32,
    live_idx: usize,
    live_name: &str,
    req_board: &HeartBoard,
    heart_sources: &mut Vec<SourceInfo>,
    allocations: &mut Vec<serde_json::Value>,
    remaining_hearts: &mut [u8; 7],
) {
    let req_arr = req_board.to_array();

    // 1. Specific colors 0-5
    for color_idx in 0..6 {
        let mut needed = req_arr[color_idx];
        if needed == 0 { continue; }

        // Try matching color first
        for src in heart_sources.iter_mut() {
            let available = src.hearts[color_idx];
            let take = available.min(needed);
            if take > 0 {
                // Determine if this heart is 'base' or 'bonus'
                let base_available = src.base_hearts[color_idx];
                let from_base = base_available.min(take);
                src.base_hearts[color_idx] -= from_base;

                src.hearts[color_idx] -= take;
                needed -= take;
                allocations.push(json!({
                    "source_id": src.id,
                    "source_slot": src.slot,
                    "source_name": src.name,
                    "source_type": if src.is_yell { "yell" } else { "member" },
                    "is_bonus": from_base < take,
                    "target_id": live_id,
                    "target_idx": live_idx,
                    "target_name": live_name,
                    "color": color_idx,
                    "amount": take
                }));
            }
            if needed == 0 { break; }
        }

        // Then try wildcards (index 6)
        if needed > 0 {
            for src in heart_sources.iter_mut() {
                let available = src.hearts[6];
                let take = available.min(needed);
                if take > 0 {
                    let base_available = src.base_hearts[6];
                    let from_base = base_available.min(take);
                    src.base_hearts[6] -= from_base;

                    src.hearts[6] -= take;
                    needed -= take;
                    allocations.push(json!({
                        "source_id": src.id,
                        "source_slot": src.slot,
                        "source_name": src.name,
                        "source_type": if src.is_yell { "yell" } else { "member" },
                        "is_bonus": from_base < take,
                        "target_id": live_id,
                        "target_idx": live_idx,
                        "target_name": live_name,
                        "color": color_idx,
                        "amount": take,
                        "wildcard": true
                    }));
                }
                if needed == 0 { break; }
            }
        }
    }

    // 2. Any hearts (index 6)
    let mut any_needed = req_arr[6];
    if any_needed > 0 {
        // Use wildcards first
        for src in heart_sources.iter_mut() {
            let available = src.hearts[6];
            let take = available.min(any_needed);
            if take > 0 {
                let base_available = src.base_hearts[6];
                let from_base = base_available.min(take);
                src.base_hearts[6] -= from_base;

                src.hearts[6] -= take;
                any_needed -= take;
                allocations.push(json!({
                    "source_id": src.id,
                    "source_slot": src.slot,
                    "source_name": src.name,
                    "source_type": if src.is_yell { "yell" } else { "member" },
                    "is_bonus": from_base < take,
                    "target_id": live_id,
                    "target_idx": live_idx,
                    "target_name": live_name,
                    "color": 6,
                    "amount": take
                }));
            }
            if any_needed == 0 { break; }
        }

        // Then use remaining colors
        if any_needed > 0 {
            for color_idx in 0..6 {
                for src in heart_sources.iter_mut() {
                    let available = src.hearts[color_idx];
                    let take = available.min(any_needed);
                    if take > 0 {
                        let base_available = src.base_hearts[color_idx];
                        let from_base = base_available.min(take);
                        src.base_hearts[color_idx] -= from_base;

                        src.hearts[color_idx] -= take;
                        any_needed -= take;
                        allocations.push(json!({
                            "source_id": src.id,
                            "source_slot": src.slot,
                            "source_name": src.name,
                            "source_type": if src.is_yell { "yell" } else { "member" },
                            "is_bonus": from_base < take,
                            "target_id": live_id,
                            "target_idx": live_idx,
                            "target_name": live_name,
                            "color": 6,
                            "amount": take
                        }));
                    }
                    if any_needed == 0 { break; }
                }
                if any_needed == 0 { break; }
            }
        }
    }

    let mut remaining_hearts_u32 = remaining_hearts.map(|x| x as u32);
    crate::core::hearts::process_hearts(
        &mut remaining_hearts_u32,
        &req_arr.map(|x| x as u32),
    );
    *remaining_hearts = remaining_hearts_u32.map(|x| x as u8);
}
