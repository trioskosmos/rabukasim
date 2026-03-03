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
//! Bit 60:     Dynamic Value flag
//! Bit 61:     Optional flag
//! Bit 62:     Keyword: Activated Energy
//! Bit 63:     Keyword: Activated Member

use super::CardDatabase;
use serde::{Deserialize, Serialize};

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
pub const FILTER_REVEALED_CONTEXT: u64 = 1u64 << 43;
pub const FILTER_BLADE_FILTER_FLAG: u64 = 0x02000000;

/// A structured representation of the 64-bit filter attribute
/// Synchronized with ability.py _pack_filter_attr layout (Revision 5).
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
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
    // Bits 13-14
    pub has_blade_heart: i8, // 1=yes, -1=no, 0=don't care
    // Bit 15
    pub unique_names: bool,
    // Bit 16 + Bits 17-23
    pub unit_enabled: bool,
    pub unit_id: u8,
    // Bit 24 + Bits 25-29 + Bit 30 + Bit 31
    pub value_enabled: bool,
    pub value_threshold: u8,
    pub is_le: bool,
    pub is_cost_type: bool, // true=Cost, false=Heart
    // Bits 32-38
    pub color_mask: u8,
    // Bits 39-45, 46-52
    pub char_id_1: u8,
    pub char_id_2: u8,
    // Bits 53-55
    pub zone_mask: u8,
    // Bits 56-58
    pub special_id: u8,
    // Bit 59
    pub is_setsuna: bool,
}

impl CardFilter {
    pub fn matches(
        &self,
        db: &CardDatabase,
        cid: i32,
        is_tapped_override: bool,
        effective_hearts: Option<&[u8; 7]>,
    ) -> bool {
        if !self.is_enabled {
            return true;
        }
        if cid == -1 {
            return false;
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
                        return false;
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
                    // If color mask is 0, sum all hearts (TOTAL_HEARTS). 
                    // Otherwise, sum only the masked colors (e.g., HAS_HEART_02_X3).
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

            if self.is_le {
                if actual_val > self.value_threshold {
                    return false;
                }
            } else {
                if actual_val < self.value_threshold {
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
        if self.has_blade_heart != 0 {
            let has = if let Some(m) = db.get_member(cid) {
                m.blade_hearts.iter().any(|&h| h > 0)
            } else {
                false
            };
            if self.has_blade_heart > 0 && !has {
                return false;
            }
            if self.has_blade_heart < 0 && has {
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

        true
    }

    pub fn from_attr(attr: i64) -> Self {
        if attr == 0 {
            return Self::default();
        }

        let a = attr as u64;

        // Any non-zero attribute means filtering is active
        let mut filter = Self {
            is_enabled: true,
            ..Self::default()
        };

        // Bits 0-1: Target Player
        filter.target_player = (a & 0x03) as u8;

        // Bits 2-3: Card Type (1=Member, 2=Live)
        filter.card_type = ((a >> 2) & 0x03) as u8;

        // Bit 4: Group Enable
        filter.group_enabled = (a & 0x10) != 0;
        // Bits 5-11: Group ID
        filter.group_id = ((a >> 5) & 0x7F) as u8;

        // Bit 12: Tapped
        filter.is_tapped = (a & (1 << 12)) != 0;

        // Bit 13: Has Blade Heart
        // Bit 14: NOT Has Blade Heart
        if (a & (1 << 13)) != 0 {
            filter.has_blade_heart = 1;
        } else if (a & (1 << 14)) != 0 {
            filter.has_blade_heart = -1;
        }

        // Bit 15: Unique Names
        filter.unique_names = (a & (1 << 15)) != 0;

        // Bit 16: Unit Enable
        filter.unit_enabled = (a & 0x10000) != 0;
        // Bits 17-23: Unit ID
        filter.unit_id = ((a >> 17) & 0x7F) as u8;

        // Bit 24: Value Enable / Cost Enable
        filter.value_enabled = (a & (1 << 24)) != 0;
        // Bits 25-29: Value Threshold
        filter.value_threshold = ((a >> 25) & 0x1F) as u8;
        // Bit 30: Cost Mode (0=GE, 1=LE)
        filter.is_le = (a & (1 << 30)) != 0;
        // Bit 31: Cost Type (1=Cost, 0=Heart)
        filter.is_cost_type = (a & (1u64 << 31)) != 0;

        // Bits 32-38: Color Mask
        filter.color_mask = ((a >> 32) & 0x7F) as u8;

        // Bits 39-45: Character ID #1
        filter.char_id_1 = ((a >> 39) & 0x7F) as u8;

        // Bits 46-52: Character ID #2
        filter.char_id_2 = ((a >> 46) & 0x7F) as u8;

        // Bits 53-55: Zone Mask
        filter.zone_mask = ((a >> 53) & 0x07) as u8;

        // Bits 56-58: Special ID
        filter.special_id = ((a >> 56) & 0x07) as u8;

        // Bit 59: Setsuna
        filter.is_setsuna = (a & (1u64 << 59)) != 0;

        filter
    }

    pub fn to_attr(&self) -> i64 {
        if !self.is_enabled {
            return 0;
        }

        let mut a: u64 = 0;

        // Bits 0-1: Target Player
        a |= (self.target_player & 0x03) as u64;

        // Bits 2-3: Card Type
        a |= ((self.card_type & 0x03) as u64) << 2;

        // Bit 4 + Bits 5-11: Group
        if self.group_enabled {
            a |= 0x10;
            a |= ((self.group_id & 0x7F) as u64) << 5;
        }

        // Bit 12: Tapped
        if self.is_tapped {
            a |= 1 << 12;
        }

        // Bits 13-14: Blade Heart
        if self.has_blade_heart > 0 {
            a |= 1 << 13;
        }
        if self.has_blade_heart < 0 {
            a |= 1 << 14;
        }

        // Bit 15: Unique Names
        if self.unique_names {
            a |= 1 << 15;
        }

        // Bit 16 + Bits 17-23: Unit
        if self.unit_enabled {
            a |= 0x10000;
            a |= ((self.unit_id & 0x7F) as u64) << 17;
        }

        // Bit 24 + Bits 25-29 + Bit 30 + Bit 31: Value/Cost
        if self.value_enabled {
            a |= 1 << 24;
            a |= ((self.value_threshold & 0x1F) as u64) << 25;
            if self.is_le {
                a |= 1 << 30;
            }
            if self.is_cost_type {
                a |= 1u64 << 31;
            }
        }

        // Bits 32-38: Color Mask
        a |= ((self.color_mask & 0x7F) as u64) << 32;

        // Bits 39-45: Character ID #1
        a |= ((self.char_id_1 & 0x7F) as u64) << 39;

        // Bits 46-52: Character ID #2
        a |= ((self.char_id_2 & 0x7F) as u64) << 46;

        // Bits 53-55: Zone Mask
        a |= ((self.zone_mask & 0x07) as u64) << 53;

        // Bits 56-58: Special ID
        a |= ((self.special_id & 0x07) as u64) << 56;

        // Bit 59: Setsuna
        if self.is_setsuna {
            a |= 1u64 << 59;
        }

        a as i64
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
            has_blade_heart: -1,
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
        };

        let attr = filter.to_attr();
        let parsed = CardFilter::from_attr(attr);
        assert_eq!(filter, parsed);
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
