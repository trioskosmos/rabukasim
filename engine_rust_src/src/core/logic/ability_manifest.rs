use serde::{Deserialize, Serialize};
use serde_json::{Map, Value};
use std::collections::BTreeMap;

const CONTROL_OPS: &[&str] = &["RETURN", "JUMP", "JUMP_IF_FALSE"];
const PROMPT_OPS: &[&str] = &[
    "SELECT_MODE",
    "SELECT_MEMBER",
    "SELECT_CARDS",
    "LOOK_AND_CHOOSE",
    "SELECT_PLAYER",
    "SELECT_LIVE",
    "OPPONENT_CHOOSE",
];
const COST_OPS: &[&str] = &[
    "PAY_ENERGY",
    "PAY_ENERGY_DYNAMIC",
    "MOVE_TO_DISCARD",
    "SET_TAPPED",
    "TAP_MEMBER",
    "ACTIVATE_ENERGY",
    "REDUCE_COST",
    "INCREASE_COST",
    "INCREASE_HEART_COST",
    "REDUCE_HEART_REQ",
    "REDUCE_LIVE_SET_LIMIT",
    "PREVENT_PLAY_TO_SLOT",
    "PREVENT_ACTIVATE",
    "PREVENT_BATON_TOUCH",
    "PREVENT_SET_TO_SUCCESS_PILE",
];

