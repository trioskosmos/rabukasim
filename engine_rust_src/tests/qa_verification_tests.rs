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
        "FILTER_GROUP_SHIFT",      // Should be FILTER_GROUP_ID_SHIFT
        "FILTER_UNIT_SHIFT",       // Should be FILTER_UNIT_ID_SHIFT
        "FILTER_SPECIAL_SHIFT",    // Should be FILTER_SPECIAL_ID_SHIFT
        "FILTER_COST_SHIFT",       // Should be FILTER_VALUE_THRESHOLD_SHIFT
    ];

    let generated_files = vec![
        "generated_constants.rs",
        "generated_layout.rs",
    ];

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

    scan_directory(Path::new(src_dir), &forbidden_patterns, &generated_files, &mut violations);

    if !violations.is_empty() {
        panic!(
            "Anti-drift test FAILED: Found {} legacy filter constant usage(s):\n{}",
            violations.len(),
            violations.join("\n")
        );
    }
}
