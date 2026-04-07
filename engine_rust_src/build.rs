use std::env;
use std::path::{Path, PathBuf};
use std::process::Command;

fn main() {
    let manifest_dir =
        PathBuf::from(env::var("CARGO_MANIFEST_DIR").expect("missing CARGO_MANIFEST_DIR"));
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
        "data/ability_frame_source.json",
        "data/metadata.json",
        "engine/compiler/runtime_cards.py",
        "engine/compiler/main.py",
        "tools/sync_metadata.py",
        "tools/build_cards.py",
        "tools/abilities/pipeline.py",
        "tools/frame_codec.py",
    ] {
        println!(
            "cargo:rerun-if-changed={}",
            workspace_root.join(rel).display()
        );
    }

    if env::var_os("LOVECA_SKIP_ABILITY_PIPELINE").is_some() {
        return;
    }

    if let Some(uv) = find_uv() {
        if let Err(message) = run_uv_pipeline(&workspace_root, &uv, &["tools/sync_metadata.py"]) {
            panic!("Metadata sync failed: {}", message);
        }
        if let Err(message) =
            run_uv_pipeline(&workspace_root, &uv, &["tools/build_cards.py", "--quiet"])
        {
            panic!("Ability pipeline failed: {}", message);
        }
        return;
    }

    match find_python(&workspace_root) {
        Some(python) => {
            if let Err(message) = run_pipeline(
                &workspace_root,
                python.as_path(),
                &["tools/sync_metadata.py"],
            ) {
                panic!("Metadata sync failed: {}", message);
            }
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
                "cargo:warning=Skipping ability pipeline because neither uv nor a usable Python interpreter was found"
            );
        }
    }
}

fn find_uv() -> Option<PathBuf> {
    let candidates = [PathBuf::from("uv.exe"), PathBuf::from("uv")];
    for candidate in candidates {
        let status = Command::new(&candidate).arg("--version").output();
        if status.map(|out| out.status.success()).unwrap_or(false) {
            return Some(candidate);
        }
    }
    None
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

fn run_uv_pipeline(workspace_root: &Path, uv: &Path, python_args: &[&str]) -> Result<(), String> {
    let mut args = vec!["run", "--no-sync", "--python", "3.12", "python"];
    args.extend_from_slice(python_args);

    let output = Command::new(uv)
        .args(&args)
        .current_dir(workspace_root)
        .output()
        .map_err(|error| format!("Failed to start {}: {error}", uv.display()))?;

    if output.status.success() {
        return Ok(());
    }

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);
    Err(format!(
        "Ability pipeline command `{} {}` failed with status {}\nstdout:\n{}\nstderr:\n{}",
        uv.display(),
        args.join(" "),
        output.status,
        stdout,
        stderr,
    ))
}
