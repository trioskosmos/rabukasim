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
use super::rules::BoardAura;
use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use serde::{Deserialize, Serialize};
use smallvec::SmallVec;

fn default_baton_touch_limit() -> u8 {
    3
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Serialize, Deserialize)]
pub struct PlayerState {
    pub player_id: u8,
    #[serde(default)]
    pub hand: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub deck: SmallVec<[i32; 60]>,
    #[serde(default)]
    pub initial_deck: SmallVec<[i32; 60]>, // Stable reference for AZ
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
    // 16..17: baton_touch_limit (2 bits)
    #[serde(default = "default_baton_touch_limit")]
    pub baton_touch_limit: u8,
    #[serde(default)]
    pub live_set_limit: u8,
    #[serde(default)]
    pub blade_overrides: [i16; 3], // -1 = no override
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
    pub revealed_cards: SmallVec<[i32; 16]>, // Persistent buffer for SAME_NAME_AS_REVEALED during an ability
    #[serde(default)]
    pub live_deck: SmallVec<[i32; 12]>, // Live cards available for Live Set phase
    #[serde(default)]
    pub granted_abilities: Vec<(i32, i32, u16)>, // (target_cid, source_cid, ab_idx)
    #[serde(default)]
    pub perf_triggered_abilities: Vec<(i32, i16, TriggerType)>, // (source_cid, ab_idx, trigger)
    #[serde(default)]
    pub board_aura: BoardAura,

    #[serde(default)]
    pub cost_modifiers: Vec<(Condition, i32)>, // (condition, amount)
    #[serde(default)]
    pub played_group_mask: u32,

    #[serde(default)]
    pub flags: u32,
    // Bitfields in flags:
    // 0: cannot_live
    // 1: deck_refreshed
    // 2: immunity
    // 3..5: tapped_m_0..2
    // 6..8: moved_m_0..2
    // 9..11: revealed_m_0..2
    // 12: suppress_auto_deck_refresh
    // 13: skip_next_activate
    // 14..15: baton_touch_count (2 bits)
    // 16..17: baton_touch_limit (2 bits)
    // 18..22: play_count_this_turn (5 bits: 0-31)
    // 23..24: prevent_activate (2 bits)
    // 25..26: prevent_baton_touch (2 bits)
    // 27..28: prevent_success_pile_set (2 bits)
    // 29..31: prevent_play_to_slot_mask (3 bits)
    #[serde(default)]
    pub cheer_mod_count: u16,
    #[serde(default)]
    pub yell_count_reduction: i16,
    #[serde(default)]
    pub negated_triggers: Vec<(i32, TriggerType, i32)>, // (target_cid, trigger_type, count)
    #[serde(default)]
    pub yell_cards: SmallVec<[i32; 8]>,
    #[serde(default)]
    pub excess_hearts: u32,
    #[serde(default)]
    pub excess_hearts_by_color: [u8; 7],
    #[serde(default)]
    pub activated_energy_group_mask: u32,
    #[serde(default)]
    pub activated_member_group_mask: u32,
    #[serde(default)]
    pub discarded_this_turn: u16,
    #[serde(default)]
    pub discard_ids_this_turn: SmallVec<[i32; 16]>,
    #[serde(default)]
    pub baton_source_ids: SmallVec<[i32; 4]>,
    #[serde(default)]
    pub baton_source_slots: SmallVec<[usize; 4]>,
    #[serde(default)]
    pub cached_total_hearts: HeartBoard,
    #[serde(default)]
    pub cached_total_blades: u32,
    #[serde(default)]
    pub cached_slot_blades: [u32; 3],
    #[serde(default)]
    pub cached_slot_hearts: [HeartBoard; 3],
    #[serde(default)]
    pub cached_deck_stats: DeckStats,
    #[serde(default)]
    pub yell_heart_bonus: [HeartBoard; 3],
    #[serde(default)]
    pub yell_blade_bonus: [u32; 3],
}

