@echo off
echo [Build] Recompiling Rust Engine (Optimized Dev Mode)...
uv run maturin develop --profile dev-release
if %errorlevel% neq 0 (
    echo [ERROR] Rust build failed!
    pause
    exit /b %errorlevel%
)
echo [Build] Complete.
