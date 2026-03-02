use crate::core::logic::{GameState, CardDatabase};
// use crate::core::enums::*;

pub trait GameStateEncoding {
    fn encode_state(&self, db: &CardDatabase) -> Vec<f32>;
    fn encode_member_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase);
    fn encode_live_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase, visible: bool);
    fn encode_card_features(&self, feats: &mut Vec<f32>, cid: i32, db: &CardDatabase);
}

impl GameStateEncoding for GameState {
    fn encode_state(&self, db: &CardDatabase) -> Vec<f32> {
        const TOTAL_SIZE: usize = 1200;
        let mut feats = Vec::with_capacity(TOTAL_SIZE);

        feats.push(self.turn as f32 / 50.0);
        feats.push(self.phase as i32 as f32 / 10.0);
        feats.push(self.current_player as f32);
        feats.push(self.core.players[0].score as f32 / 10.0);
        feats.push(self.core.players[1].score as f32 / 10.0);
        feats.push(self.core.players[0].success_lives.len() as f32 / 3.0);
        feats.push(self.core.players[1].success_lives.len() as f32 / 3.0);
        feats.push(self.core.players[0].hand.len() as f32 / 10.0);
        feats.push(self.core.players[1].hand.len() as f32 / 10.0);
        feats.push(self.core.players[0].energy_zone.len() as f32 / 10.0);
        feats.push(self.core.players[1].energy_zone.len() as f32 / 10.0);
        feats.push(self.core.players[0].deck.len() as f32 / 50.0);
        feats.push(self.core.players[1].deck.len() as f32 / 50.0);
        let p0_tapped = (0..self.core.players[0].energy_zone.len()).filter(|&i| self.core.players[0].is_energy_tapped(i)).count();
        let p1_tapped = (0..self.core.players[1].energy_zone.len()).filter(|&i| self.core.players[1].is_energy_tapped(i)).count();
        feats.push(p0_tapped as f32 / 10.0);
        feats.push(p1_tapped as f32 / 10.0);
        feats.push(self.core.players[0].baton_touch_count as f32 / 3.0);
        feats.push(self.core.players[1].baton_touch_count as f32 / 3.0);
        while feats.len() < 20 { feats.push(0.0); }

        for i in 0..3 { self.encode_member_slot(&mut feats, 0, i, db); }
        for i in 0..3 { self.encode_member_slot(&mut feats, 1, i, db); }
        for i in 0..3 { self.encode_live_slot(&mut feats, 0, i, db, true); }
        for i in 0..3 {
            let revealed = self.core.players[1].is_revealed(i);
            self.encode_live_slot(&mut feats, 1, i, db, revealed);
        }

        const CARD_FEAT_SIZE: usize = 48;
        for slot in 0..10 {
            if slot < self.core.players[0].hand.len() {
                let cid = self.core.players[0].hand[slot];
                self.encode_card_features(&mut feats, cid, db);
            } else {
                for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
            }
        }
        feats.push(self.core.players[1].hand.len() as f32 / 10.0);

        let mut p0_power = 0i32;
        let mut p1_power = 0i32;
        for i in 0..3 {
            p0_power += self.get_effective_blades(0, i, db, 0) as i32;
            p1_power += self.get_effective_blades(1, i, db, 0) as i32;
        }
        feats.push(p0_power as f32 / 30.0);
        feats.push(p1_power as f32 / 30.0);
        feats.push((p0_power - p1_power) as f32 / 30.0);

        let mut p0_stage_hearts = [0u32; 7];
        for i in 0..3 {
            let h = self.get_effective_hearts(0, i, db, 0);
            let h_arr = h.to_array();
            for c in 0..7 { p0_stage_hearts[c] += h_arr[c] as u32; }
        }

        let mut suitability = 0.0f32;
        if self.core.players[0].live_zone[0] >= 0 {
            if let Some(l) = db.get_live(self.core.players[0].live_zone[0]) {
                let mut total_req = 0u32;
                let mut total_sat = 0u32;
                for c in 0..7 {
                    let req = l.required_hearts[c] as u32;
                    let have = p0_stage_hearts[c].min(req);
                    total_req += req;
                    total_sat += have;
                }
                let remaining = total_req.saturating_sub(total_sat);
                let any_color = p0_stage_hearts[6];
                total_sat += remaining.min(any_color);
                if total_req > 0 { suitability = total_sat as f32 / total_req as f32; }
            }
        }
        feats.push(suitability);
        feats.push((3 - self.core.players[0].success_lives.len()) as f32 / 3.0);
        feats.push((3 - self.core.players[1].success_lives.len()) as f32 / 3.0);
        feats.push(self.core.players[0].current_turn_notes as f32 / 20.0);
        feats.push(self.core.players[1].current_turn_notes as f32 / 20.0);

        while feats.len() < TOTAL_SIZE - 10 { feats.push(0.0); }
        while feats.len() < TOTAL_SIZE { feats.push(0.0); }
        if feats.len() > TOTAL_SIZE { feats.truncate(TOTAL_SIZE); }
        feats
    }

