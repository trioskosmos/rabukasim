use crate::core::logic::*;
use std::collections::HashMap;
use std::io::Write;

fn load_real_db() -> CardDatabase {
    let json_str = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json at ../data/");
    CardDatabase::from_json(&json_str).expect("Failed to parse CardDatabase")
}

use crate::test_helpers::ZoneSnapshot;


#[derive(Debug)]
struct StateDelta {
    hand: i32,
    deck: i32,
    discard: i32,
    energy: i32,
    tapped: i32,
    looked: i32,
    stage_changed: bool,
    live_changed: bool,
    suspended: bool, // Did engine pause for interaction?
}

impl StateDelta {
    fn compute(before: &ZoneSnapshot, after: &ZoneSnapshot, suspended: bool) -> Self {
        Self {
            hand: after.hand_len as i32 - before.hand_len as i32,
            deck: after.deck_len as i32 - before.deck_len as i32,
            discard: after.discard_len as i32 - before.discard_len as i32,
            energy: after.energy_len as i32 - before.energy_len as i32,
            tapped: after.tapped_energy_count as i32 - before.tapped_energy_count as i32,
            looked: after.looked_cards_len as i32 - before.looked_cards_len as i32,
            stage_changed: before.stage != after.stage,
            live_changed: before.live_zone != after.live_zone,
            suspended,
        }
    }

    fn is_noop(&self) -> bool {
        self.hand == 0 && self.deck == 0 && self.discard == 0 &&
        self.energy == 0 && self.tapped == 0 && self.looked == 0 &&
        !self.stage_changed && !self.live_changed && !self.suspended
    }

    fn to_string(&self) -> String {
        let mut parts = Vec::new();
        if self.hand != 0 { parts.push(format!("Hand{:+}", self.hand)); }
        if self.deck != 0 { parts.push(format!("Deck{:+}", self.deck)); }
        if self.discard != 0 { parts.push(format!("Discard{:+}", self.discard)); }
        if self.energy != 0 { parts.push(format!("Energy{:+}", self.energy)); }
        if self.tapped != 0 { parts.push(format!("Tapped{:+}", self.tapped)); }
        if self.looked != 0 { parts.push(format!("Looked{:+}", self.looked)); }
        if self.stage_changed { parts.push("StageChanged".to_string()); }
        if self.live_changed { parts.push("LiveChanged".to_string()); }
        if self.suspended { parts.push("⏸Suspended".to_string()); }
        if parts.is_empty() { "NO CHANGE".to_string() } else { parts.join(", ") }
    }
}

/// Heuristic: check if the Japanese text implies something the delta didn't produce
fn flag_mismatches(jp_text: &str, delta: &StateDelta) -> Vec<String> {
    let mut flags = Vec::new();

    // Draw indicators
    if (jp_text.contains("ドロー") || jp_text.contains("引く") || jp_text.contains("引き"))
        && delta.hand <= 0 && !delta.suspended {
        flags.push("⚠️ JP says DRAW but hand didn't increase".to_string());
    }

    // Discard indicators
    if (jp_text.contains("控え室に置") || jp_text.contains("控え室へ"))
        && delta.discard <= 0 && !delta.suspended {
        flags.push("⚠️ JP says DISCARD but discard didn't increase".to_string());
    }

    // Recovery indicators
    if (jp_text.contains("回復") || jp_text.contains("控え室から"))
        && delta.discard >= 0 && !delta.suspended {
        flags.push("⚠️ JP says RECOVER but nothing left discard".to_string());
    }

    // Look/Reveal indicators
    if (jp_text.contains("公開") || jp_text.contains("見る") || jp_text.contains("めくる"))
        && delta.looked <= 0 && !delta.suspended {
        flags.push("⚠️ JP says LOOK/REVEAL but no looked cards".to_string());
    }

    // Tap/Rest indicators
    if (jp_text.contains("レスト") || jp_text.contains("横にする"))
        && !delta.stage_changed && delta.tapped <= 0 && !delta.suspended {
        flags.push("⚠️ JP says REST/TAP but no tap change".to_string());
    }

    // Energy indicators
    if jp_text.contains("エネルギー") && delta.energy == 0 && delta.tapped == 0 && !delta.suspended {
        flags.push("⚠️ JP mentions ENERGY but no energy change".to_string());
    }

    // Heart/Blade buff indicators
    if (jp_text.contains("ブレード") || jp_text.contains("ハート"))
        && delta.is_noop() && !delta.suspended {
        // This is OK for Constant abilities (buffs) — they modify stats not zones
        // Only flag for non-Constant triggers
    }

    // No-op detection (ability with text but does nothing)
    if delta.is_noop() && !jp_text.is_empty() {
        flags.push("ℹ️ Ability had NO observable effect (may be buff/condition only)".to_string());
    }

    flags
}

