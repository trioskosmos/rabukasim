use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::core::logic::card_db::CardDatabase;
use crate::core::logic::filter::CardFilter;
use crate::core::logic::interpreter::instruction::DecodedSlot;
use crate::core::logic::models::{AbilityFrame, AbilityTraceView};
use serde::Serialize;

const DEFAULT_INPUT_CANDIDATES: &[&str] = &[
    "data/cards_compiled.json",
    "../data/cards_compiled.json",
    "launcher/static_content/data/cards_compiled.json",
];

const DEFAULT_OUTPUT_CANDIDATES: &[&str] = &[
    "data/ability_runtime_entrypoints.json",
    "../data/ability_runtime_entrypoints.json",
];

const COMPILED_CARDS_SOURCE_LABEL: &str = "data/cards_compiled.json";

#[derive(Debug, Serialize)]
struct ExportMetadata {
    generated_unix_seconds: u64,
    hydration_boundary: &'static str,
    extraction_entrypoint: &'static str,
    compiled_cards_source: String,
}

#[derive(Debug, Default, Serialize)]
struct ExportSummary {
    member_card_count: usize,
    live_card_count: usize,
    ability_count: usize,
    abilities_with_resolved_frames: usize,
    source_counts: BTreeMap<String, usize>,
}

#[derive(Debug, Serialize)]
struct SemanticAbilityFrameExport {
    opcode: i32,
    value: i32,
    attr: CardFilter,
    slot: DecodedSlot,
    is_cost: bool,
    params: serde_json::Value,
}

impl From<&AbilityFrame> for SemanticAbilityFrameExport {
    fn from(frame: &AbilityFrame) -> Self {
        Self {
            opcode: frame.opcode,
            value: frame.value,
            attr: frame.filter(),
            slot: frame.dslot(),
            is_cost: frame.is_cost,
            params: frame.params.clone(),
        }
    }
}

#[derive(Debug, Serialize)]
struct HydratedAbilityEntry {
    card_kind: &'static str,
    card_id: i32,
    card_no: String,
    card_name: String,
    ability_index: usize,
    trigger: crate::core::enums::TriggerType,
    resolved_frame_source: String,
    frame_program_present: bool,
    has_resolved_frames: bool,
    raw_text: String,
    pseudocode: String,
    choice_count: u8,
    effect_count: usize,
    condition_count: usize,
    cost_count: usize,
    resolved_frames: Vec<SemanticAbilityFrameExport>,
    trace_view: AbilityTraceView,
}

#[derive(Debug, Serialize)]
struct HydratedAbilityExport {
    metadata: ExportMetadata,
    summary: ExportSummary,
    abilities: Vec<HydratedAbilityEntry>,
}

fn now_unix_seconds() -> u64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|duration| duration.as_secs())
        .unwrap_or(0)
}

fn first_existing_path(candidates: &[&str]) -> Option<PathBuf> {
    candidates.iter().map(PathBuf::from).find(|path| path.exists())
}

fn resolve_output_path() -> PathBuf {
    if let Some(path) = first_existing_path(DEFAULT_OUTPUT_CANDIDATES) {
        return path;
    }

    PathBuf::from(DEFAULT_OUTPUT_CANDIDATES[0])
}

fn load_db() -> Result<(CardDatabase, PathBuf), String> {
    let input_path = first_existing_path(DEFAULT_INPUT_CANDIDATES)
        .ok_or_else(|| "could not locate cards_compiled.json".to_string())?;
    let json = fs::read_to_string(&input_path)
        .map_err(|error| format!("failed reading {}: {}", input_path.display(), error))?;
    let db = CardDatabase::from_json(&json)
        .map_err(|error| format!("failed parsing {}: {}", input_path.display(), error))?;
    Ok((db, input_path))
}

