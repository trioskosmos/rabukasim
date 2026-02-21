import os

# Define the Japanese strings as Unicode escapes to be 100% safe
strings = {
    "group_niji": "\u8679\u30e2\u5d0e", # 虹ヶ咲
    "group_hasu": "\u84ee\u30ce\u7a7a", # 蓮ノ空
    "group_other": "\u4ed6", # 他
    "unit_slsz": "\u30b9\u30ea\u30fc\u30ba\u30d6\u30fc\u30b1", # スリーズブーケ
    "unit_miraku": "\u307f\u3089\u304f\u3089\u3071\u30fc\u304f", # みらくらぱーく
    "unit_univ": "\u30e6\u30cb\u30c3\u30c8", # ユニット
    "trigger_onplay": "\u767b\u5834\u6642",
    "trigger_live_start": "\u30e9\u30a4\u30d6\u9032\u884c\u6642",
    "trigger_live_success": "\u30e9\u30a4\u30d6\u6210\u529f\u6642",
    "trigger_turn_start": "\u30bf\u30fc\u30f3\u958b\u59cb\u6642",
    "trigger_turn_end": "\u30bf\u30fc\u30f3\u7d42\u4e86\u6642",
    "trigger_constant": "\u5e38\u6642",
    "trigger_act": "\u8d77\u52d5",
    "self": "\u81ea\u5206",
    "opponent": "\u76f8\u624b",
    "all": "\u5168\u4f53",
    "start_perf": " \u3010\u958b\u59cb\u3011\u30d1\u30d5\u30a9\u30fc\u30de\u30f3\u30b9",
    "start_perf_desc": "\u30d1\u30d5\u30a9\u30fc\u30de\u30f3\u30b9\u3022\u958b\u59cb\u3057\u307e\u3059\u3002",
    "finish_perf": "\u3010\u5b8c\u4e86\u3011\u6b21\u3078",
    "finish_perf_desc": "\u7d50\u679c\u3022\u78ba\u8a8d\u3057\u3066\u6b21\u3078\u9032\u307f\u307e\u3059\u3002",
    "confirm_mulligan": "\u3010\u78ba\u5b9a\u3011\u30de\u30ea\u30ac\u30f3",
    "confirm_mulligan_desc": "\u624b\u672d\u3022\u78ba\u5b9a\u3057\u3066\u30de\u30ea\u30ac\u30f3\u3022\u7d42\u4e86\u3057\u307e\u3059\u3002",
    "confirm_liveset": "\u3010\u78ba\u5b9a\u3011\u30bb\u30c3\u30c8\u5b8c\u4e86",
    "confirm_liveset_desc": "\u30e9\u30a4\u30d6\u30ab\u30fc\u30c9\u306e\u30bb\u30c3\u30c8\u3022\u7d42\u4e86\u3057\u307e\u3059\u3002",
    "pass_skip": "\u3010\u30b9\u30ad\u30c3\u30d7\u3011\u30d1\u30b9",
    "pass_skip_desc": "\u4f55\u3082\u3057\u306a\u3044\u3002",
    "mulligan": "\u3010\u30de\u30ea\u30ac\u30f3\u3011",
    "mulligan_desc": "\u3053\u306e\u30ab\u30fc\u30c9\u3022\u30c7\u30c3\u30ad\u306b\u623b\u3057\u3066\u5f15\u304d\u76f4\u3057\u307e\u3059\u3002",
    "left": "\u5de6",
    "mid": "\u4e2d",
    "right": "\u53f3",
    "onplay": "\u767b\u5834",
    "baton": "\u30d0\u30c8\u30f3\u30bf\u30c3\u30c1",
    "leaves": "\u9000\u5834",
    "pay": "\u652f\u6255",
    "cost": "\u30b3\u30b9\u30c8",
    "ability": "\u30a2\u30d3\u30ea\u30c6\u30a3",
    "act": "\u3010\u8d77\u52d5\u3011",
    "select_slot": "\u7b2c{}\u67a0\u3022\u9078\u629e",
    "tap": "\u30bf\u30c3\u30d7: {}",
    "opp_slot": "\u76f8\u624b\u306e{}\u67a0",
    "choice": "\u9078\u629e\u80a2 {}",
    "select": "\u3010\u9078\u629e\u3011",
    "select_desc": "\u3053\u306e\u30ab\u30fc\u30c9\u3022\u9078\u629e\u3057\u307e\u3059\u3002",
    "recover": "\u3010\u56de\u53ce\u3011",
    "recover_desc": "\u3053\u306e\u30ab\u30fc\u30c9\u3022\u624b\u672d\u306b\u623b\u3057\u307e\u3059\u3002",
    "discard": "\u3010\u63a7\u3048\u5ba4\u3011",
    "discard_desc": "\u3053\u306e\u30ab\u30fc\u30c9\u3022\u63a7\u3048\u5ba4\u306b\u7f6e\u304d\u307e\u3059\u3002",
    "color_pink": "\u30d4\u30f3\u30af",
    "color_red": "\u8d64",
    "color_yellow": "\u9ec4",
    "color_green": "\u7dd1",
    "color_blue": "\u9752",
    "color_purple": "\u7d2b",
    "select_color": "\u3010\u8272\u3022\u9078\u629e\u3011{}",
    "add_effect": "\u3010\u8ffd\u52a0\u52b9\u679c\u3011",
    "discard_act": "\u3010\u63a7\u3048\u5ba4\u304b\u3089\u8d77\u52d5\u3011",
    "discard_act_desc": "\u63a7\u3048\u5ba4\u306b\u3042\u308b\u3053\u306e\u30ab\u30fc\u30c9\u306e\u80fd\u529b\u3022\u4f7f\u3044\u307e\u3059\u3002",
    "set": "\u3010\u30bb\u30c3\u30c8\u3011",
    "set_desc": "\u3053\u306e\u30e9\u30a4\u30d6\u3022\u30e9\u30a4\u30d6\u30be\u30fc\u30f3\u306b\u30bb\u30c3\u30c8\u3057\u307e\u3059\u3002",
    "gu": "\u30b0\u30fc",
    "pa": "\u30d1\u30fc",
    "choki": "\u30c1\u30e7\u30ad",
    "rps_label": "\u3010\u3058\u3083\u3093\u3051\u3093\u3011{}",
    "first": "\u3010\u9078\u629e\u3011\u5148\u653b",
    "second": "\u3010\u9078\u629e\u3011\u5f8c\u653b",
    "swap": "\u3010\u5165\u308c\u66ff\u3048\u3011{} \u3068 {}",
    "swap_desc": "{} \u67a0\u3068 {} \u67a0\u306e\u30e1\u30f3\u30d0\u30fc\u3022\u5165\u308c\u66ff\u3048\u307e\u3059\u3002",
    "choice_mode": "\u30e2\u30fc\u30c9\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_card": "\u30ab\u30fc\u30c9\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_color": "\u8272\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_opp": "\u76f8\u624b\u306e\u67a0\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_live": "\u56de\u53ce\u3059\u308b\u30e9\u30a4\u30d6\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_member": "\u56de\u53ce\u3059\u308b\u30e1\u30f3\u30d0\u30fc\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_discard": "\u6368\u3066\u308b\u30ab\u30fc\u30c9\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_play": "\u30d7\u30ec\u30a4\u3059\u308b\u30ab\u30fc\u30c9\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_liveslot": "\u30e9\u30a4\u30d6\u30b9\u30ed\u30c3\u30c8\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_stage": "\u30b9\u30c6\u30fc\u30b8\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "choice_energy": "\u30a8\u30cd\u30eb\u30ae\u30fc\u3022\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044",
    "please_select": "\u9078\u629e\u3057\u3066\u304f\u3060\u3055\u3044"
}

