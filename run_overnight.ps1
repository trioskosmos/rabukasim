# run_overnight.ps1 - runs overnight training and redirects output to logs\overnight.log
Set-StrictMode -Version Latest
Set-Location -Path "$PSScriptRoot"
if (-not (Test-Path -Path .\logs)) { New-Item -ItemType Directory -Path .\logs | Out-Null }

# Use PowerShell redirection to capture stdout and stderr into the same log file
$log = Join-Path -Path $PSScriptRoot -ChildPath "logs\overnight.log"

# Command to run (edit arguments as needed)
$launcher = "uv"
$scriptArgs = if ($env:LOVECA_OVERNIGHT_ARGS) {
    @("run", "python", "alphazero/training/overnight_vanilla.py") + ($env:LOVECA_OVERNIGHT_ARGS -split " ")
} else {
    @(
        "run",
        "python",
        "alphazero/training/overnight_vanilla.py",
        "overfit",
        "--run-name", "vanilla_compact_abilityless_h20_onegame_overfit",
        "--cycles", "1000000",
        "--max-hours", "0",
        "--seed", "1337",
        "--fixed-cycle-seed",
        "--reset-run",
        "--device", "cuda",
        "--model-preset", "small",
        "--batch-size", "256",
        "--train-steps-per-cycle", "128",
        "--min-buffer-samples", "1",
        "--buffer-dir", "alphazero/training/experience_vanilla_compact_h20_onegame_overfit",
        "--checkpoint-dir", "alphazero/training/vanilla_checkpoints_compact_h20_onegame_overfit",
        "--checkpoint-every-cycles", "1"
    )
}

# Run the process and redirect both streams
try {
    & $launcher @scriptArgs *>&1 | Out-File -FilePath $log -Encoding utf8 -Append
} catch {
    "$(Get-Date -Format o) - Failed to start training: $_" | Out-File -FilePath $log -Encoding utf8 -Append
}
