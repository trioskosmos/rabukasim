use std::fs;

#[test]
fn export_hydrated_abilities_writes_data_folder_entrypoint_index() {
    let output_path = engine_rust::export_hydrated_abilities::run_default()
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

    assert!(ability_count > 0, "export should contain hydrated abilities");

    let first_attr = export
        .get("abilities")
        .and_then(|abilities| abilities.as_array())
        .and_then(|abilities| {
            abilities
                .iter()
                .flat_map(|ability| {
                    ability
                        .get("resolved_frames")
                        .and_then(|frames| frames.as_array())
                        .into_iter()
                        .flatten()
                })
                .find_map(|frame| frame.get("attr"))
        })
        .expect("export should include semantic resolved frame attr");

    assert!(
        first_attr.is_object(),
        "resolved frame attr should be serialized as a semantic object"
    );

    assert_eq!(
        export
            .get("metadata")
            .and_then(|metadata| metadata.get("extraction_entrypoint"))
            .and_then(|value| value.as_str()),
        Some("Ability::resolved_frames() + Ability::trace_view()")
    );
}
