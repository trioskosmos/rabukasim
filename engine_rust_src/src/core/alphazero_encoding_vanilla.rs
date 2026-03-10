use crate::core::logic::{CardDatabase, GameState};

pub const AZ_VANILLA_CARD_FEATURES: usize = 13;
pub const AZ_VANILLA_TOTAL_CARDS: usize = 60;
// Global(20) + 60 * 13 = 20 + 780 = 800
pub const AZ_VANILLA_TOTAL_INPUT: usize = 800;

pub trait AlphaZeroVanillaEncoding {
    fn to_vanilla_tensor(&self, db: &CardDatabase) -> Vec<f32>;
}

impl AlphaZeroVanillaEncoding for GameState {
    fn to_vanilla_tensor(&self, db: &CardDatabase) -> Vec<f32> {
        let mut tensor = Vec::with_capacity(AZ_VANILLA_TOTAL_INPUT);

        // 1. Perspective
        let me = self.current_player as usize;
        let opp = 1 - me;

        // 2. Global State (20 floats)
        tensor.push(self.phase as i32 as f32);
        tensor.push(self.turn as f32 / 20.0);
        tensor.push(me as f32);
        tensor.push(self.core.players[me].score as f32 / 10.0);
        tensor.push(self.core.players[opp].score as f32 / 10.0);
        tensor.push(self.core.players[me].hand.len() as f32 / 10.0);
        tensor.push(self.core.players[me].energy_zone.len() as f32 / 10.0);
        tensor.push(self.core.players[me].yell_cards.len() as f32 / 10.0);
        tensor.push(self.core.players[opp].yell_cards.len() as f32 / 10.0);
        tensor.push(if self.core.performance_yell_done[me] { 1.0 } else { 0.0 });

        // 2.1 Portfolio Synergies
        let (portfolio_stats, participation_hints) = self.analyze_portfolio_synergies(me, db);
        for &val in &portfolio_stats { tensor.push(val); }

        while tensor.len() < 20 { tensor.push(0.0); }

        // 3. High-Fidelity Card State (60 cards)
        let p = &self.core.players[me];
        for i in 0..AZ_VANILLA_TOTAL_CARDS {
            let cid = if i < p.initial_deck.len() { p.initial_deck[i] } else { -1 };
            if cid < 0 {
                for _ in 0..AZ_VANILLA_CARD_FEATURES { tensor.push(0.0); }
                continue;
            }

            // 1. Zone
            let zone = get_card_zone(self, me, cid);
            tensor.push(zone as f32 / 10.0);

            if let Some(m) = db.get_member(cid) {
                // 2. Type
                tensor.push(1.0);
                // 3. Cost
                tensor.push(m.cost as f32 / 10.0);
                // 4-9. Normal Hearts (P,R,Y,G,B,P)
                for h in 0..6 { tensor.push(m.hearts[h] as f32); }
                // 10. Star Heart
                tensor.push(m.hearts[6] as f32);
                // 11. Individual Prob (Simple proxy for members: total hearts as potential)
                tensor.push(m.hearts.iter().sum::<u8>() as f32 / 5.0);
                // 12. Participation Hint
                tensor.push(if participation_hints.contains(&cid) { 1.0 } else { 0.0 });
                // 13. Note Icons
                tensor.push(m.note_icons as f32 / 10.0);
            } else if let Some(l) = db.get_live(cid) {
                tensor.push(2.0); // Type
                tensor.push(l.score as f32 / 10.0); // Value
                for h in 0..6 { tensor.push(l.required_hearts[h] as f32 / 10.0); }
                tensor.push(l.required_hearts[6] as f32 / 10.0); // Star
                // 11. Individual Success Prob
                let stage_hearts = self.get_total_stage_hearts(me, db);
                let yell_stats = crate::core::heuristics::calculate_deck_expectations(&p.deck, db);
                let blades = (0..3).map(|i| self.get_effective_blades(me, i, db, 0)).sum::<u32>();
                let exp_yell_hearts: Vec<f32> = yell_stats.avg_hearts.iter().map(|&h| h * blades as f32).collect();
                let prob = crate::core::heuristics::calculate_live_success_prob(
                    l, &stage_hearts, &exp_yell_hearts, p.heart_req_reductions.to_array()
                );
                tensor.push(prob.min(1.0));
                // 12. Participation Hint
                tensor.push(if participation_hints.contains(&cid) { 1.0 } else { 0.0 });
                // 13. Stats
                tensor.push(l.note_icons as f32 / 10.0);
            } else {
                for _ in 0..AZ_VANILLA_CARD_FEATURES-1 { tensor.push(0.0); }
            }
        }

        while tensor.len() < AZ_VANILLA_TOTAL_INPUT {
            tensor.push(0.0);
        }

        tensor
    }
}

