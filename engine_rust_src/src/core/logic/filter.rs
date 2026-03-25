//! Card Filter Module
//!
//! This module provides a structured way to handle card filtering logic.
//! The 64-bit filter attribute is decomposed into meaningful fields for clarity.
//!
//! BIT LAYOUT (synchronized with Python _pack_filter_attr, Revision 5):
//! -----------------------------------------------------------------
//! Bits 0-1:   Target Player (1=Self, 2=Opponent)
//! Bits 2-3:   Card Type (1=Member, 2=Live)
//! Bit 4:      Group Enable flag
//! Bits 5-11:  Group ID (7 bits, 0-127)
//! Bit 12:     is_tapped flag
//! Bit 13:     has_blade_heart flag
//! Bit 14:     NOT has_blade_heart flag
//! Bit 15:     UNIQUE_NAMES flag
//! Bit 16:     Unit Enable flag
//! Bits 17-23: Unit ID (7 bits, 0-127)
//! Bit 24:     Cost/Value Enable flag
//! Bits 25-29: Value Threshold (5 bits, 0-31)
//! Bit 30:     Cost Mode (0=GE, 1=LE)
//! Bit 31:     Cost Type flag (1=Cost, 0=Heart) / TOTAL_COST
//! Bits 32-38: Color Mask (7 bits)
//! Bits 39-45: Character ID #1 (7 bits)
//! Bits 46-52: Character ID #2 (7 bits)
//! Bits 53-55: Zone Mask
//! Bits 56-58: Special ID
//! Bit 59:     Setsuna flag
//! Bit 60:     Compare Against Accumulated flag (New)
//! Bit 61:     Optional flag
//! Bit 62:     Keyword: Activated Energy
//! Bit 63:     Keyword: Activated Member

use super::CardDatabase;
pub use crate::core::generated_constants::*;
use serde::{Deserialize, Serialize};
// use crate::core::enums::Zone;
use crate::core::models::{AbilityContext, GameState};

// --- Filter Bitfield Constants (Now loaded from generated_constants.rs via constants.rs) ---
pub const FILTER_STATE_FLAGS_MASK: u64 = 61440; // 0xF000

/// A structured representation of the 64-bit filter attribute
/// Synchronized with ability.py _pack_filter_attr layout.
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
#[serde(default)]
pub struct CardFilter {
    pub is_enabled: bool,
    // Bits 0-1
    pub target_player: u8,
    // Bits 2-3
    pub card_type: u8,
    // Bit 4 + Bits 5-11
    pub group_enabled: bool,
    pub group_id: u8,
    // Bit 12
    pub is_tapped: bool,
    pub has_blade_heart: bool,
    pub not_has_blade_heart: bool,
    pub unique_names: bool,
    pub unit_enabled: bool,
    pub unit_id: u8,
    pub value_enabled: bool,
    pub value_threshold: u8,
    pub is_le: bool,
    pub is_cost_type: bool,
    pub color_mask: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub zone_mask: u8,
    pub special_id: u8,
    pub is_setsuna: bool,
    pub compare_accumulated: bool,
    pub is_optional: bool,
    pub keyword_energy: bool,
    pub keyword_member: bool,
}

