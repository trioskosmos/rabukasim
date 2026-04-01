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
use serde::{de, Deserialize, Deserializer, Serialize};
// use crate::core::enums::Zone;
use crate::core::models::{AbilityContext, GameState};

/// Conversion error types for better error handling
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ConversionError {
    InvalidTargetPlayer(u8),
    InvalidCardType(u8),
    InvalidGroupId(u8),
    InvalidUnitId(u8),
    InvalidValueThreshold(u8),
    InvalidZoneMask(u8),
}

impl std::fmt::Display for ConversionError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ConversionError::InvalidTargetPlayer(p) => write!(f, "Invalid target player: {}", p),
            ConversionError::InvalidCardType(t) => write!(f, "Invalid card type: {}", t),
            ConversionError::InvalidGroupId(g) => write!(f, "Invalid group ID: {}", g),
            ConversionError::InvalidUnitId(u) => write!(f, "Invalid unit ID: {}", u),
            ConversionError::InvalidValueThreshold(v) => write!(f, "Invalid value threshold: {}", v),
            ConversionError::InvalidZoneMask(z) => write!(f, "Invalid zone mask: {}", z),
        }
    }
}

impl std::error::Error for ConversionError {}

/// Helper function to deserialize bool from either bool or integer
fn bool_from_int<'de, D>(deserializer: D) -> Result<bool, D::Error>
where
    D: Deserializer<'de>,
{
    struct BoolOrInt;

    impl<'de> de::Visitor<'de> for BoolOrInt {
        type Value = bool;

        fn expecting(&self, formatter: &mut std::fmt::Formatter) -> std::fmt::Result {
            formatter.write_str("bool or integer (0 or 1)")
        }

        fn visit_bool<E>(self, value: bool) -> Result<bool, E>
        where
            E: de::Error,
        {
            Ok(value)
        }

        fn visit_i64<E>(self, value: i64) -> Result<bool, E>
        where
            E: de::Error,
        {
            Ok(value != 0)
        }

        fn visit_u64<E>(self, value: u64) -> Result<bool, E>
        where
            E: de::Error,
        {
            Ok(value != 0)
        }
    }

    deserializer.deserialize_any(BoolOrInt)
}

// --- Filter Bitfield Constants (Now loaded from generated_constants.rs via constants.rs) ---
pub const FILTER_STATE_FLAGS_MASK: u64 = 61440; // 0xF000

/// A structured representation of the 64-bit filter attribute
#[derive(Debug, Clone, Copy, Default, PartialEq, Eq, Serialize, Deserialize, Hash)]
#[serde(default)]
pub struct CardFilter {
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_enabled: bool,
    // Bits 0-1
    pub target_player: u8,
    // Bits 2-3
    pub card_type: u8,
    // Bit 4 + Bits 5-11
    #[serde(deserialize_with = "bool_from_int", default)]
    pub group_enabled: bool,
    pub group_id: u8,
    // Bit 12
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_tapped: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub has_blade_heart: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub not_has_blade_heart: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub unique_names: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub unit_enabled: bool,
    pub unit_id: u8,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub value_enabled: bool,
    pub value_threshold: u8,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_le: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_cost_type: bool,
    pub color_mask: u8,
    pub char_id_1: u8,
    pub char_id_2: u8,
    pub char_id_3: u8,
    pub zone_mask: u8,
    pub special_id: u8,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_setsuna: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub compare_accumulated: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub is_optional: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub keyword_energy: bool,
    #[serde(deserialize_with = "bool_from_int", default)]
    pub keyword_member: bool,
}

/// Conversion helpers for filter operations
impl CardFilter {
    /// Extract group information with validation
    fn get_group_info(&self) -> (bool, u8) {
        (self.group_enabled, self.group_id)
    }