path = r"c:\Users\trios\.gemini\antigravity\vscode\loveca-copy\launcher\src\serialization.rs"

with open(path, "rb") as f:
    raw = f.read()

content = raw.decode("utf-8", errors="replace")

# 1. get_group_name
content = re.sub(r'2 => ".*",\s*3 => "Liella!",\s*4 => ".*"', 
                 f'2 => "{strings["group_niji"]}", 3 => "Liella!", 4 => "{strings["group_hasu"]}"', content)
content = re.sub(r'_ => ".*"', f'_ => "{strings["group_other"]}"', content, count=1)

# 2. get_unit_name
content = content.replace('13 => "スリーズブーケ"', f'13 => "{strings["unit_slsz"]}"')
content = content.replace('15 => "みらくらぱーく"', f'15 => "{strings["unit_miraku"]}"')
content = content.replace('_ => "ユニット"', f'_ => "{strings["unit_univ"]}"')

# 3. get_ability_summary
content = re.sub(r'let t_map = \["", ".*", ".*", ".*", ".*", ".*", ".*", ".*"\];', 
                 f'let t_map = ["", "{strings["trigger_onplay"]}", "{strings["trigger_live_start"]}", "{strings["trigger_live_success"]}", "{strings["trigger_turn_start"]}", "{strings["trigger_turn_end"]}", "{strings["trigger_constant"]}", "{strings["trigger_act"]}"];', content)
