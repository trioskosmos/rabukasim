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

use super::models::*;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlayerState {
    pub player_id: u8,
    #[serde(default)]
    pub hand: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub deck: SmallVec<[i32; 60]>,
    #[serde(default)]
    pub discard: SmallVec<[i32; 32]>,
    #[serde(default)]
    pub exile: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub energy_deck: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub energy_zone: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub success_lives: SmallVec<[i32; 8]>,
    #[serde(default)]
    pub live_zone: [i32; 3], // -1 or ID
    #[serde(default)]
    pub stage: [i32; 3],
    #[serde(default)]
    pub stage_energy_count: [u8; 3],
    #[serde(default)]
    pub tapped_energy_mask: u64, // Bitmask for energy_zone status
    #[serde(default)]
    pub baton_touch_count: u8,
    #[serde(default)]
    pub baton_touch_limit: u8,
    #[serde(default)]
    pub score: u32,
    #[serde(default)]
    pub current_turn_notes: u32,
    #[serde(default)]
    pub used_abilities: SmallVec<[u32; 16]>,
    #[serde(default)]
    pub live_score_bonus: i32,
    #[serde(default)]
    pub live_score_bonus_logs: SmallVec<[(i32, i32); 4]>, // (source_cid, amount)
    #[serde(default)]
    pub blade_buffs: [i16; 3],
    #[serde(default)]
    pub heart_buffs: [HeartBoard; 3],
    #[serde(default)]
    pub blade_buff_logs: SmallVec<[(i32, i16, u8); 4]>, // (source_cid, amount, slot_idx)
    #[serde(default)]
    pub heart_buff_logs: SmallVec<[(i32, i32, u8, u8); 4]>, // (source_cid, amount, color, slot_idx)
    #[serde(default)]
    pub cost_reduction: i16,
    #[serde(default)]
    pub hand_increased_this_turn: u32,
    #[serde(default)]
    pub stage_energy: [SmallVec<[i32; 4]>; 3],
    #[serde(default)]
    pub slot_cost_modifiers: [i16; 3], // Cached cost modifiers for each stage slot
    #[serde(default)]
    pub color_transforms: SmallVec<[(i32, u8, u8); 4]>, // (source_cid, src_color, dst_color)
    #[serde(default)]
    pub heart_req_reductions: HeartBoard,
    #[serde(default)]
    pub heart_req_additions: HeartBoard,
    #[serde(default)]
    pub heart_req_reduction_logs: SmallVec<[(i32, u8, u8); 4]>, // (source_cid, color, amount)
    #[serde(default)]
    pub heart_req_addition_logs: SmallVec<[(i32, u8, u8); 4]>, // (source_cid, color, amount)
    #[serde(default)]
    pub mulligan_selection: u64,
    #[serde(default)]
    pub hand_added_turn: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub restrictions: SmallVec<[u8; 8]>,
    #[serde(default)]
    pub looked_cards: SmallVec<[i32; 16]>, // Shared buffer for revealing cards to UI
    #[serde(default)]
    pub live_deck: SmallVec<[i32; 12]>, // Live cards available for Live Set phase
    #[serde(default)]
    pub granted_abilities: Vec<(i32, i32, u16)>, // (target_cid, source_cid, ab_idx)
    #[serde(default)]
    pub perf_triggered_abilities: Vec<(i32, i16, TriggerType)>, // (source_cid, ab_idx, trigger)

    #[serde(default)]
    pub cost_modifiers: Vec<(Condition, i32)>, // (condition, amount)
    #[serde(default)]
    pub played_group_mask: u32,
    #[serde(default)]
    pub play_count_this_turn: u8,

    // Bitfields
    #[serde(default)]
    pub flags: u32, // [cannot_live:1, deck_refreshed:1, immunity:1, tapped_m_0..3:3, moved_m_0..3:3, live_revealed_0..3:3]
    #[serde(default)]
    pub cheer_mod_count: u16,
    #[serde(default)]
    pub yell_count_reduction: i16,
    #[serde(default)]
    pub negated_triggers: Vec<(i32, TriggerType, i32)>, // (target_cid, trigger_type, count)
    #[serde(default)]
    pub prevent_activate: u8,
    #[serde(default)]
    pub prevent_baton_touch: u8,
    #[serde(default)]
    pub prevent_success_pile_set: u8,
    #[serde(default)]
    pub prevent_play_to_slot_mask: u8,
    #[serde(default)]
    pub yell_cards: SmallVec<[i32; 8]>,
    #[serde(default)]
    pub excess_hearts: u32,
    #[serde(default)]
    pub skip_next_activate: bool,
    #[serde(default)]
    pub activated_energy_group_mask: u32,
    #[serde(default)]
    pub activated_member_group_mask: u32,
    #[serde(default)]
    pub discarded_this_turn: u16,
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
            current_turn_notes: 0,
            used_abilities: SmallVec::new(),
            live_score_bonus: 0,
            live_score_bonus_logs: SmallVec::new(),
            blade_buffs: [0; 3],
            heart_buffs: [HeartBoard::default(); 3],
            blade_buff_logs: SmallVec::new(),
            heart_buff_logs: SmallVec::new(),
            cost_reduction: 0,
            hand_increased_this_turn: 0,
            stage_energy: [SmallVec::new(), SmallVec::new(), SmallVec::new()],
            slot_cost_modifiers: [0; 3],
            color_transforms: SmallVec::new(),
            heart_req_reductions: HeartBoard::default(),
            heart_req_additions: HeartBoard::default(),
            heart_req_reduction_logs: SmallVec::new(),
            heart_req_addition_logs: SmallVec::new(),
            mulligan_selection: 0,
            hand_added_turn: SmallVec::new(),
            restrictions: SmallVec::new(),
            looked_cards: SmallVec::new(),
            live_deck: SmallVec::new(),
            granted_abilities: Vec::new(),
            perf_triggered_abilities: Vec::new(),
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
            play_count_this_turn: 0,
            yell_cards: SmallVec::new(),
            excess_hearts: 0,
            skip_next_activate: false,
            activated_energy_group_mask: 0,
            activated_member_group_mask: 0,
            discarded_this_turn: 0,
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

    pub fn get_flag(&self, bit: u8) -> bool {
        (self.flags >> bit) & 1 == 1
    }
    pub fn set_flag(&mut self, bit: u8, val: bool) {
        if val {
            self.flags |= 1 << bit;
        } else {
            self.flags &= !(1 << bit);
        }
    }

    pub fn is_tapped(&self, slot: usize) -> bool {
        self.get_flag(Self::OFFSET_TAPPED + slot as u8)
    }
    pub fn set_tapped(&mut self, slot: usize, val: bool) {
        self.set_flag(Self::OFFSET_TAPPED + slot as u8, val);
    }

    pub fn is_moved(&self, slot: usize) -> bool {
        self.get_flag(Self::OFFSET_MOVED + slot as u8)
    }
    pub fn set_moved(&mut self, slot: usize, val: bool) {
        self.set_flag(Self::OFFSET_MOVED + slot as u8, val);
    }

    pub fn is_revealed(&self, slot: usize) -> bool {
        self.get_flag(Self::OFFSET_REVEALED + slot as u8)
    }
    pub fn set_revealed(&mut self, slot: usize, val: bool) {
        self.set_flag(Self::OFFSET_REVEALED + slot as u8, val);
    }

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

    pub fn untap_all(&mut self, skip_physical_untap: bool) {
        if !skip_physical_untap {
            // Clear tapped and moved flags (bits 3-8)
            self.flags &= !0b111111000;
            self.tapped_energy_mask = 0;
        } else {
            // Even if skipping untap, we must clear "moved" flags for next turn
            self.flags &= !0b111000000;
        }

        self.baton_touch_count = 0;
        self.blade_buffs = [0; 3];
        self.heart_buffs = [HeartBoard::default(); 3];
        self.cost_reduction = 0;
        self.slot_cost_modifiers = [0; 3];
        self.live_score_bonus = 0;
        self.live_score_bonus_logs.clear();
        self.used_abilities.clear();
        self.color_transforms.clear();
        self.heart_req_reductions = HeartBoard::default();
        self.heart_req_additions = HeartBoard::default();
        self.heart_req_reduction_logs.clear();
        self.heart_req_addition_logs.clear();
        self.blade_buff_logs.clear();
        self.heart_buff_logs.clear();
        self.mulligan_selection = 0;
        self.granted_abilities.clear();
        self.perf_triggered_abilities.clear();
        self.cost_modifiers.clear();

        self.cheer_mod_count = 0;
        self.prevent_activate = 0;
        self.prevent_baton_touch = 0;
        self.prevent_success_pile_set = 0;
        self.prevent_play_to_slot_mask = 0;
        self.played_group_mask = 0;
        self.play_count_this_turn = 0;
        self.yell_cards.clear();
        self.excess_hearts = 0;
        self.activated_energy_group_mask = 0;
        self.activated_member_group_mask = 0;
        self.discarded_this_turn = 0;
    }

    pub fn copy_from(&mut self, other: &PlayerState) {
        macro_rules! copy_smallvec {
            ($dst:expr, $src:expr) => {
                if $src.is_empty() {
                    $dst.clear();
                } else {
                    $dst.clear();
                    $dst.extend_from_slice(&$src);
                }
            };
        }

        self.player_id = other.player_id;
        copy_smallvec!(self.hand, other.hand);
        copy_smallvec!(self.deck, other.deck);
        copy_smallvec!(self.discard, other.discard);
        copy_smallvec!(self.exile, other.exile);
        copy_smallvec!(self.energy_deck, other.energy_deck);
        copy_smallvec!(self.energy_zone, other.energy_zone);
        copy_smallvec!(self.success_lives, other.success_lives);
        self.live_zone = other.live_zone;
        self.stage = other.stage;
        self.stage_energy_count = other.stage_energy_count;
        self.tapped_energy_mask = other.tapped_energy_mask;
        self.baton_touch_count = other.baton_touch_count;
        self.baton_touch_limit = other.baton_touch_limit;
        self.score = other.score;
        self.current_turn_notes = other.current_turn_notes;
        copy_smallvec!(self.used_abilities, other.used_abilities);
        self.live_score_bonus = other.live_score_bonus;
        copy_smallvec!(self.live_score_bonus_logs, other.live_score_bonus_logs);
        self.blade_buffs = other.blade_buffs;
        self.heart_buffs = other.heart_buffs;
        self.cost_reduction = other.cost_reduction;
        self.hand_increased_this_turn = other.hand_increased_this_turn;
        self.slot_cost_modifiers = other.slot_cost_modifiers;
        copy_smallvec!(self.blade_buff_logs, other.blade_buff_logs);
        copy_smallvec!(self.heart_buff_logs, other.heart_buff_logs);
        for i in 0..3 {
            copy_smallvec!(self.stage_energy[i], other.stage_energy[i]);
        }
        copy_smallvec!(self.color_transforms, other.color_transforms);
        self.heart_req_reductions = other.heart_req_reductions;
        self.heart_req_additions = other.heart_req_additions;
        copy_smallvec!(
            self.heart_req_reduction_logs,
            other.heart_req_reduction_logs
        );
        self.mulligan_selection = other.mulligan_selection;
        copy_smallvec!(self.hand_added_turn, other.hand_added_turn);
        copy_smallvec!(self.restrictions, other.restrictions);
        copy_smallvec!(self.looked_cards, other.looked_cards);
        copy_smallvec!(self.live_deck, other.live_deck);
        copy_smallvec!(self.granted_abilities, other.granted_abilities);

        self.perf_triggered_abilities.clear();
        if !other.perf_triggered_abilities.is_empty() {
            self.perf_triggered_abilities.extend(other.perf_triggered_abilities.iter().cloned());
        }


        self.cost_modifiers.clear();
        if !other.cost_modifiers.is_empty() {
            self.cost_modifiers
                .extend(other.cost_modifiers.iter().cloned());
        }

        self.flags = other.flags;
        self.cheer_mod_count = other.cheer_mod_count;
        self.yell_count_reduction = other.yell_count_reduction;
        copy_smallvec!(self.negated_triggers, other.negated_triggers);
        self.prevent_activate = other.prevent_activate;
        self.prevent_baton_touch = other.prevent_baton_touch;
        self.prevent_success_pile_set = other.prevent_success_pile_set;
        self.prevent_play_to_slot_mask = other.prevent_play_to_slot_mask;
        self.played_group_mask = other.played_group_mask;
        self.play_count_this_turn = other.play_count_this_turn;
        copy_smallvec!(self.yell_cards, other.yell_cards);
        self.excess_hearts = other.excess_hearts;
        self.skip_next_activate = other.skip_next_activate;
        self.activated_energy_group_mask = other.activated_energy_group_mask;
        self.activated_member_group_mask = other.activated_member_group_mask;
        self.discarded_this_turn = other.discarded_this_turn;
    }
    pub fn is_energy_tapped(&self, idx: usize) -> bool {
        if idx >= 64 {
            return false;
        }
        (self.tapped_energy_mask & (1u64 << idx)) != 0
    }

    pub fn set_energy_tapped(&mut self, idx: usize, tapped: bool) {
        if idx >= 64 {
            return;
        }
        if tapped {
            self.tapped_energy_mask |= 1u64 << idx;
        } else {
            self.tapped_energy_mask &= !(1u64 << idx);
        }
    }

    pub fn get_untapped_energy_indices(&self, count: usize) -> Vec<usize> {
        if count == 0 {
            return Vec::new();
        }
        let mut indices = Vec::with_capacity(count);
        for i in 0..self.energy_zone.len() {
            if !self.is_energy_tapped(i) {
                indices.push(i);
                if indices.len() == count {
                    break;
                }
            }
        }
        indices
    }

    pub fn tapped_energy_count(&self) -> u32 {
        self.tapped_energy_mask.count_ones()
    }
}