fn push_member_entries(
    entries: &mut Vec<HydratedAbilityEntry>,
    summary: &mut ExportSummary,
    db: &CardDatabase,
) {
    let mut members: Vec<_> = db.members.values().collect();
    members.sort_by(|left, right| {
        left.card_no
            .cmp(&right.card_no)
            .then(left.card_id.cmp(&right.card_id))
    });

    summary.member_card_count = members.len();
    for member in members {
        for (ability_index, ability) in member.abilities.iter().enumerate() {
            let resolved_frame_source = ability.resolved_frame_source().to_string();
            let resolved_frames: Vec<SemanticAbilityFrameExport> = ability
                .resolved_frames()
                .iter()
                .map(SemanticAbilityFrameExport::from)
                .collect();
            let has_resolved_frames = !resolved_frames.is_empty();
            let trace_view = ability.trace_view();

            *summary
                .source_counts
                .entry(resolved_frame_source.clone())
                .or_insert(0) += 1;
            summary.ability_count += 1;
            if has_resolved_frames {
                summary.abilities_with_resolved_frames += 1;
            }

            entries.push(HydratedAbilityEntry {
                card_kind: "member",
                card_id: member.card_id,
                card_no: member.card_no.clone(),
                card_name: member.name.clone(),
                ability_index,
                trigger: ability.trigger,
                resolved_frame_source,
                frame_program_present: ability.frame_program.is_some(),
                has_resolved_frames,
                raw_text: ability.raw_text.clone(),
                pseudocode: ability.pseudocode.clone(),
                choice_count: ability.choice_count,
                effect_count: ability.effects.len(),
                condition_count: ability.conditions.len(),
                cost_count: ability.costs.len(),
                resolved_frames,
                trace_view,
            });
        }
    }
}

fn push_live_entries(
    entries: &mut Vec<HydratedAbilityEntry>,
    summary: &mut ExportSummary,
    db: &CardDatabase,
) {
    let mut lives: Vec<_> = db.lives.values().collect();
    lives.sort_by(|left, right| {
        left.card_no
            .cmp(&right.card_no)
            .then(left.card_id.cmp(&right.card_id))
    });

    summary.live_card_count = lives.len();
    for live in lives {
        for (ability_index, ability) in live.abilities.iter().enumerate() {
            let resolved_frame_source = ability.resolved_frame_source().to_string();
            let resolved_frames: Vec<SemanticAbilityFrameExport> = ability
                .resolved_frames()
                .iter()
                .map(SemanticAbilityFrameExport::from)
                .collect();
            let has_resolved_frames = !resolved_frames.is_empty();
            let trace_view = ability.trace_view();

            *summary
                .source_counts
                .entry(resolved_frame_source.clone())
                .or_insert(0) += 1;
            summary.ability_count += 1;
            if has_resolved_frames {
                summary.abilities_with_resolved_frames += 1;
            }

            entries.push(HydratedAbilityEntry {
                card_kind: "live",
                card_id: live.card_id,
                card_no: live.card_no.clone(),
                card_name: live.name.clone(),
                ability_index,
                trigger: ability.trigger,
                resolved_frame_source,
                frame_program_present: ability.frame_program.is_some(),
                has_resolved_frames,
                raw_text: ability.raw_text.clone(),
                pseudocode: ability.pseudocode.clone(),
                choice_count: ability.choice_count,
                effect_count: ability.effects.len(),
                condition_count: ability.conditions.len(),
                cost_count: ability.costs.len(),
                resolved_frames,
                trace_view,
            });
        }
    }
}

fn build_export(db: &CardDatabase) -> HydratedAbilityExport {
    let mut summary = ExportSummary::default();
    let mut abilities = Vec::new();

    push_member_entries(&mut abilities, &mut summary, db);
    push_live_entries(&mut abilities, &mut summary, db);

    HydratedAbilityExport {
        metadata: ExportMetadata {
            generated_unix_seconds: now_unix_seconds(),
            hydration_boundary: "CardDatabase::attach_sparse_ability_index()",
            extraction_entrypoint: "Ability::resolved_frames() + Ability::trace_view()",
            compiled_cards_source: COMPILED_CARDS_SOURCE_LABEL.to_string(),
        },
        summary,
        abilities,
    }
}

fn write_export(output_path: &Path, export: &HydratedAbilityExport) -> Result<(), String> {
    if let Some(parent) = output_path.parent() {
        fs::create_dir_all(parent)
            .map_err(|error| format!("failed creating {}: {}", parent.display(), error))?;
    }

    let json = serde_json::to_string_pretty(export)
        .map_err(|error| format!("failed serializing export: {}", error))?;
    fs::write(output_path, json)
        .map_err(|error| format!("failed writing {}: {}", output_path.display(), error))
}

pub fn run(output_override: Option<PathBuf>) -> Result<PathBuf, String> {
    let (db, _input_path) = load_db()?;
    let output_path = output_override.unwrap_or_else(resolve_output_path);
    let export = build_export(&db);

    write_export(&output_path, &export)?;

    println!(
        "exported {} hydrated abilities to {}",
        export.summary.ability_count,
        output_path.display()
    );

    Ok(output_path)
}

pub fn run_default() -> Result<PathBuf, String> {
    run(None)
}
