//! # LovecaSim Player State
//!
//! This module defines the `PlayerState` struct, which encapsulates all data 
//! belonging to a single player (Hand, Deck, Stage Slots, Energy, etc.).
//!
//! ## Key Data Structures:
//! - **Stage Slots**: A fixed-size array of member IDs currently on the field.
//! - **Energy Zone**: A `SmallVec` of booleans representing whether an energy card is tapped.
//! - **Blade/Heart Buffs**: Temporary modifiers applied to specific stage slots.
//! - **Restriction Flags**: Flags like `prevent_baton_touch` used by Meta Rules to 
//!   limit player actions.
//!
//! ## Memory Efficiency:
//! `PlayerState` uses `SmallVec` and fixed-size arrays where possible to minimize 
//! heap allocations, which is critical for MCTS performance.

use serde::{Deserialize, Serialize};
use smallvec::SmallVec;
use crate::core::hearts::HeartBoard;
use crate::core::enums::*;
use super::models::*;

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlayerState {
    pub player_id: u8,
    pub hand: SmallVec<[i32; 16]>,
    pub deck: SmallVec<[i32; 60]>,
    pub discard: SmallVec<[i32; 32]>,
    pub exile: SmallVec<[i32; 16]>,
    pub energy_deck: SmallVec<[i32; 16]>,
    pub energy_zone: SmallVec<[i32; 16]>,
    pub success_lives: SmallVec<[i32; 8]>,
    pub live_zone: [i32; 3], // -1 or ID
    pub stage: [i32; 3],
    pub stage_energy_count: [u8; 3],
    pub tapped_energy_mask: u64, // Bitmask for energy_zone status
    pub baton_touch_count: u8,
    pub baton_touch_limit: u8,
    pub score: u32,
    pub current_turn_volume: u32,
    pub used_abilities: SmallVec<[u32; 16]>,
    pub live_score_bonus: i32,
    pub blade_buffs: [i16; 3],
    pub heart_buffs: [HeartBoard; 3],
    pub cost_reduction: i16,
    pub hand_increased_this_turn: u32,
    pub stage_energy: [SmallVec<[i32; 4]>; 3],
    pub color_transforms: SmallVec<[(i32, u8, u8); 4]>, // (source_cid, src_color, dst_color)
    pub heart_req_reductions: HeartBoard,
    pub heart_req_additions: HeartBoard,
    pub heart_req_reduction_logs: SmallVec<[(i32, u8, u8); 4]>, // (source_cid, color, amount)
    pub mulligan_selection: u64,
    pub hand_added_turn: SmallVec<[i32; 16]>,
    pub restrictions: SmallVec<[u8; 8]>,
    pub looked_cards: SmallVec<[i32; 16]>, // Shared buffer for revealing cards to UI
    pub live_deck: SmallVec<[i32; 12]>, // Live cards available for Live Set phase
    pub granted_abilities: Vec<(i32, i32, u16)>, // (target_cid, source_cid, ab_idx)
    pub cost_modifiers: Vec<(Condition, i32)>, // (condition, amount)
    pub played_group_mask: u32,
    // Bitfields
    pub flags: u32, // [cannot_live:1, deck_refreshed:1, immunity:1, tapped_m_0..3:3, moved_m_0..3:3, live_revealed_0..3:3]
    pub cheer_mod_count: u16,
    pub yell_count_reduction: i16,
    pub negated_triggers: Vec<(i32, TriggerType, i32)>, // (target_cid, trigger_type, count)
    pub prevent_activate: u8,
    pub prevent_baton_touch: u8,
    pub prevent_success_pile_set: u8,
    pub prevent_play_to_slot_mask: u8,
    pub yell_cards: SmallVec<[i32; 8]>,
    #[serde(default)]
    pub excess_hearts: u32,
}