impl Default for PlayerState {
    fn default() -> Self {
        PlayerState {
            player_id: 0,
            hand: SmallVec::new(),
            deck: SmallVec::new(),
            initial_deck: SmallVec::new(),
            discard: SmallVec::new(),
            exile: SmallVec::new(),
            energy_deck: SmallVec::new(),
            energy_zone: SmallVec::new(),
            success_lives: SmallVec::new(),
            live_zone: [-1; 3],
            stage: [-1; 3],
            stage_energy_count: [0; 3],
            tapped_energy_mask: 0,
            score: 0,
            current_turn_notes: 0,
            used_abilities: SmallVec::new(),
            live_score_bonus: 0,
            live_score_bonus_logs: SmallVec::new(),
            blade_buffs: [0; 3],
            live_set_limit: 0,
            blade_overrides: [-1; 3],
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
            revealed_cards: SmallVec::new(),
            live_deck: SmallVec::new(),
            granted_abilities: Vec::new(),
            perf_triggered_abilities: Vec::new(),
            cost_modifiers: Vec::new(),
            board_aura: BoardAura::default(),
            flags: 3 << 16, // Default baton_touch_limit = 3 (bits 16..17)
            baton_touch_limit: 3,
            cheer_mod_count: 0,
            yell_count_reduction: 0,
            negated_triggers: Vec::new(),
            played_group_mask: 0,
            yell_cards: SmallVec::new(),
            excess_hearts: 0,
            excess_hearts_by_color: [0; 7],
            activated_energy_group_mask: 0,
            activated_member_group_mask: 0,
            discarded_this_turn: 0,
            baton_source_ids: SmallVec::new(),
            baton_source_slots: SmallVec::new(),
            cached_total_hearts: HeartBoard::default(),
            cached_total_blades: 0,
            cached_slot_blades: [0; 3],
            cached_slot_hearts: [HeartBoard::default(); 3],
            cached_deck_stats: DeckStats::default(),
            yell_heart_bonus: [HeartBoard::default(); 3],
            yell_blade_bonus: [0; 3],
            discard_ids_this_turn: SmallVec::new(),
        }
    }
}

impl PlayerState {
    pub const FLAG_CANNOT_LIVE: u8 = 0;
    pub const FLAG_DECK_REFRESHED: u8 = 1;
    pub const FLAG_IMMUNITY: u8 = 2;
    pub const FLAG_SUPPRESS_AUTO_DECK_REFRESH: u8 = 12;
    pub const OFFSET_TAPPED: u8 = 3;
    pub const OFFSET_MOVED: u8 = 6;
    pub const OFFSET_REVEALED: u8 = 9;
    pub const OFFSET_SKIP_NEXT_ACTIVATE: u8 = 13;
    pub const OFFSET_BATON_COUNT: u8 = 14;
    pub const OFFSET_BATON_LIMIT: u8 = 16;
    pub const OFFSET_PLAY_COUNT: u8 = 18;
    pub const OFFSET_PREVENT_ACTIVATE: u8 = 23;
    pub const OFFSET_PREVENT_BATON: u8 = 25;
    pub const OFFSET_PREVENT_SUCCESS_PILE: u8 = 27;
    pub const OFFSET_PREVENT_PLAY_TO_SLOT: u8 = 29;

    pub const MASK_TAPPED: u32 = 56;
    pub const MASK_MOVED: u32 = 448;
    pub const MASK_REVEALED: u32 = 3584;
    pub const MASK_BATON_COUNT: u32 = 49152;
    pub const MASK_BATON_LIMIT: u32 = 196608;
    pub const MASK_PLAY_COUNT: u32 = 8126464;
    pub const MASK_PREVENT_ACTIVATE: u32 = 25165824;
    pub const MASK_PREVENT_BATON: u32 = 100663296;
    pub const MASK_PREVENT_SUCCESS_PILE: u32 = 402653184;
    pub const MASK_PREVENT_PLAY_TO_SLOT: u32 = 3758096384;

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

    pub fn skip_next_activate(&self) -> bool {
        self.get_flag(Self::OFFSET_SKIP_NEXT_ACTIVATE)
    }
    pub fn set_skip_next_activate(&mut self, val: bool) {
        self.set_flag(Self::OFFSET_SKIP_NEXT_ACTIVATE, val);
    }