impl GameState {
    fn analyze_portfolio_synergies(&self, p_idx: usize, db: &CardDatabase) -> (Vec<f32>, Vec<i32>) {
        let p = &self.core.players[p_idx];
        let mut stats = vec![0.0; 8]; // Best1Raw, Best2Raw, Best3Raw, Best1RA, Best2RA, Best3RA, Exhaust, Spare
        let mut hints = Vec::new();

        // 1. Collect all 12 Live Cards from the total pool (initial_deck)
        // This gives the AI a 'Strategic Ceiling' to aim for.
        let mut candidates = Vec::new();
        for &cid in &p.initial_deck {
            if cid >= 0 && db.get_live(cid).is_some() && !candidates.contains(&cid) {
                candidates.push(cid);
            }
        }
        if candidates.is_empty() { return (stats, hints); }

        // 2. Setup Resources
        let stage_hearts = self.get_total_stage_hearts(p_idx, db);
        let yell_stats = crate::core::heuristics::calculate_deck_expectations(&p.deck, db);
        let blades = (0..3).map(|i| self.get_effective_blades(p_idx, i, db, 0)).sum::<u32>();
        let exp_yell_hearts: Vec<f32> = yell_stats.avg_hearts.iter().map(|&h| h * blades as f32).collect();

        // 3. Absolute Best Subsets (1, 2, and 3)
        let mut best_global_ra_ev = 0.0;
        let mut best_indices = Vec::new();

        let search_limit = candidates.len().min(12);

        // a) Evaluate Singles
        for i in 0..search_limit {
            let l1 = db.get_live(candidates[i]).unwrap();
            let p1 = crate::core::heuristics::calculate_live_success_prob(l1, &stage_hearts, &exp_yell_hearts, p.heart_req_reductions.to_array());
            let ev_raw = l1.score as f32 * p1;
            let ev_ra = l1.score as f32 * p1.powf(1.5);

            stats[0] = stats[0].max(ev_raw);
            stats[3] = stats[3].max(ev_ra);
            if ev_ra > best_global_ra_ev {
                best_global_ra_ev = ev_ra;
                best_indices = vec![candidates[i]];
            }
        }

        // b) Evaluate Pairs
        if search_limit >= 2 {
            for i in 0..search_limit {
                for j in (i+1)..search_limit {
                    let l1 = db.get_live(candidates[i]).unwrap();
                    let l2 = db.get_live(candidates[j]).unwrap();
                    let mut combined = l1.clone();
                    for c in 0..7 { combined.required_hearts[c] += l2.required_hearts[c]; }
                    let p2 = crate::core::heuristics::calculate_live_success_prob(&combined, &stage_hearts, &exp_yell_hearts, p.heart_req_reductions.to_array());
                    let ev_raw = (l1.score + l2.score) as f32 * p2;
                    let ev_ra = (l1.score + l2.score) as f32 * p2.powf(1.5);

                    stats[1] = stats[1].max(ev_raw);
                    stats[4] = stats[4].max(ev_ra);
                    if ev_ra > best_global_ra_ev {
                        best_global_ra_ev = ev_ra;
                        best_indices = vec![candidates[i], candidates[j]];
                    }
                }
            }
        }

        // c) Evaluate Trios
        if search_limit >= 3 {
            for i in 0..search_limit {
                for j in (i+1)..search_limit {
                    for k in (j+1)..search_limit {
                        let l1 = db.get_live(candidates[i]).unwrap();
                        let l2 = db.get_live(candidates[j]).unwrap();
                        let l3 = db.get_live(candidates[k]).unwrap();
                        let mut combined = l1.clone();
                        for c in 0..7 { combined.required_hearts[c] += l2.required_hearts[c] + l3.required_hearts[c]; }
                        let p3 = crate::core::heuristics::calculate_live_success_prob(&combined, &stage_hearts, &exp_yell_hearts, p.heart_req_reductions.to_array());
                        let ev_raw = (l1.score + l2.score + l3.score) as f32 * p3;
                        let ev_ra = (l1.score + l2.score + l3.score) as f32 * p3.powf(1.5);

                        stats[2] = stats[2].max(ev_raw);
                        stats[5] = stats[5].max(ev_ra);
                        if ev_ra > best_global_ra_ev {
                            best_global_ra_ev = ev_ra;
                            best_indices = vec![candidates[i], candidates[j], candidates[k]];
                        }
                    }
                }
            }
        }

        // 4. Exhaustion Statistics
        let total_avail: u32 = stage_hearts.iter().sum::<u32>() + exp_yell_hearts.iter().sum::<f32>() as u32;
        if total_avail > 0 {
            let mut best_3_req = 0;
            if best_indices.len() == 3 {
                for &cid in &best_indices {
                    if let Some(l) = db.get_live(cid) {
                        best_3_req += l.required_hearts.iter().sum::<u8>() as u32;
                    }
                }
            }
            stats[6] = (best_3_req as f32 / total_avail as f32).min(2.0);
            stats[7] = (total_avail as f32 - best_3_req as f32) / 10.0;
        }
        hints = best_indices;

        (stats, hints)
    }

    fn get_total_stage_hearts(&self, p_idx: usize, db: &CardDatabase) -> [u32; 7] {
        let mut hearts = [0u32; 7];
        for i in 0..3 {
            let h = self.get_effective_hearts(p_idx, i, db, 0);
            let h_arr = h.to_array();
            for c in 0..7 { hearts[c] += h_arr[c] as u32; }
        }
        hearts
    }
}

fn get_card_zone(state: &GameState, p_idx: usize, cid: i32) -> u8 {
    let p = &state.core.players[p_idx];
    if p.hand.contains(&cid) { return 1; }
    if p.stage.contains(&cid) { return 2; }
    if p.energy_zone.contains(&cid) { return 3; }
    if p.discard.contains(&cid) { return 4; }
    if p.success_lives.contains(&cid) { return 5; }
    if p.yell_cards.contains(&cid) { return 6; }
    if p.live_zone.contains(&cid) { return 7; }
    0 // Deck
}
