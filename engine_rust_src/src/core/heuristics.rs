use crate::core::logic::{
    CardDatabase, GameState, LiveCard, Phase, FLAG_CHARGE, FLAG_DRAW, FLAG_RECOVER, FLAG_SEARCH,
    FLAG_WIN_COND,
};
#[cfg(feature = "extension-module")]
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

#[cfg_attr(feature = "extension-module", pyclass(get_all, set_all))]
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct HeuristicConfig {
    pub weight_live_score: f32,
    pub weight_success_bonus: f32,
    pub weight_member_cost: f32,
    pub weight_heart: f32,
    pub weight_slot_bonus: f32,
    pub weight_slot_penalty: f32,
    pub weight_blade: f32,
    pub weight_draw_potential: f32,
    pub weight_vol_bonus: f32,
    pub weight_discard_bonus: f32,
    pub weight_stage_ability: f32,
    pub weight_untapped_bonus: f32,
    pub weight_synergy_group: f32,
    pub weight_synergy_center: f32,
    pub weight_mill_bonus: f32,
    pub weight_live_filter: f32,
    pub scaling_factor: f32,
}

impl Default for HeuristicConfig {
    fn default() -> Self {
        Self {
            weight_live_score: 10.0,
            weight_success_bonus: 20.0,
            weight_member_cost: 0.1,
            weight_heart: 0.5,
            weight_slot_bonus: 0.1,
            weight_slot_penalty: 0.05,
            weight_blade: 0.1, // Normal focus
            weight_draw_potential: 0.1,
            weight_vol_bonus: 2.0,
            weight_discard_bonus: 0.1,
            weight_stage_ability: 1.0,
            weight_untapped_bonus: 1.05,
            weight_synergy_group: 0.05,
            weight_synergy_center: 0.2,
            weight_mill_bonus: 0.0,
            weight_live_filter: 0.0, // Never penalize lives; keep them all
            scaling_factor: 0.5,     // Significantly increased sensitivity
        }
    }
}

