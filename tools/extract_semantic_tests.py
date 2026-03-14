#!/usr/bin/env python3
"""
Extract semantic tests from semantic_truth JSON files and convert to GPU parity tests.

This script reads semantic_truth_v3.json (or other versions) and generates
Rust test code for GPU parity testing.

Semantic Test Format:
{
  "CARD-ID": {
    "id": "CARD-ID",
    "abilities": [
      {
        "trigger": "ONPLAY|ONLIVESTART|ONLIVESUCCESS|ACTIVATED|...",
        "sequence": [
          {
            "text": "Description of effect",
            "deltas": [
              {"tag": "SCORE_DELTA", "value": 5},
              {"tag": "ENERGY_TAP_DELTA", "value": 2}
            ]
          }
        ]
      }
    ]
  }
}

Delta Tags:
- HAND_DISCARD: Cards discarded from hand
- HAND_DELTA: Net change in hand size
- DISCARD_DELTA: Net change in discard pile
- ENERGY_TAP_DELTA: Energy cards tapped
- ENERGY_DELTA: Net change in energy zone
- SCORE_DELTA / LIVE_SCORE_DELTA: Score change
- HEART_DELTA: Heart buff change
- MEMBER_TAP_DELTA: Members tapped
- MEMBER_SACRIFICE: Members removed from stage
- STAGE_DELTA: Members added to stage
- YELL_DELTA: Yell count change
- ACTION_PREVENTION: Action prevention flags changed
- STAGE_ENERGY_DELTA: Stage energy change
"""

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class SemanticDelta:
    tag: str
    value: Any

    @classmethod
    def from_json(cls, data: dict) -> "SemanticDelta":
        return cls(tag=data["tag"], value=data["value"])

    def to_rust_assertion(self, player_idx: int = 0) -> str:
        """Convert delta to Rust assertion code."""
        tag = self.tag
        val = self.value

        # Handle opponent-prefixed tags
        if tag.startswith("OPPONENT_"):
            actual_tag = tag[9:]  # Remove "OPPONENT_" prefix
            return self._generate_assertion(actual_tag, val, player_idx=1, prefix="OPP_")

        return self._generate_assertion(tag, val, player_idx=player_idx)

    def _generate_assertion(self, tag: str, val: Any, player_idx: int = 0, prefix: str = "") -> str:
        """Generate assertion for a specific tag."""
        p = player_idx

        if tag == "HAND_DISCARD":
            return f'assert!(cpu.players[{p}].hand.len() + {val} == initial_{prefix}hand_len, "Expected {val} cards discarded");'
        elif tag == "HAND_DELTA":
            if val >= 0:
                return f'assert!(cpu.players[{p}].hand.len() >= initial_{prefix}hand_len, "Expected hand gain");'
            else:
                return f'assert!(cpu.players[{p}].hand.len() <= initial_{prefix}hand_len, "Expected hand loss");'
        elif tag == "DISCARD_DELTA":
            return f'assert!(cpu.players[{p}].discard.len() as i32 == initial_{prefix}discard_len as i32 + {val}, "Expected discard delta");'
        elif tag == "ENERGY_TAP_DELTA":
            return f'assert!(cpu.players[{p}].tapped_energy_count() >= initial_{prefix}tapped_energy + {val}, "Expected energy tap");'
        elif tag == "ENERGY_DELTA":
            return f'assert!(cpu.players[{p}].energy_zone.len() as i32 == initial_{prefix}energy_len as i32 + {val}, "Expected energy delta");'
        elif tag in ("SCORE_DELTA", "LIVE_SCORE_DELTA"):
            return f'assert!(cpu.players[{p}].score as i32 >= initial_{prefix}score as i32 + {val}, "Expected score delta");'
        elif tag == "HEART_DELTA":
            return f"// HEART_DELTA: {val} (complex assertion needed)"
        elif tag == "MEMBER_TAP_DELTA":
            return f'assert!(cpu.players[{p}].tapped_count() >= initial_{prefix}tapped + {val}, "Expected member tap");'
        elif tag == "MEMBER_SACRIFICE":
            return f'assert!(cpu.players[{p}].stage.iter().filter(|&&c| c >= 0).count() as i32 <= initial_{prefix}stage_count as i32 - {val}, "Expected member sacrifice");'
        elif tag == "STAGE_DELTA":
            return f'assert!(cpu.players[{p}].stage.iter().filter(|&&c| c >= 0).count() as i32 >= initial_{prefix}stage_count as i32 + {val}, "Expected stage gain");'
        elif tag == "YELL_DELTA":
            return f'assert!(cpu.players[{p}].yell_count as i32 == initial_{prefix}yell as i32 + {val}, "Expected yell delta");'
        elif tag == "ACTION_PREVENTION":
            return "// ACTION_PREVENTION flag changed"
        elif tag == "STAGE_ENERGY_DELTA":
            return f"// STAGE_ENERGY_DELTA: {val}"
        else:
            return f"// Unknown delta tag: {tag} = {val}"


