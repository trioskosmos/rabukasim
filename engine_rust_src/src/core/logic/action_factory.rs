use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::models::AbilityContext;
use crate::core::generated_constants::*;

/// Structured representation of a decoded Action ID.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DecodedAction {
    Pass,
    MulliganSelect { card_idx: u16 },
    SetLive { hand_idx: usize },
    SelectMode { mode_idx: i32 },
    SelectColor { color_idx: i32 },
    SelectStageSlot { slot_idx: usize },
    PlayMember {
        hand_idx: usize,
        slot_idx: usize,
        other_slot: Option<usize>,
        choice_idx: Option<i32>,
    },
    ActivateMember {
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: Option<i32>,
    },
    ActivateFromDiscard {
        discard_idx: usize,
        ab_idx: usize,
    },
    SelectEnergy {
        energy_idx: usize,
    },
    SelectChoice {
        choice_idx: i32,
    },
    Unknown(i32),
}

/// Central factory for Action ID management and human-readable labeling.
pub struct ActionFactory;

impl ActionFactory {
    /// Parses a raw action ID into a structured DecodedAction.
    pub fn parse_action(action_id: i32) -> DecodedAction {
        if action_id == ACTION_BASE_PASS {
            return DecodedAction::Pass;
        }

        if action_id >= ACTION_BASE_MULLIGAN && action_id < ACTION_BASE_MULLIGAN + 60 {
            return DecodedAction::MulliganSelect {
                card_idx: (action_id - ACTION_BASE_MULLIGAN) as u16,
            };
        }

        if action_id >= ACTION_BASE_LIVESET && action_id < ACTION_BASE_LIVESET + 100 {
            return DecodedAction::SetLive {
                hand_idx: (action_id - ACTION_BASE_LIVESET) as usize,
            };
        }

        if action_id >= ACTION_BASE_MODE && action_id < ACTION_BASE_MODE + 100 {
            return DecodedAction::SelectMode {
                mode_idx: action_id - ACTION_BASE_MODE,
            };
        }

        if action_id >= ACTION_BASE_COLOR && action_id < ACTION_BASE_COLOR + 10 {
            return DecodedAction::SelectColor {
                color_idx: action_id - ACTION_BASE_COLOR,
            };
        }

        if action_id >= ACTION_BASE_STAGE_SLOTS && action_id < ACTION_BASE_STAGE_SLOTS + 20 {
            return DecodedAction::SelectStageSlot {
                slot_idx: (action_id - ACTION_BASE_STAGE_SLOTS) as usize,
            };
        }

        if action_id >= ACTION_BASE_HAND && action_id < ACTION_BASE_HAND_CHOICE {
            let adj = (action_id - ACTION_BASE_HAND) as usize;
            let hand_idx = adj / 10;
            let offset = adj % 10;
            if offset < 3 {
                return DecodedAction::PlayMember {
                    hand_idx,
                    slot_idx: offset,
                    other_slot: None,
                    choice_idx: None,
                };
            } else if offset >= 3 && offset < 9 {
                let combo_idx = offset - 3;
                let slot_idx = combo_idx / 2;
                let is_next = (combo_idx % 2) == 1;
                let other_slot = crate::core::logic::game::GameState::get_combo_other_slot(slot_idx, is_next);
                return DecodedAction::PlayMember {
                    hand_idx,
                    slot_idx,
                    other_slot: Some(other_slot),
                    choice_idx: None,
                };
            }
        }

        if action_id >= ACTION_BASE_HAND_CHOICE && action_id < ACTION_BASE_HAND_SELECT {
            let adj = (action_id - ACTION_BASE_HAND_CHOICE) as usize;
            let hand_idx = adj / 100;
            let rem = adj % 100;
            let slot_idx = rem / 10;
            let choice_idx = (rem % 10) as i32;
            return DecodedAction::PlayMember {
                hand_idx,
                slot_idx,
                other_slot: None,
                choice_idx: Some(choice_idx),
            };
        }

        if action_id >= ACTION_BASE_HAND_SELECT && action_id < ACTION_BASE_HAND_SELECT + 1000 {
            return DecodedAction::SelectChoice {
                choice_idx: action_id - ACTION_BASE_HAND_SELECT,
            };
        }

        if action_id >= ACTION_BASE_STAGE && action_id < ACTION_BASE_STAGE_CHOICE {
            let adj = action_id - ACTION_BASE_STAGE;
            return DecodedAction::ActivateMember {
                slot_idx: (adj / 100) as usize,
                ab_idx: ((adj % 100) / 10) as usize,
                choice_idx: None,
            };
        }

        if action_id >= ACTION_BASE_STAGE_CHOICE && action_id < ACTION_BASE_DISCARD_ACTIVATE {
            let adj = action_id - ACTION_BASE_STAGE_CHOICE;
            return DecodedAction::ActivateMember {
                slot_idx: (adj / 100) as usize,
                ab_idx: ((adj % 100) / 10) as usize,
                choice_idx: Some(adj % 10),
            };
        }

        if action_id >= ACTION_BASE_DISCARD_ACTIVATE && action_id < ACTION_BASE_DISCARD_ACTIVATE + 600 {
            let adj = action_id - ACTION_BASE_DISCARD_ACTIVATE;
            return DecodedAction::ActivateFromDiscard {
                discard_idx: (adj / 10) as usize,
                ab_idx: (adj % 10) as usize,
            };
        }

        if action_id >= ACTION_BASE_ENERGY && action_id < ACTION_BASE_ENERGY + 100 {
            return DecodedAction::SelectEnergy {
                energy_idx: (action_id - ACTION_BASE_ENERGY) as usize,
            };
        }

        if action_id >= ACTION_BASE_CHOICE && action_id < ACTION_BASE_CHOICE + 2000 {
            return DecodedAction::SelectChoice {
                choice_idx: action_id - ACTION_BASE_CHOICE,
            };
        }

        DecodedAction::Unknown(action_id)
    }

