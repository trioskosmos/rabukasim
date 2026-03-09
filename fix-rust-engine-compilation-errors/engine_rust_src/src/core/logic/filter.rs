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
use serde::{Deserialize, Serialize};
pub use crate::core::generated_constants::*;
pub use crate::core::generated_layout::*;
use crate::core::logic::constants::*;
// use crate::core::enums::Zone;
use crate::core::models::{GameState, AbilityContext};

// --- Filter Bitfield Constants (Now loaded from generated_constants.rs via constants.rs) ---
pub const FILTER_STATE_FLAGS_MASK: u64 = FILTER_TAPPED | FILTER_HAS_BLADE_HEART | FILTER_NOT_HAS_BLADE_HEART | FILTER_UNIQUE_NAMES;

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

        // 0. Target Player Filter (bits 0-1)
        if self.target_player > 0 && self.target_player < 4 {
             if let Some((p_idx, _)) = checked_slot {
                 let target_p = match self.target_player {
                     1 => ctx.player_id,
                     2 => 1 - ctx.player_id,
                     3 => 255, // Both (always pass later)
                     _ => ctx.player_id,
                 };
                 if target_p != 255 && p_idx != target_p {
                     if state.debug.debug_mode && cid == 4632 { println!("[DEBUG_MATCH] Fails Player check (Expected {}, Got {})", target_p, p_idx); }
                     return false;
                 }
             }
        }

        // 1. Card Type Filter (bits 2-3)
        if self.card_type > 0 {
            if self.card_type == 1 {
                // Member
                if !db.members.contains_key(&cid) {
                    if cid == 4632 { println!("[DEBUG_MATCH] Fails Type check (Member)"); }
                    return false;
                }
            } else if self.card_type == 2 {
                // Live
                if !db.lives.contains_key(&cid) {
                    if cid == 4632 { println!("[DEBUG_MATCH] Fails Type check (Live)"); }
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
                        if cid == 4632 { println!("[DEBUG_MATCH] Fails Group Special 101"); }
                        return false;
                    }
                } else if !m.groups.contains(&self.group_id) {
                    if cid == 4632 { println!("[DEBUG_MATCH] Fails Group check (Expected {}, card has {:?})", self.group_id, m.groups); }
                    return false;
                }
            } else if let Some(l) = db.get_live(cid) {
                if self.group_id == 101 {
                    if !l.groups.contains(&1) && !l.groups.contains(&11) {
                        if cid == 4632 { println!("[DEBUG_MATCH] Fails Live Group Special 101"); }
                        return false;
                    }
                } else if !l.groups.contains(&self.group_id) {
                    if cid == 4632 { println!("[DEBUG_MATCH] Fails Live Group check (Expected {})", self.group_id); }
                    return false;
                }
            } else {
                if cid == 4632 { println!("[DEBUG_MATCH] Fails Group check (Not found in DB)"); }
                return false;
            }
        }

        // 3. Unit Filter (bit 16 + bits 17-23)
        if self.unit_enabled {
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&self.unit_id) {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 4. Character ID Filter (bits 39-45)
        if self.char_id_1 > 0 {
            let name = if let Some(m) = db.get_member(cid) {
                &m.name
            } else if let Some(l) = db.get_live(cid) {
                &l.name
            } else {
                ""
            };

            let target_name = crate::core::logic::card_db::get_character_name(self.char_id_1);
            if !name
                .replace(" ", "")
                .contains(&target_name.replace(" ", ""))
            {
                // Check char_id_2 as alternate match
                if self.char_id_2 > 0 {
                    let target_name_2 =
                        crate::core::logic::card_db::get_character_name(self.char_id_2);
                    if !name
                        .replace(" ", "")
                        .contains(&target_name_2.replace(" ", ""))
                    {
                        // Check char_id_3 as alternate match
                        if self.char_id_3 > 0 {
                            let target_name_3 =
                                crate::core::logic::card_db::get_character_name(self.char_id_3);
                            if !name
                                .replace(" ", "")
                                .contains(&target_name_3.replace(" ", ""))
                            {
                                return false;
                            }
                        } else {
                            return false;
                        }
                    }
                } else {
                    return false;
                }
            }
        }

        // 5. Setsuna Filter (bit 59)
        if self.is_setsuna {
            let name = if let Some(m) = db.get_member(cid) {
                &m.name
            } else if let Some(l) = db.get_live(cid) {
                &l.name
            } else {
                ""
            };
            if !name.contains("せつ菜") {
                return false;
            }
        }

        // 6. Value Threshold Filter — Cost for Members, Hearts for Live (bit 24 + bits 25-29)
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
            let name = if let Some(m) = db.get_member(cid) {
                m.name.as_str()
            } else if let Some(l) = db.get_live(cid) {
                l.name.as_str()
            } else {
                ""
            };
            match self.special_id {
                1 => {
                    if !name.contains("澁谷かのん") {
                        return false;
                    }
                }
                2 => {
                    if name.contains("MY舞") {
                        return false;
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
                _ => {}
            }
        }

        // 11. Zone Mask Filter (bits 53-55)
        if self.zone_mask > 0 {
            if !state.is_card_in_zone(ctx.player_id, self.target_player, cid, self.zone_mask) {
                if state.debug.debug_mode {
                    println!("[DEBUG_FILTER] Card {} fails Zone check. Mask: {}, Player: {}", cid, self.zone_mask, self.target_player);
                }
                return false;
            }
        }

        if state.debug.debug_mode {
            let name = if let Some(m) = db.get_member(cid) { &m.name } else if let Some(l) = db.get_live(cid) { &l.name } else { "Unknown" };
            println!("[DEBUG_FILTER] Card {} ({}) MATCHED filter.", cid, name);
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
        self.matches(state, db, cid, checked_slot, is_tapped_override, effective_hearts, ctx)
    }

    pub fn from_attr(a: i64) -> Self {
        if a == 0 {
            return Self::default();
        }
        let a = a as u64;

        // Implementation Note: This unpacking follows the "A_STANDARD" layout (Revision 5).
        // Bits 0-1: Target Player (0=Self, 1=Active, 2=Opponent)
        // Bits 2-3: Card Type (1=Member, 2=Live)
        // Bits 32-38: Color Mask
        Self {
            is_enabled: true,
            target_player: ((a >> A_STANDARD_TARGET_PLAYER_SHIFT) & 0x3) as u8,
            card_type: ((a >> A_STANDARD_CARD_TYPE_SHIFT) & 0x3) as u8,
            group_enabled: ((a >> A_STANDARD_GROUP_ENABLED_SHIFT) & 0x1) != 0,
            group_id: ((a >> A_STANDARD_GROUP_ID_SHIFT) & 0x7F) as u8,
            is_tapped: ((a >> A_STANDARD_IS_TAPPED_SHIFT) & 0x1) != 0,
            has_blade_heart: ((a >> (A_STANDARD_IS_TAPPED_SHIFT + 1)) & 0x1) != 0,
            not_has_blade_heart: ((a >> (A_STANDARD_IS_TAPPED_SHIFT + 2)) & 0x1) != 0,
            unique_names: ((a >> (A_STANDARD_IS_TAPPED_SHIFT + 3)) & 0x1) != 0,
            unit_enabled: ((a >> A_STANDARD_UNIT_ENABLED_SHIFT) & 0x1) != 0,
            unit_id: ((a >> A_STANDARD_UNIT_ID_SHIFT) & 0x7F) as u8,
            value_enabled: ((a >> A_STANDARD_VALUE_ENABLED_SHIFT) & 0x1) != 0,
            value_threshold: ((a >> A_STANDARD_VALUE_THRESHOLD_SHIFT) & 0x1F) as u8,
            is_le: ((a >> A_STANDARD_IS_LE_SHIFT) & 0x1) != 0,
            is_cost_type: ((a >> A_STANDARD_IS_COST_TYPE_SHIFT) & 0x1) != 0,
            color_mask: ((a >> A_STANDARD_COLOR_MASK_SHIFT) & 0x7F) as u8,
            char_id_1: ((a >> A_STANDARD_CHAR_ID_1_SHIFT) & 0x7F) as u8,
            char_id_2: ((a >> A_STANDARD_CHAR_ID_2_SHIFT) & 0x7F) as u8,
            char_id_3: 0,
            zone_mask: ((a >> A_STANDARD_ZONE_MASK_SHIFT) & 0x7) as u8,
            special_id: ((a >> A_STANDARD_SPECIAL_ID_SHIFT) & 0x7) as u8,
            is_setsuna: ((a >> A_STANDARD_IS_SETSUNA_SHIFT) & 0x1) != 0,
            compare_accumulated: ((a >> A_STANDARD_COMPARE_ACCUMULATED_SHIFT) & 0x1) != 0,
            is_optional: ((a >> A_STANDARD_IS_OPTIONAL_SHIFT) & 0x1) != 0,
            keyword_energy: ((a >> A_STANDARD_KEYWORD_ENERGY_SHIFT) & 0x1) != 0,
            keyword_member: ((a >> A_STANDARD_KEYWORD_MEMBER_SHIFT) & 0x1) != 0,
        }
    }

    pub fn to_attr(&self) -> i64 {
        if !self.is_enabled {
            return 0;
        }

        let mut a: u64 = 0;
        a |= (self.target_player as u64 & 0x3) << A_STANDARD_TARGET_PLAYER_SHIFT;
        a |= (self.card_type as u64 & 0x3) << A_STANDARD_CARD_TYPE_SHIFT;
        if self.group_enabled {
            a |= 1u64 << A_STANDARD_GROUP_ENABLED_SHIFT;
            a |= (self.group_id as u64 & 0x7F) << A_STANDARD_GROUP_ID_SHIFT;
        }
        if self.is_tapped { a |= 1u64 << A_STANDARD_IS_TAPPED_SHIFT; }
        if self.has_blade_heart { a |= 1u64 << (A_STANDARD_IS_TAPPED_SHIFT+1); }
        if self.not_has_blade_heart { a |= 1u64 << (A_STANDARD_IS_TAPPED_SHIFT+2); }
        if self.unique_names { a |= 1u64 << (A_STANDARD_IS_TAPPED_SHIFT+3); }
        if self.unit_enabled {
            a |= 1u64 << A_STANDARD_UNIT_ENABLED_SHIFT;
            a |= (self.unit_id as u64 & 0x7F) << A_STANDARD_UNIT_ID_SHIFT;
        }
        if self.value_enabled {
            a |= 1u64 << A_STANDARD_VALUE_ENABLED_SHIFT;
            a |= (self.value_threshold as u64 & 0x1F) << A_STANDARD_VALUE_THRESHOLD_SHIFT;
            if self.is_le { a |= 1u64 << A_STANDARD_IS_LE_SHIFT; }
            if self.is_cost_type { a |= 1u64 << A_STANDARD_IS_COST_TYPE_SHIFT; }
        }
        a |= (self.color_mask as u64 & 0x7F) << A_STANDARD_COLOR_MASK_SHIFT;
        a |= (self.char_id_1 as u64 & 0x7F) << A_STANDARD_CHAR_ID_1_SHIFT;
        a |= (self.char_id_2 as u64 & 0x7F) << A_STANDARD_CHAR_ID_2_SHIFT;
        a |= (self.zone_mask as u64 & 0x7) << A_STANDARD_ZONE_MASK_SHIFT;
        a |= (self.special_id as u64 & 0x7) << A_STANDARD_SPECIAL_ID_SHIFT;
        if self.is_setsuna { a |= 1u64 << A_STANDARD_IS_SETSUNA_SHIFT; }
        if self.compare_accumulated { a |= 1u64 << A_STANDARD_COMPARE_ACCUMULATED_SHIFT; }
        if self.is_optional { a |= 1u64 << A_STANDARD_IS_OPTIONAL_SHIFT; }
        if self.keyword_energy { a |= 1u64 << A_STANDARD_KEYWORD_ENERGY_SHIFT; }
        if self.keyword_member { a |= 1u64 << A_STANDARD_KEYWORD_MEMBER_SHIFT; }

        a as i64
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
    let mut attr: u64 = 0;
    for part in filter.split(',') {
        let part_trimmed = part.trim();
        let part = part_trimmed.to_uppercase();
        if part.is_empty() {
            continue;
        }

        if part_trimmed.contains("NAME_IN") && part_trimmed.contains("澁谷かのん") {
            attr |= 1u64 << FILTER_SPECIAL_SHIFT;
            continue;
        }
        if part_trimmed.contains("NOT_NAME=MY舞") {
            attr |= 2u64 << FILTER_SPECIAL_SHIFT;
            continue;
        }

        if part.starts_with("COST") {
            let val_str = if part.contains('=') {
                part.split('=').last()
            } else {
                part.split('_').last()
            };
            if let Some(s) = val_str {
                if let Ok(threshold) = s.parse::<i32>() {
                    attr |= (1u64 << A_STANDARD_VALUE_ENABLED_SHIFT) | ((threshold as u64) << A_STANDARD_VALUE_THRESHOLD_SHIFT);
                    if part.contains("_LE") {
                        attr |= (1u64 << A_STANDARD_IS_LE_SHIFT);
                    }
                    attr |= (1u64 << A_STANDARD_IS_COST_TYPE_SHIFT); // Set Cost Type flag
                }
            }
        } else if part.starts_with("GROUP_ID=") || part.starts_with("GROUP_ID_") {
            let gid_str = if part.contains('=') {
                part.split('=').last()
            } else {
                part.split('_').last()
            };
            if let Some(s) = gid_str {
                if let Ok(gid) = s.parse::<i32>() {
                    attr |= crate::core::logic::constants::FILTER_GROUP_ENABLE | ((gid as u64) << A_STANDARD_GROUP_ID_SHIFT);
                }
            }
        } else if part.starts_with("UNIT_") {
            let unit_name = part.replace("UNIT_", "").replace("_ONLY", "");
            let unit_id: i32 = match unit_name.as_str() {
                "PRINTEMPS" => 0,
                "LILY_WHITE" | "LILYWHITE" => 1,
                "BIBI" => 2,
                "CYARON" | "CYARON!" => 3,
                "AZALEA" => 4,
                "GUILTY_KISS" | "GUILTYKISS" => 5,
                "DIVER_DIVA" | "DIVERDIVA" => 6,
                "A_ZU_NA" | "AZUNA" => 7,
                "QU4RTZ" => 8,
                "R3BIRTH" => 9,
                "CATCHU" | "CATCHU!" => 10,
                "KALEIDOSCORE" => 11,
                "5YNCRI5E" | "SYNCRISE" => 12,
                "CERISE_BOUQUET" | "CERISE" => 13,
                "DOLLCHESTRA" => 14,
                "MIRA_CRA_PARK" | "MIRACRA" | "MIRACRA_PARK" => 15,
                "EDEL_NOTE" | "EDELNOTE" => 16,
                _ => -1,
            };
            if unit_id >= 0 {
                attr |= crate::core::logic::constants::FILTER_UNIT_ENABLE | ((unit_id as u64) << FILTER_UNIT_SHIFT);
            }
        } else if part == "TAPPED" {
            attr |= FILTER_TAPPED;
        } else if part == "HAS_BLADE_HEART" {
            attr |= FILTER_HAS_BLADE_HEART;
        } else if part == "NOT_HAS_BLADE_HEART" {
            attr |= FILTER_NOT_HAS_BLADE_HEART;
        } else if part == "TYPE_MEMBER" {
            attr |= FILTER_TYPE_MEMBER;
        } else if part == "TYPE_LIVE" {
            attr |= FILTER_TYPE_LIVE;
        } else if part == "AQOURS" {
            attr |= FILTER_GROUP_ENABLE | (1u64 << A_STANDARD_GROUP_ID_SHIFT);
        } else if part == "M'S" || part == "μ'S" || part == "U'S" || part == "MUSE" {
            attr |= FILTER_GROUP_ENABLE | (0u64 << A_STANDARD_GROUP_ID_SHIFT);
        } else if part == "UNIQUE_NAMES=TRUE"
            || part == "UNIQUE_NAMES"
            || part == "SAME_UNIQUE_NAMES"
        {
            attr |= FILTER_UNIQUE_NAMES;
        } else if part == "SMILE" || part == "PINK" || part == "COLOR_0" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 0);
        } else if part == "PURE" || part == "GREEN" || part == "COLOR_3" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 3);
        } else if part == "COOL" || part == "BLUE" || part == "COLOR_4" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 4);
        } else if part == "RED" || part == "COLOR_1" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 1);
        } else if part == "YELLOW" || part == "COLOR_2" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 2);
        } else if part == "PURPLE" || part == "COLOR_5" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 5);
        } else if part == "ANY" || part == "COLOR_7" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 6); // R5 uses bit 6 for ANY/ALL
        } else if part.starts_with("BLADE_LE") {
            let val_str = part.replace("BLADE_LE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << A_STANDARD_VALUE_THRESHOLD_SHIFT);
                attr |= (1u64 << A_STANDARD_IS_LE_SHIFT);
            }
        } else if part.starts_with("BLADE_GE") {
            let val_str = part.replace("BLADE_GE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << A_STANDARD_VALUE_THRESHOLD_SHIFT);
            }
        } else if part == "COST_LE_REVEALED" {
            attr |= FILTER_COST_ENABLE | (1u64 << A_STANDARD_VALUE_THRESHOLD_SHIFT);
            attr |= (1u64 << A_STANDARD_IS_LE_SHIFT);
            attr |= FILTER_REVEALED_CONTEXT;
            attr |= FILTER_COST_TYPE_FLAG;
        } else if part == "HEART_PINK" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 0);
        } else if part == "HEART_BLUE" {
            attr |= 1u64 << (A_STANDARD_COLOR_MASK_SHIFT + 4);
        } else if part == "HASUNOSORA" {
            attr |= FILTER_GROUP_ENABLE | (4u64 << A_STANDARD_GROUP_ID_SHIFT);
        } else if part == "LIELLA" {
            attr |= FILTER_GROUP_ENABLE | (3u64 << A_STANDARD_GROUP_ID_SHIFT);
        } else if part == "NIJIGASAKI" || part == "NIJIGAKU" {
            attr |= FILTER_GROUP_ENABLE | (2u64 << A_STANDARD_GROUP_ID_SHIFT);
        }
    }
    attr
}
