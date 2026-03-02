path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8", errors="replace")

# Mapping of English strings to Japanese strings for action descriptions
string_map = {
    "Perform Live": "【開始】パフォーマンス",
    "Start the performance check.": "パフォーマンスを開始します。",
    "Finish Performance": "【完了】次へ",
    "Confirm results and proceed.": "結果を確認して次へ進みます。",
    "Confirm Mulligan": "【確定】マリガン終了",
    "Finish Mulligan and start the game.": "手札を確定してマリガンを終了します。",
    "Confirm Live Set": "【確定】セット完了",
    "Finish setting cards for the live zone.": "ライブカードのセットを終了します。",
    "Pass / Confirm": "【スキップ】パス",
    "Skip or confirm current action.": "何もしない。",
    "Mulligan: ": "【マリガン】",
    "Return this card to deck and draw a new one.": "このカードをデッキに戻して引き直します。",
    "Select: ": "【選択】",
    "Select this card.": "このカードを選択します。",
    "Recover: ": "【回収】",
    "Return this card to hand.": "このカードを手札に戻します。",
    "Discard: ": "【控え室】",
    "Put this card into the discard pile.": "このカードを控え室に置きます。",
    "Ability": "アビリティ",
    "Use ": "【起動】",
    "Left": "左",
    "Mid": "中",
    "Right": "右",
    "On Play": "登場",
    "to": "に置く",
    "Baton Touch": "バトンタッチ",
    "leaves": "退場",
    "Pay": "支払",
    "Cost": "コスト",
    "Pink": "ピンク",
    "Red": "赤",
    "Yellow": "黄",
    "Green": "緑",
    "Blue": "青",
    "Purple": "紫",
    "Choose ": "【色を選択】",
    "Additional Effect": "【追加効果】",
}

# Repairing get_action_desc_rich logic
content = content.replace(
    '("縲宣幕蟋九€代ヱ繝輔か繝ｼ繝槭Φ繧ｹ".into(), "繝代ヵ繧ｩ繝ｼ繝槭Φ繧ｹ繧帝幕蟋九＠縺ｾ縺吶€・.into())',
    '("【開始】パフォーマンス".into(), "パフォーマンスを開始します。".into())',
)
content = content.replace(
    '("縲仙ｮ御ｺ・€第ｬ｡縺へ".into(), "邨先棡繧堤｢ｺ隱阪＠縺ｦ谺｡縺へ騾ｲ縺ｿ縺ｾ縺吶€・.into())',
    '("【完了】次へ".into(), "結果を確認して次へ進みます。".into())',
)
content = content.replace(
    '("縲千｢ｺ螳壹€代・繝ｪ繧ｬ繝ｳ".into(), "謇区惆繧堤｢ｺ螳壹＠縺ｦ繝槭Μ繧ｬ繝ｳ繧堤ｵゆｺ・＠縺ｾ縺吶€・.into())',
    '("【確定】マリガン".into(), "手札を確定してマリガンを終了します。".into())',
)
content = content.replace(
    '("縲千｢ｺ螳壹€代そ繝・ヨ螳御ｺ守.into(), "繝ｩ繧､繝悶き繝ｼ繝峨・繧ｻ繝・ヨ繧堤ｵゆｺ・＠縺ｾ縺吶€・.into())',
    '("【確定】セット完了".into(), "ライブカードのセットを終了します。".into())',
)
content = content.replace(
    '("縲舌せ繧ｭ繝・・縲代ヱ繧ｹ".into(), "菴輔ｂ縺励↑縺・€・.into())',
    '("【スキップ】パス".into(), "何もしない。".into())',
)
content = content.replace('format!("縲舌・繝ｪ繧ｬ繝ｳ縲捜}", card_name)', 'format!("【マリガン】{}", card_name)')
content = content.replace(
    '"縺薙・繧ｫ繝ｼ繝峨ｒ繝・ャ繧ｭ縺ｫ謌ｻ縺励※蠑輔″逶ｴ縺励∪縺吶€・.into()',
    '"このカードをデッキに戻して引き直します。".into()',
)
content = content.replace(
    '("蟾ｦ", "荳ｭ", "蜿ｳ", "逋ｻ蝣ｴ", "縺ｫ鄂ｮ縺・, "繝舌ヨ繝ｳ繧ｿ繝・メ", "騾€蝣ｴ", "謾ｯ謇・, "繧ｳ繧ｹ繝・)',
    '("左", "中", "右", "登場", "に置く", "バトンタッチ", "退場", "支払", "コスト")',
)
content = content.replace('format!("{} ({}){} ({}: {}騾€蝣ｴ, {}:{})"', 'format!("{} ({}){} ({}: {}退場, {}:{})"')
content = content.replace('format!("({}: {}騾€蝣ｴ, {}:{})"', 'format!("({}: {}退場, {}:{})"')
content = content.replace('"繧｢繝薙Μ繝・ぅ".into()', '"アビリティ".into()')
content = content.replace('["蟾ｦ", "荳ｭ", "蜿ｳ"]', '["左", "中", "右"]')
content = content.replace('format!("縲占ｵｷ蜍輔€捜}: {} ({})"', 'format!("【起動】{}: {} ({})"')
content = content.replace('format!("隨ｬ{}譫繧帝∈謚・, choice_idx + 1)', 'format!("第{}枠を選択", choice_idx + 1)')
content = content.replace('format!("繧ｿ繝・・: {}"', 'format!("タップ: {}")')
content = content.replace('format!("逶ｸ謇九・{}譫"', 'format!("相手の{}枠", areas.get(choice_idx).unwrap_or(&""))')
content = content.replace('"縺薙・繧ｫ繝ｼ繝峨ｒ驕ｸ謚槭＠縺ｾ縺吶€・', '"このカードを選択します。"')
content = content.replace('"縲宣∈謚槭€・', '"【選択】"')
content = content.replace('"縲仙屓蜿弱€・', '"【回収】"')
content = content.replace('"縺薙・繧ｫ繝ｼ繝峨ｒ謇区惆縺ｫ謌ｻ縺励∪縺吶€・', '"このカードを手札に戻します。"')
content = content.replace('"縲先而縺亥ｮ､縲・', '"【控え室】"')
content = content.replace('"縺薙・繧ｫ繝ｼ繝峨ｒ謗ｧ縺亥ｮ､縺ｫ鄂ｮ縺阪∪縺吶€・', '"このカードを控え室に置きます。"')
content = content.replace('["繝斐Φ繧ｯ", "襍､", "鮟・, "邱・, "髱・, "邏ｫ"]', '["ピンク", "赤", "黄", "緑", "青", "紫"]')
content = content.replace('format!("縲占牡繧帝∈謚槭€捜}"', 'format!("【色を選択】{}"')
content = content.replace('format!("縲占ｿｽ蜉蜉ｹ譫懊€捜}: {} ({})"', 'format!("【追加効果】{}: {} ({})"')

