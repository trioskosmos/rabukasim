fn main() {
    if let Err(error) = engine_rust::export_hydrated_abilities::run_default() {
        eprintln!("[export_hydrated_abilities] {}", error);
        std::process::exit(1);
    }
}
