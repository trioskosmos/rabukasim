use std::collections::HashSet;
use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;
use std::sync::{Mutex, OnceLock};

struct CoverageRecorder {
    out_path: PathBuf,
    seen: HashSet<(i32, i16)>,
}

static COVERAGE_RECORDER: OnceLock<Option<Mutex<CoverageRecorder>>> = OnceLock::new();

fn coverage_recorder() -> Option<&'static Mutex<CoverageRecorder>> {
    COVERAGE_RECORDER
        .get_or_init(|| {
            let Ok(raw_path) = std::env::var("RUST_ABILITY_COVERAGE_OUT") else {
                return None;
            };
            let out_path = PathBuf::from(raw_path);
            Some(Mutex::new(CoverageRecorder {
                out_path,
                seen: HashSet::new(),
            }))
        })
        .as_ref()
}

pub fn record_ability_resolution(source_card_id: i32, ability_index: i16) {
    if source_card_id < 0 || ability_index < 0 {
        return;
    }

    let Some(recorder) = coverage_recorder() else {
        return;
    };
    let Ok(mut recorder) = recorder.lock() else {
        return;
    };
    if !recorder.seen.insert((source_card_id, ability_index)) {
        return;
    }

    let Ok(mut file) = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&recorder.out_path)
    else {
        return;
    };

    let _ = writeln!(
        file,
        "{{\"source_card_id\":{},\"ability_index\":{}}}",
        source_card_id,
        ability_index
    );
}