    pub fn baton_touch_count(&self) -> u8 {
        ((self.flags & Self::MASK_BATON_COUNT) >> Self::OFFSET_BATON_COUNT) as u8
    }
    pub fn set_baton_touch_count(&mut self, val: u8) {
        self.flags = (self.flags & !Self::MASK_BATON_COUNT)
            | (((val as u32) & 0b11) << Self::OFFSET_BATON_COUNT);
    }

    pub fn baton_touch_limit(&self) -> u8 {
        self.baton_touch_limit
    }
    pub fn set_baton_touch_limit(&mut self, val: u8) {
        self.baton_touch_limit = val;
    }

    pub fn play_count_this_turn(&self) -> u8 {
        ((self.flags & Self::MASK_PLAY_COUNT) >> Self::OFFSET_PLAY_COUNT) as u8
    }
    pub fn set_play_count_this_turn(&mut self, val: u8) {
        self.flags = (self.flags & !Self::MASK_PLAY_COUNT)
            | (((val as u32) & 0b11111) << Self::OFFSET_PLAY_COUNT);
    }

    pub fn prevent_activate(&self) -> u8 {
        ((self.flags & Self::MASK_PREVENT_ACTIVATE) >> Self::OFFSET_PREVENT_ACTIVATE) as u8
    }
    pub fn set_prevent_activate(&mut self, val: u8) {
        self.flags = (self.flags & !Self::MASK_PREVENT_ACTIVATE)
            | (((val as u32) & 0b11) << Self::OFFSET_PREVENT_ACTIVATE);
    }

    pub fn prevent_baton_touch(&self) -> u8 {
        ((self.flags & Self::MASK_PREVENT_BATON) >> Self::OFFSET_PREVENT_BATON) as u8
    }
    pub fn set_prevent_baton_touch(&mut self, val: u8) {
        self.flags = (self.flags & !Self::MASK_PREVENT_BATON)
            | (((val as u32) & 0b11) << Self::OFFSET_PREVENT_BATON);
    }

    pub fn prevent_success_pile_set(&self) -> u8 {
        self.live_set_limit
    }
    pub fn set_prevent_success_pile_set(&mut self, val: u8) {
        self.live_set_limit = val;
    }

