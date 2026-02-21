use crate::core::logic::{GameState, PlayerState, CardDatabase};
use crate::core::gpu_state::{GpuGameState, GpuPlayerState, GpuCardStats, MAX_HAND, MAX_DECK, MAX_DISCARD};

impl GameState {
    pub fn to_gpu(&self, db: &CardDatabase) -> GpuGameState {
        GpuGameState {
            player0: self.core.players[0].to_gpu(db, self.live_set_pending_draws[0] as u32),
            player1: self.core.players[1].to_gpu(db, self.live_set_pending_draws[1] as u32),
            current_player: self.current_player as u32,
            phase: self.phase as i32,
            turn: self.turn as u32,
            active_count: 0,
            winner: 0,
            prev_card_id: self.prev_card_id as i32,
            forced_action: -1,
            is_debug: 0,
            rng_state_lo: 0,
            rng_state_hi: 0,
            first_player: self.first_player as u32,
            _pad_game: [0; 5],
        }
    }
}

impl PlayerState {
    pub fn to_gpu(&self, db: &CardDatabase, pending_draws: u32) -> GpuPlayerState {
        let stats = crate::core::heuristics::calculate_deck_expectations(&self.deck, db);
        let mut avg_hearts = [0u32; 8];
        for i in 0..7 {
            avg_hearts[i] = (stats.avg_hearts[i] * 100.0) as u32;
        }

        let mut ps = GpuPlayerState {
            hand: [0; 32],
            hand_len: self.hand.len().min(MAX_HAND) as u32,
            deck: [0; 32],
            deck_len: self.deck.len().min(MAX_DECK) as u32,
            discard_pile: [0; 32],
            discard_pile_len: self.discard.len().min(MAX_DISCARD) as u32,
            stage: [0; 2],
            live_zone: [0; 2],
            score: self.score as u32,
            flags: self.flags as u32,
            hand_added_mask: 0,
            heart_buffs: [
                self.heart_buffs[0].0 as u32, (self.heart_buffs[0].0 >> 32) as u32,
                self.heart_buffs[1].0 as u32, (self.heart_buffs[1].0 >> 32) as u32,
                self.heart_buffs[2].0 as u32, (self.heart_buffs[2].0 >> 32) as u32,
                0, 0,
            ],
            heart_req_reductions: [
                self.heart_req_reductions.0 as u32, (self.heart_req_reductions.0 >> 32) as u32
            ],
            current_turn_volume: self.current_turn_volume as u32,
            baton_touch_count: self.baton_touch_count as u32,
            energy_count: self.energy_zone.len() as u32,
            pending_draws,
            tapped_energy_count: self.tapped_energy_mask.count_ones(),
            used_abilities_mask: 0, // Reset for rollout starts
            blade_buffs: [
                self.blade_buffs[0] as u32,
                self.blade_buffs[1] as u32,
                self.blade_buffs[2] as u32,
                0,
            ],
            board_blades: 0,        // Handled by main loop
            lives_cleared_count: self.success_lives.len() as u32,
            avg_hearts,
            mcts_reward: 0.0,
            baton_touch_limit: self.baton_touch_limit as u32,
            moved_flags: {
                let mut flags = 0u32;
                for i in 0..3 {
                    if self.is_moved(i) { flags |= 1 << i; }
                }
                flags
            },
            energy_deck_len: self.energy_deck.len() as u32,
            heart_req_additions: [
                self.heart_req_additions.0 as u32, (self.heart_req_additions.0 >> 32) as u32
            ],
            yell_count_reduction: self.yell_count_reduction as u32,
            prevent_activate: self.prevent_activate as u32,
            prevent_baton_touch: self.prevent_baton_touch as u32,
            prevent_success_pile_set: self.prevent_success_pile_set as u32,
            prevent_play_to_slot_mask: self.prevent_play_to_slot_mask as u32,
            _pad_player: 0,
            success_lives: [0; 4],
        };

        // Pack success lives
        for i in 0..self.success_lives.len().min(8) {
            let word_idx = i / 2;
            let shift = (i % 2) * 16;
            ps.success_lives[word_idx] |= (self.success_lives[i] as u16 as u32) << shift;
        }

        // Pack Hand (2 x u16 per u32)
        for i in 0..self.hand.len().min(MAX_HAND) {
            let word_idx = i / 2;
            let shift = (i % 2) * 16;
            ps.hand[word_idx] |= (self.hand[i] as u16 as u32) << shift;
        }

        // Pack Deck
        for i in 0..self.deck.len().min(MAX_DECK) {
            let word_idx = i / 2;
            let shift = (i % 2) * 16;
            ps.deck[word_idx] |= (self.deck[i] as u16 as u32) << shift;
        }

        // Pack Discard
        for i in 0..self.discard.len().min(MAX_DISCARD) {
            let word_idx = i / 2;
            let shift = (i % 2) * 16;
            ps.discard_pile[word_idx] |= (self.discard[i] as u16 as u32) << shift;
        }

        // Pack Stage
        for i in 0..3 {
            if self.stage[i] >= 0 {
                let word_idx = i / 2;
                let shift = (i % 2) * 16;
                ps.stage[word_idx] |= (self.stage[i] as u16 as u32) << shift;
            }
        }

        // Pack Live Zone
        for i in 0..3 {
            if self.live_zone[i] >= 0 {
                let word_idx = i / 2;
                let shift = (i % 2) * 16;
                ps.live_zone[word_idx] |= (self.live_zone[i] as u16 as u32) << shift;
            }
        }

        ps
    }
}

