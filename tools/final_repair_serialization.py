import os

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

# We will read the whole file as a string (handling possible encoding mess)
with open(path, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8", errors="replace")

# 1. Fix the double-replacement in get_ability_summary
# We'll just replace the whole function to be safe.
import re

func_pattern = re.compile(r"pub fn get_ability_summary\(.*?\n\}", re.DOTALL)
new_func = """pub fn get_ability_summary(ab: &Value, lang: &str) -> String {
    let trigger = ab.get("trigger").and_then(|v| v.as_i64()).unwrap_or(0);
    let prefix = if lang == "jp" {
        let t_map = ["", "登場時", "ライブ進行時", "ライブ成功時", "ターン開始時", "ターン終了時", "常時", "起動"];
        let t_desc = t_map.get(trigger as usize).unwrap_or(&"");
        if !t_desc.is_empty() { format!("【{}】", t_desc) } else { "".to_string() }
    } else {
        let t_map = ["", "OnPlay", "LiveStart", "Success", "TurnStart", "TurnEnd", "Constant", "Act"];
        let t_desc = t_map.get(trigger as usize).unwrap_or(&"");
        if !t_desc.is_empty() { format!("[{}]", t_desc) } else { "".to_string() }
    };

    let effects = ab.get("effects").and_then(|v| v.as_array());
    if effects.is_none() || effects.unwrap().is_empty() {
        let raw = ab.get("raw_text").and_then(|v| v.as_str()).unwrap_or("");
        let short_raw = if raw.len() > 25 { format!("{}...", &raw[..22]) } else { raw.to_string() };
        return format!("{}{}", prefix, short_raw);
    }

    let eff = &effects.unwrap()[0];
    let etype = eff.get("effect_type").and_then(|v| v.as_i64()).unwrap_or(-1);
    let val = eff.get("value").and_then(|v| v.as_i64()).unwrap_or(0);
    let target = eff.get("target").and_then(|v| v.as_i64()).unwrap_or(0);
    let params = eff.get("params").and_then(|v| v.as_object());
    
    let tg_name = if lang == "jp" {
        match target {
            1 => "自分",
            2 => "相手",
            _ => "全体"
        }
    } else {
        match target {
            1 => "Self",
            2 => "Opponent",
            _ => "All"
        }
    };

    format!("{}{}: {}", prefix, tg_name, etype) // Placeholder for rich summary
}"""

content = func_pattern.sub(new_func, content)

# 2. Fix the Choice Type Titles Mojibake in serialize_game
choice_titles_jp = {
    "SELECT_MODE": "モードを選択してください",
    "LOOK_AND_CHOOSE": "カードを選択してください",
    "SELECT_CARDS": "カードを選択してください",
    "COLOR_SELECT": "色を選択してください",
    "TAP_O": "相手の枠を選択してください",
    "RECOV_L": "回収するライブを選択してください",
    "RECOV_M": "回収するメンバーを選択してください",
    "SELECT_HAND_DISCARD": "捨てるカードを選択してください",
    "SELECT_HAND_PLAY": "プレイするカードを選択してください",
    "SELECT_LIVE_SLOT": "ライブスロットを選択してください",
    "SELECT_STAGE": "ステージを選択してください",
    "PAY_ENERGY": "エネルギーを選択してください",
    "_": "選択してください"
}

for key, val in choice_titles_jp.items():
    if key == "_":
        # Handle the default case separately or carefully
        content = re.sub(r'_ => "驕ｸ謚槭＠縺ｦ縺上□縺輔＞"\.to_string\(\)', f'_ => "{val}".to_string()', content)
    else:
        # Match "KEY" => "MOJIBAKE".to_string()
        pattern = fr'"{key}" => ".*"\.to_string\(\)'
        replacement = f'"{key}" => "{val}".to_string()'
        content = re.sub(pattern, replacement, content)

# 3. Final cleanup of any lingering PowerShell trash or corrupted delimiters
content = content.replace('format!("縲須}縲・', 'format!("【{}】"')
content = content.replace(') } else { "".to_string() } else { "".to_string() }', ') } else { "".to_string() }')

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Final repair complete.")
