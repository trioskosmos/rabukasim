use engine_rust::core::logic::{GameState, PlayerState, CardDatabase, card_db};
use engine_rust::core::logic::*;
use engine_rust::core::enums;
use std::collections::HashMap;
use serde_json::{json, Value};

pub fn get_group_name(id: u8, lang: &str) -> &'static str {
    enums::get_group_name(id, lang)
}

pub fn get_unit_name(id: u8, lang: &str) -> &'static str {
    enums::get_unit_name(id, lang)
}

pub fn get_filter_description(filter_attr: u64, lang: &str) -> String {
    if filter_attr == 0 { return String::new(); }
    let mut parts: Vec<String> = Vec::new();

    // Type Filter (Bit 2-3)
    let type_filter = (filter_attr >> 2) & 0x03;
    match type_filter {
        1 => parts.push((if lang == "jp" { "メンバー" } else { "Member" }).to_string()),
        2 => parts.push((if lang == "jp" { "ライブ" } else { "Live" }).to_string()),
        _ => {}
    }

    // Character Filter (Bit 42)
    if (filter_attr & (1 << 42)) != 0 {
         let id1 = ((filter_attr >> 31) & 0x7F) as u8;
         let id2 = ((filter_attr >> 17) & 0x7F) as u8;
         let id3 = ((filter_attr >> 24) & 0x7F) as u8;

         let mut names = Vec::new();
         if id1 > 0 { names.push(card_db::get_character_name(id1)); }
         if id2 > 0 { names.push(card_db::get_character_name(id2)); }
         if id3 > 0 { names.push(card_db::get_character_name(id3)); }

         if !names.is_empty() {
             let name_str = names.join("・"); // Use dot for Japanese names? Or slash? Slash is fine.
             if lang == "jp" {
                 parts.push(format!("指定: {}", name_str));
             } else {
                 parts.push(format!("Character: {}", name_str));
             }
         }
    }

    // Color Filter (Bits 32-38)
    let color_mask = (filter_attr >> 32) & 0x7F;
    if color_mask != 0 {
        let colors = if lang == "jp" {
            ["スマイル", "ピュア", "クール", "緑", "青", "紫"]
        } else {
            ["Smile", "Pure", "Cool", "Green", "Blue", "Purple"]
        };
        for i in 0..6 {
            if (color_mask & (1 << i)) != 0 {
                parts.push(colors[i].to_string());
            }
        }
    }

    // Group Filter (Bit 4 + 5-11)
    if (filter_attr & 0x10) != 0 {
        let group_id = ((filter_attr >> 5) & 0x7F) as u8;
        parts.push(get_group_name(group_id, lang).to_string());
    }

    // Unit Filter (Bit 16 + 17-23)
    if (filter_attr & 0x10000) != 0 {
        let unit_id = ((filter_attr >> 17) & 0x7F) as u8;
        parts.push(get_unit_name(unit_id, lang).to_string());
    }

    // Cost/Hearts Filter (Bit 24 + 25-29 + 30 + 40)
    if (filter_attr & 0x01000000) != 0 {
        let threshold = (filter_attr >> 25) & 0x1F;
        let is_le = (filter_attr & 0x40000000) != 0;
        let label = if lang == "jp" {
            if is_le { format!("コスト{}以下", threshold) } else { format!("コスト{}以上", threshold) }
        } else {
            if is_le { format!("Cost <= {}", threshold) } else { format!("Cost >= {}", threshold) }
        };
        return if parts.is_empty() { label } else { format!("{} ({})", parts.join("/"), label) };
    }

    // Blades Filter (Bits 13-14)
    if (filter_attr & 0x2000) != 0 { parts.push((if lang == "jp" { "アピール" } else { "Appeal" }).to_string()); }
    if (filter_attr & 0x4000) != 0 { parts.push((if lang == "jp" { "カードのみ" } else { "Card Only" }).to_string()); }

    // Tapped (Bit 12)
    if (filter_attr & 0x1000) != 0 { parts.push((if lang == "jp" { "タップ状態" } else { "Tapped" }).to_string()); }

    parts.join("/")
}

pub fn decode_bytecode_to_strings(bytecode: &[i32]) -> Vec<String> {
    let mut decoded = Vec::new();
    for (i, chunk) in bytecode.chunks(5).enumerate() {
        if chunk.len() < 5 { break; }
        let ip = i * 5;
        let (op, v) = (chunk[0], chunk[1]);
        let a_low = chunk[2] as u32;
        let a_high = chunk[3] as u32;
        let s = chunk[4];
        let a = ((a_high as i64) << 32) | (a_low as i64);
        let desc = interpreter::logging::describe_bytecode(op, v, a, s);
        decoded.push(format!("ip={:<3} {}", ip, desc));
    }
    decoded
}

pub fn resolve_card_name(cid: i32, db: &CardDatabase, lang: &str) -> String {
    if cid == -1 { return if lang == "jp" { "カード" } else { "Card" }.to_string(); }
    if let Some(m) = db.get_member(cid) {
        format!("{} ({})", m.name, m.card_no)
    } else if let Some(l) = db.get_live(cid) {
        format!("{} ({})", l.name, l.card_no)
    } else if db.energy_db.contains_key(&cid) {
        format!("Energy #{}", cid)
    } else {
        format!("Unknown Card #{}", cid)
    }
}


pub fn resolve_card_desc(cid: i32, db: &CardDatabase) -> String {
    if cid == -1 { return "".to_string(); }
    if let Some(m) = db.get_member(cid) {
        m.original_text.clone()
    } else if let Some(l) = db.get_live(cid) {
        l.original_text.clone()
    } else {
        "".to_string()
    }
}

pub fn get_ability_summary(ab: &Value, lang: &str) -> String {
    let trigger = ab.get("trigger").and_then(|v| v.as_i64()).unwrap_or(0);
    let trigger_prefix = if lang == "jp" {
        let t = trigger as i32;
        if t == TriggerType::OnPlay as i32 { "【登場時】" }
        else if t == TriggerType::OnLiveStart as i32 { "【ライブ開始時】" }
        else if t == TriggerType::OnLiveSuccess as i32 { "【ライブ成功時】" }
        else if t == TriggerType::TurnStart as i32 { "【ターン開始時】" }
        else if t == TriggerType::TurnEnd as i32 { "【ターン終了時】" }
        else if t == TriggerType::Constant as i32 { "【常時】" }
        else if t == TriggerType::Activated as i32 { "【起動】" }
        else if t == TriggerType::OnLeaves as i32 { "【離脱時】" }
        else if t == TriggerType::OnReveal as i32 { "【公開時】" }
        else { "" }
    } else {
        let t = trigger as i32;
        if t == TriggerType::OnPlay as i32 { "[OnPlay]" }
        else if t == TriggerType::OnLiveStart as i32 { "[LiveStart]" }
        else if t == TriggerType::OnLiveSuccess as i32 { "[Success]" }
        else if t == TriggerType::TurnStart as i32 { "[TurnStart]" }
        else if t == TriggerType::TurnEnd as i32 { "[TurnEnd]" }
        else if t == TriggerType::Constant as i32 { "[Constant]" }
        else if t == TriggerType::Activated as i32 { "[Act]" }
        else if t == TriggerType::OnLeaves as i32 { "[Leaves]" }
        else if t == TriggerType::OnReveal as i32 { "[Reveal]" }
        else { "" }
    }.to_string();

    let costs = ab.get("costs").and_then(|v| v.as_array());
    let mut cost_str = String::new();
    if let Some(c_list) = costs {
        for c in c_list {
            let c_type = c.get("type").and_then(|v| v.as_i64()).unwrap_or(-1) as i32;
            if c_type == COST_SACRIFICE_SELF {
                cost_str = if lang == "jp" { "自身を退場させて: ".into() } else { "Sacrifice self: ".into() };
            } else if c_type == COST_ENERGY {
                let val = c.get("value").and_then(|v| v.as_i64()).unwrap_or(0);
                cost_str = if lang == "jp" { format!("{}コスト: ", val) } else { format!("{} Cost: ", val) };
            }
        }
    }

    let effects = ab.get("effects").and_then(|v| v.as_array());
    if effects.is_none() || effects.unwrap().is_empty() {
        let raw = ab.get("raw_text").and_then(|v| v.as_str()).unwrap_or("");
        let short_raw = if raw.len() > 25 { format!("{}...", &raw[..22]) } else { raw.to_string() };
        return format!("{}{}{}", trigger_prefix, cost_str, short_raw);
    }

    // Map comprehensive effect types based on engine/models/ability.py
    let get_eff_name = |etype: i64, l: &str| -> String {
        match etype as i32 {
            O_DRAW => if l == "jp" { "ドロー".into() } else { "Draw".into() },
            O_ADD_BLADES => if l == "jp" { "ボルテージ+".into() } else { "Voltage+".into() },
            O_ADD_HEARTS => if l == "jp" { "ピース+".into() } else { "Hearts+".into() },
            O_REDUCE_COST => if l == "jp" { "コスト軽減".into() } else { "Reduce Cost".into() },
            O_LOOK_DECK => if l == "jp" { "デッキの上から見る".into() } else { "Look Deck".into() },
            O_RECOVER_LIVE => if l == "jp" { "ライブを回収".into() } else { "Recov Live".into() },
            O_BOOST_SCORE => if l == "jp" { "スコア+".into() } else { "Boost".into() },
            O_RECOVER_MEMBER => if l == "jp" { "メンバーを回収".into() } else { "Recov Member".into() },
            O_BUFF_POWER => if l == "jp" { "パワー+".into() } else { "Buff".into() },
            O_IMMUNITY => if l == "jp" { "効果無効".into() } else { "Immunity".into() },
            O_MOVE_MEMBER => if l == "jp" { "メンバー移動".into() } else { "Move".into() },
            O_SWAP_CARDS => if l == "jp" { "手札交換".into() } else { "Swap".into() },
            O_SEARCH_DECK => if l == "jp" { "デッキ検索".into() } else { "Search".into() },
            O_ENERGY_CHARGE => if l == "jp" { "エネルギーチャージ".into() } else { "Charge".into() },
            O_SET_BLADES => if l == "jp" { "ブレード固定".into() } else { "Set Blades".into() },
            O_SET_HEARTS => if l == "jp" { "ハート固定".into() } else { "Set Hearts".into() },
            O_FORMATION_CHANGE => if l == "jp" { "配置変更".into() } else { "Formation".into() },
            O_NEGATE_EFFECT => if l == "jp" { "効果打ち消し".into() } else { "Negate".into() },
            O_ORDER_DECK => if l == "jp" { "デッキ並べ替え".into() } else { "Order Deck".into() },
            O_META_RULE => if l == "jp" { "ルール変更".into() } else { "Meta Rule".into() },
            O_SELECT_MODE => if l == "jp" { "モード選択".into() } else { "Select Mode".into() },
            O_MOVE_TO_DECK => if l == "jp" { "デッキに戻す".into() } else { "To Deck".into() },
            O_TAP_OPPONENT => if l == "jp" { "相手をウェイトにする".into() } else { "Tap Opp".into() },
            O_PLACE_UNDER => if l == "jp" { "メンバーの下に置く".into() } else { "Place Under".into() },
            O_RESTRICTION => if l == "jp" { "プレイ制限".into() } else { "Restriction".into() },
            O_BATON_TOUCH_MOD => if l == "jp" { "バトンタッチ変更".into() } else { "Baton Mod".into() },
            O_SET_SCORE => if l == "jp" { "スコア固定".into() } else { "Set Score".into() },
            O_SWAP_ZONE => if l == "jp" { "カード移動".into() } else { "Swap Zone".into() },
            O_TRANSFORM_COLOR => if l == "jp" { "色変換".into() } else { "Transf Color".into() },
            O_REVEAL_CARDS => if l == "jp" { "公開".into() } else { "Reveal".into() },
            O_LOOK_AND_CHOOSE => if l == "jp" { "見て選ぶ".into() } else { "Look & Choose".into() },
            O_CHEER_REVEAL => if l == "jp" { "応援で公開".into() } else { "Cheer Reveal".into() },
            O_ACTIVATE_MEMBER => if l == "jp" { "アクティブにする".into() } else { "Untap".into() },
            O_ADD_TO_HAND => if l == "jp" { "手札に加える".into() } else { "To Hand".into() },
            O_COLOR_SELECT => if l == "jp" { "色選択".into() } else { "Color Select".into() },
            // O_REPLACE_EFFECT removed as it is not a valid opcode
            O_TRIGGER_REMOTE => if l == "jp" { "リモート能力".into() } else { "Trigger".into() },
            O_REDUCE_HEART_REQ => if l == "jp" { "ハート条件変更".into() } else { "Reduce Heart".into() },
            O_MODIFY_SCORE_RULE => if l == "jp" { "スコア計算変更".into() } else { "Score Mod".into() },
            O_TAP_MEMBER => if l == "jp" { "ウェイトにする".into() } else { "Tap".into() },
            O_PLAY_MEMBER_FROM_HAND => if l == "jp" { "登場させる".into() } else { "Play".into() },
            O_MOVE_TO_DISCARD => if l == "jp" { "控え室に置く".into() } else { "Discard".into() },
            O_GRANT_ABILITY => if l == "jp" { "能力付与".into() } else { "Grant".into() },
            O_INCREASE_HEART_COST => if l == "jp" { "ハート増加".into() } else { "Incr Heart".into() },
            O_REDUCE_YELL_COUNT => if l == "jp" { "エール数軽減".into() } else { "Reduce Yell".into() },
            O_PLAY_MEMBER_FROM_DISCARD => if l == "jp" { "控えから登場".into() } else { "Play Discard".into() },
            O_PAY_ENERGY => if l == "jp" { "エネルギーを支払う".into() } else { "Pay Energy".into() },
            O_SELECT_MEMBER => if l == "jp" { "メンバー選択".into() } else { "Select Member".into() },
            O_DRAW_UNTIL => if l == "jp" { "枚数になるまで引く".into() } else { "Draw Until".into() },
            O_SELECT_PLAYER => if l == "jp" { "プレイヤー選択".into() } else { "Select Player".into() },
            O_SELECT_LIVE => if l == "jp" { "ライブ選択".into() } else { "Select Live".into() },
            O_REVEAL_UNTIL => if l == "jp" { "条件まで公開".into() } else { "Reveal Until".into() },
            O_INCREASE_COST => if l == "jp" { "コスト増加".into() } else { "Incr Cost".into() },
            O_PREVENT_PLAY_TO_SLOT => if l == "jp" { "プレイ制限".into() } else { "No Play".into() },
            O_SWAP_AREA => if l == "jp" { "エリア移動".into() } else { "Swap Area".into() },
            O_TRANSFORM_HEART => if l == "jp" { "ハート変換".into() } else { "Transf Heart".into() },
            O_SELECT_CARDS => if l == "jp" { "カード選択".into() } else { "Select Cards".into() },
            O_OPPONENT_CHOOSE => if l == "jp" { "相手が選ぶ".into() } else { "Opp Choose".into() },
            O_PLAY_LIVE_FROM_DISCARD => if l == "jp" { "控えからライブ".into() } else { "Play Live Discard".into() },
            O_REDUCE_LIVE_SET_LIMIT => if l == "jp" { "ライブ制限変更".into() } else { "Live Limit".into() },
            O_PREVENT_SET_TO_SUCCESS_PILE => if l == "jp" { "成功制限".into() } else { "No Success".into() },
            O_ACTIVATE_ENERGY => if l == "jp" { "エネルギー回復".into() } else { "Untap Energy".into() },
            O_PREVENT_ACTIVATE => if l == "jp" { "起動制限".into() } else { "No Act".into() },
            O_SET_HEART_COST => if l == "jp" { "ハート固定".into() } else { "Set Heart Cost".into() },
            O_PREVENT_BATON_TOUCH => if l == "jp" { "バトン制限".into() } else { "No Baton".into() },
            _ => format!("Eff {}", etype)
        }
    };

    let eff_list = effects.unwrap();
    let eff0 = &eff_list[0];
    let etype0 = eff0.get("effect_type").and_then(|v| v.as_i64()).unwrap_or(-1);
    let target = eff0.get("target").and_then(|v| v.as_i64()).unwrap_or(0);
    let val = eff0.get("value").and_then(|v| v.as_i64()).unwrap_or(0);

    let tg_name: String = if lang == "jp" {
        match target {
            1 => "自分".into(),
            2 => "相手".into(),
            6 => "手札へ".into(),
            _ => "全体".into(),
        }
    } else {
        match target {
            1 => "Self".into(),
            2 => "Opponent".into(),
            6 => "To Hand".into(),
            _ => "All".into(),
        }
    };

    let eff_name = get_eff_name(etype0, lang);
    let val_str = if val > 0 { format!(": {}", val) } else { "".to_string() };

    format!("{}{}{}: {}{}", trigger_prefix, cost_str, tg_name, eff_name, val_str)
}

