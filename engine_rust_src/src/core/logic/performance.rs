use super::card_db::CardDatabase; // LiveCard removed
use super::game::GameState;
use super::models::*;
use super::player::PlayerState;
use crate::core::enums::*;
// use crate::core::hearts::*;
pub use super::performance_allocation::*;
pub use super::performance_requirements::*;
use crate::core::logic::heart_semantics::decode_heart_type_from_params;
use crate::core::logic::interpreter::check_condition;
use serde_json::{json, Value};
use smallvec::SmallVec;

/// Type-safe constants for performance calculations
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum PerformanceSlot {
    Left = 0,
    Center = 1,
    Right = 2,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ColorIndex {
    Red = 0,
    Blue = 1,
    Yellow = 2,
    Green = 3,
    Pink = 4,
    Purple = 5,
    Rainbow = 6,
}

impl ColorIndex {
    /// Convert from mask value with validation
    pub fn from_mask(mask: usize) -> Option<Self> {
        match mask {
            0x7F => Some(ColorIndex::Rainbow),
            m if m.count_ones() == 1 && m < 1 << 7 => {
                match m.trailing_zeros() {
                    0 => Some(ColorIndex::Red),
                    1 => Some(ColorIndex::Blue),
                    2 => Some(ColorIndex::Yellow),
                    3 => Some(ColorIndex::Green),
                    4 => Some(ColorIndex::Pink),
                    5 => Some(ColorIndex::Purple),
                    _ => None,
                }
            }
            _ => None,
        }
    }
    
    pub fn as_usize(self) -> usize {
        self as usize
    }
}

impl PerformanceSlot {
    /// Convert to usize with bounds checking
    pub fn as_usize(self) -> usize {
        self as usize
    }
    
    /// Create from index with validation
    pub fn from_index(idx: usize) -> Option<Self> {
        match idx {
            0 => Some(PerformanceSlot::Left),
            1 => Some(PerformanceSlot::Center),
            2 => Some(PerformanceSlot::Right),
            _ => None,
        }
    }
}

// Add profiling counters at module level
#[cfg(feature = "perf_profile")]
static mut ABILITY_CHECK_COUNT: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
#[cfg(feature = "perf_profile")]
static mut CHECK_CONDITION_TIME_US: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);

pub type PerformanceResults = serde_json::Value;

// Flat struct for silent mode performance data - eliminates JSON allocations
#[derive(Default, Clone, Debug)]
pub struct PerfResultFlat {
    pub success: bool,
    pub lives: [(i32, bool); 3], // (score, passed) for each live slot
    pub total_hearts: [u8; 7],
    pub note_icons: u32,
    pub yell_count: u32,
    pub total_score_bonus: i32,
    pub total_score: u32,
}

/// Common validation helpers for performance logic
mod validation {
    use super::*;
    
    /// Validate color mask and return appropriate color index
    pub fn validate_color_mask(mask: usize) -> Option<usize> {
        if mask == 0x7F {
            return Some(6); // Special case for full mask
        }
        if mask.count_ones() == 1 && mask < 1 << 7 {
            return Some(mask.trailing_zeros() as usize);
        }
        None
    }
    
    /// Validate raw attribute mask for color extraction
    pub fn validate_raw_attr_mask(mask: usize) -> Option<usize> {
        if mask == 0x7F {
            return Some(6); // Special case for full mask
        }
        if mask.count_ones() == 1 && mask < 1 << 7 {
            return Some(mask.trailing_zeros() as usize);
        }
        None
    }
    
    /// Check if deck refresh is needed for player
    pub fn needs_deck_refresh(state: &GameState, p_idx: usize) -> bool {
        state.players[p_idx].deck.is_empty()
    }
    
    /// Validate yell count with reductions
    pub fn calculate_actual_yell_count(state: &GameState, count: u32) -> u32 {
        let p_idx = state.current_player as usize;
        let reduction = state.players[p_idx].yell_count_reduction.max(0) as u32;
        count.saturating_sub(reduction)
    }
}

fn semantic_heart_color_from_frame(frame: &AbilityFrameComponents<'_>, fallback: usize) -> usize {
    // Try to decode from parameters first
    if let Some(color) = decode_heart_type_from_params(frame.params) {
        return color;
    }

    // Validate color mask
    if frame.filter.color_mask != 0 {
        if let Some(color) = validation::validate_color_mask(frame.filter.color_mask as usize) {
            return color;
        }
        return frame.filter.color_mask.trailing_zeros() as usize;
    }

    // Validate raw attribute mask
    if frame.raw_attr != 0 {
        if let Some(color) = validation::validate_raw_attr_mask(frame.raw_attr as usize) {
            return color;
        }
    }

    fallback
}

// ============================================================================
// MODULE: YELL SYSTEM
// ============================================================================

pub fn do_yell(state: &mut GameState, db: &CardDatabase, count: u32) -> Vec<i32> {
    let p_idx = state.current_player as usize;
    let mut revealed = Vec::new();
    let actual_count = validation::calculate_actual_yell_count(state, count);
    
    for _ in 0..actual_count {
        if validation::needs_deck_refresh(state, p_idx) {
            state.resolve_deck_refresh(p_idx);
        }
        if let Some(card_id) = state.players[p_idx].pop_deck_card() {
            revealed.push(card_id);
            state.players[p_idx].yell_cards.push(card_id);
            let slot = (revealed.len() - 1) % 3;
            state.players[p_idx].stage_energy[slot].push(card_id);

            // Update yell bonus cache
            update_yell_bonus_cache(state, db, p_idx, slot, card_id);
            state.players[p_idx].sync_stage_energy_count(slot);
            
            // Dispatch OnReveal trigger
            state.trigger_event(db, TriggerType::OnReveal, p_idx, card_id, -1, 0, -1);
        }
    }
    revealed
}

/// Update yell bonus cache for a card
fn update_yell_bonus_cache(state: &mut GameState, db: &CardDatabase, p_idx: usize, slot: usize, card_id: i32) {
    if let Some(m) = db.get_member(card_id) {
        state.players[p_idx].yell_blade_bonus[slot] += m.blades as u32;
        state.players[p_idx].yell_heart_bonus[slot].add(m.blade_hearts_board);
    } else if let Some(l) = db.get_live(card_id) {
        state.players[p_idx].yell_heart_bonus[slot].add(l.blade_hearts_board);
    }
}

// ============================================================================
// MODULE: PERFORMANCE PHASE MAIN
// ============================================================================

