@echo off
echo [Build] Recompiling Rust Engine...
uv run maturin develop --release -m engine_rust_src/Cargo.toml
if %errorlevel% neq 0 (
    echo [ERROR] Rust build failed!
    pause
    exit /b %errorlevel%
)
echo [Build] Complete.