    fn encode_member_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase) {
        const CARD_FEAT_SIZE: usize = 48;
        let cid = self.core.players[p_idx].stage[slot];
        if cid >= 0 {
            if let Some(m) = db.get_member(cid) {
                feats.push(1.0); feats.push(1.0); feats.push(0.0); feats.push(0.0);
                feats.push(m.cost as f32 / 10.0);
                feats.push(self.get_effective_blades(p_idx, slot, db, 0) as f32 / 10.0);
                let hearts = self.get_effective_hearts(p_idx, slot, db, 0);
                for h in hearts.to_array() { feats.push(h as f32 / 5.0); }
                for _ in 0..7 { feats.push(0.0); }
                for &bh in &m.blade_hearts { feats.push(bh as f32 / 5.0); }
                feats.push(m.note_icons as f32 / 5.0);
                feats.push(if (m.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
                feats.push(if (m.semantic_flags & 0x04) != 0 { 1.0 } else { 0.0 });
                feats.push(if (m.semantic_flags & 0x02) != 0 { 1.0 } else { 0.0 });
                feats.push(if self.core.players[p_idx].is_tapped(slot) { 1.0 } else { 0.0 });
                while (feats.len() % 48) != 0 { feats.push(0.0); }
                return;
            }
        }
        for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
    }

    fn encode_live_slot(&self, feats: &mut Vec<f32>, p_idx: usize, slot: usize, db: &CardDatabase, visible: bool) {
        const CARD_FEAT_SIZE: usize = 48;
        let cid = self.core.players[p_idx].live_zone[slot];
        if cid >= 0 && visible {
            if let Some(l) = db.get_live(cid) {
                feats.push(1.0); feats.push(0.0); feats.push(1.0); feats.push(0.0);
                feats.push(0.0); feats.push(l.score as f32 / 10.0);
                for _ in 0..7 { feats.push(0.0); }
                for &h in &l.required_hearts { feats.push(h as f32 / 5.0); }
                for &bh in &l.blade_hearts { feats.push(bh as f32 / 5.0); }
                feats.push(l.note_icons as f32 / 5.0);
                feats.push(if (l.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
                feats.push(0.0); feats.push(0.0);
                while (feats.len() % 48) != 0 { feats.push(0.0); }
                return;
            }
        }
        for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
    }

    fn encode_card_features(&self, feats: &mut Vec<f32>, cid: i32, db: &CardDatabase) {
        const CARD_FEAT_SIZE: usize = 48;
        if let Some(m) = db.get_member(cid) {
            feats.push(1.0); feats.push(1.0); feats.push(0.0); feats.push(0.0);
            feats.push(m.cost as f32 / 10.0); feats.push(0.0);
            for &h in &m.hearts { feats.push(h as f32 / 5.0); }
            for _ in 0..7 { feats.push(0.0); }
            for &bh in &m.blade_hearts { feats.push(bh as f32 / 5.0); }
            for _ in 0..7 { feats.push(0.0); } // Padding for blade hearts if 7 colors
            feats.push(m.note_icons as f32 / 5.0);
            feats.push(if (m.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
            feats.push(if (m.semantic_flags & 0x04) != 0 { 1.0 } else { 0.0 });
            feats.push(if (m.semantic_flags & 0x02) != 0 { 1.0 } else { 0.0 });
            feats.push(0.0);
            while (feats.len() % 48) != 0 { feats.push(0.0); }
        } else if let Some(l) = db.get_live(cid) {
            feats.push(1.0); feats.push(0.0); feats.push(1.0); feats.push(0.0);
            feats.push(0.0); feats.push(l.score as f32 / 10.0);
            for _ in 0..7 { feats.push(0.0); }
            for &h in &l.required_hearts { feats.push(h as f32 / 5.0); }
            for &bh in &l.blade_hearts { feats.push(bh as f32 / 5.0); }
            feats.push(l.note_icons as f32 / 5.0);
            feats.push(if (l.semantic_flags & 0x01) != 0 { 1.0 } else { 0.0 });
            feats.push(0.0); feats.push(0.0); feats.push(0.0);
            while (feats.len() % 48) != 0 { feats.push(0.0); }
        } else {
            for _ in 0..CARD_FEAT_SIZE { feats.push(0.0); }
        }
    }
}
