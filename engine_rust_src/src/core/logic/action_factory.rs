use crate::core::generated_constants::*;
use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::models::AbilityContext;

/// Structured representation of a decoded Action ID.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum DecodedAction {
    Pass,
    MulliganSelect {
        card_idx: u16,
    },
    SetLive {
        hand_idx: usize,
    },
    SelectMode {
        mode_idx: i32,
    },
    SelectColor {
        color_idx: i32,
    },
    SelectStageSlot {
        slot_idx: usize,
    },
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
    ActivateFromHand {
        hand_idx: usize,
        ab_idx: usize,
    },
    SelectEnergy {
        energy_idx: usize,
    },
    SelectChoice {
        choice_idx: i32,
    },
    Rps {
        p_idx: usize,
        choice: i8,
    },
    TurnChoice {
        choice: i8,
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

        if action_id >= ACTION_BASE_HAND && action_id < ACTION_BASE_HAND_ACTIVATE {
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
                let other_slot =
                    crate::core::logic::game::GameState::get_combo_other_slot(slot_idx, is_next);
                return DecodedAction::PlayMember {
                    hand_idx,
                    slot_idx,
                    other_slot: Some(other_slot),
                    choice_idx: None,
                };
            }
        }

        if action_id >= ACTION_BASE_HAND_ACTIVATE && action_id < ACTION_BASE_HAND_CHOICE {
            let adj = (action_id - ACTION_BASE_HAND_ACTIVATE) as usize;
            return DecodedAction::ActivateFromHand {
                hand_idx: adj / 10,
                ab_idx: adj % 10,
            };
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

        if action_id >= ACTION_BASE_HAND_SELECT && action_id < ACTION_BASE_STAGE {
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

        if action_id >= ACTION_BASE_DISCARD_ACTIVATE && action_id < ACTION_BASE_ENERGY {
            let adj = action_id - ACTION_BASE_DISCARD_ACTIVATE;
            return DecodedAction::ActivateFromDiscard {
                discard_idx: (adj / 10) as usize,
                ab_idx: (adj % 10) as usize,
            };
        }

        if action_id >= ACTION_BASE_ENERGY && action_id < ACTION_BASE_CHOICE {
            return DecodedAction::SelectEnergy {
                energy_idx: (action_id - ACTION_BASE_ENERGY) as usize,
            };
        }

        if action_id >= ACTION_BASE_CHOICE && action_id < ACTION_BASE_CHOICE + 5000 {
            return DecodedAction::SelectChoice {
                choice_idx: action_id - ACTION_BASE_CHOICE,
            };
        }

        if action_id >= ACTION_BASE_RPS && action_id < ACTION_BASE_RPS + 10 {
            return DecodedAction::Rps {
                p_idx: 0,
                choice: (action_id - ACTION_BASE_RPS) as i8,
            };
        }
        if action_id >= ACTION_BASE_RPS_P2 && action_id < ACTION_BASE_RPS_P2 + 10 {
            return DecodedAction::Rps {
                p_idx: 1,
                choice: (action_id - ACTION_BASE_RPS_P2) as i8,
            };
        }

        DecodedAction::Unknown(action_id)
    }

    /// Returns a human-readable label for a given action ID, including card details if available.
    pub fn get_verbose_action_label(
        action_id: i32,
        state: &super::game::GameState,
        db: &CardDatabase,
    ) -> String {
        if state.phase == crate::core::enums::Phase::TurnChoice {
            if action_id == ACTION_BASE_TURN_ORDER_FIRST {
                return "Turn Choice: Go First".to_string();
            }
            if action_id == ACTION_BASE_TURN_ORDER_FIRST + 1 {
                return "Turn Choice: Go Second".to_string();
            }
        }

        let decoded = Self::parse_action(action_id);
        if let DecodedAction::SelectMode { mode_idx } = decoded {
            if let Some(pi) = state.interaction_stack.last() {
                let card_id = if pi.card_id != -1 { pi.card_id } else { pi.ctx.source_card_id };
                if let Some(card) = db.get_member(card_id) {
                    if let Some(ab) = card.abilities.get(pi.ability_index as usize) {
                        if let Some(name) = ab.option_names.get(mode_idx as usize) {
                            if !name.is_empty() {
                                return format!("Mode: {}", Self::map_technical_label(name));
                            }
                        }
                        if let Some(options) = ab.modal_options.as_object() {
                            if let Some(name) = options.get(&mode_idx.to_string()) {
                                if let Some(s) = name.as_str() {
                                    return format!("Mode: {}", Self::map_technical_label(s));
                                }
                            }
                        }
                    }
                }
            }
        }

        let p_idx = state.current_player as usize;
        let player = &state.players[p_idx];

        match decoded {
            DecodedAction::MulliganSelect { card_idx } => {
                if let Some(&cid) = player.hand.get(card_idx as usize) {
                    if let Some(m) = db.get_member(cid) {
                        return format!("Mulligan Hand[{}] ([{}] {})", card_idx, m.card_no, m.name);
                    }
                }
                format!("Mulligan Hand[{}]", card_idx)
            }
            DecodedAction::SetLive { hand_idx } => {
                if let Some(&cid) = player.hand.get(hand_idx) {
                    if let Some(l) = db.get_live(cid) {
                        return format!(
                            "Set Live card ([{}] {}) (Hand[{}])",
                            l.card_no, l.name, hand_idx
                        );
                    }
                }
                format!("Set Live card (Hand[{}])", hand_idx)
            }
            DecodedAction::PlayMember {
                hand_idx,
                slot_idx,
                other_slot,
                choice_idx,
            } => {
                let mut label = String::new();
                if let Some(&cid) = player.hand.get(hand_idx) {
                    if let Some(m) = db.get_member(cid) {
                        label = format!(
                            "Play ([{}] {}) (Hand[{}]) to Slot {}",
                            m.card_no, m.name, hand_idx, slot_idx
                        );
                    }
                }
                if label.is_empty() {
                    label = format!("Play Hand[{}] to Slot {}", hand_idx, slot_idx);
                }
                if let Some(other) = other_slot {
                    label.push_str(&format!(" and Slot {}", other));
                }
                if let Some(c) = choice_idx {
                    label.push_str(&format!(" with Choice {}", c));
                }
                label
            }
            DecodedAction::ActivateMember {
                slot_idx,
                ab_idx,
                choice_idx,
            } => {
                let cid = player.stage[slot_idx];
                let mut label = String::new();
                if cid >= 0 {
                    if let Some(m) = db.get_member(cid) {
                        label = format!(
                            "Activate ([{}] {}) at Slot {}, Ability {}",
                            m.card_no, m.name, slot_idx, ab_idx
                        );
                    }
                }
                if label.is_empty() {
                    label = format!("Activate Slot {}, Ability {}", slot_idx, ab_idx);
                }
                if let Some(c) = choice_idx {
                    label.push_str(&format!(" with Choice {}", c));
                }
                label
            }
            DecodedAction::ActivateFromDiscard {
                discard_idx,
                ab_idx,
            } => {
                if let Some(&cid) = player.discard.get(discard_idx) {
                    if let Some(m) = db.get_member(cid) {
                        return format!(
                            "Activate from Discard Index {}, Ability {} ([{}] {})",
                            discard_idx, ab_idx, m.card_no, m.name
                        );
                    }
                }
                format!(
                    "Activate from Discard Index {}, Ability {}",
                    discard_idx, ab_idx
                )
            }
            DecodedAction::ActivateFromHand { hand_idx, ab_idx } => {
                if let Some(&cid) = player.hand.get(hand_idx) {
                    if let Some(m) = db.get_member(cid) {
                        return format!(
                            "Activate from Hand Index {}, Ability {} ([{}] {})",
                            hand_idx, ab_idx, m.card_no, m.name
                        );
                    }
                }
                format!("Activate from Hand Index {}, Ability {}", hand_idx, ab_idx)
            }
            DecodedAction::Rps { p_idx, choice } => {
                let move_label = match choice {
                    0 => "Rock",
                    1 => "Paper",
                    2 => "Scissors",
                    _ => "Unknown",
                };
                format!("RPS (P{}): {}", p_idx + 1, move_label)
            }
            DecodedAction::SelectStageSlot { slot_idx } => {
                let cid = player.stage[slot_idx];
                let slot_name = match slot_idx {
                    0 => "Left Slot",
                    1 => "Mid Slot",
                    2 => "Right Slot",
                    _ => "Stage Slot",
                };
                if cid >= 0 {
                    if let Some(m) = db.get_member(cid) {
                        return format!("Select Member ([{}] {}) at Slot {}", m.card_no, m.name, slot_idx + 1);
                    }
                }
                format!("Select {}", slot_name)
            }
            DecodedAction::TurnChoice { choice } => {
                format!(
                    "Turn Choice: {}",
                    if choice == 0 { "Go First" } else { "Go Second" }
                )
            }
            DecodedAction::SelectChoice { choice_idx } => {
                let choice_idx = choice_idx as usize;
                if let Some(pi) = state.interaction_stack.last() {
                    if let Some(option) = pi.options.get(choice_idx) {
                        if let Some(s) = option.as_str() {
                            if !s.is_empty() {
                                return Self::map_technical_label(s);
                            }
                        }
                    }
                }
                Self::get_action_label(action_id)
            }
            _ => {
                if state.phase == crate::core::enums::Phase::TurnChoice {
                    if action_id == ACTION_BASE_TURN_ORDER_FIRST {
                        return "Turn Choice: Go First".to_string();
                    }
                    if action_id == ACTION_BASE_TURN_ORDER_FIRST + 1 {
                        return "Turn Choice: Go Second".to_string();
                    }
                }
                Self::get_action_label(action_id)
            }
        }
    }

    /// Returns a human-readable label for a given action ID.
    pub fn get_action_label(action_id: i32) -> String {
        match Self::parse_action(action_id) {
            DecodedAction::Pass => "Pass / Done".to_string(),
            DecodedAction::MulliganSelect { card_idx } => {
                format!("Mulligan Hand Index {}", card_idx)
            }
            DecodedAction::SetLive { hand_idx } => {
                format!("Set Live Card (Hand Index {})", hand_idx)
            }
            DecodedAction::SelectMode { mode_idx } => format!("Select Mode {}", mode_idx),
            DecodedAction::SelectColor { color_idx } => {
                let color = match color_idx {
                    0 => "Pink",
                    1 => "Red",
                    2 => "Yellow",
                    3 => "Green",
                    4 => "Blue",
                    5 => "Purple",
                    _ => "Unknown",
                };
                format!("Select Color {}", color)
            }
            DecodedAction::SelectStageSlot { slot_idx } => {
                match slot_idx {
                    0 => "Select Left Slot".to_string(),
                    1 => "Select Mid Slot".to_string(),
                    2 => "Select Right Slot".to_string(),
                    _ => "Select Slot".to_string(),
                }
            }
            DecodedAction::PlayMember {
                hand_idx,
                slot_idx,
                other_slot,
                choice_idx,
            } => {
                let mut s = format!("Play Hand[{}] to Slot {}", hand_idx, slot_idx);
                if let Some(other) = other_slot {
                    s.push_str(&format!(" and Slot {}", other));
                }
                if let Some(c) = choice_idx {
                    s.push_str(&format!(" with Choice {}", c));
                }
                s
            }
            DecodedAction::ActivateMember {
                slot_idx,
                ab_idx,
                choice_idx,
            } => {
                let mut s = format!("Activate Member Slot {}, Ability {}", slot_idx, ab_idx);
                if let Some(c) = choice_idx {
                    s.push_str(&format!(" with Choice {}", c));
                }
                s
            }
            DecodedAction::ActivateFromDiscard {
                discard_idx,
                ab_idx,
            } => {
                format!(
                    "Activate from Discard Index {}, Ability {}",
                    discard_idx, ab_idx
                )
            }
            DecodedAction::ActivateFromHand { hand_idx, ab_idx } => {
                format!("Activate from Hand Index {}, Ability {}", hand_idx, ab_idx)
            }
            DecodedAction::SelectEnergy { energy_idx } => {
                format!("Select Energy Index {}", energy_idx)
            }
            DecodedAction::SelectChoice { choice_idx } => {
                format!("Choice {}", choice_idx + 1)
            }
            DecodedAction::Rps { p_idx, choice } => {
                let move_label = match choice {
                    0 => "Rock",
                    1 => "Paper",
                    2 => "Scissors",
                    _ => "Unknown",
                };
                format!("RPS (P{}): {}", p_idx + 1, move_label)
            }
            DecodedAction::TurnChoice { choice } => {
                format!(
                    "Turn Choice: {}",
                    if choice == 0 { "Go First" } else { "Go Second" }
                )
            }
            DecodedAction::Unknown(id) => format!("Unknown Action {}", id),
        }
    }

    /// Gets the descriptive text for a card choice.
    pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String {
        let (original_text, ability_text, name) = if let Some(card) = db.get_member(ctx.source_card_id) {
            (&card.original_text, &card.ability_text, &card.name)
        } else if let Some(live) = db.get_live(ctx.source_card_id) {
            (&live.original_text, &live.ability_text, &live.name)
        } else {
            return String::new();
        };

        if !original_text.is_empty() && !ability_text.is_empty() {
            format!("[JP] {} / [EN] {}", original_text, ability_text)
        } else if !original_text.is_empty() {
            original_text.clone()
        } else if !ability_text.is_empty() {
            ability_text.clone()
        } else if !name.is_empty() {
            // Provide a more descriptive label for optional choices if only the name is available
            format!("Activate {}?", name)
        } else {
            String::new()
        }
    }

    /// Maps a technical label (like "PAY_ENERGY(2)") to a friendly multi-lang string.
    pub fn map_technical_label(label: &str) -> String {
        if label.is_empty() {
            return label.to_string();
        }

        // Check for common technical patterns
        if label.starts_with("PAY_ENERGY(") && label.ends_with(')') {
            let val = &label[11..label.len() - 1];
            return format!("[JP] {}エネルギーを支払う / [EN] Pay {} Energy", val, val);
        }
        if label.starts_with("DISCARD_HAND(") && label.ends_with(')') {
            let val = &label[13..label.len() - 1];
            return format!("[JP] 手札を{}枚捨てる / [EN] Discard {} card(s)", val, val);
        }
        if label.starts_with("DRAW(") && label.ends_with(')') {
            let val = &label[5..label.len() - 1];
            return format!("[JP] カードを{}枚引く / [EN] Draw {} card(s)", val, val);
        }
        if label.starts_with("ADD_HEARTS(") && label.ends_with(')') {
            let val = &label[11..label.len() - 1];
            return format!("[JP] ボルテージ+{} / [EN] Voltage +{}", val, val);
        }
        if label.starts_with("ADD_BLADES(") && label.ends_with(')') {
            let val = &label[11..label.len() - 1];
            return format!("[JP] ブレード+{} / [EN] Blade +{}", val, val);
        }

        // Special case for generic Pass/Done if it matches technical key
        if label == "PASS" || label == "DONE" {
            return "[JP] 終了 / [EN] Pass / Done".to_string();
        }

        label.to_string()
    }
}
