from engine.game.enums import Phase
from engine.game.state_utils import get_base_id


def get_v(obj, key, default=None):
    """Safely get a value from a dictionary or an object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    # Handle pydantic/dataclass/custom objects
    return getattr(obj, key, default)


def get_ability_summary(ab, lang="jp"):
    """
    Generate a specific human-readable summary of an ability.
    """
    if not ab:
        return ""

    trigger = int(get_v(ab, "trigger", 0))
    if lang == "jp":
        t_map = {
            1: "登場時",
            2: "ライブ進行時",
            3: "ライブ成功時",
            4: "ターン開始時",
            5: "ターン終了時",
            6: "常時",
            7: "起動",
        }
        t_desc = t_map.get(trigger, "")
        prefix = f"【{t_desc}】" if t_desc else ""
    else:
        t_map = {1: "OnPlay", 2: "LiveStart", 3: "Success", 4: "TurnStart", 5: "TurnEnd", 6: "Constant", 7: "Act"}
        t_desc = t_map.get(trigger, "")
        prefix = f"[{t_desc}]" if t_desc else ""

    effects = get_v(ab, "effects", [])
    if not effects:
        raw = get_v(ab, "raw_text", "").split("\n")[0][:25]
        return f"{prefix} {raw}..." if lang == "en" else f"{prefix}{raw}"

    eff = effects[0]
    etype = int(get_v(eff, "effect_type", -1))
    val = get_v(eff, "value", 0)
    target = int(get_v(eff, "target", 0))
    params = get_v(eff, "params", {})

    # Target Mapping
    if lang == "jp":
        tg_map = {1: "自分", 2: "相手", 3: "全員", 4: "自身", 12: "相手メン"}
    else:
        tg_map = {1: "Player", 2: "Opponent", 3: "All", 4: "Self", 12: "OppMem"}
    tg_name = tg_map.get(target, "")

    # Effect Detail Mapping
    if lang == "jp":
        e_map = {
            0: "ドロー",
            1: "ブレード+",
            2: "ハート+",
            3: "コスト-",
            4: "デッキ確認",
            5: "ライブ回収",
            6: "スコア+",
            7: "回収",
            8: "パワー+",
            9: "効果無効",
            10: "移動",
            11: "手札交換",
            12: "サーチ",
            13: "エネチャージ",
            15: "並べ替え",
            17: "選択",
            20: "下に置く",
            19: "タップ",
            27: "見て選ぶ",
            30: "手札に加える",
            31: "ブレード固定",
            37: "色選択",
            38: "スコア計算変更",
            41: "控えに置く",
            44: "エール減",
            46: "支払い",
            48: "ドロー",
            81: "エネ回復",
        }
    else:
        e_map = {
            0: "Draw",
            1: "Blades+",
            2: "Hearts+",
            3: "Cost-",
            4: "LookDeck",
            5: "RecLive",
            6: "Score+",
            7: "RecMem",
            8: "Power+",
            9: "Immune",
            10: "Move",
            11: "Swap",
            12: "Search",
            13: "Energy+",
            15: "SortDeck",
            17: "Choice",
            20: "PutUnder",
            19: "TapOpp",
            27: "PickDeck",
            30: "AddToHand",
            31: "SetBlade",
            37: "ColorChoice",
            38: "ScoreMod",
            41: "ToDiscard",
            44: "Yell-",
            46: "Pay",
            48: "DrawUntil",
            81: "ActEnergy",
        }

    e_name = e_map.get(etype, f"Eff{etype}")

    # Specific tweaks for common complex effects
    if etype == 17:  # SELECT_MODE
        opts = params.get("options", [])
        e_name = f"択{len(opts)}" if lang == "jp" else f"Choose{len(opts)}"
        val = 0
    elif etype == 27:  # LOOK_AND_CHOOSE
        e_name = f"{val}見選" if lang == "jp" else f"Pick{val}Deck"
        val = 0
    elif etype == 48:  # DRAW_UNTIL
        e_name = f"手札{val}枚まで引く" if lang == "jp" else f"DrawTo{val}"
        val = 0

    # Build final string
    parts = []
    if prefix:
        parts.append(prefix)
    if tg_name and target not in (0, 4):
        parts.append(tg_name)
    parts.append(e_name)
    if val > 0:
        parts.append(str(val))

    # Add filter hint if short
    filt = params.get("filter", "")
    if filt:
        # Clean up common filter blocks
        clean_filt = filt.replace("CHARACTER_", "").replace("GROUP_", "").replace("COLOR_", "")
        if len(clean_filt) < 15:
            parts.append(f"({clean_filt})")

    return "".join(parts) if lang == "jp" else " ".join(parts)


def get_action_desc(a, gs, lang="jp", text=None):
    """
    Generate clear, informative action descriptions.
    Shows card names, costs, and ability sources for better user understanding.
    """
    if gs is None:
        return f"Action {a}"

    ability_prefix = ""
    if text:
        # Use first line of ability text as prefix
        clean_text = text.replace("【", "[").replace("】", "]").split("\n")[0].strip()
        if len(clean_text) > 30:
            clean_text = clean_text[:27] + "..."
        ability_prefix = f"[{clean_text}] " if lang == "en" else f"【{clean_text}】"

    # Localization helper
    def t(key, **kwargs):
        templates = {
            "jp": {
                "pass": "【終了】メインフェイズを終了する",
                "confirm_mulligan": "【確認】マリガンを実行",
                "skip_ability": "【スキップ】{source}の効果を使用しない",
                "main_end": "【終了】メインフェイズを終了する",
                "live_confirm": "【確認】ライブカードをセットして続行",
                "next": "【進む】次へ進む",
                "color_select_label": "【色選択】 {color}",
                "stage_select_label": "【ステージ選択】 {area}: {name}を{desc}",
                "hand_select_label": "【手札選択】 {name}を{desc}",
                "mode_select_label": "【モード選択】 {mode}",
                "ability_solve": "【能力解決】 {source}の効果を発動 ({idx}/{total})",
                "live_select": "【ライブ選択】 {area}: {name}",
                "performance": "【パフォーマンス】 {area}: {name} ({summary})",
                "sort_top": "【並べ替え】 {name}を一番上へ",
                "sort_confirm": "【確定】 並び替えを終了",
                "target_opp": "【ターゲット】 相手のステージ ({area}: {name}) を選択",
                "list_select": "【リスト選択】 {name}",
                "generic_select": "【選択】 {name}",
                "choice_fallback": "【選択肢】 {idx}",
                "discard_solve": "【控え召喚】 {name}: {summary}",
                "discard_fallback": "【控え室】 {name}",
                "deck_top": "デッキトップ: {name}",
                "color_choice": "色選択: {color}",
                "place_on": "【{area}に置く】 {name}{suffix} (バトンタッチ: {old_name}退場, 支払:{cost})",
                "place_on_new": "【{area}に置く】 {name}{suffix} (コスト {cost})",
                "energy_charge": "【エネルギー】 {name}をチャージ",
                "mulligan_toggle": "【マリガン】 {name}を選択/解除",
                "live_set": "【ライブセット】 {name}",
                "activated_ability": "【起動】{name}: {summary} ({area})",
                "none": "なし",
                "empty_area": "空エリア",
                "member": "メンバー",
                "ability": "アビリティ",
                "unknown": "不明",
                "discard": "捨てる",
                "recover": "回収",
                "wait": "ウェイト",
                "move_src": "移動元",
                "place_to": "に置く",
                "select": "選択",
                "confirm": "確定",
                "pass_action": "【パス】何もしない",
                "order_deck": "並べ替え",
                "select_member": "メンバー選択",
                "target_opp_member": "ターゲット選択",
                "select_success": "成功ライブ選択",
                "select_discard": "控え室回収",
                "select_hand": "手札選択",
                "select_discard_hand": "【手札破棄】 捨てるカードを選択",
                "colors": ["赤", "青", "緑", "黄", "紫", "ピンク"],
                "areas": ["左", "センター", "右"],
                "areas_short": ["左", "中", "右"],
            },
            "en": {
                "pass": "[End] End Main Phase",
                "confirm_mulligan": "[Confirm] Execute Mulligan",
                "skip_ability": "[Skip] Do not use {source}'s effect",
                "main_end": "[End] End Main Phase",
                "live_confirm": "[Confirm] Set Live card and continue",
                "next": "[Next] Proceed",
                "color_select_label": "[Color] Select {color}",
                "stage_select_label": "[Stage] {area}: {desc} {name}",
                "hand_select_label": "[Hand] {desc} {name}",
                "mode_select_label": "[Mode] {mode}",
                "ability_solve": "[Ability] Activate {source}'s effect ({idx}/{total})",
                "live_select": "[Live] {area}: {name}",
                "performance": "[Performance] {area}: {name} ({summary})",
                "sort_top": "[Sort] Move {name} to top",
                "sort_confirm": "[Confirm] End sorting",
                "target_opp": "[Target] Opponent's stage ({area}: {name})",
                "list_select": "[List] Select {name}",
                "generic_select": "[Select] {name}",
                "choice_fallback": "[Choice] {idx}",
                "discard_solve": "[Discard Act] {name}: {summary}",
                "discard_fallback": "[Discard] {name}",
                "deck_top": "Top: {name}",
                "color_choice": "Color: {color}",
                "place_on": "[To {area}] {name}{suffix} (Baton Touch: {old_name} leaves, Pay:{cost})",
                "place_on_new": "[To {area}] {name}{suffix} (Cost {cost})",
                "energy_charge": "[Energy] Charge {name}",
                "mulligan_toggle": "[Mulligan] Toggle {name}",
                "live_set": "[Live Set] {name}",
                "activated_ability": "[Act] {name}: {summary} ({area})",
                "none": "None",
                "empty_area": "Empty",
                "member": "Member",
                "ability": "Ability",
                "unknown": "Unknown",
                "discard": "Discard",
                "recover": "Recover",
                "wait": "Wait",
                "move_src": "Move From",
                "place_to": "Place to",
                "select": "Select",
                "confirm": "Confirm",
                "pass_action": "[Pass] Do nothing",
                "order_deck": "Sort Deck",
                "select_member": "Select Member",
                "target_opp_member": "Target Opponent",
                "select_success": "Select Success Live",
                "select_discard": "Recover from Discard",
                "select_hand": "Select from Hand",
                "select_discard_hand": "Select card to discard",
                "colors": ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"],
                "areas": ["Left", "Center", "Right"],
                "areas_short": ["Left", "Mid", "Right"],
            },
        }
        lang_data = templates.get(lang, templates["jp"])
        res = lang_data.get(key, key)
        if isinstance(res, str):
            try:
                formatted = res.format(**kwargs)
                return ability_prefix + formatted
            except KeyError:
                return ability_prefix + res
        return res

    # Handle both Python and Rust engine (PyGameState)
    if hasattr(gs, "get_player"):
        p_idx = gs.current_player
        p = gs.get_player(p_idx)
    else:
        p = gs.active_player
        p_idx = gs.current_player

    member_db = gs.member_db
    live_db = gs.live_db

    # Helper to get from DB, handling int/str keys
    def get_from_db(db, key, default=None):
        if not db:
            return default
        if hasattr(db, "get"):
            res = db.get(key)
            if res is not None:
                return res
            return db.get(str(key), default)
        try:
            if key in db:
                return db[key]
            if str(key) in db:
                return db[str(key)]
        except:
            pass
        return default

    # Helper to get card name
    def get_card_name(cid, gs_override=None):
        _gs = gs_override or gs
        if cid < 0:
            return t("none")

        base_id = get_base_id(int(cid))

        # Try all DBs with the helper
        m = get_from_db(member_db, base_id)
        if m:
            name = get_v(m, "name", f"{t('member')} #{base_id}")
            card_no = get_v(m, "card_no", "??")
            return f"{name} ({card_no})"

        l = get_from_db(live_db, base_id)
        if l:
            name = get_v(l, "name", f"ライブ #{base_id}")
            card_no = get_v(l, "card_no", "??")
            return f"{name} ({card_no})"

        e = get_from_db(getattr(_gs, "energy_db", None), base_id)
        if e:
            name = get_v(e, "name", f"エネルギー #{base_id}")
            card_no = get_v(e, "card_no", "??")
            return f"{name} ({card_no})"

        return f"カード #{cid}"

    # Helper for pending choices
    def get_top_pending():
        if not gs.pending_choices:
            return None, {}
        choice_type, params = gs.pending_choices[0]
        if isinstance(params, str):
            import json

            try:
                return choice_type, json.loads(params)
            except:
                return choice_type, {}
        return choice_type, params

    # --- ACTION HANDLERS ---

    # Action 0: Pass / Confirm / Skip
    if a == 0:
        if int(gs.phase) == int(Phase.MAIN):
            return t("main_end")
        if int(gs.phase) == int(Phase.LIVE_SET):
            return t("live_confirm")
        if int(gs.phase) == int(Phase.LIVE_RESULT):
            return t("next")
        if int(gs.phase) in (int(Phase.MULLIGAN_P1), int(Phase.MULLIGAN_P2)):
            return t("confirm_mulligan")
        choice_type, params = get_top_pending()
        if choice_type:
            source_name = params.get("source_member", t("ability"))
            return t("skip_ability", source=source_name)
        return t("pass_action")

    # 580-585: Color Selection
    if 580 <= a <= 585:
        colors = t("colors")
        return t("color_select_label", color=colors[a - 580])

    # 560-562: Stage Slot Selection
    if 560 <= a <= 562:
        idx = a - 560
        areas = t("areas")
        cid = p.stage[idx]
        name = t("empty_area")
        base_id = get_base_id(int(cid))
        if cid >= 0:
            m = get_from_db(member_db, base_id)
            if m:
                name = get_v(m, "name", t("member"))

        desc = t("select")
        choice_type, params = get_top_pending()
        if choice_type:
            if choice_type == "MOVE_MEMBER":
                desc = t("move_src")
            elif choice_type == "TAP_MEMBER":
                desc = t("wait")
            elif choice_type in ("PLAY_MEMBER_FROM_HAND", "PLAY_MEMBER_FROM_DISCARD"):
                desc = t("place_to")
        return t("stage_select_label", area=areas[idx], name=name, desc=desc)

    # 500-509: Hand Card Selection
    if 500 <= a <= 509:
        idx = a - 500
        if idx < len(p.hand):
            cid = p.hand[idx]
            name = get_card_name(cid)
            desc = t("select")
            choice_type, params = get_top_pending()
            if choice_type:
                if choice_type == "RECOVER_MEMBER":
                    desc = t("recover")
                elif choice_type == "DISCARD":
                    desc = t("discard")
            return t("hand_select_label", name=name, desc=desc)

    # 570-579: Mode Selection
    if 570 <= a <= 579:
        choice_type, params = get_top_pending()
        mode_label = f"Mode {a - 570 + 1}"
        if choice_type:
            options = params.get("options", [])
            if a - 570 < len(options):
                mode_label = options[a - 570]
        return t("mode_select_label", mode=mode_label)

    # 590-599: Ability Trigger/Resolution Order
    if 590 <= a <= 599:
        idx = a - 590
        if idx < len(gs.triggered_abilities):
            t_obj = gs.triggered_abilities[idx]
            if len(t_obj) >= 2:
                cid = getattr(t_obj[2], "card_id", -1) if len(t_obj) > 2 else -1
                src_name = get_card_name(cid) if cid >= 0 else t("unknown")
                return t("ability_solve", source=src_name, idx=idx + 1, total=len(gs.triggered_abilities))
        return t("ability_solve", source="???", idx=idx + 1, total=len(gs.triggered_abilities))

    # 820-822: Live Zone Targeting
    if 820 <= a <= 822:
        idx = a - 820
        areas = t("areas")
        cid = p.live_zone[idx] if idx < len(p.live_zone) else -1
        name = t("none")
        if cid >= 0:
            name = get_card_name(cid)
        return t("live_select", area=areas[idx], name=name)

    # 900-902: Performance Execution
    if 900 <= a <= 902:
        idx = a - 900
        areas = t("areas")
        cid = p.live_zone[idx] if idx < len(p.live_zone) else -1
        name = t("none")
        summary = "Performance"
        if cid >= 0:
            name = get_card_name(cid)
            base_id = get_base_id(cid)
            live = get_from_db(live_db, base_id)
            if live:
                abilities = get_v(live, "abilities", [])
                if abilities:
                    summary = get_ability_summary(abilities[0], lang=lang)
        return t("performance", area=areas[idx], name=name, summary=summary)

    # 600-719: Broad Choice Range
    if 600 <= a <= 719:
        idx = a - 600
        choice_type, params = get_top_pending()

        # Context-aware mapping using choice_type
        type_mapping = {
            "ORDER_DECK": "order_deck",
            "SELECT_MEMBER": "select_member",
            "TARGET_OPPONENT_MEMBER": "target_opp_member",
            "SELECT_FROM_LIST": "list_select",
            "SELECT_MODE": "select",
            "SELECT_SUCCESS_LIVE": "select_success",
            "SELECT_FROM_DISCARD": "select_discard",
            "SELECT_FROM_HAND": "select_hand",
        }
        type_key = type_mapping.get(choice_type, "generic_select")

        if choice_type == "ORDER_DECK":
            cards = params.get("cards", [])
            if idx < len(cards):
                return t("sort_top", name=get_card_name(cards[idx]))
            return t("sort_confirm")

        if idx <= 2 and choice_type in ("SELECT_MEMBER", "TARGET_OPPONENT_MEMBER"):
            areas = t("areas")
            opp = gs.get_player(1 - p_idx) if hasattr(gs, "get_player") else gs.inactive_player
            cid = opp.stage[idx]
            name = t("empty_area")
            if cid >= 0:
                base_id = get_base_id(int(cid))
                m = get_from_db(member_db, base_id)
                if m:
                    name = get_v(m, "name", t("member"))
            return t("target_opp", area=areas[idx], name=name)

        # Handle list choices
        params_cards = params.get("cards", [])
        if idx < len(params_cards):
            return t("list_select", name=get_card_name(params_cards[idx]))

        options = params.get("options", [])
        if idx < len(options):
            return t("generic_select", name=options[idx])

        if choice_type == "SELECT_SUCCESS_LIVE":
            idx = a - 600
            if idx <= 2:
                areas = t("areas")
                cid = p.live_zone[idx] if hasattr(p, "live_zone") and idx < len(p.live_zone) else -1
                name = t("unknown")
                if cid >= 0:
                    name = get_card_name(cid)
                return t("live_select", area=areas[idx], name=name)

        return f"{t(type_key)}: {t('choice_fallback', idx=idx + 1)}"

    # 550-849: Complex Choice Resolution
    if 550 <= a <= 849:
        adj = a - 550
        area_idx = adj // 100
        ab_idx = (adj % 100) // 10
        choice_idx = adj % 10

        areas_short = t("areas_short")
        area_name = areas_short[area_idx] if area_idx < 3 else f"Slot {area_idx}"
        cid = p.stage[area_idx] if area_idx < 3 else -1
        card_name = t("member")
        if cid >= 0:
            base_id = get_base_id(cid)
            m = get_from_db(member_db, base_id)
            if m:
                card_name = get_v(m, "name", t("member"))

        choice_type, params = get_top_pending()
        choice_label = t("choice_fallback", idx=choice_idx + 1)

        if choice_type == "ORDER_DECK":
            cards = params.get("cards", [])
            if choice_idx < len(cards):
                choice_label = t("deck_top", name=get_card_name(cards[choice_idx]))
            else:
                choice_label = t("confirm")
        elif choice_type == "COLOR_SELECT":
            colors = t("colors")
            if choice_idx < len(colors):
                choice_label = t("color_choice", color=colors[choice_idx])
        elif choice_type == "SELECT_MODE":
            options = params.get("options", [])
            if choice_idx < len(options):
                choice_label = options[choice_idx]
        elif choice_type == "SELECT_FROM_LIST":
            cards = params.get("cards", [])
            if choice_idx < len(cards):
                choice_label = t("list_select", name=get_card_name(cards[choice_idx]))
        elif choice_type == "SELECT_HAND_DISCARD":
            if choice_idx < len(p.hand):
                cid = p.hand[choice_idx]
                choice_label = t("select_discard_hand") + ": " + get_card_name(cid)
            else:
                choice_label = t("discard")

        return f"[{card_name}] {choice_label} ({area_name})"

    # 1-180: Playing Members (Main Phase)
    if 1 <= a <= 180 and int(gs.phase) == int(Phase.MAIN):
        idx = (a - 1) // 3
        area_idx = (a - 1) % 3
        areas = t("areas")
        area_name = areas[area_idx]
        card_name = f"Card[{idx}]"
        new_card_cost = 0
        suffix = ""
        if idx < len(p.hand):
            cid = p.hand[idx]
            base_cid = get_base_id(int(cid))
            m = get_from_db(member_db, base_cid)
            if m:
                card_name = get_v(m, "name", t("member"))
                new_card_cost = get_v(m, "cost", 0)
                abilities = get_v(m, "abilities", [])
                if any(get_v(ab, "trigger", 0) == 1 for ab in abilities):
                    suffix = " [On Play]" if lang == "en" else " [登場]"

        stage_cid = p.stage[area_idx]
        if stage_cid >= 0:
            base_stage_cid = get_base_id(int(stage_cid))
            old_card = get_from_db(member_db, base_stage_cid)
            if old_card:
                old_name = get_v(old_card, "name", t("member"))
                old_cost = get_v(old_card, "cost", 0)
                actual_cost = max(0, new_card_cost - old_cost)
                return t("place_on", area=area_name, name=card_name, suffix=suffix, old_name=old_name, cost=actual_cost)
        return t("place_on_new", area=area_name, name=card_name, suffix=suffix, cost=new_card_cost)

    # 100-159: Energy Charge Selection
    if 100 <= a <= 159 and int(gs.phase) == int(Phase.ENERGY):
        idx = a - 100
        card_name = f"Hand[{idx}]"
        if idx < len(p.hand):
            card_name = get_card_name(p.hand[idx])
        return t("energy_charge", name=card_name)

    # 300-359: Mulligan Selection
    if 300 <= a <= 359:
        idx = a - 300
        card_name = f"Hand[{idx}]"
        if idx < len(p.hand):
            card_name = get_card_name(p.hand[idx])
        return t("mulligan_toggle", name=card_name)

    # 400-459: Live Set Selection
    if 400 <= a <= 459:
        idx = a - 400
        card_name = f"Hand[{idx}]"
        if idx < len(p.hand):
            cid = p.hand[idx]
            card_name = get_card_name(cid)
        return t("live_set", name=card_name)

    # 200-299: Activated Ability on Stage
    if 200 <= a <= 299:
        adj = a - 200
        area_idx = adj // 10
        ab_idx = adj % 10
        areas = t("areas")
        area_name = areas[area_idx] if area_idx < 3 else f"Slot {area_idx}"
        cid = p.stage[area_idx] if area_idx < 3 else -1
        if cid >= 0:
            base_cid = get_base_id(int(cid))
            member = get_from_db(member_db, base_cid)
            if member:
                card_name = get_v(member, "name", t("member"))
                abilities = get_v(member, "abilities", [])
                summary = t("ability")
                if len(abilities) > ab_idx:
                    summary = get_ability_summary(abilities[ab_idx], lang=lang)
                return t("activated_ability", name=card_name, summary=summary, area=area_name)
        return f"{t('ability')} ({area_name})"

    # 2000-2999: Discard Pile Activation
    if 2000 <= a <= 2999:
        adj = a - 2000
        discard_idx = adj // 10
        ab_idx = adj % 10
        card_name = f"Discard[{discard_idx}]"
        if discard_idx < len(p.discard):
            cid = p.discard[discard_idx]
            card_name = get_card_name(cid)
            base_id = get_base_id(cid)
            member = get_from_db(member_db, base_id)
            if member:
                abilities = get_v(member, "abilities", [])
                summary = t("ability")
                if len(abilities) > ab_idx:
                    summary = get_ability_summary(abilities[ab_idx], lang=lang)
                return t("discard_solve", name=card_name, summary=summary)
        return t("discard_fallback", name=card_name)

    # 1000-1999: OnPlay Sub-Choices
    if 1000 <= a <= 1999:
        adj = a - 1000
        choice_idx = adj % 10
        choice_type, params = get_top_pending()

        if choice_type == "ORDER_DECK":
            cards = params.get("cards", [])
            if choice_idx < len(cards):
                return t("sort_top", name=get_card_name(cards[choice_idx]))
            return t("sort_confirm")
        elif choice_type == "COLOR_SELECT":
            colors = t("colors")
            if choice_idx < len(colors):
                return t("color_select_label", color=colors[choice_idx])
        elif choice_type == "SELECT_MODE":
            options = params.get("options", [])
            if choice_idx < len(options):
                return t("mode_select_label", mode=options[choice_idx])
            return t("mode_select_label", mode=f"{choice_idx + 1}")
        elif choice_type == "SELECT_FROM_LIST":
            cards = params.get("cards", [])
            if choice_idx < len(cards):
                return t("list_select", name=get_card_name(cards[choice_idx]))

        return t("choice_fallback", idx=choice_idx + 1)

    # 510-559: Generic Hand Selection Fallback
    if 510 <= a <= 559:
        idx = a - 500
        card_name = f"Hand[{idx}]"
        if idx < len(p.hand):
            card_name = get_card_name(p.hand[idx])
        return t("hand_select_label", name=card_name, desc=t("select"))

    return f"Action {a}"

    return f"Action {a}"