pub trait GpuConverter {
    fn convert_to_gpu(&self) -> (Vec<GpuCardStats>, Vec<i32>);
}

impl GpuConverter for CardDatabase {
    fn convert_to_gpu(&self) -> (Vec<GpuCardStats>, Vec<i32>) {
        let mut stats_vec = Vec::new();
        let mut bytecode_full = Vec::new();

        let max_member_id = self.members.keys().max().copied().unwrap_or(0) as usize;
        let max_live_id = self.lives.keys().max().copied().unwrap_or(0) as usize;
        let max_id = max_member_id.max(max_live_id);

        stats_vec.resize(max_id + 1, GpuCardStats::default());

        for (id, m) in self.members.iter() {
            let ab_flags_lo = (m.ability_flags & 0xFFFFFFFF) as u32;
            let ab_flags_hi = (m.ability_flags >> 32) as u32;
            let mut gs = GpuCardStats {
                cost: m.cost as u32,
                blades: m.blades as u32,
                card_type: 1, // Member
                ability_flags_lo: ab_flags_lo,
                ability_flags_hi: ab_flags_hi,
                bytecode_start: bytecode_full.len() as u32,
                bytecode_len: 0,
                volume_icons: m.volume_icons,
                extra_val: 0,
                hearts_lo: 0, hearts_hi: 0,
                blade_hearts_lo: 0, blade_hearts_hi: 0,
                groups: m.groups.get(0).cloned().unwrap_or(0) as u32,
                units: 0, char_id: m.char_id as u32,
                synergy_flags: 0,
                rarity: m.rarity as u32,
                _pad_card: [0; 2],
            };

            // Pack hearts into u32 bits
            for i in 0..4 { gs.hearts_lo |= (m.hearts[i] as u32) << (i * 8); }
            for i in 4..7 { gs.hearts_hi |= (m.hearts[i] as u32) << ((i-4) * 8); }

            for i in 0..4 { gs.blade_hearts_lo |= (m.blade_hearts[i] as u32) << (i * 8); }
            for i in 4..7 { gs.blade_hearts_hi |= (m.blade_hearts[i] as u32) << ((i-4) * 8); }

            for i in 0..m.groups.len().min(4) { gs.groups |= (m.groups[i] as u32) << (i * 8); }
            for i in 0..m.units.len().min(4) { gs.units |= (m.units[i] as u32) << (i * 8); }

            let mut card_bytecode = Vec::new();
            card_bytecode.push(m.abilities.len() as i32); // Header: Number of abilities

            for (ab_idx, ab) in m.abilities.iter().enumerate() {
                card_bytecode.push(ab.trigger as i32);
                card_bytecode.push(if ab.is_once_per_turn { 1 } else { 0 });
                card_bytecode.push(ab_idx as i32); // Store index for mask tracking
                card_bytecode.push(ab.bytecode.len() as i32);
                for &code in &ab.bytecode {
                    card_bytecode.push(code as i32);
                }
                while card_bytecode.len() % 4 != 0 {
                    card_bytecode.push(0); // Pad to 4-word instruction boundary
                }
            }
            gs.bytecode_len = card_bytecode.len() as u32;
            bytecode_full.extend(card_bytecode);

            stats_vec[*id as usize] = gs;
        }

        for (id, l) in self.lives.iter() {
            let mut gs = GpuCardStats {
                cost: 0,
                blades: 0,
                card_type: 2, // Live
                ability_flags_lo: 0, ability_flags_hi: 0,
                bytecode_start: bytecode_full.len() as u32,
                bytecode_len: 0,
                volume_icons: l.volume_icons,
                extra_val: l.score,
                hearts_lo: 0, hearts_hi: 0,
                blade_hearts_lo: 0, blade_hearts_hi: 0,
                groups: 0, units: 0, char_id: 0,
                synergy_flags: 0,
                rarity: 0,
                _pad_card: [0; 2],
            };

            for i in 0..4 { gs.hearts_lo |= (l.required_hearts[i] as u32) << (i * 8); }
            for i in 4..7 { gs.hearts_hi |= (l.required_hearts[i] as u32) << ((i-4) * 8); }

            for i in 0..4 { gs.blade_hearts_lo |= (l.blade_hearts[i] as u32) << (i * 8); }
            for i in 4..7 { gs.blade_hearts_hi |= (l.blade_hearts[i] as u32) << ((i-4) * 8); }

            for i in 0..l.groups.len().min(4) { gs.groups |= (l.groups[i] as u32) << (i * 8); }
            for i in 0..l.units.len().min(4) { gs.units |= (l.units[i] as u32) << (i * 8); }

            let mut card_bytecode = Vec::new();
            for ab in &l.abilities {
                card_bytecode.extend_from_slice(&ab.bytecode);
                while card_bytecode.len() % 4 != 0 {
                    card_bytecode.push(0);
                }
            }
            gs.bytecode_len = card_bytecode.len() as u32;
            bytecode_full.extend(card_bytecode);

            stats_vec[*id as usize] = gs;
        }

        if bytecode_full.is_empty() {
            bytecode_full.push(0);
        }
        (stats_vec, bytecode_full)
    }
}
