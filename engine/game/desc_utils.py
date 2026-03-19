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
            1: "逋ｻ蝣ｴ譎・,
            2: "繝ｩ繧､繝夜ｲ陦梧凾",
            3: "繝ｩ繧､繝匁・蜉滓凾",
            4: "繧ｿ繝ｼ繝ｳ髢句ｧ区凾",
            5: "繧ｿ繝ｼ繝ｳ邨ゆｺ・凾",
            6: "蟶ｸ譎・,
            7: "襍ｷ蜍・,
        }
        t_desc = t_map.get(trigger, "")
        prefix = f"縲須t_desc}縲・ if t_desc else ""
    else:
        t_map = {1: "Play", 2: "LiveStart", 3: "Success", 4: "TurnStart", 5: "TurnEnd", 6: "Constant", 7: "Act"}
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
        tg_map = {1: "閾ｪ蛻・, 2: "逶ｸ謇・, 3: "蜈ｨ蜩｡", 4: "閾ｪ霄ｫ", 12: "逶ｸ謇九Γ繝ｳ"}
    else:
        tg_map = {1: "Player", 2: "Opponent", 3: "All", 4: "Self", 12: "OppMem"}
    tg_name = tg_map.get(target, "")

    # Effect Detail Mapping
    if lang == "jp":
        e_map = {
            0: "繝峨Ο繝ｼ",
            1: "繝悶Ξ繝ｼ繝・",
            2: "繝上・繝・",
            3: "繧ｳ繧ｹ繝・",
            4: "繝・ャ繧ｭ遒ｺ隱・,
            5: "繝ｩ繧､繝門屓蜿・,
            6: "繧ｹ繧ｳ繧｢+",
            7: "蝗槫庶",
            8: "繝代Ρ繝ｼ+",
            9: "蜉ｹ譫懃┌蜉ｹ",
            10: "遘ｻ蜍・,
            11: "謇区惆莠､謠・,
            12: "繧ｵ繝ｼ繝・,
            13: "繧ｨ繝阪メ繝｣繝ｼ繧ｸ",
            15: "荳ｦ縺ｹ譖ｿ縺・,
            17: "驕ｸ謚・,
            20: "荳九↓鄂ｮ縺・,
            19: "繧ｿ繝・・",
            27: "隕九※驕ｸ縺ｶ",
            30: "謇区惆縺ｫ蜉縺医ｋ",
            31: "繝悶Ξ繝ｼ繝牙崋螳・,
            37: "濶ｲ驕ｸ謚・,
            38: "繧ｹ繧ｳ繧｢險育ｮ怜､画峩",
            41: "謗ｧ縺医↓鄂ｮ縺・,
            44: "繧ｨ繝ｼ繝ｫ貂・,
            46: "謾ｯ謇輔＞",
            48: "繝峨Ο繝ｼ",
            81: "繧ｨ繝榊屓蠕ｩ",
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
        e_name = f"謚桀len(opts)}" if lang == "jp" else f"Choose{len(opts)}"
        val = 0
    elif etype == 27:  # LOOK_AND_CHOOSE
        e_name = f"{val}隕矩∈" if lang == "jp" else f"Pick{val}Deck"
        val = 0
    elif etype == 48:  # DRAW_UNTIL
        e_name = f"謇区惆{val}譫壹∪縺ｧ蠑輔￥" if lang == "jp" else f"DrawTo{val}"
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
        clean_text = text.replace("縲・, "[").replace("縲・, "]").split("\n")[0].strip()
        if len(clean_text) > 30:
            clean_text = clean_text[:27] + "..."
        ability_prefix = f"[{clean_text}] " if lang == "en" else f"縲須clean_text}縲・

    # Localization helper
    def t(key, **kwargs):
        templates = {
            "jp": {
                "pass": "縲千ｵゆｺ・代Γ繧､繝ｳ繝輔ぉ繧､繧ｺ繧堤ｵゆｺ・☆繧・,
                "confirm_mulligan": "縲千｢ｺ螳壹代・繝ｪ繧ｬ繝ｳ繧貞ｮ御ｺ・☆繧・,
                "skip_ability": "縲舌せ繧ｭ繝・・縲捜source}縺ｮ蜉ｹ譫懊ｒ菴ｿ繧上↑縺・,
                "main_end": "縲舌Γ繧､繝ｳ邨ゆｺ・代ち繝ｼ繝ｳ繧剃ｺ､莉｣縺吶ｋ",
                "live_confirm": "縲千｢ｺ隱阪代Λ繧､繝悶ｒ繧ｻ繝・ヨ縺励※騾ｲ繧",
                "next": "縲先ｬ｡縺ｸ縲・,
                "color_select_label": "縲占牡驕ｸ謚槭捜color}",
                "stage_select_label": "縲舌せ繝・・繧ｸ縲捜area}: {name}繧畜desc}",
                "hand_select_label": "縲先焔譛ｭ縲捜name}繧畜desc}",
                "mode_select_label": "縲舌Δ繝ｼ繝峨捜mode}",
                "ability_solve": "縲仙柑譫懆ｧ｣豎ｺ縲捜source} ({idx}/{total})",
                "live_select": "縲舌Λ繧､繝夜∈謚槭捜area}: {name}",
                "performance": "縲舌ヱ繝輔か繝ｼ繝槭Φ繧ｹ縲捜area}: {name} ({summary})",
                "sort_top": "縲蝉ｸｦ縺ｳ譖ｿ縺医捜name}繧偵ヨ繝・・縺ｸ",
                "sort_confirm": "縲千｢ｺ螳壹台ｸｦ縺ｳ譖ｿ縺医ｒ螳御ｺ・,
                "target_opp": "縲舌ち繝ｼ繧ｲ繝・ヨ縲醍嶌謇・{area}: {name}",
                "list_select": "縲宣∈謚槭捜name}",
                "generic_select": "縲宣∈謚槭捜name}",
                "choice_fallback": "縲宣∈謚櫁い縲捜idx}",
                "discard_solve": "縲先而縺・activation縲捜name}: {summary}",
                "discard_fallback": "縲先而縺亥ｮ､縲捜name}",
                "deck_top": "繝・ャ繧ｭ繝医ャ繝・ {name}",
                "color_choice": "{color}",
                "place_on": "縲舌ヰ繝医Φ繧ｿ繝・メ縲捜name} (竊須old_name}) 謾ｯ謇・{cost}",
                "place_on_new": "縲千匳蝣ｴ縲捜name} (繧ｳ繧ｹ繝・{cost})",
                "energy_charge": "縲舌メ繝｣繝ｼ繧ｸ縲捜name}",
                "mulligan_toggle": "縲舌・繝ｪ繧ｬ繝ｳ縲捜name}",
                "live_set": "縲舌Λ繧､繝悶そ繝・ヨ縲捜name}",
                "activated_ability": "縲占ｵｷ蜍輔捜name}: {summary}",
                "none": "縺ｪ縺・,
                "empty_area": "遨ｺ縺・,
                "member": "繝｡繝ｳ繝舌・",
                "ability": "蜉ｹ譫・,
                "unknown": "荳肴・",
                "discard": "遐ｴ譽・,
                "recover": "蝗槫庶",
                "wait": "蠕・ｩ・,
                "move_src": "遘ｻ蜍募・",
                "place_to": "驟咲ｽｮ",
                "select": "驕ｸ謚・,
                "confirm": "遒ｺ螳・,
                "pass_action": "縲舌ヱ繧ｹ縲台ｽ輔ｂ縺励↑縺・,
                "order_deck": "螻ｱ譛ｭ謫堺ｽ・,
                "select_member": "繝｡繝ｳ繝舌・驕ｸ謚・,
                "target_opp_member": "逶ｸ謇九ｒ驕ｸ謚・,
                "select_success": "謌仙粥繝ｩ繧､繝夜∈謚・,
                "select_discard": "謗ｧ縺亥ｮ､蝗槫庶",
                "select_hand": "謇区惆驕ｸ謚・,
                "select_discard_hand": "縲先焔譛ｭ遐ｴ譽・代き繝ｼ繝峨ｒ驕ｸ縺ｶ",
                "colors": ["襍､", "髱・, "邱・, "鮟・, "邏ｫ", "繝斐Φ繧ｯ"],
                "areas": ["蟾ｦ", "荳ｭ", "蜿ｳ"],
                "areas_short": ["蟾ｦ", "荳ｭ", "蜿ｳ"],
                "yes": "縺ｯ縺・,
                "no": "縺・＞縺・,
            },
            "en": {
                "pass": "[End] End Main Phase",
                "confirm_mulligan": "[Confirm] Finish Mulligan",
                "skip_ability": "[Skip] Do not use {source}'s effect",
                "main_end": "[End Turn] Pass to opponent",
                "live_confirm": "[Confirm] Set Live and continue",
                "next": "[Next] Proceed",
                "color_select_label": "[Color] Select {color}",
                "stage_select_label": "[Stage] {area}: {desc} {name}",
                "hand_select_label": "[Hand] {desc} {name}",
                "mode_select_label": "[Mode] {mode}",
                "ability_solve": "[Resolving] {source} ({idx}/{total})",
                "live_select": "[Live] {area}: {name}",
                "performance": "[Performance] {area}: {name} ({summary})",
                "sort_top": "[Sort] Move {name} to Top",
                "sort_confirm": "[Confirm] Finish sorting",
                "target_opp": "[Target] Opponent {area}: {name}",
                "list_select": "[Select] {name}",
                "generic_select": "[Select] {name}",
                "choice_fallback": "[Choice] {idx}",
                "discard_solve": "[From Discard] {name}: {summary}",
                "discard_fallback": "[In Discard] {name}",
                "deck_top": "Top: {name}",
                "color_choice": "{color}",
                "place_on": "[Baton Pass] {name} (over {old_name}) Pay:{cost}",
                "place_on_new": "[Play] {name} (Cost:{cost})",
                "energy_charge": "[Charge] {name}",
                "mulligan_toggle": "[Mulligan] Toggle {name}",
                "live_set": "[Live Set] {name}",
                "activated_ability": "[Act] {name}: {summary}",
                "none": "None",
                "empty_area": "Empty",
                "member": "Member",
                "ability": "Effect",
                "unknown": "Unknown",
                "discard": "Discard",
                "recover": "Recover",
                "wait": "Wait",
                "move_src": "From",
                "place_to": "To",
                "select": "Select",
                "confirm": "Confirm",
                "pass_action": "[Pass] Do nothing",
                "order_deck": "Sort Deck",
                "select_member": "Select Member",
                "target_opp_member": "Target Opponent",
                "select_success": "Select Success Live",
                "select_discard": "Recover from Discard",
                "select_hand": "Select Hand",
                "yes": "Yes",
                "no": "No",
                "select_discard_hand": "[Discard] Choose card",
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
            except (KeyError, IndexError):
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
            name = get_v(l, "name", f"繝ｩ繧､繝・#{base_id}")
            card_no = get_v(l, "card_no", "??")
            return f"{name} ({card_no})"

        e = get_from_db(getattr(_gs, "energy_db", None), base_id)
        if e:
            name = get_v(e, "name", f"繧ｨ繝阪Ν繧ｮ繝ｼ #{base_id}")
            card_no = get_v(e, "card_no", "??")
            return f"{name} ({card_no})"

        return f"繧ｫ繝ｼ繝・#{cid}"

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

    # 1000-1599: Play Member
    if 1000 <= a <= 1599:
        idx = (a - 1000) // 10
        area_idx = (a - 1000) % 10
        areas = t("areas")
        area_name = areas[area_idx] if area_idx < 3 else f"Slot {area_idx}"
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
                    suffix = " [On Play]" if lang == "en" else " [逋ｻ蝣ｴ]"

        if area_idx < len(p.stage):
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

    # 8300-8599: Stage Ability
    if 8300 <= a <= 8599:
        adj = a - 8300
        area_idx = adj // 100
        ab_idx = (adj % 100) // 10
        areas = t("areas")
        area_name = areas[area_idx] if area_idx < 3 else f"Slot {area_idx}"
        cid = p.stage[area_idx] if area_idx < len(p.stage) else -1
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

    # 1600-2199: Hand Ability
    if 1600 <= a <= 2199:
        adj = a - 1600
        hand_idx = adj // 10
        ab_idx = adj % 10
        cid = p.hand[hand_idx] if hand_idx < len(p.hand) else -1
        if cid >= 0:
            card_name = get_card_name(cid)
            base_id = get_base_id(cid)
            member = get_from_db(member_db, base_id)
            if member:
                abilities = get_v(member, "abilities", [])
                summary = t("ability")
                if len(abilities) > ab_idx:
                    summary = get_ability_summary(abilities[ab_idx], lang=lang)
                return t("activated_ability", name=card_name, summary=summary, area="-")
        return t("ability")

    # 9300-9999: Discard Ability
    if 9300 <= a <= 9999:
        adj = a - 9300
        discard_idx = adj // 10
        ab_idx = adj % 10
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
        return t("discard")

    elif 2200 <= a <= 2799:
        h_idx = (a - 2200) // 10
        c_idx = (a - 2200) % 10
        player = gs.get_player(gs.current_player)
        name = t("card")
        if h_idx < len(player.hand):
            cid = player.hand[h_idx]
            bid = cid & 0xFFFFF
            card_data = gs.member_db.get(str(bid)) or gs.live_db.get(str(bid)) or gs.energy_db.get(str(bid))
            if card_data: 
                name = getattr(card_data, 'name', f"Card #{bid}")
        return f"{name} 竊・{t('choice_fallback', idx=c_idx)}" if lang == "en" else f"{name}縺ｮ驕ｸ謚櫁い {c_idx + 1}"
    elif 8600 <= a <= 8899:
        s_idx = (a - 8600) // 100
        c_idx = (a - 8600) % 100
        player = gs.get_player(gs.current_player)
        name = t("member")
        if s_idx < len(player.stage) and player.stage[s_idx] >= 0:
            cid = player.stage[s_idx]
            bid = cid & 0xFFFFF
            card_data = gs.member_db.get(str(bid))
            if card_data: 
                name = getattr(card_data, 'name', f"Member #{bid}")
        return f"{name} 竊・{t('choice_fallback', idx=c_idx)}" if lang == "en" else f"{name}縺ｮ驕ｸ謚櫁い {c_idx + 1}"
    elif 11000 <= a <= 15999:
        idx = a - 11000
        
        # Special case: LOOK_REORDER_DISCARD (opcode 125) - choice_idx 99 is "Done", else resolve to card from looked_cards
        if idx == 99:
            return t("confirm")
        
        # Try to resolve from looked_cards if available
        if hasattr(p, 'looked_cards') and p.looked_cards:
            if idx < len(p.looked_cards):
                cid = p.looked_cards[idx]
                return get_card_name(cid)
        
        # Fallback to text params (for modal choices, etc.)
        ctype, params = get_top_pending()
        choice_text = text or params.get("text") or params.get("choice_text", "")
        if choice_text:
            # Protect icon tags {{...|...}} from being split by replacing their pipes temporarily
            import re
            protected_text = re.sub(r'\{\{([^}]*)\|([^}]*)\}\}', r'{{\1__PIPE__\2}}', choice_text)
            if '|' in protected_text:
                parts = protected_text.split('|')
                if idx < len(parts):
                    return parts[idx].replace('__PIPE__', '|')
            
        # Better defaults for Optional Yes/No
        if ctype == "Optional":
            if idx == 0: return t("yes")
            if idx == 1: return t("no")
            
        return choice_text if choice_text and idx == 0 and '|' not in choice_text else f"Option {idx}"

    # 300-359: Mulligan
    elif 300 <= a <= 359:
        idx = a - 300
        card_name = get_card_name(p.hand[idx]) if idx < len(p.hand) else f"Hand[{idx}]"
        return t("mulligan_toggle", name=card_name)

    # 400-459: Live Set
    elif 400 <= a <= 459:
        idx = a - 400
        card_name = get_card_name(p.hand[idx]) if idx < len(p.hand) else f"Hand[{idx}]"
        return t("live_set", name=card_name)

    # 100-159, 8200-8259: Select Hand (note: 500-599 is MODE, not hand)
    if 100 <= a <= 159 or 8200 <= a <= 8259:
        if 100 <= a <= 159: idx = a - 100
        else: idx = a - 8200
        card_name = get_card_name(p.hand[idx]) if idx < len(p.hand) else f"Hand[{idx}]"
        desc = t("select")
        choice_type, params = get_top_pending()
        if choice_type == "RECOVER_MEMBER": desc = t("recover")
        elif choice_type == "DISCARD": desc = t("discard")
        return t("hand_select_label", name=card_name, desc=desc)

    # 600-602: Select Stage
    if 600 <= a <= 602:
        idx = a - 600
        areas = t("areas")
        cid = p.stage[idx] if idx < len(p.stage) else -1
        name = get_card_name(cid) if cid >= 0 else t("empty_area")
        return t("stage_select_label", area=areas[idx], name=name, desc=t("select"))

    # 900-929: Select Live
    if 900 <= a <= 929:
        idx = a - 900
        areas = t("areas")
        cid = p.live_zone[idx] if idx < len(p.live_zone) else -1
        name = get_card_name(cid) if cid >= 0 else t("none")
        return t("live_select", area=areas[idx], name=name)
    
    # 1600-2199: Hand Ability (activate ability from hand before playing)
    if 1600 <= a <= 2199:
        adj = a - 1600
        hand_idx = adj // 10
        ab_idx = adj % 10
        cid = p.hand[hand_idx] if hand_idx < len(p.hand) else -1
        if cid >= 0:
            card_name = get_card_name(cid)
            base_id = get_base_id(cid)
            member = get_from_db(member_db, base_id)
            if member:
                abilities = get_v(member, "abilities", [])
                summary = t("ability")
                if len(abilities) > ab_idx:
                    summary = get_ability_summary(abilities[ab_idx], lang=lang)
                return t("activated_ability", name=card_name, summary=summary, area="hand")
        return t("ability")

    # 10000+: Energy Select
    if 10000 <= a <= 10999:
        return t("energy_charge", name=f"Energy[{a-10000}]")

    # 500-599: Mode Select (ACTION_BASE_MODE = 500)
    if 500 <= a <= 599:
        choice_type, params = get_top_pending()
        mode_idx = a - 500
        mode_label = f"Mode {mode_idx+1}"
        options = params.get("options", [])
        if mode_idx < len(options): mode_label = options[mode_idx]
        return t("mode_select_label", mode=mode_label)

    # 580-585: Color Select
    if 580 <= a <= 585:
        colors = t("colors")
        return t("color_select_label", color=colors[a-580])

    # 5000-5001: Turn Order
    if 5000 <= a <= 5001:
        return t("choose_turn_order")

    return f"Action {a}"


