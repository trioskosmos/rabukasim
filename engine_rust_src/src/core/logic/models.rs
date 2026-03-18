use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use serde::{Deserialize, Serialize};
use crate::core::logic::interpreter::instruction::BytecodeProgram;
use std::collections::BTreeMap;

// Re-export constants so they're available to all modules using `use super::models::*;`
pub use crate::core::logic::constants::*;

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Condition {
    #[serde(rename = "type")]
    // Rule 3.5.1: Condition Type
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
    // Rule 3.5.3: Effect Type
    pub effect_type: EffectType,
    #[serde(default)]
    pub value: i32,
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

impl std::hash::Hash for Effect {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.effect_type.hash(state);
        self.value.hash(state);
        self.value_cond.hash(state);
        self.target.hash(state);
        self.is_optional.hash(state);
        self.runtime_opcode.hash(state);
        self.runtime_value.hash(state);
        self.runtime_attr.hash(state);
        self.runtime_slot.hash(state);
        self.modal_options.to_string().hash(state);
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Cost {
    #[serde(rename = "type")]
    // Rule 3.5.2: Cost Type
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
    // Rule 3.1.2: [能力のマスター (Master of Ability)]
    // Rule 3.1.2.1: [常時能力のマスターは、そのカードのマスターです (Master of Always Ability)]
    // Rule 3.1.2.2: [起動能力のマスターは、その能力をプレイしたプレイヤーです (Master of Activated Ability)]
    // Rule 3.1.2.3: [自動能力のマスターは、そのカードのマスターです (Master of Auto Ability)]
    pub player_id: u8,
    pub activator_id: u8, // The player who originally triggered/activated the ability
    pub area_idx: i16,
    pub source_card_id: i32,
    pub target_card_id: i32,
    pub target_slot: i16,
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
    // Rule 1.3.4: [蜷梧凾縺ｮ驕ｸ謚・ (Simultaneous choice)]
    pub selected_cards: Vec<i32>, // IDs of cards picked in the current/last selection action
    #[serde(default)]
    pub auto_pick: bool, // If true, mandatory single-choice steps (like O_SELECT_MODE) will resolve automatically
}

impl Default for AbilityContext {
    fn default() -> Self {
        Self {
            player_id: 0,
            activator_id: 0,
            area_idx: -1,
            source_card_id: -1,
            target_card_id: -1,
            target_slot: -1,
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
            selected_cards: Vec::new(),
            auto_pick: false,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq, Default)]
pub struct PendingInteraction {
    pub ctx: AbilityContext,
    pub card_id: i32,
    pub ability_index: i16,
    pub effect_opcode: i32,
    pub target_slot: i32,
    #[serde(default)]
    pub choice_type: ChoiceType,
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
    pub execution_id: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default, Hash)]
pub struct PreparsedModifier {
    pub op: i32,
    pub val: i32,
    pub attr: u64,
    pub slot: i32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct CanonicalStep {
    #[serde(default)]
    pub kind: String,
    #[serde(default)]
    pub op: String,
    #[serde(default)]
    pub target: Option<String>,
    #[serde(default)]
    pub count: Option<i32>,
    #[serde(default)]
    pub value: Option<i32>,
    #[serde(default)]
    pub is_optional: bool,
    #[serde(default)]
    pub params: serde_json::Value,
    #[serde(default, flatten)]
    pub extra: BTreeMap<String, serde_json::Value>,
}

impl std::hash::Hash for CanonicalStep {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.kind.hash(state);
        self.op.hash(state);
        self.target.hash(state);
        self.count.hash(state);
        self.value.hash(state);
        self.is_optional.hash(state);
        self.params.to_string().hash(state);
        self.extra.len().hash(state);
        for (key, value) in &self.extra {
            key.hash(state);
            value.to_string().hash(state);
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct CanonicalAbilityProgram {
    #[serde(default)]
    pub trigger: String,
    #[serde(default)]
    pub conditions: Vec<CanonicalStep>,
    #[serde(default)]
    pub effects: Vec<CanonicalStep>,
    #[serde(default)]
    pub costs: Vec<CanonicalStep>,
}

impl std::hash::Hash for CanonicalAbilityProgram {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.trigger.hash(state);
        self.conditions.hash(state);
        self.effects.hash(state);
        self.costs.hash(state);
    }
}

/// Rule 2.12: Card Text (Ability Definition)
/// Rule 3.4: [繧｢繝薙fa繧｣繝・ぅ (Ability)]
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct Ability {
    #[serde(default)]
    pub raw_text: String,
    // Rule 3.4.1: [繝医Μ繧ｬ繝ｼ (Trigger Definition)]
    pub trigger: TriggerType,
    #[serde(default)]
    pub effects: Vec<Effect>,
    #[serde(default)]
    pub conditions: Vec<Condition>,
    #[serde(default)]
    pub costs: Vec<Cost>,
    #[serde(default)]
    // Rule 11.2: [繧ｿ繝ｼ繝・1 蝗・ (Once per Turn)]
    // Rule 3.4.3: [繧｢繝薙fa繧｣繝・ぅ縺ｮ菴ｿ逕ｨ蜃 Mario (Ability usage status)]
    pub is_once_per_turn: bool,
    #[serde(default)]
    // Rule 11.4: [繧ｪ繝ｼ繝・] (Auto ability)
    pub bytecode: Vec<i32>,
    #[serde(default)]
    pub modal_options: serde_json::Value,
    #[serde(default)]
    pub option_names: Vec<String>,
    #[serde(default)]
    pub pseudocode: String,
    #[serde(default)]
    pub requires_selection: bool,
    #[serde(default)]
    pub choice_flags: u8,
    #[serde(default)]
    pub choice_count: u8,
    #[serde(default)]
    pub filters: Vec<crate::core::logic::filter::CardFilter>,
    #[serde(default)]
    pub preparsed_modifiers: Vec<PreparsedModifier>,
    #[serde(default)]
    #[serde(skip_serializing)]
    pub opcodes_mask: u128,
    /// Source: "canonical" if from hybrid preview with no bytecode, "legacy" if fallback, null for compiled
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    pub source: Option<String>,
    /// Track if this ability needs fallback (canonical with no bytecode)
    #[serde(default)]
    #[serde(skip_serializing)]
    pub needs_fallback: bool,
    /// Fallback bytecode for canonical entries (stored if available)
    #[serde(default)]
    #[serde(skip_serializing_if = "Vec::is_empty")]
    pub fallback_bytecode: Vec<i32>,
    /// Structured canonical plan carried through the bridge so runtime metadata can
    /// be derived without depending on bytecode scans.
    #[serde(default)]
    #[serde(skip_serializing_if = "Option::is_none")]
    pub canonical_program: Option<CanonicalAbilityProgram>,
}

impl std::hash::Hash for Ability {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.raw_text.hash(state);
        self.trigger.hash(state);
        self.effects.hash(state);
        self.conditions.hash(state);
        self.costs.hash(state);
        self.is_once_per_turn.hash(state);
        self.bytecode.hash(state);
        // modal_options is skipped
        self.option_names.hash(state);
        self.pseudocode.hash(state);
        self.requires_selection.hash(state);
        self.choice_flags.hash(state);
        self.choice_count.hash(state);
        self.preparsed_modifiers.hash(state);
        self.opcodes_mask.hash(state);
        self.source.hash(state);
        self.needs_fallback.hash(state);
        self.fallback_bytecode.hash(state);
        self.canonical_program.hash(state);
    }
}

impl Ability {
    pub fn bytecode_program(&self) -> BytecodeProgram {
        BytecodeProgram::from_slice(&self.bytecode)
    }
}
// Rule 2.2.2.3: Energy Card
// Rule 2.2.2.3.1: [カードの種類を示す箇所に‘エネルギーカード’と表記されているカードは、カードタイプがエネルギーです (Energy label)]
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EnergyCard {
    pub card_id: i32,
    // Rule 2.14: Marginalia
    pub card_no: String,
    // Rule 2.3: Card Name
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
    // Rule 2.14: Rarity
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