pub const MANIFEST_SCHEMA: &str = "ability_manifest.v1";

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize, Default)]
pub struct AbilityManifestSummary {
    pub card_count: usize,
    pub ability_count: usize,
    pub trigger_counts: BTreeMap<String, usize>,
    pub flow_counts: BTreeMap<String, usize>,
    pub opcode_counts: BTreeMap<String, usize>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AbilityManifestFrame {
    pub index: usize,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub opcode_id: Option<i32>,
    pub opcode: String,
    pub role: String,
    pub summary: String,
    pub optional: bool,
    pub negated: bool,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<i32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub attr: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub slot: Option<Value>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub decoded: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AbilityManifestAbility {
    pub ability_index: usize,
    pub trigger_id: i32,
    pub trigger: String,
    pub flow_pattern: String,
    pub summary: String,
    pub frame_count: usize,
    pub opcode_sequence: Vec<String>,
    pub source_text: String,
    pub source_text_en: String,
    pub frames: Vec<AbilityManifestFrame>,
    pub choice_flags: u8,
    pub choice_count: u8,
    pub requires_selection: bool,
    pub is_once_per_turn: bool,
    pub card_no: String,
    pub card_id: i32,
    pub name: String,
    pub db: String,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AbilityManifestCard {
    pub card_id: i32,
    pub card_no: String,
    pub name: String,
    pub db: String,
    pub ability_count: usize,
    pub source_text: String,
    pub source_text_en: String,
    pub abilities: Vec<AbilityManifestAbility>,
}

#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct AbilityManifest {
    pub generated_at: String,
    pub source_cards: String,
    pub source_metadata: String,
    pub schema: String,
    pub summary: AbilityManifestSummary,
    pub cards: Vec<AbilityManifestCard>,
}

impl AbilityManifest {
    pub fn build(
        cards_payload: &Value,
        metadata: &Value,
        generated_at: String,
        source_cards: String,
        source_metadata: String,
    ) -> Self {
        let mut cards_out = Vec::new();
        let mut trigger_counts: BTreeMap<String, usize> = BTreeMap::new();
        let mut flow_counts: BTreeMap<String, usize> = BTreeMap::new();
        let mut opcode_counts: BTreeMap<String, usize> = BTreeMap::new();

        for (db_name, card) in iter_cards(cards_payload) {
            let card_no = card
                .get("card_no")
                .and_then(Value::as_str)
                .unwrap_or("")
                .trim()
                .to_string();
            let card_id = card.get("card_id").and_then(Value::as_i64).unwrap_or(0) as i32;
            let name = card
                .get("name")
                .and_then(Value::as_str)
                .unwrap_or("")
                .to_string();
            let source_text = normalize_source_text(card);
            let source_text_en = card
                .get("original_text_en")
                .and_then(Value::as_str)
                .unwrap_or("")
                .trim()
                .to_string();
            let abilities = card
                .get("abilities")
                .and_then(Value::as_array)
                .cloned()
                .unwrap_or_default();

            let mut abilities_out = Vec::new();

            for (ability_index, ability) in abilities.iter().enumerate() {
                let trigger_id = ability.get("trigger").and_then(Value::as_i64).unwrap_or(0) as i32;
                let trigger = trigger_name(metadata, trigger_id);
                let instructions = ability
                    .get("frame_program")
                    .and_then(|program| program.get("instructions").or_else(|| program.get("frames")))
                    .and_then(Value::as_array)
                    .cloned()
                    .unwrap_or_default();

                let mut frame_values = Vec::new();
                let mut opcode_sequence = Vec::new();
                for (idx, frame) in instructions.iter().enumerate() {
                    if !frame.is_object() {
                        continue;
                    }
                    let normalized = normalize_frame(metadata, frame, idx);
                    opcode_sequence.push(normalized.opcode.clone());
                    frame_values.push(normalized);
                }

                let (flow_pattern, summary) = summarize_frames(metadata, &instructions);

                *trigger_counts.entry(trigger.clone()).or_default() += 1;
                *flow_counts.entry(flow_pattern.clone()).or_default() += 1;
                for opcode in &opcode_sequence {
                    *opcode_counts.entry(opcode.clone()).or_default() += 1;
                }

                abilities_out.push(AbilityManifestAbility {
                    ability_index,
                    trigger_id,
                    trigger,
                    flow_pattern,
                    summary,
                    frame_count: frame_values.len(),
                    opcode_sequence,
                    source_text: source_text.clone(),
                    source_text_en: source_text_en.clone(),
                    frames: frame_values,
                    choice_flags: ability.get("choice_flags").and_then(Value::as_u64).unwrap_or(0) as u8,
                    choice_count: ability.get("choice_count").and_then(Value::as_u64).unwrap_or(0) as u8,
                    requires_selection: ability
                        .get("requires_selection")
                        .and_then(Value::as_bool)
                        .unwrap_or(false),
                    is_once_per_turn: ability
                        .get("is_once_per_turn")
                        .and_then(Value::as_bool)
                        .unwrap_or(false),
                    card_no: card_no.clone(),
                    card_id,
                    name: name.clone(),
                    db: db_name.to_string(),
                });
            }

            if !abilities_out.is_empty() {
                cards_out.push(AbilityManifestCard {
                    card_id,
                    card_no,
                    name,
                    db: db_name.to_string(),
                    ability_count: abilities_out.len(),
                    source_text,
                    source_text_en,
                    abilities: abilities_out,
                });
            }
        }

        cards_out.sort_by(|a, b| a.card_no.cmp(&b.card_no).then_with(|| a.card_id.cmp(&b.card_id)));

        let total_abilities: usize = cards_out.iter().map(|card| card.ability_count).sum();

        Self {
            generated_at,
            source_cards,
            source_metadata,
            schema: MANIFEST_SCHEMA.to_string(),
            summary: AbilityManifestSummary {
                card_count: cards_out.len(),
                ability_count: total_abilities,
                trigger_counts,
                flow_counts,
                opcode_counts,
            },
            cards: cards_out,
        }
    }

    pub fn card_by_no(&self, card_no: &str) -> Option<&AbilityManifestCard> {
        self.cards.iter().find(|card| card.card_no == card_no)
    }

    pub fn card_by_id(&self, card_id: i32) -> Option<&AbilityManifestCard> {
        self.cards.iter().find(|card| card.card_id == card_id)
    }

    pub fn render_markdown(&self) -> String {
        let mut out = String::new();
        out.push_str("# Ability System Manifest\n\n");
        out.push_str(&format!(
            "Generated: {}  Cards with abilities: {}  Total abilities: {}\n\n",
            self.generated_at, self.summary.card_count, self.summary.ability_count
        ));
        out.push_str("## Summary\n\n");
        out.push_str("| Metric | Value |\n");
        out.push_str("| :-- | --: |\n");
        out.push_str(&format!("| Cards | {} |\n", self.summary.card_count));
        out.push_str(&format!("| Abilities | {} |\n", self.summary.ability_count));

        out.push_str("\n### Trigger Counts\n");
        for (name, count) in &self.summary.trigger_counts {
            out.push_str(&format!("- `{}`: {}\n", name, count));
        }

        out.push_str("\n### Flow Counts\n");
        for (name, count) in &self.summary.flow_counts {
            out.push_str(&format!("- `{}`: {}\n", name, count));
        }

        out.push_str("\n## Cards\n");
        for card in &self.cards {
            out.push_str(&format!("\n### {} - {}\n\n", card.card_no, card.name));
            out.push_str(&format!("- `card_id`: {}\n", card.card_id));
            out.push_str(&format!("- `db`: `{}`\n", card.db));

            if !card.source_text.is_empty() {
                out.push_str(&format!("\n```text\n{}\n```\n", card.source_text));
            }

            for ability in &card.abilities {
                let opcode_sequence = ability.opcode_sequence.join(", ");
                out.push_str(&format!("\n#### Ability {}\n\n", ability.ability_index + 1));
                out.push_str(&format!("- `trigger`: `{}`\n", ability.trigger));
                out.push_str(&format!("- `flow_pattern`: `{}`\n", ability.flow_pattern));
                out.push_str(&format!("- `summary`: {}\n", ability.summary));
                out.push_str(&format!("- `opcode_sequence`: `{}`\n", opcode_sequence));
                if !ability.source_text_en.is_empty() {
                    out.push_str(&format!("- `source_text_en`: {}\n", ability.source_text_en));
                }

                out.push_str("\n| # | Role | Opcode | Summary |\n");
                out.push_str("| :-- | :-- | :-- | :-- |\n");
                for frame in &ability.frames {
                    out.push_str(&format!(
                        "| {} | {} | `{}` | {} |\n",
                        frame.index,
                        frame.role,
                        frame.opcode,
                        frame.summary.replace('|', "\\|")
                    ));
                }
            }
        }

        out
    }
}

fn metadata_lookup(map: &Value, section: &str, id: i32) -> String {
    let id = id as i64;
    map.get(section)
        .and_then(|v| v.as_object())
        .and_then(|obj| {
            obj.iter().find_map(|(name, raw)| {
                raw.as_i64().filter(|found| *found == id).map(|_| name.clone())
            })
        })
        .unwrap_or_else(|| format!("{}_{}", section.to_uppercase(), id))
}

fn trigger_name(metadata: &Value, id: i32) -> String {
    metadata_lookup(metadata, "triggers", id)
}

fn opcode_name(metadata: &Value, frame: &Value) -> String {
    if let Some(name) = frame
        .get("opcode")
        .or_else(|| frame.get("op"))
        .or_else(|| frame.get("opcode_name"))
        .or_else(|| frame.get("kind"))
        .and_then(Value::as_str)
    {
        return name.to_ascii_uppercase();
    }
    if let Some(id) = frame.get("opcode_id").and_then(Value::as_i64) {
        return metadata_lookup(metadata, "opcodes", id as i32);
    }
    "UNKNOWN".to_string()
}

fn object_field<'a>(value: &'a Value, key: &str) -> Option<&'a Value> {
    value.get(key).and_then(|item| item.is_object().then_some(item))
}

