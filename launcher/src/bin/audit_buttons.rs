use serde_json::{json, Value};
use engine_rust::core::logic::*;
use engine_rust::core::logic::{GameState, CardDatabase, PendingInteraction};
// use engine_rust::core::enums::*;
use loveca_launcher::serialization::get_action_desc_rich;
use std::fs::File;
use std::io::Write;
use std::collections::HashMap;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("Starting refined ability audit...");

    // 1. Load DB
    let db_path = "static_content/data/cards_compiled.json";
    let db_json = std::fs::read_to_string(db_path).expect("Failed to read DB");
    let card_db = CardDatabase::from_json(&db_json).expect("Failed to parse DB");

    let mut output = Vec::new();
    let mut unique_labels: HashMap<String, Value> = HashMap::new();

    // 2. Member Ability Audit
    println!("Auditing member abilities...");
    let mut member_audit = Vec::new();
    let mut sorted_members: Vec<_> = card_db.members.values().collect();
    sorted_members.sort_by_key(|m| &m.card_no);

    for member in sorted_members {
        let cid = member.card_id;
        let mut card_entries = Vec::new();

        // 2a. Audit ACTIVATED labels (Member on stage)
        let mut gs_ab = GameState::default();
        gs_ab.phase = Phase::Main;
        gs_ab.players[0].stage = [cid as i32, -1, -1];
        
        for (ab_idx, _) in member.abilities.iter().enumerate() {
            let aid = ACTION_BASE_STAGE + (0 * 10) + ab_idx as i32; 
            let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_ab, &card_db, 0, "jp");
            
            if t_str == "ABILITY" || t_str == "ACTIVATE" {
                let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_ab, &card_db, 0, "en");
                let entry = json!({ 
                    "context": format!("On Stage (AbIdx {})", ab_idx), 
                    "id": aid, 
                    "type": t_str.clone(), 
                    "jp": { "label": l_jp.clone(), "desc": d_jp.clone() }, 
                    "en": { "label": l_en.clone(), "desc": d_en.clone() } 
                });
                card_entries.push(entry.clone());
                unique_labels.entry(l_jp.clone()).or_insert(json!({
                    "jp_label": l_jp, "jp_desc": d_jp,
                    "en_label": l_en, "en_desc": d_en,
                    "type": t_str,
                    "example_card": format!("{} ({})", member.name, member.card_no)
                }));
            }
        }

        // 2b. Audit DISCARD labels
        let mut gs_ds = GameState::default();
        gs_ds.phase = Phase::Main;
        gs_ds.players[0].discard.push(cid);
        for (ab_idx, _) in member.abilities.iter().enumerate() {
            let aid = ACTION_BASE_DISCARD_ACTIVATE + (0 * 10) + ab_idx as i32;
            let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_ds, &card_db, 0, "jp");
            
            if t_str == "ABILITY" || t_str == "ACTIVATE" {
                let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_ds, &card_db, 0, "en");
                let entry = json!({ 
                    "context": format!("In Discard (AbIdx {})", ab_idx), 
                    "id": aid, 
                    "type": t_str.clone(), 
                    "jp": { "label": l_jp.clone(), "desc": d_jp.clone() }, 
                    "en": { "label": l_en.clone(), "desc": d_en.clone() } 
                });
                card_entries.push(entry.clone());
                unique_labels.entry(l_jp.clone()).or_insert(json!({
                    "jp_label": l_jp, "jp_desc": d_jp,
                    "en_label": l_en, "en_desc": d_en,
                    "type": t_str,
                    "example_card": format!("{} ({}) [Discard]", member.name, member.card_no)
                }));
            }
        }

        if !card_entries.is_empty() {
            member_audit.push(json!({
                "card_no": member.card_no,
                "name": member.name,
                "entries": card_entries
            }));
        }
    }
    output.push(json!({ "scenario": "Member Ability Audit", "data": member_audit }));

    // 3. Live Ability Audit
    println!("Auditing live abilities...");
    let mut live_audit = Vec::new();
    let mut sorted_lives: Vec<_> = card_db.lives.values().collect();
    sorted_lives.sort_by_key(|l| &l.card_no);

    for live in sorted_lives {
        let cid = live.card_id;
        let mut card_entries = Vec::new();

        let mut gs_ab = GameState::default();
        gs_ab.phase = Phase::Main;
        gs_ab.players[0].stage = [cid as i32, -1, -1];
        
        for (ab_idx, _) in live.abilities.iter().enumerate() {
            let aid = ACTION_BASE_STAGE + (0 * 10) + ab_idx as i32;
            let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_ab, &card_db, 0, "jp");
            
            if t_str == "ABILITY" || t_str == "ACTIVATE" {
                let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_ab, &card_db, 0, "en");
                let entry = json!({ 
                    "context": format!("Live Ability (AbIdx {})", ab_idx), 
                    "id": aid, 
                    "type": t_str.clone(), 
                    "jp": { "label": l_jp.clone(), "desc": d_jp.clone() }, 
                    "en": { "label": l_en.clone(), "desc": d_en.clone() } 
                });
                card_entries.push(entry.clone());
                unique_labels.entry(l_jp.clone()).or_insert(json!({
                    "jp_label": l_jp, "jp_desc": d_jp,
                    "en_label": l_en, "en_desc": d_en,
                    "type": t_str,
                    "example_card": format!("{} ({}) [Live]", live.name, live.card_no)
                }));
            }
        }

        if !card_entries.is_empty() {
            live_audit.push(json!({
                "card_no": live.card_no,
                "name": live.name,
                "entries": card_entries
            }));
        }
    }
    output.push(json!({ "scenario": "Live Ability Audit", "data": live_audit }));

    // 4. Selection Action Audit (Simulation)
    println!("Auditing selection actions...");
    let mut selection_audit = Vec::new();
    
    // Test Case: O_LOOK_AND_CHOOSE with mocked looked_cards
    let mut gs_sel = GameState::default();
    gs_sel.phase = Phase::Response;
    gs_sel.interaction_stack.push(PendingInteraction {
        effect_opcode: O_LOOK_AND_CHOOSE,
        ..Default::default()
    });
    gs_sel.players[0].looked_cards = vec![1179, 10].into(); // Some random IDs (Rank 19 and something else)
    
    let mut entries = Vec::new();
    for choice_idx in 0..2 {
        let aid = ACTION_BASE_CHOICE + choice_idx as i32; // Action::SelectChoice { choice_idx }
        let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_sel, &card_db, 0, "jp");
        let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_sel, &card_db, 0, "en");
        let entry = json!({
            "context": format!("SelectChoice (Looked Card Index {})", choice_idx),
            "id": aid,
            "type": t_str.clone(),
            "jp": { "label": l_jp.clone(), "desc": d_jp.clone() },
            "en": { "label": l_en.clone(), "desc": d_en.clone() }
        });
        entries.push(entry.clone());
        unique_labels.entry(l_jp.clone()).or_insert(json!({
            "jp_label": l_jp, "jp_desc": d_jp,
            "en_label": l_en, "en_desc": d_en,
            "type": t_str,
            "example_card": "[Selection Simulation]"
        }));
    }
    selection_audit.push(json!({ "name": "LOOK_AND_CHOOSE Simulation", "entries": entries }));

    // Test Case: O_RECOV_L (Hand Selection)
    let mut gs_rec = GameState::default();
    gs_rec.phase = Phase::Response;
    gs_rec.interaction_stack.push(PendingInteraction {
        effect_opcode: O_RECOVER_LIVE,
        ..Default::default()
    });
    gs_rec.players[0].hand = vec![1179, 500].into();
    
    let mut entries = Vec::new();
    for hand_idx in 0..2 {
        let aid = ACTION_BASE_HAND_SELECT + hand_idx as i32; // Action::SelectHand { hand_idx }
        let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_rec, &card_db, 0, "jp");
        let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_rec, &card_db, 0, "en");
        let entry = json!({
            "context": format!("SelectHand (Recover Live) Index {}", hand_idx),
            "id": aid,
            "type": t_str.clone(),
            "jp": { "label": l_jp.clone(), "desc": d_jp.clone() },
            "en": { "label": l_en.clone(), "desc": d_en.clone() }
        });
        entries.push(entry.clone());
        unique_labels.entry(l_jp.clone()).or_insert(json!({
            "jp_label": l_jp, "jp_desc": d_jp,
            "en_label": l_en, "en_desc": d_en,
            "type": t_str,
            "example_card": "[Hand Selection Simulation]"
        }));
    }
    selection_audit.push(json!({ "name": "RECOV_L Hand Selection Simulation", "entries": entries }));

    // Test Case: O_SELECT_MEMBER (Stage Selection)
    let mut gs_sm = GameState::default();
    gs_sm.phase = Phase::Response;
    gs_sm.interaction_stack.push(PendingInteraction {
        effect_opcode: O_SELECT_MEMBER,
        ..Default::default()
    });
    gs_sm.players[0].stage = [1179, 10, -1];
    
    let mut entries = Vec::new();
    for slot_idx in 0..2 {
        let aid = ACTION_BASE_CHOICE + slot_idx as i32; // Action::SelectChoice { choice_idx }
        let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_sm, &card_db, 0, "jp");
        let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_sm, &card_db, 0, "en");
        let entry = json!({
            "context": format!("SelectChoice (Select Member Slot {})", slot_idx),
            "id": aid,
            "type": t_str.clone(),
            "jp": { "label": l_jp.clone(), "desc": d_jp.clone() },
            "en": { "label": l_en.clone(), "desc": d_en.clone() }
        });
        entries.push(entry.clone());
        unique_labels.entry(l_jp.clone()).or_insert(json!({
            "jp_label": l_jp, "jp_desc": d_jp,
            "en_label": l_en, "en_desc": d_en,
            "type": t_str,
            "example_card": "[Stage Selection Simulation]"
        }));
    }
    selection_audit.push(json!({ "name": "SELECT_MEMBER Simulation", "entries": entries }));

    // Test Case: O_TAP_O (Opponent Stage Selection)
    let mut gs_to = GameState::default();
    gs_to.phase = Phase::Response;
    gs_to.interaction_stack.push(PendingInteraction {
        effect_opcode: O_TAP_OPPONENT,
        ..Default::default()
    });
    gs_to.players[1].stage = [500, -1, -1]; // Opponent has one card on left
    
    let mut entries = Vec::new();
    for slot_idx in 0..1 {
        let aid = ACTION_BASE_CHOICE + slot_idx as i32; // Action::SelectChoice { choice_idx }
        let (l_jp, d_jp, t_str, _, _) = get_action_desc_rich(aid, &gs_to, &card_db, 0, "jp");
        let (l_en, d_en, _, _, _) = get_action_desc_rich(aid, &gs_to, &card_db, 0, "en");
        let entry = json!({
            "context": format!("SelectChoice (Tap Opponent Slot {})", slot_idx),
            "id": aid,
            "type": t_str.clone(),
            "jp": { "label": l_jp.clone(), "desc": d_jp.clone() },
            "en": { "label": l_en.clone(), "desc": d_en.clone() }
        });
        entries.push(entry.clone());
        unique_labels.entry(l_jp.clone()).or_insert(json!({
            "jp_label": l_jp, "jp_desc": d_jp,
            "en_label": l_en, "en_desc": d_en,
            "type": t_str,
            "example_card": "[Opponent Selection Simulation]"
        }));
    }
    selection_audit.push(json!({ "name": "TAP_O Simulation", "entries": entries }));

    output.push(json!({ "scenario": "Selection Action Audit", "data": selection_audit }));

    // Write exhaustive report
    let json_out = serde_json::to_string_pretty(&output)?;
    let mut file = File::create("action_buttons_exhaustive.json")?;
    file.write_all(json_out.as_bytes())?;
    println!("Successfully generated action_buttons_exhaustive.json");

    // Write unique summary
    let mut unique_list: Vec<_> = unique_labels.into_values().collect();
    // Sort by label for easier reading
    unique_list.sort_by_key(|v| v.get("jp_label").and_then(|s| s.as_str()).unwrap_or("").to_string());
    
    let unique_out = serde_json::to_string_pretty(&unique_list)?;
    let mut file_u = File::create("action_buttons_unique.json")?;
    file_u.write_all(unique_out.as_bytes())?;
    println!("Successfully generated action_buttons_unique.json");
    Ok(())
}
