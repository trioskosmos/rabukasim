//! Action factory types

use crate::core::generated_constants::*;
use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::models::AbilityContext;
use crate::core::logic::state::GameState;
use serde_json::json;

fn summarize_modal_option_label(ability: &crate::core::logic::Ability, index: usize) -> Option<String> {
    let frames = ability.get_modal_option_frames(index)?;
    let summary = frames
        .iter()
        .find(|frame| frame.opcode() != crate::core::logic::O_RETURN)
        .map(|frame| frame.components().to_trace_step().summary)?;

    let cleaned = summary
        .trim()
        .trim_end_matches('.')
        .replace("card(s)", "cards")
        .replace("member(s)", "members");
    (!cleaned.is_empty()).then_some(cleaned)
}

/// Decoded action from action ID
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum DecodedAction {
    Pass,
    ToggleMulligan { card_idx: usize },
    SelectTurnOrder { go_first: bool },
    Rps { choice: i32 },
    PlayMember {
        hand_idx: usize,
        slot_idx: usize,
        other_slot: Option<usize>,
        choice_idx: Option<i32>,
    },
    SetLive { hand_idx: usize },
    ActivateEnergy { energy_idx: usize },
    ActivateAbility { card_idx: usize, ability_idx: usize },
    ActivateMember {
        slot_idx: usize,
        ab_idx: usize,
        choice_idx: Option<i32>,
    },
    ActivateFromDiscard { discard_idx: usize, ab_idx: usize },
    ActivateFromHand { hand_idx: usize, ab_idx: usize },
    SelectMode { mode_idx: i32 },
    SelectChoice { choice_idx: i32 },
    SelectColor { color_idx: i32 },
    SelectHand { hand_idx: usize },
    SelectEnergy { energy_idx: usize },
    SelectStageSlot { slot_idx: usize },
    SelectCards { from_zone: i32, selected_indices: Vec<u8> },
    OrderDeck { new_order: Vec<u8> },
    SelectLiveSet { live_indices: Vec<u8> },
    Formation { arrangement: Vec<u8> },
    Unknown,
}

impl DecodedAction {
    /// Decode action ID into DecodedAction
    pub fn decode(action_id: i32) -> Self {
        if action_id == ACTION_BASE_PASS || action_id == 99 {
            return Self::Pass;
        }

        if action_id >= ACTION_BASE_MULLIGAN && action_id < ACTION_BASE_HAND {
            if action_id >= ACTION_BASE_MODE {
                if action_id < ACTION_BASE_COLOR {
                    return Self::SelectMode {
                        mode_idx: action_id - ACTION_BASE_MODE,
                    };
                }
                if action_id < ACTION_BASE_STAGE_SLOTS {
                    return Self::SelectColor {
                        color_idx: action_id - ACTION_BASE_COLOR,
                    };
                }
                if action_id < ACTION_BASE_HAND {
                    return Self::SelectStageSlot {
                        slot_idx: (action_id - ACTION_BASE_STAGE_SLOTS) as usize,
                    };
                }
            }

            if action_id >= ACTION_BASE_LIVESET {
                return Self::SetLive {
                    hand_idx: (action_id - ACTION_BASE_LIVESET) as usize,
                };
            }

            return Self::ToggleMulligan {
                card_idx: (action_id - ACTION_BASE_MULLIGAN) as usize,
            };
        }

        if action_id >= ACTION_BASE_HAND && action_id < ACTION_BASE_HAND_CHOICE {
            if action_id >= ACTION_BASE_HAND_ACTIVATE {
                let raw = action_id - ACTION_BASE_HAND_ACTIVATE;
                return Self::ActivateFromHand {
                    hand_idx: (raw / 10) as usize,
                    ab_idx: (raw % 10) as usize,
                };
            }

            let raw = action_id - ACTION_BASE_HAND;
            let hand_idx = (raw / 10) as usize;
            let slot_code = (raw % 10) as usize;
            let (slot_idx, other_slot) = if slot_code < 3 {
                (slot_code, None)
            } else {
                let combo_idx = slot_code - 3;
                let slot_idx = combo_idx / 2;
                let other_slot = if combo_idx % 2 == 1 {
                    (slot_idx + 1) % 3
                } else {
                    (slot_idx + 2) % 3
                };
                (slot_idx, Some(other_slot))
            };
            return Self::PlayMember {
                hand_idx,
                slot_idx,
                other_slot,
                choice_idx: None,
            };
        }

        if action_id >= ACTION_BASE_HAND_CHOICE && action_id < ACTION_BASE_HAND_SELECT {
            let raw = action_id - ACTION_BASE_HAND_CHOICE;
            if action_id < ACTION_BASE_STAGE {
                return Self::PlayMember {
                    hand_idx: (raw / 100) as usize,
                    slot_idx: ((raw % 100) / 10) as usize,
                    other_slot: None,
                    choice_idx: Some(raw % 10),
                };
            }

            if action_id < ACTION_BASE_STAGE_CHOICE {
                return Self::ActivateMember {
                    slot_idx: (raw / 100) as usize,
                    ab_idx: ((raw % 100) / 10) as usize,
                    choice_idx: None,
                };
            }

            if action_id < ACTION_BASE_DISCARD_ACTIVATE {
                return Self::ActivateMember {
                    slot_idx: (raw / 100) as usize,
                    ab_idx: ((raw % 100) / 10) as usize,
                    choice_idx: Some(raw % 10),
                };
            }

            return Self::ActivateFromDiscard {
                discard_idx: (action_id - ACTION_BASE_DISCARD_ACTIVATE) as usize / 10,
                ab_idx: (action_id - ACTION_BASE_DISCARD_ACTIVATE) as usize % 10,
            };
        }

        if action_id >= ACTION_BASE_HAND_SELECT && action_id < ACTION_BASE_STAGE {
            return Self::SelectHand {
                hand_idx: (action_id - ACTION_BASE_HAND_SELECT) as usize,
            };
        }

        if action_id >= ACTION_BASE_STAGE && action_id < ACTION_BASE_STAGE_CHOICE {
            let raw = action_id - ACTION_BASE_STAGE;
            return Self::ActivateMember {
                slot_idx: (raw / 100) as usize,
                ab_idx: ((raw % 100) / 10) as usize,
                choice_idx: None,
            };
        }

        if action_id >= ACTION_BASE_STAGE_CHOICE && action_id < ACTION_BASE_DISCARD_ACTIVATE {
            let raw = action_id - ACTION_BASE_STAGE_CHOICE;
            return Self::ActivateMember {
                slot_idx: (raw / 100) as usize,
                ab_idx: ((raw % 100) / 10) as usize,
                choice_idx: Some(raw % 10),
            };
        }

        if action_id >= ACTION_BASE_DISCARD_ACTIVATE && action_id < ACTION_BASE_ENERGY {
            let raw = action_id - ACTION_BASE_DISCARD_ACTIVATE;
            return Self::ActivateFromDiscard {
                discard_idx: (raw / 10) as usize,
                ab_idx: (raw % 10) as usize,
            };
        }

        if action_id >= ACTION_BASE_ENERGY && action_id < ACTION_BASE_CHOICE {
            return Self::SelectEnergy {
                energy_idx: (action_id - ACTION_BASE_ENERGY) as usize,
            };
        }

        if action_id >= ACTION_BASE_CHOICE && action_id < ACTION_BASE_RPS {
            return Self::SelectChoice {
                choice_idx: action_id - ACTION_BASE_CHOICE,
            };
        }

        if action_id >= ACTION_BASE_RPS_P2 && action_id < ACTION_BASE_RPS_P2 + 3 {
            return Self::Rps {
                choice: action_id - ACTION_BASE_RPS_P2,
            };
        }

        if action_id >= ACTION_BASE_RPS && action_id < ACTION_BASE_RPS + 3 {
            return Self::Rps {
                choice: action_id - ACTION_BASE_RPS,
            };
        }

        if action_id == ACTION_BASE_TURN_ORDER_FIRST {
            return Self::SelectTurnOrder { go_first: true };
        }

        if action_id == ACTION_BASE_TURN_ORDER_FIRST + 1 {
            return Self::SelectTurnOrder { go_first: false };
        }

        Self::Unknown
    }
}

