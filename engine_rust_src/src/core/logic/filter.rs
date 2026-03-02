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

use serde::{Deserialize, Serialize};
use super::CardDatabase;

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
    pub has_blade_heart: i8,   // 1=yes, -1=no, 0=don't care
    // Bit 15
    pub unique_names: bool,
    // Bit 16 + Bits 17-23
    pub unit_enabled: bool,
    pub unit_id: u8,
    // Bit 24 + Bits 25-29 + Bit 30 + Bit 31
    pub value_enabled: bool,
    pub value_threshold: u8,
    pub is_le: bool,
    pub is_cost_type: bool,    // true=Cost, false=Heart
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
        effective_hearts: Option<&[u8; 7]>
    ) -> bool {
        if !self.is_enabled { return true; }
        if cid == -1 { return false; }

        // 1. Card Type Filter (bits 2-3)
        if self.card_type > 0 {
            if self.card_type == 1 { // Member
                if !db.members.contains_key(&cid) { return false; }
            } else if self.card_type == 2 { // Live
                if !db.lives.contains_key(&cid) { return false; }
            }
        }

        // 2. Group Filter (bit 4 + bits 5-11)
        if self.group_enabled {
            if let Some(m) = db.get_member(cid) {
                if !m.groups.contains(&self.group_id) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if !l.groups.contains(&self.group_id) { return false; }
            } else {
                return false;
            }
        }

        // 3. Unit Filter (bit 16 + bits 17-23)
        if self.unit_enabled {
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&self.unit_id) { return false; }
            } else {
                return false;
            }
        }

        // 4. Character ID Filter (bits 39-45)
        if self.char_id_1 > 0 {
            let name = if let Some(m) = db.get_member(cid) { &m.name }
                       else if let Some(l) = db.get_live(cid) { &l.name }
                       else { "" };

            let target_name = crate::core::logic::card_db::get_character_name(self.char_id_1);
            if !name.replace(" ", "").contains(&target_name.replace(" ", "")) {
                // Check char_id_2 as alternate match
                if self.char_id_2 > 0 {
                    let target_name_2 = crate::core::logic::card_db::get_character_name(self.char_id_2);
                    if !name.replace(" ", "").contains(&target_name_2.replace(" ", "")) {
                        return false;
                    }
                } else {
                    return false;
                }
            }
        }

        // 5. Setsuna Filter (bit 59)
        if self.is_setsuna {
            let name = if let Some(m) = db.get_member(cid) { &m.name }
                       else if let Some(l) = db.get_live(cid) { &l.name }
                       else { "" };
            if !name.contains("せつ菜") { return false; }
        }

        // 6. Value Threshold Filter — Cost for Members, Hearts for Live (bit 24 + bits 25-29)
        if self.value_enabled && self.value_threshold > 0 {
            let actual_val = if self.is_cost_type {
                // Cost mode: check member cost
                if let Some(m) = db.get_member(cid) { m.cost as u8 }
                else { 0 }
            } else {
                // Heart mode: check total hearts
                if let Some(h) = effective_hearts {
                    h.iter().sum::<u8>()
                } else if let Some(l) = db.get_live(cid) {
                    l.required_hearts.iter().sum::<u8>()
                } else if let Some(m) = db.get_member(cid) {
                    m.hearts.iter().sum::<u8>()
                } else {
                    0
                }
            };

            if self.is_le {
                if actual_val > self.value_threshold { return false; }
            } else {
                if actual_val < self.value_threshold { return false; }
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
                if !match_found { return false; }
            } else {
                return false;
            }
        }

        // 8. Tapped Filter (bit 12)
        if self.is_tapped {
            if !is_tapped_override { return false; }
        }

        // 9. Blade Heart Filter (bits 13-14)
        if self.has_blade_heart != 0 {
            let has = if let Some(m) = db.get_member(cid) {
                m.blade_hearts.iter().any(|&h| h > 0)
            } else {
                false
            };
            if self.has_blade_heart > 0 && !has { return false; }
            if self.has_blade_heart < 0 && has { return false; }
        }

        // 10. Special ID Name Filter (bits 56-58)
        // These are hardcoded name checks matching map_filter_string_to_attr:
        //   special_id=1: NAME_IN=澁谷かのん (カノン/Kanon)
        //   special_id=2: NOT_NAME=MY舞 (excludes cards with MY舞 in name)
        if self.special_id > 0 {
            let name = if let Some(m) = db.get_member(cid) { m.name.as_str() }
                       else if let Some(l) = db.get_live(cid) { l.name.as_str() }
                       else { "" };
            match self.special_id {
                1 => { if !name.contains("澁谷かのん") { return false; } },
                2 => { if name.contains("MY舞") { return false; } },
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
        if !self.is_enabled { return 0; }

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
        if self.is_tapped { a |= 1 << 12; }

        // Bits 13-14: Blade Heart
        if self.has_blade_heart > 0 { a |= 1 << 13; }
        if self.has_blade_heart < 0 { a |= 1 << 14; }

        // Bit 15: Unique Names
        if self.unique_names { a |= 1 << 15; }

        // Bit 16 + Bits 17-23: Unit
        if self.unit_enabled {
            a |= 0x10000;
            a |= ((self.unit_id & 0x7F) as u64) << 17;
        }

        // Bit 24 + Bits 25-29 + Bit 30 + Bit 31: Value/Cost
        if self.value_enabled {
            a |= 1 << 24;
            a |= ((self.value_threshold & 0x1F) as u64) << 25;
            if self.is_le { a |= 1 << 30; }
            if self.is_cost_type { a |= 1u64 << 31; }
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
        if self.is_setsuna { a |= 1u64 << 59; }

        a as i64
    }
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
            card_type: 1,       // Member
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
        assert_eq!(attr & 0x10, 0x10);          // Group Enable
        assert_eq!((attr >> 5) & 0x7F, 3);      // Group ID = 3
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
        let python_attr: i64 = 0x01 | (0x01 << 2) | 0x10 | (3 << 5) | (1 << 24) | (5 << 25) | (1i64 << 31);
        let filter = CardFilter::from_attr(python_attr);

        assert!(filter.is_enabled);
        assert_eq!(filter.target_player, 1);     // Self
        assert_eq!(filter.card_type, 1);          // Member
        assert!(filter.group_enabled);
        assert_eq!(filter.group_id, 3);           // Liella
        assert!(filter.value_enabled);
        assert_eq!(filter.value_threshold, 5);
        assert!(!filter.is_le);                    // GE (cost_min)
        assert!(filter.is_cost_type);              // Cost type
    }
}
