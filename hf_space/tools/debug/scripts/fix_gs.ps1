$c = Get-Content engine/game/game_state.py
$start = $c[0..106]
$end = $c[481..($c.Length-1)]
Write-Host "Start lines: $($start.Length)"
Write-Host "First end line: $($end[0])"
$new = $start + $end
$new | Set-Content engine/game/game_state.py
Write-Host "Done"
