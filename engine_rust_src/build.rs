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
    println!("cargo:rerun-if-env-changed=UV_CACHE_DIR");
    println!("cargo:rerun-if-env-changed=UV_PYTHON_INSTALL_DIR");
    for rel in [
        "data/cards.json",
        "data/ability_frame_index.yaml",
        "data/ability_frame_index.json",
        "data/consolidated_abilities.json",
        "data/cards_compiled.json",
        "data/metadata.json",
        "compiler/main.py",
        "tools/build_cards.py",
        "tools/abilities/pipeline.py",
        "tools/frame_codec.py",
        "tools/bytecode_codec.py",
        "engine/models/ability_frames.py",
    ] {
        println!("cargo:rerun-if-changed={}", workspace_root.join(rel).display());
    }

    if env::var_os("LOVECA_SKIP_ABILITY_PIPELINE").is_some() {
        println!("cargo:warning=Skipping ability pipeline because LOVECA_SKIP_ABILITY_PIPELINE is set");
        return;
    }

    if let Err(message) = run_pipeline(
        &workspace_root,
        &[
            "uv",
            "run",
            "--isolated",
            "--managed-python",
            "--python",
            "3.12",
            "python",
            "tools/build_cards.py",
            "--quiet",
        ],
    )
    .or_else(|_| {
        run_pipeline(
            &workspace_root,
            &["python", "tools/build_cards.py", "--quiet"],
        )
    })
    {
        println!("cargo:warning=Skipping ability pipeline during build: {}", message);
    }
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
