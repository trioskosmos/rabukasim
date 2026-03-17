@echo off
echo [Build] Recompiling Rust Engine (Optimized Release Mode)...
uv run maturin develop --release --features extension-module -m engine_rust_src/Cargo.toml
if %errorlevel% neq 0 (
    echo [ERROR] Rust build failed!
    exit /b %errorlevel%
)
if not exist .tmp_engine mkdir .tmp_engine
copy /Y engine_rust_src\target\release\engine_rust.dll .tmp_engine\engine_rust.pyd >nul
if %errorlevel% neq 0 (
    echo [ERROR] Failed to refresh .tmp_engine\engine_rust.pyd
    exit /b %errorlevel%
)
echo [Build] Complete.