    pub fn prevent_play_to_slot_mask(&self) -> u8 {
        ((self.flags & Self::MASK_PREVENT_PLAY_TO_SLOT) >> Self::OFFSET_PREVENT_PLAY_TO_SLOT) as u8
    }
    pub fn set_prevent_play_to_slot_mask(&mut self, val: u8) {
        self.flags = (self.flags & !Self::MASK_PREVENT_PLAY_TO_SLOT)
            | (((val as u32) & 0b111) << Self::OFFSET_PREVENT_PLAY_TO_SLOT);
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

    pub fn push_hand_card(&mut self, card_id: i32) {
        self.hand.push(card_id);
    }

    pub fn draw_hand_card(&mut self, card_id: i32, turn: i32) {
        self.hand.push(card_id);
        self.hand_added_turn.push(turn);
    }

    pub fn gain_hand_card(&mut self, card_id: i32) {
        self.hand.push(card_id);
        self.hand_increased_this_turn = self.hand_increased_this_turn.saturating_add(1);
    }

    pub fn push_discard_card(&mut self, card_id: i32) {
        self.discard.push(card_id);
        self.discarded_this_turn += 1;
        self.discard_ids_this_turn.push(card_id);
    }

    pub fn pop_discard_card(&mut self) -> Option<i32> {
        self.discard.pop()
    }

    pub fn remove_discard_card(&mut self, idx: usize) -> Option<i32> {
        if idx >= self.discard.len() {
            return None;
        }

        Some(self.discard.remove(idx))
    }

    pub fn push_deck_card(&mut self, card_id: i32) {
        self.cached_deck_stats = DeckStats::default();
        self.deck.push(card_id);
    }

    pub fn pop_deck_card(&mut self) -> Option<i32> {
        self.cached_deck_stats = DeckStats::default();
        self.deck.pop()
    }

    pub fn remove_deck_card(&mut self, idx: usize) -> Option<i32> {
        if idx >= self.deck.len() {
            return None;
        }

        self.cached_deck_stats = DeckStats::default();
        Some(self.deck.remove(idx))
    }

    pub fn push_energy_card(&mut self, card_id: i32, tapped: bool) {
        let idx = self.energy_zone.len();
        self.energy_zone.push(card_id);
        self.set_energy_tapped(idx, tapped);
    }

    pub fn pop_energy_card(&mut self) -> Option<i32> {
        let idx = self.energy_zone.len().checked_sub(1)?;
        let card_id = self.energy_zone.pop();
        self.set_energy_tapped(idx, false);
        card_id
    }

    pub fn remove_energy_card(&mut self, idx: usize) -> Option<i32> {
        if idx >= self.energy_zone.len() {
            return None;
        }

        let card_id = self.energy_zone.remove(idx);
        let lower_mask = if idx == 0 {
            0
        } else {
            self.tapped_energy_mask & ((1u64 << idx) - 1)
        };
        let upper_mask = self.tapped_energy_mask >> (idx + 1);
        self.tapped_energy_mask = lower_mask | (upper_mask << idx);
        Some(card_id)
    }

    pub fn remove_hand_card(&mut self, idx: usize) -> Option<i32> {
        if idx >= self.hand.len() {
            return None;
        }

        let card_id = self.hand.remove(idx);
        if idx < self.hand_added_turn.len() {
            self.hand_added_turn.remove(idx);
        }
        Some(card_id)
    }

    pub fn pop_hand_card(&mut self) -> Option<i32> {
        let card_id = self.hand.pop();
        if card_id.is_some() && self.hand_added_turn.len() > self.hand.len() {
            self.hand_added_turn.pop();
        }
        card_id
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
            self.blade_overrides.swap(i, j);
            self.heart_buffs.swap(i, j);
        }
    }

    /// Moves all data from src slot to dst slot (dst must be empty). Clears src after move.
    pub fn move_slot_data(&mut self, src: usize, dst: usize) {
        if src < 3 && dst < 3 && src != dst && self.stage[dst] == -1 {
            self.stage[dst] = self.stage[src];
            self.stage[src] = -1;
            
            let was_tapped = self.is_tapped(src);
            self.set_tapped(dst, was_tapped);
            self.set_tapped(src, false);
            
            // Move energy data
            self.stage_energy[dst] = std::mem::take(&mut self.stage_energy[src]);
            self.stage_energy_count[dst] = self.stage_energy_count[src];
            self.stage_energy_count[src] = 0;
            
            // Move buffs
            self.blade_buffs[dst] = self.blade_buffs[src];
            self.blade_buffs[src] = 0;
            self.blade_overrides[dst] = self.blade_overrides[src];
            self.blade_overrides[src] = -1;
            self.heart_buffs[dst] = self.heart_buffs[src];
            self.heart_buffs[src] = HeartBoard::default();
            
            self.set_moved(src, true);
            self.set_moved(dst, true);
        }
    }

    pub fn get_slot_of(&self, card_id: i32) -> Option<usize> {
        self.stage
            .iter()
            .position(|&stage_card_id| stage_card_id == card_id)
    }