fn frame_field<'a>(frame: &'a Value, key: &str) -> Option<&'a Value> {
    object_field(frame, key)
        .or_else(|| frame.get("semantic").and_then(|semantic| object_field(semantic, key)))
}

fn bool_flag(value: &Value, key: &str) -> bool {
    value.get(key).and_then(Value::as_bool).unwrap_or(false)
}

fn frame_bool_flag(frame: &Value, key: &str) -> bool {
    bool_flag(frame, key) || semantic_flag(frame, key)
}

fn semantic_value<'a>(frame: &'a Value, key: &str) -> Option<&'a Value> {
    frame.get("semantic").and_then(|semantic| semantic.get(key))
}

fn semantic_flag(value: &Value, key: &str) -> bool {
    semantic_value(value, key).and_then(Value::as_bool).unwrap_or(false)
}

fn nested_flag_value(frame: &Value, key: &str, nested_key: &str) -> bool {
    frame
        .get(key)
        .or_else(|| semantic_value(frame, key))
        .and_then(|value| value.get(nested_key))
        .and_then(Value::as_i64)
        .unwrap_or(0)
        != 0
}

fn semantic_text_contains(value: &Value, needle: &str) -> bool {
    value
        .get("decoded")
        .or_else(|| semantic_value(value, "decoded"))
        .and_then(Value::as_str)
        .map(|decoded| decoded.to_ascii_lowercase().contains(needle))
        .unwrap_or(false)
}

fn frame_attr(frame: &Value) -> Option<&Value> {
    frame_field(frame, "attr")
}

fn frame_slot(frame: &Value) -> Option<&Value> {
    frame_field(frame, "slot")
}

