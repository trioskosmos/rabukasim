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
        "engine/compiler/main.py",
        "tools/build_cards.py",
        "tools/abilities/pipeline.py",
        "tools/frame_codec.py",
    ] {
        println!("cargo:rerun-if-changed={}", workspace_root.join(rel).display());
    }

    if env::var_os("LOVECA_SKIP_ABILITY_PIPELINE").is_some() {
        println!("cargo:warning=Skipping ability pipeline because LOVECA_SKIP_ABILITY_PIPELINE is set");
        return;
    }

    match find_python(&workspace_root) {
        Some(python) => {
            if let Err(message) = run_pipeline(
                &workspace_root,
                python.as_path(),
                &["tools/build_cards.py", "--quiet"],
            ) {
                panic!("Ability pipeline failed: {}", message);
            }
        }
        None => {
            println!(
                "cargo:warning=Skipping ability pipeline because no usable Python interpreter was found"
            );
        }
    }
}

fn find_python(workspace_root: &Path) -> Option<PathBuf> {
    let candidates = [
        workspace_root.join(".venv/Scripts/python.exe"),
        workspace_root.join(".uv-python/cpython-3.12.12-windows-x86_64-none/python.exe"),
        workspace_root.join(".uv-python/cpython-3.12.12-windows-x86_64-none/python3.12.exe"),
    ];

    for candidate in candidates {
        if candidate.exists() {
            return Some(candidate);
        }
    }

    None
}

fn run_pipeline(workspace_root: &Path, program: &Path, args: &[&str]) -> Result<(), String> {
    let output = Command::new(program)
        .args(args)
        .current_dir(workspace_root)
        .output()
        .map_err(|error| format!("Failed to start {}: {error}", program.display()))?;

    if output.status.success() {
        return Ok(());
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    Err(format!(
        "Ability pipeline command `{} {}` failed with status {}\nstdout:\n{}\nstderr:\n{}",
        program.display(),
        args.join(" "),
        output.status,
        stdout,
        stderr,
    ))
}