@dataclass
class SemanticSegment:
    text: str
    deltas: List[SemanticDelta] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "SemanticSegment":
        deltas = [SemanticDelta.from_json(d) for d in data.get("deltas", [])]
        return cls(text=data.get("text", ""), deltas=deltas)


@dataclass
class SemanticAbility:
    trigger: str
    sequence: List[SemanticSegment] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "SemanticAbility":
        sequence = [SemanticSegment.from_json(s) for s in data.get("sequence", [])]
        return cls(trigger=data.get("trigger", "NONE"), sequence=sequence)


@dataclass
class SemanticCardTruth:
    card_id: str
    abilities: List[SemanticAbility] = field(default_factory=list)

    @classmethod
    def from_json(cls, data: dict) -> "SemanticCardTruth":
        abilities = [SemanticAbility.from_json(a) for a in data.get("abilities", [])]
        return cls(card_id=data.get("id", ""), abilities=abilities)


def load_semantic_truth(path: Path) -> Dict[str, SemanticCardTruth]:
    """Load semantic truth from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return {card_id: SemanticCardTruth.from_json(card_data) for card_id, card_data in data.items()}


def sanitize_identifier(s: str) -> str:
    """Convert string to valid Rust identifier."""
    # Replace non-alphanumeric characters with underscores
    s = re.sub(r"[^a-zA-Z0-9_]", "_", s)
    # Remove leading digits
    s = re.sub(r"^[0-9]+", "", s)
    # Collapse multiple underscores
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def trigger_to_rust(trigger: str) -> str:
    """Convert trigger string to Rust TriggerType."""
    trigger_map = {
        "ONPLAY": "TriggerType::OnPlay",
        "ONLIVESTART": "TriggerType::OnLiveStart",
        "ONLIVESUCCESS": "TriggerType::OnLiveSuccess",
        "ONLEAVES": "TriggerType::OnLeaves",
        "TURNEND": "TriggerType::TurnEnd",
        "ACTIVATED": "TriggerType::Activated",
        "CONSTANT": "TriggerType::Constant",
        "NONE": "TriggerType::None",
    }
    return trigger_map.get(trigger.upper(), "TriggerType::None")


def generate_test_function(card: SemanticCardTruth, ab_idx: int, ability: SemanticAbility) -> str:
    """Generate a Rust test function for a semantic ability."""
    test_name = f"semantic_{sanitize_identifier(card.card_id)}_ab{ab_idx}"

    # Collect all deltas
    all_deltas = []
    for segment in ability.sequence:
        all_deltas.extend(segment.deltas)

    # Generate assertions
    assertions = []
    for delta in all_deltas:
        assertions.append(delta.to_rust_assertion())

    # Determine trigger handling
    trigger_code = generate_trigger_code(ability.trigger)

    rust_trigger = trigger_to_rust(ability.trigger)

    # Check if this is a simple test (no interactions)
    is_simple = len(ability.sequence) <= 1 and not any(
        d.tag in ("HAND_DISCARD", "MEMBER_TAP_DELTA") and d.value > 0 for d in all_deltas
    )

    if not ability.sequence or all(len(s.deltas) == 0 for s in ability.sequence):
        # Empty sequence - skip test
        return f"// SKIPPED: {test_name} - empty ability sequence\n"

    if is_simple:
        return generate_simple_test(test_name, card.card_id, ab_idx, rust_trigger, trigger_code, assertions)
    else:
        return generate_complex_test(test_name, card.card_id, ab_idx, rust_trigger, trigger_code, ability, assertions)


def generate_trigger_code(trigger: str, ab_idx: int = 0) -> str:
    """Generate code to trigger an ability."""
    trigger = trigger.upper()

    if trigger == "ACTIVATED":
        return f"""        // Activate ability
        state.activate_ability(&db, 0, {ab_idx}).ok();
        state.process_trigger_queue(&db);"""

    elif trigger == "ONPLAY":
        return """        // Trigger OnPlay
        state.trigger_event(&db, TriggerType::OnPlay, 0, real_id, 0, 0, -1);
        state.process_trigger_queue(&db);"""

    elif trigger == "ONLIVESTART":
        return """        // Trigger OnLiveStart
        state.phase = Phase::PerformanceP1;
        state.trigger_event(&db, TriggerType::OnLiveStart, 0, real_id, 0, 0, -1);
        state.process_trigger_queue(&db);"""

    elif trigger == "ONLIVESUCCESS":
        return """        // Trigger OnLiveSuccess
        state.phase = Phase::LiveResult;
        state.trigger_event(&db, TriggerType::OnLiveSuccess, 0, real_id, 0, 0, -1);
        state.process_trigger_queue(&db);"""

    elif trigger == "ONLEAVES":
        return """        // Trigger OnLeaves
        state.core.players[0].stage[0] = -1;
        state.trigger_event(&db, TriggerType::OnLeaves, 0, real_id, 0, 0, -1);
        state.process_trigger_queue(&db);"""

    elif trigger == "TURNEND":
        return """        // Trigger TurnEnd
        state.phase = Phase::Terminal;
        state.trigger_event(&db, TriggerType::TurnEnd, 0, real_id, 0, 0, -1);
        state.process_trigger_queue(&db);"""

    else:
        return f"""        // Unknown trigger: {trigger}
        // Manual trigger code needed"""


