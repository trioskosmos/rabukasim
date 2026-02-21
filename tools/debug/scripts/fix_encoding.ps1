$c = Get-Content engine/game/game_state.py
# If it's already fixed, just re-save with UTF8
$c | Set-Content engine/game/game_state.py -Encoding UTF8
Write-Host "Re-saved with UTF8"
