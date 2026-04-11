#[allow(unused_imports)]
use engine_rust::core::logic::{ActionFactory, CardDatabase, GameState, PendingInteraction, Phase};
use std::fs;
use std::path::Path;

#[test]
fn test_q103_dynamic_condition_resolution() {
    let json_content = std::fs::read_to_string("../data/cards_compiled.json")
        .expect("Failed to read cards_compiled.json");
    let mut _db = CardDatabase::from_json(&json_content).unwrap();
}

/// Anti-drift test: Verify that legacy filter shift constants are NOT used
/// in engine source files outside of generated_constants.rs and generated_layout.rs.
/// All filter constants should use their canonical names (e.g., FILTER_GROUP_ID_SHIFT).
#[test]
fn test_filter_constant_usage_canonical_names_only() {
    let src_dir = "../src";
    let forbidden_patterns = vec![
        "FILTER_GROUP_SHIFT",   // Should be FILTER_GROUP_ID_SHIFT
        "FILTER_UNIT_SHIFT",    // Should be FILTER_UNIT_ID_SHIFT
        "FILTER_SPECIAL_SHIFT", // Should be FILTER_SPECIAL_ID_SHIFT
        "FILTER_COST_SHIFT",    // Should be FILTER_VALUE_THRESHOLD_SHIFT
    ];

    let generated_files = vec!["generated_constants.rs", "generated_layout.rs"];

    let mut violations = Vec::new();

    fn scan_directory(
        dir: &Path,
        forbidden_patterns: &[&str],
        generated_files: &[&str],
        violations: &mut Vec<String>,
    ) {
        if let Ok(entries) = fs::read_dir(dir) {
            for entry in entries.flatten() {
                let path = entry.path();
                if path.is_dir() {
                    scan_directory(&path, forbidden_patterns, generated_files, violations);
                } else if path.extension().map_or(false, |ext| ext == "rs") {
                    // Skip generated files
                    let filename = path.file_name().unwrap().to_string_lossy();
                    if generated_files.iter().any(|&gf| filename.contains(gf)) {
                        continue;
                    }

                    if let Ok(content) = fs::read_to_string(&path) {
                        for (line_num, line) in content.lines().enumerate() {
                            for pattern in forbidden_patterns {
                                if line.contains(pattern) {
                                    violations.push(format!(
                                        "{}:{}: Found forbidden pattern '{}' (use canonical name instead)",
                                        path.display(),
                                        line_num + 1,
                                        pattern
                                    ));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    scan_directory(
        Path::new(src_dir),
        &forbidden_patterns,
        &generated_files,
        &mut violations,
    );

    if !violations.is_empty() {
        panic!(
            "Anti-drift test FAILED: Found {} legacy filter constant usage(s):\n{}",
            violations.len(),
            violations.join("\n")
        );
    }
}

#[test]
fn test_ability_frame_source_has_explicit_add_hearts_metadata() {
    let json_content = std::fs::read_to_string("../data/ability_frame_source.json")
        .expect("Failed to read ability_frame_source.json");
    let data: serde_json::Value = serde_json::from_str(&json_content)
        .expect("Failed to parse ability_frame_source.json");

    let abilities = data
        .get("abilities")
        .and_then(|value| value.as_array())
        .expect("ability_frame_source.json should contain an abilities array");

    let mut add_hearts_count = 0usize;
    for ability in abilities {
        if let Some(frames) = ability.get("frames").and_then(|value| value.as_array()) {
            for frame in frames {
                if frame.get("op").and_then(|value| value.as_str()) != Some("ADD_HEARTS") {
                    continue;
                }

                add_hearts_count += 1;
                let params = frame
                    .get("params")
                    .and_then(|value| value.as_object())
                    .expect("ADD_HEARTS frames should carry params metadata");
                assert!(
                    params.contains_key("heart_type") || params.contains_key("heart_types"),
                    "ADD_HEARTS frames should explicitly mark heart_type or heart_types: {:?}",
                    frame
                );
            }
        }
    }

    assert_eq!(add_hearts_count, 73, "Expected the normalized source to contain 73 ADD_HEARTS frames");

    fn find_ability<'a>(
        abilities: &'a [serde_json::Value],
        card_no: &str,
        ability_index: usize,
    ) -> &'a serde_json::Value {
        abilities
            .iter()
            .find(|ability| {
                ability
                    .get("card_refs")
                    .and_then(|value| value.as_array())
                    .and_then(|refs| refs.first())
                    .and_then(|first| first.get("card_no"))
                    .and_then(|value| value.as_str())
                    == Some(card_no)
                    && ability
                        .get("card_refs")
                        .and_then(|value| value.as_array())
                        .and_then(|refs| refs.first())
                        .and_then(|first| first.get("ability_index"))
                        .and_then(|value| value.as_u64())
                        .map(|idx| idx as usize)
                        == Some(ability_index)
            })
            .expect("Expected to find a matching ability entry in ability_frame_source.json")
    }

    let tiny_stars = find_ability(abilities, "PL!SP-bp1-024-L", 0);
    let tiny_hearts: Vec<i64> = tiny_stars
        .get("frames")
        .and_then(|value| value.as_array())
        .unwrap()
        .iter()
        .filter(|frame| frame.get("op").and_then(|value| value.as_str()) == Some("ADD_HEARTS"))
        .map(|frame| {
            frame
                .get("params")
                .and_then(|value| value.as_object())
                .and_then(|params| params.get("heart_type"))
                .and_then(|value| value.as_i64())
                .expect("Tiny Stars ADD_HEARTS frames should have numeric heart_type metadata")
        })
        .collect();
    assert_eq!(tiny_hearts, vec![4, 0], "Tiny Stars should carry distinct heart metadata for each member");

    for (ability_index, expected_heart_type, expected_target_player) in [
        (0usize, 2i64, Some("OPPONENT")),
        (1usize, 2i64, Some("BOTH")),
        (2usize, 4i64, Some("SELF")),
    ] {
        let card_864 = find_ability(abilities, "PL!SP-bp5-011-AR", ability_index);
        let card_864_heart = card_864
            .get("frames")
            .and_then(|value| value.as_array())
            .unwrap()
            .iter()
            .find(|frame| frame.get("op").and_then(|value| value.as_str()) == Some("ADD_HEARTS"))
            .expect("Card 864 ADD_HEARTS frame should exist");
        let params = card_864_heart
            .get("params")
            .and_then(|value| value.as_object())
            .expect("Card 864 ADD_HEARTS frame should have params");
        assert_eq!(
            params.get("heart_type").and_then(|value| value.as_i64()),
            Some(expected_heart_type),
            "Card 864 ability {} should preserve the expected heart color",
            ability_index
        );
        assert_eq!(
            card_864_heart
                .get("attr")
                .and_then(|value| value.as_object())
                .and_then(|attr| attr.get("target_player"))
                .and_then(|value| value.as_str()),
            expected_target_player,
            "Card 864 ability {} should preserve the expected target scope",
            ability_index
        );
    }

    let rina_all = find_ability(abilities, "PL!N-bp3-009-P", 0);
    let rina_heart = rina_all
        .get("frames")
        .and_then(|value| value.as_array())
        .unwrap()
        .iter()
        .find(|frame| frame.get("op").and_then(|value| value.as_str()) == Some("ADD_HEARTS"))
        .expect("Rina ability should include ADD_HEARTS");
    let rina_params = rina_heart
        .get("params")
        .and_then(|value| value.as_object())
        .expect("Rina ADD_HEARTS should have params");
    assert_eq!(
        rina_params.get("heart_type").and_then(|value| value.as_i64()),
        Some(6),
        "All-heart grants should be normalized to the ANY heart type"
    );
    assert_eq!(
        rina_params.get("all").and_then(|value| value.as_bool()),
        Some(true),
        "All-heart grants should also mark the explicit all-heart flag"
    );

    let mia = find_ability(abilities, "PL!N-bp4-011-P", 0);
    let mia_heart = mia
        .get("frames")
        .and_then(|value| value.as_array())
        .unwrap()
        .iter()
        .find(|frame| frame.get("op").and_then(|value| value.as_str()) == Some("ADD_HEARTS"))
        .expect("Mia ability should include ADD_HEARTS");
    let mia_params = mia_heart
        .get("params")
        .and_then(|value| value.as_object())
        .expect("Mia ADD_HEARTS should have params");
    assert_eq!(
        mia_params.get("heart_type").and_then(|value| value.as_str()),
        Some("SELECTED"),
        "Choice-based heart grants should be marked as selected hearts"
    );
}

#[test]
fn test_all_abilities_have_frame_verification() {
    let json_content = std::fs::read_to_string("../data/ability_frame_source.json")
        .expect("Failed to read ability_frame_source.json");
    let data: serde_json::Value = serde_json::from_str(&json_content)
        .expect("Failed to parse ability_frame_source.json");

    let abilities = data
        .get("abilities")
        .and_then(|value| value.as_array())
        .expect("ability_frame_source.json should contain an abilities array");

    let mut missing_verification = Vec::new();
    let mut invalid_verification = Vec::new();

    for (index, ability) in abilities.iter().enumerate() {
        // Check if frame_verification exists
        let verification = match ability.get("frame_verification") {
            Some(v) => v,
            None => {
                missing_verification.push(index);
                continue;
            }
        };

        // Check verification structure
        let has_verified = verification.get("verified").is_some();
        let has_notes = verification.get("notes").and_then(|v| v.as_array()).is_some();
        let has_text_mapping = verification.get("text_mapping").is_some();

        if !has_verified || !has_notes || !has_text_mapping {
            invalid_verification.push((
                index,
                format!(
                    "verified: {}, notes: {}, text_mapping: {}",
                    has_verified, has_notes, has_text_mapping
                ),
            ));
        }
    }

    if !missing_verification.is_empty() {
        panic!(
            "Found {} abilities without frame_verification: {:?}",
            missing_verification.len(),
            missing_verification
        );
    }

    if !invalid_verification.is_empty() {
        panic!(
            "Found {} abilities with invalid verification structure:\n{}",
            invalid_verification.len(),
            invalid_verification
                .iter()
                .map(|(idx, reason)| format!("Ability {}: {}", idx, reason))
                .collect::<Vec<_>>()
                .join("\n")
        );
    }

    println!(
        "All {} abilities have valid frame_verification structures",
        abilities.len()
    );
}