impl Default for PlayerState {
    fn default() -> Self {
        PlayerState {
            player_id: 0,
            hand: SmallVec::new(),
            deck: SmallVec::new(),
            discard: SmallVec::new(),
            exile: SmallVec::new(),
            energy_deck: SmallVec::new(),
            energy_zone: SmallVec::new(),
            success_lives: SmallVec::new(),
            live_zone: [-1; 3],
            stage: [-1; 3],
            stage_energy_count: [0; 3],
            tapped_energy_mask: 0,
            baton_touch_count: 0,
            baton_touch_limit: 3,
            score: 0,
            current_turn_volume: 0,
            used_abilities: SmallVec::new(),
            live_score_bonus: 0,
            blade_buffs: [0; 3],
            heart_buffs: [HeartBoard::default(); 3],
            cost_reduction: 0,
            hand_increased_this_turn: 0,
            stage_energy: [SmallVec::new(), SmallVec::new(), SmallVec::new()],
            color_transforms: SmallVec::new(),
            heart_req_reductions: HeartBoard::default(),
            heart_req_additions: HeartBoard::default(),
            heart_req_reduction_logs: SmallVec::new(),
            mulligan_selection: 0,
            hand_added_turn: SmallVec::new(),
            restrictions: SmallVec::new(),
            looked_cards: SmallVec::new(),
            live_deck: SmallVec::new(),
            granted_abilities: Vec::new(),
            cost_modifiers: Vec::new(),
            flags: 0,
            cheer_mod_count: 0,
            yell_count_reduction: 0,
            negated_triggers: Vec::new(),
            prevent_activate: 0,
            prevent_baton_touch: 0,
            prevent_success_pile_set: 0,
            prevent_play_to_slot_mask: 0,
            played_group_mask: 0,
            yell_cards: SmallVec::new(),
            excess_hearts: 0,
        }
    }
}

impl PlayerState {
    pub const FLAG_CANNOT_LIVE: u8 = 0;
    pub const FLAG_DECK_REFRESHED: u8 = 1;
    pub const FLAG_IMMUNITY: u8 = 2;
    pub const OFFSET_TAPPED: u8 = 3;
    pub const OFFSET_MOVED: u8 = 6;
    pub const OFFSET_REVEALED: u8 = 9;

    pub fn get_flag(&self, bit: u8) -> bool { (self.flags >> bit) & 1 == 1 }
    pub fn set_flag(&mut self, bit: u8, val: bool) {
        if val { self.flags |= 1 << bit; }
        else { self.flags &= !(1 << bit); }
    }

    pub fn is_tapped(&self, slot: usize) -> bool { self.get_flag(Self::OFFSET_TAPPED + slot as u8) }
    pub fn set_tapped(&mut self, slot: usize, val: bool) { self.set_flag(Self::OFFSET_TAPPED + slot as u8, val); }

    pub fn is_moved(&self, slot: usize) -> bool { self.get_flag(Self::OFFSET_MOVED + slot as u8) }
    pub fn set_moved(&mut self, slot: usize, val: bool) { self.set_flag(Self::OFFSET_MOVED + slot as u8, val); }

    pub fn is_revealed(&self, slot: usize) -> bool { self.get_flag(Self::OFFSET_REVEALED + slot as u8) }
    pub fn set_revealed(&mut self, slot: usize, val: bool) { self.set_flag(Self::OFFSET_REVEALED + slot as u8, val); }

    pub fn swap_tapped(&mut self, i: usize, j: usize) {
        let ti = self.is_tapped(i);
        let tj = self.is_tapped(j);
        self.set_tapped(i, tj);
        self.set_tapped(j, ti);
    }

    pub fn swap_moved(&mut self, i: usize, j: usize) {
        let mi = self.is_moved(i);
        let mj = self.is_moved(j);
        self.set_moved(i, mj);
        self.set_moved(j, mi);
    }

    /// Synchronizes the stage_energy_count for a slot based on its energy list size.
    pub fn sync_stage_energy_count(&mut self, slot: usize) {
        if slot < 3 {
            self.stage_energy_count[slot] = self.stage_energy[slot].len() as u8;
        }
    }

    /// Swaps all data associated with two stage slots and marks them as moved.
    pub fn swap_slot_data(&mut self, i: usize, j: usize) {
        if i < 3 && j < 3 && i != j {
            self.stage.swap(i, j);
            self.swap_tapped(i, j);
            // self.swap_moved(i, j); // INCORRECT: Moving implies they are now "moved" this turn
            self.set_moved(i, true);
            self.set_moved(j, true);
            
            self.stage_energy_count.swap(i, j);
            self.stage_energy.swap(i, j);
            self.blade_buffs.swap(i, j);
            self.heart_buffs.swap(i, j);
        }
    }

    pub fn untap_all(&mut self) {
        // Clear tapped and moved flags (bits 3-8)
        self.flags &= !0b111111000; 
        self.tapped_energy_mask = 0;
        self.baton_touch_count = 0;
        self.blade_buffs = [0; 3];
        self.heart_buffs = [HeartBoard::default(); 3];
        self.cost_reduction = 0;
        self.live_score_bonus = 0;
        self.used_abilities.clear();
        self.color_transforms.clear();
        self.heart_req_reductions = HeartBoard::default();
        self.heart_req_additions = HeartBoard::default();
        self.heart_req_reduction_logs.clear();
        self.mulligan_selection = 0;
        self.granted_abilities.clear();
        self.cost_modifiers.clear();
        self.cheer_mod_count = 0;
        self.prevent_activate = 0;
        self.prevent_baton_touch = 0;
        self.prevent_success_pile_set = 0;
        self.prevent_play_to_slot_mask = 0;
        self.played_group_mask = 0;
        self.yell_cards.clear();
        self.excess_hearts = 0;
    }