def generate_simple_test(
    test_name: str, card_id: str, ab_idx: int, rust_trigger: str, trigger_code: str, assertions: List[str]
) -> str:
    """Generate a simple test without interaction handling."""

    assertions_code = "\n".join(f"    {a}" for a in assertions)

    return f'''#[test]
fn {test_name}() -> Result<(), String> {{
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str)
        .expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    let real_id = find_card_id(&db, "{card_id}")
        .ok_or_else(|| format!("Card {{card_id}} not found"))?;

    // Setup oracle environment
    SemanticAssertionEngine::setup_oracle_environment(&mut state, &db, real_id);

    // Capture initial state
    let initial_hand_len = state.core.players[0].hand.len();
    let initial_energy_len = state.core.players[0].energy_zone.len();
    let initial_score = state.core.players[0].score;
    let initial_tapped = state.core.players[0].tapped_count();
    let initial_tapped_energy = state.core.players[0].tapped_energy_count();
    let initial_discard_len = state.core.players[0].discard.len();
    let initial_stage_count = state.core.players[0].stage.iter().filter(|&&c| c >= 0).count();

{trigger_code}

    // Assertions
{assertions_code}

    Ok(())
}}
'''


def generate_complex_test(
    test_name: str,
    card_id: str,
    ab_idx: int,
    rust_trigger: str,
    trigger_code: str,
    ability: SemanticAbility,
    assertions: List[str],
) -> str:
    """Generate a test with interaction handling."""

    assertions_code = "\n".join(f"    {a}" for a in assertions)

    return f'''#[test]
fn {test_name}() -> Result<(), String> {{
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str)
        .expect("Failed to parse CardDatabase");

    let mut state = create_test_state();
    let real_id = find_card_id(&db, "{card_id}")
        .ok_or_else(|| format!("Card {{card_id}} not found"))?;

    // Setup oracle environment
    SemanticAssertionEngine::setup_oracle_environment(&mut state, &db, real_id);

    // Capture initial state
    let initial_hand_len = state.core.players[0].hand.len();
    let initial_energy_len = state.core.players[0].energy_zone.len();
    let initial_score = state.core.players[0].score;
    let initial_tapped = state.core.players[0].tapped_count();
    let initial_tapped_energy = state.core.players[0].tapped_energy_count();
    let initial_discard_len = state.core.players[0].discard.len();
    let initial_stage_count = state.core.players[0].stage.iter().filter(|&&c| c >= 0).count();

{trigger_code}

    // Resolve interactions
    let mut safety = 0;
    while !state.interaction_stack.is_empty() && safety < 10 {{
        // Auto-resolve: pick first valid option
        let action = 8000; // Default action base
        state.step(&db, action).ok();
        safety += 1;
    }}

    // Assertions
{assertions_code}

    Ok(())
}}
'''


