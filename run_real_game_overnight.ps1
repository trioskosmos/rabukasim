$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RepoRoot

$Python = Join-Path $RepoRoot '.venv_cuda\Scripts\python.exe'
$Trainer = Join-Path $RepoRoot 'alphazero\training\real_game_trainer.py'
$Checkpoint = Join-Path $RepoRoot 'checkpoints\real_game_agent.pt'
$ReplayDir = Join-Path $RepoRoot 'replay\real_game_agent'
$LogDir = Join-Path $RepoRoot 'logs'
$LogFile = Join-Path $LogDir 'real_game_overnight.log'

if (-not (Test-Path $Python)) {
    throw "CUDA Python not found at '$Python'"
}

if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

Write-Host '============================================================'
Write-Host 'Real Game Overnight Training'
Write-Host '============================================================'
Write-Host "Python: $Python"
Write-Host "Log:    $LogFile"
Write-Host "Check:  $Checkpoint"
Write-Host "Replay: $ReplayDir"
Write-Host ''
Write-Host 'Starting...'
Write-Host ''

$args = @(
    $Trainer
    '--device', 'cuda'
    '--episodes', '1000'
    '--eval-games', '32'
    '--updates-per-episode', '4'
    '--batch-size', '512'
    '--hidden-dim', '768'
    '--save-interval-seconds', '300'
    '--parallel-self-play-games', '24'
    '--cpu-search-sims', '4'
    '--checkpoint-path', $Checkpoint
    '--replay-buffer-dir', $ReplayDir
    '--replay-buffer-capacity', '4096'
    '--replay-buffer-max-candidates', '128'
    '--log-every-episodes', '1'
)

& $Python @args 2>&1 | Tee-Object -FilePath $LogFile -Append
exit $LASTEXITCODE
