use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use serde::{Deserialize, Serialize};

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
    pub opcodes_mask: u128,
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