    /// Convert to raw 64-bit format with clear bit operations and validation
    pub fn to_attr_computed(&self) -> u64 {
        let mut attr: u64 = 0;
        
        // Validate inputs before conversion
        debug_assert!(self.target_player <= 2, "Invalid target player: {}", self.target_player);
        debug_assert!(self.card_type <= 2, "Invalid card type: {}", self.card_type);
        debug_assert!(self.group_id <= 127, "Invalid group ID: {}", self.group_id);
        debug_assert!(self.unit_id <= 127, "Invalid unit ID: {}", self.unit_id);
        debug_assert!(self.value_threshold <= 31, "Invalid value threshold: {}", self.value_threshold);
        
        // Set basic fields
        attr |= self.target_player as u64;
        attr |= (self.card_type as u64) << 2;
        
        // Set group information
        let (group_enabled, group_id) = self.get_group_info();
        if group_enabled {
            attr |= 1 << 4; // Group Enable flag
            attr |= (group_id as u64) << 5;
        }
        
        // Set boolean flags
        if self.is_tapped { attr |= 1 << 12; }
        if self.has_blade_heart { attr |= 1 << 13; }
        if self.not_has_blade_heart { attr |= 1 << 14; }
        if self.unique_names { attr |= 1 << 15; }
        
        // Set unit information
        if self.unit_enabled {
            attr |= 1 << 16;
            attr |= (self.unit_id as u64) << 17;
        }
        
        // Set value information
        if self.value_enabled {
            attr |= 1 << 24;
            attr |= (self.value_threshold as u64) << 25;
            if self.is_le { attr |= 1 << 30; }
            if self.is_cost_type { attr |= 1 << 31; }
        }
        
        // Set remaining fields
        attr |= (self.color_mask as u64) << 32;
        attr |= (self.char_id_1 as u64) << 39;
        attr |= (self.char_id_2 as u64) << 46;
        attr |= (self.zone_mask as u64) << 53;
        attr |= (self.special_id as u64) << 56;
        if self.is_setsuna { attr |= 1 << 59; }
        if self.compare_accumulated { attr |= 1 << 60; }
        if self.is_optional { attr |= 1 << 61; }
        if self.keyword_energy { attr |= 1 << 62; }
        if self.keyword_member { attr |= 1 << 63; }
        
        attr
    }

    /// Validate filter state and return structured errors
    pub fn validate(&self) -> Result<(), ConversionError> {
        if self.target_player > 2 {
            return Err(ConversionError::InvalidTargetPlayer(self.target_player));
        }
        if self.card_type > 2 {
            return Err(ConversionError::InvalidCardType(self.card_type));
        }
        if self.group_id > 127 {
            return Err(ConversionError::InvalidGroupId(self.group_id));
        }
        if self.unit_id > 127 {
            return Err(ConversionError::InvalidUnitId(self.unit_id));
        }
        if self.value_threshold > 31 {
            return Err(ConversionError::InvalidValueThreshold(self.value_threshold));
        }
        // Additional validation for zone mask
        if self.zone_mask > 0b111 {
            return Err(ConversionError::InvalidZoneMask(self.zone_mask));
        }
        Ok(())
    }