fn is_optional_frame(frame: &Value) -> bool {
    bool_flag(frame, "optional")
        || nested_flag_value(frame, "filter", "is_optional")
        || nested_flag_value(frame, "attr", "is_optional")
        || frame_bool_flag(frame, "is_optional")
        || frame_bool_flag(frame, "optional_effect")
        || semantic_text_contains(frame, "optional")
        || semantic_text_contains(frame, "may")
        || semantic_text_contains(frame, "もよい")
}

fn is_negated_frame(frame: &Value) -> bool {
    frame_bool_flag(frame, "is_negated") || frame_bool_flag(frame, "negated")
}

fn friendly_zone(zone: Option<&Value>) -> String {
    let Some(zone) = zone.and_then(Value::as_str) else {
        return String::new();
    };
    match zone.to_ascii_uppercase().as_str() {
        "HAND" => "hand".to_string(),
        "DISCARD" => "discard".to_string(),
        "STAGE" => "stage".to_string(),
        "DECK" => "deck".to_string(),
        "DECK_TOP" => "top of deck".to_string(),
        "DECK_BOTTOM" => "bottom of deck".to_string(),
        "ENERGY" => "energy".to_string(),
        "LIVE" | "SUCCESS_PILE" => "success pile".to_string(),
        other => other.to_ascii_lowercase().replace('_', " "),
    }
}

fn frame_role(op: &str, optional: bool) -> &'static str {
    if CONTROL_OPS.contains(&op) {
        "control"
    } else if PROMPT_OPS.contains(&op) {
        "prompt"
    } else if COST_OPS.contains(&op) || optional {
        "cost"
    } else {
        "effect"
    }
}

fn compact_value(value: &Value) -> Value {
    match value {
        Value::Object(map) => {
            let mut out = Map::new();
            for (key, item) in map.iter().filter(|(_, item)| match item {
                Value::Null => false,
                Value::String(text) => !text.is_empty(),
                Value::Array(items) => !items.is_empty(),
                Value::Object(obj) => !obj.is_empty(),
                _ => true,
            }) {
                out.insert(key.clone(), compact_value(item));
            }
            Value::Object(out)
        }
        Value::Array(items) => Value::Array(items.iter().map(compact_value).collect()),
        other => other.clone(),
    }
}

