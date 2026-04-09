use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};

#[test]
fn export_hydrated_abilities_writes_data_folder_entrypoint_index() {
    let unique_suffix = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock should be after unix epoch")
        .as_nanos();
    let output_path = std::env::temp_dir().join(format!(
        "ability_runtime_entrypoints_test_{}.json",
        unique_suffix
    ));

    let output_path = engine_rust::export_hydrated_abilities::run(Some(output_path))
        .expect("hydrated ability export should complete");

    let json = fs::read_to_string(&output_path)
        .unwrap_or_else(|error| panic!("failed reading {}: {}", output_path.display(), error));
    let export: serde_json::Value = serde_json::from_str(&json)
        .unwrap_or_else(|error| panic!("failed parsing {}: {}", output_path.display(), error));

    let ability_count = export
        .get("summary")
        .and_then(|summary| summary.get("ability_count"))
        .and_then(|value| value.as_u64())
        .expect("export should include summary.ability_count");

    assert!(
        ability_count > 0,
        "export should contain hydrated abilities"
    );

    let first_filter = export
        .get("abilities")
        .and_then(|abilities| abilities.as_array())
        .and_then(|abilities| {
            abilities
                .iter()
                .flat_map(|ability| {
                    ability
                        .get("trace_view")
                        .and_then(|trace_view| trace_view.get("steps"))
                        .and_then(|steps| steps.as_array())
                        .into_iter()
                        .flatten()
                })
                .find_map(|step| step.get("filter"))
        })
        .expect("export should include semantic trace_view filter data");

    assert!(
        first_filter.is_object(),
        "trace_view filter should be serialized as a semantic object"
    );

    assert_eq!(
        export
            .get("metadata")
            .and_then(|metadata| metadata.get("extraction_entrypoint"))
            .and_then(|value| value.as_str()),
        Some("Ability::trace_view()")
    );

    let _ = fs::remove_file(&output_path);
}