pub struct ActionFactory;

impl ActionFactory {
    pub fn get_choice_text(db: &CardDatabase, ctx: &AbilityContext) -> String {
        let ability_text = |abilities: &[crate::core::logic::Ability]| {
            usize::try_from(ctx.ability_index)
                .ok()
                .and_then(|ability_index| abilities.get(ability_index))
                .map(|ability| {
                    if !ability.raw_text.is_empty() {
                        ability.raw_text.clone()
                    } else {
                        ability
                            .option_names
                            .first()
                            .cloned()
                            .unwrap_or_else(|| "Choose an option".to_string())
                    }
                })
        };

        if let Some(card) = db.get_member(ctx.source_card_id) {
            if let Some(text) = ability_text(&card.abilities) {
                return text;
            }
            if !card.ability_text.is_empty() {
                return card.ability_text.clone();
            }
            if !card.original_text.is_empty() {
                return card.original_text.clone();
            }
            if !card.name.is_empty() {
                return card.name.clone();
            }
        }

        if let Some(card) = db.get_live(ctx.source_card_id) {
            if let Some(text) = ability_text(&card.abilities) {
                return text;
            }
            if !card.ability_text.is_empty() {
                return card.ability_text.clone();
            }
            if !card.original_text.is_empty() {
                return card.original_text.clone();
            }
            if !card.name.is_empty() {
                return card.name.clone();
            }
        }

        "Choose an option".to_string()
    }

    pub fn infer_all_select_mode_options(
        db: &CardDatabase,
        source_card_id: i32,
        ability_index: i16,
        option_count: i16,
    ) -> Vec<serde_json::Value> {
        let abilities = db
            .get_member(source_card_id)
            .map(|card| card.abilities.as_slice())
            .or_else(|| db.get_live(source_card_id).map(|card| card.abilities.as_slice()));

        let Some(ability) = abilities.and_then(|abilities| {
            usize::try_from(ability_index)
                .ok()
                .and_then(|ability_index| abilities.get(ability_index))
        }) else {
            return Vec::new();
        };

        let count = usize::try_from(option_count.max(0)).unwrap_or(0).max(
            ability
                .option_names
                .len()
                .max(ability.modal_option_count())
                .max(ability.choice_count as usize),
        );

        (0..count)
            .map(|index| {
                let label = ability
                    .option_names
                    .get(index)
                    .cloned()
                    .filter(|label| !label.is_empty())
                    .or_else(|| summarize_modal_option_label(ability, index))
                    .unwrap_or_else(|| format!("Option {}", index + 1));
                json!({
                    "index": index,
                    "label": label,
                })
            })
            .collect()
    }

    pub fn get_action_label(action_id: i32) -> String {
        format!("{:?}", DecodedAction::decode(action_id))
    }

    pub fn get_verbose_action_label(
        action_id: i32,
        _state: &GameState,
        _db: &CardDatabase,
    ) -> String {
        Self::get_action_label(action_id)
    }
}