#[cfg(feature = "extension-module")]
#[pymethods]
impl HeuristicConfig {
    #[new]
    fn new() -> Self {
        Self::default()
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DeckStats {
    pub avg_hearts: [f32; 7],
    pub avg_notes: f32,
    pub avg_draw: f32,
    pub count: f32,
}

#[cfg_attr(feature = "extension-module", pyclass(eq, eq_int))]
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum EvalMode {
    Normal,
    Solitaire,
    Blind,
    TerminalOnly,
}

pub trait Heuristic: Send + Sync {
    fn name(&self) -> &str;
    fn evaluate(
        &self,
        state: &GameState,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        eval_mode: EvalMode,
        p0_deck_stats: Option<DeckStats>,
        p1_deck_stats: Option<DeckStats>,
    ) -> f32;
}

pub struct LegacyHeuristic {
    pub config: HeuristicConfig,
}

impl Default for LegacyHeuristic {
    fn default() -> Self {
        Self {
            config: HeuristicConfig::default(),
        }
    }
}

impl Heuristic for LegacyHeuristic {
    fn name(&self) -> &str {
        "LegacyHeuristic"
    }
    fn evaluate(
        &self,
        state: &GameState,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        _eval_mode: EvalMode,
        _p0_deck_stats: Option<DeckStats>,
        _p1_deck_stats: Option<DeckStats>,
    ) -> f32 {
        let score0 = self.evaluate_player(state, db, 0, p0_baseline);
        let score1 = self.evaluate_player(state, db, 1, p1_baseline);
        ((score0 - score1) + 1.0) / 2.0
    }
}

pub struct OriginalHeuristic {
    pub config: HeuristicConfig,
}

impl Default for OriginalHeuristic {
    fn default() -> Self {
        Self {
            config: HeuristicConfig::default(),
        }
    }
}

impl Heuristic for OriginalHeuristic {
    fn name(&self) -> &str {
        "OriginalHeuristic"
    }
    fn evaluate(
        &self,
        state: &GameState,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        eval_mode: EvalMode,
        p0_deck_stats: Option<DeckStats>,
        p1_deck_stats: Option<DeckStats>,
    ) -> f32 {
        self.heuristic_eval(
            state,
            db,
            p0_baseline,
            p1_baseline,
            eval_mode,
            p0_deck_stats,
            p1_deck_stats,
        )
    }
}

impl LegacyHeuristic {
    fn evaluate_player(
        &self,
        state: &GameState,
        db: &CardDatabase,
        p_idx: usize,
        baseline_score: u32,
    ) -> f32 {
        let p = &state.players[p_idx];
        let mut score = 0.0;

        // 1. Success Lives (Goal) - 0.5 per live
        score += p.success_lives.len() as f32 * 0.5;

        // 2. Bonus for clearing a live this turn - Significant reward for immediate progress
        if p.success_lives.len() > baseline_score as usize {
            score += 0.4; // Increased from 0.3
        }

        // 3. Power on Board (Capabilities) - 0.02 per blade
        let mut my_power = 0;
        for i in 0..3 {
            my_power += state.get_effective_blades(p_idx, i, db, 0);
        }
        score += my_power as f32 * 0.02; // Increased from 0.01

        // 4. Energy Zone (Fuel) - 0.05 per energy
        // This was previously missing entirely.
        score += p.energy_zone.len() as f32 * 0.05;

        // 5. Board Hearts / Proximity
        let mut stage_hearts = [0u32; 7];
        for i in 0..3 {
            let h = state.get_effective_hearts(p_idx, i, db, 0);
            let h_arr = h.to_array();
            for color in 0..7 {
                stage_hearts[color] += h_arr[color] as u32;
            }
        }

        // Conservative Yell + Volume Icons estimation
        let mut expected_hearts = stage_hearts;
        expected_hearts[6] += (my_power as f32 * 0.1) as u32;

        let mut num_lives = 0;
        let mut zone_reqs = [0u32; 7];
        for &cid in &p.live_zone {
            if cid >= 0 {
                if let Some(l) = db.get_live(cid) {
                    num_lives += 1;
                    for h in 0..7 {
                        zone_reqs[h] += l.required_hearts[h] as u32;
                    }
                }
            }
        }

        if num_lives > 0 {
            let p_val_yell = self.calculate_proximity_u32(&expected_hearts, &zone_reqs);
            let p_val_board = self.calculate_proximity_u32(&stage_hearts, &zone_reqs);

            if p_val_board >= 0.999 {
                // Guaranteed. Penalize redundancy (encourage playing lives if ready).
                score += 0.4 - (num_lives as f32 - 1.0) * 0.1;
            } else if p_val_yell >= 0.999 {
                // Soft guarantee via Yells.
                score += 0.15;
            } else {
                // Reward based on proximity (squared to favor being closer).
                score += (p_val_yell * p_val_yell) * 0.3;
            }
        }

        // 6. Hand Value (Long term potential)
        let is_mulligan = matches!(
            state.phase,
            crate::core::logic::Phase::MulliganP1 | crate::core::logic::Phase::MulliganP2
        );

        for (i, &cid) in p.hand.iter().enumerate() {
            if is_mulligan && ((p.mulligan_selection >> i) & 1 == 1) {
                // If selected for mulligan, value slightly less than average draw
                score += 0.04;
            } else if let Some(l) = db.get_live(cid) {
                // Live cards in hand are valuable if we can clear them
                score += (self
                    .calculate_proximity_u32(&stage_hearts, &l.required_hearts.map(|v| v as u32))
                    * 0.1)
                    .max(0.04);
            } else {
                // Member cards in hand are generally good (increased from 0.03)
                score += 0.06;
            }
        }

        score
    }

    #[inline]
    fn calculate_proximity_u32(&self, pool: &[u32; 7], req: &[u32; 7]) -> f32 {
        let mut pool_clone = *pool;
        let (sat, tot) = crate::core::hearts::process_hearts(&mut pool_clone, req);
        if tot == 0 {
            return 1.0;
        }
        (sat as f32 / tot as f32).clamp(0.0, 1.0)
    }
}

impl OriginalHeuristic {
    pub fn heuristic_eval(
        &self,
        state: &GameState,
        db: &CardDatabase,
        p0_baseline: u32,
        p1_baseline: u32,
        eval_mode: EvalMode,
        p0_deck_stats: Option<DeckStats>,
        p1_deck_stats: Option<DeckStats>,
    ) -> f32 {
        if eval_mode == EvalMode::TerminalOnly {
            return 0.5;
        }
        let score0 = evaluate_player(state, db, 0, p0_baseline, p0_deck_stats, Some(&self.config));

        if eval_mode == EvalMode::Solitaire {
            return (score0 / 25.0).clamp(0.0, 1.0);
        }

        let score1 = evaluate_player(state, db, 1, p1_baseline, p1_deck_stats, Some(&self.config));
        let mut final_val = (score0 - score1) * self.config.scaling_factor + 0.5;

        let _p0_notes = state.players[0].current_turn_notes;
        let _p1_notes = state.players[1].current_turn_notes;

        if state.phase == Phase::Rps {
            // Pseudo-random tie-breaker for RPS based on turn number and deck lengths
            // This ensures that even if scores are tied, different moves are slightly preferred
            // to break deterministic Rock-vs-Rock loops in greedy agents.
            let p0_seed = (state.players[0].deck.len() as u32).wrapping_shl(8) ^ state.turn as u32;
            let p1_seed = (state.players[1].deck.len() as u32).wrapping_shl(16) ^ state.turn as u32;
            
            // Add a tiny deterministic noise (+/- 0.0001)
            let noise = ((p0_seed.wrapping_sub(p1_seed) % 100) as f32) / 1000000.0;
            final_val += noise;
        }

        final_val.clamp(0.0, 1.0)
    }
}

pub fn evaluate_player(
    state: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    baseline_score: u32,
    deck_stats: Option<DeckStats>,
    config: Option<&HeuristicConfig>,
) -> f32 {
    let default_config = HeuristicConfig::default();
    let cfg = config.unwrap_or(&default_config);

    let p = &state.players[p_idx];
    let mut score = 0.0;

    let mut live_val = 0.0;
    for &cid in &p.success_lives {
        if let Some(l) = db.get_live(cid) {
            live_val += l.score as f32 * cfg.weight_live_score;
        }
    }
    score += live_val;

    if p.success_lives.len() > baseline_score as usize {
        score += cfg.weight_success_bonus;
    }

    let mut stage_hearts = [0u32; 7];
    let mut stage_blades = 0;
    let mut stage_val = 0.0;
    let mut occupied_slots = 0;

    for i in 0..3 {
        let cid = state.players[p_idx].stage[i];
        if cid != -1 {
            occupied_slots += 1;
            if let Some(m) = db.get_member(cid) {
                stage_val += m.cost as f32 * cfg.weight_member_cost;

                // Ability awareness on stage
                let flags = m.ability_flags;
                let mut ability_val = 0.0;

                // Value "engine building" or "pressure" abilities
                if (flags & FLAG_CHARGE) != 0 {
                    ability_val += cfg.weight_stage_ability;
                }
                if (flags & FLAG_DRAW) != 0 {
                    ability_val += cfg.weight_stage_ability * 0.8;
                }
                if (flags & FLAG_SEARCH) != 0 {
                    ability_val += cfg.weight_stage_ability * 0.8;
                }
                if (flags & FLAG_RECOVER) != 0 {
                    ability_val += cfg.weight_stage_ability * 0.5;
                }
                if (flags & FLAG_WIN_COND) != 0 {
                    ability_val += cfg.weight_stage_ability * 1.2;
                }

                // Bonus for being untapped (ready to use)
                if !state.players[p_idx].is_tapped(i) && ability_val > 0.0 {
                    ability_val *= cfg.weight_untapped_bonus;
                }

                // Synergy awareness
                if (m.synergy_flags & crate::core::logic::SYN_FLAG_CENTER) != 0 && i == 1 {
                    ability_val += cfg.weight_synergy_center;
                }

                if (m.synergy_flags & crate::core::logic::SYN_FLAG_GROUP) != 0 {
                    ability_val += cfg.weight_synergy_group;
                }

                stage_val += ability_val;
            }
        }
        let h = state.get_effective_hearts(p_idx, i, db, 0);
        let h_arr = h.to_array();
        for color in 0..7 {
            stage_hearts[color] += h_arr[color] as u32;
        }
        stage_blades += state.get_effective_blades(p_idx, i, db, 0);
    }
    score += stage_val;

    let total_hearts: u32 = stage_hearts.iter().sum();
    let heart_val = total_hearts as f32 * cfg.weight_heart;
    score += heart_val;

    let empty_slots = 3 - occupied_slots;
    let slot_bonus = occupied_slots as f32 * cfg.weight_slot_bonus;
    let slot_penalty = empty_slots as f32 * cfg.weight_slot_penalty;
    score += slot_bonus;
    score -= slot_penalty;

    score += stage_blades as f32 * cfg.weight_blade;

    let stats = if let Some(s) = deck_stats {
        s
    } else {
        calculate_deck_expectations(&p.deck, db)
    };

    let mut expected_yell_count = stage_blades as f32;
    let hand_added_blades = p
        .hand
        .iter()
        .filter_map(|&cid| db.get_member(cid))
        .map(|m| m.blades)
        .sum::<u32>();
    if !p.energy_zone.is_empty() {
        expected_yell_count += (hand_added_blades as f32 / p.hand.len().max(1) as f32).min(2.0);
    }

    let draw_potential = stats.avg_draw * expected_yell_count;
    expected_yell_count += draw_potential * cfg.weight_draw_potential;

    let expected_yell_hearts: Vec<f32> = stats
        .avg_hearts
        .iter()
        .map(|&h| h * expected_yell_count)
        .collect();
    let expected_notes = stats.avg_notes * expected_yell_count;

    let mut max_prob = 0.0;
    for &cid in &p.live_zone {
        if cid >= 0 {
            if let Some(l) = db.get_live(cid) {
                let prob = calculate_live_success_prob(
                    l,
                    &stage_hearts,
                    &expected_yell_hearts,
                    p.heart_req_reductions.to_array(),
                );
                let prob_val = prob * 2000.0;
                score += prob_val;
                if prob > max_prob {
                    max_prob = prob;
                }

                let mut proximity_score = 0.0;
                let mut current_req_board = l.hearts_board;
                for h in 0..7 {
                    let red = p.heart_req_reductions.get_color_count(h);
                    let val =
                        (current_req_board.get_color_count(h) as i32 - red as i32).max(0) as u8;
                    current_req_board.set_color_count(h, val);
                }

                for color in 0..7 {
                    let req = current_req_board.get_color_count(color) as u32;
                    if req > 0 {
                        let has = stage_hearts[color];
                        proximity_score += has.min(req) as f32 / req as f32;
                    }
                }
                let prox_val = proximity_score * 500.0;
                score += prox_val;
            }
        }
    }

    if max_prob > 0.5 {
        let notes_bonus = (expected_notes + p.current_turn_notes as f32) * max_prob * 0.5;
        score += notes_bonus;
    }

    let hand_val = calculate_hand_quality(state, db, p_idx);
    score += hand_val * 1.0;

    let ez_val = p.energy_zone.len() as f32 * 0.5;
    score += ez_val;

    let tapped_energy = p.tapped_energy_mask.count_ones() as usize;
    let tapped_val = tapped_energy as f32 * 5.0; // Reduced from 20.0 to not overwhelm scoring
    score += tapped_val;

    /*
    if !state.ui.silent {
        msg.push_str(&format!("Total: {:.2}", score));
        println!("{}", msg);
    }
    */

    let has_recovery = p.hand.iter().any(|&cid| {
        db.get_member(cid)
            .map_or(false, |m| (m.ability_flags & FLAG_RECOVER) != 0)
    });

    if has_recovery {
        let discard_val = p
            .discard
            .iter()
            .filter(|&&cid| {
                db.get_live(cid).is_some() || db.get_member(cid).map_or(false, |m| m.cost >= 3)
            })
            .count();
        score += discard_val as f32 * cfg.weight_discard_bonus * 5.0; // High bonus if we can recover
    }

    // Phase 2: Milling & Velocity
    // Reward graveyard depth even without immediate recovery (engine scaling)
    if !p.discard.is_empty() {
        score += p.discard.len() as f32 * cfg.weight_mill_bonus;
    }

    // Velocity: Reward nearing end of deck if we have searchers/strong cards left
    if p.deck.len() < 10 && p.deck.len() > 0 {
        score += (10.0 - p.deck.len() as f32) * 0.5;
    }

    // Phase 2: Live Filtering
    // Penalize holding "Impossible" Live cards
    for &cid in &p.hand {
        if let Some(l) = db.get_live(cid) {
            let mut total_req = 0;
            let mut impossible_colors = 0;
            for i in 0..6 {
                let req = (l.required_hearts[i] as i32
                    - p.heart_req_reductions.get_color_count(i) as i32)
                    .max(0) as u32;
                total_req += req;
                if req > 0 && stage_hearts[i] == 0 && stage_blades < 3 {
                    // No board setup for this color and low yell volume
                    impossible_colors += 1;
                }
            }
            if total_req > 8 || impossible_colors > 0 {
                // This card is hard to clear. Penalty makes AI more likely to discard it during effects.
                score -= cfg.weight_live_filter;
            }
        }
    }

    score
}

pub fn calculate_deck_expectations(deck: &[i32], db: &CardDatabase) -> DeckStats {
    if deck.is_empty() {
        return DeckStats::default();
    }

    let mut total_hearts = [0.0; 7];
    let mut total_notes = 0.0;
    let mut total_draw = 0.0;
    let count = deck.len() as f32;

    for &cid in deck {
        if let Some(m) = db.get_member(cid) {
            for i in 0..7 {
                total_hearts[i] += m.blade_hearts[i] as f32;
            }
            total_notes += m.note_icons as f32;
            total_draw += m.draw_icons as f32;
        } else if let Some(l) = db.get_live(cid) {
            for i in 0..7 {
                total_hearts[i] += l.blade_hearts[i] as f32;
            }
            total_notes += l.note_icons as f32;
        }
    }

    DeckStats {
        avg_hearts: total_hearts.map(|v| v / count),
        avg_notes: total_notes / count,
        avg_draw: total_draw / count,
        count,
    }
}

pub fn calculate_live_success_prob(
    live: &LiveCard,
    stage_hearts: &[u32; 7],
    expected_yell_hearts: &[f32],
    reductions: [u8; 7],
) -> f32 {
    let mut needed = live.required_hearts;
    for i in 0..7 {
        needed[i] = (needed[i] as i32 - reductions[i] as i32).max(0) as u8;
    }

    let mut satisfied = 0.0;
    let mut total_req = 0.0;
    let mut wildcards_avail = stage_hearts[6] as f32 + expected_yell_hearts[6];

    for i in 0..6 {
        let req = needed[i] as f32;
        total_req += req;
        let have = stage_hearts[i] as f32 + expected_yell_hearts[i];

        if have >= req {
            satisfied += req;
        } else {
            satisfied += have;
            let deficit = req - have;
            let used_wild = wildcards_avail.min(deficit);
            satisfied += used_wild;
            wildcards_avail -= used_wild;
        }
    }

    let any_req = needed[6] as f32;
    total_req += any_req;

    let used_wild = wildcards_avail.min(any_req);
    satisfied += used_wild;
    let mut remaining_any = any_req - used_wild;

    if remaining_any > 0.0 {
        for i in 0..6 {
            let req = needed[i] as f32;
            let have = stage_hearts[i] as f32 + expected_yell_hearts[i];
            let surplus = (have - req).max(0.0);
            let used = surplus.min(remaining_any);
            satisfied += used;
            remaining_any -= used;
            if remaining_any <= 0.0 {
                break;
            }
        }
    }

    let prob = if total_req > 0.0 {
        let mut p = (satisfied / total_req).clamp(0.0, 1.0);
        p = p.powf(0.5);
        if p >= 1.0 {
            p = 1.2;
        }
        p
    } else {
        1.2
    };

    prob
}

fn calculate_hand_quality(state: &GameState, db: &CardDatabase, p_idx: usize) -> f32 {
    let p = &state.players[p_idx];
    let mut val = 0.0;

    let is_mulligan = match state.phase {
        Phase::MulliganP1 | Phase::MulliganP2 => true,
        _ => false,
    };
    let max_energy = if is_mulligan {
        3
    } else {
        p.energy_zone.len() as u32
    };

    for (i, &cid) in p.hand.iter().enumerate() {
        let card_val = calculate_card_potential(cid, db, max_energy);
        if is_mulligan && ((p.mulligan_selection >> i) & 1u64 == 1) {
            val += 0.4; // Reduced to 0.4 to encourage keeping almost any functional card
        } else {
            val += card_val;
        }
    }
    val
}

fn calculate_card_potential(cid: i32, db: &CardDatabase, max_energy: u32) -> f32 {
    if let Some(m) = db.get_member(cid) {
        let mut score = 0.0;
        let stat_sum: u32 = m.hearts.iter().map(|&x| x as u32).sum();
        score += (m.blades as f32 * 10.0 + stat_sum as f32) / (m.cost as f32 + 1.0);

        if m.cost > max_energy {
            let diff = m.cost - max_energy;
            score -= diff as f32 * 0.5;
        }

        use crate::core::logic::{
            FLAG_BOOST, FLAG_BUFF, FLAG_CHARGE, FLAG_DRAW, FLAG_RECOVER, FLAG_REDUCE, FLAG_SEARCH,
            FLAG_TEMPO, FLAG_TRANSFORM, FLAG_WIN_COND,
        };

        let f = m.ability_flags;
        if (f & FLAG_DRAW) != 0 {
            score += 5.0;
        }
        if (f & FLAG_SEARCH) != 0 {
            score += 5.0;
        }
        if (f & FLAG_RECOVER) != 0 {
            score += 0.5;
        }
        if (f & FLAG_BUFF) != 0 {
            score += 0.4;
        }
        if (f & FLAG_CHARGE) != 0 {
            score += 1.2;
        }
        if (f & FLAG_TEMPO) != 0 {
            score += 0.3;
        }
        if (f & FLAG_REDUCE) != 0 {
            score += 0.6;
        }
        if (f & FLAG_BOOST) != 0 {
            score += 0.6;
        }
        if (f & FLAG_TRANSFORM) != 0 {
            score += 0.4;
        }
        if (f & FLAG_WIN_COND) != 0 {
            score += 1.0;
        }

        if (m.synergy_flags & crate::core::logic::SYN_FLAG_GROUP) != 0 {
            score += 0.3;
        }
        if (m.synergy_flags & crate::core::logic::SYN_FLAG_CENTER) != 0 {
            score += 0.5;
        }
        if (m.cost_flags & crate::core::logic::COST_FLAG_TAP as u32) != 0 {
            score += 0.2;
        }

        score
    } else if let Some(l) = db.get_live(cid) {
        l.score as f32 * 0.2
    } else {
        0.0
    }
}

pub struct SimpleHeuristic;

impl Heuristic for SimpleHeuristic {
    fn name(&self) -> &str {
        "SimpleHeuristic"
    }
    fn evaluate(
        &self,
        state: &GameState,
        _db: &CardDatabase,
        _p0_baseline: u32,
        _p1_baseline: u32,
        _eval_mode: EvalMode,
        _p0_deck_stats: Option<DeckStats>,
        _p1_deck_stats: Option<DeckStats>,
    ) -> f32 {
        let p0 = &state.players[0];
        let p1 = &state.players[1];

        let score0 = p0.success_lives.len() as f32 * 10.0
            + p0.energy_zone.len() as f32 * 0.5
            + p0.hand.len() as f32 * 0.1;
        let score1 = p1.success_lives.len() as f32 * 10.0
            + p1.energy_zone.len() as f32 * 0.5
            + p1.hand.len() as f32 * 0.1;

        if score0 > score1 {
            0.6
        } else if score1 > score0 {
            0.4
        } else {
            0.5
        }
    }
}
