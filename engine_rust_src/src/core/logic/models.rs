use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use crate::core::generated_layout::*;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::{
    parse_comparison_value, parse_remainder_zone_value, parse_target_slot_value, DecodedSlot,
};
use crate::core::logic::interpreter::conditions::common::parse_condition_type;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::borrow::Cow;
use std::hash::{Hash, Hasher};

pub(crate) fn derive_conditions_from_frame_program(program: &FrameProgram) -> Vec<Condition> {
    let mut conditions = Vec::new();
    for frame in &program.frames {
        let components = frame.components();
        let opcode = components.opcode;
        let is_raw_condition = components
            .params
            .and_then(|params| params.as_object())
            .map(|params| params.get("raw_cond").is_some() || params.get("RAW_COND").is_some())
            .unwrap_or(false);
        let is_condition_opcode = is_raw_condition
            || (opcode >= crate::core::logic::constants::CONDITION_START_1
                && opcode <= crate::core::logic::constants::CONDITION_END_1)
            || (opcode >= crate::core::logic::constants::CONDITION_START_2
                && opcode <= crate::core::logic::constants::CONDITION_END_2);
        if !is_condition_opcode {
            continue;
        }

        conditions.push(Condition {
            condition_type: parse_condition_type(opcode),
            value: components.value,
            attr: components.raw_attr,
            target_slot: components.raw_slot as u8,
            is_negated: components.is_negated,
            params: components.params.cloned().unwrap_or_default(),
        });
    }
    conditions
}

/// Flat, uniform runtime ability frame.
///
/// Replaces the old 10-variant enum with a single struct. All ability frame types
/// are now represented by the same five packed fields plus optional `params`.
///
/// * `opcode` – raw opcode value; may include `OPCODE_NEGATION_OFFSET` for negated frames.
///   Use [`is_negated()`] and [`effective_opcode()`] accordingly.
/// * `value`  – packed value/count (depends on opcode).
/// * `attr`   – packed 64-bit filter attribute (see [`CardFilter`]).
/// * `slot`   – packed slot word (see [`DecodedSlot`]).
/// * `is_cost` – true when this frame represents a cost step.
/// * `params` – optional extra JSON params for handlers that need them (usually `null`).
#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct AbilityFrame {
    pub opcode: i32,
    pub value: i32,
    pub attr: u64,
    pub slot: i32,
    pub is_cost: bool,
    pub params: Value,
}

impl<'de> Deserialize<'de> for AbilityFrame {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let raw_value = Value::deserialize(deserializer)?;
        Ok(Self::from_json_value(&raw_value))
    }
}

impl Serialize for AbilityFrame {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        use serde::ser::SerializeMap;
        let size = if self.params.is_null() { 5 } else { 6 };
        let mut map = serializer.serialize_map(Some(size))?;
        map.serialize_entry("opcode", &self.opcode)?;
        map.serialize_entry("value", &self.value)?;
        map.serialize_entry("attr", &self.attr)?;
        map.serialize_entry("slot", &self.slot)?;
        map.serialize_entry("is_cost", &self.is_cost)?;
        if !self.params.is_null() {
            map.serialize_entry("params", &self.params)?;
        }
        map.end()
    }
}