def generate_gpu_parity_test(card: SemanticCardTruth, ab_idx: int, ability: SemanticAbility) -> str:
    """Generate a GPU parity test for a semantic ability."""
    test_name = f"gpu_parity_{sanitize_identifier(card.card_id)}_ab{ab_idx}"

    # Collect all deltas
    all_deltas = []
    for segment in ability.sequence:
        all_deltas.extend(segment.deltas)

    if not all_deltas:
        return f"// SKIPPED: {test_name} - no deltas to verify\n"

    # Generate GPU-specific assertions
    gpu_assertions = []
    for delta in all_deltas:
        gpu_assertions.append(generate_gpu_assertion(delta))

    gpu_assertions_code = "\n".join(f"        {a}" for a in gpu_assertions if a)

    trigger_code = generate_trigger_code(ability.trigger, ab_idx)

    return f'''    // {card.card_id} - Ability {ab_idx} ({ability.trigger})
    {{
        let test_name = "{test_name}";
        println!("Running {{}}", test_name);

        let real_id = find_card_id(&db, "{card.card_id}")
            .expect("Card not found");

        let mut state = create_test_state();
        setup_oracle_environment(&mut state, &db, real_id);

{trigger_code}

        // Resolve any interactions
        let mut safety = 0;
        while !state.interaction_stack.is_empty() && safety < 10 {{
            let action = 8000;
            state.step(&db, action).ok();
            safety += 1;
        }}

        // Get final states and verify parity
        let cpu = &state.core;
        let gpu = state.to_gpu(&db);

        // Verify parity
{gpu_assertions_code}
    }}
'''


def generate_gpu_assertion(delta: SemanticDelta) -> str:
    """Generate GPU parity assertion for a delta."""
    tag = delta.tag
    val = delta.value

    if tag.startswith("OPPONENT_"):
        actual_tag = tag[9:]
        return generate_gpu_assertion_for_tag(actual_tag, val, player_idx=1)

    return generate_gpu_assertion_for_tag(tag, val, player_idx=0)


def generate_gpu_assertion_for_tag(tag: str, val: Any, player_idx: int) -> str:
    """Generate GPU assertion for a specific tag."""
    p = player_idx
    pfx = f"player{p}"  # GpuGameState uses player0, player1

    if tag == "SCORE_DELTA" or tag == "LIVE_SCORE_DELTA":
        return f'assert_eq!(gpu.{pfx}.score, cpu.players[{p}].score, "Score parity failed");'
    elif tag == "ENERGY_TAP_DELTA":
        return "// Energy tap: GPU uses tapped_energy_mask"
    elif tag == "HAND_DISCARD":
        return f'assert_eq!(gpu.{pfx}.hand_count as usize, cpu.players[{p}].hand.len(), "Hand count parity");'
    elif tag == "DISCARD_DELTA":
        return f'assert_eq!(gpu.{pfx}.discard_count as usize, cpu.players[{p}].discard.len(), "Discard count parity");'
    elif tag == "MEMBER_TAP_DELTA":
        return "// Member tap: check tapped_mask in GPU"
    elif tag == "HEART_DELTA":
        return "// Heart delta: check heart_req_reduction in GPU"
    elif tag == "STAGE_DELTA":
        return "// Stage delta: check stage slots in GPU"
    else:
        return f"// {tag}: {val} (GPU assertion needed)"


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Extract semantic tests to GPU parity tests")
    parser.add_argument(
        "--input", "-i", default="../reports/semantic_truth_v3.json", help="Input semantic truth JSON file"
    )
    parser.add_argument(
        "--output", "-o", default="../engine_rust_src/tests/generated_semantic_parity_tests.rs", help="Output Rust file"
    )
    parser.add_argument(
        "--format", "-f", choices=["unit"], default="unit", help="Output format"
    )
    parser.add_argument("--limit", "-l", type=int, default=0, help="Limit number of tests to generate (0 = all)")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    print(f"Loading semantic truth from {input_path}...")
    cards = load_semantic_truth(input_path)
    print(f"Loaded {len(cards)} cards")

    # Generate tests
    output = generate_unit_tests(cards, args.limit)

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Generated tests written to {output_path}")


def generate_unit_tests(cards: Dict[str, SemanticCardTruth], limit: int = 0) -> str:
    """Generate unit test functions."""
    header = """//! Auto-generated semantic tests
//! Generated by tools/extract_semantic_tests.py

use engine_rust::core::logic::{GameState, CardDatabase, Phase};
use engine_rust::core::models::TriggerType;
use engine_rust::test_helpers::create_test_state;
use engine_rust::semantic_assertions::{SemanticAssertionEngine, SemanticDelta};

fn find_card_id(db: &CardDatabase, card_no: &str) -> Option<i32> {
    for (&id, m) in &db.members {
        if m.card_no == card_no { return Some(id); }
    }
    for (&id, l) in &db.lives {
        if l.card_no == card_no { return Some(id); }
    }
    None
}

"""

    test_functions = []
    count = 0

    for card_id, card in cards.items():
        for ab_idx, ability in enumerate(card.abilities):
            if limit > 0 and count >= limit:
                break

            test_fn = generate_test_function(card, ab_idx, ability)
            test_functions.append(test_fn)
            count += 1

        if limit > 0 and count >= limit:
            break

    return header + "\n".join(test_functions)


