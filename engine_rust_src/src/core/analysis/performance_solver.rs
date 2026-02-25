use crate::core::logic::game::GameState;
use crate::core::logic::card_db::CardDatabase;
use crate::core::hearts::HeartBoard;

/// Analysis tool to calculate mathematical probabilities during the performance phase.
pub struct PerformanceProbabilitySolver;

#[derive(Debug, Clone, serde::Serialize)]
pub struct PerformanceChance {
    pub success_probability: f32,
    pub expected_hearts: [f32; 7],
    pub expected_score: f32,
    pub expected_extra_score: f32,
    pub k_yells: u32,
}

/// Modifiers from abilities that haven't triggered yet but are expected.
#[derive(Debug, Default, Clone, serde::Serialize)]
pub struct AbilityAdjustments {
    pub extra_hearts: [u8; 7],
    pub extra_volume: u16,
    pub virtual_draws: u8,
    pub boost_score: u8, // For O_BOOST_SCORE
}

impl PerformanceProbabilitySolver {
    /// Calculates the probability of clearing a specific live card given the current game state.
    pub fn calculate_win_chance(
        state: &GameState,
        db: &CardDatabase,
        _player_id: usize,
        live_card_id: i32,
    ) -> PerformanceChance {
        let live_card = match db.get_live(live_card_id) {
            Some(l) => l,
            None => return PerformanceChance::zero(),
        };
        Self::calculate_performance_chance(state, db, live_card, &AbilityAdjustments::default())
    }