    pub fn copy_from(&mut self, other: &PlayerState) {
        self.player_id = other.player_id;
        self.hand.clear(); self.hand.extend_from_slice(&other.hand);
        self.deck.clear(); self.deck.extend_from_slice(&other.deck);
        self.discard.clear(); self.discard.extend_from_slice(&other.discard);
        self.exile.clear(); self.exile.extend_from_slice(&other.exile);
        self.energy_deck.clear(); self.energy_deck.extend_from_slice(&other.energy_deck);
        self.energy_zone.clear(); self.energy_zone.extend_from_slice(&other.energy_zone);
        self.success_lives.clear(); self.success_lives.extend_from_slice(&other.success_lives);
        self.live_zone = other.live_zone;
        self.stage = other.stage;
        self.stage_energy_count = other.stage_energy_count;
        self.tapped_energy_mask = other.tapped_energy_mask;
        self.baton_touch_count = other.baton_touch_count;
        self.baton_touch_limit = other.baton_touch_limit;
        self.score = other.score;
        self.current_turn_volume = other.current_turn_volume;
        self.used_abilities.clear(); self.used_abilities.extend_from_slice(&other.used_abilities);
        self.live_score_bonus = other.live_score_bonus;
        self.blade_buffs = other.blade_buffs;
        self.heart_buffs = other.heart_buffs;
        self.cost_reduction = other.cost_reduction;
        self.hand_increased_this_turn = other.hand_increased_this_turn;
        for i in 0..3 {
             self.stage_energy[i].clear();
             self.stage_energy[i].extend_from_slice(&other.stage_energy[i]);
        }
        self.color_transforms.clear(); self.color_transforms.extend_from_slice(&other.color_transforms);
        self.heart_req_reductions = other.heart_req_reductions;
        self.heart_req_additions = other.heart_req_additions;
        self.heart_req_reduction_logs.clear(); self.heart_req_reduction_logs.extend_from_slice(&other.heart_req_reduction_logs);
        self.mulligan_selection = other.mulligan_selection;
        self.hand_added_turn.clear(); self.hand_added_turn.extend_from_slice(&other.hand_added_turn);
        self.restrictions.clear(); self.restrictions.extend_from_slice(&other.restrictions);
        self.looked_cards.clear(); self.looked_cards.extend_from_slice(&other.looked_cards);
        self.live_deck.clear(); self.live_deck.extend_from_slice(&other.live_deck);
        self.granted_abilities.clear(); self.granted_abilities.extend_from_slice(&other.granted_abilities);
        self.cost_modifiers.clear(); self.cost_modifiers.extend(other.cost_modifiers.iter().cloned());
        self.flags = other.flags;
        self.cheer_mod_count = other.cheer_mod_count;
        self.yell_count_reduction = other.yell_count_reduction;
        self.negated_triggers.clear(); self.negated_triggers.extend_from_slice(&other.negated_triggers);
        self.prevent_activate = other.prevent_activate;
        self.prevent_baton_touch = other.prevent_baton_touch;
        self.prevent_success_pile_set = other.prevent_success_pile_set;
        self.prevent_play_to_slot_mask = other.prevent_play_to_slot_mask;
        self.played_group_mask = other.played_group_mask;
        self.yell_cards.clear(); self.yell_cards.extend_from_slice(&other.yell_cards);
        self.excess_hearts = other.excess_hearts;
    }
    pub fn is_energy_tapped(&self, idx: usize) -> bool {
        if idx >= 64 { return false; }
        (self.tapped_energy_mask & (1u64 << idx)) != 0
    }

    pub fn set_energy_tapped(&mut self, idx: usize, tapped: bool) {
        if idx >= 64 { return; }
        if tapped {
            self.tapped_energy_mask |= 1u64 << idx;
        } else {
            self.tapped_energy_mask &= !(1u64 << idx);
        }
    }

    pub fn get_untapped_energy_indices(&self, count: usize) -> Vec<usize> {
        if count == 0 { return Vec::new(); }
        let mut indices = Vec::with_capacity(count);
        for i in 0..self.energy_zone.len() {
            if !self.is_energy_tapped(i) {
                indices.push(i);
                if indices.len() == count { break; }
            }
        }
        indices
    }

    pub fn tapped_energy_count(&self) -> u32 {
        self.tapped_energy_mask.count_ones()
    }
}