    pub fn untap_all(&mut self, skip_physical_untap: bool) {
        if !skip_physical_untap {
            // Clear tapped and moved flags
            self.flags &= !(Self::MASK_TAPPED | Self::MASK_MOVED);
            self.tapped_energy_mask = 0;
        } else {
            // Even if skipping untap, we must clear "moved" flags for next turn
            self.flags &= !Self::MASK_MOVED;
        }

        self.set_baton_touch_count(0);
        self.baton_source_ids.clear();
        self.baton_source_slots.clear();
        self.blade_buffs = [0; 3];
        self.blade_overrides = [-1; 3];
        self.heart_buffs = [HeartBoard::default(); 3];
        self.cost_reduction = 0;
        self.slot_cost_modifiers = [0; 3];
        // self.cost_reductions is inside BoardAura so it is reset by BoardAura::default()
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

        self.reset_turn_restrictions();
        self.cheer_mod_count = 0;
        self.played_group_mask = 0;
        self.yell_cards.clear();
        self.excess_hearts = 0;
        self.excess_hearts_by_color = [0; 7];
        self.activated_energy_group_mask = 0;
        self.activated_member_group_mask = 0;
        self.discarded_this_turn = 0;
        self.discard_ids_this_turn.clear();
        self.cached_total_hearts = HeartBoard::default();
        self.cached_total_blades = 0;
        self.cached_deck_stats = DeckStats::default();
        self.yell_heart_bonus = [HeartBoard::default(); 3];
        self.yell_blade_bonus = [0; 3];
    }

    pub fn reset_turn_restrictions(&mut self) {
        self.set_prevent_activate(0);
        self.set_prevent_baton_touch(0);
        self.set_prevent_success_pile_set(0);
        self.set_prevent_play_to_slot_mask(0);
        self.set_play_count_this_turn(0);
        self.set_baton_touch_count(0);
    }

