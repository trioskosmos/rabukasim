use crate::core::logic::{GameState, PlayerState, CardDatabase};

pub const AZ_BYTECODE_MAX_LEN: usize = 128;
// Base(16) + Identity(16) + Stats(10) + Bytecode(128) = 170
pub const AZ_ENTITY_VECTOR_SIZE: usize = 16 + 16 + 10 + AZ_BYTECODE_MAX_LEN; 
pub const AZ_MAX_ENTITIES_PER_PLAYER: usize = 60;

pub trait AlphaZeroEncoding {
    fn to_alphazero_tensor(&self, db: &CardDatabase) -> Vec<f32>;
}

impl AlphaZeroEncoding for GameState {
    fn to_alphazero_tensor(&self, db: &CardDatabase) -> Vec<f32> {
        let mut tensor = Vec::with_capacity(AZ_ENTITY_VECTOR_SIZE * 120 + 100);

        // 1. Perspective: Always encode from current_player's POV
        let me = self.current_player as usize;
        let opp = 1 - me;

        // 2. Global State (25 floats)
        tensor.push(self.phase as i32 as f32);
        tensor.push(self.turn as f32 / 20.0);
        tensor.push(me as f32);
        tensor.push(self.first_player as f32);
        
        tensor.push(self.core.players[me].score as f32 / 10.0);
        tensor.push(self.core.players[opp].score as f32 / 10.0);
        tensor.push(self.core.players[me].success_lives.len() as f32 / 9.0);
        tensor.push(self.core.players[opp].success_lives.len() as f32 / 9.0);
        
        tensor.push(self.core.players[me].energy_zone.len() as f32 / 10.0);
        tensor.push(self.core.players[opp].energy_zone.len() as f32 / 10.0);
        tensor.push(self.core.players[me].hand.len() as f32 / 15.0);
        tensor.push(self.core.players[opp].hand.len() as f32 / 15.0);

        tensor.push(self.core.players[me].baton_touch_count as f32);
        tensor.push(self.core.players[me].baton_touch_limit as f32);
        tensor.push(self.core.players[opp].baton_touch_count as f32);
        tensor.push(self.core.players[opp].baton_touch_limit as f32);

        tensor.push(self.core.players[me].hand_increased_this_turn as f32 / 5.0);
        tensor.push(self.core.players[opp].hand_increased_this_turn as f32 / 5.0);

        tensor.push(if self.core.performance_yell_done[me] { 1.0 } else { 0.0 });
        tensor.push(if self.core.performance_yell_done[opp] { 1.0 } else { 0.0 });
        tensor.push(if self.core.live_result_selection_pending { 1.0 } else { 0.0 });

        // Padding to exactly 25
        while tensor.len() < 25 { tensor.push(0.0); }

        // 3. Physical Entity Tracking (120 Entities total, 60 per player)
        // We create a map of logical UID -> (Owner, Zone, Index) for all visible/tracked cards.
        // Slots per player (60 total):
        // 0..2   : Stage (3)
        // 3..12  : Hand (10)
        // 13..22 : Energy (10)
        // 23..25 : Live Zone (3)
        // 26..34 : Success Lives (9)
        // 35..59 : Discard (25)
        let mut entity_map: std::collections::HashMap<u32, (usize, u8, usize)> = std::collections::HashMap::with_capacity(120);

        for p_idx in 0..2 {
            let p = &self.core.players[p_idx];
            let base_uid = if p_idx == 0 { 0 } else { 60 };
            
            // Stage (0..2)
            for (idx, cid) in p.stage.iter().enumerate() {
                if *cid >= 0 { entity_map.insert(base_uid + idx as u32, (p_idx, 2, idx)); }
            }
            // Hand (3..12)
            for (idx, _) in p.hand.iter().enumerate().take(10) {
                entity_map.insert(base_uid + 3 + idx as u32, (p_idx, 1, idx));
            }
            // Energy (13..22)
            for (idx, _) in p.energy_zone.iter().enumerate().take(10) {
                entity_map.insert(base_uid + 13 + idx as u32, (p_idx, 3, idx));
            }
            // Live Zone (23..25)
            for (idx, cid) in p.live_zone.iter().enumerate() {
                if *cid >= 0 { entity_map.insert(base_uid + 23 + idx as u32, (p_idx, 7, idx)); }
            }
            // Success Lives (26..34)
            for (idx, _) in p.success_lives.iter().enumerate().take(9) {
                entity_map.insert(base_uid + 26 + idx as u32, (p_idx, 6, idx));
            }
            // Discard (35..59)
            for (idx, _) in p.discard.iter().enumerate().take(25) {
                entity_map.insert(base_uid + 35 + idx as u32, (p_idx, 4, idx));
            }
        }

        // Now iterate all possible UIDs and append vectors
        // Slots 0-59: Me, 60-119: Opponent (Logical UIDs are stable)
        let player_uid_bases = if me == 0 { [0, 60] } else { [60, 0] };

        for &uid_base in &player_uid_bases {
            for offset in 0..AZ_MAX_ENTITIES_PER_PLAYER {
                let uid = uid_base + offset as u32;
                if let Some(&(owner, zone, z_idx)) = entity_map.get(&uid) {
                    // Find card Template ID by scanning the zone (only done once per state)
                    let p = &self.core.players[owner];
                    let cid = match zone {
                        1 => p.hand[z_idx],
                        2 => p.stage[z_idx],
                        3 => p.energy_zone[z_idx],
                        4 => p.discard[z_idx],
                        5 => p.deck[z_idx],
                        6 => p.success_lives[z_idx],
                        7 => p.live_zone[z_idx],
                        8 => p.energy_deck[z_idx],
                        _ => -1,
                    };

                    append_entity_vector(&mut tensor, cid, owner == me, zone, z_idx, db, &self.core.players[owner]);
                } else {
                    append_empty_entity_vector(&mut tensor);
                }
            }
        }

        tensor
    }
}

