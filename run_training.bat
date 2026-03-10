@echo off
setlocal
:: Prevent CUDA Fragmentation on Windows
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

echo [1/3] Compiling Card Data...
uv run python -m compiler.main

echo [2/3] Syncing Rust Engine...
if exist "engine_rust_src\target\release\engine_rust.dll" (
    copy /y "engine_rust_src\target\release\engine_rust.dll" "%~dp0\engine_rust.pyd" >nul
    echo Logic: Using latest RELEASE build.
) else if exist "engine_rust_src\target\debug\engine_rust.dll" (
    copy /y "engine_rust_src\target\debug\engine_rust.dll" "%~dp0\engine_rust.pyd" >nul
    echo Logic: WARNING: Using DEBUG build.
) else (
    echo Logic: No compiled engine found. Attempting build...
    pushd engine_rust_src
    cargo build --release --features extension-module
    copy /y target\release\engine_rust.dll ..\engine_rust.pyd
    popd
)

echo [3/3] Starting AlphaZero Vanilla Training...
uv run python alphazero/training/overnight_vanilla.py

pause
