//! Unified Semantic Frame Types
//!
//! Type definitions for the new unified semantic JSON format.
//! These types represent effects with human-readable semantics, no opcodes.

use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// A semantic frame from the unified JSON format
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SemanticFrame {
    #[serde(rename = "type")]
    pub frame_type: String,
    
    #[serde(flatten)]
    pub params: HashMap<String, serde_json::Value>,
    
    /// Original ability text (Japanese)
    #[serde(rename = "_ability_text", default)]
    pub ability_text: String,
    
    /// Original card text (Japanese)
    #[serde(rename = "_original_text", default)]
    pub original_text: String,
}

/// A complete ability with semantic frames
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SemanticAbility {
    pub signature: String,
    pub trigger: String,
    #[serde(rename = "card_no")]
    pub card_no: String,
    #[serde(rename = "card_name")]
    pub card_name: String,
    #[serde(rename = "original_text")]
    pub original_text: String,
    #[serde(rename = "translated_text")]
    pub translated_text: String,
    pub effects: Vec<SemanticFrame>,
}

/// Card data with semantic abilities - LEAN format
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct SemanticCard {
    #[serde(rename = "card_id")]
    pub card_id: String,
    #[serde(rename = "card_no")]
    pub card_no: String,
    #[serde(rename = "original_text")]
    pub original_text: String,
    pub abilities: Vec<SemanticAbility>,
}

/// The unified semantic frames database
#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
pub struct UnifiedSemanticFrames {
    pub schema: String,
    #[serde(rename = "generated_at")]
    pub generated_at: String,
    pub documentation: HashMap<String, String>,
    pub cards: Vec<SemanticCard>,
    pub statistics: Option<HashMap<String, i32>>,
}