fn describe_frame(metadata: &Value, frame: &Value) -> String {
    let op = opcode_name(metadata, frame);
    let value = frame.get("value").and_then(Value::as_i64).unwrap_or(0);
    let attr = frame_attr(frame);
    let slot = frame_slot(frame);
    let optional = is_optional_frame(frame);
    let prefix = if optional && !CONTROL_OPS.contains(&op.as_str()) {
        "May "
    } else {
        ""
    };

    match op.as_str() {
        "RETURN" => "Done.".to_string(),
        "JUMP" => format!("Jump ahead {} frame(s).", value),
        "JUMP_IF_FALSE" => format!("Skip ahead {} frame(s) if the preceding condition fails.", value),
        "DRAW" => format!("{prefix}Draw {} card(s).", value),
        "BOOST_SCORE" => format!("{prefix}Gain +{} score.", value),
        "RECOVER_MEMBER" => {
            let source = friendly_zone(slot.and_then(|s| s.get("source_zone"))).if_empty("discard");
            let target = friendly_zone(slot.and_then(|s| s.get("dest_zone"))).if_empty("hand");
            format!("{prefix}Recover {} member(s) from {} to {}.", value, source, target)
        }
        "RECOVER_LIVE" => {
            let target = friendly_zone(slot.and_then(|s| s.get("dest_zone"))).if_empty("success pile");
            format!("{prefix}Recover {} live card(s) to {}.", value, target)
        }
        "MOVE_TO_DISCARD" => {
            let source = friendly_zone(slot.and_then(|s| s.get("source_zone"))).if_empty("hand");
            format!("{prefix}Move {} matching card(s) from {} to discard.", value, source)
        }
        "PAY_ENERGY" => format!("Pay {} energy.", value),
        "PAY_ENERGY_DYNAMIC" => format!("Pay dynamic energy cost ({}).", value),
        "SET_TAPPED" => "Tap the selected member.".to_string(),
        "TAP_MEMBER" => "Tap a member.".to_string(),
        "ACTIVATE_MEMBER" => "Untap the selected member.".to_string(),
        "SELECT_MEMBER" => format!("Choose {} member(s).", value),
        "SELECT_CARDS" => format!("Choose {} card(s).", value),
        "LOOK_AND_CHOOSE" => {
            let choose_count = attr
                .and_then(|a| a.get("choose_count"))
                .and_then(Value::as_i64)
                .unwrap_or(value);
            let look_count = attr
                .and_then(|a| a.get("look_count"))
                .and_then(Value::as_i64)
                .unwrap_or(value);
            format!("Look at {} card(s) and choose {}.", look_count, choose_count)
        }
        "SELECT_MODE" => format!("Choose one of {} mode(s).", value),
        "SELECT_PLAYER" => "Choose a player.".to_string(),
        "SELECT_LIVE" => "Choose a live card.".to_string(),
        "OPPONENT_CHOOSE" => "Opponent chooses.".to_string(),
        "PLAY_MEMBER_FROM_HAND" => "Play a member from hand.".to_string(),
        "PLAY_MEMBER_FROM_DISCARD" => "Play a member from discard.".to_string(),
        "PLAY_LIVE_FROM_DISCARD" => "Play a live card from discard.".to_string(),
        "ADD_TO_HAND" => format!("Add {} card(s) to hand.", value),
        "ADD_STAGE_ENERGY" => format!("Add {} energy to stage.", value),
        "ENERGY_CHARGE" => format!("Charge {} energy card(s).", value),
        "SET_SCORE" => format!("Set score to {}.", value),
        "REDUCE_SCORE" => format!("Reduce score by {}.", value),
        "SET_HEART_COST" => format!("Set heart cost to {}.", value),
        "SET_HEARTS" => format!("Set hearts to {}.", value),
        "SET_BLADES" => format!("Set blades to {}.", value),
        "ADD_BLADES" => format!("Gain {} blade(s).", value),
        "ADD_HEARTS" => format!("Gain {} heart(s).", value),
        "REDUCE_COST" => format!("Reduce cost by {}.", value),
        "INCREASE_COST" => format!("Increase cost by {}.", value),
        "INCREASE_HEART_COST" => format!("Increase heart cost by {}.", value),
        "REDUCE_HEART_REQ" => format!("Reduce heart requirement by {}.", value),
        "REDUCE_LIVE_SET_LIMIT" => format!("Reduce live set limit by {}.", value),
        "PREVENT_PLAY_TO_SLOT" => "Prevent play to the selected slot.".to_string(),
        "PREVENT_ACTIVATE" => "Prevent activation.".to_string(),
        "PREVENT_BATON_TOUCH" => "Prevent baton touch.".to_string(),
        "PREVENT_SET_TO_SUCCESS_PILE" => {
            "Prevent setting a card to the success pile.".to_string()
        }
        "LOOK_DECK" => format!("Look at {} card(s) from the deck.", value),
        "LOOK_DECK_DYNAMIC" => "Look at a dynamic number of cards from the deck.".to_string(),
        "LOOK_REORDER_DISCARD" => "Look and reorder discard.".to_string(),
        "REVEAL_CARDS" => format!("Reveal {} card(s).", value),
        "REVEAL_UNTIL" => "Reveal cards until the target is found.".to_string(),
        "SEARCH_DECK" => "Search the deck.".to_string(),
        "DRAW_UNTIL" => "Draw until a condition is met.".to_string(),
        "REPEAT_ABILITY" => "Repeat the ability.".to_string(),
        "CALC_SUM_COST" => "Calculate the summed cost.".to_string(),
        "TRANSFORM_COLOR" => "Transform color.".to_string(),
        "TRANSFORM_HEART" => "Transform heart.".to_string(),
        "TRANSFORM_BLADES" => "Transform blades.".to_string(),
        "ACTIVATE_ENERGY" => "Activate energy.".to_string(),
        "MOVE_MEMBER" => "Move a member.".to_string(),
        _ => {
            if let Some(decoded) = frame
                .get("semantic")
                .and_then(|semantic| semantic.get("decoded"))
                .and_then(Value::as_str)
            {
                let text = decoded
                    .split_once('|')
                    .map(|(_, tail)| tail.trim())
                    .unwrap_or(decoded);
                return text.chars().take(240).collect();
            }

            let mut fallback = Map::new();
            fallback.insert("value".to_string(), Value::from(value));
            if let Some(attr) = attr {
                fallback.insert("attr".to_string(), compact_value(attr));
            }
            if let Some(slot) = slot {
                fallback.insert("slot".to_string(), compact_value(slot));
            }
            format!("{} {}", op, Value::Object(fallback))
        }
    }
}