impl CardFilter {
    pub fn matches(
        &self,
        state: &crate::core::logic::GameState,
        db: &CardDatabase,
        cid: i32,
        checked_slot: Option<(u8, i16)>,
        is_tapped_override: bool,
        effective_hearts: Option<&[u8; 7]>,
        ctx: &crate::core::logic::AbilityContext,
    ) -> bool {
        if !self.is_enabled {
            return true;
        }
        if cid == -1 {
            return false;
        }

        let inferred_owner = if checked_slot.is_some() {
            None
        } else {
            state
                .players
                .iter()
                .enumerate()
                .find_map(|(p_idx, player)| {
                    let owns_card = player.stage.iter().any(|&card_id| card_id == cid)
                        || player.hand.iter().any(|&card_id| card_id == cid)
                        || player.discard.iter().any(|&card_id| card_id == cid)
                        || player.deck.iter().any(|&card_id| card_id == cid)
                        || player.energy_zone.iter().any(|&card_id| card_id == cid)
                        || player.success_lives.iter().any(|&card_id| card_id == cid)
                        || player.live_zone.iter().any(|&card_id| card_id == cid)
                        || player.yell_cards.iter().any(|&card_id| card_id == cid);
                    if owns_card {
                        Some(p_idx as u8)
                    } else {
                        None
                    }
                })
        };

        // 0. Target Player Filter (bits 0-1)
        if self.target_player > 0 && self.target_player < 4 {
            let target_p = match self.target_player {
                1 => ctx.player_id,
                2 => 1 - ctx.player_id,
                3 => 255, // Both (always pass later)
                _ => ctx.player_id,
            };

            if target_p != 255 {
                let matches_owner = if let Some((p_idx, _)) = checked_slot {
                    Some(p_idx == target_p)
                } else {
                    inferred_owner.map(|owner| owner == target_p)
                };

                if matches_owner == Some(false) {
                    return false;
                }
            }
        }

        // 1. Card Type Filter (bits 2-3)
        if self.card_type > 0 {
            if self.card_type == 1 {
                // Member
                if !db.members.contains_key(&cid) {
                    return false;
                }
            } else if self.card_type == 2 {
                // Live
                if !db.lives.contains_key(&cid) {
                    return false;
                }
            }
        }

        // 2. Group Filter (bit 4 + bits 5-11)
        if self.group_enabled {
            if let Some(m) = db.get_member(cid) {
                if self.group_id == 101 {
                    // Special case for AQOURS_OR_SAINT_SNOW
                    if !m.groups.contains(&1) && !m.groups.contains(&11) {
                        return false;
                    }
                } else if !m.groups.contains(&self.group_id) {
                    return false;
                }
            } else if let Some(l) = db.get_live(cid) {
                if self.group_id == 101 {
                    if !l.groups.contains(&1) && !l.groups.contains(&11) {
                        return false;
                    }
                } else if !l.groups.contains(&self.group_id) {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 3. Unit Filter (bit 16 + bits 17-23)
        if self.unit_enabled {
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&self.unit_id) {
                    return false;
                }
            } else if let Some(l) = db.get_live(cid) {
                if !l.units.contains(&self.unit_id) {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 4. Character ID Filter
        if self.char_id_1 > 0 {
            let member = db.get_member(cid);
            let live = if member.is_none() {
                db.get_live(cid)
            } else {
                None
            };
            let (char_mask, normalized_name, _card_name) = if let Some(m) = member {
                (m.char_mask, Some(&m.normalized_name), Some(&m.name))
            } else if let Some(l) = live {
                (l.char_mask, Some(&l.normalized_name), Some(&l.name))
            } else {
                (0, None, None)
            };

            let mut filter_mask = 1u128 << self.char_id_1;
            if self.char_id_2 > 0 {
                filter_mask |= 1u128 << self.char_id_2;
            }
            let actual_char_id_3 = if self.char_id_3 > 0 {
                self.char_id_3
            } else if !self.unit_enabled && self.unit_id > 0 {
                self.unit_id
            } else {
                0
            };
            if actual_char_id_3 > 0 {
                filter_mask |= 1u128 << actual_char_id_3;
            }

            if char_mask != 0 {
                if (char_mask & filter_mask) == 0 {
                    return false;
                }
            } else if let Some(name) = normalized_name {
                // FALLBACK for manual test cards
                let mut matched = false;
                let target1 = crate::core::logic::card_db::get_character_name(self.char_id_1);
                if name.contains(&target1.replace(" ", "")) {
                    matched = true;
                }
                if !matched && self.char_id_2 > 0 {
                    let target2 = crate::core::logic::card_db::get_character_name(self.char_id_2);
                    if name.contains(&target2.replace(" ", "")) {
                        matched = true;
                    }
                }
                if !matched && actual_char_id_3 > 0 {
                    let target3 = crate::core::logic::card_db::get_character_name(actual_char_id_3);
                    if name.contains(&target3.replace(" ", "")) {
                        matched = true;
                    }
                }
                if !matched {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 5. Setsuna Filter (bit 59)
        if self.is_setsuna {
            let (s_flags, name) = if let Some(m) = db.get_member(cid) {
                (m.semantic_flags, Some(&m.name))
            } else if let Some(l) = db.get_live(cid) {
                (l.semantic_flags, Some(&l.name))
            } else {
                (0, None)
            };
            // Optimization: Use bit 8 (Setsuna) from semantic_flags
            if (s_flags & 0x100) == 0 {
                // Fallback for manual tests that didn't set flags but HAVE name
                if let Some(n) = name {
                    if !n.contains("KANON") {
                        return false;
                    }
                } else {
                    return false;
                }
            }
        }

        // 6. Value Threshold Filter - Cost for Members, Hearts for Live (bit 24 + bits 25-29)
        if self.value_enabled {
            let actual_val = if self.is_cost_type {
                // Cost mode: check member cost
                if let Some(m) = db.get_member(cid) {
                    m.cost as u8
                } else {
                    0
                }
            } else {
                // Heart mode: check total hearts of matching colors
                let h_slice = if let Some(h) = effective_hearts {
                    Some(h)
                } else if let Some(l) = db.get_live(cid) {
                    Some(&l.required_hearts)
                } else if let Some(m) = db.get_member(cid) {
                    Some(&m.hearts)
                } else {
                    None
                };

                if let Some(h) = h_slice {
                    if self.color_mask > 0 {
                        let mut sum = 0;
                        for i in 0..7 {
                            if (self.color_mask & (1 << i)) != 0 {
                                sum += h[i];
                            }
                        }
                        sum
                    } else {
                        h.iter().sum::<u8>()
                    }
                } else {
                    0
                }
            };

            let threshold = if self.compare_accumulated {
                ctx.v_accumulated as u8
            } else {
                self.value_threshold
            };

            if self.special_id == 5 && self.is_cost_type && self.compare_accumulated {
                let expected = (ctx.v_accumulated + self.value_threshold as i16).max(0) as u8;
                if actual_val != expected {
                    return false;
                }
            } else {
                if self.is_le {
                    if actual_val > threshold {
                        return false;
                    }
                } else {
                    if actual_val < threshold {
                        return false;
                    }
                }
            }
        }

        if self.keyword_energy {
            let Some((p_idx, _)) = checked_slot else {
                return false;
            };
            let player = &state.players[p_idx as usize];
            if self.group_enabled {
                if (player.activated_energy_group_mask & (1 << self.group_id)) == 0 {
                    return false;
                }
            } else if player.activated_energy_group_mask == 0 {
                return false;
            }
        }

        if self.keyword_member {
            let Some((p_idx, _)) = checked_slot else {
                return false;
            };
            let player = &state.players[p_idx as usize];
            if self.group_enabled {
                if (player.activated_member_group_mask & (1 << self.group_id)) == 0 {
                    return false;
                }
            } else if player.activated_member_group_mask == 0 {
                return false;
            }
        }

        // 7. Color Mask Filter (bits 32-38)
        if self.color_mask > 0 {
            let hearts = if let Some(h) = effective_hearts {
                Some(h)
            } else if let Some(m) = db.get_member(cid) {
                Some(&m.hearts)
            } else if let Some(l) = db.get_live(cid) {
                Some(&l.required_hearts)
            } else {
                None
            };

            if let Some(h) = hearts {
                let mut match_found = false;
                for i in 0..7 {
                    if (self.color_mask & (1 << i)) != 0 && h[i] > 0 {
                        match_found = true;
                        break;
                    }
                }
                if !match_found {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 8. Tapped Filter (bit 12)
        if self.is_tapped {
            if !is_tapped_override {
                return false;
            }
        }

        // 9. Blade Heart Filter (bits 13-14)
        if self.has_blade_heart || self.not_has_blade_heart {
            let has = if let Some(m) = db.get_member(cid) {
                m.blade_hearts.iter().any(|&h| h > 0)
            } else {
                false
            };
            if self.has_blade_heart && !has {
                return false;
            }
            if self.not_has_blade_heart && has {
                return false;
            }
        }

        // 10. Special ID Name Filter (bits 56-58)
        if self.special_id > 0 {
            let (s_flags, name) = if let Some(m) = db.get_member(cid) {
                (m.semantic_flags, Some(&m.name))
            } else if let Some(l) = db.get_live(cid) {
                (l.semantic_flags, Some(&l.name))
            } else {
                (0, None)
            };
            match self.special_id {
                1 => {
                    if (s_flags & 0x200) == 0 {
                        if let Some(n) = name {
                            if !n.contains("KANON") {
                                return false;
                            }
                        } else {
                            return false;
                        }
                    }
                }
                2 => {
                    if (s_flags & 0x400) != 0 {
                        return false;
                    }
                    if let Some(n) = name {
                        if n.contains("MY") {
                            return false;
                        }
                    }
                }
                3 => {
                    // special_id=3: NOT_SELF (skips card itself)
                    // IDENTITY FIX: Use slot index if available, fallback to card ID
                    if let Some((p_idx, s_idx)) = checked_slot {
                        if p_idx == ctx.player_id && s_idx == ctx.area_idx {
                            return false;
                        }
                    } else if cid == ctx.source_card_id {
                        return false;
                    }
                }
                5 => {
                    // Dynamic exact-cost comparison is handled in the value filter.
                }
                6 => {
                    if !ctx.selected_cards.contains(&cid) {
                        return false;
                    }
                }
                7 => {
                    if ctx.selected_cards.contains(&cid) {
                        return false;
                    }
                }
                _ => {}
            }
        }
        // 10.5 Unique Names Filter (bit 15) - Used as SAME_NAME_AS_REVEALED
        if self.special_id == 4 {
            let p_idx = ctx.player_id as usize;
            if state.players[p_idx].revealed_cards.is_empty() {
                return false;
            }

            let (char_mask, name) = if let Some(m) = db.get_member(cid) {
                (m.char_mask, Some(&m.name))
            } else if let Some(l) = db.get_live(cid) {
                (l.char_mask, Some(&l.name))
            } else {
                (0, None)
            };

            let mut matched = false;
            for &looked_cid in &state.players[p_idx].revealed_cards {
                // Optimization: Use char_mask intersection if both have masks
                if char_mask != 0 {
                    let looked_mask = if let Some(lm) = db.get_member(looked_cid) {
                        lm.char_mask
                    } else if let Some(ll) = db.get_live(looked_cid) {
                        ll.char_mask
                    } else {
                        0
                    };
                    if looked_mask != 0 && (char_mask & looked_mask) == 0 {
                        continue;
                    }
                }

                // Fallback to string contains
                let looked_name = if let Some(looked_m) = db.get_member(looked_cid) {
                    &looked_m.name
                } else if let Some(looked_l) = db.get_live(looked_cid) {
                    &looked_l.name
                } else {
                    ""
                };

                if let Some(n) = name {
                    if n.contains(looked_name) {
                        matched = true;
                        break;
                    }
                }
            }
            if !matched {
                return false;
            }
        }

        // 11. Zone Mask Filter (bits 53-55)
        if self.zone_mask > 0 {
            if !state.is_card_in_zone(ctx.player_id, self.target_player, cid, self.zone_mask) {
                if state.debug.debug_mode {
                    println!(
                        "[DEBUG_FILTER] Card {} fails Zone check. Mask: {}, Player: {}",
                        cid, self.zone_mask, self.target_player
                    );
                }
                return false;
            }
        }
        true
    }

    pub fn matches_with_logs(
        &self,
        db: &CardDatabase,
        state: &GameState,
        cid: i32,
        ctx: &AbilityContext,
        checked_slot: Option<(u8, i16)>,
        is_tapped_override: bool,
        effective_hearts: Option<&[u8; 7]>,
    ) -> bool {
        self.matches(
            state,
            db,
            cid,
            checked_slot,
            is_tapped_override,
            effective_hearts,
            ctx,
        )
    }

    pub fn from_attr(a: i64) -> Self {
        crate::core::logic::filter_attr_compat::card_filter_from_attr(a)
    }

    pub fn to_attr(&self) -> i64 {
        crate::core::logic::filter_attr_compat::card_filter_to_attr(self)
    }

    pub fn new() -> Self {
        Self {
            is_enabled: true,
            ..Self::default()
        }
    }

    pub fn with_target(mut self, player: u8) -> Self {
        self.target_player = player;
        self
    }

    pub fn with_member_type(mut self) -> Self {
        self.card_type = 1;
        self
    }

    pub fn with_live_type(mut self) -> Self {
        self.card_type = 2;
        self
    }

    pub fn with_group(mut self, gid: u8) -> Self {
        self.group_enabled = true;
        self.group_id = gid;
        self
    }

    pub fn with_unit(mut self, uid: u8) -> Self {
        self.unit_enabled = true;
        self.unit_id = uid;
        self
    }

    pub fn with_cost_ge(mut self, threshold: u8) -> Self {
        self.value_enabled = true;
        self.value_threshold = threshold;
        self.is_le = false;
        self.is_cost_type = true;
        self
    }

    pub fn with_cost_le(mut self, threshold: u8) -> Self {
        self.value_enabled = true;
        self.value_threshold = threshold;
        self.is_le = true;
        self.is_cost_type = true;
        self
    }

    pub fn with_heart_ge(mut self, threshold: u8, color_mask: u8) -> Self {
        self.value_enabled = true;
        self.value_threshold = threshold;
        self.is_le = false;
        self.is_cost_type = false;
        self.color_mask = color_mask;
        self
    }

    pub fn with_char(mut self, char_id: u8) -> Self {
        if self.char_id_1 == 0 {
            self.char_id_1 = char_id;
        } else {
            self.char_id_2 = char_id;
        }
        self
    }

    pub fn with_tapped(mut self) -> Self {
        self.is_tapped = true;
        self
    }

    pub fn with_blade_heart(mut self) -> Self {
        self.has_blade_heart = true;
        self
    }

    pub fn with_no_blade_heart(mut self) -> Self {
        self.not_has_blade_heart = true;
        self
    }

    pub fn with_unique_names(mut self) -> Self {
        self.unique_names = true;
        self
    }

    pub fn with_setsuna(mut self) -> Self {
        self.is_setsuna = true;
        self
    }

    pub fn with_special_id(mut self, sid: u8) -> Self {
        self.special_id = sid;
        self
    }

    pub fn with_zone_mask(mut self, mask: u8) -> Self {
        self.zone_mask = mask;
        self
    }
}

pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    crate::core::logic::filter_attr_compat::map_filter_string_to_attr(filter)
}

pub fn filter_attr_from_params(params: Option<&serde_json::Value>) -> Option<u64> {
    crate::core::logic::filter_attr_compat::filter_attr_from_params(params)
}