/// Execute the main performance phase for the current player
/// Handles scoring, heart collection, and victory condition checking
pub fn execute_performance_phase(state: &mut GameState, db: &CardDatabase) {
    let p_idx = state.current_player as usize;
    if !state.ui.silent {
        state.log(format!("Rule 8.3.1, Rule 8.3.2, Rule 8.3.2.1: performance Phase: Player {} is turn player.", p_idx));
    }
    // 8.3.3 Start triggers
    if !state.performance_reveals_done[p_idx] && state.live_start_processed_mask[p_idx] == 0 {
        if !state.ui.silent {
            state.log("Rule 8.3.3: performance Phase start: triggers check.".to_string());
        }
    }

    // 8.3.4 Flip all cards in Live Zone
    if !state.performance_reveals_done[p_idx] {
        if !state.ui.silent {
            state.log("Rule 8.3.4, Rule 8.3.5, Rule 8.3.6, Rule 8.3.7: Flip cards in Live Zone and check existence.".to_string());
        }
        for i in 0..3 {
            if !state.players[p_idx].is_revealed(i) {
                let cid = state.players[p_idx].live_zone[i];
                state.players[p_idx].set_revealed(i, true);
                if cid >= 0 {
                    state.trigger_event(db, TriggerType::OnReveal, p_idx, cid, i as i16, 0, -1);
                    if state.phase == Phase::Response {
                        return;
                    }
                }
            }
        }
        state.performance_reveals_done[p_idx] = true;
        if !state.ui.silent {
            state.log("Rule 8.3.5, Rule 8.3.6: Checking timing after reveal.".to_string());
        }
    }

    // Discard non-live cards (Rule 8.3.4) BEFORE triggering OnLiveStart (Rule 11.4/8.3.8)
    for i in 0..3 {
        let cid = state.players[p_idx].live_zone[i];
        if cid >= 0 && db.get_live(cid).is_none() {
            if !state.ui.silent {
                state.log(format!(
                    "Rule 8.3.4: Discarding non-live card #{} from Live Zone.",
                    cid
                ));
            }
            state.players[p_idx].push_discard_card(cid);
            state.players[p_idx].live_zone[i] = -1;
        }
    }

    // Q68: If player has FLAG_CANNOT_LIVE, discard all live cards and skip live entirely
    // (No OnLiveStart triggers, no Yell)
    if state.players[p_idx].get_flag(PlayerState::FLAG_CANNOT_LIVE) {
        if !state.ui.silent {
            state.log(
                "Q68: Player cannot perform live. Discarding all cards from Live Zone.".to_string(),
            );
        }
        for i in 0..3 {
            let cid = state.players[p_idx].live_zone[i];
            if cid >= 0 {
                state.players[p_idx].push_discard_card(cid);
                state.players[p_idx].live_zone[i] = -1;
            }
        }
        state.live_start_triggers_done = true; // Mark as done to prevent future triggers
        advance_from_performance(state);
        return;
    }

    // Rule 11.4 [ライブ開始時] (Live Start)
    if !state.live_start_triggers_done {
        state.live_start_triggers_done = true;
        if !state.ui.silent {
            state.log("Rule 11.4, Rule 11.4.1 (Q227): Broadcasting [ライブ開始時] (On Live Start) triggers. (Costs cannot be paid with future live rewards).".to_string());
            state.log("Rule 8.3.7, Rule 8.3.8, Rule 8.3.9: Performance Phase: Logic timing after live start.".to_string());
        }
        let ctx = AbilityContext {
            source_card_id: -1,
            player_id: p_idx as u8,
            activator_id: p_idx as u8,
            area_idx: -1,
            trigger_type: TriggerType::OnLiveStart,
            ..Default::default()
        };
        state.trigger_abilities(db, TriggerType::OnLiveStart, &ctx);
        if state.phase == Phase::Response {
            return;
        }
    }

    if state.players[p_idx].live_zone.iter().all(|&c| c < 0) {
        advance_from_performance(state);
        return;
    }

    // 8.3.10-11 Yell
    // Initialize breakdown logs Early to capture sources before they are moved by triggers
    // HEADLESS PATH: Skip all UI data structures in headless mode
    let is_headless = state.ui.headless;
    
    let mut heart_breakdown = Vec::new();
    let mut blade_breakdown = Vec::new();
    let mut heart_sources: Vec<SourceInfo> = Vec::new();
    let mut allocations = Vec::new();
    let mut transform_logs = Vec::new();
    let mut member_summary: std::collections::HashMap<(usize, i32), Value> = std::collections::HashMap::new();
    
    // HEADLESS OPTIMIZATION: requirement_logs is never populated - skip entirely
    // Old code: let requirement_logs: Vec<serde_json::Value> = Vec::new();
    
    // Only build UI data structures when not in headless mode
    if !is_headless {
        for i in 0..3 {
            let cid = state.players[p_idx].stage[i];
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    member_summary.insert(
                        (i, cid),
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
    }

    let mut total_blades = 0;
    if !state.ui.silent && !is_headless {
        state.log("Rule 8.3.10: Summing blades of active members.".to_string());
    }
    // Apply Cheer Mod (Meta Rule)
    total_blades += state.players[p_idx].cheer_mod_count as u32;

    for i in 0..3 {
        let eff_b = state.get_effective_blades(p_idx, i, db, 0);
        let cid = state.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                if !is_headless && eff_b > 0 {
                    blade_breakdown.push(json!({
                        "source": m.name,
                        "source_id": cid,
                        "value": eff_b,
                        "type": "member"
                    }));
                }

                if !is_headless {
                    if let Some(entry) = member_summary.get_mut(&(i, cid)) {
                        let bonus_b = eff_b as i32 - m.blades as i32;
                        entry["blades"] = json!(eff_b);
                        entry["bonus_blades"] = json!(bonus_b);
                    }

                    let mut slot_blade_buffs: Vec<Value> = state.players[p_idx]
                        .blade_buff_logs
                        .iter()
                        .filter(|&&(_, _, slot)| slot == i as u8)
                        .map(|&(src_cid, amt, _)| {
                            let source_name =
                                db.get_name(src_cid).unwrap_or_else(|| "Effect".to_string());
                            let (ability_text, img) = if let Some(m) = db.get_member(src_cid) {
                                (m.original_text.as_str(), m.img_path.as_str())
                            } else if let Some(l) = db.get_live(src_cid) {
                                (l.original_text.as_str(), l.img_path.as_str())
                            } else {
                                ("", "")
                            };
                            json!({ "source": source_name, "amount": amt, "ability_text": ability_text, "img": img })
                        })
                        .collect();

                    // Scan constant abilities for blade sources - UI only
                    // HEADLESS: Skip ability scanning for UI data
                    if !is_headless && !db.is_vanilla {
                    for other_slot in 0..3 {
                        let other_cid = state.players[p_idx].stage[other_slot];
                        if other_cid < 0 {
                            continue;
                        }
                        if let Some(other_m) = db.get_member(other_cid) {
                            for ab in &other_m.abilities {
                                if ab.trigger == TriggerType::Constant {
                                    let ctx = AbilityContext {
                                        source_card_id: other_cid,
                                        player_id: p_idx as u8,
                                        activator_id: p_idx as u8,
                                        area_idx: other_slot as i16,
                                        target_slot: i as i16,
                                        ..Default::default()
                                    };
                                    if ab
                                        .conditions
                                        .iter()
                                        .all(|c| check_condition(state, db, p_idx, c, &ctx, 1))
                                    {
                                        if let Some(frame_program) = ab.frame_program.as_ref() {
                                            for frame in &frame_program.frames {
                                                let bop = frame.opcode();
                                                let bv = frame.value();
                                                let bs = frame.slot();
                                                let mut targets_us = false;
                                                if bs == 1 {
                                                    targets_us = true;
                                                } else if (bs == 4 || bs == 0) && other_slot == i {
                                                    targets_us = true;
                                                } else if bs == 10 && i as i16 == ctx.target_slot {
                                                    targets_us = true;
                                                }
                                                if (bop == O_ADD_BLADES || bop == O_BUFF_POWER)
                                                    && targets_us
                                                    && bv > 0
                                                {
                                                    slot_blade_buffs.push(json!({
                                                        "source": &other_m.name,
                                                        "amount": bv,
                                                        "ability_text": ab.raw_text.as_str(),
                                                        "img": other_m.img_path.as_str()
                                                    }));
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    }
                    // Wave 2: Granted abilities for blade sources - UI only
                    if !is_headless && !db.is_vanilla {
                    for &(target_cid, source_cid, ab_idx) in &state.players[p_idx].granted_abilities
                    {
                        if target_cid != cid {
                            continue;
                        }
                        if let Some(src_m) = db.get_member(source_cid) {
                            if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                                if ab.trigger == TriggerType::Constant {
                                    let ctx = AbilityContext {
                                        source_card_id: cid,
                                        player_id: p_idx as u8,
                                        activator_id: p_idx as u8,
                                        area_idx: i as i16,
                                        ..Default::default()
                                    };
                                    if ab
                                        .conditions
                                        .iter()
                                        .all(|c| check_condition(state, db, p_idx, c, &ctx, 1))
                                    {
                                        if let Some(frame_program) = ab.frame_program.as_ref() {
                                            for frame in &frame_program.frames {
                                                if frame.opcode() == O_ADD_BLADES
                                                    && frame.value() > 0
                                                {
                                                    slot_blade_buffs.push(json!({
                                                        "source": format!("Granted: {}", src_m.name),
                                                        "amount": frame.value(),
                                                        "ability_text": ab.raw_text.as_str(),
                                                        "img": src_m.img_path.as_str()
                                                    }));
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    }
                    if let Some(entry) = member_summary.get_mut(&(i, cid)) {
                        entry["ability_blade_bonuses"] = json!(slot_blade_buffs);
                    }
                }
                total_blades += eff_b;
            }
        }
    }

    if !state.performance_yell_done[p_idx] {
        if !state.ui.silent {
            state.log(format!(
                "Rule 8.3.11: Player {} performs Yell ({} blades).",
                p_idx, total_blades
            ));
        }
        // Rule 8.3.10, Rule 8.3.11: Pops from main deck based on blades.
        let yell_count = total_blades;
        let yelled_cards = do_yell(state, db, yell_count);
        if !state.ui.silent && !yelled_cards.is_empty() {
            let mut yelled_names = Vec::new();
            for cid in yelled_cards {
                let cid_i32 = cid as i32;
                if let Some(m) = db.get_member(cid_i32) {
                    yelled_names.push(format!("{} ({})", m.name, m.card_no));
                } else if let Some(l) = db.get_live(cid_i32) {
                    yelled_names.push(format!("{} ({})", l.name, l.card_no));
                } else {
                    yelled_names.push(format!("ID:{}", cid_i32));
                }
            }
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
        let mut printed_h = [0u32; 7];

        let cid = state.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                for k in 0..7 {
                    printed_h[k] = m.hearts[k] as u32;
                }
            }
        }

        // Apply color transforms to member hearts
        for &(src_cid, src_col, dst_col) in &state.players[p_idx].color_transforms {
            if src_col == 0 && (dst_col as usize) < 7 {
                let sum: u32 = eff_h.iter().sum();
                eff_h = [0u32; 7];
                eff_h[dst_col as usize] = sum;

                let printed_sum: u32 = printed_h.iter().sum();
                printed_h = [0u32; 7];
                printed_h[dst_col as usize] = printed_sum;

                if !state.ui.silent && transform_logs.is_empty() {
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

        let cid = state.players[p_idx].stage[i];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                let mut source_base_h = [0u8; 7];
                let mut true_bonus_h = [0u32; 7];
                let mut documented_bonus_h = [0u8; 7];
                for k in 0..7 {
                    let base_amt = printed_h[k].min(eff_h[k]);
                    source_base_h[k] = base_amt.min(u8::MAX as u32) as u8;
                    true_bonus_h[k] = eff_h[k].saturating_sub(base_amt);
                }

                // Calculate documented bonus hearts from heart_buff_logs
                for &(_, amt, color, slot) in &state.players[p_idx].heart_buff_logs {
                    if slot == i as u8 && (color as usize) < 7 {
                        documented_bonus_h[color as usize] =
                            documented_bonus_h[color as usize].saturating_add(amt as u8);
                    }
                }

                if eff_h.iter().any(|&v| v > 0) {
                    if !is_headless {
                        let mut h8 = [0u8; 7];
                        for k in 0..7 {
                            h8[k] = eff_h[k] as u8;
                        }
                        heart_sources.push(SourceInfo {
                            id: cid,
                            slot: i as i16,
                            name: m.name.clone(),
                            hearts: h8,
                            base_hearts: source_base_h,
                            documented_bonus_hearts: documented_bonus_h,
                            is_yell: false,
                        });

                        heart_breakdown.push(json!({
                            "source": m.name,
                            "source_id": cid,
                            "value": eff_h,
                            "type": "member"
                        }));
                    }

                    let mut slot_heart_buffs = if !is_headless {
                        state.players[p_idx]
                        .heart_buff_logs
                        .iter()
                        .filter(|&&(_, _, _, slot)| slot == i as u8)
                        .map(|&(src_cid, amt, color, _)| {
                            let source_name =
                                db.get_name(src_cid).unwrap_or_else(|| "Effect".to_string());
                            let (ability_text, img) = if let Some(m) = db.get_member(src_cid) {
                                (m.original_text.as_str(), m.img_path.as_str())
                            } else if let Some(l) = db.get_live(src_cid) {
                                (l.original_text.as_str(), l.img_path.as_str())
                            } else {
                                ("", "")
                            };
                            json!({ "source": source_name, "amount": amt, "color": color, "ability_text": ability_text, "img": img })
                        })
                        .collect::<Vec<_>>()
                    } else {
                        Vec::new()
                    };

                    // Scan constant abilities for heart sources - UI only
                    // HEADLESS: Skip ability scanning
                    if !is_headless {
                    for other_slot in 0..3 {
                        let other_cid = state.players[p_idx].stage[other_slot];
                        if other_cid < 0 {
                            continue;
                        }
                        if let Some(other_m) = db.get_member(other_cid) {
                            for ab in &other_m.abilities {
                                if ab.trigger == TriggerType::Constant {
                                    let ctx = AbilityContext {
                                        source_card_id: other_cid,
                                        player_id: p_idx as u8,
                                        activator_id: p_idx as u8,
                                        area_idx: other_slot as i16,
                                        target_slot: i as i16,
                                        ..Default::default()
                                    };
                                    if ab
                                        .conditions
                                        .iter()
                                        .all(|c| check_condition(state, db, p_idx, c, &ctx, 1))
                                    {
                                        if let Some(frame_program) = ab.frame_program.as_ref() {
                                            for frame in &frame_program.frames {
                                                let bop = frame.opcode();
                                                let bv = frame.value();
                                                let bs = frame.slot();
                                                let mut targets_us = false;
                                                if bs == 1 {
                                                    targets_us = true;
                                                } else if (bs == 4 || bs == 0)
                                                    && other_slot == i
                                                {
                                                    targets_us = true;
                                                } else if bs == 10
                                                    && i as i16 == ctx.target_slot
                                                {
                                                    targets_us = true;
                                                }
                                                if bop == O_ADD_HEARTS && targets_us && bv > 0 {
                                                    let color = semantic_heart_color_from_frame(
                                                        &frame.components(),
                                                        ctx.selected_color as usize,
                                                    );
                                                    if color < 7 {
                                                    slot_heart_buffs.push(json!({
                                                        "source": &other_m.name,
                                                        "amount": bv,
                                                        "color": color,
                                                        "ability_text": ab.raw_text.as_str(),
                                                        "img": other_m.img_path.as_str()
                                                    }));
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    } // End of UI-only ability scanning block
                    }
                    // Wave 2: Granted abilities for heart sources - UI only
                    if !is_headless {
                    for &(target_cid, source_cid, ab_idx) in
                        &state.players[p_idx].granted_abilities
                    {
                        if target_cid != cid {
                            continue;
                        }
                        if let Some(src_m) = db.get_member(source_cid) {
                            if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                                if ab.trigger == TriggerType::Constant {
                                    let ctx = AbilityContext {
                                        source_card_id: cid,
                                        player_id: p_idx as u8,
                                        activator_id: p_idx as u8,
                                        area_idx: i as i16,
                                        ..Default::default()
                                    };
                                    if ab
                                        .conditions
                                        .iter()
                                        .all(|c| check_condition(state, db, p_idx, c, &ctx, 1))
                                    {
                                        if let Some(frame_program) = ab.frame_program.as_ref() {
                                            for frame in &frame_program.frames {
                                                if frame.opcode() == O_ADD_HEARTS
                                                    && frame.value() > 0
                                                {
                                                    let color = semantic_heart_color_from_frame(
                                                        &frame.components(),
                                                        ctx.selected_color as usize,
                                                    );
                                                    if color < 7 {
                                                        slot_heart_buffs.push(json!({
                                                        "source": format!("Granted: {}", src_m.name),
                                                        "amount": frame.value(),
                                                        "color": color,
                                                        "ability_text": ab.raw_text.as_str(),
                                                        "img": src_m.img_path.as_str()
                                                    }));
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }

                    if let Some(entry) = member_summary.get_mut(&(i, cid)) {
                        entry["hearts"] = json!(eff_h);
                        entry["base_hearts"] = json!(source_base_h);
                        entry["bonus_hearts"] = json!(true_bonus_h);
                        entry["note_icons"] = json!(m.note_icons);
                        entry["base_notes"] = json!(m.note_icons);
                        entry["ability_heart_bonuses"] = json!(slot_heart_buffs);
                    }
                    }
                }
                note_icons += m.note_icons;
            }
        }
        for h in 0..7 {
            total_hearts[h] += eff_h[h] as u8;
        }
    }
    for &cid in state.players[p_idx].yell_cards.iter() {
        // Only fetch card data if we need it for UI
        let (bh, ni) = if !is_headless {
            if let Some(m) = db.get_member(cid) {
                (m.blade_hearts, m.note_icons)
            } else if let Some(l) = db.get_live(cid) {
                (l.blade_hearts, l.note_icons)
            } else {
                ([0u8; 7], 0)
            }
        } else {
            // In silent mode, we don't need names for logging - just compute hearts
            if let Some(m) = db.get_member(cid) {
                (m.blade_hearts, m.note_icons)
            } else if let Some(l) = db.get_live(cid) {
                (l.blade_hearts, l.note_icons)
            } else {
                ([0u8; 7], 0)
            }
        };

        // Log yell card contributions
        if !is_headless {
            // Only compute names when needed for UI logging
            let name = if let Some(m) = db.get_member(cid) {
                m.name.as_str()
            } else if let Some(l) = db.get_live(cid) {
                l.name.as_str()
            } else {
                "Unknown"
            };
            let bh_sum: u32 = bh.iter().map(|&h| h as u32).sum();
            if bh_sum > 0 {
                heart_sources.push(SourceInfo {
                    id: cid,
                    slot: -1,
                    name: format!("Yell: {}", name),
                    hearts: bh,
                    base_hearts: bh, // For yells, everything is "base" (printed on yell card)
                    documented_bonus_hearts: [0u8; 7], // Yells don't have documented bonuses
                    is_yell: true,
                });

                heart_breakdown.push(json!({
                    "source": format!("Yell: {}", name),
                    "source_id": cid,
                    "value": bh,
                    "type": "yell"
                }));
            }
        }
        if ni > 0 {
            if !is_headless {
                // Re-fetch name only when needed for UI
                let name = if let Some(m) = db.get_member(cid) {
                    m.name.as_str()
                } else if let Some(l) = db.get_live(cid) {
                    l.name.as_str()
                } else {
                    "Unknown"
                };
                blade_breakdown.push(json!({
                    "source": format!("Yell: {}", name),
                    "source_id": cid,
                    "value": ni,
                    "type": "yell"
                }));
            }
        }

        // Yell cards are excluded from member_summary to focus on stage cards

        let mut adj_bh = [0u32; 7];
        for i in 0..7 {
            adj_bh[i] = bh[i] as u32;
        }

        for &(src_cid, src_col, dst_col) in &state.players[p_idx].color_transforms {
            if src_col == 0 && (dst_col as usize) < 7 {
                let mut sum = 0;
                for i in 0..7 {
                    if i != dst_col as usize {
                        sum += adj_bh[i];
                        adj_bh[i] = 0;
                    }
                }
                adj_bh[dst_col as usize] += sum;

                if !state.ui.silent {
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
        }
        for i in 0..7 {
            total_hearts[i] += adj_bh[i] as u8;
        }
        note_icons += ni;
    }
    state.players[p_idx].current_turn_notes = note_icons;

    if !is_headless {
        state.log("Rule 8.3.12, Rule 8.3.13: Checking timing after Yell.".to_string());
        state.log(format!("Rule 8.3.14: Total Hearts (Live Heart + BladeHeart): {:?}", total_hearts));
        state.log(format!("  Rule 8.3.14: Note Icons: {}", note_icons));
    }

    // 8.3.15-16 Check heart requirements
    if !state.ui.silent {
        state.log("Rule 8.3.15: Verifying heart requirements for each live card.".to_string());
    }
    let mut passed_flags = [false; 3];
    let mut sequential_passed = [false; 3]; // To track filling logic for UI even on failure
    let mut any_failed = false;

    // In this implementation, we consume hearts per live card (8.3.15.1.2)
    let mut remaining_hearts = total_hearts;
    for i in 0..3 {
        if let Some(cid) = state.players[p_idx]
            .live_zone
            .get(i)
            .copied()
            .filter(|&c| c >= 0)
        {
            if let Some(live) = db.get_live(cid) {
                if !state.ui.silent {
                    state.log(format!(
                        "    Live {}: {} - Checking requirements...",
                        i, live.name
                    ));
                }

                let (req_board, _) = get_live_requirements(state, db, p_idx, live);
                if !state.ui.silent {
                    state.log(format!("Rule 8.3.15, Rule 8.3.15.1: Checking requirements for {}: {:?}", live.name, req_board.to_array()));
                    state.log("Rule 8.3.15.1.1: Star icons can be treated as any color.".to_string());
                }
                if check_live_success(state, db, p_idx, live, &remaining_hearts) {
                    let _req_arr = req_board.to_array();

                    if !state.ui.silent {
                        allocate_hearts_for_live(
                            cid,
                            i,
                            &live.name,
                            &req_board,
                            &mut heart_sources,
                            &mut allocations,
                            &mut remaining_hearts,
                        );
                    } else {
                        use super::performance_requirements::consume_hearts_from_pool;
                        consume_hearts_from_pool(&mut remaining_hearts, &req_board.to_array());
                    }
                    if !state.ui.silent {
                        state.log(format!("Rule 8.3.15.1.2: Consuming hearts to meet requirements for {}.", live.name));
                    }
                    passed_flags[i] = true;
                    sequential_passed[i] = true;
                    if !state.ui.silent {
                        state.log(format!("    -> SUCCESS for {}", live.name));
                    }
                } else {
                    if !state.ui.silent {
                        state.log(format!(
                            "    -> FAILED for {} (Hearts or Restrictions)",
                            live.name
                        ));
                    }
                    any_failed = true;
                }
            }
        }
    }

    // Rule 8.3.16 covers this: if any fail, all are discarded.
    // We capture IDs here so we can still report them to UI even if discarded.
    let live_ids_before_discard: Vec<i32> = state.players[p_idx].live_zone.to_vec();

    // Rule 8.3.16: If ANY live card's requirements were not met, discard all live cards.
    if any_failed {
        if !state.ui.silent {
            state.log("  Rule 8.3.16: Performance FAILED. All live cards discarded.".to_string());
        }
        for i in 0..3 {
            if state.players[p_idx].live_zone[i] >= 0 {
                let cid = state.players[p_idx].live_zone[i];
                state.players[p_idx].push_discard_card(cid);
                state.players[p_idx].live_zone[i] = -1;
                passed_flags[i] = false; // Ensure UI reflects failure
            }
        }
    } else {
        if !state.ui.silent {
            state.log("Rule 8.3.16: Performance SUCCESS for all live cards.".to_string());
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
        state.players[p_idx].excess_hearts = remaining_hearts.iter().map(|&x| x as u32).sum();
        state.players[p_idx].excess_hearts_by_color = remaining_hearts;
    } else {
        state.players[p_idx].excess_hearts = 0;
        state.players[p_idx].excess_hearts_by_color = [0; 7];
    }

    if !state.ui.silent {
        state.log("Rule 8.3.17: performance Phase ended. Checking timing.".to_string());
    }

    // --- Store Performance Results for UI ---
    // Rule 8.4.10: Participants change to Rest state
    for i in 0..3 {
        if state.players[p_idx].stage[i] >= 0 {
            state.players[p_idx].set_tapped(i, true);
        }
    }

    // Build UI data only when not silent
    let mut yell_cards_meta = Vec::new();
    if !state.ui.silent {
        for &cid in state.players[p_idx].yell_cards.iter() {
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
    }

    // Calculate total_score directly (needed for game logic)
    let mut live_score: u32 = 0;
    for i in 0..3 {
        if passed_flags[i] {
            if let Some(cid) = live_ids_before_discard.get(i).copied() {
                if cid >= 0 {
                    if let Some(l) = db.get_live(cid) {
                        live_score += l.score as u32;
                    }
                }
            }
        }
    }
    let total_score =
        live_score + note_icons as u32 + state.players[p_idx].live_score_bonus.max(0) as u32;

    // Build performance result data for UI.
    {
        let mut lives_list: Vec<Value> = Vec::new();
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

        let mut score_breakdown: Vec<Value> = Vec::new();
        if live_score > 0 {
            score_breakdown.push(json!({
                "source": "Base Live Score",
                "value": live_score,
                "type": "base"
            }));
        }
        for i in 0..3 {
            if passed_flags[i] {
                if let Some(cid) = live_ids_before_discard.get(i).copied() {
                    if cid >= 0 {
                        if let Some(l) = db.get_live(cid) {
                            score_breakdown.push(json!({
                                "source": format!("Live: {}", l.name),
                                "value": l.score,
                                "type": "base_live"
                            }));
                        }
                    }
                }
            }
        }
        if note_icons > 0 {
            score_breakdown.push(json!({
                "source": "Note Bonus",
                "value": note_icons,
                "type": "note"
            }));
        }
        for &(cid, bonus) in &state.players[p_idx].live_score_bonus_logs {
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
                    "allocations": allocations,
                    "requirements": Vec::<serde_json::Value>::new(),
                    "transforms": transform_logs,
                    "score_bonus_logs": state.players[p_idx].live_score_bonus_logs,
                    "scores": score_breakdown,
                },
                "total_score_bonus": state.players[p_idx].live_score_bonus,
                "total_score": total_score
            }),
        );
    }

    // state.yell_cards.clear(); // REMOVED: Now cleared in untap_all() for persistence
    advance_from_performance(state);
}

// ============================================================================
// MODULE: LIVE RESULT PROCESSING
// ============================================================================

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
        state.log("Rule 8.4, Rule 8.4.1: --- LIVE RESULT PHASE BEGIN: Start triggers ---".to_string());
    }

    let mut scores = [0u32; 2];
    let mut has_success = [false; 2];

    // 1. Judgment Phase: Calculate scores based on SUCCESSFUL lives (still in zone)
    // IMPORTANT: We move this BEFORE triggers so that ON_LIVE_SUCCESS abilities can refer to current turn scores.
    // We only perform this calculation if triggers haven't finished (to allow re-entry)
    if !state.live_result_triggers_done {
        // FAST PATH: In silent+vanilla mode, performance_results is empty - compute directly from state
        let is_silent_vanilla = state.ui.silent && db.is_vanilla;
        
        for p in 0..2 {
            let mut live_score = 0;
            let mut player_has_success = false;
            let mut has_live = false;
            let mut p_score = 0;

            if !state.ui.silent {
                state.log(format!("Rule 8.4.2: Calculating total score for Player {}.", p));
            }

            // OPTIMIZATION: Cache live cards to avoid repeated HashMap lookups
            let live_cards: [Option<(i32, &crate::core::logic::card_db::LiveCard)>; 3] = [
                if state.players[p].live_zone[0] >= 0 { 
                    db.get_live(state.players[p].live_zone[0]).map(|l| (state.players[p].live_zone[0], l)) 
                } else { None },
                if state.players[p].live_zone[1] >= 0 { 
                    db.get_live(state.players[p].live_zone[1]).map(|l| (state.players[p].live_zone[1], l)) 
                } else { None },
                if state.players[p].live_zone[2] >= 0 { 
                    db.get_live(state.players[p].live_zone[2]).map(|l| (state.players[p].live_zone[2], l)) 
                } else { None },
            ];
            
            // FAST PATH: For silent+vanilla, skip JSON snapshot lookup and compute directly
            let perf_res = if is_silent_vanilla {
                None
            } else {
                state.ui.performance_results.get(&(p as u8))
            };
            let live_lives = perf_res.and_then(|res| res.get("lives").and_then(|l| l.as_array()));
            let snapshot_success = if is_silent_vanilla {
                // In vanilla mode, any card still in live_zone passed (failed ones were discarded)
                live_cards.iter().any(|c| c.is_some())
            } else {
                // Check snapshot from check_performance_requirements first
                perf_res
                    .and_then(|res| res.get("success"))
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false)
            };
            
            for i in 0..3 {
                if let Some((_cid, card)) = live_cards[i] {
                    has_live = true;
                    
                    // FAST PATH: In silent+vanilla mode, compute score directly
                    let (snapshot_passed, snapshot_score) = if is_silent_vanilla {
                        // Card is in zone = it passed, use its score directly
                        (true, Some(card.score as u64))
                    } else {
                        // Use snapshot score if available (from check_performance_requirements)
                        let live_res = live_lives.and_then(|lives| lives.get(i));
                        let score = live_res
                            .and_then(|l_res| l_res.get("score"))
                            .and_then(|s| s.as_u64());
                        let passed = live_res
                            .and_then(|l_res| l_res.get("passed"))
                            .and_then(|v| v.as_bool())
                            .unwrap_or(false);
                        (passed, score)
                    };

                    if snapshot_passed || snapshot_score.is_some() {
                        p_score += snapshot_score.unwrap_or(card.score as u64) as u32;
                    }
                }
            }

            if has_live && snapshot_success {
                live_score = p_score;
                player_has_success = true;
            } else if has_live {
                // Rule 8.3.16: Clear zone if snapshot indicates failure
                if !state.ui.silent && state.debug.debug_mode {
                    println!(
                        "[DEBUG] Rule 8.3.16: P{} performance FAILED. Clearing live zone.",
                        p
                    );
                }
                for i in 0..3 {
                    if state.players[p].live_zone[i] >= 0 {
                        let cid = state.players[p].live_zone[i];
                        state.players[p].push_discard_card(cid);
                        state.players[p].live_zone[i] = -1;
                    }
                }
            }

            if player_has_success {
                // FAST PATH: In silent+vanilla mode, compute notes directly from player state
                if is_silent_vanilla {
                    live_score += state.players[p].current_turn_notes as u32;
                } else if let Some(res) = state.ui.performance_results.get(&(p as u8)) {
                    if let Some(vol) = res
                        .get("yell_score_bonus")
                        .and_then(|v| v.as_u64())
                        .or_else(|| res.get("note_icons").and_then(|v| v.as_u64()))
                    {
                        live_score += vol as u32;
                    }
                }
                has_success[p] = true;
                if !state.ui.silent {
                    state.log(format!("Rule 8.4.2.1: Note icons and score bonuses summed for Player {}.", p));
                }
            }

            // Pool O_BOOST_SCORE from constant abilities
            // OPTIMIZATION: Cache stage cards to avoid repeated HashMap lookups
            let stage_cards: [Option<(i32, &crate::core::logic::card_db::MemberCard)>; 3] = [
                if state.players[p].stage[0] >= 0 { 
                    db.get_member(state.players[p].stage[0]).map(|m| (state.players[p].stage[0], m)) 
                } else { None },
                if state.players[p].stage[1] >= 0 { 
                    db.get_member(state.players[p].stage[1]).map(|m| (state.players[p].stage[1], m)) 
                } else { None },
                if state.players[p].stage[2] >= 0 { 
                    db.get_member(state.players[p].stage[2]).map(|m| (state.players[p].stage[2], m)) 
                } else { None },
            ];
            
            let mut constant_bonuses = std::collections::HashMap::new();
            
            // FAST PATH: Use pre-computed unconditional score boosts
            for slot in 0..STAGE_SLOT_COUNT {
                if let Some((cid, m)) = stage_cards[slot] {
                    // Only check conditional abilities
                    for ab in &m.abilities {
                        if ab.trigger != TriggerType::Constant {
                            continue;
                        }
                        
                        // Skip abilities with no conditions (already counted in unconditional_score_boost)
                        if ab.conditions.is_empty() {
                            continue;
                        }
                        
                        let ctx = AbilityContext {
                            source_card_id: cid,
                            player_id: p as u8,
                            activator_id: p as u8,
                            area_idx: slot as i16,
                            ..Default::default()
                        };
                        
                        if ab.conditions
                            .iter()
                            .all(|c| state.check_condition(db, p, c, &ctx, 1))
                        {
                            for frame in ab.frames() {
                                let frame_data = frame.components();
                                if frame_data.opcode == O_BOOST_SCORE {
                                    *constant_bonuses.entry(cid).or_insert(0) +=
                                        frame_data.value;
                                }
                            }
                        }
                    }
                }
            }
            
            // Pool O_BOOST_SCORE from granted constant abilities
            for &(target_cid, source_cid, ab_idx) in &state.players[p].granted_abilities {
                if let Some(slot) = state.players[p]
                    .stage
                    .iter()
                    .position(|&stage_cid| stage_cid == target_cid)
                {
                    if let Some(src_m) = db.get_member(source_cid) {
                        if let Some(ab) = src_m.abilities.get(ab_idx as usize) {
                            if ab.trigger == TriggerType::Constant {
                                let ctx = AbilityContext {
                                    source_card_id: target_cid,
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
                                    for frame in ab.frames() {
                                        let frame_data = frame.components();
                                        if frame_data.opcode == O_BOOST_SCORE {
                                            *constant_bonuses.entry(source_cid).or_insert(0) +=
                                                frame_data.value;
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Calculate total constant bonus BEFORE applying to score
            let total_constant_bonus: i32 = constant_bonuses.values().sum();

            scores[p] = live_score
                + total_constant_bonus.max(0) as u32
                + state.players[p].live_score_bonus.max(0) as u32;

            // CRITICAL: Update player score in state so conditions (opcode 220) can refer to it.
            state.players[p].score = scores[p];

            if !state.ui.silent {
                state.log(format!("Rule 8.4.3, Rule 8.4.3.1, Rule 8.4.3.2, Rule 8.4.3.3, Rule 8.4.4, Rule 8.4.5: Score determination logic finished for Player {}.", p));

                let mut score_breakdown = Vec::new();

                // 1. Base Score (Lives)
                score_breakdown.push(json!({
                    "source": "Base (Lives)",
                    "value": live_score.saturating_sub(state.players[p].current_turn_notes),
                    "type": "base"
                }));

                // 2. Note Bonus
                if state.players[p].current_turn_notes > 0 {
                    score_breakdown.push(json!({
                        "source": "Note Bonus",
                        "value": state.players[p].current_turn_notes,
                        "type": "note"
                    }));
                }

                // 3. Constant Bonuses
                for (cid, bonus) in &constant_bonuses {
                    let name = db
                        .get_member(*cid)
                        .map(|m| m.name.as_str())
                        .unwrap_or("Unknown");
                    score_breakdown.push(json!({
                        "source": name,
                        "source_id": cid,
                        "value": bonus,
                        "type": "constant_ability"
                    }));
                }

                // 4. Triggered/Activated Bonuses (live_score_bonus_logs)
                for &(cid, bonus) in &state.players[p].live_score_bonus_logs {
                    let name = if cid >= 0 {
                        db.get_member(cid)
                            .map(|m| m.name.as_str())
                            .or_else(|| db.get_live(cid).map(|l| l.name.as_str()))
                            .unwrap_or("Unknown")
                    } else {
                        "Ability Effect"
                    };
                    score_breakdown.push(json!({
                        "source": name,
                        "source_id": cid,
                        "value": bonus,
                        "type": "triggered_ability"
                    }));
                }

                if let Some(res) = state.ui.performance_results.get_mut(&(p as u8)) {
                    if let serde_json::Value::Object(ref mut map) = res {
                        if let Some(serde_json::Value::Object(ref mut b_map)) = map.get_mut("breakdown")
                        {
                            b_map.insert("scores".to_string(), json!(score_breakdown));
                        }
                    }
                }
            }
        }
    } else {
        // Triggers already in progress, just pull scores from state
        for p in 0..2 {
            scores[p] = state.players[p].score;
            // FAST PATH: In silent+vanilla mode, use has_success already computed
            if !(state.ui.silent && db.is_vanilla) {
                has_success[p] = state
                    .ui
                    .performance_results
                    .get(&(p as u8))
                    .and_then(|res| res.get("success"))
                    .and_then(|v| v.as_bool())
                    .unwrap_or(false);
            }
        }
    }

    // 0. Trigger ON_LIVE_SUCCESS for successful performances (Rule 8.3.15 sequence completion)
    // We iterate through players and slots, using a mask to track which cards have already triggered
    // This allows us to resume correctly if an ability (like Kimi no Kokoro) pauses for input.
    // FAST PATH: In silent+vanilla mode, use has_success directly without JSON lookup
    let is_silent_vanilla = state.ui.silent && db.is_vanilla;
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;
        let p_success = if is_silent_vanilla {
            // In silent+vanilla, has_success is already correctly set from direct computation
            has_success[p]
        } else {
            state
                .ui
                .performance_results
                .get(&(p as u8))
                .and_then(|res| res.get("success"))
                .and_then(|v| v.as_bool())
                .unwrap_or(false)
        };

        if p_success {
            // Use bit 7 for "broad trigger done"
            if (state.live_result_processed_mask[p] & 0x80) == 0 {
                state.live_result_processed_mask[p] |= 0x80;

                if !state.ui.silent {
                    state.log(format!("Rule 11.5, Rule 11.5.1, Rule 11.5.2: Broadcasting [ライブ成功時] (On Live Success) triggers for player {}.", p));
                    state.log(format!("Rule 8.4.1, Rule 8.4.2, Rule 8.4.3, Rule 8.4.4, Rule 8.4.6: Player {} live SUCCESS event and score resolution.", p));
                }
                state.trigger_event(db, TriggerType::OnLiveSuccess, p, -1, -1, 0, -1);
                if state.phase == Phase::Response {
                    return;
                }
            }
        }
    }

    // All triggers are done.
    state.live_result_triggers_done = true;

    // CRITICAL: Recalculate scores AFTER triggers have potentially boosted live_score_bonus
    for p in 0..2 {
        scores[p] = state.players[p].score;
    }

    // DETERMINATION OF LEAD based on updated scores
    let p0_wins = has_success[0] && (!has_success[1] || scores[0] >= scores[1]);
    let p1_wins = has_success[1] && (!has_success[0] || scores[1] >= scores[0]);

    if !state.ui.silent && state.debug.debug_mode {
        println!(
            "[DEBUG] Rule 8.4.6: p0_wins={}, p1_wins={}, has_success={:?}, scores={:?}",
            p0_wins, p1_wins, has_success, scores
        );
    }

    // Update performance results with final p0_wins/p1_wins and triggered abilities
    // Only build abilities JSON when not in silent mode
    if !state.ui.silent {
        for p in 0..2 {
            let abilities: Vec<_> = state.players[p]
                .perf_triggered_abilities
                .iter()
                .map(|&(cid, ab_idx, trig)| {
                    let card_name: String = db
                        .get_member(cid)
                        .map(|m| m.name.clone())
                        .or_else(|| db.get_live(cid).map(|l| l.name.clone()))
                        .unwrap_or_else(|| format!("Card#{}", cid));
                    let trigger_label = crate::core::logic::interpreter::logging::trigger_as_str(trig);
                    json!({
                        "source_card_id": cid,
                        "card_name": card_name,
                        "name": format!("【{}】", trigger_label),
                        "id": ab_idx
                    })
                })
                .collect();

            if let Some(res) = state.ui.performance_results.get_mut(&(p as u8)) {
                if let serde_json::Value::Object(ref mut map) = res {
                    map.insert("total_score".to_string(), json!(scores[p]));
                    map.insert("triggered_abilities".to_string(), json!(abilities));
                    map.insert("p0_wins".to_string(), json!(p0_wins));
                    map.insert("p1_wins".to_string(), json!(p1_wins));
                }
            }
        }
    } else {
        // Silent mode: just insert minimal data.
        for p in 0..2 {
            if let Some(res) = state.ui.performance_results.get_mut(&(p as u8)) {
                if let serde_json::Value::Object(ref mut map) = res {
                    map.insert("total_score".to_string(), json!(scores[p]));
                    map.insert("p0_wins".to_string(), json!(p0_wins));
                    map.insert("p1_wins".to_string(), json!(p1_wins));
                }
            }
        }
    }

    // Save current results to history only if a performance actually occurred AND not in silent mode
    // In silent mode, we don't need to track history - it just wastes memory and CPU
    if !state.ui.performance_results.is_empty() && !state.ui.silent {
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

    // HEADLESS OPTIMIZATION: Skip cloning performance_results in silent mode
    // In silent mode, we don't need to preserve UI data between phases
    if !state.ui.silent {
        state.ui.last_performance_results = state.ui.performance_results.clone();
    } else {
        // In silent mode, just clear it to save memory
        state.ui.last_performance_results.clear();
    }

    if !state.ui.silent {
        state.log(format!(
            "Rule 8.4.6: P0 Score: {} (Success: {} wins: {})",
            scores[0], has_success[0], p0_wins
        ));
        state.log(format!(
            "Rule 8.4.6: P1 Score: {} (Success: {} wins: {})",
            scores[1], has_success[1], p1_wins
        ));
        state.log("Rule 8.4.6.1, Rule 8.4.6.2: Final Lead determined based on comparative scores.".to_string());
    }

    // 2. Handling Winners (Rule 8.4.7)
    if !state.ui.silent {
        state.log("Rule 8.4.7: Moving won live cards to success pile.".to_string());
    }
    let mut choices_pending = false;
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;
        let wins = if p == 0 { p0_wins } else { p1_wins };
        if wins && !state.obtained_success_live[p] {
            state.obtained_success_live[p] = true;
            // Use performance_results snapshot instead of re-checking hearts
            // Rule 8.3.15-16: Cards that passed are still in live_zone, failed cards were already discarded
            // FAST PATH: In silent+vanilla mode, all cards in live_zone passed (no JSON lookup needed)
            let perf_res = if is_silent_vanilla { None } else { state.ui.performance_results.get(&(p as u8)) };
            let lives_snapshot = perf_res.and_then(|res| res.get("lives").and_then(|l| l.as_array()));
            let mut valid_candidates: SmallVec<[usize; 3]> = SmallVec::new();
            for i in 0..3 {
                let cid = state.players[p].live_zone[i];
                if cid < 0 {
                    continue;
                }
                if let Some(card) = db.get_live(cid) {
                    // Check for prevention effects
                    if state.players[p].prevent_success_pile_set() != 0 {
                        continue;
                    }
                    if card.abilities.iter().any(|a| {
                        a.effects
                            .iter()
                            .any(|e| e.effect_type == EffectType::PreventSetToSuccessPile)
                    }) {
                        continue;
                    }

                    // FAST PATH: In silent+vanilla mode, card in zone = passed
                    if is_silent_vanilla {
                        valid_candidates.push(i);
                        continue;
                    }

                    // Use the "passed" flag from performance_results snapshot
                    // This is the authoritative record from the performance phase (Rule 8.3.15)
                    if lives_snapshot
                        .and_then(|lives| lives.get(i))
                        .and_then(|live_res| live_res.get("passed"))
                        .and_then(|v| v.as_bool())
                        .unwrap_or(false)
                    {
                        valid_candidates.push(i);
                        continue;
                    }

                    // Fallback: if card is still in live_zone after performance phase,
                    // it passed the requirements (Rule 8.3.16 already discarded failed cards)
                    valid_candidates.push(i);
                }
            }

            // Rule 8.4.7.1:
            // If scores are tied (Both Win), a player who ALREADY has 2+ success lives
            // does NOT move a card to success. (Catch-up mechanic).
            let is_comparative_tie = p0_wins && p1_wins;
            let is_at_limit = state.players[p].success_lives.len() >= 2;
            let is_tie_capped = is_comparative_tie && is_at_limit;

            if is_tie_capped {
                if !state.ui.silent {
                    state.log(format!(
                        "  Rule 8.4.7.1: Tie Penalty - P{} already at 2 lives. No move.",
                        p
                    ));
                }
            } else if state.players[p].success_lives.len() >= 3 {
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
                let cid = state.players[p].live_zone[target_idx];

                state.players[p].success_lives.push(cid as i32);
                if cid == 111 {
                    state.players[p].push_discard_card(cid);
                }
                state.check_win_condition(); // NEW: Immediate win check
                state.players[p].live_zone[target_idx] = -1;
                if !state.ui.silent {
                    state.log(format!(
                        "Rule 8.4.7: P{} obtained Success Live: Card ID {}",
                        p, cid
                    ));
                    state.log("Rule 8.4.9: Checking timing after scoring success live.".to_string());
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

// ============================================================================
// MODULE: RESULT FINALIZATION
// ============================================================================

pub fn finalize_live_result(state: &mut GameState) {
    for p in 0..2 {
        let success_count = state.players[p].success_lives.len() as i32;
        let perf_res = state.ui.performance_results.get(&(p as u8));
        let lives_snapshot = perf_res
            .and_then(|res| res.get("lives"))
            .and_then(|lives| lives.as_array());
        let resolved_live_score = lives_snapshot
            .map(|lives| {
                lives
                    .iter()
                    .filter(|live| {
                        live.get("passed")
                            .and_then(|value| value.as_bool())
                            .unwrap_or(false)
                    })
                    .map(|live| {
                        live.get("score")
                            .and_then(|value| value.as_i64())
                            .unwrap_or(0) as i32
                    })
                    .sum::<i32>()
            })
            .unwrap_or(0);
        let live_score_bonus = perf_res
            .and_then(|res| res.get("total_score_bonus"))
            .and_then(|value| value.as_i64())
            .unwrap_or(0) as i32;

        if !state.ui.silent {
            state.log("Rule 8.3.17, Q232: Score icons add to total performance score, not live card score.".to_string());
            if resolved_live_score + live_score_bonus <= 0 && (resolved_live_score != 0 || live_score_bonus != 0) {
                state.log("Rule 8.4.6, Q231: Total performance score capped at minimum 0.".to_string());
            }
        }
        state.players[p].score = (state.players[p].score as i32)
            .max(success_count.max(resolved_live_score + live_score_bonus))
            .max(0) as u32;
    }

    // 8.4.8 Cleanup all live zones
    if !state.ui.silent {
        state.log("Rule 8.4.8: Cleaning up all cards from Live Zone and Resolution Area.".to_string());
    }
    for i in 0..2 {
        let p = (state.first_player as usize + i) % 2;

        // Debug output only in debug mode and not silent
        if state.debug.debug_mode && !state.ui.silent {
            println!("DEBUG: Player {} live_zone before cleanup: {:?}", p, state.players[p].live_zone);
        }

        for i in 0..3 {
            if state.players[p].live_zone[i] >= 0 {
                let cid = state.players[p].live_zone[i];
                if state.debug.debug_mode && !state.ui.silent {
                    println!("DEBUG: Moving card {} from live_zone[{}] to discard", cid, i);
                }
                state.players[p].push_discard_card(cid);
                state.players[p].live_zone[i] = -1;
            }
        }

        // Rule 8.4.8: Cleanup all cards from stage energy and move to discard
        for i in 0..3 {
            while let Some(cid) = state.players[p].stage_energy[i].pop() {
                state.players[p].push_discard_card(cid);
            }
            state.players[p].sync_stage_energy_count(i);
        }

        state.players[p].current_turn_notes = 0;
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
        if !state.ui.silent {
            state.log("Rule 8.4.8, Rule 8.4.9: Processing cleanup and post-scoring triggers.".to_string());
            state.log("Rule 8.4.11, Rule 8.4.12: Expiring turn-based effects and checking loop conditions.".to_string());
            state.log("Rule 8.4.13, Rule 8.4.14: Turn cycle phase transition complete.".to_string());
        }
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
    for p in 0..2 {
        state.players[p].perf_triggered_abilities.clear();
    }
}