content = content.replace('match target {\n            1 => "自分"', f'match target {{\n            1 => "{strings["self"]}"')
content = content.replace('2 => "相手"', f'2 => "{strings["opponent"]}"')
content = content.replace('_ => "全体"', f'_ => "{strings["all"]}"')

# 4. get_action_desc_rich (HEAVY FIX)
# We'll replace the match action block with the clean version using escapes
import re
match_pattern = re.compile(r'let \(name, text, type_str, area_idx_opt\) = match action \{.*?\}\n\n\s*\(name, text, type_str, area_idx_opt, metadata\)', re.DOTALL)

new_match_block = f"""let (name, text, type_str, area_idx_opt) = match action {{
        Action::Pass => {{
            let (name, text) = match gs.phase {{
                Phase::PerformanceP1 | Phase::PerformanceP2 => {{
                    if lang == "jp" {{ ("{strings["start_perf"]}".into(), "{strings["start_perf_desc"]}".into()) }}
                    else {{ ("Perform Live".into(), "Start the performance check.".into()) }}
                }},
                Phase::LiveResult => {{
                    if lang == "jp" {{ ("{strings["finish_perf"]}".into(), "{strings["finish_perf_desc"]}".into()) }}
                    else {{ ("Finish Performance".into(), "Confirm results and proceed.".into()) }}
                }},
                Phase::MulliganP1 | Phase::MulliganP2 => {{
                    if lang == "jp" {{ ("{strings["confirm_mulligan"]}".into(), "{strings["confirm_mulligan_desc"]}".into()) }}
                    else {{ ("Confirm Mulligan".into(), "Finish Mulligan and start the game.".into()) }}
                }},
                Phase::LiveSet => {{
                    if lang == "jp" {{ ("{strings["confirm_liveset"]}".into(), "{strings["confirm_liveset_desc"]}".into()) }}
                    else {{ ("Confirm Live Set".into(), "Finish setting cards for the live zone.".into()) }}
                }},
                _ => {{
                    if lang == "jp" {{ ("{strings["pass_skip"]}".into(), "{strings["pass_skip_desc"]}".into()) }}
                    else {{ ("Pass / Confirm".into(), "Skip or confirm current action.".into()) }}
                }}
            }};
            (name, text, "PASS".into(), None)
        }},
        Action::ToggleMulligan {{ hand_idx }} => {{
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(u16::MAX);
            let card_name = if cid < 10000 {{
                db.get_member(cid as u16).map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| format!("Member #{{}}", cid))
            }} else if cid < 40000 {{
                db.get_live(cid as u16).map(|l| l.name.clone()).unwrap_or_else(|| format!("Live #{{}}", cid))
            }} else {{ "Card".to_string() }};

            let (label, desc) = if lang == "jp" {{
                (format!("{strings["mulligan"]}{{}}", card_name), "{strings["mulligan_desc"]}".into())
            }} else {{
                (format!("Mulligan: {{}}", card_name), "Return this card to deck and draw a new one.".into())
            }};
            metadata.insert("hand_idx".into(), json!(hand_idx));
            (label, desc, "MULLIGAN".into(), None)
        }},
        Action::PlayMember {{ hand_idx, slot_idx }} => {{
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(u16::MAX);
            let card = if cid != u16::MAX {{ db.get_member(cid as u16) }} else {{ None }};
            let lang_data = if lang == "jp" {{
                ("{strings["left"]}", "{strings["mid"]}", "{strings["right"]}", "{strings["onplay"]}", "\u306b\u7f6e\u304f", "{strings["baton"]}", "{strings["leaves"]}", "{strings["pay"]}", "{strings["cost"]}")
            }} else {{
                ("Left", "Mid", "Right", "On Play", "to", "Baton Touch", "leaves", "Pay", "Cost")
            }};
            let (l_name, c_name, r_name, suffix_str, _to_str, baton_str, leaves_str, pay_str, cost_str) = lang_data;
            let areas = [l_name, c_name, r_name];

            let raw_name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
            let card_no = card.map(|m| m.card_no.clone()).unwrap_or_else(|| "??".into());
            let suffix = if let Some(m) = card {{
                 if m.abilities.iter().any(|ab| ab.trigger == engine_rust::core::enums::TriggerType::OnPlay) {{ format!(" [{{}}]", suffix_str) }} else {{ "".into() }}
            }} else {{ "".into() }};

            let new_cost = card.map(|m| m.cost as i32).unwrap_or(0);
            let prev_cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let mut old_name = "".to_string();
            let base_cost = (new_cost - p.cost_reduction).max(0);
            let mut actual_cost = base_cost;
            if prev_cid >= 0 {{
                if let Some(old_m) = db.get_member(prev_cid as u16) {{
                    old_name = old_m.name.clone();
                    actual_cost = (base_cost - old_m.cost as i32).max(0);
                }}
            }}

            let label = if lang == "jp" {{
                if prev_cid >= 0 {{
                    format!("{{}} ({{}}){{}} ({{}}: {{}}{strings["leaves"]}, {{}}:{{}})", raw_name, card_no, suffix, baton_str, old_name, pay_str, actual_cost)
                }} else {{
                    format!("{{}} ({{}}){{}} ({{}} {{}})", raw_name, card_no, suffix, cost_str, actual_cost)
                }}
            }} else {{
                if prev_cid >= 0 {{
                    format!("{{}} ({{}}){{}} ({{}}: {{}} {{}}, {{}}:{{}})", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                }} else {{
                    format!("{{}} ({{}}){{}} ({{}} {{}})", raw_name, card_no, suffix, cost_str, actual_cost)
                }}
            }};
            
            let cost_label = if lang == "jp" {{
                if prev_cid >= 0 {{ format!("({{}}: {{}}{strings["leaves"]}, {{}}:{{}})", baton_str, old_name, pay_str, actual_cost) }}
                else {{ format!("({{}} {{}})", cost_str, actual_cost) }}
            }} else {{
                if prev_cid >= 0 {{ format!("({{}}: {{}} {{}}, {{}}:{{}})", baton_str, old_name, leaves_str, pay_str, actual_cost) }}
                else {{ format!("({{}} {{}})", cost_str, actual_cost) }}
            }};


            let card_name_full = resolve_card_name(cid, db);

            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("full_label".into(), json!(label.clone()));
            metadata.insert("cost_label".into(), json!(cost_label));
            metadata.insert("cost".into(), json!(actual_cost));
            metadata.insert("name".into(), json!(card_name_full));
            (label, card.map(|m| m.original_text.clone()).unwrap_or_default(), "PLAY".into(), Some(slot_idx))
        }},
        Action::ActivateAbility {{ slot_idx, ab_idx }} => {{
            let cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let card = if cid >= 0 {{ db.get_member(cid as u16) }} else {{ None }};
            let name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" {{ "{strings["ability"]}".into() }} else {{ "Ability".into() }});
            
            let areas = if lang == "jp" {{ ["{strings["left"]}", "{strings["mid"]}", "{strings["right"]}"] }} else {{ ["Left", "Mid", "Right"] }};
            let area_name = areas.get(slot_idx).unwrap_or(&"");
            
            let label = if lang == "jp" {{
                format!("{strings["act"]}{{}}: {{}} ({{}})", name, summary, area_name)
            }} else {{
                format!("Use {{}}: {{}} ({{}})", name, summary, area_name)
            }};
            metadata.insert("category".into(), json!("ABILITY"));
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            (label, "".into(), "ABILITY".into(), Some(slot_idx))
        }},
        Action::SelectChoice {{ choice_idx }} => {{
             let mut name = String::new();
             let text = String::new();
             let type_str = "CHOICE".to_string();
             
             let pending = gs.interaction_stack.last();
             let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);
             let card_id = pending.map(|p| p.card_id).unwrap_or(-1);
             let ab_idx = pending.map(|p| p.ability_index).unwrap_or(-1);

             if gs.phase == Phase::LiveResult {{
                 name = if lang == "jp" {{ format!("{strings["select_slot"]}", choice_idx + 1) }} else {{ format!("Select Slot {{}}", choice_idx + 1) }};
             }} else if opcode == O_SELECT_MODE as i16 {{
                  let member = if card_id >= 0 {{ db.get_member(card_id as u16) }} else {{ None }};
                  let ab = member.and_then(|m| m.abilities.get(ab_idx as usize));
                  if let Some(ab) = ab {{
                      if let Some(arr) = ab.modal_options.as_array() {{
                          if let Some(opt) = arr.get(choice_idx) {{
                               if let Some(s) = opt.as_str() {{
                                   name = s.to_string();
                               }}
                          }}
                      }}
                  }}
             }} else if opcode == O_TAP_O as i16 {{
                  let opp_idx = 1 - viewer_idx;
                  let cid = gs.players[opp_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {{
                      name = if lang == "jp" {{ format!("{strings["tap"]}", resolve_card_name(cid as u16, db)) }} else {{ format!("Tap: {{}}", resolve_card_name(cid as u16, db)) }};
                  }} else {{
                      let areas = if lang == "jp" {{ ["{strings["left"]}", "{strings["mid"]}", "{strings["right"]}"] }} else {{ ["Left", "Mid", "Right"] }};
                      name = if lang == "jp" {{ format!("{strings["opp_slot"]}", areas.get(choice_idx).unwrap_or(&"")) }} else {{ format!("Opponent's {{}} Slot", areas.get(choice_idx).unwrap_or(&"")) }};
                  }}
             }} else if opcode == O_SELECT_MEMBER as i16 {{
                  let cid = gs.players[viewer_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {{
                      name = resolve_card_name(cid as u16, db);
                  }}
             }} else if opcode == O_SELECT_LIVE as i16 {{
                  let cid = gs.players[viewer_idx].live_zone.get(choice_idx).cloned().unwrap_or(-1);
                  if cid >= 0 {{
                      name = resolve_card_name(cid as u16, db);
                  }}
             }} else if opcode == O_RECOV_L as i16 || opcode == O_ORDER_DECK as i16 {{
                 if let Some(cid) = gs.players[viewer_idx].looked_cards.get(choice_idx) {{
                     name = resolve_card_name(*cid as u16, db);
                 }}
             }} else if opcode == O_SELECT_CARDS as i16 || opcode == O_LOOK_AND_CHOOSE as i16 {{
                 // Lookup choices from looked_cards if available
                 if let Some(cid) = gs.players[viewer_idx].looked_cards.get(choice_idx) {{
                     name = resolve_card_name(*cid as u16, db);
                 }}
             }} else if opcode == O_MOVE_TO_DISCARD as i16 || opcode == O_PLAY_MEMBER_FROM_HAND as i16 {{
                 if let Some(cid) = gs.players[viewer_idx].hand.get(choice_idx) {{
                     name = resolve_card_name(*cid, db);
                 }}
             }}

             if name.is_empty() {{
                 name = if lang == "jp" {{ format!("{strings["choice"]}", choice_idx + 1) }} else {{ format!("Choice {{}}", choice_idx + 1) }};
             }}
             metadata.insert("choice_idx".into(), json!(choice_idx));
             metadata.insert("opcode".into(), json!(opcode));
             metadata.insert("category".into(), json!("CHOICE"));
             (name, text, type_str, None)
        }},
        Action::SelectHand {{ hand_idx }} => {{
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(u16::MAX);
            let card_name = if cid < 10000 {{
                db.get_member(cid as u16).map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| format!("Member #{{}}", cid))
            }} else if cid < 40000 {{
                db.get_live(cid as u16).map(|l| l.name.clone()).unwrap_or_else(|| format!("Live #{{}}", cid))
            }} else {{ "Card".to_string() }};
            
            let mut desc = if lang == "jp" {{ "{strings["select_desc"]}".to_string() }} else {{ "Select this card.".to_string() }};
            let mut label_prefix = if lang == "jp" {{ "{strings["select"]}" }} else {{ "Select: " }};

            let pending = gs.interaction_stack.last();
            let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);

            if gs.phase == Phase::Response {{
                if opcode == O_RECOV_L as i16 || opcode == O_RECOV_M as i16 {{
                    label_prefix = if lang == "jp" {{ "{strings["recover"]}" }} else {{ "Recover: " }};
                    desc = if lang == "jp" {{ "{strings["recover_desc"]}".to_string() }} else {{ "Return this card to hand.".to_string() }};
                }} else if opcode == O_MOVE_TO_DISCARD as i16 {{
                    label_prefix = if lang == "jp" {{ "{strings["discard"]}" }} else {{ "Discard: " }};
                    desc = if lang == "jp" {{ "{strings["discard_desc"]}".to_string() }} else {{ "Put this card into the discard pile.".to_string() }};
                }}
            }}

            let label = format!("{{}}{{}}", label_prefix, card_name);
            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("category".into(), json!("SELECT"));
            metadata.insert("opcode".into(), json!(opcode));
            (label, desc, "SELECT".into(), None)
        }},
        Action::SelectResponseSlot {{ slot_idx }} => {{
            let areas = if lang == "jp" {{ ["{strings["left"]}", "{strings["mid"]}", "{strings["right"]}"] }} else {{ ["Left", "Mid", "Right"] }};
            let label = if lang == "jp" {{ format!("{strings["select_slot"]}", areas.get(slot_idx).unwrap_or(&"")) }} else {{ format!("Select {{}} Slot", areas.get(slot_idx).unwrap_or(&"")) }};
            metadata.insert("slot_idx".into(), json!(slot_idx));
            (label, "".into(), "SELECT".into(), Some(slot_idx))
        }},
        Action::SelectResponseColor {{ color_idx }} => {{
            let colors = if lang == "jp" {{ ["{strings["color_pink"]}", "{strings["color_red"]}", "{strings["color_yellow"]}", "{strings["color_green"]}", "{strings["color_blue"]}", "{strings["color_purple"]}"] }} else {{ ["Pink", "Red", "Yellow", "Green", "Blue", "Purple"] }};
            let label = if lang == "jp" {{ format!("{strings["select_color"]}", colors.get(color_idx as usize).unwrap_or(&"")) }} else {{ format!("Choose {{}}", colors.get(color_idx as usize).unwrap_or(&"")) }};
            metadata.insert("color_idx".into(), json!(color_idx));
            (label, "".into(), "COLOR".into(), None)
        }},
        Action::ActivateAbilityWithChoice {{ slot_idx, ab_idx, choice_idx }} => {{
            let cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
            let card = if cid \u003e= 0 {{ db.get_member(cid as u16) }} else {{ None }};
            let mut name = card.map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(&serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" {{ "{strings["ability"]}".into() }} else {{ "Ability".into() }});
            
            let pending = gs.interaction_stack.last();
            let opcode = pending.map(|p| p.effect_opcode).unwrap_or(0);

            // Resolve card name if it's a card selection activation
            if gs.phase == Phase::Response {{
                if opcode == O_LOOK_AND_CHOOSE as i16 || opcode == O_SELECT_CARDS as i16 || opcode == O_RECOV_L as i16 || opcode == O_ORDER_DECK as i16 {{
                    if let Some(cid) = gs.players[viewer_idx].looked_cards.get(choice_idx) {{
                        name = resolve_card_name(*cid as u16, db);
                    }}
                }} else if opcode == O_MOVE_TO_DISCARD as i16 {{
                    if let Some(\u0026cid) = gs.players[viewer_idx].hand.get(choice_idx) {{
                        name = resolve_card_name(cid as u16, db);
                    }}
                }} else if opcode == O_SELECT_MEMBER as i16 {{
                     let sel_cid = gs.players[viewer_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid \u003e= 0 {{ name = resolve_card_name(sel_cid as u16, db); }}
                }} else if opcode == O_SELECT_LIVE as i16 {{
                     let sel_cid = gs.players[viewer_idx].live_zone.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid \u003e= 0 {{ name = resolve_card_name(sel_cid as u16, db); }}
                }} else if opcode == O_TAP_O as i16 {{
                     let opp_idx = 1 - viewer_idx;
                     let sel_cid = gs.players[opp_idx].stage.get(choice_idx).cloned().unwrap_or(-1);
                     if sel_cid \u003e= 0 {{ name = format!("{strings["tap"]}", resolve_card_name(sel_cid as u16, db)); }}
                }}
            }}

            let areas = if lang == "jp" {{ ["{strings["left"]}", "{strings["mid"]}", "{strings["right"]}"] }} else {{ ["Left", "Mid", "Right"] }};
            let area_name = areas.get(slot_idx).unwrap_or(\u0026"");

            let label = if lang == "jp" {{
                format!("{strings["add_effect"]}{{}}: {{}} ({{}})", name, summary, area_name)
            }} else {{
                format!("Use {{}}: {{}} ({{}})", name, summary, area_name)
            }};
            metadata.insert("slot_idx".into(), json!(slot_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            metadata.insert("choice_idx".into(), json!(choice_idx));
            metadata.insert("category".into(), json!("ABILITY"));
            metadata.insert("opcode".into(), json!(opcode));
            (label, "".into(), "ABILITY".into(), Some(slot_idx))
        }},
        Action::PlayMemberWithChoice {{ hand_idx, slot_idx, choice_idx }} => {{
             let cid = p.hand.get(hand_idx).cloned().unwrap_or(u16::MAX);
             let card = if cid != u16::MAX {{ db.get_member(cid as u16) }} else {{ None }};
             let lang_data = if lang == "jp" {{
                 ("{strings["left"]}", "{strings["mid"]}", "{strings["right"]}", "{strings["onplay"]}", "\u306b\u7f6e\u304f", "{strings["baton"]}", "{strings["leaves"]}", "{strings["pay"]}", "{strings["cost"]}")
             }} else {{
                 ("Left", "Mid", "Right", "On Play", "to", "Baton Touch", "leaves", "Pay", "Cost")
             }};
             let (l_name, c_name, r_name, suffix_str, _to_str, baton_str, leaves_str, pay_str, cost_str) = lang_data;
             let areas = [l_name, c_name, r_name];

             let raw_name = card.map(|m| m.name.clone()).unwrap_or_else(|| "Member".into());
             let card_no = card.map(|m| m.card_no.clone()).unwrap_or_else(|| "??".into());
             let suffix = if let Some(m) = card {{
                  if m.abilities.iter().any(|ab| ab.trigger == engine_rust::core::enums::TriggerType::OnPlay) {{ format!(" [{{}}]", suffix_str) }} else {{ "".into() }}
             }} else {{ "".into() }};

             let new_cost = card.map(|m| m.cost as i32).unwrap_or(0);
             let prev_cid = p.stage.get(slot_idx).cloned().unwrap_or(-1);
             let mut old_name = "".to_string();
             let base_cost = (new_cost - p.cost_reduction).max(0);
             let mut actual_cost = base_cost;
             if prev_cid \u003e= 0 {{
                 if let Some(old_m) = db.get_member(prev_cid as u16) {{
                     old_name = old_m.name.clone();
                     actual_cost = (base_cost - old_m.cost as i32).max(0);
                 }}
             }}

             let label = if lang == "jp" {{
                 if prev_cid \u003e= 0 {{
                     format!("{{}} ({{}}){{}} ({{}}: {{}}{strings["leaves"]}, {{}}:{{}})*", raw_name, card_no, suffix, baton_str, old_name, pay_str, actual_cost)
                 }} else {{
                     format!("{{}} ({{}}){{}} ({{}} {{}})*", raw_name, card_no, suffix, cost_str, actual_cost)
                 }}
             }} else {{
                 if prev_cid \u003e= 0 {{
                     format!("{{}} ({{}}){{}} ({{}}: {{}} {{}}, {{}}:{{}})*", raw_name, card_no, suffix, baton_str, old_name, leaves_str, pay_str, actual_cost)
                 }} else {{
                     format!("{{}} ({{}}){{}} ({{}} {{}})*", raw_name, card_no, suffix, cost_str, actual_cost)
                 }}
             }};
             
             let cost_label = if lang == "jp" {{
                 if prev_cid \u003e= 0 {{ format!("({{}}: {{}}{strings["leaves"]}, {{}}:{{}})", baton_str, old_name, pay_str, actual_cost) }}
                 else {{ format!("({{}} {{}})", cost_str, actual_cost) }}
             }} else {{
                 if prev_cid \u003e= 0 {{ format!("({{}}: {{}} {{}}, {{}}:{{}})", baton_str, old_name, leaves_str, pay_str, actual_cost) }}
                 else {{ format!("({{}} {{}})", cost_str, actual_cost) }}
             }};


             let card_name_full = card.map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| {{
                 if cid < 10000 {{
                    db.get_member(cid as u16).map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| format!("Member #{{}}", cid))
                 }} else if cid < 40000 {{
                    db.get_live(cid as u16).map(|l| l.name.clone()).unwrap_or_else(|| format!("Live #{{}}", cid))
                 }} else {{
                    format!("Card #{{}}", cid)
                 }}
             }});

             metadata.insert("hand_idx".into(), json!(hand_idx));
             metadata.insert("slot_idx".into(), json!(slot_idx));
             metadata.insert("choice_idx".into(), json!(choice_idx));
             metadata.insert("full_label".into(), json!(label.clone()));
             metadata.insert("cost_label".into(), json!(cost_label));
             metadata.insert("cost".into(), json!(actual_cost));
             metadata.insert("name".into(), json!(card_name_full));
             (label, card.map(|m| m.original_text.clone()).unwrap_or_default(), "PLAY".into(), Some(slot_idx))
        }},
        Action::ActivateFromDiscard {{ discard_idx, ab_idx }} => {{
            let cid = p.discard.get(discard_idx).cloned().unwrap_or(u16::MAX);
            let card = if cid != u16::MAX {{ db.get_member(cid as u16) }} else {{ None }};
            let name = card.map(|m| format!("{{}} ({{}})", m.name, m.card_no)).unwrap_or_else(|| "Member".into());
            let summary = card.and_then(|c| c.abilities.get(ab_idx as usize))
                .map(|ab| get_ability_summary(\u0026serde_json::to_value(ab).unwrap(), lang))
                .unwrap_or_else(|| if lang == "jp" {{ "{strings["ability"]}".into() }} else {{ "Ability".into() }});

            let (label, desc) = if lang == "jp" {{
                (format!("{strings["discard_act"]}{{}}: {{}}", name, summary), "{strings["discard_act_desc"]}".into())
            }} else {{
                (format!("Discard Act {{}}: {{}}", name, summary), "Use this card's ability from the discard pile.".into())
            }};
            metadata.insert("discard_idx".into(), json!(discard_idx));
            metadata.insert("ab_idx".into(), json!(ab_idx));
            (label, desc, "ABILITY".into(), None)
        }},
        Action::PlaceLive {{ hand_idx }} => {{
            let cid = p.hand.get(hand_idx).cloned().unwrap_or(u16::MAX);
            let name = resolve_card_name(cid, db);
            let live_card = db.get_live(cid as u16);

            let label = if lang == "jp" {{
                format!("{strings["set"]}{{}}", name)
            }} else {{
                format!("Set Live: {{}}", name)
            }};

            let mut desc = if let Some(l) = live_card {{
                if !l.original_text.is_empty() {{
                    l.original_text.clone()
                }} else if !l.abilities.is_empty() {{
                    get_ability_summary(\u0026serde_json::to_value(\u0026l.abilities[0]).unwrap(), lang)
                }} else {{
                    "".to_string()
                }}
            }} else {{
                "".to_string()
            }};

            if desc.is_empty() {{
                desc = if lang == "jp" {{
                    "{strings["set_desc"]}".to_string()
                }} else {{
                    "Set this live card to the live zone.".to_string()
                }};
            }}

            metadata.insert("hand_idx".into(), json!(hand_idx));
            metadata.insert("name".into(), json!(name));
            (label, desc, "LIVE_SET".into(), None)
        }},
        Action::Rps {{ choice, .. }} => {{
            let choices = if lang == "jp" {{ ["{strings["gu"]}", "{strings["pa"]}", "{strings["choki"]}"] }} else {{ ["Rock", "Paper", "Scissors"] }};
            let label = if lang == "jp" {{ format!("{strings["rps_label"]}", choices.get(choice as usize).unwrap_or(\u0026"")) }} else {{ format!("Choose {{}}", choices.get(choice as usize).unwrap_or(\u0026"")) }};
            metadata.insert("choice".into(), json!(choice));
            (label, "".into(), "RPS".into(), None)
        }},
        Action::ChooseTurnOrder {{ first }} => {{
            let label = if lang == "jp" {{
                if first {{ "{strings["first"]}" }} else {{ "{strings["second"]}" }}
            }} else {{
                if first {{ "Go First" }} else {{ "Go Second" }}
            }};
            metadata.insert("first".into(), json!(first));
            (label.into(), "".into(), "TURN_ORDER".into(), None)
        }},
        Action::Formation {{ src_idx, dst_idx }} => {{
            let areas = if lang == "jp" {{ ["{strings["left"]}", "{strings["mid"]}", "{strings["right"]}"] }} else {{ ["Left", "Mid", "Right"] }};
            let (src_name, dst_name) = (areas.get(src_idx).unwrap_or(\u0026"??"), areas.get(dst_idx).unwrap_or(\u0026"??"));
            let label = if lang == "jp" {{
                format!("{strings["swap"]}", src_name, dst_name)
            }} else {{
                format!("Formation: Swap {{}} and {{}}", src_name, dst_name)
            }};
            let text = if lang == "jp" {{
                format!("{strings["swap_desc"]}", src_name, dst_name)
            }} else {{
                format!("Swap members between {{}} and {{}} slots.", src_name, dst_name)
            }};
            metadata.insert("src_idx".into(), json!(src_idx));
            metadata.insert("dst_idx".into(), json!(dst_idx));
            (label, text, "FORMATION".into(), None)
        }},
        _ => (format!("Action {{}}", id), "".into(), "OTHER".into(), None),
    }};

    (name, text, type_str, area_idx_opt, metadata)"""

content = match_pattern.sub(new_match_block, content)

# 5. serialize_game Choice Titles Fix
choice_mapping = {
    "SELECT_MODE": strings["choice_mode"],
    "LOOK_AND_CHOOSE": strings["choice_card"],
    "SELECT_CARDS": strings["choice_card"],
    "COLOR_SELECT": strings["choice_color"],
    "TAP_O": strings["choice_opp"],
    "RECOV_L": strings["choice_live"],
    "RECOV_M": strings["choice_member"],
    "SELECT_HAND_DISCARD": strings["choice_discard"],
    "SELECT_HAND_PLAY": strings["choice_play"],
    "SELECT_LIVE_SLOT": strings["choice_liveslot"],
    "SELECT_STAGE": strings["choice_stage"],
    "PAY_ENERGY": strings["choice_energy"],
    "_": strings["please_select"]
}

for key, val in choice_mapping.items():
    if key == "_":
        content = re.sub(r'_ => ".*"\.to_string\(\)', f'_ => "{val}".to_string()', content)
    else:
        pattern = fr'"{key}" => ".*"\.to_string\(\)'
        replacement = f'"{key}" => "{val}".to_string()'
        content = re.sub(pattern, replacement, content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Definitive repair complete.")