def generate_gpu_parity_tests(cards: Dict[str, SemanticCardTruth], limit: int = 0) -> str:
    """Generate GPU parity test scenarios."""
    header = """//! Auto-generated GPU parity tests from semantic truth
//! Generated by tools/extract_semantic_tests.py
//!
//! Run with: cargo test --test generated_semantic_parity_tests

use engine_rust::core::logic::{GameState, CardDatabase, Phase};
use engine_rust::core::models::TriggerType;
use engine_rust::test_helpers::create_test_state;

fn find_card_id(db: &CardDatabase, card_no: &str) -> Option<i32> {
    for (&id, m) in &db.members {
        if m.card_no == card_no { return Some(id); }
    }
    for (&id, l) in &db.lives {
        if l.card_no == card_no { return Some(id); }
    }
    None
}

/// Setup oracle environment for testing (copied from semantic_assertions.rs)
fn setup_oracle_environment(state: &mut GameState, db: &CardDatabase, real_id: i32) {
    // Find same-group members for stage neighbors
    let card_group = db.get_member(real_id)
        .and_then(|m| m.groups.first().copied())
        .unwrap_or(1);
    let same_group_members: Vec<i32> = db.members.iter()
        .filter(|(&id, m)| id != real_id && m.groups.contains(&card_group) && m.cost <= 6)
        .map(|(&id, _)| id)
        .take(10)
        .collect();

    // Real energy cards
    let energy_ids: Vec<i32> = db.energy_db.keys().copied().take(20).collect();
    let energy_fill: Vec<i32> = if energy_ids.is_empty() { vec![5001; 20] } else { energy_ids.clone() };

    // Real live cards
    let real_lives: Vec<i32> = db.lives.keys().copied().take(6).collect();
    let live_fill: Vec<i32> = if real_lives.is_empty() { vec![15000, 15001, 15002] } else { real_lives[..3.min(real_lives.len())].to_vec() };

    // Real member cards for hand/deck/discard
    let other_members: Vec<i32> = db.members.iter()
        .filter(|(&id, _)| id != real_id)
        .map(|(&id, _)| id)
        .take(20)
        .collect();

    // PLAYER 0 (card under test)
    state.core.players[0].energy_zone.extend(energy_fill.iter().cloned());

    for &id in same_group_members.iter().take(5) {
        state.core.players[0].hand.push(id);
    }
    for &id in other_members.iter().skip(5).take(6) {
        state.core.players[0].hand.push(id);
    }

    for &id in other_members.iter().take(10) {
        state.core.players[0].deck.push(id);
    }
    for &id in real_lives.iter() {
        state.core.players[0].deck.push(id);
    }

    for &id in same_group_members.iter().take(5) {
        state.core.players[0].discard.push(id);
    }

    state.core.players[0].success_lives.extend(live_fill.iter().cloned());
    state.core.players[0].live_zone[0] = real_lives.first().copied().unwrap_or(5003);

    // Stage (card under test at center)
    state.core.players[0].stage[0] = real_id;
    state.core.players[0].stage[1] = same_group_members.first().copied().unwrap_or(5000);
    state.core.players[0].stage[2] = same_group_members.get(1).copied().unwrap_or(5000);

    state.core.players[0].score = 99;

    // PLAYER 1 (opponent)
    let opp_members: Vec<i32> = db.members.iter()
        .filter(|(&id, _)| !same_group_members.contains(&id) && id != real_id)
        .map(|(&id, _)| id)
        .take(30)
        .collect();

    state.core.players[1].energy_zone.extend(energy_ids.iter().take(10).cloned());
    state.core.players[1].hand.extend(opp_members.iter().take(5).cloned());
    state.core.players[1].stage[0] = opp_members.get(5).copied().unwrap_or(5002);
    state.core.players[1].stage[1] = opp_members.get(6).copied().unwrap_or(5002);
    state.core.players[1].stage[2] = opp_members.get(7).copied().unwrap_or(5002);

    state.phase = Phase::Main;
    state.turn = 5;
}

#[test]
fn semantic_gpu_parity_tests() {
    let compiled_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let db = CardDatabase::from_json(&compiled_str)
        .expect("Failed to parse CardDatabase");

"""

    test_cases = []
    count = 0

    for card_id, card in cards.items():
        for ab_idx, ability in enumerate(card.abilities):
            if limit > 0 and count >= limit:
                break

            test_case = generate_gpu_parity_test(card, ab_idx, ability)
            test_cases.append(test_case)
            count += 1

        if limit > 0 and count >= limit:
            break

    footer = """
}
"""

    return header + "\n".join(test_cases) + footer


if __name__ == "__main__":
    main()
