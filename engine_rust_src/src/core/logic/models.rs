use crate::core::enums::ChoiceType;
use crate::core::enums::*;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use crate::core::logic::interpreter::instruction::BytecodeProgram;
use crate::core::logic::interpreter::instruction::{DecodedSlot, DecodedFilterAttr, DecodedLookAndChoose};

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Hash)]
pub enum AbilityFrame {
    Return,
    Draw {
        count: i32,
    },
    Semantic {
        opcode: i32,
        value: i32,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
        #[serde(default)]
        params: Value,
    },
    RecoverLive {
        count: i32,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    RecoverMember {
        count: i32,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    LookAndChoose {
        params: DecodedLookAndChoose,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    SelectMember {
        count: i32,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    MoveMember {
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    MetaRule {
        rule_type: i32,
        filter: DecodedFilterAttr,
        slot: DecodedSlot,
    },
    Raw {
        opcode: i32,
        value: i32,
        attr: u64,
        slot: i32,
    },
}

impl Default for AbilityFrame {
    fn default() -> Self {
        AbilityFrame::Raw { opcode: 0, value: 0, attr: 0, slot: 0 }
    }
}

impl AbilityFrame {
    pub fn new(opcode: i32, value: i32, attr: i64, raw_s: i32) -> Self {
        AbilityFrame::Raw {
            opcode,
            value,
            attr: attr as u64,
            slot: raw_s,
        }
    }

    pub fn opcode(&self) -> i32 {
        match self {
            AbilityFrame::Return => O_RETURN,
            AbilityFrame::Draw { .. } => O_DRAW,
            AbilityFrame::Semantic { opcode, .. } => *opcode,
            AbilityFrame::RecoverLive { .. } => O_RECOVER_LIVE,
            AbilityFrame::RecoverMember { .. } => O_RECOVER_MEMBER,
            AbilityFrame::LookAndChoose { .. } => O_LOOK_AND_CHOOSE,
            AbilityFrame::SelectMember { .. } => O_SELECT_MEMBER,
            AbilityFrame::MoveMember { .. } => O_MOVE_MEMBER,
            AbilityFrame::MetaRule { .. } => O_META_RULE,
            AbilityFrame::Raw { opcode, .. } => *opcode,
        }
    }

    pub fn value(&self) -> i32 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { count } => *count,
            AbilityFrame::Semantic { value, .. } => *value,
            AbilityFrame::RecoverLive { count, .. } => *count,
            AbilityFrame::RecoverMember { count, .. } => *count,
            AbilityFrame::LookAndChoose { params, .. } => params.to_raw(),
            AbilityFrame::SelectMember { count, .. } => *count,
            AbilityFrame::MoveMember { .. } => 0,
            AbilityFrame::MetaRule { rule_type, .. } => *rule_type,
            AbilityFrame::Raw { value, .. } => *value,
        }
    }

    pub fn attr(&self) -> u64 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { .. } => 0,
            AbilityFrame::Semantic { filter, .. } => filter.to_attr(),
            AbilityFrame::RecoverLive { filter, .. } => filter.to_attr(),
            AbilityFrame::RecoverMember { filter, .. } => filter.to_attr(),
            AbilityFrame::LookAndChoose { filter, .. } => filter.to_attr(),
            AbilityFrame::SelectMember { filter, .. } => filter.to_attr(),
            AbilityFrame::MoveMember { filter, .. } => filter.to_attr(),
            AbilityFrame::MetaRule { filter, .. } => filter.to_attr(),
            AbilityFrame::Raw { attr, .. } => *attr,
        }
    }

    pub fn slot(&self) -> i32 {
        match self {
            AbilityFrame::Return => 0,
            AbilityFrame::Draw { .. } => 0,
            AbilityFrame::Semantic { slot, .. } => slot.to_raw(),
            AbilityFrame::RecoverLive { slot, .. } => slot.to_raw(),
            AbilityFrame::RecoverMember { slot, .. } => slot.to_raw(),
            AbilityFrame::LookAndChoose { slot, .. } => slot.to_raw(),
            AbilityFrame::SelectMember { slot, .. } => slot.to_raw(),
            AbilityFrame::MoveMember { slot, .. } => slot.to_raw(),
            AbilityFrame::MetaRule { slot, .. } => slot.to_raw(),
            AbilityFrame::Raw { slot, .. } => *slot,
        }
    }


    
    pub fn raw_opcode(&self) -> i32 {
        self.to_instruction().op
    }
    pub fn raw_value(&self) -> i32 {
        self.to_instruction().v
    }
    pub fn raw_attr(&self) -> u64 {
        self.to_instruction().a as u64
    }
    pub fn raw_slot(&self) -> i32 {
        self.to_instruction().raw_s
    }


    pub fn look_choose(&self) -> crate::core::logic::interpreter::instruction::DecodedLookAndChoose {
        self.to_instruction().look_choose()
    }
    pub fn is_dynamic(&self) -> bool {
        self.to_instruction().is_dynamic()
    }
    pub fn scalar_dynamic_base(&self) -> i32 {
        self.to_instruction().scalar_dynamic_base()
    }
    pub fn scalar_dynamic_divisor(&self) -> i32 {
        self.to_instruction().scalar_dynamic_divisor()
    }
    pub fn heart_requirements(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartRequirements {
        self.to_instruction().heart_requirements()
    }
    pub fn heart_counts(&self) -> crate::core::logic::interpreter::instruction::DecodedHeartCounts {
        self.to_instruction().heart_counts()
    }

    pub fn filter(&self) -> DecodedFilterAttr {
        match self {
            AbilityFrame::Semantic { filter, .. } => *filter,
            AbilityFrame::RecoverLive { filter, .. } => *filter,
            AbilityFrame::RecoverMember { filter, .. } => *filter,
            AbilityFrame::LookAndChoose { filter, .. } => *filter,
            AbilityFrame::SelectMember { filter, .. } => *filter,
            AbilityFrame::MoveMember { filter, .. } => *filter,
            AbilityFrame::MetaRule { filter, .. } => *filter,
            AbilityFrame::Raw { attr, .. } => DecodedFilterAttr::decode((*attr) as i64),
            _ => DecodedFilterAttr::default(),
        }
    }

    pub fn dslot(&self) -> DecodedSlot {
        match self {
            AbilityFrame::Semantic { slot, .. } => *slot,
            AbilityFrame::RecoverLive { slot, .. } => *slot,
            AbilityFrame::RecoverMember { slot, .. } => *slot,
            AbilityFrame::LookAndChoose { slot, .. } => *slot,
            AbilityFrame::SelectMember { slot, .. } => *slot,
            AbilityFrame::MoveMember { slot, .. } => *slot,
            AbilityFrame::MetaRule { slot, .. } => *slot,
            AbilityFrame::Raw { slot, .. } => DecodedSlot::decode(*slot),
            _ => DecodedSlot::default(),
        }
    }

    pub fn to_instruction(&self) -> crate::core::logic::interpreter::instruction::BytecodeInstruction {
        let op = self.opcode();
        let v = self.value();
        let a = self.attr();
        let s = self.slot();
        crate::core::logic::interpreter::instruction::BytecodeInstruction { op, v, a: a as i64, raw_s: s }
    }
}

impl From<&AbilityFrame> for AbilityFrame {
    fn from(frame: &AbilityFrame) -> Self {
        frame.clone()
    }
}

impl From<&crate::core::logic::interpreter::instruction::BytecodeInstruction> for AbilityFrame {
    fn from(instr: &crate::core::logic::interpreter::instruction::BytecodeInstruction) -> Self {
        AbilityFrame::new(instr.op, instr.v, instr.a, instr.raw_s)
    }
}
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default, Hash)]
pub struct FrameProgram {
    #[serde(default)]
    pub frames: Vec<AbilityFrame>,
}

