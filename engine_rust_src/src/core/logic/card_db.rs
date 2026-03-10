//! # LovecaSim Card Database
//!
//! This module defines the `CardDatabase` which acts as the source of truth for
//! card statistics, images, and bytecode instructions.
//!
//! ## Key Roles:
//! - **Centralized Card Data**: Stores `MemberCard` and `LiveCard` structures.
//! - **Fast Lookups**: Implements a `card_no_to_id` mapping for O(1) lookups by
//!   collector number (e.g., "LL-bp1-001").
//! - **Data Integrity**: Ensures that card IDs are unique and that all referenced
//!   metadata exists.
//!
//! ## Design Strategy:
//! The `CardDatabase` is typically loaded once at startup and shared across
//! game instances. Test helpers like `create_test_db` provide a minimal subset
//! for unit testing.

use crate::core::enums::*;
use crate::core::hearts::HeartBoard;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
// use crate::core::generated_constants::*; // Redundant due to enums.rs re-export
// use crate::core::generated_constants::*; // Re-exported by enums.rs
use super::models::*;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MemberCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub cost: u32,
    pub hearts: [u8; 7],
    pub blade_hearts: [u8; 7],
    pub blades: u32,
    pub groups: Vec<u8>,
    pub units: Vec<u8>,
    pub abilities: Vec<Ability>,
    #[serde(alias = "volume_icons")]
    pub note_icons: u32,
    pub draw_icons: u32,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub char_id: u32,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub rarity: u8,
    #[serde(default)]
    pub semantic_flags: u32,
    #[serde(default)]
    pub ability_flags: u64,
    #[serde(default)]
    pub synergy_flags: u32,
    #[serde(default)]
    pub cost_flags: u32,
    #[serde(default)]
    pub hearts_board: HeartBoard,
    #[serde(default)]
    pub blade_hearts_board: HeartBoard,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct LiveCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub score: u32,
    pub required_hearts: [u8; 7],
    pub abilities: Vec<Ability>,
    pub groups: Vec<u8>,
    pub units: Vec<u8>,
    #[serde(alias = "volume_icons")]
    pub note_icons: u32,
    pub blade_hearts: [u8; 7],
    #[serde(default)]
    pub rare: String,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub semantic_flags: u32,
    #[serde(default)]
    pub synergy_flags: u32,
    #[serde(default)]
    pub hearts_board: HeartBoard,
    #[serde(default)]
    pub blade_hearts_board: HeartBoard,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Card {
    Member(MemberCard),
    Live(LiveCard),
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CardDatabase {
    pub members: HashMap<i32, MemberCard>,
    pub lives: HashMap<i32, LiveCard>,
    // Optimization 1: Fast Lookup Vectors
    pub members_vec: Vec<Option<MemberCard>>,
    pub lives_vec: Vec<Option<LiveCard>>,
    // Optimization 2: String No Lookup
    pub card_no_to_id: HashMap<String, i32>,
    pub energy_db: HashMap<i32, EnergyCard>,
    #[serde(default)]
    pub is_vanilla: bool,
}

pub const LOGIC_ID_MASK: i32 = 0x0FFF;

impl CardDatabase {
    /// Extract the logical ID (0-4095) from a packed card ID.
    pub fn to_logic_id(packed_id: i32) -> usize {
        (packed_id & LOGIC_ID_MASK) as usize
    }

    /// Extract the variant index (0-15) from a packed card ID.
    pub fn to_variant_idx(packed_id: i32) -> u8 {
        ((packed_id >> 12) & 0x0F) as u8
    }
}

impl Default for CardDatabase {
    fn default() -> Self {
        Self {
            members: HashMap::new(),
            lives: HashMap::new(),
            members_vec: vec![None; 4096],
            lives_vec: vec![None; 4096],
            card_no_to_id: HashMap::new(),
            energy_db: HashMap::new(),
            is_vanilla: false,
        }
    }
}

impl CardDatabase {
    pub fn from_json(json_str: &str) -> serde_json::Result<Self> {
        let raw: serde_json::Value = serde_json::from_str(json_str)?;
        Self::from_value(raw)
    }

    pub fn from_value(raw: serde_json::Value) -> serde_json::Result<Self> {
        let mut db = Self {
            members: HashMap::new(),
            lives: HashMap::new(),
            members_vec: vec![None; 4096],
            lives_vec: vec![None; 4096],
            card_no_to_id: HashMap::new(),
            energy_db: HashMap::new(),
            is_vanilla: false,
        };

        if let Some(members_raw) = raw.get("member_db").and_then(|m| m.as_object()) {
            for (_, val) in members_raw {
                match serde_json::from_value::<MemberCard>(val.clone()) {
                    Ok(mut card) => {
                        // Trust pre-computed flags if present (non-zero)
                        if card.ability_flags == 0 && card.semantic_flags == 0 {
                            // Pre-compute ability flags
                            let mut flags = 0u64;
                            let mut s_flags = 0u32;
                            for ab in &mut card.abilities {
                                if Self::has_opcode_static_fast(&ab.bytecode, O_RETURN as i32)
                                    || Self::has_opcode_static_fast(
                                        &ab.bytecode,
                                        O_LOOK_AND_CHOOSE as i32,
                                    )
                                {
                                    flags |= FLAG_DRAW as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_SEARCH_DECK as i32)
                                {
                                    flags |= FLAG_SEARCH as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_RECOVER_LIVE as i32)
                                    || Self::has_opcode_static_fast(
                                        &ab.bytecode,
                                        O_RECOVER_MEMBER as i32,
                                    )
                                {
                                    flags |= FLAG_RECOVER as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_ADD_BLADES as i32)
                                    || Self::has_opcode_static_fast(
                                        &ab.bytecode,
                                        O_ADD_HEARTS as i32,
                                    )
                                {
                                    flags |= FLAG_BUFF as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_MOVE_MEMBER as i32)
                                    || Self::has_opcode_static_fast(
                                        &ab.bytecode,
                                        O_SWAP_CARDS as i32,
                                    )
                                {
                                    flags |= FLAG_MOVE as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_TAP_OPPONENT as i32)
                                    || Self::has_opcode_static_fast(
                                        &ab.bytecode,
                                        O_TAP_MEMBER as i32,
                                    )
                                {
                                    flags |= FLAG_TAP as u64;
                                }
                                if Self::has_opcode_static_fast(
                                    &ab.bytecode,
                                    O_ENERGY_CHARGE as i32,
                                ) {
                                    flags |= FLAG_CHARGE as u64;
                                }
                                if Self::has_opcode_static_fast(
                                    &ab.bytecode,
                                    O_ACTIVATE_MEMBER as i32,
                                ) || Self::has_opcode_static_fast(
                                    &ab.bytecode,
                                    O_SET_TAPPED as i32,
                                ) {
                                    flags |= FLAG_TEMPO as u64;
                                }

                                if Self::has_opcode_static_fast(&ab.bytecode, O_REDUCE_COST as i32)
                                {
                                    flags |= FLAG_REDUCE as u64;
                                }
                                if Self::has_opcode_static_fast(&ab.bytecode, O_BOOST_SCORE as i32)
                                {
                                    flags |= FLAG_BOOST as u64;
                                }
                                if Self::has_opcode_static_fast(
                                    &ab.bytecode,
                                    O_TRANSFORM_COLOR as i32,
                                ) {
                                    flags |= FLAG_TRANSFORM as u64;
                                }
                                if Self::has_opcode_static_fast(
                                    &ab.bytecode,
                                    O_REDUCE_HEART_REQ as i32,
                                ) {
                                    flags |= FLAG_WIN_COND as u64;
                                }

                                if ab.trigger == TriggerType::OnPlay {
                                    s_flags |= 0x01;
                                }
                                if ab.trigger == TriggerType::Activated {
                                    s_flags |= 0x02;
                                }
                                if ab.trigger == TriggerType::TurnStart
                                    || ab.trigger == TriggerType::TurnEnd
                                {
                                    s_flags |= 0x04;
                                }
                                if ab.is_once_per_turn {
                                    s_flags |= 0x08;
                                }

                                // Compute Choice Flags and counts, and Ability Flags
                                let mut ability_flags_for_ab = 0u64;
                                let mut unflagged_logic_present = false;
                                let flagged_ops = [
                                    O_DRAW,
                                    O_RECOVER_MEMBER,
                                    O_RECOVER_LIVE,
                                    O_ADD_BLADES,
                                    O_ADD_HEARTS,
                                    O_SEARCH_DECK,
                                    O_BOOST_SCORE,
                                    O_ENERGY_CHARGE,
                                    O_MOVE_MEMBER,
                                    O_SWAP_CARDS,
                                    O_TAP_OPPONENT,
                                    O_MODIFY_SCORE_RULE,
                                    O_REDUCE_COST,
                                    O_REDUCE_HEART_REQ,
                                    O_RETURN,
                                    O_LOOK_AND_CHOOSE,
                                    O_TAP_MEMBER,
                                    O_ACTIVATE_MEMBER,
                                    O_SET_TAPPED,
                                    O_TRANSFORM_COLOR,
                                ];

                                for chunk in ab.bytecode.chunks(5) {
                                    if chunk.is_empty() {
                                        continue;
                                    }
                                    let op = chunk[0];

                                    // Ability Flags
                                    match op {
                                        O_RETURN | O_LOOK_AND_CHOOSE => {
                                            ability_flags_for_ab |= FLAG_DRAW as u64
                                        }
                                        O_SEARCH_DECK => ability_flags_for_ab |= FLAG_SEARCH as u64,
                                        O_RECOVER_LIVE | O_RECOVER_MEMBER => {
                                            ability_flags_for_ab |= FLAG_RECOVER as u64
                                        }
                                        O_ADD_BLADES | O_ADD_HEARTS => {
                                            ability_flags_for_ab |= FLAG_BUFF as u64
                                        }
                                        O_MOVE_MEMBER | O_SWAP_CARDS => {
                                            ability_flags_for_ab |= FLAG_MOVE as u64
                                        }
                                        O_TAP_OPPONENT | O_TAP_MEMBER => {
                                            ability_flags_for_ab |= FLAG_TAP as u64
                                        }
                                        O_ENERGY_CHARGE => {
                                            ability_flags_for_ab |= FLAG_CHARGE as u64
                                        }
                                        O_ACTIVATE_MEMBER | O_SET_TAPPED => {
                                            ability_flags_for_ab |= FLAG_TEMPO as u64
                                        }
                                        O_REDUCE_COST => ability_flags_for_ab |= FLAG_REDUCE as u64,
                                        O_BOOST_SCORE => ability_flags_for_ab |= FLAG_BOOST as u64,
                                        O_TRANSFORM_COLOR => {
                                            ability_flags_for_ab |= FLAG_TRANSFORM as u64
                                        }
                                        O_REDUCE_HEART_REQ => {
                                            ability_flags_for_ab |= FLAG_WIN_COND as u64
                                        }
                                        _ => {}
                                    }

                                    // Choice Flags
                                    match op {
                                        O_LOOK_AND_CHOOSE => {
                                            ab.choice_flags |= CHOICE_FLAG_LOOK;
                                            // choice_count for UI: Unpack from v (Byte 2) or default to 3
                                            if ab.choice_count == 0 {
                                                let v = chunk.get(1).copied().unwrap_or(0);
                                                let pick = (v >> 8) & 0xFF;
                                                ab.choice_count =
                                                    if pick > 0 { pick as u8 } else { 3 };
                                            }
                                        }
                                        O_SELECT_MODE => {
                                            ab.choice_flags |= CHOICE_FLAG_MODE;
                                            if ab.choice_count == 0 {
                                                ab.choice_count =
                                                    chunk.get(1).copied().unwrap_or(2) as u8;
                                            }
                                        }
                                        O_COLOR_SELECT => {
                                            ab.choice_flags |= CHOICE_FLAG_COLOR;
                                            if ab.choice_count == 0 {
                                                ab.choice_count = 6;
                                            }
                                        }
                                        O_ORDER_DECK => {
                                            ab.choice_flags |= CHOICE_FLAG_ORDER;
                                            if ab.choice_count == 0 {
                                                ab.choice_count = 3;
                                            }
                                        }
                                        _ => {}
                                    }

                                    // Check for unflagged logic (semantic extension)
                                    if !flagged_ops.contains(&op) {
                                        unflagged_logic_present = true;
                                    }
                                }
                                flags |= ability_flags_for_ab; // Accumulate ability flags for the card

                                if unflagged_logic_present {
                                    s_flags |= 0x10;
                                }

                                // Compute Synergy Flags
                                let mut syn_flags = 0u32;
                                for c in &ab.conditions {
                                    match c.condition_type {
                                        ConditionType::CountGroup | ConditionType::SelfIsGroup => {
                                            syn_flags |= SYN_FLAG_GROUP
                                        }
                                        ConditionType::HasColor => syn_flags |= SYN_FLAG_COLOR,
                                        ConditionType::Baton => syn_flags |= SYN_FLAG_BATON,
                                        ConditionType::IsCenter => syn_flags |= SYN_FLAG_CENTER,
                                        ConditionType::LifeLead => syn_flags |= SYN_FLAG_LIFE_LEAD,
                                        _ => {}
                                    }
                                }
                                card.synergy_flags |= syn_flags;

                                // Compute Cost Flags
                                let mut c_flags = 0u32;
                                for c in &ab.costs {
                                    match c.cost_type {
                                        AbilityCostType::DiscardHand
                                        | AbilityCostType::DiscardMember => {
                                            c_flags |= COST_FLAG_DISCARD as u32
                                        }
                                        AbilityCostType::TapSelf | AbilityCostType::TapMember => {
                                            c_flags |= COST_FLAG_TAP as u32
                                        }
                                        _ => {}
                                    }
                                }
                                card.cost_flags |= c_flags;
                            }
                            card.ability_flags = flags;
                            card.semantic_flags |= s_flags; // Apply accumulated semantic flags
                        }

                        // HeartBoard population (always needed if deserialized as default/0)
                        if card.hearts_board.0 == 0 {
                            card.hearts_board = HeartBoard::from_array(&card.hearts);
                        }
                        if card.blade_hearts_board.0 == 0 {
                            card.blade_hearts_board = HeartBoard::from_array(&card.blade_hearts);
                        }

                        db.members.insert(card.card_id, card.clone());
                        db.card_no_to_id.insert(card.card_no.clone(), card.card_id);

                        // Populate Vector (Logic Deduplication)
                        let logic_id = Self::to_logic_id(card.card_id);
                        if logic_id < db.members_vec.len() {
                            if db.members_vec[logic_id].is_none()
                                || Self::to_variant_idx(card.card_id) == 0
                            {
                                db.members_vec[logic_id] = Some(card.clone());
                            }
                        }
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Member card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        if let Some(lives_raw) = raw.get("live_db").and_then(|l| l.as_object()) {
            for (_, val) in lives_raw {
                match serde_json::from_value::<LiveCard>(val.clone()) {
                    Ok(mut card) => {
                        if card.semantic_flags == 0 {
                            let mut s_flags = 0u32;
                            for ab in &card.abilities {
                                if ab.trigger == TriggerType::OnPlay {
                                    s_flags |= 0x01;
                                }

                                let mut syn_flags = 0u32;
                                for c in &ab.conditions {
                                    match c.condition_type {
                                        ConditionType::CountGroup | ConditionType::SelfIsGroup => {
                                            syn_flags |= SYN_FLAG_GROUP
                                        }
                                        ConditionType::HasColor => syn_flags |= SYN_FLAG_COLOR,
                                        ConditionType::Baton => syn_flags |= SYN_FLAG_BATON,
                                        ConditionType::IsCenter => syn_flags |= SYN_FLAG_CENTER,
                                        ConditionType::LifeLead => syn_flags |= SYN_FLAG_LIFE_LEAD,
                                        _ => {}
                                    }
                                }
                                card.synergy_flags |= syn_flags;
                            }
                            card.semantic_flags = s_flags;
                        }

                        if card.hearts_board.0 == 0 {
                            card.hearts_board = HeartBoard::from_array(&card.required_hearts);
                        }
                        if card.blade_hearts_board.0 == 0 {
                            card.blade_hearts_board = HeartBoard::from_array(&card.blade_hearts);
                        }

                        db.lives.insert(card.card_id, card.clone());
                        db.card_no_to_id.insert(card.card_no.clone(), card.card_id);

                        // Populate Vector (Logic Deduplication)
                        let logic_id = Self::to_logic_id(card.card_id);
                        if logic_id < db.lives_vec.len() {
                            if db.lives_vec[logic_id].is_none()
                                || Self::to_variant_idx(card.card_id) == 0
                            {
                                db.lives_vec[logic_id] = Some(card.clone());
                            }
                        }
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Live card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        if let Some(energy_raw) = raw.get("energy_db").and_then(|e| e.as_object()) {
            for (_, val) in energy_raw {
                match serde_json::from_value::<EnergyCard>(val.clone()) {
                    Ok(card) => {
                        db.energy_db.insert(card.card_id, card);
                    }
                    Err(e) => {
                        println!(
                            "[DB] ERROR: Failed to parse Energy card {}: {}",
                            val["card_no"], e
                        );
                    }
                }
            }
        }

        Ok(db)
    }

    // Fast Lookups
    pub fn get_member(&self, id: i32) -> Option<&MemberCard> {
        let template_id = id;
        if let Some(m) = self.members.get(&template_id) {
            return Some(m);
        }
        // Collision protection: If this ID is known to be a Live card, it can't be a member variant.
        if self.lives.contains_key(&id) {
            return None;
        }

        let logic_id = Self::to_logic_id(id);
        if logic_id < self.members_vec.len() {
            if let Some(m) = &self.members_vec[logic_id] {
                // Verify this logic entry actually belongs to a Member variant space
                // (This is a heuristic, but checking lives.contains_key above is the primary guard)
                return Some(m);
            }
        }
        None
    }

    pub fn get_live(&self, id: i32) -> Option<&LiveCard> {
        let template_id = id;
        if let Some(l) = self.lives.get(&template_id) {
            return Some(l);
        }
        // Collision protection
        if self.members.contains_key(&id) {
            return None;
        }

        let logic_id = Self::to_logic_id(id);
        if logic_id < self.lives_vec.len() {
            if let Some(l) = &self.lives_vec[logic_id] {
                return Some(l);
            }
        }
        None
    }

    pub fn id_by_no(&self, card_no: &str) -> Option<i32> {
        self.card_no_to_id.get(card_no).copied()
    }

    pub fn get_name(&self, id: i32) -> Option<String> {
        if let Some(m) = self.get_member(id) {
            return Some(m.name.clone());
        }
        if let Some(l) = self.get_live(id) {
            return Some(l.name.clone());
        }
        None
    }
    // Static opcode check
    pub fn has_opcode_static(bytecode: &[i32], target_op: i32) -> bool {
        let mut i = 0;
        while i < bytecode.len() {
            if i + 4 >= bytecode.len() {
                break;
            }
            let op = bytecode[i];
            if op == target_op {
                return true;
            }
            i += 5;
        }
        false
    }

    // Optimized opcode check that just checks 0th element of chunks(5)
    pub fn has_opcode_static_fast(bytecode: &[i32], target_op: i32) -> bool {
        let len = bytecode.len();
        let mut i = 0;
        while i < len {
            if bytecode[i] == target_op {
                return true;
            }
            i += 5;
        }
        false
    }

    pub fn to_binary(&self) -> bincode::Result<Vec<u8>> {
        bincode::serialize(self)
    }

    pub fn from_binary(data: &[u8]) -> bincode::Result<Self> {
        bincode::deserialize(data)
    }
}

pub fn bytecode_has_choice(bytecode: &[i32]) -> bool {
    bytecode.chunks(5).any(|chunk| {
        if chunk.is_empty() {
            return false;
        }
        let op = chunk[0];
        op == O_SELECT_MODE
            || op == O_LOOK_AND_CHOOSE
            || op == O_COLOR_SELECT
            || op == O_TAP_OPPONENT
            || op == O_ORDER_DECK
            || op == O_PLAY_MEMBER_FROM_HAND
            || op == O_PLAY_MEMBER_FROM_DISCARD
            || op == O_OPPONENT_CHOOSE
    })
}

pub fn bytecode_needs_early_pause(bytecode: &[i32]) -> bool {
    bytecode.chunks(5).any(|chunk| {
        if chunk.is_empty() {
            return false;
        }
        let op = chunk[0];
        op == O_SELECT_MODE || op == O_COLOR_SELECT || op == O_LOOK_AND_CHOOSE
    })
}

pub fn bytecode_needs_early_pause_opcode(bytecode: &[i32]) -> i32 {
    bytecode
        .chunks(5)
        .find(|chunk| {
            if chunk.is_empty() {
                return false;
            }
            let op = chunk[0];
            op == O_SELECT_MODE || op == O_COLOR_SELECT || op == O_LOOK_AND_CHOOSE
        })
        .map(|chunk| chunk[0])
        .unwrap_or(-1)
}

pub const CHARACTER_NAMES: [&str; 78] = [
    "", // 0
    "高坂穂乃果",
    "絢瀬絵里",
    "南ことり",
    "園田海未",
    "星空凛", // 1-5
    "西木野真姫",
    "東條希",
    "小泉花陽",
    "矢澤にこ",
    "", // 6-10
    "高海千歌",
    "桜内梨子",
    "松浦果南",
    "黒澤ダイヤ",
    "渡辺曜", // 11-15
    "津島善子",
    "国木田花丸",
    "小原鞠莉",
    "黒澤ルビィ",
    "", // 16-20
    "上原歩夢",
    "中須かすみ",
    "桜坂しずく",
    "朝香果林",
    "宮下愛", // 21-25
    "近江彼方",
    "優木せつ菜",
    "エマ・ヴェルデ",
    "天王寺璃奈",
    "三船栞子", // 26-30
    "ミア・テイラー",
    "鐘嵐珠",
    "高咲侑",
    "",
    "",
    "",
    "",
    "",
    "",
    "", // 31-40
    "澁谷かのん",
    "唐可可",
    "嵐千砂都",
    "平安名すみれ",
    "葉月恋", // 41-45
    "桜小路きな子",
    "米女メイ",
    "若菜四季",
    "鬼塚夏美",
    "ウィーン・マルガレーテ", // 46-50
    "鬼塚冬毬",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "",
    "", // 51-60
    "日野下花帆",
    "村野さやか",
    "乙宗梢",
    "夕霧綴理",
    "大沢瑠璃乃", // 61-65
    "藤島慈",
    "百生吟子",
    "徒町小鈴",
    "安養寺姫芽", // 66-69
    "", // 70
    "綺羅ツバサ",
    "統堂英玲奈",
    "優木あんじゅ",
    "聖澤悠奈",
    "柊摩央",
    "鹿角聖良",
    "鹿角理亞", // 71-77
];

pub fn get_character_name(id: u8) -> &'static str {
    CHARACTER_NAMES.get(id as usize).copied().unwrap_or("")
}

pub fn get_trigger_label(trigger: TriggerType) -> &'static str {
    match trigger {
        TriggerType::OnPlay => "【登場】",
        TriggerType::OnLiveStart => "【開始】",
        TriggerType::OnLiveSuccess => "【成功】",
        TriggerType::TurnStart => "【ターン開始】",
        TriggerType::TurnEnd => "【ターン終了】",
        TriggerType::Constant => "【常時】",
        TriggerType::Activated => "【起動】",
        TriggerType::OnLeaves => "【退場】",
        TriggerType::OnReveal => "【公開】",
        TriggerType::OnPositionChange => "【移動】",
        TriggerType::OnAbilityResolve => "【解決】",
        TriggerType::OnAbilitySuccess => "【成功】",
        TriggerType::None => "",
    }
}