# Fix any remaining mojibake in titles (serialize_game part)
content = content.replace('"繝｢繝ｼ繝峨ｒ驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"モードを選択してください"')
content = content.replace('"繧ｫ繝ｼ繝峨ｒ驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"カードを選択してください"')
content = content.replace('"濶ｲ繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"色を選択してください"')
content = content.replace('"逶ｸ謇九・譫繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"相手の枠を選択してください"')
content = content.replace('"蝗槫庶縺吶ｋ繝ｩ繧､繝悶ｒ驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"回収するライブを選択してください"')
content = content.replace('"蝗槫庶縺吶ｋ繝｡繝ｳ繝舌・繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"回収するメンバーを選択してください"')
content = content.replace('"謐ｨ縺ｦ繧九き繝ｼ繝峨ｒ驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"捨てるカードを選択してください"')
content = content.replace('"繝励Ξ繧､縺吶ｋ繧ｫ繝ｼ繝峨ｒ驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"プレイするカードを選択してください"')
content = content.replace('"繝ｩ繧､繝悶せ繝ｭ繝・ヨ繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"ライブスロットを選択してください"')
content = content.replace('"繧ｹ繝・・繧ｸ繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"ステージを選択してください"')
content = content.replace('"繧ｨ繝阪Ν繧ｮ繝ｼ繧帝∈謚槭＠縺ｦ縺上□縺輔＞"', '"エネルギーを選択してください"')
content = content.replace('"驕ｸ謚槭＠縺ｦ縺上□縺輔＞"', '"選択してください"')

# Final delimiter fix for the double-else or mismatched braces
content = content.replace('else { "".to_string() } else { "".to_string() }', 'else { "".to_string() }')

# Normalize line endings
content = content.replace("\r\n", "\n").replace("\r", "").replace("\n", "\r\n")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Restoration complete.")