    pub fn calculate_performance_chance(
        state: &GameState,
        db: &CardDatabase,
        live_card: &crate::core::logic::card_db::LiveCard,
        adj: &AbilityAdjustments,
    ) -> PerformanceChance {
        let player_id = state.current_player as usize; // Assuming current_player is the one performing
        let player = &state.core.players[player_id];

        // 1. Calculate Required Hearts
        let mut req_board = live_card.hearts_board;

        let reductions = player.heart_req_reductions;
        let additions = player.heart_req_additions;
        for i in 0..7 {
            let red = reductions.get_color_count(i) as i32;
            let add = additions.get_color_count(i) as i32;
            let val = (req_board.get_color_count(i) as i32 - red + add).max(0) as u8;
            req_board.set_color_count(i, val);
        }

        // 2. Calculate Hearts & Volume Already on Stage
        let mut stage_hearts = [0u8; 7];
        let mut stage_volume = 0u32; 
        
        for i in 0..3 {
            let eff_h = state.get_effective_hearts(player_id, i, db, 0);
            let arr = eff_h.to_array();
            for j in 0..7 {
                stage_hearts[j] = stage_hearts[j].saturating_add(arr[j]);
            }
            
            let cid = player.stage[i];
            if cid >= 0 {
                if let Some(m) = db.get_member(cid) {
                    stage_volume += m.volume_icons;
                }
            }
        }

        // Apply Ability Adjustments: Hearts & Volume
        for i in 0..7 {
            stage_hearts[i] = stage_hearts[i].saturating_add(adj.extra_hearts[i]);
        }
        stage_volume += adj.extra_volume as u32;
        
        // 3. Current Live Score Potential
        let mut expected_score = live_card.score as f32 + player.live_score_bonus as f32 + stage_volume as f32 + adj.boost_score as f32;

        // 4. Analyze Deck Population
        let k_yells = {
            let mut blades = player.cheer_mod_count as u32;
            for i in 0..3 {
                blades += state.get_effective_blades(player_id, i, db, 0);
            }
            let reduction = player.yell_count_reduction.max(0) as u32;
            let base = blades.saturating_sub(reduction);
            // Apply Ability Adjustments: Yells (virtual draws)
            base.saturating_add(adj.virtual_draws as u32)
        };

        let pool_board = HeartBoard::from_array(&stage_hearts);
        if pool_board.satisfies(req_board) {
            // Already satisfied, just need to factor in expected volume from yells if any
            if k_yells > 0 {
                let n_deck = player.deck.len() as f32;
                if n_deck > 0.0 {
                    let mut deck_sum_volume = 0u32;
                    for &cid in player.deck.iter() {
                        if let Some(m) = db.get_member(cid) { deck_sum_volume += m.volume_icons; }
                        else if let Some(l) = db.get_live(cid) { deck_sum_volume += l.volume_icons; }
                    }
                    expected_score += (k_yells as f32) * (deck_sum_volume as f32 / n_deck);
                }
            }
            return PerformanceChance::guaranteed(k_yells, expected_score);
        }

        if k_yells == 0 {
            return PerformanceChance::failing(0, expected_score);
        }

        let mut pool = player.deck.to_vec();
        if k_yells > pool.len() as u32 {
            pool.extend_from_slice(&player.discard);
        }

        let n_pool = pool.len() as f32;
        // Cap the number of yells by the total number of cards available (Deck + Discard)
        let k_draw = (k_yells as f32).min(n_pool);
        let mut expected_hearts = [0.0f32; 7];
        
        let mut pool_sum_hearts = [0u32; 7];
        let mut pool_sum_volume = 0u32;

        for &cid in pool.iter() {
            if let Some(m) = db.get_member(cid) {
                for i in 0..7 { pool_sum_hearts[i] += m.blade_hearts[i] as u32; }
                pool_sum_volume += m.volume_icons;
            } else if let Some(l) = db.get_live(cid) {
                for i in 0..7 { pool_sum_hearts[i] += l.blade_hearts[i] as u32; }
                pool_sum_volume += l.volume_icons;
            }
        }

        if n_pool > 0.0 {
            for i in 0..7 {
                expected_hearts[i] = k_draw * (pool_sum_hearts[i] as f32 / n_pool);
            }
            expected_score += k_draw * (pool_sum_volume as f32 / n_pool);
        }

        // 5. Calculate Deficits
        let req_arr = req_board.to_array();
        let mut heart_deficit = [0i32; 7];
        for i in 0..7 {
            heart_deficit[i] = (req_arr[i] as i32 - stage_hearts[i] as i32).max(0);
        }

        // 6. Strict Bounds Check
        let mut max_h_in_pool = 1u8;
        for i in 0..7 {
            let color_max = pool.iter().map(|&cid| {
                db.get_member(cid).map(|m| m.blade_hearts[i]).unwrap_or(0)
            }).max().unwrap_or(0);
            if color_max > max_h_in_pool { max_h_in_pool = color_max; }
        }

        let mut total_heart_deficit = 0.0f32;
        for i in 0..6 { total_heart_deficit += heart_deficit[i] as f32; }
        total_heart_deficit = (total_heart_deficit - expected_hearts[6]).max(0.0);
        
        if k_draw * (max_h_in_pool as f32) < total_heart_deficit {
            return PerformanceChance::failing(k_yells, expected_score);
        }

        // 7. Improved Success Probability Model
        // We evaluate how well expected hearts (Normal + Special) cover the deficit.
        let mut color_needed_total = 0.0f32;
        for i in 0..6 { color_needed_total += heart_deficit[i] as f32; }

        let special_buffer = expected_hearts[6];
        let mut total_coverage = 0.0f32;
        
        for i in 0..6 {
            let d = heart_deficit[i] as f32;
            if d > 0.0 {
                let exp = expected_hearts[i];
                // Local color coverage
                total_coverage += exp.min(d);
            }
        }
        
        // Total potential hearts compared to needed
        let total_potential = total_coverage + special_buffer;
        
        let mut win_prob: f32;
        if total_potential < color_needed_total {
            // Even with all specials, we are short on average
            win_prob = (total_potential / color_needed_total).powi(2) * 0.2;
        } else {
            // We have enough on average. Prob is high but not 100% due to variance.
            let margin = total_potential - color_needed_total;
            win_prob = 0.7 + (margin / (color_needed_total + 1.0)).min(0.29);
        }

        // Cap based on individual mandatory colors if we don't have enough yells
        for i in 0..6 {
            if heart_deficit[i] > 0 && expected_hearts[i] == 0.0 && special_buffer == 0.0 {
                win_prob = 0.0;
            }
        }
        // Note: Success probability DOES NOT depend on Volume.
        // Volume just increases expected_score.

        PerformanceChance {
            success_probability: win_prob.clamp(0.0, 1.0),
            expected_hearts,
            expected_score,
            expected_extra_score: 0.0, // stars / bonus logic if needed
            k_yells,
        }
    }

    pub fn analyze_current_permissible_lives(state: &GameState, db: &CardDatabase, player_id: usize) -> Vec<(i32, PerformanceChance)> {
        let player = &state.core.players[player_id];
        let mut results = Vec::new();
        for &cid in player.live_zone.iter() {
            if cid >= 0 {
                let live_card = match db.get_live(cid) {
                    Some(l) => l,
                    None => continue,
                };
                results.push((cid, Self::calculate_performance_chance(state, db, live_card, &AbilityAdjustments::default())));
            }
        }
        results
    }