fn append_entity_vector(tensor: &mut Vec< f32>, packed_cid: i32, is_me: bool, zone: u8, z_idx: usize, db: &CardDatabase, player: &PlayerState) {
    let start_pos = tensor.len();
    let template_id = packed_cid;

    // 1. Meta Block (16 floats)
    tensor.push(1.0); // Exists
    tensor.push(if is_me { 0.0 } else { 1.0 }); // Owner
    tensor.push(zone as f32); // Zone (1=Hand, 2=Stage, 3=Energy, etc.)
    tensor.push(z_idx as f32); // Index in zone
    
    // Hidden Information Masking
    // We only show card details if:
    // - Card is Mine and NOT in Deck
    // - Card is Opponent's and in Stage, SuccessLives, or Discard (Common knowledge)
    // - Card is Opponent's Hand and we have a specific reveal (not implemented yet, but possible)
    let is_revealed = is_me && (zone != 5 && zone != 8) || (!is_me && (zone == 2 || zone == 4 || zone == 6 || zone == 7));

    // Meta Padding
    for _ in 0..12 { tensor.push(0.0); }

    if !is_revealed {
        // Just fill the rest with zeros if hidden
        while tensor.len() < start_pos + AZ_ENTITY_VECTOR_SIZE {
            tensor.push(0.0);
        }
        return;
    }

    // 2. Identity Block (16 floats)
    if let Some(m) = db.get_member(template_id) {
        tensor.push(1.0); // Type: Member
        tensor.push(m.char_id as f32);
        tensor.push(m.rarity as f32);
        tensor.push(m.groups.get(0).copied().unwrap_or(0) as f32);
        tensor.push(m.groups.get(1).copied().unwrap_or(0) as f32);
        tensor.push(m.units.get(0).copied().unwrap_or(0) as f32);
        tensor.push(m.units.get(1).copied().unwrap_or(0) as f32);
        let mut attr_mask = 0.0f32;
        for i in 0..7 { if m.hearts[i] > 0 { attr_mask += (1 << i) as f32; } }
        tensor.push(attr_mask);
        tensor.push(if m.blade_hearts.iter().any(|&h| h > 0) { 1.0 } else { 0.0 });
        tensor.push(if m.char_id == 27 { 1.0 } else { 0.0 }); // Setsuna
        for _ in 0..6 { tensor.push(0.0); }

        // 3. Stats Block (10 floats)
        tensor.push(m.cost as f32);
        tensor.push(m.blades as f32);
        for h in 0..7 { tensor.push(m.hearts[h] as f32); }
        let tapped = if zone == 2 { player.is_tapped(z_idx) } else { false };
        tensor.push(if tapped { 1.0 } else { 0.0 });

    } else if let Some(l) = db.get_live(template_id) {
        tensor.push(2.0); // Type: Live
        for _ in 0..2 { tensor.push(0.0); }
        tensor.push(l.groups.get(0).copied().unwrap_or(0) as f32);
        tensor.push(l.groups.get(1).copied().unwrap_or(0) as f32);
        tensor.push(l.units.get(0).copied().unwrap_or(0) as f32);
        tensor.push(l.units.get(1).copied().unwrap_or(0) as f32);
        let mut attr_mask = 0.0f32;
        for i in 0..7 { if l.required_hearts[i] > 0 { attr_mask += (1 << i) as f32; } }
        tensor.push(attr_mask);
        tensor.push(if l.blade_hearts.iter().any(|&h| h > 0) { 1.0 } else { 0.0 });
        for _ in 0..7 { tensor.push(0.0); }

        // 3. Stats Block (10 floats)
        tensor.push(l.score as f32);
        tensor.push(l.note_icons as f32);
        for h in 0..7 { tensor.push(l.required_hearts[h] as f32); }
        tensor.push(0.0);

    } else {
        // Energy or Unknown
        tensor.push(3.0); // Type: Energy
        for _ in 0..25 { tensor.push(0.0); }
    }

    // 4. Bytecode Block (128 floats)
    let mut instructions_added = 0;
    let abilities = db.get_member(template_id).map(|m| &m.abilities)
                     .or_else(|| db.get_live(template_id).map(|l| &l.abilities));

    if let Some(abs) = abilities {
        for (ab_idx, ab) in abs.iter().enumerate() {
            if instructions_added + 5 >= AZ_BYTECODE_MAX_LEN { break; }
            tensor.push(ab.trigger as i32 as f32);
            tensor.push(if ab.is_once_per_turn { 1.0 } else { 0.0 });
            tensor.push(ab.bytecode.len() as f32);
            let is_spent = if ab.is_once_per_turn {
                let s_type = if db.get_member(template_id).is_some() { 0 } else { 1 };
                let uid = crate::core::logic::interpreter::get_ability_uid(s_type, template_id as u32, ab_idx as u32);
                if player.used_abilities.contains(&uid) { 1.0 } else { 0.0 }
            } else { 0.0 };
            tensor.push(is_spent);
            instructions_added += 4;
            for &code in &ab.bytecode {
                if instructions_added < AZ_BYTECODE_MAX_LEN - 1 {
                    tensor.push(code as f32);
                    instructions_added += 1;
                }
            }
            if instructions_added < AZ_BYTECODE_MAX_LEN {
                tensor.push(-1.0);
                instructions_added += 1;
            }
        }
    }
    while instructions_added < AZ_BYTECODE_MAX_LEN {
        tensor.push(0.0);
        instructions_added += 1;
    }
}

fn append_empty_entity_vector(tensor: &mut Vec<f32>) {
    for _ in 0..AZ_ENTITY_VECTOR_SIZE {
        tensor.push(0.0);
    }
}