    /// Returns a human-readable label for a given action ID.
    pub fn get_action_label(action_id: i32) -> String {
        match Self::parse_action(action_id) {
            DecodedAction::Pass => "Pass / Done".to_string(),
            DecodedAction::MulliganSelect { card_idx } => format!("Mulligan Hand Index {}", card_idx),
            DecodedAction::SetLive { hand_idx } => format!("Set Live Card (Hand Index {})", hand_idx),
            DecodedAction::SelectMode { mode_idx } => format!("Select Mode {}", mode_idx),
            DecodedAction::SelectColor { color_idx } => {
                let color = match color_idx {
                    0 => "Pink", 1 => "Red", 2 => "Yellow", 3 => "Green", 4 => "Blue", 5 => "Purple",
                    _ => "Unknown",
                };
                format!("Select Color {}", color)
            },
            DecodedAction::SelectStageSlot { slot_idx } => format!("Select Stage Slot {}", slot_idx),
            DecodedAction::PlayMember { hand_idx, slot_idx, other_slot, choice_idx } => {
                let mut s = format!("Play Hand[{}] to Slot {}", hand_idx, slot_idx);
                if let Some(other) = other_slot { s.push_str(&format!(" and Slot {}", other)); }
                if let Some(c) = choice_idx { s.push_str(&format!(" with Choice {}", c)); }
                s
            },
            DecodedAction::ActivateMember { slot_idx, ab_idx, choice_idx } => {
                let mut s = format!("Activate Member Slot {}, Ability {}", slot_idx, ab_idx);
                if let Some(c) = choice_idx { s.push_str(&format!(" with Choice {}", c)); }
                s
            },
            DecodedAction::ActivateFromDiscard { discard_idx, ab_idx } => {
                format!("Activate from Discard Index {}, Ability {}", discard_idx, ab_idx)
            },
            DecodedAction::SelectEnergy { energy_idx } => format!("Select Energy Index {}", energy_idx),
            DecodedAction::SelectChoice { choice_idx } => format!("Select Choice Index {}", choice_idx),
            DecodedAction::Unknown(id) => format!("Unknown Action {}", id),
        }
    }

    /// Extracted from interpreter.rs: Gets the descriptive text for a card choice.
    pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String {
        if let Some(card) = db.get_member(ctx.source_card_id) {
            if !card.original_text.is_empty() { card.original_text.clone() }
            else if !card.ability_text.is_empty() { card.ability_text.clone() }
            else { card.name.clone() }
        } else if let Some(live) = db.get_live(ctx.source_card_id) {
            if !live.original_text.is_empty() { live.original_text.clone() }
            else if !live.ability_text.is_empty() { live.ability_text.clone() }
            else { live.name.clone() }
        } else {
            String::new()
        }
    }
}
