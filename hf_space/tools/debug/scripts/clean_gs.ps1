$path = "engine/game/game_state.py"
$content = Get-Content $path
$newContent = $content[0..762] + $content[3350..($content.Length - 1)]
$newContent | Set-Content $path -Encoding UTF8