impl Default for AbilityFrame {
    fn default() -> Self {
        AbilityFrame {
            opcode: 0,
            value: 0,
            attr: 0,
            slot: 0,
            is_cost: false,
            params: Value::Null,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct AbilityFrameComponents<'a> {
    pub raw_opcode: i32,
    pub opcode: i32,
    pub value: i32,
    pub filter: CardFilter,
    pub slot: DecodedSlot,
    pub raw_attr: u64,
    pub raw_slot: i32,
    pub is_negated: bool,
    pub is_cost: bool,
    pub params: Option<&'a Value>,
}

impl<'a> AbilityFrameComponents<'a> {
    pub fn resolved_filter_attr(&self) -> u64 {
        if self.raw_attr != 0 {
            self.raw_attr
        } else {
            self.filter.to_attr()
        }
    }

    pub fn targeted_select_member_filter_attr(&self) -> u64 {
        let filter_attr = self.resolved_filter_attr();
        if self.slot.target_slot == crate::core::logic::constants::TARGET_SLOT_STAGE as u8
            && filter_attr != 0
        {
            let mut filter = crate::core::logic::filter::structured_filter_from_attr(filter_attr);
            let passthrough = crate::core::logic::filter::passthrough_filter_attr(filter_attr);
            filter.target_player = TARGET_PLAYER_SELF as u8;
            filter.to_attr() | passthrough
        } else {
            filter_attr
        }
    }

    pub fn comparison_mode(&self) -> SemanticComparisonMode {
        if self.filter.is_le {
            SemanticComparisonMode::LessEqual
        } else {
            SemanticComparisonMode::GreaterEqual
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticCountZone {
    Hand,
    Discard,
    Stage,
    SuccessPile,
    Energy,
}

impl SemanticCountZone {
    pub fn opcode(self) -> i32 {
        match self {
            Self::Hand => C_COUNT_HAND,
            Self::Discard => C_COUNT_DISCARD,
            Self::Stage => C_COUNT_STAGE,
            Self::SuccessPile => C_COUNT_SUCCESS_LIVE,
            Self::Energy => C_COUNT_ENERGY,
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticScaleSource {
    None,
    CountZone(SemanticCountZone),
    SuccessPile,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticComparisonMode {
    GreaterEqual,
    LessEqual,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SemanticDiscardSpec {
    pub requested_count: i32,
    pub source_zone: Zone,
    pub filter_attr: u64,
    pub prompt_filter_attr: u64,
    pub suspend_slot: i32,
    pub is_optional: bool,
    pub allow_under_member_selection: bool,
    pub is_until_size_operation: bool,
    pub embedded_count_opcode: Option<i32>,
    pub same_unit_discard: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SemanticLookAndChooseSpec {
    pub look_count: usize,
    pub choose_count: usize,
    pub source_zone: Zone,
    pub target_slot: u8,
    pub remainder_zone: Zone,
    pub reveal: bool,
    pub remainder_to_discard: bool,
    pub is_optional: bool,
    pub selection_filter: CardFilter,
    pub selection_filter_attr: u64,
    pub suspend_slot: i32,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticRecoveryBranchKind {
    UniqueDiscardLiveNames,
    UniqueDiscardLiveGroups,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub struct SemanticRecoveryBranchSpec {
    pub kind: SemanticRecoveryBranchKind,
    pub minimum: usize,
}

pub fn semantic_recovery_branch_spec_from_params(
    params: Option<&Value>,
) -> Option<SemanticRecoveryBranchSpec> {
    let params = params?.as_object()?;
    let raw_cond = params
        .get("raw_cond")
        .or_else(|| params.get("RAW_COND"))
        .and_then(|value| value.as_str())?;
    let minimum = params
        .get("MIN")
        .or_else(|| params.get("min"))
        .and_then(|value| value.as_i64())
        .unwrap_or(3) as usize;

    let kind = match raw_cond {
        "UNIQUE_DISCARD_LIVE_NAMES_COUNT" => SemanticRecoveryBranchKind::UniqueDiscardLiveNames,
        "UNIQUE_DISCARD_LIVE_GROUPS_COUNT" => SemanticRecoveryBranchKind::UniqueDiscardLiveGroups,
        _ => return None,
    };

    Some(SemanticRecoveryBranchSpec { kind, minimum })
}

impl SemanticLookAndChooseSpec {
    pub fn finalize_destination(&self) -> Zone {
        if self.remainder_to_discard {
            Zone::Discard
        } else if self.remainder_zone != Zone::Default {
            self.remainder_zone
        } else {
            self.source_zone
        }
    }

    pub fn choice_type(&self) -> ChoiceType {
        match self.source_zone {
            Zone::Hand => ChoiceType::SelectHandDiscard,
            Zone::Discard => ChoiceType::SelectDiscardPlay,
            _ => ChoiceType::LookAndChoose,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AbilityTraceStep {
    pub opcode: String,
    pub summary: String,
    #[serde(default)]
    pub is_cost: bool,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub value: Option<i32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub source_zone: Option<Zone>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dest_zone: Option<Zone>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub target_slot: Option<u8>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub choose_count: Option<u8>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub reveal: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub remainder_to_discard: Option<bool>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub filter: Option<CardFilter>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub slot: Option<DecodedSlot>,
    #[serde(default, skip_serializing_if = "Value::is_null")]
    pub params: Value,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub family: Option<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub consumer_paths: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub serialization_fields: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct AbilityDiagnosticsView {
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub source_paths: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub action_routes: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub serialization_paths: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub serialization_fields: Vec<String>,
    #[serde(default, skip_serializing_if = "Vec::is_empty")]
    pub warnings: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct AbilityTraceView {
    pub trigger: TriggerType,
    pub frame_source: String,
    #[serde(default)]
    pub raw_text: String,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default)]
    pub steps: Vec<AbilityTraceStep>,
    #[serde(default)]
    pub diagnostics: AbilityDiagnosticsView,
}

fn trace_opcode_name(opcode: i32) -> String {
    match opcode {
        O_DRAW => "DRAW".to_string(),
        O_MOVE_TO_DISCARD => "MOVE_TO_DISCARD".to_string(),
        O_LOOK_AND_CHOOSE => "LOOK_AND_CHOOSE".to_string(),
        O_RECOVER_LIVE => "RECOVER_LIVE".to_string(),
        O_RECOVER_MEMBER => "RECOVER_MEMBER".to_string(),
        O_SWAP_ZONE => "SWAP_ZONE".to_string(),
        O_RETURN => "RETURN".to_string(),
        O_JUMP => "JUMP".to_string(),
        O_JUMP_IF_FALSE => "JUMP_IF_FALSE".to_string(),
        O_PAY_ENERGY => "PAY_ENERGY".to_string(),
        O_SELECT_MEMBER => "SELECT_MEMBER".to_string(),
        O_ADD_BLADES => "ADD_BLADES".to_string(),
        O_ADD_HEARTS => "ADD_HEARTS".to_string(),
        O_BOOST_SCORE => "BOOST_SCORE".to_string(),
        O_TAP_MEMBER => "TAP_MEMBER".to_string(),
        O_SET_TAPPED => "SET_TAPPED".to_string(),
        O_NOP => "NOP".to_string(),
        _ => format!("OP_{}", opcode),
    }
}

fn trace_step_family(opcode: i32) -> Option<&'static str> {
    match opcode {
        O_PAY_ENERGY | O_PAY_ENERGY_DYNAMIC | O_ACTIVATE_ENERGY | O_MOVE_TO_DISCARD => {
            Some("cost")
        }
        O_LOOK_AND_CHOOSE | O_SELECT_MEMBER | O_SELECT_CARDS | O_SELECT_LIVE | O_SELECT_PLAYER
        | O_SELECT_MODE => Some("selection"),
        O_DRAW | O_RECOVER_LIVE | O_RECOVER_MEMBER | O_MOVE_MEMBER | O_MOVE_TO_DECK
        | O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD | O_SWAP_ZONE => Some("movement"),
        O_BOOST_SCORE | O_ADD_BLADES | O_ADD_HEARTS | O_SET_SCORE | O_REDUCE_SCORE
        | O_REDUCE_COST | O_INCREASE_COST | O_SET_HEART_COST | O_INCREASE_HEART_COST
        | O_REDUCE_HEART_REQ | O_TRANSFORM_COLOR | O_TRANSFORM_BLADES | O_TRANSFORM_HEART => {
            Some("score")
        }
        O_JUMP | O_JUMP_IF_FALSE | O_RETURN => Some("control"),
        O_TRIGGER_REMOTE | O_META_RULE => Some("branch"),
        O_TAP_MEMBER | O_SET_TAPPED | O_ACTIVATE_MEMBER | O_TAP_OPPONENT => Some("state"),
        O_SEARCH_DECK | O_LOOK_DECK | O_LOOK_DECK_DYNAMIC | O_ORDER_DECK | O_REVEAL_UNTIL
        | O_REVEAL_CARDS | O_LOOK_REORDER_DISCARD => Some("search"),
        _ => None,
    }
}

fn trace_consumer_paths_for_opcode(opcode: i32) -> Vec<String> {
    let mut paths = Vec::new();
    match opcode {
        O_PAY_ENERGY | O_PAY_ENERGY_DYNAMIC | O_ACTIVATE_ENERGY => {
            paths.push("engine_rust_src/src/core/logic/action_gen/main_phase.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/costs.rs".to_string());
        }
        O_LOOK_AND_CHOOSE | O_SELECT_MEMBER | O_SELECT_CARDS | O_SELECT_LIVE | O_SELECT_PLAYER
        | O_SELECT_MODE => {
            paths.push("engine_rust_src/src/core/logic/action_gen/response.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/flow_select.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/interaction.rs".to_string());
        }
        O_DRAW | O_RECOVER_LIVE | O_RECOVER_MEMBER | O_MOVE_MEMBER | O_MOVE_TO_DECK
        | O_PLAY_MEMBER_FROM_HAND | O_PLAY_MEMBER_FROM_DISCARD | O_MOVE_TO_DISCARD
        | O_SWAP_ZONE => {
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/movement_deck.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/movement_discard.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/movement_swap_zone.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/interaction.rs".to_string());
        }
        O_BOOST_SCORE | O_ADD_BLADES | O_ADD_HEARTS | O_SET_SCORE | O_REDUCE_SCORE
        | O_REDUCE_COST | O_INCREASE_COST | O_SET_HEART_COST | O_INCREASE_HEART_COST
        | O_REDUCE_HEART_REQ | O_TRANSFORM_COLOR | O_TRANSFORM_BLADES | O_TRANSFORM_HEART => {
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/state_score_bonus.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/state_score_stats.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/state_score_requirements.rs".to_string());
        }
        O_JUMP | O_JUMP_IF_FALSE | O_RETURN => {
            paths.push("engine_rust_src/src/core/logic/interpreter/mod.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/mod.rs".to_string());
        }
        O_TRIGGER_REMOTE | O_META_RULE => {
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/flow_effects.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/game_trigger.rs".to_string());
        }
        O_TAP_MEMBER | O_SET_TAPPED | O_ACTIVATE_MEMBER | O_TAP_OPPONENT => {
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/state_member_tap.rs".to_string());
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/state_member.rs".to_string());
        }
        O_SEARCH_DECK | O_LOOK_DECK | O_LOOK_DECK_DYNAMIC | O_ORDER_DECK | O_REVEAL_UNTIL
        | O_REVEAL_CARDS | O_LOOK_REORDER_DISCARD => {
            paths.push("engine_rust_src/src/core/logic/interpreter/handlers/movement_deck.rs".to_string());
        }
        _ => {}
    }
    paths
}

fn trace_serialization_fields() -> Vec<String> {
    vec![
        "Ability.raw_text".to_string(),
        "Ability.trigger".to_string(),
        "Ability.effects".to_string(),
        "Ability.conditions".to_string(),
        "Ability.costs".to_string(),
        "Ability.frame_program".to_string(),
        "Ability.choice_count".to_string(),
        "Ability.requires_selection".to_string(),
        "Ability.is_once_per_turn".to_string(),
        "AbilityFrame.opcode".to_string(),
        "AbilityFrame.value".to_string(),
        "AbilityFrame.attr".to_string(),
        "AbilityFrame.slot".to_string(),
        "AbilityFrame.is_cost".to_string(),
        "AbilityFrame.params".to_string(),
    ]
}

fn trace_source_paths() -> Vec<String> {
    vec![
        "data/cards_compiled.json".to_string(),
        "data/ability_frame_source.json".to_string(),
        "data/ability_runtime_entrypoints.json".to_string(),
        "engine_rust_src/src/core/logic/card_db.rs".to_string(),
        "engine_rust_src/src/export_hydrated_abilities.rs".to_string(),
    ]
}

fn trace_warnings_for_ability(ability: &Ability, frames: &[AbilityFrame]) -> Vec<String> {
    let mut warnings = Vec::new();

    if !ability.has_authored_frame_program() && !ability.effects.is_empty() {
        warnings.push(
            "resolved through synthesized semantic effects instead of an authored frame_program"
                .to_string(),
        );
    }

    if frames.iter().any(|frame| frame.opcode() == O_SELECT_MODE) {
        warnings.push("modal branching depends on runtime selection legality".to_string());
    }

    if frames.iter().any(|frame| frame.opcode() == O_LOOK_AND_CHOOSE) {
        warnings.push("look-and-choose legality depends on current zone contents".to_string());
    }

    warnings
}

fn trace_zone(zone: Zone) -> Option<Zone> {
    if zone == Zone::Default {
        None
    } else {
        Some(zone)
    }
}

fn scalar_dynamic_param_parts(params: Option<&Value>, fallback_value: i32) -> Option<(i32, i32)> {
    let params_obj = params?.as_object()?;
    let source = params_obj
        .get("scalar_dynamic")
        .and_then(Value::as_object)
        .unwrap_or(params_obj);

    let parse_i32 = |key: &str| {
        source
            .get(key)
            .or_else(|| source.get(&key.to_ascii_uppercase()))
            .and_then(|value| value.as_i64())
            .map(|value| value as i32)
    };

    let base_value = parse_i32("base_value").or_else(|| parse_i32("base"));
    let divisor = parse_i32("divisor");

    if base_value.is_none() && divisor.is_none() {
        None
    } else {
        Some((base_value.unwrap_or(fallback_value), divisor.unwrap_or(1)))
    }
}

impl<'a> AbilityFrameComponents<'a> {
    pub fn from_raw_parts(
        raw_opcode: i32,
        value: i32,
        raw_attr: u64,
        raw_slot: i32,
        is_cost: bool,
        params: Option<&'a Value>,
    ) -> Self {
        let is_negated = raw_opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        let opcode = if is_negated {
            raw_opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            raw_opcode
        };
        Self {
            raw_opcode,
            opcode,
            value,
            filter: CardFilter::from_attr(raw_attr),
            slot: DecodedSlot::decode(raw_slot),
            raw_attr,
            raw_slot,
            is_negated,
            is_cost,
            params,
        }
    }

    /// Resolve which player this frame targets based on the structured slot data.
    pub fn target_player_index(&self, controller_idx: usize) -> usize {
        if self.slot.is_opponent || self.filter.target_player == TARGET_PLAYER_OPPONENT as u8 {
            1 - controller_idx
        } else {
            controller_idx
        }
    }

    pub fn stage_player_scope(&self, controller_idx: usize) -> (usize, Option<usize>) {
        match self.filter.target_player {
            x if x == TARGET_PLAYER_OPPONENT as u8 => (1 - controller_idx, None),
            x if x == TARGET_PLAYER_BOTH as u8 => (controller_idx, Some(1 - controller_idx)),
            _ if (self.raw_attr & crate::core::generated_constants::FILTER_ANY_STAGE) != 0 => {
                (controller_idx, Some(1 - controller_idx))
            }
            _ => (controller_idx, None),
        }
    }

    /// `ADD_TO_HAND` is effectively two effects: draw from deck, or consume the
    /// shared `looked_cards` buffer produced by search/reveal effects.
    pub fn add_to_hand_uses_looked_cards(&self) -> bool {
        (self.raw_attr & crate::core::logic::constants::FILTER_REVEALED_CONTEXT) != 0
            || self.raw_slot == crate::core::generated_constants::ZONE_LOOKED_CARDS
            || self.slot.target_slot as i32 == crate::core::generated_constants::SLOT_HAND
    }

    pub fn resolved_target_player(&self, controller_idx: usize) -> usize {
        if self.slot.is_opponent
            || self.slot.target_slot as i32 == TARGET_PLAYER_OPPONENT
            || self.filter.target_player == TARGET_PLAYER_OPPONENT as u8
        {
            1 - controller_idx
        } else {
            controller_idx
        }
    }

    pub fn filter_attr_without_state_flags(&self) -> u64 {
        self.resolved_filter_attr() & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK
    }

    pub fn has_structured_filter_constraints(&self) -> bool {
        crate::core::logic::filter::has_structured_filter_constraints(self.resolved_filter_attr())
    }

    pub fn legacy_group_id_hint(&self) -> Option<u8> {
        let lower_attr = self.raw_attr & crate::core::logic::constants::FILTER_MASK_LOWER;
        if (lower_attr & FILTER_GROUP_ENABLE) == 0 && lower_attr != 0 && lower_attr < 300 {
            Some((lower_attr & A_STANDARD_GROUP_ID_MASK) as u8)
        } else {
            None
        }
    }

    pub fn semantic_group_id(&self, fallback_value: i32) -> Option<u8> {
        if let Some(group_id) = self.legacy_group_id_hint() {
            Some(group_id)
        } else if self.filter.group_enabled || self.filter.group_id > 0 {
            Some(self.filter.group_id)
        } else if fallback_value > 0 {
            Some((fallback_value as u64 & A_STANDARD_GROUP_ID_MASK) as u8)
        } else {
            None
        }
    }

    pub fn counts_unique_names(&self) -> bool {
        self.filter.unique_names
            || (self.raw_attr & crate::core::logic::constants::FILTER_UNIQUE_NAMES) != 0
    }

    pub fn counts_unique_groups(&self) -> bool {
        self.params
            .as_ref()
            .and_then(|params| params.as_object())
            .and_then(|params| params.get("raw_cond").or_else(|| params.get("RAW_COND")))
            .and_then(|value| value.as_str())
            .map(|raw_cond| raw_cond == "UNIQUE_GROUPS_COUNT")
            .unwrap_or(false)
    }

    pub fn compare_accumulated(&self) -> bool {
        self.filter.compare_accumulated
    }

    pub fn uses_total_cost_budget(&self) -> bool {
        self.filter.compare_accumulated
            || (self.raw_attr & crate::core::generated_constants::FILTER_TOTAL_COST) != 0
    }

    pub fn count_filter_attr(&self) -> u64 {
        self.raw_attr & crate::core::logic::constants::FILTER_MASK_LOWER
    }

    pub fn count_filter(&self) -> CardFilter {
        crate::core::logic::filter::structured_filter_from_attr(self.count_filter_attr())
    }

    pub fn dynamic_count_filter_attr(&self) -> u64 {
        self.count_filter_attr()
    }

    pub fn restriction_id(&self) -> u8 {
        self.count_filter_attr() as u8
    }

    pub fn negate_count_limit(&self) -> i32 {
        self.resolved_filter_value(1).max(1)
    }

    pub fn resolved_filter_value(&self, fallback_value: i32) -> i32 {
        let filter_attr = self.count_filter_attr();
        if filter_attr != 0 {
            filter_attr as i32
        } else {
            fallback_value
        }
    }

    pub fn comparison_reversed(&self) -> bool {
        (self.raw_attr & 0x01) != 0
    }

    pub fn requests_keyword_energy(&self) -> bool {
        self.filter.keyword_energy
            || (self.raw_attr & crate::core::generated_constants::KEYWORD_ACTIVATED_ENERGY_BY_GROUP)
                != 0
    }

    pub fn requests_keyword_member(&self) -> bool {
        self.filter.keyword_member
            || (self.raw_attr & crate::core::generated_constants::KEYWORD_ACTIVATED_MEMBER_BY_GROUP)
                != 0
    }

    pub fn requests_played_this_turn_keyword(&self) -> bool {
        (self.raw_attr & crate::core::generated_constants::KEYWORD_PLAYED_THIS_TURN) != 0
            || self.raw_attr == 0
    }

    pub fn requests_yell_count_keyword(&self) -> bool {
        (self.raw_attr & crate::core::generated_constants::KEYWORD_YELL_COUNT) != 0
    }

    pub fn requests_has_live_set_keyword(&self) -> bool {
        (self.raw_attr & crate::core::generated_constants::KEYWORD_HAS_LIVE_SET) != 0
    }

    pub fn inferred_count_zone(&self) -> Option<SemanticCountZone> {
        match self.slot.source_zone {
            Zone::Hand => Some(SemanticCountZone::Hand),
            Zone::Discard => Some(SemanticCountZone::Discard),
            Zone::Stage => Some(SemanticCountZone::Stage),
            Zone::SuccessPile => Some(SemanticCountZone::SuccessPile),
            Zone::Default if self.slot.is_dynamic => {
                if self.slot.remainder_zone >= 200 {
                    Some(SemanticCountZone::Hand)
                } else if self.slot.remainder_zone >= 100 {
                    Some(SemanticCountZone::Discard)
                } else {
                    Some(SemanticCountZone::Stage)
                }
            }
            _ => None,
        }
    }

    pub fn count_opcode_hint(&self, default_hand_for_dynamic_cost: bool) -> Option<i32> {
        if let Some(per_card) = self
            .params
            .and_then(|value| value.as_object())
            .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
            .and_then(|value| value.as_str())
        {
            let zone = match per_card.to_ascii_uppercase().as_str() {
                "HAND" => Some(SemanticCountZone::Hand),
                "DISCARD" | "DISCARD_COUNT" => Some(SemanticCountZone::Discard),
                "SUCCESS_LIVE" | "SUCCESS_PILE" | "COUNT" | "COUNT_VAL" => {
                    Some(SemanticCountZone::SuccessPile)
                }
                "STAGE" => Some(SemanticCountZone::Stage),
                "ENERGY" => Some(SemanticCountZone::Energy),
                _ => None,
            };
            if let Some(zone) = zone {
                return Some(zone.opcode());
            }
        }

        if default_hand_for_dynamic_cost
            && self.slot.source_zone == Zone::Default
            && (self.slot.is_dynamic
                || self.filter.compare_accumulated
                || self.filter.special_id == 3
                || self.slot.remainder_zone >= 200
                || self.params.is_some())
        {
            return Some(SemanticCountZone::Hand.opcode());
        }

        self.inferred_count_zone().map(SemanticCountZone::opcode)
    }

    pub fn scale_source(&self) -> SemanticScaleSource {
        const LEGACY_SUCCESS_PILE_FLAG: u64 = 0x40;
        const LEGACY_LOW_WORD_MASK: u64 = 0xFFFF_FFFF;
        const LEGACY_SUCCESS_PILE_SENTINEL: u64 = 1;
        const LEGACY_SUCCESS_PILE_HIGH_WORD_FLOOR: u64 = 0x00FF_FFFF;
        const LEGACY_MULTIPLIER_FLAG: i32 = 0x1_0000;

        if let Some(per_card) = self
            .params
            .and_then(|value| value.as_object())
            .and_then(|params| params.get("per_card").or_else(|| params.get("PER_CARD")))
            .and_then(|value| value.as_str())
        {
            return match per_card.to_ascii_uppercase().as_str() {
                "HAND" => SemanticScaleSource::CountZone(SemanticCountZone::Hand),
                "DISCARD" | "DISCARD_COUNT" => {
                    SemanticScaleSource::CountZone(SemanticCountZone::Discard)
                }
                "STAGE" => SemanticScaleSource::CountZone(SemanticCountZone::Stage),
                "SUCCESS_LIVE" | "SUCCESS_PILE" | "COUNT" | "COUNT_VAL" => {
                    SemanticScaleSource::SuccessPile
                }
                "ENERGY" => SemanticScaleSource::CountZone(SemanticCountZone::Energy),
                _ => SemanticScaleSource::None,
            };
        }

        if (self.raw_attr & LEGACY_SUCCESS_PILE_FLAG) != 0
            || self.raw_attr == ConditionType::SuccessPileCount as u64
            || ((self.raw_attr & LEGACY_LOW_WORD_MASK) == LEGACY_SUCCESS_PILE_SENTINEL
                && (self.raw_attr >> 32) > LEGACY_SUCCESS_PILE_HIGH_WORD_FLOOR)
            || (self.value > 0xFFFF && (self.value & LEGACY_MULTIPLIER_FLAG) != 0)
        {
            return SemanticScaleSource::SuccessPile;
        }

        if let Some(zone) = self.inferred_count_zone() {
            return SemanticScaleSource::CountZone(zone);
        }

        SemanticScaleSource::None
    }

    pub fn target_area(&self) -> i32 {
        self.slot.target_slot as i32
    }

    pub fn debug_slot_value(&self) -> i32 {
        self.raw_slot & 0xFF
    }

    pub fn is_baton_slot_only(&self) -> bool {
        ((self.raw_slot as u64) & crate::core::generated_constants::FLAG_BATON_SLOT_ONLY) != 0
    }

    pub fn heart_compare_color_index(&self) -> usize {
        if self.filter.color_mask != 0 {
            self.filter.color_mask.trailing_zeros() as usize
        } else {
            (self.count_filter_attr() & A_STANDARD_COLOR_MASK_MASK) as usize
        }
    }

    pub fn resolved_color_index(&self, selected_color: usize, any_fallback: usize) -> usize {
        if let Some(color) = crate::core::logic::heart_semantics::decode_heart_type_from_params(self.params) {
            return color;
        }

        if matches!(self.raw_slot, 4 | 7) {
            return any_fallback;
        }

        let color_mask = self.filter.color_mask as usize;
        if color_mask != 0 {
            if color_mask == A_STANDARD_COLOR_MASK_MASK as usize {
                return selected_color;
            }
            return color_mask.trailing_zeros() as usize;
        }

        match self.raw_slot as usize {
            0..=6 => self.raw_slot as usize,
            _ => any_fallback,
        }
    }

    pub fn normalized_baton_filter_attr(&self) -> u64 {
        let attr = self.raw_attr;
        let lower_attr = attr & crate::core::logic::constants::FILTER_MASK_LOWER;
        if (attr >> 32) == 0 && (lower_attr & ((1 << FILTER_GROUP_ID_SHIFT) - 1)) == 0 && attr != 0 && attr < 300 {
            FILTER_GROUP_ENABLE | (attr << FILTER_GROUP_ID_SHIFT)
        } else {
            attr
        }
    }

    pub fn is_optional(&self) -> bool {
        self.filter.is_optional
            || (self.raw_attr & crate::core::logic::constants::FILTER_IS_OPTIONAL) != 0
    }

    pub fn allow_under_member_selection(&self) -> bool {
        (self.raw_slot & (1 << 25)) != 0
    }

    pub fn embedded_count_opcode(&self) -> Option<i32> {
        if (self.raw_slot & 0x1_0000) != 0 {
            Some((self.raw_slot >> 8) & 0xFFFF)
        } else {
            None
        }
    }

    pub fn discard_source_zone(&self) -> Zone {
        match self.slot.source_zone {
            Zone::Default => {
                let target_slot = self.slot.target_slot;
                if target_slot == TARGET_SLOT_STAGE {
                    Zone::Stage
                } else if target_slot == Zone::Hand as u8 {
                    Zone::Hand
                } else if (9..=11).contains(&target_slot) {
                    Zone::LiveSet
                } else {
                    Zone::Deck
                }
            }
            Zone::Hand => Zone::Hand,
            Zone::Stage => Zone::Stage,
            Zone::Discard => Zone::Discard,
            Zone::Yell => Zone::Yell,
            other => other,
        }
    }

    pub fn semantic_discard_spec(&self) -> SemanticDiscardSpec {
        let mut source_zone = self.discard_source_zone();
        if source_zone == Zone::Stage && self.is_until_size_operation() {
            source_zone = Zone::Hand;
        }

        let filter_attr = self.filter_attr_without_state_flags();
        let mut prompt_filter = CardFilter::default();
        match source_zone {
            Zone::Stage => prompt_filter.zone_mask = Zone::Stage as u8,
            Zone::Hand => prompt_filter.zone_mask = Zone::Hand as u8,
            Zone::Discard => prompt_filter.zone_mask = Zone::Discard as u8,
            _ => {}
        }

        SemanticDiscardSpec {
            requested_count: self.value,
            source_zone,
            filter_attr,
            prompt_filter_attr: prompt_filter.to_attr() | self.raw_attr.max(self.filter.to_attr()),
            suspend_slot: self.raw_slot,
            is_optional: self.is_optional(),
            allow_under_member_selection: self.allow_under_member_selection(),
            is_until_size_operation: self.is_until_size_operation(),
            embedded_count_opcode: self.embedded_count_opcode(),
            same_unit_discard: self
                .params
                .and_then(|params| params.get("same_unit_discard"))
                .and_then(|value| value.as_bool())
                .unwrap_or(false),
        }
    }

    pub fn is_until_size_operation(&self) -> bool {
        self.params
            .and_then(|params| params.get("operation"))
            .and_then(|value| value.as_str())
            .map(|value| value.eq_ignore_ascii_case("UNTIL_SIZE"))
            .unwrap_or(false)
            || ((self.value as u32) & (1 << 31)) != 0
    }

    pub fn has_revealed_context_passthrough(&self) -> bool {
        self.add_to_hand_uses_looked_cards()
    }

    /// Check if this frame uses dynamic value calculation (accumulated compare)
    pub fn is_dynamic(&self) -> bool {
        use crate::core::generated_layout::{A_STANDARD_COMPARE_ACCUMULATED_MASK, A_STANDARD_COMPARE_ACCUMULATED_SHIFT};
        (self.raw_attr & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT)) != 0
    }

    /// Get heart counts from frame data - returns tuple for compatibility
    pub fn heart_counts(&self) -> (i32, i32) {
        use crate::core::generated_layout::{
            V_HEART_COUNTS_PINK_SHIFT, V_HEART_COUNTS_RED_SHIFT, V_HEART_COUNTS_YELLOW_SHIFT,
            V_HEART_COUNTS_GREEN_SHIFT, V_HEART_COUNTS_BLUE_SHIFT, V_HEART_COUNTS_PURPLE_SHIFT,
            V_HEART_COUNTS_ANY_SHIFT,
            V_HEART_COUNTS_PINK_MASK, V_HEART_COUNTS_RED_MASK, V_HEART_COUNTS_YELLOW_MASK,
            V_HEART_COUNTS_GREEN_MASK, V_HEART_COUNTS_BLUE_MASK, V_HEART_COUNTS_PURPLE_MASK,
            V_HEART_COUNTS_ANY_MASK
        };
        
        let value_u32 = self.value as u32;
        let pink = ((value_u32 >> V_HEART_COUNTS_PINK_SHIFT) & V_HEART_COUNTS_PINK_MASK) as i32;
        let red = ((value_u32 >> V_HEART_COUNTS_RED_SHIFT) & V_HEART_COUNTS_RED_MASK) as i32;
        let yellow = ((value_u32 >> V_HEART_COUNTS_YELLOW_SHIFT) & V_HEART_COUNTS_YELLOW_MASK) as i32;
        let green = ((value_u32 >> V_HEART_COUNTS_GREEN_SHIFT) & V_HEART_COUNTS_GREEN_MASK) as i32;
        let blue = ((value_u32 >> V_HEART_COUNTS_BLUE_SHIFT) & V_HEART_COUNTS_BLUE_MASK) as i32;
        let purple = ((value_u32 >> V_HEART_COUNTS_PURPLE_SHIFT) & V_HEART_COUNTS_PURPLE_MASK) as i32;
        let any = ((value_u32 >> V_HEART_COUNTS_ANY_SHIFT) & V_HEART_COUNTS_ANY_MASK) as i32;
        
        let total_hearts = pink + red + yellow + green + blue + purple;
        (total_hearts, any)
    }

    /// Get heart counts as DecodedHeartCounts struct
    pub fn heart_counts_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        crate::core::logic::interpreter::instruction::DecodedHeartCounts::decode(self.value)
    }

    /// Get heart requirements from frame data - returns tuple for compatibility
    pub fn heart_requirements(&self) -> (i32, i32) {
        let decoded = self.heart_requirements_struct();
        let total_reqs: i32 = decoded.reqs.iter().map(|&r| r as i32).sum();
        (total_reqs, 0)
    }

    /// Get heart requirements as DecodedHeartRequirements struct
    pub fn heart_requirements_struct(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        crate::core::logic::interpreter::instruction::DecodedHeartRequirements::decode(self.raw_attr as i64)
    }

    /// Extract look and choose parameters from this frame
    pub fn look_choose(&self) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        AbilityFrame::decode_look_choose(self.value, self.params)
    }

    pub fn semantic_look_and_choose_spec(&self, fallback_choose_count: usize) -> SemanticLookAndChooseSpec {
        let look = self.look_choose();
        let source_zone = if self.slot.source_zone == Zone::Default {
            Zone::Deck
        } else {
            self.slot.source_zone
        };
        let mut selection_filter = self.filter;
        selection_filter.char_id_1 = look.char_id_1;
        selection_filter.char_id_2 = look.char_id_2;
        selection_filter.char_id_3 = look.char_id_3;

        SemanticLookAndChooseSpec {
            look_count: look.count.max(1) as usize,
            choose_count: look.choose_count.max(fallback_choose_count as u8).max(1) as usize,
            source_zone,
            target_slot: self.slot.target_slot,
            remainder_zone: self.slot.dest_zone,
            reveal: look.reveal,
            remainder_to_discard: look.dest_discard,
            is_optional: self.filter.is_optional,
            selection_filter,
            selection_filter_attr: {
                let attr = if self.raw_attr != 0 {
                    self.raw_attr
                } else {
                    selection_filter.to_attr()
                };
                if matches!(source_zone, Zone::Deck | Zone::DeckTop | Zone::DeckBottom)
                    && look.choose_count.max(fallback_choose_count as u8) > 1
                {
                    0
                } else {
                    attr
                }
            },
            suspend_slot: self.raw_slot,
        }
    }

    pub fn semantic_select_cards_spec(&self) -> SemanticLookAndChooseSpec {
        let source_zone = if self.slot.source_zone == Zone::Default {
            match self.slot.target_slot {
                x if x == Zone::Hand as u8 => Zone::Hand,
                x if x == Zone::Discard as u8 => Zone::Discard,
                x if x == Zone::Deck as u8 => Zone::Deck,
                x if x == Zone::Yell as u8 => Zone::Yell,
                _ => Zone::Discard,
            }
        } else {
            self.slot.source_zone
        };

        SemanticLookAndChooseSpec {
            look_count: 0,
            choose_count: 1,
            source_zone,
            target_slot: self.slot.target_slot,
            remainder_zone: self.slot.dest_zone,
            reveal: false,
            remainder_to_discard: false,
            is_optional: self.filter.is_optional,
            selection_filter: self.filter,
            selection_filter_attr: self.resolved_filter_attr(),
            suspend_slot: self.raw_slot,
        }
    }

    /// Get the divisor for dynamic value calculation
    pub fn scalar_dynamic_divisor(&self) -> i32 {
        if let Some((_, divisor)) = scalar_dynamic_param_parts(self.params, self.value) {
            return divisor;
        }
        use crate::core::generated_layout::{V_SCALAR_DYNAMIC_DIVISOR_MASK, V_SCALAR_DYNAMIC_DIVISOR_SHIFT};
        ((self.value as u32 >> V_SCALAR_DYNAMIC_DIVISOR_SHIFT) & V_SCALAR_DYNAMIC_DIVISOR_MASK) as i32
    }

    /// Get the base for dynamic value calculation
    pub fn scalar_dynamic_base(&self) -> i32 {
        if let Some((base_value, _)) = scalar_dynamic_param_parts(self.params, self.value) {
            return base_value;
        }
        use crate::core::generated_layout::{V_SCALAR_DYNAMIC_BASE_VALUE_MASK, V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT};
        ((self.value as u32 >> V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT) & V_SCALAR_DYNAMIC_BASE_VALUE_MASK) as i32
    }

    pub fn to_trace_step(&self) -> AbilityTraceStep {
        let opcode = trace_opcode_name(self.opcode);
        let family = trace_step_family(self.opcode).map(|value| value.to_string());
        let consumer_paths = trace_consumer_paths_for_opcode(self.opcode);
        let mut step = AbilityTraceStep {
            summary: opcode.clone(),
            opcode,
            is_cost: self.is_cost,
            value: Some(self.value),
            source_zone: trace_zone(self.slot.source_zone),
            dest_zone: trace_zone(self.slot.dest_zone),
            target_slot: (self.slot.target_slot != 0).then_some(self.slot.target_slot),
            choose_count: None,
            reveal: None,
            remainder_to_discard: None,
            filter: (self.filter != CardFilter::default()).then_some(self.filter),
            slot: (self.slot != DecodedSlot::default()).then_some(self.slot),
            params: self.params.cloned().unwrap_or(Value::Null),
            family,
            consumer_paths,
            serialization_fields: vec![
                "opcode".to_string(),
                "value".to_string(),
                "attr".to_string(),
                "slot".to_string(),
                "is_cost".to_string(),
                "params".to_string(),
            ],
        };

        step.summary = match self.opcode {
            O_RETURN => {
                step.value = None;
                step.filter = None;
                step.slot = None;
                "return".to_string()
            }
            O_DRAW => format!("draw {} card(s)", self.value.max(0)),
            O_MOVE_TO_DISCARD => {
                let from_zone = step
                    .source_zone
                    .map(|zone| format!("{:?}", zone))
                    .unwrap_or_else(|| "Default".to_string());
                format!("move {} card(s) from {} to discard", self.value.max(0), from_zone)
            }
            O_RECOVER_LIVE => format!("recover {} live card(s) from discard", self.value.max(0)),
            O_RECOVER_MEMBER => format!("recover {} member card(s) from discard", self.value.max(0)),
            O_LOOK_AND_CHOOSE => {
                let look = self.look_choose();
                step.choose_count = Some(look.choose_count.max(1));
                step.reveal = Some(look.reveal);
                step.remainder_to_discard = Some(look.dest_discard);
                let from_zone = step
                    .source_zone
                    .map(|zone| format!("{:?}", zone))
                    .unwrap_or_else(|| "Deck".to_string());
                format!(
                    "look {} choose {} from {}{}",
                    look.count.max(1),
                    look.choose_count.max(1),
                    from_zone,
                    if look.dest_discard { ", remainder to discard" } else { "" }
                )
            }
            O_JUMP => format!("jump by {} frame(s)", self.value),
            O_JUMP_IF_FALSE => format!("if false jump by {} frame(s)", self.value),
            O_PAY_ENERGY => format!("pay {} energy", self.value.max(0)),
            O_SELECT_MEMBER => format!("select {} member(s)", self.value.max(1)),
            O_ADD_BLADES => format!("add {} blade(s)", self.value),
            O_ADD_HEARTS => format!("add {} heart(s)", self.value),
            O_BOOST_SCORE => format!("boost score by {}", self.value),
            O_TAP_MEMBER => format!("tap {} member(s)", self.value.max(1)),
            O_SET_TAPPED => {
                if self.value != 0 {
                    "set tapped".to_string()
                } else {
                    "clear tapped".to_string()
                }
            }
            O_NOP => "no-op".to_string(),
            _ => format!("{} value={}", step.opcode, self.value),
        };

        step
    }
}

impl AbilityFrame {
    fn decode_look_choose(
        value: i32,
        params: Option<&Value>,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        let mut decoded =
            crate::core::logic::interpreter::instruction::DecodedLookAndChoose::decode(value);

        let Some(params) = params else {
            return decoded;
        };

        if let Some(count) = params
            .get("count")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.count = count;
        }
        if let Some(choose_count) = params
            .get("choose_count")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.choose_count = choose_count;
        }
        if let Some(char_id_1) = params
            .get("char_id_1")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_1 = char_id_1;
        }
        if let Some(char_id_2) = params
            .get("char_id_2")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_2 = char_id_2;
        }
        if let Some(char_id_3) = params
            .get("char_id_3")
            .and_then(|value| value.as_u64())
            .and_then(|value| u8::try_from(value).ok())
        {
            decoded.char_id_3 = char_id_3;
        }
        if let Some(reveal) = params.get("reveal").and_then(|value| value.as_bool()) {
            decoded.reveal = reveal;
        }
        if let Some(dest_discard) = params.get("dest_discard").and_then(|value| value.as_bool()) {
            decoded.dest_discard = dest_discard;
        }

        decoded
    }

    fn with_components(
        opcode: i32,
        value: i32,
        filter: CardFilter,
        slot: DecodedSlot,
        is_cost: bool,
        params: Value,
    ) -> Self {
        AbilityFrame {
            opcode,
            value,
            attr: filter.to_attr(),
            slot: slot.to_raw(),
            is_cost,
            params,
        }
    }

    fn with_raw_parts(
        opcode: i32,
        value: i32,
        attr: u64,
        slot: i32,
        is_cost: bool,
        params: Value,
    ) -> Self {
        AbilityFrame {
            opcode,
            value,
            attr,
            slot,
            is_cost,
            params,
        }
    }

    pub(crate) fn opcode_from_effect_type(effect_type: EffectType) -> i32 {
        match effect_type {
            EffectType::Draw => O_DRAW,
            EffectType::PayEnergy => O_PAY_ENERGY,
            EffectType::AddBlades => O_ADD_BLADES,
            EffectType::AddHearts => O_ADD_HEARTS,
            EffectType::ReduceCost => O_REDUCE_COST,
            EffectType::LookDeck => O_LOOK_DECK,
            EffectType::RecoverLive => O_RECOVER_LIVE,
            EffectType::BoostScore => O_BOOST_SCORE,
            EffectType::RecoverMember => O_RECOVER_MEMBER,
            EffectType::BuffPower => O_BUFF_POWER,
            EffectType::Immunity => O_IMMUNITY,
            EffectType::MoveMember => O_MOVE_MEMBER,
            EffectType::SwapCards => O_SWAP_CARDS,
            EffectType::SearchDeck => O_SEARCH_DECK,
            EffectType::EnergyCharge => O_ENERGY_CHARGE,
            EffectType::SetBlades => O_SET_BLADES,
            EffectType::SetHearts => O_SET_HEARTS,
            EffectType::FormationChange => O_FORMATION_CHANGE,
            EffectType::NegateEffect => O_NEGATE_EFFECT,
            EffectType::OrderDeck => O_ORDER_DECK,
            EffectType::MetaRule => O_META_RULE,
            EffectType::SelectMode => O_SELECT_MODE,
            EffectType::MoveToDeck => O_MOVE_TO_DECK,
            EffectType::TapOpponent => O_TAP_OPPONENT,
            EffectType::PlaceUnder => O_PLACE_UNDER,
            EffectType::Restriction => O_RESTRICTION,
            EffectType::BatonTouchMod => O_BATON_TOUCH_MOD,
            EffectType::SetScore => O_SET_SCORE,
            EffectType::SwapZone => O_SWAP_ZONE,
            EffectType::TransformColor => O_TRANSFORM_COLOR,
            EffectType::RevealCards => O_REVEAL_CARDS,
            EffectType::LookAndChoose => O_LOOK_AND_CHOOSE,
            EffectType::CheerReveal => O_CHEER_REVEAL,
            EffectType::ActivateMember => O_ACTIVATE_MEMBER,
            EffectType::AddToHand => O_ADD_TO_HAND,
            EffectType::ColorSelect => O_COLOR_SELECT,
            EffectType::TriggerRemote => O_TRIGGER_REMOTE,
            EffectType::ReduceHeartReq => O_REDUCE_HEART_REQ,
            EffectType::ModifyScoreRule => O_MODIFY_SCORE_RULE,
            EffectType::AddStageEnergy => O_ADD_STAGE_ENERGY,
            EffectType::SetTapped => O_SET_TAPPED,
            EffectType::TapMember => O_TAP_MEMBER,
            EffectType::PlayMemberFromHand => O_PLAY_MEMBER_FROM_HAND,
            EffectType::MoveToDiscard => O_MOVE_TO_DISCARD,
            EffectType::GrantAbility => O_GRANT_ABILITY,
            EffectType::IncreaseHeartCost => O_INCREASE_HEART_COST,
            EffectType::ReduceYellCount => O_REDUCE_YELL_COUNT,
            EffectType::PlayMemberFromDiscard => O_PLAY_MEMBER_FROM_DISCARD,
            EffectType::SelectMember => O_SELECT_MEMBER,
            EffectType::DrawUntil => O_DRAW_UNTIL,
            EffectType::SelectPlayer => O_SELECT_PLAYER,
            EffectType::SelectLive => O_SELECT_LIVE,
            EffectType::RevealUntil => O_REVEAL_UNTIL,
            EffectType::IncreaseCost => O_INCREASE_COST,
            EffectType::PreventPlayToSlot => O_PREVENT_PLAY_TO_SLOT,
            EffectType::SwapArea => O_SWAP_AREA,
            EffectType::TransformHeart => O_TRANSFORM_HEART,
            EffectType::SelectCards => O_SELECT_CARDS,
            EffectType::OpponentChoose => O_OPPONENT_CHOOSE,
            EffectType::PlayLiveFromDiscard => O_PLAY_LIVE_FROM_DISCARD,
            EffectType::ReduceLiveSetLimit => O_REDUCE_LIVE_SET_LIMIT,
            EffectType::SetTargetSelf => O_SET_TARGET_SELF,
            EffectType::SetTargetOpponent => O_SET_TARGET_OPPONENT,
            EffectType::PreventSetToSuccessPile => O_PREVENT_SET_TO_SUCCESS_PILE,
            EffectType::ActivateEnergy => O_ACTIVATE_ENERGY,
            EffectType::PreventActivate => O_PREVENT_ACTIVATE,
            EffectType::SetHeartCost => O_SET_HEART_COST,
            EffectType::PreventBatonTouch => O_PREVENT_BATON_TOUCH,
            EffectType::LookDeckDynamic => O_LOOK_DECK_DYNAMIC,
            EffectType::ReduceScore => O_REDUCE_SCORE,
            EffectType::RepeatAbility => O_REPEAT_ABILITY,
            EffectType::LoseExcessHearts => O_LOSE_EXCESS_HEARTS,
            EffectType::SkipActivatePhase => O_SKIP_ACTIVATE_PHASE,
            EffectType::PayEnergyDynamic => O_PAY_ENERGY_DYNAMIC,
            EffectType::PlaceEnergyUnderMember => O_PLACE_ENERGY_UNDER_MEMBER,
            EffectType::CalcSumCost => O_CALC_SUM_COST,
            EffectType::LookReorderDiscard => O_LOOK_REORDER_DISCARD,
            EffectType::DivValue => O_DIV_VALUE,
            EffectType::TransformBlades => O_TRANSFORM_BLADES,
            _ => 0,
        }
    }

    fn normalize_frame_kind(kind: &str) -> String {
        if kind.is_empty() {
            return String::new();
        }

        if kind.chars().any(|ch| ch == '_') {
            return kind.to_ascii_uppercase();
        }

        let mut normalized = String::with_capacity(kind.len() + 4);
        let mut prev_is_lower_or_digit = false;
        for ch in kind.chars() {
            if ch.is_ascii_uppercase() && prev_is_lower_or_digit {
                normalized.push('_');
            }
            normalized.push(ch.to_ascii_uppercase());
            prev_is_lower_or_digit = ch.is_ascii_lowercase() || ch.is_ascii_digit();
        }
        normalized
    }

    fn opcode_id_from_frame_kind(kind: &str) -> i32 {
        match kind {
            "RETURN" => O_RETURN,
            "DRAW" => O_DRAW,
            "NOP" => O_NOP,
            "JUMP" => O_JUMP,
            "JUMP_IF_FALSE" => O_JUMP_IF_FALSE,
            "PAY_ENERGY" => O_PAY_ENERGY,
            "PAY_ENERGY_DYNAMIC" => O_PAY_ENERGY_DYNAMIC,
            "ENERGY_CHARGE" => O_ENERGY_CHARGE,
            "ACTIVATE_ENERGY" => O_ACTIVATE_ENERGY,
            "PLACE_ENERGY_UNDER_MEMBER" => O_PLACE_ENERGY_UNDER_MEMBER,
            "RECOVER_LIVE" => O_RECOVER_LIVE,
            "RECOVER_MEMBER" => O_RECOVER_MEMBER,
            "ACTIVATE_MEMBER" => O_ACTIVATE_MEMBER,
            "NEGATE_EFFECT" => O_NEGATE_EFFECT,
            "LOOK_AND_CHOOSE" => O_LOOK_AND_CHOOSE,
            "SELECT_MEMBER" => O_SELECT_MEMBER,
            "SELECT_LIVE" => O_SELECT_LIVE,
            "SELECT_PLAYER" => O_SELECT_PLAYER,
            "SELECT_CARDS" => O_SELECT_CARDS,
            "SELECT_MODE" => O_SELECT_MODE,
            "OPPONENT_CHOOSE" => O_OPPONENT_CHOOSE,
            "MOVE_MEMBER" => O_MOVE_MEMBER,
            "MOVE_TO_DECK" => O_MOVE_TO_DECK,
            "MOVE_TO_DISCARD" => O_MOVE_TO_DISCARD,
            "PLAY_MEMBER_FROM_HAND" => O_PLAY_MEMBER_FROM_HAND,
            "PLAY_MEMBER_FROM_DISCARD" => O_PLAY_MEMBER_FROM_DISCARD,
            "PLAY_LIVE_FROM_DISCARD" => O_PLAY_LIVE_FROM_DISCARD,
            "TAP_MEMBER" => O_TAP_MEMBER,
            "TAP_OPPONENT" => O_TAP_OPPONENT,
            "SET_TAPPED" => O_SET_TAPPED,
            "COLOR_SELECT" => O_COLOR_SELECT,
            "TRIGGER_REMOTE" => O_TRIGGER_REMOTE,
            "META_RULE" => O_META_RULE,
            "ADD_TO_HAND" => O_ADD_TO_HAND,
            "DRAW_UNTIL" => O_DRAW_UNTIL,
            "REVEAL_UNTIL" => O_REVEAL_UNTIL,
            "LOOK_DECK" => O_LOOK_DECK,
            "LOOK_DECK_DYNAMIC" => O_LOOK_DECK_DYNAMIC,
            "LOOK_REORDER_DISCARD" => O_LOOK_REORDER_DISCARD,
            "ORDER_DECK" => O_ORDER_DECK,
            "SEARCH_DECK" => O_SEARCH_DECK,
            "HAS_MEMBER" => C_HAS_MEMBER,
            "HAS_COLOR" => C_HAS_COLOR,
            "COUNT_STAGE" => C_COUNT_STAGE,
            "COUNT_HAND" => C_COUNT_HAND,
            "COUNT_DISCARD" => C_COUNT_DISCARD,
            "IS_CENTER" => C_IS_CENTER,
            "COUNT_GROUP" => C_COUNT_GROUP,
            "COUNT_ENERGY" => C_COUNT_ENERGY,
            "HAS_LIVE_CARD" => C_HAS_LIVE_CARD,
            "COUNT_SUCCESS_LIVE" => C_COUNT_SUCCESS_LIVE,
            "SCORE_COMPARE" => C_SCORE_COMPARE,
            "COST_COMPARE" => C_COST_COMPARE,
            "COUNT_HEARTS" => C_COUNT_HEARTS,
            "COUNT_BLADES" => C_COUNT_BLADES,
            "OPPONENT_ENERGY_DIFF" => C_OPPONENT_ENERGY_DIFF,
            "HAS_KEYWORD" => C_HAS_KEYWORD,
            "DECK_REFRESHED" => C_DECK_REFRESHED,
            "COUNT_LIVE_ZONE" => C_COUNT_LIVE_ZONE,
            "BATON" => C_BATON,
            "TYPE_CHECK" => C_TYPE_CHECK,
            "AREA_CHECK" => C_AREA_CHECK,
            "HEART_LEAD" => C_HEART_LEAD,
            "HAS_EXCESS_HEART" => C_HAS_EXCESS_HEART,
            "NOT_HAS_EXCESS_HEART" => C_NOT_HAS_EXCESS_HEART,
            "TOTAL_BLADES" => C_TOTAL_BLADES,
            "COUNT_ENERGY_EXACT" => C_COUNT_ENERGY_EXACT,
            "COUNT_BLADE_HEART_TYPES" => C_COUNT_BLADE_HEART_TYPES,
            "SCORE_TOTAL_CHECK" => C_SCORE_TOTAL_CHECK,
            "MAIN_PHASE" => C_MAIN_PHASE,
            "SUCCESS_PILE_COUNT" => C_SUCCESS_PILE_COUNT,
            "IS_SELF_MOVE" => C_IS_SELF_MOVE,
            "DISCARDED_CARDS" => C_DISCARDED_CARDS,
            "YELL_REVEALED_UNIQUE_COLORS" => C_YELL_REVEALED_UNIQUE_COLORS,
            "SYNC_COST" => C_SYNC_COST,
            "SUM_VALUE" => C_SUM_VALUE,
            "IS_WAIT" => C_IS_WAIT,
            "ON_ABILITY_RESOLVE" => C_ON_ABILITY_RESOLVE,
            "TARGET_MEMBER_HAS_NO_HEARTS" => C_TARGET_MEMBER_HAS_NO_HEARTS,
            "BOOST_SCORE" => O_BOOST_SCORE,
            "SET_SCORE" => O_SET_SCORE,
            "REDUCE_SCORE" => O_REDUCE_SCORE,
            "ADD_BLADES" => O_ADD_BLADES,
            "ADD_HEARTS" => O_ADD_HEARTS,
            "SET_BLADES" => O_SET_BLADES,
            "SET_HEARTS" => O_SET_HEARTS,
            "TRANSFORM_BLADES" => O_TRANSFORM_BLADES,
            "TRANSFORM_HEART" => O_TRANSFORM_HEART,
            "TRANSFORM_COLOR" => O_TRANSFORM_COLOR,
            "REPEAT_ABILITY" => O_REPEAT_ABILITY,
            "LOSE_EXCESS_HEARTS" => O_LOSE_EXCESS_HEARTS,
            "SKIP_ACTIVATE_PHASE" => O_SKIP_ACTIVATE_PHASE,
            "SET_HEART_COST" => O_SET_HEART_COST,
            "RESTRICTION" => O_RESTRICTION,
            "PREVENT_ACTIVATE" => O_PREVENT_ACTIVATE,
            "PREVENT_BATON_TOUCH" => O_PREVENT_BATON_TOUCH,
            "PREVENT_PLAY_TO_SLOT" => O_PREVENT_PLAY_TO_SLOT,
            "PREVENT_SET_TO_SUCCESS_PILE" => O_PREVENT_SET_TO_SUCCESS_PILE,
            "MODIFY_SCORE_RULE" => O_MODIFY_SCORE_RULE,
            "GRANT_ABILITY" => O_GRANT_ABILITY,
            "INCREASE_COST" => O_INCREASE_COST,
            "REDUCE_COST" => O_REDUCE_COST,
            "INCREASE_HEART_COST" => O_INCREASE_HEART_COST,
            "REDUCE_HEART_REQ" => O_REDUCE_HEART_REQ,
            "REDUCE_LIVE_SET_LIMIT" => O_REDUCE_LIVE_SET_LIMIT,
            "REDUCE_YELL_COUNT" => O_REDUCE_YELL_COUNT,
            "SWAP_CARDS" => O_SWAP_CARDS,
            "SWAP_AREA" => O_SWAP_AREA,
            "SET_TARGET_SELF" => O_SET_TARGET_SELF,
            "SET_TARGET_OPPONENT" => O_SET_TARGET_OPPONENT,
            "BATON_TOUCH_MOD" => O_BATON_TOUCH_MOD,
            "PLACE_UNDER" => O_PLACE_UNDER,
            "FORMALTION_CHANGE" => O_FORMATION_CHANGE,
            "FORMATION_CHANGE" => O_FORMATION_CHANGE,
            "CHEER_REVEAL" => O_CHEER_REVEAL,
            "REVEAL_CARDS" => O_REVEAL_CARDS,
            "CALC_SUM_COST" => O_CALC_SUM_COST,
            "DIV_VALUE" => O_DIV_VALUE,
            "APPLY_RULES" => O_META_RULE,
            "GROUP_FILTER" => C_GROUP_FILTER,
            "ALL_CARDS_MATCH" => 309,
            _ => 0,
        }
    }

    fn decoded_hint_name(decoded_hint: &str) -> Option<String> {
        let token = decoded_hint
            .split(|ch: char| ch.is_whitespace() || ch == '|')
            .find(|part| !part.is_empty())?;
        let token = token.trim_end_matches('?');
        let token = token.strip_prefix("CHECK_").unwrap_or(token);
        if token.is_empty() {
            None
        } else {
            Some(token.to_ascii_uppercase())
        }
    }

    fn extract_u8_from_text(text: &str, keys: &[&str]) -> Option<u8> {
        let lower = text.to_ascii_lowercase();
        for key in keys {
            if let Some(pos) = lower.find(key) {
                let mut digits = String::new();
                for ch in lower[pos + key.len()..].chars() {
                    if ch.is_ascii_digit() {
                        digits.push(ch);
                    } else if digits.is_empty() && (ch == ' ' || ch == '=' || ch == ':') {
                        continue;
                    } else {
                        break;
                    }
                }
                if let Ok(value) = digits.parse::<u8>() {
                    return Some(value);
                }
            }
        }
        None
    }

    fn first_field<'a>(value: &'a Value, keys: &[&str]) -> Option<&'a Value> {
        keys.iter().find_map(|key| value.get(*key))
    }

    fn first_str<'a>(value: &'a Value, keys: &[&str]) -> Option<&'a str> {
        Self::first_field(value, keys).and_then(Value::as_str)
    }

    fn first_i64(value: &Value, keys: &[&str]) -> Option<i64> {
        Self::first_field(value, keys).and_then(Value::as_i64)
    }

    fn first_cloned_value(value: &Value, keys: &[&str]) -> Value {
        Self::first_field(value, keys).cloned().unwrap_or(Value::Null)
    }

    fn zone_from_text(value: &str) -> Option<Zone> {
        match value.trim().to_ascii_uppercase().as_str() {
            "HAND" | "CARD_HAND" => Some(Zone::Hand),
            "DISCARD" | "CARD_DISCARD" => Some(Zone::Discard),
            "STAGE" => Some(Zone::Stage),
            "DECK" => Some(Zone::Deck),
            "DECK_TOP" | "TOP_DECK" => Some(Zone::DeckTop),
            "DECK_BOTTOM" | "BOTTOM_DECK" => Some(Zone::DeckBottom),
            "ENERGY" => Some(Zone::Energy),
            "LIVE" | "SUCCESS_LIVE" | "SUCCESS_PILE" => Some(Zone::SuccessPile),
            _ => None,
        }
    }

    pub(crate) fn from_json_value(frame: &Value) -> Self {
        if matches!(frame.as_str(), Some("Return" | "RETURN")) {
            return AbilityFrame { opcode: O_RETURN, ..Default::default() };
        }

        let semantic = frame.get("semantic").filter(|value| value.is_object());
        let mut payload = semantic.unwrap_or(frame);
        let mut kind = frame
            .get("kind")
            .and_then(|v| v.as_str())
            .or_else(|| frame.get("op").and_then(|v| v.as_str()))
            .unwrap_or("");
        if kind.is_empty() {
            if let Some(obj) = frame.as_object() {
                if obj.len() == 1 {
                    if let Some((key, value)) = obj.iter().next() {
                        if value.is_object()
                            || value.is_array()
                            || value.is_string()
                            || value.is_number()
                        {
                            kind = key.as_str();
                            payload = value;
                        }
                    }
                }
            }
        } else if semantic.is_none() {
            if let Some(value) = frame.get(kind) {
                if value.is_object() || value.is_array() || value.is_string() || value.is_number() {
                    payload = value;
                }
            }
        }

        let opcode_name = Self::first_str(payload, &["opcode_name", "opcode", "op"])
            .or_else(|| Self::first_str(frame, &["opcode_name", "opcode", "op"]))
            .unwrap_or("");
        let opcode_id = Self::first_i64(payload, &["opcode_id", "opcode", "op"])
            .or_else(|| Self::first_i64(frame, &["opcode_id", "opcode"]))
            .unwrap_or(0) as i32;
        let value_json = Self::first_cloned_value(payload, &["value", "count", "rule_type", "params", "v"]);
        let value = Self::first_i64(&value_json, &["value"])
            .or_else(|| Self::first_i64(payload, &["count", "rule_type", "v"]))
            .or_else(|| Self::first_i64(frame, &["value", "rule_type", "v"]))
            .unwrap_or(0) as i32;
        let options = Self::first_cloned_value(frame, &["options"]);
        let options = if options.is_null() {
            Self::first_cloned_value(payload, &["options"])
        } else {
            options
        };
        let params = Self::first_cloned_value(payload, &["params"]);
        let params = if params.is_null() {
            Self::first_cloned_value(frame, &["params"])
        } else {
            params
        };
        let is_cost = payload
            .get("is_cost")
            .or_else(|| frame.get("is_cost"))
            .or_else(|| params.get("is_cost"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let params = if params.is_null() {
            options
                .get("params")
                .cloned()
                .unwrap_or(Value::Null)
        } else {
            params
        };
        let mut filter = CardFilter::from_frame_json(payload, &options, &params);
        let filter_passthrough = [payload, &options, &params]
            .into_iter()
            .filter_map(|value| {
                crate::core::logic::filter::filter_parts_from_params(Some(value))
                    .map(|(_, extras)| extras)
            })
            .fold(0u64, |acc, extras| acc | extras);
        let slot_value = payload
            .get("slot")
            .or_else(|| frame.get("slot"))
            .cloned();
        let slot = slot_value
            .clone()
            .and_then(|value| serde_json::from_value::<DecodedSlot>(value).ok())
            .unwrap_or_default();
        let is_negated = payload
            .get("is_negated")
            .or_else(|| payload.get("negated"))
            .or_else(|| frame.get("negated"))
            .and_then(|v| v.as_bool())
            .unwrap_or(false);
        let recover_params = params.clone();
        let mut slot = slot;
        if let Some(slot_obj) = slot_value.as_ref().and_then(Value::as_object) {
            if let Some(target_slot) = slot_obj.get("target_slot").and_then(parse_target_slot_value) {
                slot.target_slot = target_slot;
            }
            if let Some(comparison) = slot_obj.get("comparison").and_then(parse_comparison_value) {
                slot.comparison = comparison;
            }
            if let Some(source_zone) = slot_obj
                .get("source_zone")
                .and_then(Value::as_str)
                .and_then(Self::zone_from_text)
            {
                slot.source_zone = source_zone;
            }
            if let Some(dest_zone) = slot_obj
                .get("dest_zone")
                .and_then(Value::as_str)
                .and_then(Self::zone_from_text)
            {
                slot.dest_zone = dest_zone;
            }
            if let Some(remainder_zone) = slot_obj
                .get("remainder_zone")
                .and_then(parse_remainder_zone_value)
            {
                slot.remainder_zone = remainder_zone;
            }
            if let Some(area_idx) = slot_obj.get("area_idx").and_then(Value::as_u64) {
                slot.area_idx = area_idx as u8;
            }
            if let Some(is_opponent) = slot_obj.get("is_opponent") {
                slot.is_opponent = is_opponent.as_bool().unwrap_or_else(|| {
                    is_opponent.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_reveal_until_live) = slot_obj.get("is_reveal_until_live") {
                slot.is_reveal_until_live = is_reveal_until_live.as_bool().unwrap_or_else(|| {
                    is_reveal_until_live
                        .as_i64()
                        .map(|value| value != 0)
                        .unwrap_or(false)
                });
            }
            if let Some(is_baton_slot) = slot_obj.get("is_baton_slot") {
                slot.is_baton_slot = is_baton_slot.as_bool().unwrap_or_else(|| {
                    is_baton_slot.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_empty_slot) = slot_obj.get("is_empty_slot") {
                slot.is_empty_slot = is_empty_slot.as_bool().unwrap_or_else(|| {
                    is_empty_slot.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_wait) = slot_obj.get("is_wait") {
                slot.is_wait = is_wait.as_bool().unwrap_or_else(|| {
                    is_wait.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
            if let Some(is_dynamic) = slot_obj.get("is_dynamic") {
                slot.is_dynamic = is_dynamic.as_bool().unwrap_or_else(|| {
                    is_dynamic.as_i64().map(|value| value != 0).unwrap_or(false)
                });
            }
        }
        if let Some(options_slot) = options.get("slot") {
            if let Ok(decoded_slot) = serde_json::from_value::<DecodedSlot>(options_slot.clone()) {
                slot = decoded_slot;
            }
        }
        if filter.target_player == 0 {
            filter.target_player = if slot.is_opponent {
                TARGET_PLAYER_OPPONENT as u8
            } else {
                TARGET_PLAYER_SELF as u8
            };
        }
        if let Some(params_obj) = params.as_object() {
            let from_zone = params_obj
                .get("FROM")
                .or_else(|| params_obj.get("from"))
                .and_then(|value| value.as_str())
                .map(|value| value.to_ascii_uppercase());
            if slot.source_zone == Zone::default() {
                match from_zone.as_deref() {
                    Some("DISCARD") => slot.source_zone = Zone::Discard,
                    Some("HAND") => slot.source_zone = Zone::Hand,
                    Some("DECK") => slot.source_zone = Zone::Deck,
                    Some("STAGE") => slot.source_zone = Zone::Stage,
                    _ => {}
                }
            }
        }
        let opcode_key = if !kind.is_empty() { kind } else { opcode_name };
        let opcode_key = Self::normalize_frame_kind(opcode_key);
        let decoded_hint = Self::first_str(payload, &["decoded"])
            .or_else(|| Self::first_str(frame, &["decoded"]))
            .unwrap_or("");
        let decoded_hint_name = Self::decoded_hint_name(decoded_hint);

        let resolved_opcode_id = if opcode_id != 0 {
            opcode_id
        } else if opcode_key == "NOP" {
            decoded_hint_name
                .as_deref()
                .map(Self::opcode_id_from_frame_kind)
                .unwrap_or(0)
        } else {
            Self::opcode_id_from_frame_kind(opcode_key.as_str())
        };

        if resolved_opcode_id == 0 {
            if params
                .as_object()
                .and_then(|params| params.get("FILTER").or_else(|| params.get("filter")))
                .and_then(|value| value.as_str())
                .is_some()
                && params
                    .as_object()
                    .and_then(|params| params.get("FROM").or_else(|| params.get("from")))
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("DISCARD"))
                    .unwrap_or(false)
            {
                return Self::with_raw_parts(
                    O_SELECT_CARDS,
                    value.max(1),
                    filter.to_attr() | filter_passthrough,
                    slot.to_raw(),
                    false,
                    params,
                );
            }
        }

        if opcode_key == "NOP" {
            if let Some(decoded_name) = decoded_hint_name.as_deref() {
                if resolved_opcode_id == 0 {
                    let mut params_obj = params.as_object().cloned().unwrap_or_default();
                    params_obj.insert("raw_cond".to_string(), Value::String(decoded_name.to_string()));
                    if decoded_name == "UNIQUE_NAMES_COUNT" {
                        params_obj.insert("MIN".to_string(), Value::from(value.max(0)));
                    }
                    return Self::with_raw_parts(
                        0,
                        value,
                        filter.to_attr() | filter_passthrough,
                        slot.to_raw(),
                        false,
                        Value::Object(params_obj),
                    );
                }
            }
        }

        match opcode_key.as_str() {
            "RETURN" => {
                if !params.is_null() {
                    eprintln!(
                        "[FRAME_LOAD] preserving RETURN frame params={} value={} attr={:#x} slot={}",
                        params,
                        value,
                        filter.to_attr() | filter_passthrough,
                        slot.to_raw()
                    );
                }
                Self::with_raw_parts(
                    O_RETURN,
                    value,
                    filter.to_attr() | filter_passthrough,
                    slot.to_raw(),
                    is_cost,
                    params,
                )
            }
            "DRAW" => Self::with_components(O_DRAW, value, CardFilter::default(), slot, is_cost, params),
            "RECOVER_LIVE" => Self::with_raw_parts(
                O_RECOVER_LIVE,
                value,
                filter.to_attr() | filter_passthrough,
                slot.to_raw(),
                is_cost,
                recover_params.clone(),
            ),
            "RECOVER_MEMBER" => Self::with_raw_parts(
                O_RECOVER_MEMBER,
                value,
                filter.to_attr() | filter_passthrough,
                slot.to_raw(),
                is_cost,
                recover_params.clone(),
            ),
            "LOOK_AND_CHOOSE" => {
                // Read individual LAC fields if present; fall back to packed `value`.
                let decoded_text = Self::first_str(payload, &["decoded"])
                    .or_else(|| Self::first_str(frame, &["decoded"]))
                    .unwrap_or("");
                let summary_text = Self::first_str(payload, &["summary"])
                    .or_else(|| Self::first_str(frame, &["summary"]))
                    .unwrap_or("");
                let value_payload = payload.get("value");
                let structured_i64 = |key: &str| {
                    payload.get(key).and_then(|v| v.as_i64())
                        .or_else(|| params.get(key).and_then(|v| v.as_i64()))
                        .or_else(|| value_payload.and_then(|v| v.get(key)).and_then(|v| v.as_i64()))
                };
                let structured_bool = |key: &str| {
                    payload.get(key).and_then(|v| v.as_bool())
                        .or_else(|| params.get(key).and_then(|v| v.as_bool()))
                        .or_else(|| value_payload.and_then(|v| v.get(key)).and_then(|v| v.as_bool()))
                };
                let lac_count = structured_i64("count")
                    .or_else(|| Self::extract_u8_from_text(decoded_text, &["look=", "look_count=", "count="]).map(|v| v as i64))
                    .or_else(|| Self::extract_u8_from_text(summary_text, &["look at ", "look ", "count="]).map(|v| v as i64))
                    .unwrap_or(value as i64) as u8;
                let lac_choose = structured_i64("choose_count")
                    .or_else(|| Self::extract_u8_from_text(decoded_text, &["choose=", "choose "]).map(|v| v as i64))
                    .or_else(|| Self::extract_u8_from_text(summary_text, &["choose "]).map(|v| v as i64))
                    .unwrap_or(0) as u8;
                let lac_reveal = structured_bool("reveal").unwrap_or(false);
                let lac_dest = structured_bool("dest_discard").unwrap_or(false);
                let lac_c1 = structured_i64("char_id_1").unwrap_or(0) as u8;
                let lac_c2 = structured_i64("char_id_2").unwrap_or(0) as u8;
                let lac_c3 = structured_i64("char_id_3").unwrap_or(0) as u8;
                let packed = crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
                    count: lac_count, choose_count: lac_choose, reveal: lac_reveal,
                    dest_discard: lac_dest, char_id_1: lac_c1, char_id_2: lac_c2, char_id_3: lac_c3,
                }.to_raw();
                let mut lac_params = params.as_object().cloned().unwrap_or_default();
                lac_params.insert("count".to_string(), Value::from(lac_count));
                lac_params.insert("choose_count".to_string(), Value::from(lac_choose));
                lac_params.insert("char_id_1".to_string(), Value::from(lac_c1));
                lac_params.insert("char_id_2".to_string(), Value::from(lac_c2));
                lac_params.insert("char_id_3".to_string(), Value::from(lac_c3));
                lac_params.insert("reveal".to_string(), Value::from(lac_reveal));
                lac_params.insert("dest_discard".to_string(), Value::from(lac_dest));
                if let Some((params_filter, _)) =
                    crate::core::logic::filter::filter_parts_from_params(Some(&params))
                {
                    filter = filter.with_overlay(&params_filter);
                }
                if params
                    .get("filter")
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("COST_LE_REVEALED"))
                    .unwrap_or(false)
                {
                    filter.is_enabled = true;
                    filter.value_enabled = true;
                    filter.value_threshold = 1;
                    filter.is_le = true;
                    filter.is_cost_type = true;
                }
                let mut attr = filter.to_attr() | filter_passthrough;
                if params
                    .get("filter")
                    .and_then(|value| value.as_str())
                    .map(|value| value.eq_ignore_ascii_case("COST_LE_REVEALED"))
                    .unwrap_or(false)
                {
                    attr |= crate::core::generated_constants::FILTER_REVEALED_CONTEXT;
                }
                Self::with_raw_parts(
                    O_LOOK_AND_CHOOSE,
                    packed,
                    attr,
                    slot.to_raw(),
                    is_cost,
                    Value::Object(lac_params),
                )
            }
            "SELECT_MEMBER" => Self::with_raw_parts(O_SELECT_MEMBER, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            "MOVE_MEMBER" => Self::with_raw_parts(O_MOVE_MEMBER, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            "META_RULE" => Self::with_raw_parts(O_META_RULE, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params),
            _ => {
                let raw_op = if is_negated && resolved_opcode_id < crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
                    resolved_opcode_id + crate::core::logic::constants::OPCODE_NEGATION_OFFSET
                } else {
                    resolved_opcode_id
                };
                Self::with_raw_parts(raw_op, value, filter.to_attr() | filter_passthrough, slot.to_raw(), is_cost, params)
            },
        }
    }

    pub fn from_instruction_words(words: &[i32], ip: usize) -> Self {
        let opcode = words.get(ip).copied().unwrap_or_default();
        let value = words.get(ip + 1).copied().unwrap_or_default();
        let attr_low = words.get(ip + 2).copied().unwrap_or_default() as u32 as u64;
        let attr_high = words.get(ip + 3).copied().unwrap_or_default() as u32 as u64;
        let slot = words.get(ip + 4).copied().unwrap_or_default();
        let attr = (attr_high << 32) | attr_low;
        Self::with_raw_parts(opcode, value, attr, slot, false, Value::Null)
    }

    pub fn new(opcode: i32, value: i32, attr: i64, raw_s: i32, is_cost: bool) -> Self {
        Self::with_raw_parts(opcode, value, attr as u64, raw_s, is_cost, Value::Null)
    }

    /// Create a RETURN frame.
    pub fn new_return() -> Self {
        AbilityFrame { opcode: O_RETURN, ..Default::default() }
    }

    /// Returns the opcode with the negation offset removed (if negated).
    pub fn effective_opcode(&self) -> i32 {
        if self.opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET {
            self.opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            self.opcode
        }
    }

    pub fn from_effect(effect: &Effect) -> Self {
        let runtime_opcode = if effect.runtime_opcode != 0 {
            effect.runtime_opcode
        } else {
            Self::opcode_from_effect_type(effect.effect_type)
        };
        let runtime_value_json = effect.value.clone();
        let runtime_attr = effect.runtime_attr;
        let mut runtime_slot = effect.runtime_slot;
        let mut slot = DecodedSlot::decode(runtime_slot);

        if let Some(destination) = effect
            .params
            .as_object()
            .and_then(|params| params.get("destination"))
            .and_then(|value| value.as_str())
        {
            match destination.to_ascii_lowercase().as_str() {
                "card_hand" => slot.target_slot = 6,
                "card_discard" => slot.target_slot = 7,
                _ => {}
            }
        }

        if let Some(source) = effect
            .params
            .as_object()
            .and_then(|params| {
                params
                    .get("source")
                    .or_else(|| params.get("SOURCE"))
                    .or_else(|| params.get("from"))
                    .or_else(|| params.get("FROM"))
            })
            .and_then(|value| value.as_str())
            .and_then(Self::zone_from_text)
        {
            slot.source_zone = source;
        }

        if let Some(dest_zone) = effect
            .params
            .as_object()
            .and_then(|params| {
                params
                    .get("destination")
                    .or_else(|| params.get("DESTINATION"))
                    .or_else(|| params.get("dest"))
                    .or_else(|| params.get("DEST"))
                    .or_else(|| params.get("to"))
                    .or_else(|| params.get("TO"))
            })
            .and_then(|value| value.as_str())
            .and_then(Self::zone_from_text)
        {
            slot.dest_zone = dest_zone;
        }

        if effect
            .params
            .as_object()
            .and_then(|params| params.get("card_type"))
            .and_then(|value| value.as_str())
            .map(|value| value.eq_ignore_ascii_case("live"))
            .unwrap_or(false)
        {
            slot.is_reveal_until_live = true;
        }

        if effect
            .params
            .as_object()
            .and_then(|params| params.get("wait").or_else(|| params.get("WAIT")))
            .and_then(|value| value.as_bool())
            .unwrap_or(false)
        {
            slot.is_wait = true;
        }

        runtime_slot = slot.to_raw();

        // Use runtime_value if set, otherwise extract from JSON value
        let value_i32 = if effect.runtime_value != 0 {
            effect.runtime_value
        } else {
            match runtime_value_json {
                Value::Number(n) => n.as_i64().unwrap_or(0) as i32,
                Value::Object(obj) => {
                    obj.get("count")
                        .and_then(|v| v.as_i64())
                        .or_else(|| obj.get("value").and_then(|v| v.as_i64()))
                        .unwrap_or(0) as i32
                }
                _ => 0,
            }
        };

        // When a formation-change opcode already encodes a permutation index in value,
        // keep that runtime shape instead of forcing an interactive prompt.
        if runtime_opcode == O_SWAP_AREA {
            return Self::with_raw_parts(O_SWAP_AREA, 0, 0, 4, false, Value::Null);
        }

        if runtime_opcode == O_FORMATION_CHANGE {
            return Self::with_raw_parts(O_FORMATION_CHANGE, 0, 0, 4, false, Value::Null);
        }

        if !effect.params.is_null() || effect.is_optional {
            let mut filter = CardFilter::from_attr(runtime_attr as u64);
            let runtime_passthrough = runtime_attr & !filter.to_attr();
            let mut params_passthrough = 0u64;

            if let Some((params_filter, passthrough)) = crate::core::logic::filter::filter_parts_from_params(Some(&effect.params)) {
                params_passthrough = passthrough;
                filter = filter.with_overlay(&params_filter);
            }
            if effect.is_optional {
                filter.is_enabled = true;
                filter.is_optional = true;
            }
            if filter.target_player == 0 {
                filter.target_player = if slot.is_opponent {
                    TARGET_PLAYER_OPPONENT as u8
                } else {
                    TARGET_PLAYER_SELF as u8
                };
            }
            return AbilityFrame {
                opcode: runtime_opcode,
                value: value_i32,
                attr: filter.to_attr() | runtime_passthrough | params_passthrough,
                slot: slot.to_raw(),
                is_cost: false,
                params: effect.params.clone(),
            };
        }
        Self::new(runtime_opcode, value_i32, runtime_attr as i64, runtime_slot, false)
    }

    pub fn opcode(&self) -> i32 {
        self.opcode
    }

    pub fn is_cost(&self) -> bool {
        self.is_cost
    }

    pub fn components(&self) -> AbilityFrameComponents<'_> {
        let raw_opcode = self.opcode;
        let is_negated = raw_opcode >= crate::core::logic::constants::OPCODE_NEGATION_OFFSET;
        let opcode = if is_negated {
            raw_opcode - crate::core::logic::constants::OPCODE_NEGATION_OFFSET
        } else {
            raw_opcode
        };
        let mut raw_attr = self.attr;
        if opcode == O_MOVE_MEMBER && !self.params.is_null() {
            let params = &self.params;
            if params.get("destination").is_some()
                || params.get("DESTINATION").is_some()
                || params.get("source").is_some()
                || params.get("SOURCE").is_some()
            {
                raw_attr |= 99;
            }
        }
        AbilityFrameComponents {
            raw_opcode,
            opcode,
            value: self.value,
            filter: CardFilter::from_attr(self.attr),
            slot: DecodedSlot::decode(self.slot),
            raw_attr,
            raw_slot: self.slot,
            is_negated,
            is_cost: self.is_cost,
            params: if self.params.is_null() { None } else { Some(&self.params) },
        }
    }

    pub fn value(&self) -> i32 {
        self.value
    }

    pub fn attr(&self) -> u64 {
        self.attr
    }

    pub fn slot(&self) -> i32 {
        self.slot
    }

    pub fn look_choose(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        Self::decode_look_choose(
            self.value,
            if self.params.is_null() {
                None
            } else {
                Some(&self.params)
            },
        )
    }

    pub fn is_dynamic(&self) -> bool {
        (self.attr()
            & (A_STANDARD_COMPARE_ACCUMULATED_MASK << A_STANDARD_COMPARE_ACCUMULATED_SHIFT) as u64)
            != 0
    }
    pub fn scalar_dynamic_base(&self) -> i32 {
        if let Some((base_value, _)) = scalar_dynamic_param_parts(Some(&self.params), self.value()) {
            return base_value;
        }
        ((self.value() as u32 >> V_SCALAR_DYNAMIC_BASE_VALUE_SHIFT)
            & V_SCALAR_DYNAMIC_BASE_VALUE_MASK) as i32
    }
    pub fn scalar_dynamic_divisor(&self) -> i32 {
        if let Some((_, divisor)) = scalar_dynamic_param_parts(Some(&self.params), self.value()) {
            return divisor;
        }
        ((self.value() as u32 >> V_SCALAR_DYNAMIC_DIVISOR_SHIFT) & V_SCALAR_DYNAMIC_DIVISOR_MASK)
            as i32
    }
    pub fn heart_requirements(
        &self,
    ) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        crate::core::logic::interpreter::instruction::DecodedHeartRequirements::decode(
            self.attr() as i64
        )
    }
    pub fn heart_counts(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        crate::core::logic::interpreter::instruction::DecodedHeartCounts::decode(self.value())
    }

    pub fn filter(&self) -> CardFilter {
        CardFilter::from_attr(self.attr)
    }

    pub fn dslot(&self) -> DecodedSlot {
        DecodedSlot::decode(self.slot)
    }

    pub fn append_instruction_words(&self, words: &mut Vec<i32>) {
        words.push(self.opcode);
        words.push(self.value);
        words.push(self.attr as u32 as i32);
        words.push((self.attr >> 32) as u32 as i32);
        words.push(self.slot);
    }
}

impl From<&AbilityFrame> for AbilityFrame {
    fn from(frame: &AbilityFrame) -> Self {
        frame.clone()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct FrameProgram {
    pub frames: Vec<AbilityFrame>,
    pub raw_program: Option<Value>,
}

impl Serialize for FrameProgram {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        if let Some(raw) = &self.raw_program {
            let has_structured_frames = raw
                .get("frames")
                .and_then(|v| v.as_array())
                .map(|frames| !frames.is_empty())
                .unwrap_or(false);

            if has_structured_frames {
                return raw.serialize(serializer);
            }

            let mut merged = raw.as_object().cloned().unwrap_or_default();
            merged.insert(
                "frames".to_string(),
                Value::Array(
                    self.frames
                        .iter()
                        .map(|frame| serde_json::to_value(frame).unwrap_or(Value::Null))
                        .collect(),
                ),
            );
            return Value::Object(merged).serialize(serializer);
        }

        let mut map = serde_json::Map::new();
        map.insert(
            "frames".to_string(),
            Value::Array(
                self.frames
                    .iter()
                    .map(|frame| serde_json::to_value(frame).unwrap_or(Value::Null))
                    .collect(),
            ),
        );
        Value::Object(map).serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for FrameProgram {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let raw_program = Value::deserialize(deserializer)?;
        let frames = raw_program
            .get("frames")
            .and_then(|v| v.as_array())
            .map(|frames| {
                frames
                    .iter()
                    .map(AbilityFrame::from_json_value)
                    .collect::<Vec<_>>()
            })
            .unwrap_or_default();

        Ok(Self {
            frames,
            raw_program: Some(raw_program),
        })
    }
}

impl Hash for FrameProgram {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.frames.hash(state);
        if let Some(raw_program) = &self.raw_program {
            if let Ok(raw_json) = serde_json::to_string(raw_program) {
                raw_json.hash(state);
            }
        }
    }
}

impl FrameProgram {
    pub fn from_instruction_words(words: &[i32]) -> Self {
        let mut frames = Vec::with_capacity(
            words.len() / crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
        );
        let mut ip = 0;
        while ip < words.len() {
            frames.push(AbilityFrame::from_instruction_words(words, ip));
            ip += crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION;
        }

        Self {
            frames,
            raw_program: Some(serde_json::json!({
                "frames": [],
                "instruction_words": words,
            })),
        }
    }

    pub fn to_words(&self) -> Vec<i32> {
        if let Some(raw_program) = &self.raw_program {
            if let Some(words) = raw_program.get("instruction_words").and_then(|v| v.as_array()) {
                let mut instruction_words = Vec::with_capacity(words.len());
                for word in words {
                    if let Some(value) = word.as_i64() {
                        instruction_words.push(value as i32);
                    }
                }
                if !instruction_words.is_empty() {
                    return instruction_words;
                }
            }
        }

        let mut words = Vec::with_capacity(
            self.frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
        );
        for frame in &self.frames {
            frame.append_instruction_words(&mut words);
        }
        words
    }

}

// Re-export constants so they're available to all modules using `use super::models::*;`
pub use crate::core::logic::constants::*;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Condition {
    #[serde(rename = "type")]
    pub condition_type: ConditionType,
    #[serde(default)]
    pub value: i32,
    #[serde(default)]
    pub attr: u64,
    #[serde(default)]
    pub target_slot: u8,
    #[serde(default)]
    pub is_negated: bool,
    #[serde(default)]
    pub params: serde_json::Value,
}

impl std::hash::Hash for Condition {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.condition_type.hash(state);
        self.value.hash(state);
        self.attr.hash(state);
        self.target_slot.hash(state);
        self.is_negated.hash(state);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Effect {
    pub effect_type: EffectType,
    #[serde(default)]
    pub value: serde_json::Value,
    #[serde(default)]
    pub value_cond: ConditionType,
    #[serde(default)]
    pub target: TargetType,
    #[serde(default)]
    pub is_optional: bool,
    #[serde(default)]
    pub params: serde_json::Value,
    #[serde(default)]
    pub runtime_opcode: i32,
    #[serde(default)]
    pub runtime_value: i32,
    #[serde(default)]
    pub runtime_attr: u64,
    #[serde(default)]
    pub runtime_slot: i32,
    #[serde(default)]
    pub modal_options: serde_json::Value,
}

impl Effect {
}

impl std::hash::Hash for Effect {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.effect_type.hash(state);
        // Hash the JSON Value directly (serde_json::Value implements Hash)
        std::hash::Hash::hash(&self.value, state);
        self.value_cond.hash(state);
        self.target.hash(state);
        self.is_optional.hash(state);
        self.runtime_opcode.hash(state);
        self.runtime_value.hash(state);
        self.runtime_attr.hash(state);
        self.runtime_slot.hash(state);
        std::hash::Hash::hash(&self.modal_options, state);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Cost {
    #[serde(rename = "type")]
    pub cost_type: AbilityCostType,
    #[serde(default)]
    pub value: i32,
    #[serde(default)]
    pub is_optional: bool,
    #[serde(default)]
    pub params: serde_json::Value,
}

impl std::hash::Hash for Cost {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.cost_type.hash(state);
        self.value.hash(state);
        self.is_optional.hash(state);
        // params is skipped
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Hash)]
pub struct AbilityContext {
    pub player_id: u8,
    pub activator_id: u8, // The player who originally triggered/activated the ability
    pub area_idx: i16,
    pub source_card_id: i32,
    #[serde(default)]
    pub ability_card_id: i32,
    pub target_card_id: i32,
    pub target_slot: i16,
    pub selected_hand_idx: i16,
    pub choice_index: i16,
    /// Accumulated value (e.g. remaining cost limit for multi-card plays)
    pub v_accumulated: i16,
    pub selected_color: i16,
    pub program_counter: u16,
    pub ability_index: i16,
    pub v_remaining: i16,
    #[serde(default)]
    pub trigger_type: TriggerType,
    #[serde(default)]
    pub original_phase: Option<Phase>,
    #[serde(default)]
    pub original_current_player: Option<u8>,
    #[serde(default)]
    pub repeat_count: i16, // For O_REPEAT_ABILITY: tracks how many times ability has repeated
    #[serde(default)]
    pub selected_cards: smallvec::SmallVec<[i32; 8]>, // IDs of cards picked in the current/last selection action
    #[serde(default)]
    pub selected_target_keys: smallvec::SmallVec<[i32; 8]>,
    #[serde(default)]
    pub auto_pick: bool, // If true, mandatory single-choice steps (like O_SELECT_MODE) will resolve automatically
    #[serde(default)]
    pub is_static_eval: bool, // If true, skip phase restoration in finish_execution
    #[serde(default)]
    pub skip_initial_condition_precheck: bool,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct StaticAbilityContext {
    pub player_id: u8,
    pub activator_id: u8,
    pub area_idx: i16,
    pub source_card_id: i32,
    pub ability_card_id: i32,
    pub target_card_id: i32,
    pub target_slot: i16,
    pub ability_index: i16,
    pub trigger_type: TriggerType,
    pub original_phase: Option<Phase>,
    pub original_current_player: Option<u8>,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash, Default)]
pub struct AbilityExecutionState {
    pub choice_index: i16,
    pub v_accumulated: i16,
    pub program_counter: u16,
    pub v_remaining: i16,
    pub repeat_count: i16,
    pub selected_cards: smallvec::SmallVec<[i32; 8]>,
    pub selected_target_keys: smallvec::SmallVec<[i32; 8]>,
    pub selected_color: i16,
    pub auto_pick: bool,
}

impl Default for AbilityContext {
    fn default() -> Self {
        Self {
            player_id: 0,
            activator_id: 0,
            area_idx: -1,
            source_card_id: -1,
            ability_card_id: -1,
            target_card_id: -1,
            target_slot: -1,
            selected_hand_idx: -1,
            choice_index: -1,
            selected_color: 0,
            program_counter: 0,
            ability_index: -1,
            v_accumulated: 0,
            v_remaining: -1,
            trigger_type: TriggerType::None,
            original_phase: None,
            original_current_player: None,
            repeat_count: 0,
            selected_cards: smallvec::SmallVec::new(),
            selected_target_keys: smallvec::SmallVec::new(),
            auto_pick: false,
            is_static_eval: false,
            skip_initial_condition_precheck: false,
        }
    }
}

impl AbilityContext {
    pub fn capture_state_raw(&mut self, phase: crate::core::enums::Phase, current_player: u8) {
        self.original_phase = Some(phase);
        self.original_current_player = Some(current_player);
    }

    pub fn execution_state(&self) -> AbilityExecutionState {
        AbilityExecutionState {
            choice_index: self.choice_index,
            v_accumulated: self.v_accumulated,
            program_counter: self.program_counter,
            v_remaining: self.v_remaining,
            repeat_count: self.repeat_count,
            selected_cards: self.selected_cards.clone(),
            selected_target_keys: self.selected_target_keys.clone(),
            selected_color: self.selected_color,
            auto_pick: self.auto_pick,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct PendingInteraction {
    pub ctx: AbilityContext,
    pub card_id: i32,
    #[serde(default)]
    pub ability_card_id: i32,
    pub ability_index: i16,
    pub effect_opcode: i32,
    pub target_slot: i32,
    #[serde(default)]
    pub choice_type: ChoiceType,
    #[serde(default)]
    pub filter: CardFilter,
    pub filter_attr: u64,
    pub choice_text: String,
    pub v_remaining: i16,
    #[serde(default)]
    pub original_phase: Phase,
    #[serde(default)]
    pub original_current_player: u8,
    #[serde(default)]
    pub actions: Vec<i32>,
    #[serde(default)]
    pub options: Vec<Value>,
    #[serde(default)]
    pub execution_id: u32,
    #[serde(default)]
    pub same_unit_discard: bool,
}

impl Default for PendingInteraction {
    fn default() -> Self {
        Self {
            ctx: AbilityContext::default(),
            card_id: -1,
            ability_card_id: -1,
            ability_index: -1,
            effect_opcode: 0,
            target_slot: -1,
            choice_type: ChoiceType::default(),
            filter: CardFilter::default(),
            filter_attr: 0,
            choice_text: String::new(),
            v_remaining: -1,
            original_phase: Phase::default(),
            original_current_player: 0,
            actions: Vec::new(),
            options: Vec::new(),
            execution_id: 0,
            same_unit_discard: false,
        }
    }
}

impl PendingInteraction {
    pub fn filter_attr_without_state_flags(&self) -> u64 {
        self.filter_attr & !crate::core::logic::filter::FILTER_STATE_FLAGS_MASK
    }

    pub fn is_move_to_discard_prompt(&self) -> bool {
        self.effect_opcode == crate::core::generated_constants::O_MOVE_TO_DISCARD
    }

    pub fn is_hand_discard_prompt(&self) -> bool {
        self.is_move_to_discard_prompt() && self.choice_type == ChoiceType::SelectHandDiscard
    }

    pub fn discard_selection_filter_attr(&self) -> u64 {
        let masked = self.filter_attr_without_state_flags();
        if self.choice_type == ChoiceType::SelectHandDiscard {
            masked & !0x3
        } else {
            masked
        }
    }

    pub fn has_structured_filter_constraints(&self) -> bool {
        crate::core::logic::filter::has_structured_filter_constraints(self.filter_attr)
    }

    pub fn selection_target_zone(&self) -> Option<usize> {
        let filter = self.filter;
        if filter.zone_mask != 0 {
            Some(filter.zone_mask as usize)
        } else {
            let fallback_filter = crate::core::logic::filter::structured_filter_from_attr(
                self.filter_attr,
            );
            if fallback_filter.zone_mask != 0 {
                return Some(fallback_filter.zone_mask as usize);
            }
            let packed_zone =
                ((self.filter_attr & crate::core::logic::constants::FILTER_MASK_LOWER) >> 12)
                    & 0x0F;
            (packed_zone > 0).then_some(packed_zone as usize)
        }
    }

    pub fn uses_total_cost_budget(&self) -> bool {
        self.filter.compare_accumulated
            || (self.filter_attr & crate::core::generated_constants::FILTER_TOTAL_COST) != 0
    }

    pub fn is_baton_slot_only(&self) -> bool {
        ((self.target_slot as u64) & crate::core::generated_constants::FLAG_BATON_SLOT_ONLY) != 0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default, Hash)]
pub struct PreparsedModifier {
    pub op: i32,
    pub val: i32,
    pub attr: u64,
    pub slot: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Ability {
    #[serde(default)]
    pub raw_text: String,
    pub trigger: TriggerType,
    #[serde(default)]
    pub effects: Vec<Effect>,
    #[serde(default)]
    pub conditions: Vec<Condition>,
    #[serde(default)]
    pub costs: Vec<Cost>,
    #[serde(default)]
    pub is_once_per_turn: bool,
    #[serde(default)]
    pub turn_limit: u8,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub frame_program: Option<FrameProgram>,
    #[serde(default)]
    pub requires_selection: bool,
    #[serde(default)]
    pub choice_flags: u8,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default, skip_serializing)]
    pub opcodes_mask: u128,
    #[serde(default)]
    pub option_names: Vec<String>,
    #[serde(default)]
    pub modal_options: serde_json::Value,
    #[serde(default)]
    pub pseudocode: String,
    #[serde(default)]
    pub preparsed_modifiers: Vec<PreparsedModifier>,
    #[serde(default)]
    pub filters: Vec<crate::core::logic::filter::CardFilter>,
    #[serde(default, skip_serializing)]
    pub runtime_metadata_ready: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_deck_top_window: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_frame_cost_checks: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_optional_frame: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_optional_cost: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_activation_conditions: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_look_choose_checks: bool,
    #[serde(default, skip_serializing)]
    pub runtime_has_interactive_prompt: bool,
    #[serde(default, skip_serializing)]
    pub runtime_prompt_before_count_blades: bool,
    #[serde(default, skip_serializing)]
    pub runtime_prompt_before_count_hearts: bool,
}

impl std::hash::Hash for Ability {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.raw_text.hash(state);
        self.trigger.hash(state);
        self.effects.hash(state);
        self.conditions.hash(state);
        self.costs.hash(state);
        self.is_once_per_turn.hash(state);
        self.turn_limit.hash(state);
        self.requires_selection.hash(state);
        self.choice_flags.hash(state);
        self.choice_count.hash(state);
        self.opcodes_mask.hash(state);
        self.option_names.hash(state);
        self.pseudocode.hash(state);
        self.preparsed_modifiers.hash(state);
        self.filters.hash(state);
        self.runtime_metadata_ready.hash(state);
        self.runtime_has_deck_top_window.hash(state);
        self.runtime_has_frame_cost_checks.hash(state);
        self.runtime_has_optional_frame.hash(state);
        self.runtime_has_optional_cost.hash(state);
        self.runtime_has_activation_conditions.hash(state);
        self.runtime_has_look_choose_checks.hash(state);
        self.runtime_has_interactive_prompt.hash(state);
        self.runtime_prompt_before_count_blades.hash(state);
        self.runtime_prompt_before_count_hearts.hash(state);
        // modal_options skipped
    }
}

impl Ability {
    pub fn per_turn_limit(&self) -> u8 {
        if self.turn_limit > 0 {
            self.turn_limit
        } else if self.is_once_per_turn {
            1
        } else {
            0
        }
    }

    pub(crate) fn has_authored_frame_program(&self) -> bool {
        self.frame_program
            .as_ref()
            .map(|program| !program.frames.is_empty())
            .unwrap_or(false)
    }

    pub fn resolved_frame_source(&self) -> &'static str {
        if self.has_authored_frame_program() {
            "frame_program"
        } else if !self.effects.is_empty() {
            "effects"
        } else {
            "none"
        }
    }

    /// Check if ability has any effects
    pub fn has_effects(&self) -> bool {
        !self.effects.is_empty()
    }

    /// Get the number of modal options from the canonical authored frame program when present.
    pub fn modal_option_count(&self) -> usize {
        if self.has_authored_frame_program() {
            let frames = self.resolved_frames();
            return frames
                .iter()
                .position(|frame| frame.opcode() == O_SELECT_MODE)
                .and_then(|select_mode_idx| {
                    let jump_count = frames
                        .iter()
                        .skip(select_mode_idx + 1)
                        .take_while(|frame| frame.opcode() == O_JUMP)
                        .count();
                    (jump_count > 0).then_some(jump_count)
                })
                .unwrap_or(0);
        }

        self.effects
            .first()
            .and_then(|e| e.modal_options.as_array())
            .map(|opts| opts.len())
            .unwrap_or(0)
    }

    /// Get effects for a specific modal option
    pub fn get_modal_effects(&self, choice_idx: usize) -> Option<Vec<Effect>> {
        self.effects.first()
            .and_then(|e| e.modal_options.as_array())
            .and_then(|opts| opts.get(choice_idx))
            .and_then(|opt| opt.as_array())
            .map(|arr| {
                arr.iter()
                    .filter_map(|v| serde_json::from_value(v.clone()).ok())
                    .collect()
            })
    }

    fn authored_modal_option_frames(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        let frames = self.resolved_frames();
        let select_mode_idx = frames.iter().position(|frame| frame.opcode() == O_SELECT_MODE)?;
        let option_count = frames[select_mode_idx].value().max(0) as usize;
        let branch_table_len = frames
            .iter()
            .skip(select_mode_idx + 1)
            .take_while(|frame| frame.opcode() == O_JUMP)
            .count();
        if branch_table_len == 0 {
            return None;
        }

        let mut cursor = select_mode_idx + 1 + branch_table_len;
        for option_idx in 0..option_count.max(branch_table_len) {
            let start = cursor;
            let mut saw_body_frame = false;
            while cursor < frames.len() {
                let opcode = frames[cursor].opcode();
                if matches!(opcode, O_JUMP) {
                    break;
                }
                if opcode == O_RETURN && saw_body_frame {
                    break;
                }
                saw_body_frame = true;
                cursor += 1;
            }

            let option_frames = frames[start..cursor].to_vec();
            if option_idx == choice_idx {
                if !option_frames.is_empty() {
                    return Some(option_frames);
                }

                break;
            }

            if cursor >= frames.len() {
                break;
            }
            cursor += 1;
        }

        let jump_frame_idx = select_mode_idx + 1 + choice_idx;
        let jump_frame = frames.get(jump_frame_idx)?;
        if jump_frame.opcode() != O_JUMP {
            return None;
        }

        let target_frame_idx = select_mode_idx + 2 + choice_idx + jump_frame.value().max(0) as usize;
        let mut option_frames = Vec::new();
        for frame in frames.iter().skip(target_frame_idx) {
            if matches!(frame.opcode(), O_JUMP | O_RETURN) {
                break;
            }
            option_frames.push(frame.clone());
        }

        (!option_frames.is_empty()).then_some(option_frames)
    }

    /// Get modal option frames from the canonical authored frame program when present.
    pub fn get_modal_option_frames(&self, choice_idx: usize) -> Option<Vec<AbilityFrame>> {
        if self.has_authored_frame_program() {
            return self.authored_modal_option_frames(choice_idx);
        }

        self.get_modal_effects(choice_idx).map(|effects| {
            effects.iter()
                .map(|e| AbilityFrame::from_effect(e))
                .collect()
        })
    }

    pub fn resolved_frames(&self) -> Cow<'_, [AbilityFrame]> {
        if let Some(ref frame_program) = self.frame_program {
            return Cow::Borrowed(&frame_program.frames);
        }

        if !self.effects.is_empty() {
            return Cow::Owned(
                self.effects
                    .iter()
                    .map(AbilityFrame::from_effect)
                    .collect(),
            );
        }

        Cow::Borrowed(&[])
    }

    pub fn has_resolved_frames(&self) -> bool {
        !self.resolved_frames().is_empty()
    }

    pub fn runtime_has_deck_top_window(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_deck_top_window;
        }
        self.resolved_frames()
            .iter()
            .any(|frame| frame.dslot().source_zone == Zone::DeckTop)
    }

    pub fn runtime_has_frame_cost_checks(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_frame_cost_checks;
        }
        self.resolved_frames().iter().any(|frame| {
            let data = frame.components();
            let implicit_deck_cost = matches!(
                data.opcode,
                O_MOVE_MEMBER | O_MOVE_TO_DISCARD | O_MOVE_TO_DECK
            ) && matches!(
                data.slot.source_zone,
                Zone::Deck | Zone::DeckTop | Zone::DeckBottom | Zone::Default
            );
            frame.is_cost() || implicit_deck_cost
        })
    }

    pub fn runtime_has_optional_frame(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_optional_frame;
        }
        self.resolved_frames()
            .iter()
            .any(|frame| frame.components().filter.is_optional)
    }

    pub fn runtime_has_optional_cost(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_optional_cost;
        }
        self.costs.iter().any(|cost| cost.is_optional)
    }

    pub fn runtime_has_activation_conditions(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_activation_conditions;
        }
        self.conditions.iter().any(|condition| {
            !matches!(
                condition.condition_type,
                ConditionType::SumValue | ConditionType::DiscardedCards
            )
        })
    }

    pub fn runtime_has_look_choose_checks(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_look_choose_checks;
        }
        self.resolved_frames()
            .iter()
            .any(|frame| frame.opcode() == O_LOOK_AND_CHOOSE && !frame.is_cost())
    }

    pub fn runtime_has_interactive_prompt(&self) -> bool {
        if self.runtime_metadata_ready {
            return self.runtime_has_interactive_prompt;
        }
        self.resolved_frames().iter().any(|frame| {
            matches!(
                frame.opcode(),
                O_SELECT_MEMBER
                    | O_SELECT_LIVE
                    | O_SELECT_PLAYER
                    | O_SELECT_MODE
                    | O_SELECT_CARDS
                    | O_LOOK_AND_CHOOSE
                    | O_COLOR_SELECT
                    | O_TAP_MEMBER
                    | O_TAP_OPPONENT
                    | O_TRIGGER_REMOTE
            )
        })
    }

    pub fn words(&self) -> Vec<i32> {
        if let Some(ref frame_program) = self.frame_program {
            return frame_program.to_words();
        }

        let frames = self.resolved_frames();
        if !frames.is_empty() {
            let mut words = Vec::with_capacity(
                frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION,
            );
            for frame in frames.iter() {
                frame.append_instruction_words(&mut words);
            }
            return words;
        }

        Vec::new()
    }

    pub fn get_frame(&self, frame_idx: usize) -> Option<AbilityFrame> {
        self.resolved_frames().get(frame_idx).cloned()
    }

    pub fn frames(&self) -> Vec<AbilityFrame> {
        self.resolved_frames().into_owned()
    }

    pub fn trace_view(&self) -> AbilityTraceView {
        let frames = self.resolved_frames();
        let steps = frames
            .iter()
            .map(|frame| frame.components().to_trace_step())
            .collect();
        let mut action_routes = Vec::new();

        if self.trigger == TriggerType::Activated {
            action_routes.push(
                "engine_rust_src/src/core/logic/action_gen/main_phase.rs".to_string(),
            );
        }
        if frames.iter().any(|frame| {
            matches!(
                frame.opcode(),
                O_SELECT_MODE
                    | O_SELECT_MEMBER
                    | O_SELECT_CARDS
                    | O_SELECT_LIVE
                    | O_SELECT_PLAYER
                    | O_LOOK_AND_CHOOSE
            )
        }) {
            action_routes.push("engine_rust_src/src/core/logic/action_gen/response.rs".to_string());
        }
        if frames.iter().any(|frame| {
            matches!(
                frame.opcode(),
                O_MOVE_TO_DISCARD
                    | O_MOVE_MEMBER
                    | O_MOVE_TO_DECK
                    | O_RECOVER_LIVE
                    | O_RECOVER_MEMBER
                    | O_DRAW
            )
        }) {
            action_routes.push(
                "engine_rust_src/src/core/logic/interpreter/handlers/interaction.rs".to_string(),
            );
        }
        if frames.iter().any(|frame| {
            matches!(
                frame.opcode(),
                O_BOOST_SCORE
                    | O_ADD_BLADES
                    | O_ADD_HEARTS
                    | O_SET_SCORE
                    | O_REDUCE_SCORE
                    | O_REDUCE_COST
                    | O_INCREASE_COST
                    | O_SET_HEART_COST
                    | O_INCREASE_HEART_COST
                    | O_REDUCE_HEART_REQ
            )
        }) {
            action_routes.push(
                "engine_rust_src/src/core/logic/interpreter/handlers/state_score_bonus.rs"
                    .to_string(),
            );
        }
        if frames.iter().any(|frame| {
            matches!(
                frame.opcode(),
                O_JUMP | O_JUMP_IF_FALSE | O_RETURN | O_TRIGGER_REMOTE | O_META_RULE
            )
        }) {
            action_routes.push("engine_rust_src/src/core/logic/interpreter/mod.rs".to_string());
        }

        action_routes.sort();
        action_routes.dedup();

        AbilityTraceView {
            trigger: self.trigger,
            frame_source: self.resolved_frame_source().to_string(),
            raw_text: self.raw_text.clone(),
            choice_count: self.choice_count,
            steps,
            diagnostics: AbilityDiagnosticsView {
                source_paths: trace_source_paths(),
                action_routes,
                serialization_paths: vec![
                    "engine_rust_src/src/core/logic/models.rs".to_string(),
                    "engine_rust_src/src/core/logic/card_db.rs".to_string(),
                    "engine_rust_src/src/export_hydrated_abilities.rs".to_string(),
                ],
                serialization_fields: trace_serialization_fields(),
                warnings: trace_warnings_for_ability(self, &frames),
            },
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::core::logic::AbilityContext;
    use crate::core::logic::CardDatabase;
    use crate::core::logic::constants::FILTER_REVEALED_CONTEXT;
    use crate::core::logic::interpreter::handlers::choice_prompt::suspend_choice;
    use crate::core::enums::Phase;
    use crate::test_helpers::{create_test_state, load_real_db, TestActionReceiver};
    use serde_json::json;
    #[test]
    fn ability_has_effects_works() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            effects: vec![Effect::default()],
            ..Default::default()
        };
        assert!(ability.has_effects());
    }

    #[test]
    fn ability_modal_count_from_effects() {
        let ability = Ability::default();
        assert_eq!(ability.modal_option_count(), 0);
    }

    #[test]
    fn get_modal_option_frames_extracts_authored_select_mode_frames() {
        let ability = Ability {
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_SELECT_MODE, 2, 0, 0, false),
                    AbilityFrame::new(O_JUMP, 0, 0, 0, false),
                    AbilityFrame::new(O_JUMP, 2, 0, 0, false),
                    AbilityFrame::new(O_DRAW, 1, 0, 0, false),
                    AbilityFrame::new(O_TAP_MEMBER, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                    AbilityFrame::new(O_ADD_BLADES, 2, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let option0 = ability.get_modal_option_frames(0).expect("option 0 frames");
        let option1 = ability.get_modal_option_frames(1).expect("option 1 frames");

        assert_eq!(option0.len(), 2);
        assert_eq!(option0[0].opcode(), O_DRAW);
        assert_eq!(option0[1].opcode(), O_TAP_MEMBER);
        assert_eq!(option1.len(), 1);
        assert_eq!(option1[0].opcode(), O_ADD_BLADES);
    }

    #[test]
    fn get_modal_option_frames_prefers_authored_frame_program_over_effect_modal_options() {
        let ability = Ability {
            effects: vec![Effect {
                modal_options: json!([
                    [{ "effect_type": EffectType::Draw, "value": 9 }],
                    [{ "effect_type": EffectType::AddBlades, "value": 9 }]
                ]),
                ..Default::default()
            }],
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_SELECT_MODE, 2, 0, 0, false),
                    AbilityFrame::new(O_JUMP, 0, 0, 0, false),
                    AbilityFrame::new(O_JUMP, 2, 0, 0, false),
                    AbilityFrame::new(O_DRAW, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                    AbilityFrame::new(O_ADD_BLADES, 2, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let option0 = ability.get_modal_option_frames(0).expect("option 0 frames");
        let option1 = ability.get_modal_option_frames(1).expect("option 1 frames");

        assert_eq!(option0[0].opcode(), O_DRAW);
        assert_eq!(option0[0].value(), 1);
        assert_eq!(option1[0].opcode(), O_ADD_BLADES);
        assert_eq!(option1[0].value(), 2);
    }

    #[test]
    fn ability_resolved_frames_fall_back_to_effects() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            effects: vec![Effect {
                effect_type: EffectType::Draw,
                value: Value::from(1),
                ..Default::default()
            }],
            ..Default::default()
        };

        let frames = ability.resolved_frames();
        assert_eq!(frames.len(), 1);
        assert_eq!(frames[0].opcode(), O_DRAW);
        assert!(ability.has_resolved_frames());
    }

    #[test]
    fn resolved_frames_prefer_frame_program_when_present() {
        let ability = Ability {
            trigger: TriggerType::Constant,
            effects: vec![Effect {
                effect_type: EffectType::AddBlades,
                value: Value::from(1),
                ..Default::default()
            }],
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_RECOVER_LIVE, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let frames = ability.resolved_frames();
        assert_eq!(ability.resolved_frame_source(), "frame_program");
        assert_eq!(frames.len(), 2);
        assert_eq!(frames[0].opcode(), O_RECOVER_LIVE);
    }

    #[test]
    fn count_group_frames_can_mark_unique_groups() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "COUNT_GROUP",
            "value": 3,
            "params": {
                "raw_cond": "UNIQUE_GROUPS_COUNT",
                "MIN": 3
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        }));

        let components = frame.components();
        assert!(components.counts_unique_groups());
        assert!(!components.counts_unique_names());
    }

    #[test]
    fn return_frames_preserve_authored_params() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "RETURN",
            "value": 0,
            "params": {
                "raw_cond": "SUCCESS_LIVE_COUNT_EQUAL_OPPONENT"
            }
        }));

        let components = frame.components();
        assert_eq!(components.opcode, O_RETURN);
        assert_eq!(
            components
                .params
                .and_then(|params| params.get("raw_cond"))
                .and_then(|value| value.as_str()),
            Some("SUCCESS_LIVE_COUNT_EQUAL_OPPONENT")
        );
    }

    #[test]
    fn empty_frame_program_still_reports_effects_source() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            effects: vec![Effect {
                effect_type: EffectType::Draw,
                value: Value::from(1),
                ..Default::default()
            }],
            frame_program: Some(FrameProgram {
                frames: vec![],
                raw_program: None,
            }),
            ..Default::default()
        };

        let frames = ability.resolved_frames();
        assert_eq!(ability.resolved_frame_source(), "effects");
        assert!(frames.is_empty());
    }

