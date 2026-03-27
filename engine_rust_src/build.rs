use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

fn main() {
    let manifest_dir = PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("missing CARGO_MANIFEST_DIR"));
    let workspace_root = manifest_dir
        .parent()
        .expect("engine_rust_src should live under the workspace root")
        .to_path_buf();

    println!("cargo:rerun-if-env-changed=LOVECA_SKIP_ABILITY_PIPELINE");
    println!("cargo:rerun-if-env-changed=LOVECA_RUN_ABILITY_PIPELINE");
    for rel in [
        "data/cards.json",
        "data/ability_frames.json",
        "data/metadata.json",
    ] {
        println!("cargo:rerun-if-changed={}", workspace_root.join(rel).display());
    }

    if env::var_os("LOVECA_SKIP_ABILITY_PIPELINE").is_some() {
        println!("cargo:warning=Skipping ability pipeline because LOVECA_SKIP_ABILITY_PIPELINE is set");
        return;
    }

    if env::var_os("LOVECA_RUN_ABILITY_PIPELINE").is_none() {
        println!(
            "cargo:warning=Skipping ability pipeline during build; set LOVECA_RUN_ABILITY_PIPELINE=1 to regenerate artifacts"
        );
        return;
    }

    run_pipeline(&workspace_root, &["uv", "run", "python", "tools/prepare_ability_pipeline.py", "--quiet"])
        .or_else(|_| run_pipeline(&workspace_root, &["python", "tools/prepare_ability_pipeline.py", "--quiet"]))
        .unwrap_or_else(|message| panic!("{message}"));
}

fn run_pipeline(workspace_root: &Path, args: &[&str]) -> Result<(), String> {
    let (program, rest) = args.split_first().expect("command args must not be empty");
    let output = Command::new(program)
        .args(rest)
        .current_dir(workspace_root)
        .output()
        .map_err(|error| format!("Failed to start {program}: {error}"))?;

    if output.status.success() {
        return Ok(());
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    Err(format!(
        "Ability pipeline command `{program} {}` failed with status {}\nstdout:\n{}\nstderr:\n{}",
        rest.join(" "),
        output.status,
        stdout,
        stderr,
    ))
}