impl FrameProgram {
    pub fn from_bytecode(bytecode: &[i32]) -> Self {
        let mut frames = Vec::new();
        let mut ip = 0;

        while ip + crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION <= bytecode.len() {
            let opcode = bytecode[ip];
            let value = bytecode[ip + 1];
            let attr = ((bytecode[ip + 3] as i64) << 32) | (bytecode[ip + 2] as u32 as i64);
            let raw_s = bytecode[ip + 4];
            frames.push(AbilityFrame::new(opcode, value, attr, raw_s));
            ip += crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION;
        }

        Self { frames }
    }

    pub fn to_bytecode(&self) -> Vec<i32> {
        let mut words = Vec::with_capacity(self.frames.len() * crate::core::logic::interpreter::instruction::WORDS_PER_INSTRUCTION);
        for frame in &self.frames {
            let instr = frame.to_instruction();
            words.push(instr.op);
            words.push(instr.v);
            words.push(instr.a as i32);
            words.push((instr.a >> 32) as i32);
            words.push(instr.raw_s);
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
    pub selected_cards: smallvec::SmallVec<[i32; 8]>, // IDs of cards picked in the current/last selection action
    #[serde(default)]
    pub auto_pick: bool, // If true, mandatory single-choice steps (like O_SELECT_MODE) will resolve automatically
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, Default)]
pub struct StaticAbilityContext {
    pub player_id: u8,
    pub activator_id: u8,
    pub area_idx: i16,
    pub source_card_id: i32,
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
            selected_cards: smallvec::SmallVec::new(),
            auto_pick: false,
        }
    }
}