    /// Predicts the adjustments that would result from playing a specific member card.
    pub fn predict_adjustments(
        state: &GameState,
        db: &CardDatabase,
        card: &crate::core::logic::card_db::MemberCard,
        slot_idx: usize,
    ) -> AbilityAdjustments {
        let mut adj = AbilityAdjustments::default();
        // Base volume from icons
        adj.extra_volume = card.volume_icons as u16;
        
        // Permanent Hearts from icons
        for i in 0..7 {
            let count = card.hearts[i];
            if count > 0 {
                adj.extra_hearts[i] = adj.extra_hearts[i].saturating_add(count);
            }
        }
        
        for ab in &card.abilities {
            if ab.trigger != crate::core::enums::TriggerType::OnPlay {
                continue;
            }

            // Check conditions!
            let ctx = crate::core::logic::AbilityContext {
                source_card_id: card.card_id,
                player_id: state.current_player,
                area_idx: slot_idx as i16,
                ..Default::default()
            };

            let mut all_met = true;
            for cond in &ab.conditions {
                if !state.check_condition(db, state.current_player as usize, cond, &ctx, 0) {
                    all_met = false;
                    break;
                }
            }
            if !all_met {
                continue;
            }

            let bc = &ab.bytecode;
            let mut i = 0;
            use crate::core::generated_constants::*;

            while i + 4 < bc.len() {
                let op = bc[i];
                let v = bc[i + 1];
                let a_low = bc[i + 2];
                let a_high = bc[i + 3];
                let a = ((a_high as i64) << 32) | (a_low as i64);
                // let s = bc[i + 4];

                if op == O_ADD_HEARTS {
                    let mut color = a as usize;
                    if color == 0 {
                        // Fallback or color selection prediction? For now, assume special if not specified.
                        // A more sophisticated solver might try all colors or use context.
                        color = 6; 
                    }
                    if color < 7 {
                        adj.extra_hearts[color] = adj.extra_hearts[color].saturating_add(v as u8);
                    }
                } else if op == O_ADD_BLADES {
                    // Each blade acts like an extra yell, which translates to virtual draws.
                    // This is a simplification; actual blades modify cheer_mod_count.
                    adj.virtual_draws = adj.virtual_draws.saturating_add(v as u8);
                } else if op == O_DRAW {
                    adj.virtual_draws = adj.virtual_draws.saturating_add(v as u8);
                } else if op == O_BOOST_SCORE {
                    adj.boost_score = adj.boost_score.saturating_add(v as u8);
                } else if op == O_REDUCE_HEART_REQ {
                    // Treat heart requirement reduction as adding special hearts for calculation purposes
                    adj.extra_hearts[6] = adj.extra_hearts[6].saturating_add(v as u8);
                }
                i += 5;
            }
        }
        adj
    }

    /// Evaluates which cards in hand provide the best boost to live success probability.
    pub fn evaluate_hand_contributions(
        state: &GameState,
        db: &CardDatabase,
        hand_cards: &[i32],
        live_card: &crate::core::logic::card_db::LiveCard,
    ) -> Vec<(i32, PerformanceChance)> {
        let mut results = Vec::new();
        
        for &cid in hand_cards {
            if cid < 0 { continue; }
            let card = match db.get_member(cid) {
                Some(m) => m,
                None => continue,
            };
            
            // Can we afford it?
            let player_id = state.current_player as usize;
            let available_energy = state.core.players[player_id].energy_zone.len() as u32 - state.core.players[player_id].tapped_energy_count();
            
            let mut best_chance = PerformanceChance {
                success_probability: 0.0,
                expected_hearts: [0.0; 7],
                expected_score: live_card.score as f32,
                expected_extra_score: 0.0,
                k_yells: 0,
            };

            // Try playing to each slot to find the best impact (important for IS_CENTER)
            for slot in 0..3 {
                // Simple heuristic: what is the cost to play here?
                let cost = state.get_member_cost(player_id, cid, slot as i16, -1, db, 0);
                if available_energy < cost as u32 {
                    continue;
                }
                
                let adj = Self::predict_adjustments(state, db, card, slot);
                let chance = Self::calculate_performance_chance(state, db, live_card, &adj);
                
                if chance.success_probability > best_chance.success_probability || 
                   (chance.success_probability == best_chance.success_probability && chance.expected_score > best_chance.expected_score) {
                    best_chance = chance;
                }
            }
            results.push((cid, best_chance));
        }
        
        // Sort by success probability descending
        results.sort_by(|a, b| b.1.success_probability.partial_cmp(&a.1.success_probability).unwrap_or(std::cmp::Ordering::Equal));
        results
    }
}

impl PerformanceChance {
    pub fn zero() -> Self {
        Self { 
            success_probability: 0.0, 
            expected_hearts: [0.0; 7],
            expected_score: 0.0,
            expected_extra_score: 0.0,
            k_yells: 0,
        }
    }
    pub fn guaranteed(k: u32, score: f32) -> Self {
        Self { 
            success_probability: 1.0, 
            expected_hearts: [0.0; 7],
            expected_score: score,
            expected_extra_score: 0.0,
            k_yells: k,
        }
    }
    pub fn failing(k: u32, score: f32) -> Self {
        Self { 
            success_probability: 0.0, 
            expected_hearts: [0.0; 7], 
            expected_score: score,
            expected_extra_score: 0.0,
            k_yells: k,
        }
    }
}