use std::panic;

#[test]
fn test_state_delta_verification() {
    let db = load_real_db();

    // Group abilities by bytecode signature to avoid testing duplicates
    let mut seen_signatures: HashMap<Vec<i32>, (String, String, String)> = HashMap::new(); // sig -> (card_no, jp_text, pseudocode)
    let mut all_entries: Vec<(String, String, String, Vec<i32>, TriggerType, i32)> = Vec::new(); // (card_no, jp_text, pseudo, bytecode, trigger, card_id)

    let mut card_ids: Vec<i32> = db.members.keys().cloned().collect();
    card_ids.sort();

    for card_id in &card_ids {
        if let Some(card) = db.members.get(card_id) {
            for ability in &card.abilities {
                if ability.bytecode.is_empty() { continue; }
                let sig = ability.bytecode.clone();
                if seen_signatures.contains_key(&sig) { continue; }

                let jp_text = ability.raw_text.clone();
                let pseudo = ability.pseudocode.clone();
                seen_signatures.insert(sig.clone(), (card.card_no.clone(), jp_text.clone(), pseudo.clone()));
                all_entries.push((card.card_no.clone(), jp_text, pseudo, sig, ability.trigger, *card_id));
            }
        }
    }

    // Now execute each unique ability and capture deltas
    let mut report_lines: Vec<String> = Vec::new();
    report_lines.push("# Ability State Delta Verification Report".to_string());
    report_lines.push(format!("Total unique ability signatures: {}\n", all_entries.len()));
    report_lines.push("| # | Card | Trigger | JP Text | Pseudocode | State Delta | Flags |".to_string());
    report_lines.push("|---|------|---------|---------|------------|-------------|-------|".to_string());

    let mut flagged_count = 0;
    let mut noop_count = 0;
    let mut suspend_count = 0;
    let mut crash_count = 0;
    let mut pass_count = 0;
    let mut crashed_cards: Vec<String> = Vec::new();

    for (idx, (card_no, jp_text, pseudo, bytecode, trigger, card_id)) in all_entries.iter().enumerate() {
        // Wrap execution in catch_unwind for fault isolation
        let bc_clone = bytecode.clone();
        let trigger_clone = *trigger;
        let card_id_clone = *card_id;

        let result = panic::catch_unwind(panic::AssertUnwindSafe(|| {
            // Setup controlled state
            let mut state = GameState::default();
            state.ui.silent = true;
            state.phase = Phase::Main;

            // Place the card on stage so activated abilities work
            state.core.players[0].stage[0] = card_id_clone;
            // Give controlled resources
            state.core.players[0].hand = (100..106).collect(); // 6 cards in hand
            state.core.players[0].deck = (200..215).collect(); // 15 cards in deck
            state.core.players[0].discard = (300..305).collect(); // 5 in discard
            state.core.players[0].energy_zone = vec![40000i32; 8].into(); // 8 energy cards
            state.core.players[0].tapped_energy_mask = 0b00001111; // 4 energy tapped
            // Put a live card in live zone and one in discard for recovery tests
            state.core.players[0].live_zone[0] = 15001;
            state.core.players[0].discard.push(15002); // Live in discard for O_RECOVER_LIVE

            let ctx = AbilityContext {
                player_id: 0,
                source_card_id: card_id_clone,
                area_idx: 0,
                ability_index: 0,
                trigger_type: trigger_clone,
                ..Default::default()
            };

            let before = ZoneSnapshot::capture(&state.core.players[0], &state);

            // Execute
            let bytecode_slice: &[i32] = &bc_clone;
            state.resolve_bytecode_slice(&db, bytecode_slice, &ctx);

            let suspended = state.phase == Phase::Response || !state.interaction_stack.is_empty();
            let after = ZoneSnapshot::capture(&state.core.players[0], &state);
            let delta = StateDelta::compute(&before, &after, suspended);

            (delta, suspended)
        }));

        let trigger_str = match trigger {
            TriggerType::OnPlay => "登場",
            TriggerType::Activated => "起動",
            TriggerType::OnLiveStart => "開始",
            TriggerType::OnLiveSuccess => "成功",
            TriggerType::TurnStart => "ターン開始",
            TriggerType::TurnEnd => "ターン終",
            TriggerType::Constant => "常時",
            TriggerType::OnLeaves => "退場",
            TriggerType::OnReveal => "公開",
            _ => "?",
        };

        let jp_short = if jp_text.len() > 60 { format!("{}...", &jp_text[..jp_text.char_indices().nth(30).map(|(i,_)|i).unwrap_or(60)]) } else { jp_text.clone() };
        let pseudo_short = if pseudo.len() > 40 { format!("{}...", &pseudo[..pseudo.char_indices().nth(20).map(|(i,_)|i).unwrap_or(40)]) } else { pseudo.clone() };

        match result {
            Ok((delta, suspended)) => {
                let flags = flag_mismatches(jp_text, &delta);
                if delta.is_noop() { noop_count += 1; }
                if suspended { suspend_count += 1; }
                if !flags.is_empty() { flagged_count += 1; }
                pass_count += 1;

                let flags_str = if flags.is_empty() { "✅".to_string() } else { flags.join(" ") };
                report_lines.push(format!("| {} | {} | {} | {} | {} | {} | {} |",
                    idx + 1, card_no, trigger_str, jp_short, pseudo_short, delta.to_string(), flags_str));
            },
            Err(panic_info) => {
                crash_count += 1;
                let panic_msg = panic_info.downcast_ref::<String>()
                    .map(|s| s.as_str())
                    .or_else(|| panic_info.downcast_ref::<&str>().copied())
                    .unwrap_or("unknown panic");
                let panic_short = if panic_msg.len() > 80 { &panic_msg[..80] } else { panic_msg };
                crashed_cards.push(format!("{}: {}", card_no, panic_short));
                report_lines.push(format!("| {} | {} | {} | {} | {} | 💥 CRASH | {} |",
                    idx + 1, card_no, trigger_str, jp_short, pseudo_short, panic_short));
            }
        }
    }

    // Summary
    report_lines.insert(2, format!(
        "- **Pass**: {} | **Crashed**: {} | **Flagged**: {} | **No-ops**: {} | **Suspended**: {}\n",
        pass_count, crash_count, flagged_count, noop_count, suspend_count
    ));

    // Write report
    let report = report_lines.join("\n");
    let mut file = std::fs::File::create("../reports/state_delta_verification.md").expect("Failed to create report");
    file.write_all(report.as_bytes()).expect("Failed to write report");

    // Also write crash list if any
    if !crashed_cards.is_empty() {
        let crash_report = crashed_cards.join("\n");
        let mut f = std::fs::File::create("../reports/crashed_abilities.txt").expect("Failed to create crash report");
        f.write_all(crash_report.as_bytes()).expect("Failed to write crash report");
    }

    println!("\n=== CRASH TRIAGE RESULTS ===");
    println!("Unique signatures tested: {}", all_entries.len());
    println!("Pass: {}", pass_count);
    println!("Crashed: {}", crash_count);
    println!("Flagged mismatches: {}", flagged_count);
    println!("No-ops (buff/condition only): {}", noop_count);
    println!("Suspended (needs interaction): {}", suspend_count);
    println!("Report written to: reports/state_delta_verification.md");
    if crash_count > 0 {
        println!("\n💥 CRASHED ABILITIES:");
        for c in &crashed_cards { println!("  {}", c); }
    }

    // The test passes as long as more than 90% of abilities don't crash
    let crash_rate = crash_count as f64 / all_entries.len() as f64;
    assert!(crash_rate < 0.10, "Crash rate {:.1}% exceeds 10% threshold ({} of {} crashed)",
        crash_rate * 100.0, crash_count, all_entries.len());
}