    pub fn matches(
        &self,
        state: &crate::core::logic::GameState,
        db: &CardDatabase,
        cid: i32,
        checked_slot: Option<(u8, i16)>,
        _is_tapped_override: bool,
        effective_hearts: Option<&[u8; 7]>,
        ctx: &crate::core::logic::AbilityContext,
    ) -> bool {
        // Implementation moved here directly from filter_attr_compat
        if !self.is_enabled {
            return true;
        }
        // 0. Target Player Filter (bits 0-1)
        if self.target_player > 0 && self.target_player < 4 {
            let target_p = match self.target_player {
                1 => ctx.player_id,
                2 => 1 - ctx.player_id,
                3 => 255, // Both (always pass later)
                _ => ctx.player_id,
            };
            if target_p != 255 {
                let inferred_owner = state.players
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
                            || player.yell_cards.iter().any(|&card_id| card_id == cid)
                            || player.looked_cards.iter().any(|&card_id| card_id == cid);
                        if owns_card {
                            Some(p_idx as u8)
                        } else {
                            None
                        }
                    });

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
        if self.card_type > 0 && self.card_type <= 2 {
            let is_member = db.get_member(cid).is_some();
            let is_live = db.get_live(cid).is_some();
            
            let matches = match self.card_type {
                1 => is_member,  // Member
                2 => is_live,    // Live
                _ => false,
            };
            
            if !matches {
                return false;
            }
        }

        // 2. Group Filter (bits 4-11)
        if self.group_enabled {
            let card_group = if let Some(m) = db.get_member(cid) {
                m.groups.iter().find(|&&g| g > 0).copied()
            } else if let Some(l) = db.get_live(cid) {
                l.groups.iter().find(|&&g| g > 0).copied()
            } else {
                None
            };
            
            if let Some(group) = card_group {
                if group != self.group_id && group.saturating_add(1) != self.group_id {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 3. Unit Filter (bits 16-23)
        if self.unit_enabled {
            if let Some(m) = db.get_member(cid) {
                if !m.units.contains(&self.unit_id) {
                    return false;
                }
            } else {
                return false;
            }
        }

        // 4. Value Filter (bits 24-31)
        if self.value_enabled {
            let actual_val = if let Some(h) = effective_hearts {
                if self.is_cost_type {
                    // For cost comparisons, sum only the colors specified in color_mask
                    let mut sum = 0;
                    for i in 0..7 {
                        if (self.color_mask & (1 << i)) != 0 && h[i] > 0 {
                            sum += h[i];
                        }
                    }
                    sum
                } else if self.compare_accumulated {
                    // For accumulated value comparisons with specific colors, sum only those colors
                    if self.color_mask != 0 {
                        let mut sum = 0;
                        for i in 0..7 {
                            if (self.color_mask & (1 << i)) != 0 {
                                sum += h[i];
                            }
                        }
                        sum
                    } else {
                        // No color mask specified, sum all hearts
                        h.iter().sum::<u8>()
                    }
                } else {
                    // For simple value threshold, sum hearts of the specified color(s)
                    let mut sum = 0;
                    for i in 0..7 {
                        if (self.color_mask & (1 << i)) != 0 {
                            sum += h[i];
                        }
                    }
                    sum
                }
            } else if self.card_type == 2 {
                // For Live cards not on stage, check required_hearts
                if let Some(live) = db.get_live(cid) {
                    let sum: u8 = live.required_hearts.iter().sum();
                    sum
                } else {
                    0
                }
            } else if self.is_cost_type {
                // For Member cards with cost comparison
                if let Some(member) = db.get_member(cid) {
                    member.cost as u8
                } else {
                    0
                }
            } else {
                0
            };

            let threshold = self.value_threshold;

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

        // 5. Check is_tapped flag (bit 12)
        if self.is_tapped {
            if let Some((p_idx, s_idx)) = checked_slot {
                if s_idx >= 0 && s_idx < 3 {
                    if !state.players[p_idx as usize].is_tapped(s_idx as usize) {
                        return false;
                    }
                } else {
                    return false;
                }
            } else {
                // If no slot provided, can't verify tapped status
                return false;
            }
        }

        // Check special filters using special_id
        if self.special_id == 1 {
            // NAME_IN filter - check if card name contains the search character
            if let Some(m) = db.get_member(cid) {
                if self.color_mask != 0 {
                    let search_char = (self.color_mask & 0x7F) as char;
                    if !m.name.to_uppercase().contains(search_char.to_ascii_uppercase()) {
                        return false;
                    }
                } else {
                    // Fallback - check for KANON
                    if !m.name.to_uppercase().contains("KANON") {
                        return false;
                    }
                }
            } else {
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

    pub fn to_attr(&self) -> u64 {
        crate::core::logic::filter_attr_compat::card_filter_to_attr(self) as u64
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
