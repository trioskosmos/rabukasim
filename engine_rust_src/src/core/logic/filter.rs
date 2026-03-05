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
use crate::core::generated_layout::*;
use crate::core::logic::constants::*;
// use crate::core::enums::Zone;

// --- Filter Bitfield Constants (Revision 5) ---
pub const FILTER_TYPE_MEMBER: u64 = 0x01 << 2;
pub const FILTER_TYPE_LIVE: u64 = 0x02 << 2;
pub const FILTER_GROUP_FLAG: u64 = 0x10;
pub const FILTER_GROUP_SHIFT: u64 = 5;
pub const FILTER_TAPPED: u64 = 1 << 12;
pub const FILTER_HAS_BLADE_HEART: u64 = 1 << 13;
pub const FILTER_NOT_HAS_BLADE_HEART: u64 = 1 << 14;
pub const FILTER_UNIQUE_NAMES: u64 = 1 << 15;
pub const FILTER_UNIT_FLAG: u64 = 0x10000;
pub const FILTER_UNIT_SHIFT: u64 = 17;
pub const FILTER_COST_FLAG: u64 = 1 << 24;
pub const FILTER_VALUE_SHIFT: u64 = 25;
pub const FILTER_IS_LE: u64 = 1 << 30;
pub const FILTER_COST_TYPE_FLAG: u64 = 1u64 << 31;
pub const FILTER_COLOR_SHIFT: u64 = 32;
pub const FILTER_SPECIAL_SHIFT: u64 = 56;

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
        if ctx.player_id == 0 && (cid == 124 || cid == 121) {
             println!("[DEBUG_FILTER] Checking CID: {}, Filter: {:?}", cid, self);
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
                if !m.groups.contains(&self.group_id) {
                    return false;
                }
            } else if let Some(l) = db.get_live(cid) {
                if !l.groups.contains(&self.group_id) {
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
            
            if cid == 100 || cid == 101 || self.char_id_1 == 41 || self.char_id_1 == 42 {
                println!("[DEBUG_FILTER] CID={} Name='{}' TargetID={} TargetName='{}'", cid, name, self.char_id_1, target_name);
            }

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
                            if cid == 100 || cid == 101 || self.char_id_1 == 41 || self.char_id_1 == 42 {
                                println!("[DEBUG_FILTER]   -> Result: FALSE (char_id_1 match failed, no char_id_2/3)");
                            }
                            return false;
                        }
                    }
                } else {
                    if cid == 100 || cid == 101 || self.char_id_1 == 41 || self.char_id_1 == 42 {
                        println!("[DEBUG_FILTER]   -> Result: FALSE (char_id_1 match failed)");
                    }
                    return false;
                }
            }
            if cid == 100 || cid == 101 || self.char_id_1 == 41 || self.char_id_1 == 42 {
                println!("[DEBUG_FILTER]   -> Result: TRUE");
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
                    // println!("[DEBUG_FILTER] Comparing Hearts: mask={:b}, threshold={}, values={:?}", self.color_mask, self.value_threshold, h);
                    // If color mask is 0, sum all hearts (TOTAL_HEARTS). 
                    // Otherwise, sum only the masked colors (e.g., HAS_HEART_02_X3).
                    if self.color_mask > 0 {
                        let mut sum = 0;
                        for i in 0..7 {
                            if (self.color_mask & (1 << i)) != 0 {
                                sum += h[i];
                            }
                        }
                        // println!("[DEBUG_FILTER] Mask Sum: {} vs threshold {}", sum, self.value_threshold);
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

            if self.compare_accumulated && state.debug.debug_mode {
                println!("[DBG_FILTER] CID={} Actual={} vs Budget={} (LE={})", cid, actual_val, threshold, self.is_le);
            }

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
        // These are hardcoded name checks matching map_filter_string_to_attr:
        //   special_id=1: NAME_IN=澁谷かのん (カノン/Kanon)
        //   special_id=2: NOT_NAME=MY舞 (excludes cards with MY舞 in name)
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
                _ => {}
            }
        }

        // 11. Zone Mask Filter (bits 53-55)
        // 4=STAGE, 6=HAND, 7=DISCARD
        if self.zone_mask > 0 {
            if !state.is_card_in_zone(ctx.player_id, self.target_player, cid, self.zone_mask) {
                return false;
            }
        }

        true
    }

    pub fn from_attr(attr: i64) -> Self {
        if attr == 0 {
            return Self::default();
        }

        let a = attr as u64;

        Self {
            is_enabled: true,
            target_player: ((a >> A_STANDARD_TARGET_PLAYER_SHIFT) & A_STANDARD_TARGET_PLAYER_MASK) as u8,
            card_type: ((a >> A_STANDARD_CARD_TYPE_SHIFT) & A_STANDARD_CARD_TYPE_MASK) as u8,
            group_enabled: ((a >> A_STANDARD_GROUP_ENABLED_SHIFT) & A_STANDARD_GROUP_ENABLED_MASK) != 0,
            group_id: ((a >> A_STANDARD_GROUP_ID_SHIFT) & A_STANDARD_GROUP_ID_MASK) as u8,
            is_tapped: ((a >> A_STANDARD_IS_TAPPED_SHIFT) & A_STANDARD_IS_TAPPED_MASK) != 0,
            has_blade_heart: ((a >> A_STANDARD_HAS_BLADE_HEART_SHIFT) & A_STANDARD_HAS_BLADE_HEART_MASK) != 0,
            not_has_blade_heart: ((a >> A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT) & A_STANDARD_NOT_HAS_BLADE_HEART_MASK) != 0,
            unique_names: ((a >> A_STANDARD_UNIQUE_NAMES_SHIFT) & A_STANDARD_UNIQUE_NAMES_MASK) != 0,
            unit_enabled: ((a >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK) != 0,
            unit_id: ((a >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8,
            value_enabled: ((a >> A_STANDARD_VALUE_ENABLED_SHIFT) & A_STANDARD_VALUE_ENABLED_MASK) != 0,
            value_threshold: ((a >> A_STANDARD_VALUE_THRESHOLD_SHIFT) & A_STANDARD_VALUE_THRESHOLD_MASK) as u8,
            is_le: ((a >> A_STANDARD_IS_LE_SHIFT) & A_STANDARD_IS_LE_MASK) != 0,
            is_cost_type: ((a >> A_STANDARD_IS_COST_TYPE_SHIFT) & A_STANDARD_IS_COST_TYPE_MASK) != 0,
            color_mask: ((a >> A_STANDARD_COLOR_MASK_SHIFT) & A_STANDARD_COLOR_MASK_MASK) as u8,
            char_id_1: ((a >> A_STANDARD_CHAR_ID_1_SHIFT) & A_STANDARD_CHAR_ID_1_MASK) as u8,
            char_id_2: ((a >> A_STANDARD_CHAR_ID_2_SHIFT) & A_STANDARD_CHAR_ID_2_MASK) as u8,
            char_id_3: 0,
            zone_mask: ((a >> A_STANDARD_ZONE_MASK_SHIFT) & A_STANDARD_ZONE_MASK_MASK) as u8,
            special_id: ((a >> A_STANDARD_SPECIAL_ID_SHIFT) & A_STANDARD_SPECIAL_ID_MASK) as u8,
            is_setsuna: ((a >> A_STANDARD_IS_SETSUNA_SHIFT) & A_STANDARD_IS_SETSUNA_MASK) != 0,
            compare_accumulated: ((a >> A_STANDARD_COMPARE_ACCUMULATED_SHIFT) & A_STANDARD_COMPARE_ACCUMULATED_MASK) != 0,
            is_optional: ((a >> A_STANDARD_IS_OPTIONAL_SHIFT) & A_STANDARD_IS_OPTIONAL_MASK) != 0,
            keyword_energy: ((a >> A_STANDARD_KEYWORD_ENERGY_SHIFT) & A_STANDARD_KEYWORD_ENERGY_MASK) != 0,
            keyword_member: ((a >> A_STANDARD_KEYWORD_MEMBER_SHIFT) & A_STANDARD_KEYWORD_MEMBER_MASK) != 0,
        }
    }

    pub fn to_attr(&self) -> i64 {
        if !self.is_enabled {
            return 0;
        }

        let mut a: u64 = 0;
        a |= (self.target_player as u64 & A_STANDARD_TARGET_PLAYER_MASK) << A_STANDARD_TARGET_PLAYER_SHIFT;
        a |= (self.card_type as u64 & A_STANDARD_CARD_TYPE_MASK) << A_STANDARD_CARD_TYPE_SHIFT;
        if self.group_enabled {
            a |= (1 & A_STANDARD_GROUP_ENABLED_MASK) << A_STANDARD_GROUP_ENABLED_SHIFT;
            a |= (self.group_id as u64 & A_STANDARD_GROUP_ID_MASK) << A_STANDARD_GROUP_ID_SHIFT;
        }
        if self.is_tapped {
            a |= (1 & A_STANDARD_IS_TAPPED_MASK) << A_STANDARD_IS_TAPPED_SHIFT;
        }
        if self.has_blade_heart {
            a |= (1 & A_STANDARD_HAS_BLADE_HEART_MASK) << A_STANDARD_HAS_BLADE_HEART_SHIFT;
        }
        if self.not_has_blade_heart {
            a |= (1 & A_STANDARD_NOT_HAS_BLADE_HEART_MASK) << A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT;
        }
        if self.unique_names {
            a |= (1 & A_STANDARD_UNIQUE_NAMES_MASK) << A_STANDARD_UNIQUE_NAMES_SHIFT;
        }
        if self.unit_enabled {
            a |= (1 & A_STANDARD_UNIT_ENABLED_MASK) << A_STANDARD_UNIT_ENABLED_SHIFT;
            a |= (self.unit_id as u64 & A_STANDARD_UNIT_ID_MASK) << A_STANDARD_UNIT_ID_SHIFT;
        }
        if self.value_enabled {
            a |= (1 & A_STANDARD_VALUE_ENABLED_MASK) << A_STANDARD_VALUE_ENABLED_SHIFT;
            a |= (self.value_threshold as u64 & A_STANDARD_VALUE_THRESHOLD_MASK) << A_STANDARD_VALUE_THRESHOLD_SHIFT;
            if self.is_le {
                a |= (1 & A_STANDARD_IS_LE_MASK) << A_STANDARD_IS_LE_SHIFT;
            }
            if self.is_cost_type {
                a |= (1 & A_STANDARD_IS_COST_TYPE_MASK) << A_STANDARD_IS_COST_TYPE_SHIFT;
            }
        }
        a |= (self.color_mask as u64 & A_STANDARD_COLOR_MASK_MASK) << A_STANDARD_COLOR_MASK_SHIFT;
        a |= (self.char_id_1 as u64 & A_STANDARD_CHAR_ID_1_MASK) << A_STANDARD_CHAR_ID_1_SHIFT;
        a |= (self.char_id_2 as u64 & A_STANDARD_CHAR_ID_2_MASK) << A_STANDARD_CHAR_ID_2_SHIFT;
        a |= (self.zone_mask as u64 & A_STANDARD_ZONE_MASK_MASK) << A_STANDARD_ZONE_MASK_SHIFT;
        a |= (self.special_id as u64 & A_STANDARD_SPECIAL_ID_MASK) << A_STANDARD_SPECIAL_ID_SHIFT;
        if self.is_setsuna {
            a |= (1 & A_STANDARD_IS_SETSUNA_MASK) << A_STANDARD_IS_SETSUNA_SHIFT;
        }
        if self.compare_accumulated {
            a |= (1 & A_STANDARD_COMPARE_ACCUMULATED_MASK) << A_STANDARD_COMPARE_ACCUMULATED_SHIFT;
        }
        if self.is_optional {
            a |= (1 & A_STANDARD_IS_OPTIONAL_MASK) << A_STANDARD_IS_OPTIONAL_SHIFT;
        }
        if self.keyword_energy {
            a |= (1 & A_STANDARD_KEYWORD_ENERGY_MASK) << A_STANDARD_KEYWORD_ENERGY_SHIFT;
        }
        if self.keyword_member {
            a |= (1 & A_STANDARD_KEYWORD_MEMBER_MASK) << A_STANDARD_KEYWORD_MEMBER_SHIFT;
        }

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

/// Parses a filter string (e.g., "GROUP_ID=3, COST_LE=2") into a 64-bit attribute bitmask.
/// This is the Rust equivalent of the Python compiler's _pack_filter_attr logic for strings.
pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let mut attr: u64 = 0;
    for part in filter.split(',') {
        let part_trimmed = part.trim();
        let part = part_trimmed.to_uppercase();
        if part.is_empty() {
            continue;
        }

        // Check for NAME_IN with Japanese characters before uppercase conversion
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
                    attr |= FILTER_COST_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
                    if part.contains("_LE") {
                        attr |= FILTER_IS_LE;
                    }
                    attr |= FILTER_COST_TYPE_FLAG; // Explicitly cost type
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
                    attr |= FILTER_GROUP_FLAG | ((gid as u64) << FILTER_GROUP_SHIFT);
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
                attr |= FILTER_UNIT_FLAG | ((unit_id as u64) << FILTER_UNIT_SHIFT);
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
            attr |= FILTER_GROUP_FLAG | (1 << FILTER_GROUP_SHIFT);
        } else if part == "M'S" || part == "μ'S" || part == "U'S" || part == "MUSE" {
            attr |= FILTER_GROUP_FLAG | (0 << FILTER_GROUP_SHIFT);
        } else if part == "UNIQUE_NAMES=TRUE"
            || part == "UNIQUE_NAMES"
            || part == "SAME_UNIQUE_NAMES"
        {
            attr |= FILTER_UNIQUE_NAMES;
        } else if part == "SMILE" || part == "PINK" || part == "COLOR_0" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 0);
        } else if part == "PURE" || part == "GREEN" || part == "COLOR_1" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 1);
        } else if part == "COOL" || part == "BLUE" || part == "COLOR_2" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 2);
        } else if part == "ALL_STARS_RED" || part == "RED" || part == "COLOR_3" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 3);
        } else if part == "ALL_STARS_YELLOW" || part == "YELLOW" || part == "COLOR_4" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 4);
        } else if part == "ALL_STARS_BLUE" || part == "LTBLUE" || part == "COLOR_5" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 5);
        } else if part == "ALL_STARS_PURPLE" || part == "PURPLE" || part == "COLOR_6" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 6);
        } else if part.starts_with("BLADE_LE") {
            let val_str = part.replace("BLADE_LE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
                attr |= FILTER_IS_LE;
            }
        } else if part.starts_with("BLADE_GE") {
            let val_str = part.replace("BLADE_GE", "").replace("_", "");
            if let Ok(threshold) = val_str.parse::<i32>() {
                attr |= FILTER_BLADE_FILTER_FLAG | ((threshold as u64) << FILTER_VALUE_SHIFT);
            }
        } else if part == "COST_LE_REVEALED" {
            attr |= FILTER_COST_FLAG | (1u64 << FILTER_VALUE_SHIFT);
            attr |= FILTER_IS_LE;
            attr |= FILTER_REVEALED_CONTEXT;
            attr |= FILTER_COST_TYPE_FLAG;
        } else if part == "HEART_PINK" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 0);
        } else if part == "HEART_BLUE" {
            attr |= 1u64 << (FILTER_COLOR_SHIFT + 2);
        } else if part == "HASUNOSORA" {
            attr |= FILTER_GROUP_FLAG | (4 << FILTER_GROUP_SHIFT);
        } else if part == "LIELLA" {
            attr |= FILTER_GROUP_FLAG | (3 << FILTER_GROUP_SHIFT);
        } else if part == "NIJIGASAKI" || part == "NIJIGAKU" {
            attr |= FILTER_GROUP_FLAG | (2 << FILTER_GROUP_SHIFT);
        }
    }
    attr
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_filter_roundtrip() {
        // Test basic Member + Cost LE filter
        let filter = CardFilter {
            is_enabled: true,
            target_player: 1,
            card_type: 1, // Member
            value_enabled: true,
            value_threshold: 5,
            is_le: true,
            is_cost_type: true,
            ..Default::default()
        };

        let attr = filter.to_attr();
        let parsed = CardFilter::from_attr(attr);
        assert_eq!(filter, parsed);
    }

    #[test]
    fn test_filter_roundtrip_group() {
        // Test Group filter (Liella = 3)
        let filter = CardFilter {
            is_enabled: true,
            target_player: 1,
            group_enabled: true,
            group_id: 3,
            ..Default::default()
        };

        let attr = filter.to_attr();
        let parsed = CardFilter::from_attr(attr);
        assert_eq!(filter, parsed);

        // Verify bit layout matches Python: bit 4 set + (3 << 5)
        assert_eq!(attr & 0x10, 0x10); // Group Enable
        assert_eq!((attr >> 5) & 0x7F, 3); // Group ID = 3
    }

    #[test]
    fn test_filter_roundtrip_full() {
        // Test all fields
        let filter = CardFilter {
            is_enabled: true,
            target_player: 2,
            card_type: 2,
            group_enabled: true,
            group_id: 4,
            is_tapped: true,
            has_blade_heart: false,
            not_has_blade_heart: true,
            unique_names: true,
            unit_enabled: true,
            unit_id: 5,
            value_enabled: true,
            value_threshold: 10,
            is_le: true,
            is_cost_type: true,
            color_mask: 0x15,
            char_id_1: 7,
            char_id_2: 12,
            zone_mask: 3,
            special_id: 2,
            is_setsuna: true,
            char_id_3: 0,
            compare_accumulated: false,
            is_optional: false,
            keyword_energy: false,
            keyword_member: false,
        };

        let _state = crate::core::logic::GameState::default();
        let _ctx = crate::core::logic::AbilityContext::default();
        let attr = filter.to_attr();
        let parsed = CardFilter::from_attr(attr);
        assert_eq!(filter, parsed);
        // Note: Actual matching would require a real DB, but we test roundtrip here.
    }

    #[test]
    fn test_filter_from_python_attr() {
        // Simulate what Python would produce for:
        //   target=Self, type=Member, group=Liella(3), cost_min=5
        // Python: attr = 0x01 | (0x01 << 2) | 0x10 | (3 << 5) | (1 << 24) | (5 << 25) | (1 << 31)
        let python_attr: i64 =
            0x01 | (0x01 << 2) | 0x10 | (3 << 5) | (1 << 24) | (5 << 25) | (1i64 << 31);
        let filter = CardFilter::from_attr(python_attr);

        assert!(filter.is_enabled);
        assert_eq!(filter.target_player, 1); // Self
        assert_eq!(filter.card_type, 1); // Member
        assert!(filter.group_enabled);
        assert_eq!(filter.group_id, 3); // Liella
        assert!(filter.value_enabled);
        assert_eq!(filter.value_threshold, 5);
        assert!(!filter.is_le); // GE (cost_min)
        assert!(filter.is_cost_type); // Cost type
    }
}