    #[test]
    fn structured_draw_frame_preserves_minimal_hand_semantics() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "DRAW",
            "value": 1,
            "slot": {
                "is_opponent": 1,
                "dest_zone": "DISCARD"
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame_data.opcode, O_DRAW);
        assert_eq!(frame_data.value, 1);
        assert_eq!(frame_data.target_player_index(0), 1);
        assert_eq!(frame_data.slot.dest_zone, Zone::Discard);
    }

    #[test]
    fn trace_view_uses_human_readable_steps() {
        let ability = Ability {
            trigger: TriggerType::OnPlay,
            raw_text: "draw 1".to_string(),
            frame_program: Some(FrameProgram {
                frames: vec![
                    AbilityFrame::new(O_DRAW, 1, 0, 0, false),
                    AbilityFrame::new_return(),
                ],
                raw_program: None,
            }),
            ..Default::default()
        };

        let trace = ability.trace_view();
        assert_eq!(trace.frame_source, "frame_program");
        assert_eq!(trace.steps[0].summary, "draw 1 card(s)");
        assert_eq!(trace.steps[1].summary, "return");
        assert!(!trace.diagnostics.source_paths.is_empty());
        assert!(!trace.diagnostics.serialization_fields.is_empty());
        assert!(trace
            .diagnostics
            .serialization_fields
            .iter()
            .any(|field| field == "Ability.frame_program"));
    }

    #[test]
    fn look_and_choose_trace_step_preserves_choose_count_from_params() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "LOOK_AND_CHOOSE",
            "value": 7,
            "slot": {
                "source_zone": "DECK",
                "dest_zone": "DISCARD",
                "target_slot": 6
            },
            "params": {
                "count": 7,
                "choose_count": 3,
                "reveal": true,
                "dest_discard": true
            }
        }));

        let trace = frame.components().to_trace_step();
        assert_eq!(trace.opcode, "LOOK_AND_CHOOSE");
        assert_eq!(trace.choose_count, Some(3));
        assert_eq!(trace.reveal, Some(true));
        assert_eq!(trace.remainder_to_discard, Some(true));
        assert!(trace.summary.contains("look 7 choose 3"));
    }

    #[test]
    fn add_to_hand_helper_accepts_legacy_looked_cards_encodings() {
        let zone_encoded = AbilityFrame::new(
            O_ADD_TO_HAND,
            1,
            0,
            crate::core::generated_constants::ZONE_LOOKED_CARDS,
            false,
        );
        let slot_encoded = AbilityFrame::new(
            O_ADD_TO_HAND,
            1,
            0,
            crate::core::generated_constants::SLOT_HAND,
            false,
        );

        assert!(zone_encoded.components().add_to_hand_uses_looked_cards());
        assert!(slot_encoded.components().add_to_hand_uses_looked_cards());
    }

    #[test]
    fn structured_reduce_cost_frame_preserves_card10_style_filter_bits() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "REDUCE_COST",
            "value": 1,
            "attr": {
                "target_player": 1,
                "special_id": "Not Self",
                "compare_accumulated": 1
            },
            "slot": {
                "is_dynamic": 1,
                "remainder_zone": 204
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame_data.filter.target_player, 1);
        assert_eq!(frame_data.filter.special_id, 3);
        assert!(frame_data.filter.compare_accumulated);
        assert!(frame_data.slot.is_dynamic);
        assert_eq!(frame_data.slot.remainder_zone, 204);
    }

    #[test]
    fn structured_count_stage_frame_preserves_not_self_filter_bits() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "COUNT_STAGE",
            "value": 1,
            "attr": {
                "group_enabled": 1,
                "group_id": 12,
                "special_id": "Not Self"
            },
            "slot": {
                "target_slot": "STAGE_0",
                "comparison": "GE"
            }
        }));

        let program = FrameProgram {
            frames: vec![frame],
            raw_program: None,
        };
        let conditions = derive_conditions_from_frame_program(&program);

        assert_eq!(conditions.len(), 1);
        assert_eq!(conditions[0].condition_type, ConditionType::CountStage);
        assert_eq!(CardFilter::from_attr(conditions[0].attr).special_id, 3);
    }

    #[test]
    fn structured_frame_parses_named_slot_identifiers() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_MEMBER",
            "value": 1,
            "slot": {
                "target_slot": "HAND",
                "comparison": "GE",
                "source_zone": "DECK_TOP",
                "remainder_zone": "DISCARD"
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame_data.slot.target_slot, 54);
        assert_eq!(frame_data.slot.comparison, 3);
        assert_eq!(frame_data.slot.source_zone, Zone::DeckTop);
        assert_eq!(frame_data.slot.remainder_zone, crate::core::generated_constants::ZONE_DISCARD as u8);
    }

    #[test]
    fn scalar_dynamic_helpers_prefer_explicit_params_over_packed_value() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "ADD_HEARTS",
            "value": 1,
            "attr": {
                "target_player": 1,
                "compare_accumulated": 1
            },
            "slot": {
                "remainder_zone": 203,
                "is_dynamic": 1
            },
            "params": {
                "scalar_dynamic": {
                    "base_value": 1,
                    "divisor": 4
                }
            }
        }));

        let frame_data = frame.components();
        assert_eq!(frame.scalar_dynamic_base(), 1);
        assert_eq!(frame.scalar_dynamic_divisor(), 4);
        assert_eq!(frame_data.scalar_dynamic_base(), 1);
        assert_eq!(frame_data.scalar_dynamic_divisor(), 4);
    }

    #[test]
    fn card_617_draws_once_per_six_energy_from_text() {
        let db = load_real_db();
        let card_id = *db.card_no_to_id.get("PL!SP-sd1-001-SD").unwrap();
        let member = db.get_member(card_id).unwrap();
        let ability = member.abilities.get(0).unwrap();

        let draw_count = |energy_count: usize| {
            let mut state = create_test_state();
            state.phase = Phase::Main;
            state.current_player = 0;
            state.ui.silent = true;
            state.players[0].stage = [card_id, -1, -1];
            state.players[0].hand.clear();
            state.players[0].discard.clear();
            state.players[0].deck.clear();
            for card in 9000..9004 {
                state.players[0].deck.push(card);
            }
            state.players[0].energy_zone.clear();
            for card in 1000..(1000 + energy_count as i32) {
                state.players[0].energy_zone.push(card);
            }

            let before = state.players[0].hand.len();
            let ctx = AbilityContext {
                player_id: 0,
                source_card_id: card_id,
                ability_index: 0,
                area_idx: 0,
                ..Default::default()
            };
            state.resolve_ability(&db, ability, &ctx);
            state.players[0].hand.len() - before
        };

            assert_eq!(draw_count(5), 0);
            assert_eq!(draw_count(6), 1);
            assert_eq!(draw_count(11), 1);
            assert_eq!(draw_count(12), 2);
    }

    #[test]
    fn energy_threshold_draw_cards_follow_their_text() {
        let db = load_real_db();
        let cards = ["PL!SP-PR-003-PR", "PL!SP-PR-007-PR", "PL!SP-PR-010-PR"];

        for card_no in cards {
            let card_id = *db.card_no_to_id.get(card_no).unwrap();
            let ability = db.get_member(card_id).unwrap().abilities.get(0).unwrap();

            let draw_count = |energy_count: usize| {
                let mut state = create_test_state();
                state.phase = Phase::Main;
                state.current_player = 0;
                state.ui.silent = true;
                state.players[0].stage = [card_id, -1, -1];
                state.players[0].hand.clear();
                state.players[0].discard.clear();
                state.players[0].deck.clear();
                for card in 9000..9004 {
                    state.players[0].deck.push(card);
                }
                state.players[0].energy_zone.clear();
                for card in 1000..(1000 + energy_count as i32) {
                    state.players[0].energy_zone.push(card);
                }

                let before = state.players[0].hand.len();
                let ctx = AbilityContext {
                    player_id: 0,
                    source_card_id: card_id,
                    ability_index: 0,
                    area_idx: 0,
                    ..Default::default()
                };
                state.resolve_ability(&db, ability, &ctx);
                state.players[0].hand.len() - before
            };

            assert_eq!(draw_count(6), 0, "{card_no} should not draw below 7 energy");
            assert_eq!(draw_count(7), 1, "{card_no} should draw at 7 energy");
        }
    }

    fn resolve_pending_prompt(state: &mut crate::core::logic::GameState, db: &CardDatabase) {
        let trace_prompts = std::env::var("TRACE_PROMPTS").is_ok();
        while !state.interaction_stack.is_empty() {
            let mut actions = TestActionReceiver::default();
            state.generate_legal_actions(db, 0, &mut actions);
            if trace_prompts {
                eprintln!("prompt={:?}", state.interaction_stack.last());
                eprintln!("actions={:?}", actions.actions);
            }
            let action_ids = actions.actions;
            let action = action_ids
                .iter()
                .copied()
                .find(|action| *action > 0)
                .or_else(|| action_ids.iter().copied().find(|action| *action == 0))
                .expect("expected a legal selection action");
            state.step(db, action).expect("selection should resolve");
            state.process_trigger_queue(db);
        }
    }

    fn ability_for_card_no<'a>(db: &'a CardDatabase, card_no: &str) -> &'a Ability {
        let card_id = *db.card_no_to_id.get(card_no).unwrap();
        db.get_member(card_id)
            .map(|card| card.abilities.get(0).unwrap())
            .or_else(|| db.get_live(card_id).map(|card| card.abilities.get(0).unwrap()))
            .expect("card should have a first ability")
    }

    #[test]
    fn muse_live_recovery_puts_the_discard_live_card_on_top_of_deck_before_draw() {
        let db = load_real_db();
        let card_id = *db.card_no_to_id.get("PL!-pb1-006-P+").unwrap();
        let live_card = db
            .lives
            .values()
            .find(|card| card.groups.contains(&(crate::core::generated_constants::GROUP_MUSE as u8)))
            .map(|card| card.card_id)
            .expect("expected at least one MUSE live card");

        let run_case = |opponent_tapped: bool| {
            let mut state = create_test_state();
            state.ui.silent = true;
            state.phase = Phase::Main;
            state.current_player = 0;
            state.players[0].hand = vec![card_id].into();
            state.players[0].discard = vec![live_card].into();
            state.players[0].deck = vec![9001, 9002].into();
            state.players[0].energy_zone = (0..20).map(|idx| 5000 + idx).collect();
            state.players[1].stage[0] = 9003;
            state.players[1].set_tapped(0, opponent_tapped);

            state
                .step(
                    &db,
                    crate::test_helpers::Action::PlayMember {
                        hand_idx: 0,
                        slot_idx: 0,
                    }
                    .id(),
                )
                .expect("play should succeed");
            state.process_trigger_queue(&db);
            resolve_pending_prompt(&mut state, &db);

            state
        };

        let calm_state = run_case(false);
        assert_eq!(calm_state.players[0].hand.len(), 0);
        assert_eq!(calm_state.players[0].discard.len(), 0);
        assert_eq!(calm_state.players[0].deck.last(), Some(&live_card));

        let tapped_state = run_case(true);
        assert_eq!(tapped_state.players[0].hand.as_slice(), &[live_card]);
        assert_eq!(tapped_state.players[0].discard.len(), 0);
        assert_eq!(tapped_state.players[0].deck.as_slice(), &[9001, 9002]);
    }

    #[test]
    fn discard_cards_can_return_to_the_top_of_the_deck() {
        let db = load_real_db();
        let card_id = *db.card_no_to_id.get("PL!N-bp4-021-N").unwrap();
        let discard_card = db
            .members
            .values()
            .find(|card| card.card_id != card_id)
            .map(|card| card.card_id)
            .expect("expected a discard card for the test");
        let mut state = create_test_state();
        state.ui.silent = true;
        state.phase = Phase::Main;
        state.current_player = 0;
        state.players[0].stage[0] = card_id;
        state.players[0].hand.clear();
        state.players[0].discard = vec![discard_card].into();
        state.players[0].deck = vec![8001, 8002].into();
        state.players[0].energy_zone = (0..20).map(|idx| 6000 + idx).collect();

        let ctx = AbilityContext {
            player_id: 0,
            source_card_id: card_id,
            ability_index: 0,
            area_idx: 0,
            trigger_type: TriggerType::OnPlay,
            ..Default::default()
        };
        state.resolve_ability(&db, ability_for_card_no(&db, "PL!N-bp4-021-N"), &ctx);
        state.process_trigger_queue(&db);
        resolve_pending_prompt(&mut state, &db);

        assert_eq!(state.players[0].discard.len(), 0);
        assert_eq!(state.players[0].deck.last(), Some(&discard_card));
        assert!(state.players[0].hand.is_empty());
    }

    #[test]
    fn neo_sky_neo_map_draws_before_putting_three_hand_cards_back_on_top() {
        let db = load_real_db();
        let card_id = *db.card_no_to_id.get("PL!N-bp4-031-L").unwrap();
        let stage_members = [4350, 285, 4381];
        let stage_cost_total: u32 = stage_members
            .iter()
            .map(|card_id| db.get_member(*card_id).expect("stage member should exist").cost)
            .sum();
        assert!(
            stage_cost_total >= 20,
            "need a stage total cost of at least 20 for the live-start ability"
        );

        let mut state = create_test_state();
        state.ui.silent = true;
        state.phase = Phase::PerformanceP1;
        state.current_player = 0;
        state.players[0].hand.clear();
        state.players[0].live_zone = [-1; 3];
        state.players[0].live_zone[0] = card_id;
        state.players[0].deck = vec![7001, 7002, 7003].into();
        state.players[0].stage = stage_members;
        state.interaction_stack.clear();

        state.trigger_event(&db, TriggerType::OnLiveStart, 0, -1, -1, 0, -1);
        state.process_trigger_queue(&db);
        resolve_pending_prompt(&mut state, &db);
        assert!(state.interaction_stack.is_empty());
        assert!(state.players[0].discard.len() <= 3);
        let mut deck = state.players[0].deck.to_vec();
        deck.sort_unstable();
        assert_eq!(deck, vec![7001, 7002, 7003]);
    }

    #[test]
    fn move_member_frame_preserves_structured_params() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "MOVE_MEMBER",
            "attr": {
                "is_optional": 1
            },
            "slot": {
                "target_slot": 4
            },
            "params": {
                "source": "STAGE",
                "destination": "STAGE"
            }
        }));

        assert_eq!(frame.opcode(), O_MOVE_MEMBER);
        assert_eq!(frame.params.get("source").and_then(|value| value.as_str()), Some("STAGE"));
        assert_eq!(
            frame.params.get("destination").and_then(|value| value.as_str()),
            Some("STAGE")
        );
        assert!(frame.components().filter.is_optional);
    }

    #[test]
    fn semantic_filter_params_preserve_passthrough_bits_in_raw_attr() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "LOOK_AND_CHOOSE",
            "value": 1,
            "params": {
                "filter": "COST_LE_REVEALED"
            }
        }));

        assert_ne!(
            frame.attr() & crate::core::logic::constants::FILTER_REVEALED_CONTEXT,
            0
        );
        assert!(frame.components().filter.is_cost_type);
        assert!(frame.components().filter.is_le);

        let mut state = create_test_state();
        let db = CardDatabase::default();
        let ctx = AbilityContext {
            player_id: 0,
            ..Default::default()
        };

        let result = suspend_choice(
            &mut state,
            &db,
            &ctx,
            &ctx,
            0,
            O_LOOK_AND_CHOOSE,
            0,
            ChoiceType::LookAndChoose,
            frame.attr(),
            1,
        );

        assert!(matches!(result, crate::core::logic::interpreter::handlers::HandlerResult::Suspend));
        assert_ne!(
            state
                .interaction_stack
                .last()
                .map(|pending| pending.filter_attr & FILTER_REVEALED_CONTEXT)
                .unwrap_or(0),
            0
        );
    }

    #[test]
    fn total_cost_budget_helper_accepts_modern_compare_accumulated() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "PLAY_MEMBER_FROM_DISCARD",
            "attr": {
                "compare_accumulated": 1,
                "value_enabled": 1,
                "value_threshold": 4
            }
        }));

        assert!(frame.components().uses_total_cost_budget());
    }

    #[test]
    fn total_cost_budget_helper_accepts_legacy_total_cost_flag() {
        let pending = PendingInteraction {
            filter_attr: crate::core::generated_constants::FILTER_TOTAL_COST,
            ..Default::default()
        };

        assert!(pending.uses_total_cost_budget());
    }

    #[test]
    fn targeted_select_member_filter_attr_preserves_passthrough_flags() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_MEMBER",
            "value": 1,
            "attr": {
                "card_type": "MEMBER",
                "target_player": "OPPONENT"
            },
            "slot": {
                "target_slot": 4
            },
            "params": {
                "area": "ANY_STAGE"
            }
        }));

        let target_attr = frame.components().targeted_select_member_filter_attr();
        let target_filter = CardFilter::from_attr(target_attr);

        assert_eq!(target_filter.target_player, TARGET_PLAYER_SELF as u8);
        assert_ne!(target_attr & FILTER_ANY_STAGE, 0);
    }

    #[test]
    fn pending_interaction_selection_target_zone_prefers_semantic_zone_mask() {
        let pending = PendingInteraction {
            filter_attr: CardFilter {
                is_enabled: true,
                zone_mask: ZONE_MASK_DISCARD as u8,
                ..Default::default()
            }
            .to_attr(),
            ..Default::default()
        };

        assert_eq!(pending.selection_target_zone(), Some(Zone::Discard as usize));
    }

    #[test]
    fn select_cards_spec_uses_source_zone_to_pick_prompt_type() {
        let hand_frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_CARDS",
            "value": 1,
            "slot": { "source_zone": "HAND" },
        }));
        let discard_frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_CARDS",
            "value": 1,
            "slot": { "source_zone": "DISCARD" },
        }));
        let deck_frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_CARDS",
            "value": 1,
            "slot": { "source_zone": "DECK" },
        }));

        assert_eq!(
            hand_frame.components().semantic_select_cards_spec().choice_type(),
            ChoiceType::SelectHandDiscard
        );
        assert_eq!(
            discard_frame.components().semantic_select_cards_spec().choice_type(),
            ChoiceType::SelectDiscardPlay
        );
        assert_eq!(
            deck_frame.components().semantic_select_cards_spec().choice_type(),
            ChoiceType::LookAndChoose
        );
    }

    #[test]
    fn select_cards_spec_falls_back_to_target_slot_zone_when_source_missing() {
        let frame = AbilityFrame::from_json_value(&json!({
            "opcode": "SELECT_CARDS",
            "value": 1,
            "slot": { "target_slot": "HAND" },
        }));

        let spec = frame.components().semantic_select_cards_spec();

        assert_eq!(spec.source_zone, Zone::Hand);
        assert_eq!(spec.choice_type(), ChoiceType::SelectHandDiscard);
    }
}
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EnergyCard {
    pub card_id: i32,
    #[serde(default)]
    pub card_no: String,
    #[serde(default)]
    pub name: String,
    #[serde(default)]
    pub img_path: String,
    #[serde(default)]
    pub ability_text: String,
    #[serde(default)]
    pub original_text: String,
    #[serde(default)]
    pub original_text_en: String,
    #[serde(default)]
    pub rare: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct TurnEvent {
    pub turn: u32,
    pub phase: Phase,
    pub player_id: u8,
    pub event_type: String, // e.g. "PLAY", "ACTIVATE", "TRIGGER", "RULE", "PERFORMANCE"
    pub source_cid: i32,
    pub ability_idx: i16,
    pub description: String,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, Default)]
pub struct DeckStats {
    pub avg_hearts: [f32; 7],
    pub avg_notes: f32,
    pub avg_draw: f32,
    pub count: f32,
}

impl PartialEq for DeckStats {
    fn eq(&self, other: &Self) -> bool {
        self.avg_hearts
            .iter()
            .zip(other.avg_hearts.iter())
            .all(|(a, b)| a.to_bits() == b.to_bits())
            && self.avg_notes.to_bits() == other.avg_notes.to_bits()
            && self.avg_draw.to_bits() == other.avg_draw.to_bits()
            && self.count.to_bits() == other.count.to_bits()
    }
}

impl Eq for DeckStats {}

impl std::hash::Hash for DeckStats {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        for &h in &self.avg_hearts {
            h.to_bits().hash(state);
        }
        self.avg_notes.to_bits().hash(state);
        self.avg_draw.to_bits().hash(state);
        self.count.to_bits().hash(state);
    }
}