pub fn get_action_desc_rich(
    id: i32,
    gs: &GameState,
    db: &CardDatabase,
    viewer_idx: usize,
    lang: &str
) -> (String, String, String, Option<usize>, HashMap<String, Value>) {
    use crate::models::Action;
    use engine_rust::core::logic::Phase;

    // Use active player for most actions, but allow viewer_idx for responses if they match
    let active_idx = gs.current_player;
    let p_idx = if gs.phase == Phase::Response {
        gs.interaction_stack.last().map(|p| p.ctx.player_id as usize).unwrap_or(active_idx as usize)
    } else {
        active_idx as usize
    };
    let p = &gs.players[p_idx];

    let action = Action::from_id(id, gs.phase);
    let mut metadata = HashMap::new();

    let (name, text, type_str, area_idx_opt) = match action {
        Action::Pass => {
            let (name, text) = match gs.phase {
                Phase::PerformanceP1 | Phase::PerformanceP2 => {
                    if lang == "jp" { ("【開始】パフォーマンス".into(), "パフォーマンスを開始します。".into()) }
                    else { ("Perform Live".into(), "Start the performance check.".into()) }
                },
                Phase::LiveResult => {
                    if lang == "jp" { ("【完了】次へ".into(), "結果を確認して次へ進みます。".into()) }
                    else { ("Finish Performance".into(), "Confirm results and proceed.".into()) }
                },
                Phase::MulliganP1 | Phase::MulliganP2 => {
                    if lang == "jp" { ("【確定】マリガン".into(), "手札を確定してマリガンを終了します。".into()) }
                    else { ("Confirm Mulligan".into(), "Finish Mulligan and start the game.".into()) }
                },
                Phase::LiveSet => {
                    if lang == "jp" { ("【確定】セット完了".into(), "ライブカードのセットを終了します。".into()) }
                    else { ("Confirm Live Set".into(), "Finish setting cards for the live zone.".into()) }
                },
                _ => {
                    let pending = gs.interaction_stack.last();
                    let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);
                    let mut name = if lang == "jp" { "【スキップ】パス".into() } else { "Pass / Confirm".into() };
                    let mut desc = if lang == "jp" { "何もしない。".into() } else { "Skip or confirm current action.".into() };

                     if gs.phase == Phase::Response {
                        let is_tap = opcode == engine_rust::core::generated_constants::O_TAP_MEMBER || opcode == engine_rust::core::generated_constants::O_TAP_OPPONENT;
                        if opcode == engine_rust::core::generated_constants::O_PAY_ENERGY || opcode == engine_rust::core::generated_constants::O_MOVE_TO_DISCARD || is_tap {
                             name = if lang == "jp" { "いいえ".into() } else { "No / Skip".into() };
                             desc = if lang == "jp" { "能力やコストの支払いをキャンセルします。".into() } else { "Decline the effect or cost.".into() };
                        }
                    }

                    (name, desc)
                }
            };
            (name, text, "PASS".into(), None)
        },
        Action::ToggleMulligan { hand_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card_name = if let Some(m) = db.get_member(cid) {
                format!("{} ({})", m.name, m.card_no)
            } else if let Some(l) = db.get_live(cid) {
                format!("{} ({})", l.name, l.card_no)
            } else if cid == -1 {
                "Card".to_string()
            } else {
                format!("Card #{}", cid)
            };

            let (label, desc) = if lang == "jp" {
                (format!("【マリガン】{}", card_name), "このカードをデッキに戻して引き直します。".into())
            } else {
                (format!("Mulligan: {}", card_name), "Return this card to deck and draw a new one.".into())
            };
            metadata.insert("hand_idx".into(), json!(hand_idx));
            (label, desc, "MULLIGAN".into(), None)
        },
        Action::PlayMember { hand_idx, slot_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card = if cid != -1 { db.get_member(cid) } else { None };
            let lang_data = if lang == "jp" {
                ("左", "中", "右", "登場", "に置く", "バトンタッチ", "退場", "支払", "コスト")
            } else {
                ("Left", "Mid", "Right", "On Play", "to", "Baton Touch", "leaves", "Pay", "Cost")
            };
            let (_l_name, _c_name, _r_name, suffix_str, _to_str, baton_str, leaves_str, pay_str, cost_str) = lang_data;

            let raw_name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
            let card_no = card.map(|m| m.card_no.clone()).unwrap_or_else(|| "??".into());
            let suffix = if let Some(m) = card {
                 if m.abilities.iter().any(|ab| ab.trigger == engine_rust::core::enums::TriggerType::OnPlay) { format!(" [{}]", suffix_str) } else { "".into() }
            } else { "".into() };

            let new_cost = card.map(|m| m.cost as i32).unwrap_or(0);
            let prev_cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let mut old_name = "".to_string();
            let base_cost = (new_cost - p.cost_reduction as i32).max(0);
            let mut actual_cost = base_cost;
            if prev_cid >= 0 {
                if let Some(old_m) = db.get_member(prev_cid) {
                    old_name = old_m.name.clone();
                    actual_cost = (base_cost - old_m.cost as i32).max(0);
                }
            }

            let label = if lang == "jp" {
                if prev_cid >= 0 {
                    format!("{} ({}){} ({}: {} {}, {}:{})", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                } else {
                    format!("{} ({}){} ({} {})", raw_name, card_no, suffix, cost_str, actual_cost)
                }
            } else {
                if prev_cid >= 0 {
                    format!("{} ({}){} ({}: {} {}, {}:{})", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                } else {
                    format!("{} ({}){} ({} {})", raw_name, card_no, suffix, cost_str, actual_cost)
                }
            };

            let cost_label = if lang == "jp" {
                if prev_cid >= 0 { format!("({}: {} {}, {}:{})", baton_str, old_name, leaves_str, pay_str, actual_cost) }
                else { format!("({} {})", cost_str, actual_cost) }
            } else {
                if prev_cid >= 0 { format!("({}: {} {}, {}:{})", baton_str, old_name, leaves_str, pay_str, actual_cost) }
                else { format!("({} {})", cost_str, actual_cost) }
            };

            let card_name_full = resolve_card_name(cid, db, lang);
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("full_label".into(), json!(label.clone()));
            metadata.insert("cost_label".into(), json!(cost_label));
            metadata.insert("cost".into(), json!(actual_cost));
            metadata.insert("name".into(), json!(card_name_full));
            metadata.insert("card_id".into(), json!(cid));
            (label, card.map(|m| m.original_text.clone()).unwrap_or_default(), "PLAY".into(), Some(slot_idx))
        },
        Action::PlayMemberDouble { hand_idx, slot_idx, other_slot } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card = if cid != -1 { db.get_member(cid) } else { None };
            let lang_data = if lang == "jp" {
                ("左", "中", "右", "登場", "に置く", "バトンタッチ", "退場", "支払", "コスト")
            } else {
                ("Left", "Mid", "Right", "On Play", "to", "Baton Touch", "leaves", "Pay", "Cost")
            };
            let (l_name, c_name, r_name, suffix_str, _to_str, baton_str, leaves_str, pay_str, _cost_str) = lang_data;
            let areas = [l_name, c_name, r_name];

            let raw_name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
            let card_no = card.map(|m| m.card_no.clone()).unwrap_or_else(|| "??".into());
            let suffix = if let Some(m) = card {
                 if m.abilities.iter().any(|ab| ab.trigger == engine_rust::core::enums::TriggerType::OnPlay) { format!(" [{}]", suffix_str) } else { "".into() }
            } else { "".into() };

            let new_cost = card.map(|m| m.cost as i32).unwrap_or(0);
            let prev1 = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let prev2 = p.stage.get(other_slot).cloned().unwrap_or(-1);

            let mut old_names = Vec::new();
            let mut reduction = 0;
            if let Some(m1) = if prev1 >= 0 { db.get_member(prev1) } else { None } {
                old_names.push(m1.name.clone());
                reduction += m1.cost as i32;
            }
            if let Some(m2) = if prev2 >= 0 { db.get_member(prev2) } else { None } {
                old_names.push(m2.name.clone());
                reduction += m2.cost as i32;
            }

            let base_cost = (new_cost - p.cost_reduction as i32).max(0);
            let actual_cost = (base_cost - reduction).max(0);

            let old_names_str = old_names.join(if lang == "jp" { "＆" } else { " & " });
            let target_area = areas.get(slot_idx).unwrap_or(&"");
            let pair_desc = format!("{} & {}", areas.get(slot_idx).unwrap_or(&""), areas.get(other_slot).unwrap_or(&""));
            let areas_desc = format!("({}) -> {}", pair_desc, target_area);

            let label = format!("{} ({}){} ({}: {} {}, {}:{}, {}: {})", raw_name, card_no, suffix, baton_str, old_names_str, leaves_str, pay_str, actual_cost, if lang == "jp" { "移動先" } else { "To" }, target_area);

            let cost_label = format!("({}: {} {}, {}:{})", baton_str, old_names_str, leaves_str, pay_str, actual_cost);

            let card_name_full = resolve_card_name(cid, db, lang);
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("secondary_slot_idx".into(), json!(other_slot));
            metadata.insert("full_label".into(), json!(label.clone()));
            metadata.insert("cost_label".into(), json!(cost_label));
            metadata.insert("cost".into(), json!(actual_cost));
            metadata.insert("name".into(), json!(card_name_full));
            metadata.insert("target_player".into(), json!(viewer_idx));
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("areas_desc".into(), json!(areas_desc));
            metadata.insert("card_id".into(), json!(cid));
            (label, card.map(|m| m.original_text.clone()).unwrap_or_default(), "PLAY".into(), Some(slot_idx))
        },
        Action::ActivateAbility { slot_idx, ab_idx } => {
            let cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let card = if cid >= 0 { db.get_member(cid) } else { None };
            let name = card.map(|m| format!("{} ({})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" { "アビリティ".into() } else { "Ability".into() });

            let areas = if lang == "jp" { ["左", "中", "右"] } else { ["Left", "Mid", "Right"] };
            let area_name = areas.get(slot_idx).unwrap_or(&"");

            let label = if lang == "jp" {
                format!("{}: {} ({})", name, summary, area_name)
            } else {
                format!("Use {}: {} ({})", name, summary, area_name)
            };
            metadata.insert("category".into(), json!("ABILITY"));
            metadata.insert("target_player".into(), json!(viewer_idx));
            metadata.insert("card_id".into(), json!(cid));
            (label, resolve_card_desc(cid, db), "ABILITY".into(), Some(slot_idx))
        },
        Action::ActivateFromHand { hand_idx, ab_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card = if cid >= 0 { db.get_member(cid) } else { None };
            let name = card.map(|m| format!("{} ({})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" { "アビリティ".into() } else { "Ability".into() });

            let label = if lang == "jp" {
                format!("{}: {} (手札)", name, summary)
            } else {
                format!("Use {}: {} (Hand)", name, summary)
            };
            metadata.insert("category".into(), json!("HAND_ABILITY"));
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            metadata.insert("card_id".into(), json!(cid));
            metadata.insert("target_player".into(), json!(viewer_idx)); // Added for consistency
            (label, resolve_card_desc(cid, db), "ABILITY".into(), None)
        },

        Action::SelectChoice { choice_idx } => {
             let mut name = String::new();
             let text = String::new();
             let type_str = "CHOICE".to_string();

             let pending = gs.interaction_stack.last();
             let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);
             let card_id = pending.map(|p| p.card_id).unwrap_or(-1);
             let ab_idx = pending.map(|p| p.ability_index).unwrap_or(-1);

             if gs.phase == Phase::LiveResult {
                 name = if lang == "jp" { format!("第{}枠を選択", choice_idx + 1) } else { format!("Select Slot {}", choice_idx + 1) };
             } else if opcode == O_SELECT_MODE {
                   let member = if card_id >= 0 { db.get_member(card_id) } else { None };
                   let live = if member.is_none() && card_id >= 0 { db.get_live(card_id) } else { None };

                   let ab = if let Some(m) = member {
                       m.abilities.get(ab_idx as usize)
                   } else if let Some(l) = live {
                       l.abilities.get(ab_idx as usize)
                   } else {
                       None
                   };

                   if let Some(ab) = ab {
                       if choice_idx < ab.option_names.len() {
                           name = ab.option_names[choice_idx].clone();
                       } else if let Some(arr) = ab.modal_options.as_array() {
                           if !arr.is_empty() {
                               if let Some(opt) = arr.get(choice_idx) {
                                   if let Some(s) = opt.as_str() {
                                       let source_name = if let Some(m) = member { m.name.clone() } else if let Some(l) = live { l.name.clone() } else { String::new() };
                                       if !source_name.is_empty() {
                                           name = if lang == "jp" { format!("{} ({})", s, source_name) } else { format!("{} ({})", s, source_name) };
                                       } else {
                                           name = s.to_string();
                                       }
                                   }
                               }
                        } else {
                            // Fallback: Peek into bytecode if no modal_options strings
                            // Each instruction is 5 words in the Rust engine.
                            let instr_ip = pending.map(|p| p.ctx.program_counter).unwrap_or(0) as usize;
                            if instr_ip + 5 + (choice_idx * 5) + 1 < ab.bytecode.len() {
                                // For SELECT_MODE, Choice i is followed by an O_JUMP instruction at instr_ip + 5 + i*5
                                let mut jump_instr_ip = instr_ip + 5 + (choice_idx * 5);

                                // Recursive Jump Following (Safety Limit: 5)
                                for _ in 0..5 {
                                    if jump_instr_ip + 1 >= ab.bytecode.len() { break; }
                                    let jump_op = ab.bytecode[jump_instr_ip];
                                    if jump_op == engine_rust::core::generated_constants::O_JUMP {
                                        let jump_val = ab.bytecode[jump_instr_ip + 1] as usize;
                                        // The target is jump_instr_ip + 5 (chunk) + jump_val chunks
                                        let target_instr_ip = jump_instr_ip + 5 + (jump_val * 5);
                                        if target_instr_ip + 1 < ab.bytecode.len() {
                                            let op = ab.bytecode[target_instr_ip] as i32;
                                            let val = ab.bytecode[target_instr_ip + 1];

                                            // Handle various opcodes
                                            match op {
                                                O_PAY_ENERGY | O_PAY_ENERGY_DYNAMIC => {
                                                    name = if lang == "jp" {
                                                        format!("{{{{icon_energy.png|E}}}}{}支払う", val)
                                                    } else {
                                                        format!("Pay {}{{{{icon_energy.png|E}}}}", val)
                                                    };
                                                    break;
                                                },
                                                O_MOVE_TO_DISCARD => {
                                                    let slot = ab.bytecode[target_instr_ip + 4];
                                                    if slot == engine_rust::core::enums::TargetType::CardHand as i32 {
                                                        name = if lang == "jp" { format!("手札を{}枚捨てる", val) } else { format!("Discard {} Hand", val) };
                                                    } else {
                                                        name = if lang == "jp" { format!("{}枚捨てる", val) } else { format!("Discard {}", val) };
                                                    }
                                                    break;
                                                },
                                                O_DRAW => {
                                                    name = if lang == "jp" { format!("{{{{icon_draw.png|D}}}}{}枚引く", val) } else { format!("Draw {}{{{{icon_draw.png|D}}}}", val) };
                                                    break;
                                                },
                                                O_ADD_BLADES => {
                                                    name = if lang == "jp" { format!("ボルテージ+{}", val) } else { format!("Voltage+{}", val) };
                                                    break;
                                                },
                                                O_ADD_HEARTS => {
                                                    name = if lang == "jp" { format!("ピース+{}", val) } else { format!("Hearts+{}", val) };
                                                    break;
                                                },
                                                O_TAP_MEMBER => {
                                                    name = if lang == "jp" { "メンバーをタップ".into() } else { "Tap Member".into() };
                                                    break;
                                                },
                                                O_TAP_OPPONENT => {
                                                    name = if lang == "jp" { "相手をタップ".into() } else { "Tap Opponent".into() };
                                                    break;
                                                },
                                                O_ACTIVATE_MEMBER => {
                                                    name = if lang == "jp" { "アピールにする".into() } else { "Untap/Ready".into() };
                                                    break;
                                                },
                                                O_BOOST_SCORE => {
                                                    name = if lang == "jp" { format!("ブースト+{}", val) } else { format!("Boost+{}", val) };
                                                    break;
                                                },
                                                O_RECOVER_MEMBER | O_RECOVER_LIVE => {
                                                    name = if lang == "jp" { "回収".into() } else { "Recover".into() };
                                                    break;
                                                },
                                                O_SEARCH_DECK | O_LOOK_DECK => {
                                                    name = if lang == "jp" { "デッキを見る".into() } else { "Look at Deck".into() };
                                                    break;
                                                },
                                                O_JUMP => {
                                                    // Follow nested jump
                                                    jump_instr_ip = target_instr_ip;
                                                    continue;
                                                }
                                                _ => { break; }
                                            }
                                        } else { break; }
                                    } else { break; }
                                }
                            }
                        }
                       }
                   }
             } else if opcode == O_TAP_OPPONENT || opcode == O_OPPONENT_CHOOSE {
                  let opp_idx = 1 - p_idx;
                  let cid = gs.players[opp_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {
                      name = if lang == "jp" { format!("タップ: {}", resolve_card_name(cid, db, lang)) } else { format!("Tap: {}", resolve_card_name(cid, db, lang)) };
                  } else {
                      let areas = if lang == "jp" { ["相手の左枠", "相手の中枠", "相手の右枠"] } else { ["Opponent's Left Slot", "Opponent's Mid Slot", "Opponent's Right Slot"] };
                      name = areas.get(choice_idx).unwrap_or(&"Slot").to_string();
                  }
             } else if opcode == O_PLAY_MEMBER_FROM_HAND || opcode == O_PLAY_MEMBER_FROM_DISCARD || opcode == O_PLAY_LIVE_FROM_DISCARD {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  if choice_type == "SELECT_STAGE" || choice_type == "SELECT_STAGE_EMPTY" {
                      let areas = if lang == "jp" { ["左枠", "中央枠", "右枠"] } else { ["Left Slot", "Mid Slot", "Right Slot"] };
                      name = areas.get(choice_idx).unwrap_or(&"Slot").to_string();
                  } else if choice_type == "SELECT_LIVE_SLOT" {
                      let areas = if lang == "jp" { ["ライブ枠 1", "ライブ枠 2", "ライブ枠 3"] } else { ["Live Slot 1", "Live Slot 2", "Live Slot 3"] };
                      name = areas.get(choice_idx).unwrap_or(&"Slot").to_string();
                  } else if choice_type == "SELECT_HAND_PLAY" || choice_type == "SELECT_DISCARD_PLAY" {
                      // These steps pick a CARD id from hand or discard
                      let cid = if choice_type == "SELECT_HAND_PLAY" {
                          gs.players[p_idx].hand.get(choice_idx).cloned().unwrap_or(-1)
                      } else {
                          gs.players[p_idx].looked_cards.get(choice_idx).cloned().unwrap_or(-1)
                      };
                      if cid >= 0 { name = resolve_card_name(cid, db, lang); }
                  }
             } else if opcode == O_SELECT_MEMBER || opcode == O_TAP_MEMBER || opcode == O_SET_TAPPED || opcode == O_ACTIVATE_MEMBER || opcode == O_SWAP_AREA {
                  let cid = gs.players[p_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {
                      name = resolve_card_name(cid, db, lang);
                  }
             } else if opcode == O_SELECT_LIVE {
                  let cid = gs.players[p_idx].live_zone.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {
                      name = resolve_card_name(cid, db, lang);
                  }
             } else if opcode == O_SELECT_PLAYER {
                  name = if choice_idx == 0 {
                      if lang == "jp" { "自分".into() } else { "Self".into() }
                  } else {
                      if lang == "jp" { "相手".into() } else { "Opponent".into() }
                  };
              } else if opcode == O_RECOVER_LIVE || opcode == O_RECOVER_MEMBER || opcode == O_ORDER_DECK || opcode == O_PLAY_MEMBER_FROM_DISCARD || opcode == O_PLAY_LIVE_FROM_DISCARD {
                 if let Some(cid) = gs.players[p_idx].looked_cards.get(choice_idx) {
                     name = resolve_card_name(*cid, db, lang);
                 }
                 if let Some(pi) = pending {
                     let filter_desc = get_filter_description(pi.filter_attr, lang);
                     if !filter_desc.is_empty() {
                         name = if lang == "jp" { format!("【{}】{}", filter_desc, name) } else { format!("{}: {}", filter_desc, name) };
                     }
                 }
              } else if opcode == O_SELECT_CARDS || opcode == O_LOOK_AND_CHOOSE {
                  if let Some(cid) = gs.players[p_idx].looked_cards.get(choice_idx) {
                      name = resolve_card_name(*cid, db, lang);
                  }
                  if let Some(pi) = pending {
                      let filter_desc = get_filter_description(pi.filter_attr, lang);
                      if !filter_desc.is_empty() {
                          name = format!("【{}】{}", filter_desc, name);
                      }
                  }
               } else if opcode == O_MOVE_TO_DISCARD || opcode == O_PLAY_MEMBER_FROM_HAND {
                  if let Some(cid) = gs.players[p_idx].hand.get(choice_idx) {
                      name = resolve_card_name(*cid, db, lang);
                  }
                  if let Some(pi) = pending {
                      let filter_desc = get_filter_description(pi.filter_attr, lang);
                      if !filter_desc.is_empty() {
                          name = if lang == "jp" { format!("【{}】{}", filter_desc, name) } else { format!("{}: {}", filter_desc, name) };
                      }
                  }
              } else if opcode == O_SWAP_ZONE {
                   let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                   if choice_type == "SELECT_SWAP_SOURCE" {
                       if let Some(cid) = gs.players[p_idx].success_lives.get(choice_idx) {
                           name = resolve_card_name(*cid, db, lang);
                       }
                   } else if choice_type == "SELECT_SWAP_TARGET" {
                       if let Some(cid) = gs.players[p_idx].hand.get(choice_idx) {
                           name = resolve_card_name(*cid, db, lang);
                       }
                   }
              } else if opcode == O_LOOK_DECK || opcode == O_REVEAL_CARDS || opcode == O_CHEER_REVEAL {
                   let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                   if choice_type == "REVEAL_HAND" {
                       if let Some(cid) = gs.players[p_idx].hand.get(choice_idx) {
                           name = resolve_card_name(*cid, db, lang);
                       }
                   } else {
                       if let Some(cid) = gs.players[p_idx].looked_cards.get(choice_idx) {
                           name = resolve_card_name(*cid, db, lang);
                       }
                   }
              } else if opcode == O_PAY_ENERGY {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  if choice_type == "OPTIONAL" {
                      name = if lang == "jp" { "はい".into() } else { "Yes / Pay".into() };
                  } else {
                      if let Some(cid) = gs.players[p_idx].energy_zone.get(choice_idx) {
                          name = resolve_card_name(*cid, db, lang);
                      }
                  }
              }

              if name.is_empty() {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  if choice_type == "OPTIONAL" && choice_idx == 0 {
                      name = if lang == "jp" { "はい".into() } else { "Yes".into() };
                  } else {
                      name = if lang == "jp" { format!("選択肢 {}", choice_idx + 1) } else { format!("Choice {}", choice_idx + 1) };
                  }
              }
              metadata.insert("choice_idx".into(), json!(choice_idx));
              metadata.insert("opcode".into(), json!(opcode));
              metadata.insert("category".into(), json!("CHOICE"));

              // For opcodes that target stage slots, re-add slot_idx so frontend can highlight
              if opcode == O_TAP_OPPONENT {
                  metadata.insert("slot_idx".into(), json!(choice_idx));
                  metadata.insert("target_player".into(), json!(1 - viewer_idx));
              } else if opcode == O_SELECT_MEMBER || opcode == O_TAP_MEMBER || opcode == O_SET_TAPPED || opcode == O_ACTIVATE_MEMBER || opcode == O_SWAP_AREA {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  let s_idx = if choice_type == "OPTIONAL" {
                      pending.map(|p| p.target_slot).unwrap_or(0)
                  } else {
                      choice_idx as i32
                  };
                  metadata.insert("slot_idx".into(), json!(s_idx));
                  metadata.insert("target_player".into(), json!(viewer_idx));
              } else if opcode == O_MOVE_TO_DISCARD || opcode == O_PLAY_MEMBER_FROM_HAND || opcode == O_LOOK_DECK || opcode == O_REVEAL_CARDS || opcode == O_SWAP_ZONE {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  if choice_type == "REVEAL_HAND" || choice_type == "SELECT_SWAP_TARGET" || opcode == O_MOVE_TO_DISCARD || opcode == O_PLAY_MEMBER_FROM_HAND {
                      metadata.insert("hand_idx".into(), json!(choice_idx));
                      metadata.insert("target_player".into(), json!(viewer_idx));
                  }
              } else if opcode == O_SELECT_LIVE || opcode == O_RECOVER_LIVE {
                  metadata.insert("slot_idx".into(), json!(choice_idx));
                  metadata.insert("category".into(), json!("LIVE"));
                  metadata.insert("target_player".into(), json!(viewer_idx));
              } else if opcode == O_PAY_ENERGY || opcode == O_ACTIVATE_ENERGY || opcode == O_ENERGY_CHARGE {
                  metadata.insert("energy_idx".into(), json!(choice_idx));
                  metadata.insert("target_player".into(), json!(viewer_idx));
              } else if opcode == O_PLAY_MEMBER_FROM_DISCARD || opcode == O_PLAY_LIVE_FROM_DISCARD {
                  metadata.insert("discard_idx".into(), json!(choice_idx));
                  metadata.insert("category".into(), json!("DISCARD"));
                  metadata.insert("target_player".into(), json!(viewer_idx));
              }

              let highlight_idx = if opcode == O_SELECT_MEMBER || opcode == O_TAP_OPPONENT || opcode == O_SET_TAPPED || opcode == O_TAP_MEMBER {
                  let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                  if choice_type == "OPTIONAL" {
                      Some(pending.map(|p| p.target_slot as usize).unwrap_or(0))
                  } else {
                      Some(choice_idx)
                  }
              } else {
                  None
              };
             (name, text, type_str, highlight_idx)
        },
        Action::SelectEnergy { energy_idx } => {
            let cid = p.energy_zone.get(energy_idx).cloned().unwrap_or(-1);
            let name = resolve_card_name(cid, db, lang);
            let text = if lang == "jp" { "コストとして支払います。".to_string() } else { "Pay as cost.".to_string() };
            let type_str = "ENERGY".to_string();
            metadata.insert("energy_idx".into(), json!(energy_idx));
            metadata.insert("category".into(), json!("ENERGY"));
            metadata.insert("card_id".into(), json!(cid));
            (name, text, type_str, None)
        },
        Action::SelectHand { hand_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card_name = if let Some(m) = db.get_member(cid) {
                format!("{} ({})", m.name, m.card_no)
            } else if let Some(l) = db.get_live(cid) {
                l.name.clone()
            } else { "Card".to_string() };

            let mut desc = if lang == "jp" { "このカードを選択します。".to_string() } else { "Select this card.".to_string() };
            let mut label_prefix = if lang == "jp" { "【選択】".to_string() } else { "Select: ".to_string() };

            let pending = gs.interaction_stack.last();
            let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);

            if gs.phase == Phase::Response {
                if opcode == O_RECOVER_LIVE || opcode == O_RECOVER_MEMBER {
                    label_prefix = if lang == "jp" { "【回収】".to_string() } else { "Recover: ".to_string() };
                    desc = if lang == "jp" { "このカードを手札に戻します。".to_string() } else { "Return this card to hand.".to_string() };
                } else if opcode == O_MOVE_TO_DISCARD {
                    label_prefix = if lang == "jp" { "【控え室】".to_string() } else { "Discard: ".to_string() };
                    desc = if lang == "jp" { "このカードを控え室に置きます。".to_string() } else { "Put this card into the discard pile.".to_string() };
                }

                if let Some(pi) = pending {
                    let filter_desc = get_filter_description(pi.filter_attr, lang);
                    if !filter_desc.is_empty() {
                        label_prefix = if lang == "jp" { format!("【{}】", filter_desc) } else { format!("{}: ", filter_desc) };
                    }
                }
            }

            let label = if lang == "jp" && label_prefix.starts_with("【") {
                format!("{}{}", label_prefix, card_name)
            } else {
                format!("{}{}", label_prefix, card_name)
            };
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("category".into(), json!("SELECT"));
            metadata.insert("opcode".into(), json!(opcode));
            (label, desc, "SELECT".into(), None)
        },
        Action::SelectResponseSlot { slot_idx } => {
            let pending = gs.interaction_stack.last();
            let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);

            let target_player = if opcode == O_TAP_OPPONENT { 1 - viewer_idx } else { viewer_idx };

            let cid = if opcode == O_SELECT_LIVE {
                gs.players[target_player].live_zone.get(slot_idx).cloned().unwrap_or(-1)
            } else {
                gs.players[target_player].stage.get(slot_idx).cloned().unwrap_or(-1)
            };

            let card_name = if cid >= 0 { resolve_card_name(cid, db, lang) } else { "".to_string() };
            let areas = if lang == "jp" { ["左", "中", "右"] } else { ["Left", "Mid", "Right"] };
            let label = if lang == "jp" {
                if card_name.is_empty() { format!("{}枠を選択", areas.get(slot_idx).unwrap_or(&"")) }
                else { format!("{} ({})", card_name, areas.get(slot_idx).unwrap_or(&"")) }
            } else {
                if card_name.is_empty() { format!("Select {} Slot", areas.get(slot_idx).unwrap_or(&"")) }
                else { format!("{} ({})", card_name, areas.get(slot_idx).unwrap_or(&"")) }
            };
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("target_player".into(), json!(target_player));
            (label, "".into(), "SELECT".into(), Some(slot_idx))
        },
        Action::SelectResponseColor { color_idx } => {
            let colors = if lang == "jp" { ["ピンク", "赤", "黄", "緑", "青", "紫"] } else { ["Pink", "Red", "Yellow", "Green", "Blue", "Purple"] };
            let label = if lang == "jp" { format!("【色を選択】{}", colors.get(color_idx as usize).unwrap_or(&"")) } else { format!("Choose {}", colors.get(color_idx as usize).unwrap_or(&"")) };
            metadata.insert("color_idx".into(), json!(color_idx));
            (label, "".into(), "COLOR".into(), None)
        },
        Action::ActivateAbilityWithChoice { slot_idx, ab_idx, choice_idx } => {
            let cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let card = if cid >= 0 { db.get_member(cid) } else { None };
            let mut name = card.map(|m| format!("{} ({})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" { "アビリティ".into() } else { "Ability".into() });

            let pending = gs.interaction_stack.last();
            let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);

            if gs.phase == Phase::Response {
                if opcode == O_LOOK_AND_CHOOSE || opcode == O_SELECT_CARDS || opcode == O_RECOVER_LIVE || opcode == O_ORDER_DECK {
                    if let Some(cid) = gs.players[viewer_idx].looked_cards.get(choice_idx) {
                        name = resolve_card_name(*cid, db, lang);
                    }
                } else if opcode == O_MOVE_TO_DISCARD {
                    if let Some(&cid) = gs.players[viewer_idx].hand.get(choice_idx) {
                        name = resolve_card_name(cid, db, lang);
                    }
                } else if opcode == O_SELECT_MEMBER || opcode == O_TAP_MEMBER || opcode == O_SET_TAPPED || opcode == O_ACTIVATE_MEMBER || opcode == O_SWAP_AREA {
                     let sel_cid = gs.players[viewer_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid >= 0 { name = resolve_card_name(sel_cid, db, lang); }
                } else if opcode == O_SELECT_LIVE {
                     let sel_cid = gs.players[viewer_idx].live_zone.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid >= 0 { name = resolve_card_name(sel_cid, db, lang); }
                } else if opcode == O_TAP_OPPONENT {
                     let opp_idx = 1 - viewer_idx;
                     let sel_cid = gs.players[opp_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid >= 0 { name = format!("タップ: {}", resolve_card_name(sel_cid, db, lang)); }
                } else if opcode == O_SWAP_ZONE {
                     let choice_type = pending.map(|p| p.choice_type.as_str()).unwrap_or("");
                     if choice_type == "SELECT_SWAP_SOURCE" {
                         if let Some(cid) = gs.players[viewer_idx].success_lives.get(choice_idx) { name = resolve_card_name(*cid, db, lang); }
                     } else if choice_type == "SELECT_SWAP_TARGET" {
                         if let Some(cid) = gs.players[viewer_idx].hand.get(choice_idx) { name = resolve_card_name(*cid, db, lang); }
                     }
                }
            }

            let areas = if lang == "jp" { ["左", "中", "右"] } else { ["Left", "Mid", "Right"] };
            let area_name = areas.get(slot_idx).unwrap_or(&"");

            let label = if lang == "jp" {
                format!("【追加効果】{}: {} ({})", name, summary, area_name)
            } else {
                format!("Use {}: {} ({})", name, summary, area_name)
            };
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            metadata.insert("choice_idx".into(), json!(choice_idx));
            metadata.insert("card_id".into(), json!(cid));
            metadata.insert("category".into(), json!("ABILITY"));
            metadata.insert("opcode".into(), json!(opcode));
            metadata.insert("target_player".into(), json!(viewer_idx));
            (label, resolve_card_desc(cid, db), "ABILITY".into(), Some(slot_idx))
        },
        Action::PlayMemberWithChoice { hand_idx, slot_idx, choice_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let card = if cid != -1 { db.get_member(cid) } else { None };
             let lang_data = if lang == "jp" {
                ("左", "中", "右", "登場", "に置く", "バトンタッチ", "退場", "支払", "コスト")
             } else {
                ("Left", "Mid", "Right", "On Play", "to", "Baton Touch", "leaves", "Pay", "Cost")
             };
             let (_l_name, _c_name, _r_name, suffix_str, _to_str, baton_str, leaves_str, pay_str, cost_str) = lang_data;

             let raw_name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
             let card_no = card.map(|m| m.card_no.clone()).unwrap_or_else(|| "??".into());
             let suffix = if let Some(m) = card {
                  if m.abilities.iter().any(|ab| ab.trigger == engine_rust::core::enums::TriggerType::OnPlay) { format!(" [{}]", suffix_str) } else { "".into() }
             } else { "".into() };

             let new_cost = card.map(|m| m.cost as i32).unwrap_or(0);
             let prev_cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
             let mut old_name = "".to_string();
             let base_cost = (new_cost - p.cost_reduction as i32).max(0);
             let mut actual_cost = base_cost;
             if prev_cid >= 0 {
                 if let Some(old_m) = db.get_member(prev_cid) {
                     old_name = old_m.name.clone();
                     actual_cost = (base_cost - old_m.cost as i32).max(0);
                 }
             }

             let label = if lang == "jp" {
                 if prev_cid >= 0 {
                      format!("{} ({}){} ({}: {} {}, {}:{})*", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                 } else {
                     format!("{} ({}){} ({} {})*", raw_name, card_no, suffix, cost_str, actual_cost)
                 }
             } else {
                 if prev_cid >= 0 {
                      format!("{} ({}){} ({}: {} {}, {}:{})*", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                 } else {
                     format!("{} ({}){} ({} {})*", raw_name, card_no, suffix, cost_str, actual_cost)
                 }
             };

             let cost_label = if lang == "jp" {
                 if prev_cid >= 0 { format!("({}: {} {}, {}:{})", baton_str, old_name, leaves_str, pay_str, actual_cost) }
                 else { format!("({} {})", cost_str, actual_cost) }
             } else {
                 if prev_cid >= 0 { format!("({}: {} {}, {}:{})", baton_str, old_name, leaves_str, pay_str, actual_cost) }
                 else { format!("({} {})", cost_str, actual_cost) }
             };

             let card_name_full = card.map(|m| format!("{} ({})", m.name, m.card_no)).unwrap_or_else(|| {
                 if let Some(m) = db.get_member(cid) {
                    format!("{} ({})", m.name, m.card_no)
                 } else if let Some(l) = db.get_live(cid) {
                    l.name.clone()
                 } else {
                    format!("Card #{}", cid)
                 }
             });

             metadata.insert("hand_idx".into(), json!(hand_idx));
             metadata.insert("slot_idx".into(), json!(slot_idx));
             metadata.insert("choice_idx".into(), json!(choice_idx));
             metadata.insert("full_label".into(), json!(label.clone()));
             metadata.insert("cost_label".into(), json!(cost_label));
             metadata.insert("cost".into(), json!(actual_cost));
             metadata.insert("name".into(), json!(card_name_full));
             metadata.insert("card_id".into(), json!(cid));
             (label, card.map(|m| m.original_text.clone()).unwrap_or_default(), "PLAY".into(), Some(slot_idx))
        },
        Action::ActivateFromDiscard { discard_idx, ab_idx } => {
            let cid = p.discard.get(discard_idx).cloned().unwrap_or(-1);
            let card = if cid != -1 { db.get_member(cid) } else { None };
            let name = card.map(|m| format!("{} ({})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" { "アビリティ".into() } else { "Ability".into() });

            let (label, _desc): (String, String) = if lang == "jp" {
                (format!("【控え室から起動】{}: {}", name, summary), "控え室にあるこのカードの能力を使います。".into())
            } else {
                (format!("【Disc activated】{}: {}", name, summary), "Activate this card ability from discard pile.".into())
            };
            metadata.insert("discard_idx".into(), json!(discard_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            metadata.insert("card_id".into(), json!(cid));
            (label, resolve_card_desc(cid, db), "ABILITY".into(), None)
        },
        Action::PlaceLive { hand_idx } => {
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(-1);
            let name = resolve_card_name(cid, db, lang);
            let live_card = db.get_live(cid);

            let label = if lang == "jp" {
                format!("【セット】{}", name)
            } else {
                format!("Set Live: {}", name)
            };

            let mut desc = if let Some(l) = live_card {
                if !l.original_text.is_empty() {
                    l.original_text.clone()
                } else if !l.abilities.is_empty() {
                    get_ability_summary(&serde_json::to_value(&l.abilities[0]).unwrap(), lang)
                } else {
                    "".to_string()
                }
            } else {
                "".to_string()
            };

            if desc.is_empty() {
                desc = if lang == "jp" {
                    "このライブをライブゾーンにセットします。".to_string()
                } else {
                    "Set this live card to the live zone.".to_string()
                };
            }

            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("name".into(), json!(name));
            (label, desc, "LIVE_SET".into(), None)
        },
        Action::Rps { choice, .. } => {
            let choices = if lang == "jp" { ["グー", "パー", "チョキ"] } else { ["Rock", "Paper", "Scissors"] };
            let label = if lang == "jp" { format!("【じゃんけん】{}", choices.get(choice as usize).unwrap_or(&"")) } else { format!("Choose {}", choices.get(choice as usize).unwrap_or(&"")) };
            metadata.insert("choice".into(), json!(choice));
            (label, "".into(), "RPS".into(), None)
        },
        Action::ChooseTurnOrder { first } => {
            let label = if lang == "jp" {
                if first { "【選択】先攻" } else { "【選択】後攻" }
            } else {
                if first { "Go First" } else { "Go Second" }
            };
            metadata.insert("first".into(), json!(first));
            (label.into(), "".into(), "TURN_ORDER".into(), None)
        },
        Action::Formation { src_idx, dst_idx } => {
            let areas = if lang == "jp" { ["左", "中", "右"] } else { ["Left", "Mid", "Right"] };
            let (src_name, dst_name) = (areas.get(src_idx).unwrap_or(&"??"), areas.get(dst_idx).unwrap_or(&"??"));
            let label = if lang == "jp" {
                format!("【入れ替え】{} と {}", src_name, dst_name)
            } else {
                format!("Formation: Swap {} and {}", src_name, dst_name)
            };
            let text = if lang == "jp" {
                format!("{} 枠と {} 枠のメンバーを入れ替えます。", src_name, dst_name)
            } else {
                format!("Swap members between {} and {} slots.", src_name, dst_name)
            };
            metadata.insert("src_idx".into(), json!(src_idx));
            metadata.insert("dst_idx".into(), json!(dst_idx));
            metadata.insert("target_player".into(), json!(viewer_idx));
            (label, text, "FORMATION".into(), None)
        },
        _ => (format!("Action {}", id), "".into(), "OTHER".into(), None),
    };

    (name, text, type_str, area_idx_opt, metadata)
}

pub fn serialize_card(cid: i32, db: &CardDatabase, viewable: bool) -> Value {
    if cid == -1 { return json!(null); }
    // Use get_member/get_live which mask with TEMPLATE_MASK internally,
    // since the CID contains packed instance bits in the upper bits.
    let member = db.get_member(cid);
    let live = db.get_live(cid);

    let (name, ability, rare, img) = if let Some(m) = member {
        (m.name.clone(), m.original_text.clone(), "M".to_string(), m.img_path.clone())
    } else if let Some(l) = live {
        (l.name.clone(), l.original_text.clone(), "LIVE".to_string(), l.img_path.clone())
    } else {
        let template_id = cid;
        let e_name = db.energy_db.get(&template_id).map(|e| e.name.as_str()).unwrap_or("Energy");
        (e_name.to_string(), "".to_string(), "E".to_string(), "img/texticon/icon_energy.png".to_string())
    };

    if viewable {
        let is_member = member.is_some();
        let is_live = live.is_some();
        let mut obj = json!({
            "id": cid,
            "name": name,
            "ability": ability,
            "rarity": rare,
            "type": if is_member { "member" } else if is_live { "live" } else { "energy" },
            "img": img
        });
        if let Some(obj_map) = obj.as_object_mut() {
            if let Some(m) = member {
                obj_map.insert("cost".to_string(), json!(m.cost));
                obj_map.insert("hearts".to_string(), json!(m.hearts));
                obj_map.insert("blade_hearts".to_string(), json!(m.blade_hearts));
                obj_map.insert("volume_icons".to_string(), json!(m.note_icons));
                obj_map.insert("semantic_flags".to_string(), json!(m.semantic_flags));
                obj_map.insert("ability_flags".to_string(), json!(m.ability_flags));
                obj_map.insert("synergy_flags".to_string(), json!(m.synergy_flags));
                obj_map.insert("cost_flags".to_string(), json!(m.cost_flags));

                // Metadata Enrichments
                obj_map.insert("char_id".to_string(), json!(m.char_id));
                obj_map.insert("groups".to_string(), json!(m.groups));
                obj_map.insert("units".to_string(), json!(m.units));

                let group_names: Vec<&str> = m.groups.iter().map(|&g| get_group_name(g, "en")).collect();
                let unit_names: Vec<&str> = m.units.iter().map(|&u| get_unit_name(u, "en")).collect();
                obj_map.insert("group_names".to_string(), json!(group_names));
                obj_map.insert("unit_names".to_string(), json!(unit_names));

                let abilities: Vec<Value> = m.abilities.iter().map(|ab| {
                    let mut ab_val = serde_json::to_value(ab).unwrap();
                    if let Some(ab_obj) = ab_val.as_object_mut() {
                        ab_obj.insert("decoded_bytecode".to_string(), json!(decode_bytecode_to_strings(&ab.bytecode)));
                    }
                    ab_val
                }).collect();
                obj_map.insert("abilities".to_string(), json!(abilities));

                if !m.abilities.is_empty() {
                    obj_map.insert("pseudocode".to_string(), json!(m.abilities[0].pseudocode));
                }
            } else if let Some(l) = live {
                obj_map.insert("score".to_string(), json!(l.score));
                obj_map.insert("required_hearts".to_string(), json!(l.required_hearts));
                obj_map.insert("volume_icons".to_string(), json!(l.note_icons));
                obj_map.insert("blade_hearts".to_string(), json!(l.blade_hearts));
                obj_map.insert("semantic_flags".to_string(), json!(l.semantic_flags));
                obj_map.insert("synergy_flags".to_string(), json!(l.synergy_flags));

                // Metadata Enrichments
                obj_map.insert("groups".to_string(), json!(l.groups));
                obj_map.insert("units".to_string(), json!(l.units));

                let group_names: Vec<&str> = l.groups.iter().map(|&g| get_group_name(g, "en")).collect();
                let unit_names: Vec<&str> = l.units.iter().map(|&u| get_unit_name(u, "en")).collect();
                obj_map.insert("group_names".to_string(), json!(group_names));
                obj_map.insert("unit_names".to_string(), json!(unit_names));

                let abilities: Vec<Value> = l.abilities.iter().map(|ab| {
                    let mut ab_val = serde_json::to_value(ab).unwrap();
                    if let Some(ab_obj) = ab_val.as_object_mut() {
                        ab_obj.insert("decoded_bytecode".to_string(), json!(decode_bytecode_to_strings(&ab.bytecode)));
                    }
                    ab_val
                }).collect();
                obj_map.insert("abilities".to_string(), json!(abilities));

                if !l.abilities.is_empty() {
                    obj_map.insert("pseudocode".to_string(), json!(l.abilities[0].pseudocode));
                }
            }
        }
        obj
    } else {
        json!({ "id": -2, "hidden": true }) // Hidden
    }
}

pub fn serialize_player_rich(
    p: &PlayerState,
    gs: &GameState,
    db: &CardDatabase,
    p_idx: usize,
    viewer_idx: usize,
    legal_mask: &[bool]
) -> Value {
    let is_viewer = p_idx == viewer_idx;

    let viewer_is_acting = gs.current_player == viewer_idx as u8;

    let hand: Vec<Value> = p.hand.iter().enumerate().map(|(i, &cid)| {
        let mut v = serialize_card(cid as i32, db, p_idx == viewer_idx);
        if viewer_is_acting {
             if let Some(obj) = v.as_object_mut() {
                 // Positional indices for mulligan, live set, and hand selections
                 let mulligan_id = ACTION_BASE_MULLIGAN + i as i32;
                 if mulligan_id < legal_mask.len() as i32 && legal_mask[mulligan_id as usize] {
                     obj.insert("is_mulligan_legal".to_string(), json!(true));
                 }
                 let live_set_id = ACTION_BASE_LIVESET + i as i32;
                 if live_set_id < legal_mask.len() as i32 && legal_mask[live_set_id as usize] {
                     obj.insert("is_live_set_legal".to_string(), json!(true));
                 }
                 let select_id = ACTION_BASE_HAND_SELECT + i as i32;
                 let select_id_alt = ACTION_BASE_HAND + i as i32;
                 if (select_id < legal_mask.len() as i32 && legal_mask[select_id as usize]) ||
                    (select_id_alt < legal_mask.len() as i32 && legal_mask[select_id_alt as usize]) {
                     obj.insert("is_select_legal".to_string(), json!(true));
                 }

                 // Highlight playable cards in Main phase (Play actions use pos * 10 + slot)
                 if gs.phase == engine_rust::core::logic::Phase::Main && p_idx == viewer_idx {
                     let any_slot_legal = (0..3).any(|slot| {
                         let aid = ACTION_BASE_HAND + (i as i32 * 10) + slot;
                         aid < legal_mask.len() as i32 && legal_mask[aid as usize]
                     });
                     let any_choice_legal = (0..3).any(|slot| {
                         (0..10).any(|choice| {
                            let aid = ACTION_BASE_HAND_CHOICE + i as i32 * 100 + slot as i32 * 10 + choice;
                            aid < legal_mask.len() as i32 && legal_mask[aid as usize]
                         })
                     });

                     if any_slot_legal || any_choice_legal {
                         obj.insert("is_legal".to_string(), json!(true));
                     }
                 }
             }
        }
        v
    }).collect();

    let stage: Vec<Value> = p.stage.iter().enumerate().map(|(i, &cid)| {
        let mut v = serialize_card(cid, db, true);
        if let Some(obj) = v.as_object_mut() {
            obj.insert("tapped".to_string(), json!(p.is_tapped(i)));
            obj.insert("moved".to_string(), json!(p.is_moved(i)));
            obj.insert("revealed".to_string(), json!(p.is_revealed(i)));

            // Interaction logic
            if viewer_is_acting {
                let any_ability_legal = (0..10).any(|ab_idx| {
                    let aid = ACTION_BASE_STAGE + (i as i32 * 100) + (ab_idx * 10);
                    aid < legal_mask.len() as i32 && legal_mask[aid as usize]
                });
                let any_choice_legal = (0..10).any(|ab_idx| {
                    (0..10).any(|choice| {
                        let aid = ACTION_BASE_STAGE_CHOICE + i as i32 * 100 + ab_idx * 10 + choice;
                        aid < legal_mask.len() as i32 && legal_mask[aid as usize]
                    })
                });

                if any_ability_legal || any_choice_legal {
                    obj.insert("is_legal".to_string(), json!(true));
                }

                let select_id = ACTION_BASE_STAGE_SLOTS + i as i32; // Selection interact (600+)
                let choice_id = ACTION_BASE_CHOICE + i as i32; // Selection interact (8000+)
                if (select_id < legal_mask.len() as i32 && legal_mask[select_id as usize]) ||
                   (choice_id < legal_mask.len() as i32 && legal_mask[choice_id as usize]) {
                    obj.insert("is_select_legal".to_string(), json!(true));
                }
            }
        }
        v
    }).collect();

    let lives: Vec<Value> = p.live_zone.iter().enumerate().map(|(i, &cid)| {
        let mut v = serialize_card(cid, db, p.is_revealed(i) || is_viewer);
        if let Some(obj) = v.as_object_mut() {
            obj.insert("revealed".to_string(), json!(p.is_revealed(i)));

            if viewer_is_acting {
                let action_id = ACTION_BASE_STAGE_SLOTS + i as i32; // Match engine 600+ for Live selection
                if action_id < legal_mask.len() as i32 && legal_mask[action_id as usize] {
                    obj.insert("is_perf_legal".to_string(), json!(true));
                }
                // Also check generic choice 8000+ for lives
                let choice_id = ACTION_BASE_CHOICE + i as i32;
                if choice_id < legal_mask.len() as i32 && legal_mask[choice_id as usize] {
                    obj.insert("is_select_legal".to_string(), json!(true));
                }
            }
        }
        v
    }).collect();

    let energy: Vec<Value> = p.energy_zone.iter().enumerate().map(|(i, &cid)| {
        let mut v = serialize_card(cid as i32, db, true);
        if let Some(obj) = v.as_object_mut() {
            obj.insert("tapped".to_string(), json!(p.is_energy_tapped(i)));
            if viewer_is_acting {
                let action_id = ACTION_BASE_ENERGY + i as i32;
                if action_id < legal_mask.len() as i32 && legal_mask[action_id as usize] {
                    obj.insert("is_legal".to_string(), json!(true));
                }
                let choice_id = ACTION_BASE_CHOICE + i as i32;
                if choice_id < legal_mask.len() as i32 && legal_mask[choice_id as usize] {
                    obj.insert("is_select_legal".to_string(), json!(true));
                }
            }
        }
        v
    }).collect();

    let success_pile: Vec<Value> = p.success_lives.iter().enumerate().map(|(i, &cid)| {
        let mut v = serialize_card(cid as i32, db, true);
        if viewer_is_acting {
            if let Some(obj) = v.as_object_mut() {
                let action_id = ACTION_BASE_CHOICE + i as i32;
                if action_id < legal_mask.len() as i32 && legal_mask[action_id as usize] {
                    obj.insert("is_legal".to_string(), json!(true));
                }
            }
        }
        v
    }).collect();

    let discard_pile: Vec<Value> = p.discard.iter().map(|&cid| {
        serialize_card(cid as i32, db, true)
    }).collect();

    let mut obj = json!({
        "score": p.score,
        "energy_untapped": p.energy_zone.len() as u32 - p.tapped_energy_count(),
        "energy_count": p.energy_zone.len() as u32,
        "total_hearts": gs.get_total_hearts(p_idx, db, 0).to_array(),
        "total_blades": gs.get_total_blades(p_idx, db, 0),
        "hand": hand,
        "stage": stage,
        "live_zone": lives,
        "energy": energy,
        "discard": discard_pile,
        "discard_count": p.discard.len(),
        "deck_count": p.deck.len(),
        "energy_deck_count": p.energy_deck.len(),
        "success_lives": success_pile,
        "hand_count": p.hand.len(),
        "is_active": gs.current_player == p_idx as u8,
        "live_zone_revealed": [p.is_revealed(0), p.is_revealed(1), p.is_revealed(2)],
        "mulligan_selection": p.mulligan_selection,
        "cost_reduction": p.cost_reduction,
        "blade_buffs": p.blade_buffs,
        "played_group_mask": p.played_group_mask,
    });

    // Add remaining fields incrementally to avoid json! recursion limit
    let m = obj.as_object_mut().unwrap();
    m.insert("looked_cards".into(), json!(p.looked_cards.iter().map(|&cid| serialize_card(cid as i32, db, is_viewer)).collect::<Vec<Value>>()));
    m.insert("heart_buffs".into(), json!(p.heart_buffs.iter().map(|hb| hb.to_array()).collect::<Vec<[u8; 7]>>()));
    m.insert("prevent_activate".into(), json!(p.prevent_activate));
    m.insert("prevent_baton_touch".into(), json!(p.prevent_baton_touch));
    m.insert("prevent_success_pile_set".into(), json!(p.prevent_success_pile_set));
    m.insert("activated_energy_group_mask".into(), json!(p.activated_energy_group_mask));
    m.insert("activated_member_group_mask".into(), json!(p.activated_member_group_mask));
    m.insert("discarded_this_turn".into(), json!(p.discarded_this_turn));
    m.insert("yell_cards".into(), json!(p.yell_cards.iter().map(|&cid| serialize_card(cid, db, true)).collect::<Vec<Value>>()));
    m.insert("heart_req_reductions".into(), json!(p.heart_req_reductions.to_array()));
    m.insert("heart_req_additions".into(), json!(p.heart_req_additions.to_array()));
    // Deep diagnostics
    m.insert("baton_touch_count".into(), json!(p.baton_touch_count));
    m.insert("baton_touch_limit".into(), json!(p.baton_touch_limit));
    m.insert("live_score_bonus".into(), json!(p.live_score_bonus));
    m.insert("live_score_bonus_logs".into(), json!(p.live_score_bonus_logs.iter().map(|(cid, amt)| json!({"source": cid, "amount": amt})).collect::<Vec<Value>>()));
    m.insert("slot_cost_modifiers".into(), json!(p.slot_cost_modifiers));
    m.insert("blade_buff_logs".into(), json!(p.blade_buff_logs.iter().map(|(src, amt, slot)| json!({"source": src, "amount": amt, "slot": slot})).collect::<Vec<Value>>()));
    m.insert("heart_buff_logs".into(), json!(p.heart_buff_logs.iter().map(|(src, amt, col, slot)| json!({"source": src, "amount": amt, "color": col, "slot": slot})).collect::<Vec<Value>>()));
    m.insert("yell_count_reduction".into(), json!(p.yell_count_reduction));
    m.insert("flags".into(), json!(p.flags));
    m.insert("play_count_this_turn".into(), json!(p.play_count_this_turn));
    m.insert("stage_energy_count".into(), json!(p.stage_energy_count));
    m.insert("stage_energy".into(), json!(p.stage_energy.iter().map(|sv| sv.iter().map(|&cid| cid).collect::<Vec<i32>>()).collect::<Vec<Vec<i32>>>()));
    m.insert("restrictions".into(), json!(p.restrictions.iter().collect::<Vec<&u8>>()));
    m.insert("negated_triggers_count".into(), json!(p.negated_triggers.len()));
    m.insert("granted_abilities_count".into(), json!(p.granted_abilities.len()));
    m.insert("prevent_play_to_slot_mask".into(), json!(p.prevent_play_to_slot_mask));
    m.insert("hand_increased_this_turn".into(), json!(p.hand_increased_this_turn));
    m.insert("cheer_mod_count".into(), json!(p.cheer_mod_count));
    m.insert("current_turn_notes".into(), json!(p.current_turn_notes));
    m.insert("color_transforms_count".into(), json!(p.color_transforms.len()));
    m.insert("excess_hearts".into(), json!(p.excess_hearts));
    m.insert("skip_next_activate".into(), json!(p.skip_next_activate));
    m.insert("used_abilities_count".into(), json!(p.used_abilities.len()));
    m.insert("exile_count".into(), json!(p.exile.len()));
    m.insert("live_deck_count".into(), json!(p.live_deck.len()));

    obj
}

pub fn serialize_state_rich(
    gs: &GameState,
    db: &CardDatabase,
    mode: &str,
    viewer_idx: usize,
    spectator_count: usize,
    is_ai_thinking: bool,
    ai_status: String,
    lang: &str,
    needs_deck: bool,
) -> Value {
    // Phase 1: Engine standard serialization (Everything)
    let mut root = serde_json::to_value(gs).unwrap();
    let map = root.as_object_mut().expect("GameState should serialize to a JSON object");

    // Phase 2: Compute UI helper data
    let legal_actions = gs.get_legal_action_ids(db);
    let mut legal_mask = vec![false; 22000];
    for &aid in &legal_actions {
        if aid >= 0 && aid < 22000 {
            legal_mask[aid as usize] = true;
        }
    }

    let p0 = serialize_player_rich(&gs.players[0], gs, db, 0, viewer_idx, &legal_mask);
    let p1 = serialize_player_rich(&gs.players[1], gs, db, 1, viewer_idx, &legal_mask);

    let triggered_abilities: Vec<Value> = gs.trigger_queue.iter()
        .filter(|(_cid, _, ctx, _, _)| ctx.player_id == 0)
        .map(|(cid, ab_idx, _, _, _)| {
            let member = db.get_member(*cid);
            let name = member.map(|m| m.name.clone()).unwrap_or_else(|| "Member".to_string());
            let text = member.and_then(|m| m.abilities.get(*ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_default();
            json!({ "name": name, "text": text })
        }).collect();

    let opponent_triggered_abilities: Vec<Value> = gs.trigger_queue.iter()
        .filter(|(_cid, _, ctx, _, _)| ctx.player_id == 1)
        .map(|(cid, ab_idx, _, _, _)| {
            let member = db.get_member(*cid);
            let name = member.map(|m| m.name.clone()).unwrap_or_else(|| "Member".to_string());
            let text = member.and_then(|m| m.abilities.get(*ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_default();
            json!({ "name": name, "text": text })
        }).collect();

    let last_action_text = gs.ui.rule_log.as_ref().and_then(|v| v.last()).cloned().unwrap_or_default();

    // Phase 3: Enrich/Overwrite with UI fields (Legacy support)
    map.insert("players".to_string(), json!([p0, p1]));
    map.insert("active_player".to_string(), json!(gs.current_player));
    map.insert("game_over".to_string(), json!(gs.phase as i8 == 9));
    map.insert("winner".to_string(), json!(gs.get_winner()));
    map.insert("last_action".to_string(), json!(last_action_text));
    map.insert("rule_log".to_string(), json!(gs.ui.rule_log.clone().unwrap_or_default()));
    map.insert("mode".to_string(), json!(mode));
    map.insert("spectators".to_string(), json!(spectator_count));
    map.insert("is_ai_thinking".to_string(), json!(is_ai_thinking));
    map.insert("ai_status".to_string(), json!(ai_status));
    map.insert("my_player_id".to_string(), json!(viewer_idx));
    map.insert("needs_deck".to_string(), json!(needs_deck));
    map.insert("performance_results".to_string(), json!(gs.ui.performance_results));
    map.insert("last_performance_results".to_string(), json!(gs.ui.last_performance_results));
    map.insert("performance_history".to_string(), json!(gs.ui.performance_history));
    map.insert("turn_events".to_string(), json!(gs.turn_history));
    map.insert("triggered_abilities".to_string(), json!(triggered_abilities));
    map.insert("opponent_triggered_abilities".to_string(), json!(opponent_triggered_abilities));
    map.insert("queue_depth".to_string(), json!(gs.trigger_queue.len()));
    map.insert("bytecode_log".to_string(), json!(gs.ui.bytecode_log.clone()));

    // RPS Masking
    if gs.phase as i8 == 1 && (gs.rps_choices[0] == -1 || gs.rps_choices[1] == -1) {
        map.insert("rps_choices".to_string(), json!([-1, -1]));
    } else {
        map.insert("rps_choices".to_string(), json!(gs.rps_choices));
    }

    // Pending Choice Enrichment
    let pending_choice_val = if let Some(pending) = gs.interaction_stack.last() {
        let mut options = Vec::new();
        let mut actions = Vec::new();
        let mut action_map = serde_json::Map::new();
        use crate::models::Action;

        for &id in &legal_actions {
            let (name, text, _type_str, _area, meta) = get_action_desc_rich(id, gs, db, viewer_idx, lang);
            let mut opt_obj = json!({ "name": name, "text": text });
            if let Some(opt_map) = opt_obj.as_object_mut() {
                for (k, v) in meta {
                    opt_map.insert(k, v);
                }
            }
            options.push(opt_obj);
            actions.push(id);

            // Populate action map
            let action = Action::from_id(id, gs.phase);
            match action {
                Action::SelectChoice { choice_idx } => { action_map.insert(choice_idx.to_string(), json!(id)); },
                Action::SelectHand { hand_idx } => { action_map.insert(hand_idx.to_string(), json!(id)); },
                Action::SelectResponseSlot { slot_idx } => { action_map.insert(slot_idx.to_string(), json!(id)); },
                Action::SelectResponseColor { color_idx } => { action_map.insert(color_idx.to_string(), json!(id)); },
                _ => {}
            }
        }

        let mut title = if !pending.choice_text.is_empty() {
            pending.choice_text.clone()
        } else if lang == "jp" {
            match pending.choice_type.as_str() {
                "SELECT_MODE" => "モードを選択してください".to_string(),
                "LOOK_AND_CHOOSE" => "カードを選択してください".to_string(),
                "SELECT_CARDS" => "カードを選択してください".to_string(),
                "COLOR_SELECT" => "色を選択してください".to_string(),
                "TAP_O" => "相手の枠を選択してください".to_string(),
                "RECOV_L" => "回収するライブを選択してください".to_string(),
                "RECOV_M" => "回収するメンバーを選択してください".to_string(),
                "SELECT_HAND_DISCARD" => "捨てるカードを選択してください".to_string(),
                "SELECT_HAND_PLAY" => "プレイするカードを選択してください".to_string(),
                "SELECT_LIVE_SLOT" => "ライブスロットを選択してください".to_string(),
                "SELECT_STAGE" => "ステージを選択してください".to_string(),
                "SELECT_DISCARD_PLAY" => "控え室からメンバーを選択してください".to_string(),
                "PAY_ENERGY" => "エネルギーを選択してください".to_string(),
                "OPTIONAL" => "効果を発動しますか？".to_string(),
                "TAP_M_SELECT" => "タップするメンバーを選択してください".to_string(),
                "REVEAL_HAND" => "手札を公開してください".to_string(),
                "OPPONENT_CHOOSE" => "相手が選択中です...".to_string(),
                "ORDER_DECK" => "カードをデッキの上に戻す順番を選んでください".to_string(),
                "SELECT_SWAP_SOURCE" => "入れ替えるライブを選んでください".to_string(),
                "SELECT_SWAP_TARGET" => "手札から入れ替えるメンバーを選んでください".to_string(),
                "SELECT_PLAYER" => "プレイヤーを選択してください".to_string(),
                "SELECT_DISCARD" => "捨てるカードを選択してください".to_string(),
                "SELECT_STAGE_EMPTY" => "空いている枠を選択してください".to_string(),
                _ => "選択してください".to_string()
            }
        } else {
            match pending.choice_type.as_str() {
                "SELECT_MODE" => "Mode Select".to_string(),
                "LOOK_AND_CHOOSE" => "Select Card".to_string(),
                "SELECT_CARDS" => "Select Card".to_string(),
                "COLOR_SELECT" => "Select Color".to_string(),
                "TAP_O" => "Select Opponent Slot".to_string(),
                "RECOV_L" => "Select Live to Recover".to_string(),
                "RECOV_M" => "Select Member to Recover".to_string(),
                "SELECT_HAND_DISCARD" => "Select Card to Discard".to_string(),
                "SELECT_HAND_PLAY" => "Select Card to Play".to_string(),
                "SELECT_LIVE_SLOT" => "Select Live Slot".to_string(),
                "SELECT_STAGE" => "Select Stage Slot".to_string(),
                "SELECT_DISCARD_PLAY" => "Select Member from Discard".to_string(),
                "PAY_ENERGY" => "Select Energy".to_string(),
                "OPTIONAL" => "Activate Effect?".to_string(),
                "TAP_M_SELECT" => "Select Member to Tap".to_string(),
                "REVEAL_HAND" => "Reveal Hand".to_string(),
                "OPPONENT_CHOOSE" => "Opponent is choosing...".to_string(),
                "ORDER_DECK" => "Order cards on Deck Top".to_string(),
                "SELECT_SWAP_SOURCE" => "Select card to swap out".to_string(),
                "SELECT_SWAP_TARGET" => "Select card to swap in".to_string(),
                "SELECT_PLAYER" => "Select Player".to_string(),
                "SELECT_DISCARD" => "Select card to discard".to_string(),
                "SELECT_STAGE_EMPTY" => "Select empty stage slot".to_string(),
                _ => "Please Select".to_string()
            }
        };

        let mut choose_count = 1;
        let mut source_ability = "".to_string();
        let mut trigger_label = "".to_string();

        if pending.card_id >= 0 {
            let member = db.get_member(pending.card_id);
            let live = db.get_live(pending.card_id);
            let abilities = if let Some(m) = member { Some(&m.abilities) } else { live.map(|l| &l.abilities) };

            if let Some(abs) = abilities {
                if let Some(ab) = abs.get(pending.ability_index.max(0) as usize) {
                    choose_count = ab.choice_count.max(1);
                    if !ab.raw_text.is_empty() {
                        source_ability = ab.raw_text.clone();
                    } else if !ab.pseudocode.is_empty() {
                        source_ability = ab.pseudocode.clone();
                    }

                    trigger_label = match ab.trigger {
                        TriggerType::OnPlay => "登場",
                        TriggerType::OnLiveStart => "開始時",
                        TriggerType::OnLiveSuccess => "成功時",
                        TriggerType::TurnStart => "ターン開始",
                        TriggerType::TurnEnd => "ターン終了",
                        TriggerType::Constant => "常時",
                        TriggerType::Activated => "起動",
                        TriggerType::OnLeaves => "自動",
                        TriggerType::OnReveal => "公開時",
                        _ => ""
                    }.to_string();

                    let ab_summary = get_ability_summary(&serde_json::to_value(ab).unwrap(), lang);
                    let source_info = if let Some(m) = member { format!("{} ({})", m.name, m.card_no) }
                                     else if let Some(l) = live { format!("{} ({})", l.name, l.card_no) }
                                     else { "".to_string() };
                    if !source_info.is_empty() {
                        title = format!("{}: {}", source_info, ab_summary);
                    } else {
                        title = ab_summary;
                    }
                }
            }
        }

        let filter_desc = get_filter_description(pending.filter_attr, lang);
        if !filter_desc.is_empty() {
            title = format!("{} ({})", title, filter_desc);
        }

        json!({
            "type": pending.choice_type,
            "title": title,
            "text": pending.choice_text,
            "card_id": pending.card_id,
            "source_ability": source_ability,
            "options": options,
            "actions": actions,
            "action_map": action_map,
            "choose_count": choose_count,
            "v_remaining": pending.v_remaining,
            "ability_index": pending.ability_index,
            "trigger_label": trigger_label
        })
    } else {
        Value::Null
    };
    map.insert("pending_choice".to_string(), pending_choice_val);

    // Legal Actions Enrichment
    let rich_legal_actions = if viewer_idx == gs.current_player as usize {
        legal_actions.into_iter().map(|id| {
            let (name, text, type_str, area_idx_opt, metadata) = get_action_desc_rich(id, gs, db, viewer_idx, lang);
            let mut obj = json!({
                "id": id,
                "name": name,
                "text": text,
                "type": type_str
            });
            let obj_map = obj.as_object_mut().unwrap();
            if let Some(idx) = area_idx_opt {
                obj_map.insert("area_idx".to_string(), json!(idx));
            }
            for (k, v) in metadata {
                obj_map.insert(k, v);
            }
            obj
        }).collect::<Vec<Value>>()
    } else {
        vec![]
    };
    map.insert("legal_actions".to_string(), json!(rich_legal_actions));

    root
}

#[cfg(test)]
mod tests {
    use super::*;
    use engine_rust::core::logic::{CardDatabase, PendingInteraction, AbilityContext};
    use std::fs;

    #[test]
    fn test_dump_action_buttons() {
        use std::io::Write;
        use engine_rust::core::logic::{
            O_SELECT_MODE, O_LOOK_AND_CHOOSE, O_COLOR_SELECT, O_TAP_OPPONENT, O_ORDER_DECK,
            O_PLAY_MEMBER_FROM_HAND, O_SELECT_CARDS, O_RECOVER_LIVE, O_RECOVER_MEMBER, O_MOVE_TO_DISCARD,
            O_SWAP_AREA
        };

        // Load DB
        let db_path = "../data/cards_compiled.json";
        let db_json = fs::read_to_string(db_path).expect("Failed to read DB");
        let db = CardDatabase::from_json(&db_json).expect("Failed to parse DB");

        let out_path = "action_buttons_exhaustive.txt";
        let mut f = fs::File::create(out_path).expect("Failed to create output file");

        let mut gs = GameState::default();

        macro_rules! dump {
            ($label:expr) => {
                writeln!(f, "\n=== Scenario: {} ===", $label).unwrap();

                // Show Phase and Pending Logic Info
                writeln!(f, "Phase: {:?}", gs.phase).unwrap();
                if gs.phase == Phase::Response {
                    let pending = gs.interaction_stack.last().unwrap();
                    writeln!(f, "[Logic Entry] Opcode: {} | CardID: {} | AbIdx: {}", pending.effect_opcode, pending.card_id, pending.ability_index).unwrap();
                }

                let legal_actions = gs.get_legal_action_ids(&db);
                if legal_actions.is_empty() {
                    writeln!(f, "(No legal actions)").unwrap();
                }
                for &id in &legal_actions {
                    let (name_jp, text_jp, type_jp, _, _) = get_action_desc_rich(id, &gs, &db, 0, "jp");
                    let (name_en, text_en, type_en, _, _) = get_action_desc_rich(id, &gs, &db, 0, "en");

                    writeln!(f, "ID {:>3} | [JP] {:<15} | {} ({})", id, name_jp, text_jp, type_jp).unwrap();
                    writeln!(f, "       | [EN] {:<15} | {} ({})", name_en, text_en, type_en).unwrap();
                    writeln!(f, "-------").unwrap();
                }
            }
        }

        use engine_rust::core::logic::AbilityContext;

        // 1. RPS Phase
        gs.phase = Phase::Rps;
        gs.rps_choices = [-1, -1];
        dump!("Rock-Paper-Scissors Phase");

        // 2. Turn Choice
        gs.phase = Phase::TurnChoice;
        gs.current_player = 0;
        dump!("Turn Choice (Winner chooses order)");

        // 3. Mulligan Phase - Mix cards
        gs.phase = Phase::MulliganP1;
        gs.players[0].hand = vec![1, 10001, 10, 11].into(); // Member, Live, Member, Member
        dump!("Mulligan Phase (Mixing Member/Live)");

        // 4. Energy Phase
        gs.phase = Phase::Energy;
        dump!("Energy Phase (Auto-draw logic prompt)");

        // Common setup for Main/Response
        gs.players[0].energy_zone = vec![40001, 40002, 40003].into(); // 3 colors
        gs.players[0].tapped_energy_mask = 0;

        // 5. Main Phase - Variety in hand
        gs.phase = Phase::Main;
        gs.players[0].hand = vec![1, 10001, 40001].into(); // Member, Live, Energy
        gs.players[0].stage = [-1, -1, -1];
        dump!("Main Phase - Variety in Hand (Member/Live/Energy)");

        // 6. Main Phase - Activated Ability
        gs.players[0].stage = [2, -1, -1];
        gs.players[0].discard = vec![1, 1, 1, 1, 1, 1].into(); // Discard req for Card 2
        dump!("Main Phase - Activated Ability (Umi #2)");

        // 7. Live Set Phase - Variety
        gs.phase = Phase::LiveSet;
        gs.players[0].hand = vec![1, 10001].into();
        dump!("Live Set Phase (Mixed Hand)");

        // --- RESPONSE PHASE SCENARIOS ---
        gs.phase = Phase::Response;

        let mut base_pending = PendingInteraction {
             card_id: 17, // Rin #17 has SELECT_MODE
             ability_index: 0,
             ctx: AbilityContext { player_id: 0, ..Default::default() },
             ..Default::default()
        };

        // 8. Color Selection
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_COLOR_SELECT; p });
        dump!("Choice: Color Selection");

        // 9. Select Mode
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_SELECT_MODE; p });
        dump!("Choice: Select Mode");

        // 10. Look and Choose - Mixed List
        gs.interaction_stack.clear();
        gs.interaction_stack.push({
            let mut p = base_pending.clone();
            p.effect_opcode = O_LOOK_AND_CHOOSE;
            p.filter_attr = 0x00000004; // Member filter (Bit 2-3 = 1)
            p
        });
        gs.players[0].looked_cards = vec![1, 10001, 2].into(); // Mix
        dump!("Choice: Look and Choose (Filtering Members from Mix)");

        // 11. Recover Live
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_RECOVER_LIVE; p });
        gs.players[0].looked_cards = vec![10001, 10002].into();
        dump!("Choice: Recover Live to Hand");

        // 12. Recover Member
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_RECOVER_MEMBER; p });
        gs.players[0].looked_cards = vec![1, 2, 10].into();
        dump!("Choice: Recover Member to Hand");

        // 13. Move to Discard
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_MOVE_TO_DISCARD; p });
        gs.players[0].hand = vec![1, 10001, 40001].into();
        dump!("Choice: Put Card to Discard (from Mixed Hand)");

        // 14. Target Opponent Slots (TAP_OPPONENT)
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_TAP_OPPONENT; p });
        dump!("Choice: Tap Opponent's Slot");

        // 15. Order Deck
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_ORDER_DECK; p });
        gs.players[0].looked_cards = vec![1, 2, 10].into();
        dump!("Choice: Order Deck Top");

        // 16. Select Cards (Generic Hand)
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_SELECT_CARDS; p });
        gs.players[0].hand = vec![1, 10, 10001].into();
        dump!("Choice: Select Cards (Generic)");

        // 17. Target Selection (Play Member from Hand/Discard)
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_PLAY_MEMBER_FROM_HAND; p });
        gs.players[0].hand = vec![1, 10001].into();
        dump!("Choice: Select Target Slot for Played Member");

        // 18. Swap Area (Member movement)
        gs.interaction_stack.clear();
        gs.interaction_stack.push({ let mut p = base_pending.clone(); p.effect_opcode = O_SWAP_AREA; p });
        dump!("Choice: Select Slot to Swap Member to");

        // 19. Kanata Konoe (ID 374) - Activated Ability
        gs.phase = Phase::Main;
        gs.interaction_stack.clear();
        gs.players[0].stage = [374, -1, -1];
        gs.players[0].hand = vec![1, 10, 20].into(); // Cards to discard as cost
        dump!("Main Phase - Kanata Konoe (ID 374) Activated Ability");

        writeln!(f, "\n[Dump Complete]").unwrap();
        println!("Exhaustive dump written to {}", out_path);
    }
}
