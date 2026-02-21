import json
import os
import re


def generate_audit_report():
    cards_path = "data/cards.json"
    pseudo_path = "data/manual_pseudocode.json"
    output_path = "docs/audit_report.md"

    with open(cards_path, "r", encoding="utf-8") as f:
        cards = json.load(f)
    with open(pseudo_path, "r", encoding="utf-8") as f:
        pseudo = json.load(f)

    candidate_cards = [
        "PL!-pb1-009-P＋",
        "PL!-pb1-009-R",
        "PL!HS-bp2-019-L",
        "PL!HS-bp2-020-L",
        "PL!N-bp4-010-P",
        "PL!N-bp4-010-P＋",
        "PL!N-bp4-010-R＋",
        "PL!N-bp4-010-SEC",
        "PL!N-bp4-026-L",
        "PL!S-bp2-004-P",
        "PL!S-bp2-004-R",
        "PL!S-bp2-024-L",
        "PL!S-bp3-020-L",
        "PL!S-pb1-022-L",
        "PL!S-pb1-022-L＋",
        "PL!SP-bp1-024-L",
        "PL!SP-bp1-026-L",
        "PL!N-bp4-007-P",
        "PL!N-bp3-008-P",
        "PL!N-pb1-004-P＋",
        "PL!-bp3-024-L",
        "PL!SP-bp4-004-P",
        "PL!-bp3-006-P",
        "PL!N-bp3-017-N",
        "PL!N-bp4-011-P",
        "LL-PR-004-PR",
        "PL!N-bp3-005-P",
        "PL!S-pb1-019-L",
        "PL!SP-bp4-027-L",
        "PL!S-pb1-002-P＋",
        "PL!SP-bp5-001-P",
        "PL!-bp4-008-P",
        "PL!N-bp4-027-L",
        "LL-bp4-001-R＋",
        "PL!-bp4-005-P",
        "PL!S-bp2-008-P",
        "PL!N-bp4-004-P",
        "PL!HS-bp2-018-N",
        "PL!N-bp1-002-P",
        "PL!SP-bp5-011-P",
        "PL!SP-bp1-001-P",
        "PL!HS-bp2-007-P",
        "PL!N-pb1-008-P＋",
        "PL!-pb1-030-L",
        "PL!SP-bp2-010-P",
        "PL!-pb1-001-P＋",
        "PL!S-bp3-007-P",
        "PL!SP-bp4-025-L",
        "PL!S-bp3-019-L",
        "PL!SP-pb1-003-P＋",
        "PL!S-bp3-024-L",
        "PL!SP-bp4-023-L",
        "PL!S-pb1-003-P＋",
        "PL!SP-bp2-006-P",
    ]
    candidate_cards = sorted(list(set(candidate_cards)))

    char_names_jp = {
        "Honoka": "高坂 穂乃果",
        "Umi": "園田 海未",
        "Kotori": "南 ことり",
        "Hanayo": "小泉 花陽",
        "Rin": "星空 凛",
        "Maki": "西木野 真姫",
        "Eli": "絢瀬 絵里",
        "Nozomi": "東條 希",
        "Nico": "矢澤 にこ",
        "Chika": "高海 千歌",
        "Riko": "桜内 梨子",
        "Kanan": "松浦 果南",
        "Dia": "黒澤 ダイヤ",
        "You": "渡辺 曜",
        "Yoshiko": "津島 善子",
        "Hanamaru": "国木田 花丸",
        "Mari": "小原 鞠莉",
        "Ruby": "黒澤 ルビィ",
        "Ayumu": "上原 歩夢",
        "Kasumi": "中須 かすみ",
        "Shizuku": "桜坂 しずく",
        "Karin": "朝香 果林",
        "Ai": "宮下 愛",
        "Kanata": "近江 彼方",
        "Setsuna": "優木 せつ菜",
        "Emma": "エマ・ヴェルデ",
        "Rina": "天王寺 璃奈",
        "Shioriko": "三船 栞子",
        "Lanzhu": "鐘 嵐珠",
        "Mia": "ミア・テイラー",
        "Kanon": "澁谷 かのん",
        "Keke": "唐 可可",
        "Chisato": "嵐 千砂都",
        "Sumire": "平安名 すみれ",
        "Ren": "葉月 恋",
        "Kinako": "桜小路 きな子",
        "Mei": "米女 メイ",
        "Shiki": "若菜 四季",
        "Natsumi": "鬼塚 夏美",
        "Eri": "絢瀬 絵里",
    }

    maps = {
        "en": {
            "attrs": {
                "FILTER": "Filter",
                "MIN": "Min",
                "MAX": "Max",
                "COUNT": "Count",
                "PER_CARD": "for each card in",
                "PER_ENERGY": "for each energy in",
                "UNIT_HASU": "Hasunosora",
                "UNIT_LIEL": "Liella!",
                "UNIT_NIJI": "Nijigasaki",
                "UNIT_AQOURS": "Aqours",
                "UNIT_MUSES": "μ's",
                "UNIQUE_NAMES": "with unique names",
                "STAGE": "Stage",
                "DISCARD": "Discard Pile",
                "HAND": "Hand",
                "SUCCESS_LIVE": "Success Area",
                "NEXT_TURN": "Next Turn",
                "NAME": "Name",
                "GROUP_ID": "Group",
                "ZONE": "Zone",
                "HEART_TYPE": "Heart Color",
                "ANY": "Any",
                "PINK": "Pink",
                "RED": "Red",
                "YELLOW": "Yellow",
                "GREEN": "Green",
                "BLUE": "Blue",
                "PURPLE": "Purple",
                "COST_LE_REVEALED": "Cost <= Revealed Card",
                "BLADE_LE_3": "Blades <= 3",
                "BLADE_LE_2": "Blades <= 2",
                "BLADE_LE_1": "Blades <= 1",
                "STAGE_OR_DISCARD": "Stage or Discard Pile",
                "TYPE_LIVE": "Live card",
                "PLAYER": "Player",
                "OPPONENT": "Opponent",
                "SELF": "This Card",
                "TARGET": "Target",
                "TARGET_MEMBER": "Target Member",
                "BOTH": "Both Players",
                "SCORE_TOTAL": "Total Score",
                "COUNT_SUCCESS_LIVE": "Number of cards in Success Area",
                "COUNT_STAGE": "Number of cards on Stage",
                "COUNT_HAND": "Number of cards in Hand",
                "COUNT_DISCARD": "Number of cards in Discard Pile",
                "COUNT_ENERGY": "Number of Energy chips",
                "COUNT_UNIQUE_NAMES": "Number of unique member names",
                "HAS_MEMBER": "If you have specific Member",
                "HAS_COLOR": "If you have specific Color",
                "IS_CENTER": "If in Center",
                "REVEALED_CONTAINS": "If Revealed cards contain",
                "SCORE_EQUAL_OPPONENT": "If your score equals opponent's",
                "AREA": "Location",
                "FROM": "From",
                "DURATION": "Duration",
                "UNTIL_LIVE_END": "Until Live Ends",
                "TRUE": "Yes",
                "FALSE": "No",
                "ALL": "All",
                "CARD_HAND": "Hand",
                "DISCARD_REMAINDER": "Discard Remainder",
                "REMAINDER": "Remainder",
                "TARGET_1": "Target 1",
                "TARGET_2": "Target 2",
                "SUCCESS_SCORE": "Success Score",
                "LIVE_SET": "Live Set",
                "HEART_LIST": "Heart Colors",
                "TYPE": "Type",
                "ALL_BLADE_AS_ANY_HEART": "ALL-Blade counts as Any Color",
                "HEART_COST_REDUCE": "Reduce Heart Requirement",
                "MODE": "Mode",
                "CENTER_ONLY": "Center Only",
                "OUT_OF_CENTER": "Out of Center",
                "NOT": "If NOT",
                "GROUP": "Group",
                "UNIT_CERISE": "Cerise Bouquet",
                "UNIT_DOLL": "DOLLCHESTRA",
                "UNIT_MIRAKURA": "Mira-Cra Park!",
                "UNIT_BIBI": "BiBi",
                "OPPONENT_HAS_WAIT": "If Opponent has Rested member",
                "TURN_1": "Once per turn",
                "CHECK_IS_IN_DISCARD": "If in Discard Pile",
                "IS_MAIN_PHASE": "During Main Phase",
                "SUCCESS": "If Successful",
                "TAPPED": "Rested",
                "ACTIVATE_AND_SELF": "Target and This Card",
                "X": "X",
                "OTHER_MEMBER": "Other Member",
            },
            "opcodes": {
                "DRAW": "Draw {v} card(s)",
                "ADD_BLADES": "Gain {v} Blade(s)",
                "ADD_HEARTS": "Gain {v} Heart(s)",
                "BOOST_SCORE": "Add {v} to Live Score",
                "SELECT_MODE": "Select a mode",
                "TAP_OPPONENT": "Rest {v} member(s) on stage",
                "PREVENT_ACTIVATE": "Prevent members from being activated",
                "META_RULE": "[Special Rule: {v}]",
                "ADD_TAG": "Gain traits ({v})",
                "MOVE_SUCCESS": "Move {v} card(s) to Success Area",
                "SELECT_LIVE": "Select a Live card",
                "REDUCE_LIVE_SET_LIMIT": "Reduce Live Set limit by {v}",
                "ACTION_YELL_MULLIGAN": "Perform Yell Mulligan",
                "PREVENT_SET_TO_SUCCESS_PILE": "Cannot be placed in Success Area",
                "TRIGGER_YELL_AGAIN": "Trigger Yell again",
                "RESET_YELL_HEARTS": "Reset Hearts gained from Yell",
                "SET_HEART_REQ": "Change required Hearts to {v}",
                "MOVE_TO_DISCARD": "Discard {v} card(s)",
                "ACTIVATE_ENERGY": "Activate {v} Energy",
                "ACTIVATE_MEMBER": "Activate {v} Member(s)",
                "BATON_TOUCH_MOD": "Modify Baton Touch condition",
                "BUFF_POWER": "Gain +{v} Power",
                "CHEER_REVEAL": "Reveal via Cheer",
                "COLOR_SELECT": "Select a Color",
                "DISCARD_HAND": "Discard {v} card(s) from Hand",
                "DRAW_UNTIL": "Draw until you have {v} cards",
                "ENERGY_CHARGE": "Charge {v} Energy",
                "FORMATION_CHANGE": "Change Formation",
                "GRANT_ABILITY": "Grant new ability: {v}",
                "GRANT_HEARTS": "Grant {v} Hearts",
                "INCREASE_COST": "Cost +{v}",
                "INCREASE_HEART_COST": "Heart Cost +{v}",
                "LOOK_AND_CHOOSE": "Look at cards and choose {v}",
                "MOVE_MEMBER": "Move a member on stage",
                "MOVE_TO_DECK": "Move {v} card(s) back to Deck",
                "NEGATE_EFFECT": "Negate an effect",
                "ORDER_DECK": "Reorder the top {v} cards of Deck",
                "PLAY_LIVE_FROM_DISCARD": "Play a Live card from Discard",
                "PLAY_MEMBER_FROM_DISCARD": "Play a Member from Discard",
                "PLAY_MEMBER_FROM_HAND": "Play a Member from Hand",
                "PREVENT_LIVE": "Prevent starting a Live",
                "RECOVER_LIVE": "Retrieve {v} Live(s) from Discard",
                "RECOVER_MEMBER": "Retrieve {v} Member(s) from Discard",
                "REDUCE_COST": "Cost -{v}",
                "REDUCE_HEART_REQ": "Reduce Heart requirement by {v}",
                "REDUCE_YELL_COUNT": "Reduce required Energy for Yell",
                "REVEAL_UNTIL": "Reveal cards until {v}",
                "SELECT_CARDS": "Select {v} card(s)",
                "SELECT_PLAYER": "Select a Player",
                "SET_BLADES": "Set Blades to {v}",
                "SET_SCORE": "Set Live Score to {v}",
                "SWAP_AREA": "Swap card positions",
                "TRANSFORM_COLOR": "Change color to {v}",
                "TRANSFORM_HEART": "Change Heart type to {v}",
                "TRIGGER_REMOTE": "Trigger an ability remotely",
                "TAP_MEMBER": "Rest {v} of your members",
                "DISCARD_SUCCESS_LIVE": "Discard {v} card(s) from Success Area",
                "PLAY_LIVE_FROM_HAND": "Play {v} Live card(s) from Hand",
                "SELECT_MEMBER": "Select {v} Member(s)",
                "LOOK_AND_CHOOSE_ORDER": "Look at {v} cards and reorder",
                "PAY_ENERGY": "Pay {v} Energy",
                "ACTIVATE_ENERGY": "Activate {v} Energy",
            },
            "steps": {
                "TRIGGER": "### Step: {v}",
                "CONDITION": "&nbsp;&nbsp;&nbsp;&nbsp;**Condition:** {v}",
                "COST": "&nbsp;&nbsp;&nbsp;&nbsp;**Cost:** {v}",
                "EFFECT": "&nbsp;&nbsp;&nbsp;&nbsp;**Effect:** {v}",
                "OPTION": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**Choice:** {v}",
                "ON_PLAY": "When Played",
                "ON_LIVE_START": "When Live Starts",
                "ON_LIVE_SUCCESS": "When Live Succeeds",
                "CONSTANT": "Always Active",
                "ACTIVATED": "When Activated",
                "ON_REVEAL": "When Revealed by Yell",
                "ON_POSITION_CHANGE": "When Position Changes",
                "TURN_START": "Turn Start",
                "TURN_END": "Turn End",
                "ON_STAGE_ENTRY": "When member enters Stage",
            },
        },
        "jp": {
            "attrs": {
                "FILTER": "フィルタ",
                "MIN": "最小",
                "MAX": "最大",
                "COUNT": "数",
                "PER_CARD": "（〜の枚数につき）",
                "PER_ENERGY": "（〜のエネルギーにつき）",
                "STAGE": "ステージ",
                "DISCARD": "控え室",
                "HAND": "手札",
                "SUCCESS_LIVE": "成功ライブ",
                "NAME": "カード名",
                "GROUP_ID": "グループ",
                "HEART_TYPE": "ハートの色",
                "ANY": "どの色でもよい",
                "PINK": "ピンク",
                "RED": "レッド",
                "YELLOW": "イエロー",
                "GREEN": "グリーン",
                "BLUE": "ブルー",
                "PURPLE": "パープル",
                "PLAYER": "自分",
                "OPPONENT": "相手",
                "SELF": "このカード",
                "BOTH": "自分と相手",
                "SCORE_TOTAL": "合計スコア",
                "COUNT_SUCCESS_LIVE": "成功ライブの枚数",
                "HAS_MEMBER": "特定のメンバーがいる場合",
                "NOT": "〜でない場合",
                "SCORE_EQUAL_OPPONENT": "自分と相手のスコアが同じ場合",
                "ALL": "すべて",
                "UNIT_LIEL": "Liella!",
                "UNIT_AQOURS": "Aqours",
                "UNIT_NIJI": "虹ヶ咲",
                "UNIT_MUSES": "μ's",
                "CARD_HAND": "手札",
                "DISCARD_REMAINDER": "残りを控え室に",
                "REMAINDER": "残りのカード",
                "TARGET_1": "対象1",
                "TARGET_2": "対象2",
                "UNTIL_LIVE_END": "ライブ終了時まで",
                "SUCCESS_SCORE": "成功時スコア",
                "LIVE_SET": "セットしたライブ",
                "COST_LE_REVEALED": "公開されたカードのコスト以下",
                "BLADE_LE_3": "ブレード数が3以下",
                "BLADE_LE_2": "ブレード数が2以下",
                "BLADE_LE_1": "ブレード数が1以下",
                "HEART_LIST": "ハートの色リスト",
                "TYPE": "種類",
                "ALL_BLADE_AS_ANY_HEART": "ALLブレードを任意のハートとして扱う",
                "HEART_COST_REDUCE": "必要ハートを減らす",
                "SCORE_TOTAL": "合計スコア",
                "MODE": "モード",
                "CENTER_ONLY": "センター限定",
                "OUT_OF_CENTER": "センター以外へ",
                "NOT": "〜でないなら",
                "GROUP": "協力体制",
                "UNIT_CERISE": "スリーズブーケ",
                "UNIT_DOLL": "DOLLCHESTRA",
                "UNIT_MIRAKURA": "みらくらぱーく！",
                "UNIT_BIBI": "BiBi",
                "OPPONENT_HAS_WAIT": "相手にウェイト状態のメンバーがいる場合",
                "TURN_1": "ターン1回",
                "CHECK_IS_IN_DISCARD": "控え室にいる場合",
                "IS_MAIN_PHASE": "メインフェイズの場合",
                "IS_CENTER": "センターの場合",
                "SUCCESS": "成功した場合",
                "TAPPED": "ウェイト状態",
                "ACTIVATE_AND_SELF": "アクティブにしたメンバーとこのカード",
                "X": "X",
                "OTHER_MEMBER": "それ以外のメンバー",
                "0": "ピンク",
                "1": "レッド",
                "2": "イエロー",
                "3": "グリーン",
                "4": "ブルー",
                "5": "パープル",
            },
            "opcodes": {
                "DRAW": "カードを{v}引く",
                "ADD_BLADES": "ブレードを{v}得る",
                "ADD_HEARTS": "ハートを{v}得る",
                "BOOST_SCORE": "スコアを＋{v}する",
                "SELECT_MODE": "モードを選択する",
                "TAP_OPPONENT": "相手のメンバーを{v}ウェイトにする",
                "META_RULE": "[特殊ルール: {v}]",
                "MOVE_SUCCESS": "カード{v}を成功ライブに置く",
                "ACTION_YELL_MULLIGAN": "エールのやり直しを行う",
                "PREVENT_SET_TO_SUCCESS_PILE": "成功ライブに置くことができない",
                "MOVE_TO_DISCARD": "カード{v}を控え室に置く",
                "DISCARD_HAND": "手札を{v}控え室に置く",
                "SELECT_MEMBER": "メンバー{v}を選ぶ",
                "LOOK_AND_CHOOSE": "カードを{v}見て選ぶ",
                "REDUCE_LIVE_SET_LIMIT": "セット上限を-{v}する",
                "SET_HEART_REQ": "必要ハートを{v}に変更する",
                "BUFF_POWER": "パワーを+{v}する",
                "TRIGGER_YELL_AGAIN": "もう一度エールを行う",
                "RESET_YELL_HEARTS": "エールのハートをリセットする",
                "SELECT_LIVE": "ライブカードを1枚選ぶ",
                "INCREASE_COST": "コストを+{v}する",
                "SCORE_TOTAL": "合計スコアをチェックする",
                "RECOVER_MEMBER": "控え室からメンバーを{v}手札に加える",
                "RECOVER_LIVE": "控え室からライブカードを{v}手札に加える",
                "REDUCE_HEART_REQ": "必要ハートを-{v}する",
                "ACTIVATE_ENERGY": "エネルギー{v}をアクティブにする",
                "CHEER_REVEAL": "{v}をエールとして公開する",
                "LOOK_AND_CHOOSE_ORDER": "カードを{v}見て並べ替える",
                "PAY_ENERGY": "エネルギーを{v}支払う",
                "PLAY_MEMBER_FROM_DISCARD": "控え室からメンバー{v}を登場させる",
                "ACTIVATE_MEMBER": "メンバー{v}をアクティブにする",
                "ADD_TAG": "属性「{v}」を得る",
                "REVEAL_UNTIL": "{v}が公開されるまでデッキをめくる",
                "TAP_MEMBER": "自分のメンバー{v}をウェイトにする",
                "DISCARD_SUCCESS_LIVE": "成功ライブからカードを{v}控え室に置く",
            },
            "steps": {
                "TRIGGER": "### ステップ: {v}",
                "CONDITION": "&nbsp;&nbsp;&nbsp;&nbsp;**条件:** {v}",
                "COST": "&nbsp;&nbsp;&nbsp;&nbsp;**コスト:** {v}",
                "EFFECT": "&nbsp;&nbsp;&nbsp;&nbsp;**効果:** {v}",
                "OPTION": "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;**選択肢:** {v}",
                "ON_PLAY": "登場時",
                "ON_LIVE_START": "ライブ開始時",
                "ON_LIVE_SUCCESS": "ライブ成功時",
                "CONSTANT": "常時",
                "ACTIVATED": "起動",
                "ON_REVEAL": "エールで公開された時",
                "ON_POSITION_CHANGE": "移動した時",
                "ON_STAGE_ENTRY": "メンバーが登場した時",
            },
        },
    }

    def translate_complex(raw_text, lang):
        if not raw_text or raw_text == "N/A":
            return "N/A"
        t = maps[lang]
        processed = raw_text

        def handle_patterns(val):
            val = re.sub(
                r"COST_LE_(\d+)",
                (lambda m: f"Cost <= {m.group(1)}" if lang == "en" else f"コスト {m.group(1)}以下"),
                val,
            )
            val = re.sub(
                r"COST_GE_(\d+)",
                (lambda m: f"Cost >= {m.group(1)}" if lang == "en" else f"コスト {m.group(1)}以上"),
                val,
            )
            val = re.sub(
                r"BLADE_LE_(\d+)",
                (lambda m: f"Blades <= {m.group(1)}" if lang == "en" else f"ブレード数 {m.group(1)}以下"),
                val,
            )
            val = re.sub(
                r"BLADE_GE_(\d+)",
                (lambda m: f"Blades >= {m.group(1)}" if lang == "en" else f"ブレード数 {m.group(1)}以上"),
                val,
            )
            # Handle technical terms that might be missed in attribute mapping but appear in direct strings
            if lang == "jp":
                val = val.replace("COST_LE_REVEALED", "公開されたカードのコスト以下")
            return val

        all_logic = {**t["opcodes"], **t["steps"]}
        for k in sorted(all_logic.keys(), key=len, reverse=True):
            replacement = all_logic[k]

            def sub_val(match):
                val = match.group(1).strip()
                if val == "99":
                    readable_val = "すべて" if lang == "jp" else "all"
                elif val.isdigit():
                    if lang == "jp":
                        if k in [
                            "DRAW",
                            "MOVE_SUCCESS",
                            "MOVE_TO_DISCARD",
                            "DISCARD_HAND",
                            "LOOK_AND_CHOOSE",
                            "RECOVER_MEMBER",
                            "RECOVER_LIVE",
                            "PLAY_MEMBER_FROM_DISCARD",
                            "DISCARD_SUCCESS_LIVE",
                        ]:
                            readable_val = f"{val}枚"
                        elif k in ["SELECT_MEMBER", "TAP_OPPONENT", "ACTIVATE_MEMBER", "TAP_MEMBER"]:
                            readable_val = f"{val}人"
                        else:
                            readable_val = val
                    else:
                        readable_val = val
                else:
                    readable_val = handle_patterns(val)
                return replacement.replace("{v}", readable_val)

            processed = re.sub(rf"\b{k}\((.*?)\)", sub_val, processed)
            processed = re.sub(rf"\b{k}\b", replacement.replace("{v}", ""), processed)

        words_to_map = [
            "PLAYER",
            "OPPONENT",
            "SELF",
            "BOTH",
            "TARGET_MEMBER",
            "CARD_HAND",
            "DISCARD_REMAINDER",
            "SCORE_TOTAL",
            "NOT",
            "IS_CENTER",
            "TURN_1",
            "OPPONENT_HAS_WAIT",
            "CHECK_IS_IN_DISCARD",
            "IS_MAIN_PHASE",
            "SUCCESS",
            "TAPPED",
            "ACTIVATE_AND_SELF",
            "OTHER_MEMBER",
        ]
        if lang == "jp":
            processed = processed.replace("->", " targeting ")
            for w in words_to_map:
                processed = re.sub(rf"\b{w}\b", t["attrs"].get(w, w), processed)
            processed = processed.replace(" targeting ", " → 対象：")
        else:
            processed = processed.replace("->", " targeting ")
            for w in words_to_map:
                processed = re.sub(rf"\b{w}\b", t["attrs"].get(w, w), processed)

        def sub_attr(match):
            content = match.group(1)
            translated_parts = []
            parts = re.split(r',(?=(?:[^"]*"[^"]*")*[^"]*$)', content)
            for p in parts:
                p = p.strip().strip('"')
                if "=" in p:
                    k_v = p.split("=", 1)
                    if len(k_v) == 2:
                        k, v = k_v[0].strip(), k_v[1].strip().strip('"')
                        v_parts = v.split("/")
                        mapped_v_parts = []
                        for vp in v_parts:
                            vp = vp.strip()
                            if lang == "jp" and k == "FILTER":
                                jp_name = char_names_jp.get(vp, t["attrs"].get(vp, vp))
                                mapped_v_parts.append(handle_patterns(jp_name))
                            else:
                                mapped_v_parts.append(t["attrs"].get(vp, vp))
                        tv = "/".join(mapped_v_parts)
                        tv = handle_patterns(tv)
                        translated_parts.append(f"{t['attrs'].get(k, k)}={tv}")
                    else:
                        translated_parts.append(handle_patterns(t["attrs"].get(k_v[0], k_v[0])))
                else:
                    translated_parts.append(handle_patterns(t["attrs"].get(p, p)))
            return " (" + ", ".join(translated_parts) + ")"

        processed = re.sub(r"\{(.*?)\}", sub_attr, processed)

        if lang == "jp":
            processed = processed.replace("[特殊ルール: ]", "[特殊ルール]")
            processed = processed.replace("Specific Details", "詳細")
            processed = processed.replace("すべて枚", "すべて")
            processed = processed.replace("すべて人", "すべて")

        final_lines = []
        step_key = "### ステップ:" if lang == "jp" else "### Step:"
        for line in [l.strip() for l in processed.split("\n") if l.strip()]:
            final_lines.append(f"\n{line}" if step_key in line else line)
        return "\n".join(final_lines).replace(": ", " ").strip()

    report = "# Logic Robustness Audit Report\n\nGenerated bilingual audit for game logic verification.\n\n"
    for cid in candidate_cards:
        c, p = cards.get(cid, {}), pseudo.get(cid, {})
        report += f"## {cid}: {c.get('name', 'N/A')}\n**Original Japanese:**\n{c.get('ability', 'N/A')}\n\n"
        report += f"**Compiled Logic (Pseudocode):**\n```\n{p.get('pseudocode', 'N/A')}\n```\n\n"
        report += (
            f"**Friendly Japanese (Verification Mode):**\n{translate_complex(p.get('pseudocode', 'N/A'), 'jp')}\n\n"
        )
        report += f"**Friendly English (Internal Audit Mode):**\n{translate_complex(p.get('pseudocode', 'N/A'), 'en')}\n\n---\n\n"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Append the script itself to the report for self-documentation
    try:
        with open(__file__, "r", encoding="utf-8") as f:
            script_content = f.read()
        report += (
            "## Generator Source Code\nThis report was automatically generated using the following script:\n\n```python\n"
            + script_content
            + "\n```\n"
        )
    except Exception as e:
        report += f"\n\n> [!WARNING]\n> Could not append generator script: {str(e)}\n"

    with open(output_path, "w", encoding="utf-8-sig") as f:
        f.write(report)
    print(f"Report generated: {output_path}")


if __name__ == "__main__":
    generate_audit_report()