fn summarize_frames(metadata: &Value, frames: &[Value]) -> (String, String) {
    let meaningful: Vec<&Value> = frames
        .iter()
        .filter(|frame| opcode_name(metadata, frame) != "RETURN")
        .collect();
    if meaningful.is_empty() {
        return ("passive".to_string(), "No executable frames.".to_string());
    }

    let roles: Vec<&'static str> = meaningful
        .iter()
        .map(|frame| frame_role(&opcode_name(metadata, frame), is_optional_frame(frame)))
        .collect();
    let has_prompt = roles.iter().any(|role| *role == "prompt");
    let has_control = roles.iter().any(|role| *role == "control");
    let has_optional = meaningful.iter().any(|frame| is_optional_frame(frame));

    let pattern = if has_prompt && has_control {
        "prompted_branching"
    } else if has_prompt {
        "prompted"
    } else if has_control && has_optional {
        "optional_branching"
    } else if has_control {
        "branching"
    } else if has_optional {
        "optional_effect"
    } else {
        "linear"
    }
    .to_string();

    let descriptions: Vec<String> = meaningful
        .iter()
        .map(|frame| describe_frame(metadata, frame))
        .collect();

    let summary = if pattern == "optional_branching" {
        let cost_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "cost")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions[0].clone());
        let effect_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "effect")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions.last().cloned().unwrap_or_default());
        format!(
            "Optional cost: {}. If paid, {}",
            cost_summary.trim_end_matches('.'),
            lower_first(&effect_summary)
        )
    } else if pattern.starts_with("prompted") {
        let prompt_summary = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "prompt")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_else(|| descriptions[0].clone());
        let tail = descriptions
            .iter()
            .zip(roles.iter())
            .find(|(_, role)| **role == "effect")
            .map(|(desc, _)| desc.clone())
            .unwrap_or_default();
        if tail.is_empty() || tail == prompt_summary {
            prompt_summary
        } else {
            format!("{}. Then {}", prompt_summary.trim_end_matches('.'), lower_first(&tail))
        }
    } else if pattern == "branching" {
        descriptions.join(" ")
    } else if pattern == "optional_effect" {
        descriptions[0].clone()
    } else {
        descriptions.join(" ")
    };

    (pattern, summary.trim().to_string())
}

fn lower_first(text: &str) -> String {
    let mut chars = text.chars();
    match chars.next() {
        Some(first) => format!("{}{}", first.to_ascii_lowercase(), chars.collect::<String>()),
        None => String::new(),
    }
}

fn normalize_frame(metadata: &Value, frame: &Value, index: usize) -> AbilityManifestFrame {
    let op = opcode_name(metadata, frame);
    let optional = is_optional_frame(frame);
    let opcode_id = frame.get("opcode_id").and_then(Value::as_i64).map(|id| id as i32);
    let value = frame.get("value").and_then(Value::as_i64).map(|value| value as i32);
    let attr = frame_attr(frame).map(compact_value);
    let slot = frame_slot(frame).map(compact_value);
    let decoded = frame
        .get("semantic")
        .and_then(|semantic| semantic.get("decoded"))
        .and_then(Value::as_str)
        .map(|decoded| decoded.to_string());

    AbilityManifestFrame {
        index,
        opcode_id,
        opcode: op.clone(),
        role: frame_role(&op, optional).to_string(),
        summary: describe_frame(metadata, frame),
        optional,
        negated: is_negated_frame(frame),
        value,
        attr,
        slot,
        decoded,
    }
}

fn normalize_source_text(card: &Value) -> String {
    for key in ["original_text", "ability_text", "raw_text"] {
        if let Some(text) = card.get(key).and_then(Value::as_str) {
            let trimmed = text.trim();
            if !trimmed.is_empty() {
                return trimmed.to_string();
            }
        }
    }
    String::new()
}

fn iter_cards<'a>(cards_payload: &'a Value) -> Vec<(&'a str, &'a Value)> {
    let mut out = Vec::new();
    if let Some(obj) = cards_payload.as_object() {
        for (db_name, db) in obj {
            if !db_name.ends_with("_db") {
                continue;
            }
            if let Some(cards) = db.as_object() {
                for card in cards.values() {
                    if card
                        .get("abilities")
                        .and_then(Value::as_array)
                        .map(|abilities| !abilities.is_empty())
                        .unwrap_or(false)
                    {
                        out.push((db_name.as_str(), card));
                    }
                }
            }
        }
    }
    out
}

trait IfEmpty {
    fn if_empty(self, fallback: &str) -> String;
}

impl IfEmpty for String {
    fn if_empty(self, fallback: &str) -> String {
        if self.is_empty() {
            fallback.to_string()
        } else {
            self
        }
    }
}
