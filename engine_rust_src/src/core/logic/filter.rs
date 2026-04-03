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
use crate::core::generated_layout::*;
use serde::{de, Deserialize, Deserializer, Serialize};
use serde_json::Value;
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
    pub fn has_group(&self) -> bool {
        self.group_enabled
    }

    pub fn group_matches(&self, group_id: u8) -> bool {
        self.group_enabled
            && match self.group_id {
                101 => group_id == 1 || group_id == 11,
                _ => self.group_id == group_id || self.group_id == group_id.saturating_add(1),
            }
    }

    pub fn from_json_value(value: &Value) -> Option<Self> {
        let candidate = if let Some(obj) = value.as_object() {
            obj.get("attr").or_else(|| obj.get("filter")).unwrap_or(value)
        } else {
            value
        };

        match candidate {
            Value::Null => None,
            Value::Number(number) => number
                .as_i64()
                .map(|attr| Self::from_attr(attr as u64))
                .or_else(|| number.as_u64().map(Self::from_attr)),
            Value::Object(object) => {
                let mut filter = serde_json::from_value::<Self>(Value::Object(object.clone())).ok()?;
                if filter != Self::default() {
                    filter.is_enabled = true;
                    Some(filter)
                } else {
                    None
                }
            }
            _ => None,
        }
    }

    fn same_name_sources(
        state: &GameState,
        db: &CardDatabase,
        ctx: &AbilityContext,
    ) -> Vec<String> {
        let p_idx = ctx.player_id as usize;
        let mut source_cards: Vec<i32> = state.players[p_idx].revealed_cards.iter().copied().collect();
        if source_cards.is_empty() {
            source_cards = ctx
                .selected_cards
                .iter()
                .copied()
                .filter(|cid| db.get_live(*cid).is_some() || db.get_member(*cid).is_some())
                .collect();
        }
        if source_cards.is_empty() {
            source_cards = state.players[p_idx]
                .hand
                .iter()
                .copied()
                .filter(|cid| db.get_live(*cid).is_some() || db.get_member(*cid).is_some())
                .collect();
        }

        source_cards
            .into_iter()
            .filter_map(|source_cid| {
                db.get_live(source_cid)
                    .map(|card| card.name.clone())
                    .or_else(|| db.get_member(source_cid).map(|card| card.name.clone()))
            })
            .collect()
    }

    /// Extract group information with validation
    fn get_group_info(&self) -> (bool, u8) {
        (self.group_enabled, self.group_id)
    }

    /// Convert to raw 64-bit format with clear bit operations and validation
    pub fn to_attr_computed(&self) -> u64 {
        let mut attr: u64 = 0;
        
        // Validate inputs before conversion
        debug_assert!(self.target_player <= 3, "Invalid target player: {}", self.target_player);
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
        } else if self.char_id_3 != 0 {
            // Legacy packed attrs reuse the unit-id bits for a third character id.
            attr |= (self.char_id_3 as u64) << 17;
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
        if self.target_player > 3 {
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
        if !self.is_enabled {
            return true;
        }
        let member = db.get_member(cid);
        let live = db.get_live(cid);
        let requested_char_mask = requested_char_mask(self);
        let needs_card_metadata = self.card_type != 0
            || self.group_enabled
            || self.unit_enabled
            || requested_char_mask != 0
            || self.has_blade_heart
            || self.not_has_blade_heart
            || self.is_setsuna
            || self.special_id == 1
            || self.special_id == 4
            || self.is_cost_type;

        if member.is_none() && live.is_none() && needs_card_metadata {
            return false;
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
            let is_member = member.is_some();
            let is_live = live.is_some();
            
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
            let group_match = member
                .map(|card| card.groups.iter().copied().any(|group| self.group_matches(group)))
                .or_else(|| {
                    live.map(|card| card.groups.iter().copied().any(|group| self.group_matches(group)))
                })
                .unwrap_or(false);

            if !group_match {
                return false;
            }
        }

        if requested_char_mask != 0 {
            let card_char_mask = member
                .map(|card| card.char_mask)
                .or_else(|| live.map(|card| card.char_mask))
                .unwrap_or_default();
            if (card_char_mask & requested_char_mask) == 0 {
                return false;
            }
        }

        // 3. Unit Filter (bits 16-23)
        if self.unit_enabled {
            let unit_match = member
                .map(|card| card.units.contains(&self.unit_id))
                .or_else(|| live.map(|card| card.units.contains(&self.unit_id)))
                .unwrap_or(false);
            if !unit_match {
                return false;
            }
        }

        let has_blade_heart = member
            .map(|card| card.blade_hearts.iter().any(|&heart| heart > 0))
            .or_else(|| live.map(|card| card.blade_hearts.iter().any(|&heart| heart > 0)))
            .unwrap_or(false);

        if self.has_blade_heart && !has_blade_heart {
            return false;
        }
        if self.not_has_blade_heart && has_blade_heart {
            return false;
        }

        if self.is_setsuna {
            let semantic_flags = member
                .map(|card| card.semantic_flags)
                .or_else(|| live.map(|card| card.semantic_flags))
                .unwrap_or_default();
            if (semantic_flags & 0x100) == 0 {
                return false;
            }
        }

        if self.zone_mask != 0 && !card_matches_zone_mask(state, cid, self.zone_mask) {
            return false;
        }

        // 4. Value Filter (bits 24-31)
        if self.value_enabled {
            let actual_val = if self.is_cost_type {
                member.map(|card| card.cost.min(u8::MAX as u32) as u8).unwrap_or(0)
            } else if let Some(h) = effective_hearts {
                sum_matching_hearts(h, self.color_mask)
            } else if let Some(card) = member {
                sum_matching_hearts(&card.hearts, self.color_mask)
            } else if let Some(card) = live {
                sum_matching_hearts(&card.required_hearts, self.color_mask)
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
            if let Some(name) = member
                .map(|card| card.name.as_str())
                .or_else(|| live.map(|card| card.name.as_str()))
            {
                if self.color_mask != 0 {
                    let search_char = (self.color_mask & 0x7F) as char;
                    if !name.to_uppercase().contains(search_char.to_ascii_uppercase()) {
                        return false;
                    }
                } else {
                    // Fallback - check for KANON
                    if !name.to_uppercase().contains("KANON") {
                        return false;
                    }
                }
            } else {
                return false;
            }
        }

        if self.special_id == 2 {
            let semantic_flags = member
                .map(|card| card.semantic_flags)
                .or_else(|| live.map(|card| card.semantic_flags))
                .unwrap_or_default();
            if (semantic_flags & 0x400) != 0 {
                return false;
            }
        }

        if self.special_id == 3 {
            if let Some((checked_player, checked_slot)) = checked_slot {
                if checked_player == ctx.player_id && ctx.area_idx >= 0 && checked_slot == ctx.area_idx {
                    return false;
                }
            } else if cid == ctx.source_card_id {
                return false;
            }
        }

        if self.special_id == 4 {
            let Some(candidate_name) = live
                .map(|card| card.name.as_str())
                .or_else(|| member.map(|card| card.name.as_str()))
            else {
                return false;
            };

            let source_names = Self::same_name_sources(state, db, ctx);
            if source_names.is_empty() {
                return false;
            }

            if !source_names
                .iter()
                .any(|source_name| candidate_name.contains(source_name))
            {
                return false;
            }
        }

        if self.special_id == 6 && !ctx.selected_cards.contains(&cid) {
            return false;
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

    /// Decode a packed 64-bit filter attribute into its structured form.
    pub fn from_attr(attr: u64) -> Self {
        if attr == 0 {
            return Self {
                is_enabled: true,
                ..Self::default()
            };
        }

        let unit_enabled =
            ((attr >> A_STANDARD_UNIT_ENABLED_SHIFT) & A_STANDARD_UNIT_ENABLED_MASK) != 0;

        Self {
            is_enabled: true,
            target_player: ((attr >> A_STANDARD_TARGET_PLAYER_SHIFT)
                & A_STANDARD_TARGET_PLAYER_MASK) as u8,
            card_type: ((attr >> A_STANDARD_CARD_TYPE_SHIFT) & A_STANDARD_CARD_TYPE_MASK) as u8,
            group_enabled: ((attr >> A_STANDARD_GROUP_ENABLED_SHIFT)
                & A_STANDARD_GROUP_ENABLED_MASK)
                != 0,
            group_id: ((attr >> A_STANDARD_GROUP_ID_SHIFT) & A_STANDARD_GROUP_ID_MASK) as u8,
            is_tapped: ((attr >> A_STANDARD_IS_TAPPED_SHIFT) & A_STANDARD_IS_TAPPED_MASK) != 0,
            has_blade_heart: ((attr >> A_STANDARD_HAS_BLADE_HEART_SHIFT)
                & A_STANDARD_HAS_BLADE_HEART_MASK)
                != 0,
            not_has_blade_heart: ((attr >> A_STANDARD_NOT_HAS_BLADE_HEART_SHIFT)
                & A_STANDARD_NOT_HAS_BLADE_HEART_MASK)
                != 0,
            unique_names: ((attr >> A_STANDARD_UNIQUE_NAMES_SHIFT)
                & A_STANDARD_UNIQUE_NAMES_MASK)
                != 0,
            unit_enabled,
            unit_id: ((attr >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8,
            value_enabled: ((attr >> A_STANDARD_VALUE_ENABLED_SHIFT)
                & A_STANDARD_VALUE_ENABLED_MASK)
                != 0,
            value_threshold: ((attr >> A_STANDARD_VALUE_THRESHOLD_SHIFT)
                & A_STANDARD_VALUE_THRESHOLD_MASK) as u8,
            is_le: ((attr >> A_STANDARD_IS_LE_SHIFT) & A_STANDARD_IS_LE_MASK) != 0,
            is_cost_type: ((attr >> A_STANDARD_IS_COST_TYPE_SHIFT)
                & A_STANDARD_IS_COST_TYPE_MASK)
                != 0,
            color_mask: ((attr >> A_STANDARD_COLOR_MASK_SHIFT) & A_STANDARD_COLOR_MASK_MASK)
                as u8,
            char_id_1: ((attr >> A_STANDARD_CHAR_ID_1_SHIFT) & A_STANDARD_CHAR_ID_1_MASK) as u8,
            char_id_2: ((attr >> A_STANDARD_CHAR_ID_2_SHIFT) & A_STANDARD_CHAR_ID_2_MASK) as u8,
            char_id_3: if unit_enabled {
                0
            } else {
                ((attr >> A_STANDARD_UNIT_ID_SHIFT) & A_STANDARD_UNIT_ID_MASK) as u8
            },
            zone_mask: ((attr >> A_STANDARD_ZONE_MASK_SHIFT) & A_STANDARD_ZONE_MASK_MASK) as u8,
            special_id: ((attr >> A_STANDARD_SPECIAL_ID_SHIFT) & A_STANDARD_SPECIAL_ID_MASK)
                as u8,
            is_setsuna: ((attr >> A_STANDARD_IS_SETSUNA_SHIFT) & A_STANDARD_IS_SETSUNA_MASK)
                != 0,
            compare_accumulated: ((attr >> A_STANDARD_COMPARE_ACCUMULATED_SHIFT)
                & A_STANDARD_COMPARE_ACCUMULATED_MASK)
                != 0,
            is_optional: ((attr >> A_STANDARD_IS_OPTIONAL_SHIFT) & A_STANDARD_IS_OPTIONAL_MASK)
                != 0,
            keyword_energy: ((attr >> A_STANDARD_KEYWORD_ENERGY_SHIFT)
                & A_STANDARD_KEYWORD_ENERGY_MASK)
                != 0,
            keyword_member: ((attr >> A_STANDARD_KEYWORD_MEMBER_SHIFT)
                & A_STANDARD_KEYWORD_MEMBER_MASK)
                != 0,
        }
    }

    pub fn to_attr(&self) -> u64 {
        if !self.is_enabled {
            0
        } else {
            self.to_attr_computed()
        }
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

    pub fn with_overlay(mut self, overlay: &CardFilter) -> Self {
        if !overlay.is_enabled {
            return self;
        }

        self.is_enabled = true;

        if overlay.target_player != 0 {
            self.target_player = overlay.target_player;
        }
        if overlay.card_type != 0 {
            self.card_type = overlay.card_type;
        }
        if overlay.group_enabled {
            self.group_enabled = true;
            self.group_id = overlay.group_id;
        }
        if overlay.is_tapped {
            self.is_tapped = true;
        }
        if overlay.has_blade_heart {
            self.has_blade_heart = true;
        }
        if overlay.not_has_blade_heart {
            self.not_has_blade_heart = true;
        }
        if overlay.unique_names {
            self.unique_names = true;
        }
        if overlay.unit_enabled {
            self.unit_enabled = true;
            self.unit_id = overlay.unit_id;
            self.char_id_3 = 0;
        } else if overlay.char_id_3 != 0 {
            self.char_id_3 = overlay.char_id_3;
        }
        if overlay.value_enabled {
            self.value_enabled = true;
            self.value_threshold = overlay.value_threshold;
            self.is_le = overlay.is_le;
            self.is_cost_type = overlay.is_cost_type;
        }
        if overlay.color_mask != 0 {
            self.color_mask = overlay.color_mask;
        }
        if overlay.char_id_1 != 0 {
            self.char_id_1 = overlay.char_id_1;
        }
        if overlay.char_id_2 != 0 {
            self.char_id_2 = overlay.char_id_2;
        }
        if overlay.zone_mask != 0 {
            self.zone_mask = overlay.zone_mask;
        }
        if overlay.special_id != 0 {
            self.special_id = overlay.special_id;
        }
        if overlay.is_setsuna {
            self.is_setsuna = true;
        }
        if overlay.compare_accumulated {
            self.compare_accumulated = true;
        }
        if overlay.is_optional {
            self.is_optional = true;
        }
        if overlay.keyword_energy {
            self.keyword_energy = true;
        }
        if overlay.keyword_member {
            self.keyword_member = true;
        }

        self
    }

    /// Create CardFilter from authored frame JSON without accepting raw packed attrs.
    pub fn from_frame_json(payload: &Value, options: &Value, params: &Value) -> Self {
        let mut filter = Self::from_json_value(payload)
            .or_else(|| filter_from_params(Some(payload)))
            .unwrap_or_default();

        if let Some(options_filter) = Self::from_json_value(options)
            .or_else(|| filter_from_params(Some(options)))
        {
            filter = filter.with_overlay(&options_filter);
        }

        if let Some(params_filter) = Self::from_json_value(params)
            .or_else(|| filter_from_params(Some(params)))
        {
            filter = filter.with_overlay(&params_filter);
        }

        if options
            .get("is_cost")
            .or_else(|| options.get("is_cost_type"))
            .or_else(|| params.get("is_cost_type"))
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            filter.is_enabled = true;
            filter.is_cost_type = true;
        }

        if options
            .get("optional")
            .or_else(|| options.get("is_optional"))
            .or_else(|| params.get("optional"))
            .or_else(|| params.get("is_optional"))
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            filter.is_enabled = true;
            filter.is_optional = true;
        }

        filter
    }
}

fn requested_char_mask(filter: &CardFilter) -> u128 {
    [filter.char_id_1, filter.char_id_2, filter.char_id_3]
        .into_iter()
        .filter(|char_id| *char_id > 0)
        .fold(0u128, |mask, char_id| mask | (1u128 << char_id))
}

fn sum_matching_hearts(hearts: &[u8; 7], color_mask: u8) -> u8 {
    if color_mask == 0 {
        hearts.iter().sum()
    } else {
        (0..7)
            .filter(|idx| (color_mask & (1 << idx)) != 0)
            .map(|idx| hearts[idx])
            .sum()
    }
}

fn card_matches_zone_mask(state: &GameState, cid: i32, zone_mask: u8) -> bool {
    let in_stage = state.players.iter().any(|player| player.stage.iter().any(|&card_id| card_id == cid));
    let in_hand = state.players.iter().any(|player| player.hand.iter().any(|&card_id| card_id == cid));
    let in_discard = state.players.iter().any(|player| player.discard.iter().any(|&card_id| card_id == cid));

    match zone_mask as i32 {
        ZONE_MASK_STAGE => in_stage,
        ZONE_MASK_HAND => in_hand,
        ZONE_MASK_DISCARD => in_discard,
        _ => true,
    }
}

pub fn map_filter_string_to_attr(filter: &str) -> u64 {
    let (parsed, extras) = filter_from_semantic_string(filter);
    parsed.to_attr() | extras
}

fn apply_keyword_param(
    filter: &mut CardFilter,
    extras: &mut u64,
    keyword: &str,
    group_id: Option<u64>,
) {
    match keyword.to_ascii_uppercase().as_str() {
        "PLAYED_THIS_TURN" | "COUNT_PLAYED_THIS_TURN" => {
            *extras |= KEYWORD_PLAYED_THIS_TURN;
        }
        "YELL_COUNT" | "COUNT_YELL_REVEALED" => {
            *extras |= KEYWORD_YELL_COUNT;
        }
        "HAS_LIVE_SET" => {
            *extras |= KEYWORD_HAS_LIVE_SET;
        }
        "UNIQUE_NAMES" | "COUNT_UNIQUE_NAMES" => {
            filter.is_enabled = true;
            filter.unique_names = true;
        }
        "DID_ACTIVATE_ENERGY"
        | "DID_ACTIVATE_ENERGY_BY_GROUP"
        | "DID_ACTIVATE_ENERGY_BY_MEMBER_EFFECT"
        | "ACTIVATED_ENERGY" => {
            filter.is_enabled = true;
            filter.keyword_energy = true;
            if let Some(group_id) = group_id {
                filter.group_enabled = true;
                filter.group_id = (group_id & 0x7F) as u8;
            }
        }
        "DID_ACTIVATE_MEMBER"
        | "DID_ACTIVATE_MEMBER_BY_GROUP"
        | "DID_ACTIVATE_MEMBER_BY_MEMBER_EFFECT"
        | "ACTIVATED_MEMBER" => {
            filter.is_enabled = true;
            filter.keyword_member = true;
            if let Some(group_id) = group_id {
                filter.group_enabled = true;
                filter.group_id = (group_id & 0x7F) as u8;
            }
        }
        "REVEALED_CONTAINS" => {
            *extras |= FILTER_REVEALED_CONTEXT;
        }
        _ => {}
    }
}

pub fn filter_parts_from_params(params: Option<&serde_json::Value>) -> Option<(CardFilter, u64)> {
    let obj = params_object(params)?;
    let mut filter = CardFilter::default();
    let mut extras = 0u64;

    macro_rules! set_flag {
        ($value:expr, $field:ident) => {
            if let Some(value) = $value {
                if as_bool_robust(value) {
                    filter.is_enabled = true;
                    filter.$field = true;
                }
            }
        };
    }

    if let Some(target_player) = obj
        .get("target_player")
        .or_else(|| obj.get("player"))
        .or_else(|| obj.get("PLAYER"))
        .and_then(parse_target_player_value)
    {
        filter.is_enabled = true;
        filter.target_player = target_player;
    }
    if let Some(card_type) = obj
        .get("card_type")
        .or_else(|| obj.get("CARD_TYPE"))
        .and_then(parse_card_type_value)
    {
        filter.is_enabled = true;
        filter.card_type = card_type;
    }
    set_flag!(obj.get("group_enabled"), group_enabled);
    if let Some(group_id) = obj
        .get("group_id")
        .or_else(|| obj.get("GROUP_ID"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = (group_id & 0x7F) as u8;
    }
    set_flag!(obj.get("is_tapped"), is_tapped);
    set_flag!(obj.get("has_blade_heart"), has_blade_heart);
    set_flag!(obj.get("not_has_blade_heart"), not_has_blade_heart);
    set_flag!(obj.get("unique_names"), unique_names);
    set_flag!(obj.get("unit_enabled"), unit_enabled);
    if let Some(unit_id) = obj
        .get("unit_id")
        .or_else(|| obj.get("UNIT_ID"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.unit_enabled = true;
        filter.unit_id = (unit_id & 0x7F) as u8;
    }
    set_flag!(obj.get("value_enabled"), value_enabled);
    if let Some(threshold) = obj
        .get("value_threshold")
        .and_then(Value::as_u64)
        .or_else(|| {
            obj.get("heart_count")
                .or_else(|| obj.get("min_count"))
                .or_else(|| obj.get("min"))
                .or_else(|| obj.get("count"))
                .or_else(|| obj.get("threshold"))
                .or_else(|| obj.get("value"))
                .and_then(Value::as_u64)
        })
    {
        filter.is_enabled = true;
        filter.value_enabled = true;
        filter.value_threshold = (threshold & 0x1F) as u8;
    }
    set_flag!(obj.get("is_le"), is_le);
    set_flag!(obj.get("is_cost_type"), is_cost_type);
    if let Some(color_mask) = obj
        .get("heart_color")
        .or_else(|| obj.get("heart_type"))
        .and_then(semantic_heart_mask_from_value)
    {
        filter.is_enabled = true;
        filter.value_enabled = true;
        filter.color_mask = color_mask;
    }
    if let Some(color_mask) = obj
        .get("color_mask")
        .or_else(|| obj.get("COLOR_MASK"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.color_mask = color_mask as u8;
    }
    if let Some(char_id) = obj
        .get("char_id_1")
        .or_else(|| obj.get("CHAR_ID_1"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.char_id_1 = (char_id & 0x7F) as u8;
    }
    if let Some(char_id) = obj
        .get("char_id_2")
        .or_else(|| obj.get("CHAR_ID_2"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.char_id_2 = (char_id & 0x7F) as u8;
    }
    if let Some(char_id) = obj
        .get("char_id_3")
        .or_else(|| obj.get("CHAR_ID_3"))
        .and_then(Value::as_u64)
    {
        filter.is_enabled = true;
        filter.char_id_3 = (char_id & 0x7F) as u8;
    }
    if let Some(zone_mask) = obj
        .get("zone_mask")
        .or_else(|| obj.get("ZONE_MASK"))
        .and_then(parse_zone_mask_value)
    {
        filter.is_enabled = true;
        filter.zone_mask = zone_mask;
    }
    if let Some(special_id) = obj
        .get("special_id")
        .or_else(|| obj.get("SPECIAL_ID"))
        .and_then(parse_special_id_value)
    {
        filter.is_enabled = true;
        filter.special_id = special_id;
    }
    if let Some(area) = obj
        .get("area")
        .or_else(|| obj.get("AREA"))
        .and_then(Value::as_str)
    {
        if area.eq_ignore_ascii_case("ANY_STAGE") || area.eq_ignore_ascii_case("ALL_AREAS") {
            extras |= FILTER_ANY_STAGE;
        }
    }
    set_flag!(obj.get("is_setsuna"), is_setsuna);
    set_flag!(obj.get("compare_accumulated"), compare_accumulated);
    set_flag!(
        obj.get("is_optional")
            .or_else(|| obj.get("optional"))
            .or_else(|| obj.get("IS_OPTIONAL")),
        is_optional
    );
    set_flag!(obj.get("keyword_energy"), keyword_energy);
    set_flag!(obj.get("keyword_member"), keyword_member);
    if let Some(keyword) = obj
        .get("keyword")
        .or_else(|| obj.get("KEYWORD"))
        .and_then(Value::as_str)
    {
        apply_keyword_param(
            &mut filter,
            &mut extras,
            keyword,
            obj.get("group_id").and_then(Value::as_u64),
        );
    }

    if let Some(filter_str) = obj
        .get("FILTER")
        .or_else(|| obj.get("filter"))
        .and_then(Value::as_str)
    {
        let normalized = filter_str.trim();
        if normalized.eq_ignore_ascii_case("Umi/Yoshiko/Rina")
            || normalized.eq_ignore_ascii_case("Umi / Yoshiko / Rina")
        {
            return Some((
                CardFilter {
                    is_enabled: true,
                    char_id_1: 4,
                    char_id_2: 16,
                    is_optional: obj
                        .get("is_optional")
                        .or_else(|| obj.get("IS_OPTIONAL"))
                        .map(as_bool_robust)
                        .unwrap_or(true),
                    ..CardFilter::default()
                },
                0,
            ));
        }

        let (parsed, parsed_extras) = filter_from_semantic_string(filter_str);
        filter = parsed.with_overlay(&filter);
        extras |= parsed_extras;
    }

    let attr = filter.to_attr() | extras;
    if attr == 0 {
        None
    } else {
        Some((filter, extras))
    }
}

pub fn filter_from_params(params: Option<&serde_json::Value>) -> Option<CardFilter> {
    filter_parts_from_params(params).and_then(|(filter, _)| {
        if filter == CardFilter::default() {
            None
        } else {
            Some(filter)
        }
    })
}

pub fn filter_attr_from_params(params: Option<&serde_json::Value>) -> Option<u64> {
    filter_parts_from_params(params).map(|(filter, extras)| filter.to_attr() | extras)
}

pub fn merge_filter_attr_with_params(base_attr: u64, params: Option<&serde_json::Value>) -> u64 {
    let base_filter = CardFilter::from_attr(base_attr);
    let base_passthrough = base_attr & !base_filter.to_attr();

    if let Some((params_filter, params_passthrough)) = filter_parts_from_params(params) {
        base_filter.with_overlay(&params_filter).to_attr() | base_passthrough | params_passthrough
    } else {
        base_attr
    }
}

pub(crate) fn parse_target_player_value(value: &Value) -> Option<u8> {
    value
        .as_u64()
        .map(|value| (value & 0x3) as u8)
        .or_else(|| {
            value.as_str().map(|value| match value.to_ascii_uppercase().as_str() {
                "SELF" | "ME" | "PLAYER" => 1,
                "OPPONENT" => 2,
                "BOTH" | "ALL" => 3,
                _ => 0,
            })
        })
}

pub(crate) fn parse_card_type_value(value: &Value) -> Option<u8> {
    value
        .as_u64()
        .map(|value| (value & 0x3) as u8)
        .or_else(|| {
            value.as_str().map(|value| match value.to_ascii_uppercase().as_str() {
                "MEMBER" => 1,
                "LIVE" => 2,
                _ => 0,
            })
        })
}

pub(crate) fn parse_special_id_value(value: &Value) -> Option<u8> {
    value
        .as_u64()
        .map(|value| (value & 0x7) as u8)
        .or_else(|| {
            value.as_str().map(|value| {
                match value
                    .to_ascii_uppercase()
                    .replace('_', " ")
                    .replace('-', " ")
                    .as_str()
                {
                    "BASE COST" => 5,
                    "SELECTED DISCARD" => 6,
                    "SAME NAME" | "SAMENAME" => 4,
                    "NOT MY" | "NOTMY" => 2,
                    "NOT SELF" | "NOTSELF" => 3,
                    _ => 0,
                }
            })
        })
}

pub(crate) fn parse_zone_mask_value(value: &Value) -> Option<u8> {
    value.as_u64().map(|value| (value & 0x7) as u8).or_else(|| {
        value.as_str().and_then(|value| {
            match value.trim().to_ascii_uppercase().replace('_', " ").as_str() {
                "ALL" | "ALL AREAS" => Some(0),
                "STAGE" => Some(ZONE_STAGE as u8),
                "HAND" => Some(ZONE_HAND as u8),
                "DISCARD" => Some(ZONE_DISCARD as u8),
                // Stage-side masks appear in authored data but are not representable in the
                // legacy 3-bit zone field, so keep them non-restrictive instead of inventing bits.
                "GUEST+FRIEND" | "GUEST + FRIEND" => Some(0),
                _ => None,
            }
        })
    })
}

fn group_id_from_name(name: &str) -> Option<u8> {
    match name {
        "HASUNOSORA" | "HASU" => Some(4),
        "LIELLA" => Some(3),
        "NIJIGASAKI" | "NIJIGAKU" | "NIJI" => Some(2),
        "AQOURS" | "AQUOURS" => Some(1),
        "MUSE" | "MUS" | "U'S" | "M'S" => Some(0),
        "ARISE" => Some(10),
        "SAINT_SNOW" => Some(11),
        "SUNNY_PASSION" => Some(12),
        "MUSICAL" => Some(13),
        _ => None,
    }
}

fn unit_id_from_name(name: &str) -> Option<u8> {
    match name {
        "PRINTEMPS" => Some(0),
        "LILY_WHITE" | "LILYWHITE" => Some(1),
        "BIBI" => Some(2),
        "CYARON" => Some(3),
        "AZALEA" => Some(4),
        "GUILTY_KISS" | "GUILTYKISS" => Some(5),
        "DIVER_DIVA" | "DIVERDIVA" => Some(6),
        "A_ZU_NA" | "AZUNA" => Some(7),
        "QU4RTZ" => Some(8),
        "R3BIRTH" => Some(9),
        "CATCHU" => Some(10),
        "KALEIDOSCORE" => Some(11),
        "5YNCRI5E" | "SYNCRISE" => Some(12),
        "CERISE_BOUQUET" | "CERISE" => Some(13),
        "DOLLCHESTRA" | "DOLL" => Some(14),
        "MIRA_CRA_PARK" | "MIRA-CRA" | "MIRAKURA" => Some(15),
        _ => None,
    }
}

fn parse_semantic_heart_filter(part: &str) -> Option<(u8, u8)> {
    let upper = part.trim().to_ascii_uppercase();
    let token = upper.strip_prefix("HAS_").unwrap_or(upper.as_str());
    let token = token
        .strip_prefix("HEART_")
        .or_else(|| token.strip_prefix("COLOR_"))
        .unwrap_or(token);
    let (color_part, threshold_part) = token.rsplit_once("_X").or_else(|| token.rsplit_once('X'))?;

    let color_mask = match color_part {
        "SMILE" | "PINK" | "COLOR_0" | "00" | "0" => 1 << 0,
        "RED" | "COLOR_1" | "01" | "1" => 1 << 1,
        "YELLOW" | "COLOR_2" | "02" | "2" => 1 << 2,
        "GREEN" | "PURE" | "COLOR_3" | "03" | "3" => 1 << 3,
        "BLUE" | "COOL" | "COLOR_4" | "04" | "4" => 1 << 4,
        "PURPLE" | "COLOR_5" | "05" | "5" => 1 << 5,
        "ANY" | "ALL" | "COLOR_7" => 1 << 6,
        _ => return None,
    };

    threshold_part
        .trim_start_matches('_')
        .parse::<u8>()
        .ok()
        .map(|threshold| (color_mask, threshold))
}

fn semantic_heart_mask_from_value(value: &Value) -> Option<u8> {
    value
        .as_u64()
        .and_then(|value| match value {
            0 => Some(1 << 0),
            1 => Some(1 << 1),
            2 => Some(1 << 2),
            3 => Some(1 << 3),
            4 => Some(1 << 4),
            5 => Some(1 << 5),
            6 => Some(1 << 6),
            _ => None,
        })
        .or_else(|| {
            value.as_str().and_then(|value| match value.trim().to_ascii_uppercase().as_str() {
                "PINK" | "SMILE" | "0" | "COLOR_0" => Some(1 << 0),
                "RED" | "1" | "COLOR_1" => Some(1 << 1),
                "YELLOW" | "2" | "COLOR_2" => Some(1 << 2),
                "GREEN" | "PURE" | "3" | "COLOR_3" => Some(1 << 3),
                "BLUE" | "COOL" | "4" | "COLOR_4" => Some(1 << 4),
                "PURPLE" | "5" | "COLOR_5" => Some(1 << 5),
                "ANY" | "ALL" | "6" | "COLOR_7" => Some(1 << 6),
                _ => None,
            })
        })
}

fn apply_string_token(filter: &mut CardFilter, extras: &mut u64, part: &str) {
    let trimmed = part.trim();
    let upper = trimmed.to_ascii_uppercase();
    if upper.is_empty() {
        return;
    }

    match upper.as_str() {
        "OPPONENT" | "TARGET=OPPONENT" | "TARGET_OPPONENT" => {
            filter.is_enabled = true;
            filter.target_player = 2;
            return;
        }
        "SELF" | "ME" | "PLAYER" | "TARGET=SELF" | "TARGET_PLAYER" => {
            filter.is_enabled = true;
            filter.target_player = 1;
            return;
        }
        "BOTH" | "ALL" | "TARGET=BOTH" | "TARGET_ALL" => {
            filter.is_enabled = true;
            filter.target_player = 3;
            return;
        }
        "HAS_GROUP_AQOURS_OR_SAINT_SNOW" => {
            filter.is_enabled = true;
            filter.group_enabled = true;
            filter.group_id = 101;
            return;
        }
        "SAME_NAME_AS_REVEALED" => {
            filter.is_enabled = true;
            filter.special_id = 4;
            return;
        }
        "SELECTED_DISCARD" => {
            filter.is_enabled = true;
            filter.special_id = 6;
            return;
        }
        "TAPPED" | "STATUS=TAPPED" => {
            filter.is_enabled = true;
            filter.is_tapped = true;
            return;
        }
        "HAS_BLADE_HEART" => {
            filter.is_enabled = true;
            filter.has_blade_heart = true;
            return;
        }
        "NOT_HAS_BLADE_HEART" => {
            filter.is_enabled = true;
            filter.not_has_blade_heart = true;
            return;
        }
        "TYPE_MEMBER" => {
            filter.is_enabled = true;
            filter.card_type = 1;
            return;
        }
        "TYPE_LIVE" => {
            filter.is_enabled = true;
            filter.card_type = 2;
            return;
        }
        "UNIQUE_NAMES=TRUE" | "UNIQUE_NAMES" | "SAME_UNIQUE_NAMES" => {
            filter.is_enabled = true;
            filter.unique_names = true;
            return;
        }
        "COST_LE_REVEALED" => {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = 1;
            filter.is_le = true;
            filter.is_cost_type = true;
            *extras |= crate::core::generated_constants::FILTER_REVEALED_CONTEXT;
            return;
        }
        _ => {}
    }

    if trimmed.contains("NAME_IN") {
        filter.is_enabled = true;
        filter.special_id = 1;
        if let Some(eq_pos) = trimmed.find('=') {
            if let Some(first_char) = trimmed[eq_pos + 1..].trim().chars().next() {
                filter.color_mask = (first_char as u8) & 0x7F;
            }
        }
        return;
    }
    if trimmed.contains("NOT_NAME=MY") {
        filter.is_enabled = true;
        filter.special_id = 2;
        return;
    }
    if let Some((color_mask, threshold)) = parse_semantic_heart_filter(trimmed) {
        filter.is_enabled = true;
        filter.value_enabled = true;
        filter.value_threshold = threshold;
        filter.color_mask = color_mask;
        return;
    }
    if upper.starts_with("COST") {
        let value = upper
            .rsplit(['=', '_'])
            .next()
            .and_then(|value| value.parse::<u8>().ok());
        if let Some(threshold) = value {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = threshold;
            filter.is_le = upper.contains("_LE");
            filter.is_cost_type = true;
        }
        return;
    }
    if upper.starts_with("GROUP_ID=") || upper.starts_with("GROUP_ID_") {
        if let Some(group_id) = upper
            .rsplit(['=', '_'])
            .next()
            .and_then(|value| value.parse::<u8>().ok())
        {
            filter.is_enabled = true;
            filter.group_enabled = true;
            filter.group_id = group_id;
        }
        return;
    }
    if upper.starts_with("UNIT_") {
        let unit_name = upper.replace("UNIT_", "").replace("_ONLY", "");
        if let Some(unit_id) = unit_id_from_name(unit_name.as_str()) {
            filter.is_enabled = true;
            filter.unit_enabled = true;
            filter.unit_id = unit_id;
        } else if let Some(group_id) = group_id_from_name(unit_name.as_str()) {
            filter.is_enabled = true;
            filter.group_enabled = true;
            filter.group_id = group_id;
        }
        return;
    }
    if upper.starts_with("BLADE_LE") || upper.starts_with("BLADE_GE") {
        if let Some(threshold) = upper
            .replace("BLADE_LE", "")
            .replace("BLADE_GE", "")
            .replace('_', "")
            .parse::<u8>()
            .ok()
        {
            filter.is_enabled = true;
            filter.value_enabled = true;
            filter.value_threshold = threshold;
            filter.is_le = upper.starts_with("BLADE_LE");
            *extras |= crate::core::generated_constants::FILTER_BLADE_FILTER_FLAG;
        }
        return;
    }

    let color_mask = match upper.as_str() {
        "SMILE" | "PINK" | "COLOR_0" | "HEART_PINK" => Some(1 << 0),
        "RED" | "COLOR_1" => Some(1 << 1),
        "YELLOW" | "COLOR_2" => Some(1 << 2),
        "PURE" | "GREEN" | "COLOR_3" => Some(1 << 3),
        "COOL" | "BLUE" | "COLOR_4" | "HEART_BLUE" => Some(1 << 4),
        "PURPLE" | "COLOR_5" => Some(1 << 5),
        "ANY" | "COLOR_7" => Some(1 << 6),
        _ => None,
    };
    if let Some(color_mask) = color_mask {
        filter.is_enabled = true;
        filter.color_mask |= color_mask;
        return;
    }

    if let Some(group_id) = group_id_from_name(upper.as_str()) {
        filter.is_enabled = true;
        filter.group_enabled = true;
        filter.group_id = group_id;
    }
}

fn filter_from_semantic_string(filter: &str) -> (CardFilter, u64) {
    let mut parsed = CardFilter::default();
    let mut extras = 0u64;
    for part in filter.split(',') {
        apply_string_token(&mut parsed, &mut extras, part);
    }
    (parsed, extras)
}

fn as_bool_robust(value: &Value) -> bool {
    value
        .as_bool()
        .unwrap_or_else(|| value.as_i64().map(|value| value != 0).unwrap_or(false))
}

fn params_object<'a>(params: Option<&'a Value>) -> Option<&'a serde_json::Map<String, Value>> {
    let mut obj = params.and_then(Value::as_object)?;
    if let Some(sub_obj) = obj
        .get("attr")
        .or_else(|| obj.get("filter"))
        .and_then(Value::as_object)
    {
        obj = sub_obj;
    }
    Some(obj)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::card_db::{LiveCard, MemberCard};
    use serde_json::json;

    fn test_db_with_runtime_cards() -> CardDatabase {
        let mut db = CardDatabase::default();

        let mut muse_member = MemberCard::default();
        muse_member.card_id = 100;
        muse_member.name = "Muse Setsuna".to_string();
        muse_member.normalized_name = "MuseSetsuna".to_string();
        muse_member.cost = 3;
        muse_member.hearts = [1, 1, 0, 0, 0, 0, 0];
        muse_member.groups = vec![0];
        muse_member.units = vec![5];
        muse_member.char_mask = (1u128 << 27) | (1u128 << 32);
        muse_member.semantic_flags = 0x100;
        db.members.insert(100, muse_member.clone());

        let mut blade_live = LiveCard::default();
        blade_live.card_id = 200;
        blade_live.name = "Blade Live".to_string();
        blade_live.normalized_name = "BladeLive".to_string();
        blade_live.required_hearts = [2, 2, 0, 0, 0, 0, 0];
        blade_live.blade_hearts = [0, 0, 0, 0, 1, 0, 0];
        blade_live.groups = vec![1, 11];
        blade_live.units = vec![5];
        blade_live.char_mask = 1u128 << 32;
        db.lives.insert(200, blade_live.clone());

        db
    }

    #[test]
    fn filter_parts_from_params_support_keyword_area_and_player_aliases() {
        let params = json!({
            "player": "OPPONENT",
            "area": "ANY_STAGE",
            "keyword": "COUNT_UNIQUE_NAMES"
        });

        let (filter, extras) = filter_parts_from_params(Some(&params)).unwrap();

        assert_eq!(filter.target_player, TARGET_PLAYER_OPPONENT as u8);
        assert!(filter.unique_names);
        assert_ne!(extras & FILTER_ANY_STAGE, 0);
    }

    #[test]
    fn merge_filter_attr_with_params_preserves_passthrough_and_overlays_filter_bits() {
        let base_attr = FILTER_REVEALED_CONTEXT | TARGET_PLAYER_SELF as u64;
        let params = json!({
            "player": "OPPONENT",
            "keyword": "DID_ACTIVATE_MEMBER",
            "group_id": 3
        });

        let merged = merge_filter_attr_with_params(base_attr, Some(&params));
        let merged_filter = CardFilter::from_attr(merged);

        assert_eq!(merged_filter.target_player, TARGET_PLAYER_OPPONENT as u8);
        assert!(merged_filter.keyword_member);
        assert!(merged_filter.group_enabled);
        assert_eq!(merged_filter.group_id, 3);
        assert_ne!(merged & FILTER_REVEALED_CONTEXT, 0);
    }

    #[test]
    fn matches_enforces_group_char_zone_and_flag_filters() {
        let db = test_db_with_runtime_cards();
        let mut state = GameState::default();
        state.players[0].stage[0] = 100;
        state.players[0].discard.push(200);

        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: 999,
            selected_cards: vec![200].into(),
            ..AbilityContext::default()
        };

        let muse_group = CardFilter {
            is_enabled: true,
            group_enabled: true,
            group_id: 0,
            ..CardFilter::default()
        };
        assert!(muse_group.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

        let char_filter = CardFilter {
            is_enabled: true,
            char_id_1: 27,
            ..CardFilter::default()
        };
        assert!(char_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
        assert!(!char_filter.matches(&state, &db, 200, None, false, None, &ctx));

        let setsuna_filter = CardFilter {
            is_enabled: true,
            is_setsuna: true,
            ..CardFilter::default()
        };
        assert!(setsuna_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
        assert!(!setsuna_filter.matches(&state, &db, 200, None, false, None, &ctx));

        let discard_zone_filter = CardFilter {
            is_enabled: true,
            zone_mask: ZONE_DISCARD as u8,
            ..CardFilter::default()
        };
        assert!(discard_zone_filter.matches(&state, &db, 200, None, false, None, &ctx));
        assert!(!discard_zone_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

        let selected_discard_filter = CardFilter {
            is_enabled: true,
            special_id: 6,
            ..CardFilter::default()
        };
        assert!(selected_discard_filter.matches(&state, &db, 200, None, false, None, &ctx));
        assert!(!selected_discard_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));

        let blade_filter = CardFilter {
            is_enabled: true,
            has_blade_heart: true,
            ..CardFilter::default()
        };
        assert!(blade_filter.matches(&state, &db, 200, None, false, None, &ctx));
        assert!(!blade_filter.matches(&state, &db, 100, Some((0, 0)), false, None, &ctx));
    }

    #[test]
    fn matches_uses_member_cost_even_with_effective_hearts() {
        let mut db = CardDatabase::default();
        let mut member = MemberCard::default();
        member.card_id = 300;
        member.cost = 4;
        member.hearts = [0, 0, 0, 0, 0, 0, 0];
        db.members.insert(300, member);

        let state = GameState::default();
        let ctx = AbilityContext::default();
        let filter = CardFilter {
            is_enabled: true,
            value_enabled: true,
            value_threshold: 4,
            is_cost_type: true,
            ..CardFilter::default()
        };
        let inflated_hearts = [9, 9, 9, 9, 9, 9, 9];

        assert!(filter.matches(&state, &db, 300, None, false, Some(&inflated_hearts), &ctx));

        let strict_filter = CardFilter {
            value_threshold: 3,
            is_le: true,
            ..filter
        };
        assert!(!strict_filter.matches(&state, &db, 300, None, false, Some(&inflated_hearts), &ctx));
    }

    #[test]
    fn filter_parts_from_params_parse_string_special_and_zone_masks() {
        let params = json!({
            "special_id": "Base Cost",
            "zone_mask": "DISCARD",
            "player": "OPPONENT"
        });

        let (filter, _) = filter_parts_from_params(Some(&params)).unwrap();

        assert_eq!(filter.special_id, 5);
        assert_eq!(filter.zone_mask, ZONE_DISCARD as u8);
        assert_eq!(filter.target_player, TARGET_PLAYER_OPPONENT as u8);
    }
}
