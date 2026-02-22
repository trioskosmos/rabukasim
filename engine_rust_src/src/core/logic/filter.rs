//! Card Filter Module
//!
//! This module provides a structured way to handle card filtering logic.
//! The 64-bit filter attribute is decomposed into meaningful fields for clarity.

use serde::{Deserialize, Serialize};
use crate::core::generated_constants::*;
use super::CardDatabase;

/// Represents a comparison operation for cost/attribute filtering
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ComparisonOp {
    LessEqual,
    GreaterEqual,
    Equal,
}

/// A structured representation of the 64-bit filter attribute
/// 
/// Bit layout (see generated_constants.rs):
/// - Bits 2-3: Card type (Member=1, Live=2)
/// - Bit 4: Group filter enable
/// - Bits 5-11: Group ID
/// - Bit 7: Setsuna filter
/// - Bit 12: Tapped filter
/// - Bit 13: Has blade heart
/// - Bit 14: Not blade heart
/// - Bit 16: Unit filter enable
/// - Bits 17-23: Unit ID
/// - Bits 32-38: Color mask
/// - Bit 42: Character filter enable
/// - Bits 48-50: Special filter ID
#[derive(Debug, Clone, Default, PartialEq, Eq, Serialize, Deserialize)]
pub struct CardFilter {
    /// Card type filter: None, Some(Member), Some(Live)
    pub card_type: Option<u8>, // 0=None, 1=Member, 2=Live
    /// Group ID to filter by
    pub group_id: Option<u8>,
    /// Unit ID to filter by
    pub unit_id: Option<u8>,
    /// Color mask (7 bits, one per color)
    pub color_mask: u8,
    /// Character IDs for name filtering (up to 3)
    pub character_ids: [Option<u8>; 3],
    /// Tapped state filter
    pub is_tapped: Option<bool>,
    /// Blade heart filter
    pub has_blade_heart: Option<bool>,
    /// Cost comparison (threshold, is_less_or_equal)
    pub cost_filter: Option<(i32, bool)>,
    /// Special filter ID
    pub special_id: u8,
    /// Setsuna filter flag
    pub setsuna_filter: bool,
}