    pub fn copy_from(&mut self, other: &PlayerState) {
        self.player_id = other.player_id;
        self.hand.clear();
        self.hand.extend_from_slice(&other.hand);
        self.deck.clear();
        self.deck.extend_from_slice(&other.deck);
        // self.initial_deck.clone_from(&other.initial_deck); // Optimization: Never changes
        self.discard.clear();
        self.discard.extend_from_slice(&other.discard);
        self.exile.clear();
        self.exile.extend_from_slice(&other.exile);
        self.energy_deck.clear();
        self.energy_deck.extend_from_slice(&other.energy_deck);
        self.energy_zone.clear();
        self.energy_zone.extend_from_slice(&other.energy_zone);
        self.success_lives.clear();
        self.success_lives.extend_from_slice(&other.success_lives);
        self.live_zone = other.live_zone;
        self.stage = other.stage;
        self.stage_energy_count = other.stage_energy_count;
        self.tapped_energy_mask = other.tapped_energy_mask;
        self.set_baton_touch_count(other.baton_touch_count());
        self.set_baton_touch_limit(other.baton_touch_limit());
        self.score = other.score;
        self.current_turn_notes = other.current_turn_notes;
        self.used_abilities = other.used_abilities.clone();
        self.live_score_bonus = other.live_score_bonus;
        self.live_score_bonus_logs.clear();
        self.live_score_bonus_logs
            .extend_from_slice(&other.live_score_bonus_logs);
        self.blade_buffs = other.blade_buffs;
        self.blade_overrides = other.blade_overrides;
        self.heart_buffs = other.heart_buffs;
        self.cost_reduction = other.cost_reduction;
        self.hand_increased_this_turn = other.hand_increased_this_turn;
        self.slot_cost_modifiers = other.slot_cost_modifiers;
        self.blade_buff_logs.clear();
        self.blade_buff_logs
            .extend_from_slice(&other.blade_buff_logs);
        self.heart_buff_logs.clear();
        self.heart_buff_logs
            .extend_from_slice(&other.heart_buff_logs);
        for i in 0..3 {
            self.stage_energy[i].clear();
            self.stage_energy[i].extend_from_slice(&other.stage_energy[i]);
        }
        self.color_transforms.clear();
        self.color_transforms
            .extend_from_slice(&other.color_transforms);
        self.heart_req_reductions = other.heart_req_reductions;
        self.heart_req_additions = other.heart_req_additions;
        self.heart_req_reduction_logs.clear();
        self.heart_req_reduction_logs
            .extend_from_slice(&other.heart_req_reduction_logs);
        self.heart_req_addition_logs.clear();
        self.heart_req_addition_logs
            .extend_from_slice(&other.heart_req_addition_logs);
        self.mulligan_selection = other.mulligan_selection;
        self.hand_added_turn.clear();
        self.hand_added_turn
            .extend_from_slice(&other.hand_added_turn);
        self.restrictions.clear();
        self.restrictions.extend_from_slice(&other.restrictions);
        self.looked_cards.clear();
        self.looked_cards.extend_from_slice(&other.looked_cards);
        self.revealed_cards.clear();
        self.revealed_cards.extend_from_slice(&other.revealed_cards);
        self.live_deck.clear();
        self.live_deck.extend_from_slice(&other.live_deck);

        self.granted_abilities = other.granted_abilities.clone();
        self.perf_triggered_abilities = other.perf_triggered_abilities.clone();
        self.cost_modifiers = other.cost_modifiers.clone();

        self.flags = other.flags;
        self.cheer_mod_count = other.cheer_mod_count;
        self.yell_count_reduction = other.yell_count_reduction;

        self.negated_triggers = other.negated_triggers.clone();
        self.played_group_mask = other.played_group_mask;

        self.yell_cards.clear();
        self.yell_cards.extend_from_slice(&other.yell_cards);

        self.excess_hearts = other.excess_hearts;
        self.excess_hearts_by_color = other.excess_hearts_by_color;
        self.activated_energy_group_mask = other.activated_energy_group_mask;
        self.activated_member_group_mask = other.activated_member_group_mask;
        self.discarded_this_turn = other.discarded_this_turn;
        self.discard_ids_this_turn.clear();
        self.discard_ids_this_turn
            .extend_from_slice(&other.discard_ids_this_turn);
        self.baton_source_ids.clear();
        self.baton_source_ids
            .extend_from_slice(&other.baton_source_ids);
        self.baton_source_slots.clear();
        self.baton_source_slots
            .extend_from_slice(&other.baton_source_slots);

        self.cached_total_hearts = other.cached_total_hearts;
        self.cached_total_blades = other.cached_total_blades;
        self.cached_slot_blades = other.cached_slot_blades;
        self.cached_slot_hearts = other.cached_slot_hearts;
        self.cached_deck_stats = other.cached_deck_stats;
        self.yell_heart_bonus = other.yell_heart_bonus;
        self.yell_blade_bonus = other.yell_blade_bonus;
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

    pub fn get_untapped_energy_indices(&self, count: usize) -> SmallVec<[usize; 8]> {
        if count == 0 {
            return SmallVec::new();
        }
        let mut indices: SmallVec<[usize; 8]> = SmallVec::new();
        let len = self.energy_zone.len().min(64);
        let mask = if len >= 64 {
            u64::MAX
        } else {
            (1u64 << len) - 1
        };
        let available_mask = (!self.tapped_energy_mask) & mask;
        let mut mask = available_mask;
        while mask != 0 && indices.len() < count {
            let idx = mask.trailing_zeros() as usize;
            indices.push(idx);
            mask &= mask - 1;
        }
        indices
    }

    pub fn get_tapped_energy_indices(&self, count: usize) -> SmallVec<[usize; 8]> {
        if count == 0 {
            return SmallVec::new();
        }
        let mut indices: SmallVec<[usize; 8]> = SmallVec::new();
        let len = self.energy_zone.len().min(64);
        let mask = if len >= 64 {
            u64::MAX
        } else {
            (1u64 << len) - 1
        };
        let mut mask = self.tapped_energy_mask & mask;
        while mask != 0 && indices.len() < count {
            let idx = mask.trailing_zeros() as usize;
            indices.push(idx);
            mask &= mask - 1;
        }
        indices
    }

    pub fn tapped_energy_count(&self) -> u32 {
        self.tapped_energy_mask.count_ones()
    }
}

#[cfg(test)]
mod test_sizes {
    use super::*;
    use std::mem::size_of;

    #[test]
    fn test_print_player_state_sizes() {
        println!("Size of PlayerState: {}", size_of::<PlayerState>());
        println!(
            "Size of SmallVec<[i32; 16]>: {}",
            size_of::<SmallVec<[i32; 16]>>()
        );
        println!(
            "Size of SmallVec<[i32; 60]>: {}",
            size_of::<SmallVec<[i32; 60]>>()
        );
    }
}