impl AbilityContext {
    pub fn static_context(&self) -> StaticAbilityContext {
        StaticAbilityContext {
            player_id: self.player_id,
            activator_id: self.activator_id,
            area_idx: self.area_idx,
            source_card_id: self.source_card_id,
            target_card_id: self.target_card_id,
            target_slot: self.target_slot,
            ability_index: self.ability_index,
            trigger_type: self.trigger_type,
            original_phase: self.original_phase,
            original_current_player: self.original_current_player,
        }
    }

    pub fn execution_state(&self) -> AbilityExecutionState {
        AbilityExecutionState {
            choice_index: self.choice_index,
            v_accumulated: self.v_accumulated,
            program_counter: self.program_counter,
            v_remaining: self.v_remaining,
            repeat_count: self.repeat_count,
            selected_cards: self.selected_cards.clone(),
            selected_color: self.selected_color,
            auto_pick: self.auto_pick,
        }
    }

    pub fn apply_execution_state(&mut self, execution_state: &AbilityExecutionState) {
        self.choice_index = execution_state.choice_index;
        self.v_accumulated = execution_state.v_accumulated;
        self.program_counter = execution_state.program_counter;
        self.v_remaining = execution_state.v_remaining;
        self.repeat_count = execution_state.repeat_count;
        self.selected_cards = execution_state.selected_cards.clone();
        self.selected_color = execution_state.selected_color;
        self.auto_pick = execution_state.auto_pick;
    }

    pub fn clear_step_state(&mut self) {
        self.choice_index = -1;
        self.v_remaining = -1;
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
    pub options: Vec<Value>,
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
    pub bytecode: Vec<i32>,
    #[serde(default)]
    pub effects: Vec<Effect>,
    #[serde(default)]
    pub conditions: Vec<Condition>,
    #[serde(default)]
    pub costs: Vec<Cost>,
    #[serde(default)]
    pub is_once_per_turn: bool,
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
    #[serde(default, skip_serializing)]
    pub opcodes_mask: u128,
    #[serde(default, skip_serializing)]
    pub sparse_frame_index: Option<serde_json::Value>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub frame_program: Option<FrameProgram>,
}

impl std::hash::Hash for Ability {
    fn hash<H: std::hash::Hasher>(&self, state: &mut H) {
        self.raw_text.hash(state);
        self.trigger.hash(state);
        self.effects.hash(state);
        self.conditions.hash(state);
        self.costs.hash(state);
        self.is_once_per_turn.hash(state);
        // modal_options is skipped
        self.option_names.hash(state);
        self.pseudocode.hash(state);
        self.requires_selection.hash(state);
        self.choice_flags.hash(state);
        self.choice_count.hash(state);
        self.preparsed_modifiers.hash(state);
        self.opcodes_mask.hash(state);
        self.sparse_frame_index.hash(state);
        self.frame_program.hash(state);
    }
}

impl Ability {
    pub fn bytecode_program(&self) -> BytecodeProgram {
        if let Some(frame_program) = &self.frame_program {
            BytecodeProgram::from_slice(&frame_program.to_bytecode())
        } else if !self.bytecode.is_empty() {
            BytecodeProgram::from_slice(&self.bytecode)
        } else {
            BytecodeProgram::from_slice(&[])
        }
    }

    pub fn bytecode(&self) -> Vec<i32> {
        if let Some(frame_program) = &self.frame_program {
            frame_program.to_bytecode()
        } else if !self.bytecode.is_empty() {
            self.bytecode.clone()
        } else {
            self.bytecode_program().words().to_vec()
        }
    }

    pub fn get_frame(&self, frame_idx: usize) -> Option<AbilityFrame> {
        if let Some(frame_program) = &self.frame_program {
            return frame_program.frames.get(frame_idx).cloned();
        }
        if let Some(sparse) = &self.sparse_frame_index {
            let fp = crate::core::logic::CardDatabase::sparse_entry_to_frame_program(sparse);
            return fp.frames.get(frame_idx).cloned();
        }
        let fp = FrameProgram::from_bytecode(&self.bytecode());
        fp.frames.get(frame_idx).cloned()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn frame_program_to_bytecode_roundtrips_through_fixed_layout_decoder() {
        let program = FrameProgram {
            frames: vec![
                AbilityFrame::Return,
                AbilityFrame::Raw { opcode: 204, value: 3, attr: 0x1122_3344_5566_7788, slot: 9 },
            ],
        };

        let words = program.to_bytecode();
        assert_eq!(words.len(), 10);

        let decoded = BytecodeProgram::from_slice(&words).decode_all();
        assert_eq!(decoded.len(), 2);
        assert_eq!(decoded[0], AbilityFrame::Return.to_instruction());
        assert_eq!(decoded[1], AbilityFrame::Raw { opcode: 204, value: 3, attr: 0x1122_3344_5566_7788, slot: 9 }.to_instruction());
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