impl CardFilter {
    /// Check if a card matches this filter.
    /// Note: is_tapped_override should be provided if the Tapped filter (bit 12) is relevant,
    /// as it depends on the dynamic GameState.
    pub fn matches(&self, db: &CardDatabase, cid: i32, is_tapped_override: bool) -> bool {
        if cid == -1 { return false; }

        // Character Filter
        if !self.character_ids.iter().all(|&id| id.is_none()) {
            let name = if let Some(m) = db.get_member(cid) { &m.name }
                       else if let Some(l) = db.get_live(cid) { &l.name }
                       else { "" };
            
            let mut match_found = false;
            let normalized_name = name.replace(" ", "");
            for &id_opt in &self.character_ids {
                if let Some(id) = id_opt {
                    let target_name = crate::core::logic::card_db::get_character_name(id).replace(" ", "");
                    if normalized_name.contains(&target_name) {
                        match_found = true;
                        break;
                    }
                }
            }
            if !match_found { return false; }
        }

        // Setsuna Filter
        if self.setsuna_filter {
            let name = if let Some(m) = db.get_member(cid) { &m.name }
                       else if let Some(l) = db.get_live(cid) { &l.name }
                       else { "" };
            let setsuna_name = crate::core::logic::card_db::get_character_name(27);
            if !name.replace(" ", "").contains(&setsuna_name.replace(" ", "")) {
                return false;
            }
        }

        // Color Filter
        if self.color_mask != 0 {
            if let Some(m) = db.get_member(cid) {
                let mut has_match = false;
                for i in 0..7 {
                    if (self.color_mask & (1 << i)) != 0 && m.hearts[i] > 0 {
                        has_match = true;
                        break;
                    }
                }
                if !has_match { return false; }
            } else if let Some(l) = db.get_live(cid) {
                let mut has_match = false;
                for i in 0..7 {
                    if (self.color_mask & (1 << i)) != 0 && l.required_hearts[i] > 0 {
                        has_match = true;
                        break;
                    }
                }
                if !has_match { return false; }
            } else {
                return false;
            }
        }

        // Type Filter
        if let Some(ct) = self.card_type {
            if ct == 1 && db.get_member(cid).is_none() { return false; }
            if ct == 2 && db.get_live(cid).is_none() { return false; }
        }

        // Group Filter
        if let Some(group_id) = self.group_id {
            if let Some(m) = db.get_member(cid) {
                if !m.groups.contains(&(group_id as u8)) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if !l.groups.contains(&(group_id as u8)) { return false; }
            } else {
                return false;
            }
        }

        // Unit Filter
        if let Some(unit_id) = self.unit_id {
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&(unit_id as u8)) { return false; }
            } else if let Some(l) = db.get_live(cid) {
                if !l.units.contains(&(unit_id as u8)) { return false; }
            } else {
                return false;
            }
        }

        // Tapped Filter
        if self.is_tapped == Some(true) && !is_tapped_override {
            return false;
        }

        // Blade Heart Filters
        if let Some(has_bh) = self.has_blade_heart {
            if let Some(m) = db.get_member(cid) {
                let actual_has = m.blade_hearts.iter().any(|&h| h > 0);
                if actual_has != has_bh { return false; }
            } else if let Some(l) = db.get_live(cid) {
                let actual_has = l.blade_hearts.iter().any(|&h| h > 0);
                if actual_has != has_bh { return false; }
            } else {
                return false;
            }
        }

        // Special Filter IDs
        if self.special_id != 0 {
            let card_name = if let Some(m) = db.get_member(cid) { &m.name }
                           else if let Some(l) = db.get_live(cid) { &l.name }
                           else { "" };
            match self.special_id {
                1 => { // NAME_IN=['澁谷かのん', 'ウィーン·マルガレーテ', '鬼塚冬毬']
                    if !["澁谷かのん", "ウィーン·マルガレーテ", "鬼塚冬毬"].contains(&card_name) { return false; }
                },
                2 => { // NOT_NAME=MY舞☆TONIGHT
                    if card_name == "MY舞☆TONIGHT" { return false; }
                },
                _ => {}
            }
        }

        // Cost/Hearts Filter
        if let Some((threshold, is_le)) = self.cost_filter {
            let card_value = if let Some(m) = db.get_member(cid) {
                m.cost as i32
            } else if let Some(l) = db.get_live(cid) {
                l.required_hearts.iter().map(|&h| h as i32).sum::<i32>()
            } else {
                return false;
            };
            if is_le {
                if card_value > threshold { return false; }
            } else {
                if card_value < threshold { return false; }
            }
        }

        true
    }

    /// Parse a 64-bit filter attribute into a structured CardFilter
    pub fn from_attr(filter_attr: u64) -> Self {
        let mut filter = CardFilter::default();
        
        // Card type (bits 2-3)
        let type_filter = (filter_attr >> FILTER_TYPE_SHIFT) & 0x03;
        if type_filter != 0 {
            filter.card_type = Some(type_filter as u8);
        }
        
        // Group filter (bit 4, bits 5-11)
        if (filter_attr & FILTER_GROUP_ENABLE) != 0 {
            filter.group_id = Some(((filter_attr >> FILTER_GROUP_SHIFT) & 0x7F) as u8);
        }
        
        // Unit filter (bit 16, bits 17-23)
        if (filter_attr & FILTER_UNIT_ENABLE) != 0 {
            filter.unit_id = Some(((filter_attr >> FILTER_UNIT_SHIFT) & 0x7F) as u8);
        }
        
        // Color mask (bits 32-38)
        filter.color_mask = ((filter_attr >> FILTER_COLOR_SHIFT) & 0x7F) as u8;
        
        // Character filter (bit 42)
        if (filter_attr & FILTER_CHARACTER_ENABLE) != 0 {
            filter.character_ids = [
                Some(((filter_attr >> 31) & 0x7F) as u8),
                Some(((filter_attr >> 17) & 0x7F) as u8),
                Some(((filter_attr >> 24) & 0x7F) as u8),
            ];
        }
        
        // Tapped filter (bit 12)
        if (filter_attr & FILTER_TAPPED) != 0 {
            filter.is_tapped = Some(true);
        }
        
        // Blade heart filters (bits 13-14)
        if (filter_attr & FILTER_HAS_BLADE_HEART) != 0 {
            filter.has_blade_heart = Some(true);
        }
        if (filter_attr & FILTER_NOT_BLADE_HEART) != 0 {
            filter.has_blade_heart = Some(false);
        }
        
        // Cost filter (bit 24, bits 25-29, bit 30)
        if (filter_attr & FILTER_COST_ENABLE) != 0 {
            let threshold = ((filter_attr >> FILTER_COST_SHIFT) & 0x1F) as i32;
            let is_le = (filter_attr & FILTER_COST_LE) != 0;
            filter.cost_filter = Some((threshold, is_le));
        }
        
        // Special filter (bits 48-50)
        filter.special_id = ((filter_attr >> FILTER_SPECIAL_SHIFT) & 0x07) as u8;
        
        // Setsuna filter (bit 7)
        if (filter_attr & FILTER_SETSUNA) != 0 {
            filter.setsuna_filter = true;
        }
        
        filter
    }
    
    /// Convert a CardFilter back to a 64-bit filter attribute
    pub fn to_attr(&self) -> u64 {
        let mut attr: u64 = 0;
        
        if let Some(ct) = self.card_type {
            attr |= (ct as u64) << FILTER_TYPE_SHIFT;
        }
        
        if let Some(gid) = self.group_id {
            attr |= FILTER_GROUP_ENABLE | ((gid as u64) << FILTER_GROUP_SHIFT);
        }
        
        if let Some(uid) = self.unit_id {
            attr |= FILTER_UNIT_ENABLE | ((uid as u64) << FILTER_UNIT_SHIFT);
        }
        
        attr |= (self.color_mask as u64) << FILTER_COLOR_SHIFT;
        
        for (i, cid) in self.character_ids.iter().enumerate() {
            if let Some(id) = cid {
                attr |= FILTER_CHARACTER_ENABLE;
                // Character IDs are stored at different bit positions
                match i {
                    0 => attr |= (*id as u64) << 31,
                    1 => attr |= (*id as u64) << 17,
                    2 => attr |= (*id as u64) << 24,
                    _ => {}
                }
            }
        }
        
        if self.is_tapped == Some(true) {
            attr |= FILTER_TAPPED;
        }
        
        if self.has_blade_heart == Some(true) {
            attr |= FILTER_HAS_BLADE_HEART;
        }
        if self.has_blade_heart == Some(false) {
            attr |= FILTER_NOT_BLADE_HEART;
        }
        
        if let Some((threshold, is_le)) = self.cost_filter {
            attr |= FILTER_COST_ENABLE | ((threshold as u64) << FILTER_COST_SHIFT);
            if is_le {
                attr |= FILTER_COST_LE;
            }
        }
        
        attr |= (self.special_id as u64) << FILTER_SPECIAL_SHIFT;
        
        if self.setsuna_filter {
            attr |= FILTER_SETSUNA;
        }
        
        attr
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_filter_roundtrip() {
        let mut filter = CardFilter::default();
        filter.card_type = Some(1);
        filter.group_id = Some(5);
        filter.color_mask = 0x3; // SMILE + PURE
        
        let attr = filter.to_attr();
        let parsed = CardFilter::from_attr(attr);
        
        assert_eq!(filter.card_type, parsed.card_type);
        assert_eq!(filter.group_id, parsed.group_id);
        assert_eq!(filter.color_mask, parsed.color_mask);
    }
    
    #[test]
    fn test_character_filter() {
        let mut filter = CardFilter::default();
        filter.character_ids = [Some(1), Some(2), None]; // Honoka, Eli
        
        let attr = filter.to_attr();
        assert!(attr & FILTER_CHARACTER_ENABLE != 0);
        
        let parsed = CardFilter::from_attr(attr);
        assert_eq!(Some(1), parsed.character_ids[0]);
        assert_eq!(Some(2), parsed.character_ids[1]);
    }
}
