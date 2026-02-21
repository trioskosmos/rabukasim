import json

from engine.game.desc_utils import get_action_desc
from engine.game.state_utils import get_base_id
from engine.models.ability import EFFECT_DESCRIPTIONS, EffectType, TriggerType


def format_effect_description(effect):
    # Logic copied/adapted from effect_mixin.py
    template = EFFECT_DESCRIPTIONS.get(effect.effect_type, getattr(effect.effect_type, "name", str(effect.effect_type)))
    context = effect.params.copy()
    context["value"] = effect.value

    # Custom overrides if needed (e.g. REDUCE_HEART_REQ)
    if effect.effect_type == EffectType.REDUCE_HEART_REQ:
        if effect.value < 0:
            return f"Reduce Heart Requirement by {abs(effect.value)}"
        else:
            return f"Increase Heart Requirement by {effect.value}"

    try:
        desc = template.format(**context)
    except KeyError:
        desc = template

    # Add contextual suffixes
    if effect.params.get("per_energy"):
        desc += " per Energy"
    if effect.params.get("per_member"):
        desc += " per Member"
    if effect.params.get("per_live"):
        desc += " per Live"

    return desc


def get_card_modifiers(player, slot_idx, card_id, member_db, live_db):
    modifiers = []

    # 0. Player Level Restrictions (Virtual Modifiers)
    if player.cannot_live:
        modifiers.append({"description": "Cannot perform Live this turn", "source": "Game Rule", "expiry": "LIVE_END"})

    # 1. Continuous Effects
    for ce in player.continuous_effects:
        target_slot = ce.get("target_slot", -1)
        eff = ce["effect"]

        # Determine relevance:
        # - member on stage (slot_idx >= 0): matches target_slot or target_slot is -1
        # - live card (slot_idx == -1): matches global effects or live-specific effects
        is_relevant = False
        if slot_idx >= 0:
            if target_slot == -1 or target_slot == slot_idx:
                is_relevant = True
        else:
            # For live cards/others, only show global or relevant types
            if target_slot == -1 or eff.effect_type in (EffectType.REDUCE_HEART_REQ, EffectType.MODIFY_SCORE_RULE):
                is_relevant = True

        if is_relevant:
            desc = format_effect_description(eff)

            # Resolve Source
            source_name = "Effect"
            sid = ce.get("source_card_id")
            if sid is not None:
                base_sid = get_base_id(int(sid))
                if base_sid in member_db:
                    source_name = member_db[base_sid].name
                elif base_sid in live_db:
                    source_name = live_db[base_sid].name

            modifiers.append({"description": desc, "source": source_name, "expiry": ce.get("expiry", "TURN_END")})

    # 2. Intrinsic Constant Abilities
    base_cid = get_base_id(int(card_id))
    db = member_db if base_cid in member_db else live_db if base_cid in live_db else None

    if db and base_cid in db:
        card = db[base_cid]
        if hasattr(card, "abilities"):
            for ab in card.abilities:
                if ab.trigger == TriggerType.CONSTANT:
                    # Check conditions
                    # Note: _check_condition_for_constant might not be available on card/db,
                    # but we assume the environment has it or fallback to True for display
                    # Serializer is often called without full GameState context for individual cards
                    # but here we have 'player'.
                    try:
                        if all(player._check_condition_for_constant(cond, slot_idx) for cond in ab.conditions):
                            for eff in ab.effects:
                                desc = format_effect_description(eff)
                                modifiers.append({"description": desc, "source": "Self", "expiry": "CONSTANT"})
                    except (AttributeError, TypeError):
                        # Fallback: display constant if it exists but condition check is impossible
                        for eff in ab.effects:
                            desc = format_effect_description(eff)
                            modifiers.append({"description": desc, "source": "Self", "expiry": "CONSTANT"})

    return modifiers


def serialize_card(cid, member_db, live_db, energy_db, is_viewable=True, peek=False, lang="jp"):
    if not is_viewable and not peek:
        return {"id": int(cid), "name": "???", "type": "unknown", "img": "cards/back.png", "hidden": True}

    card_data = {}

    # Try direct lookup, then fallback to base ID for unique IDs
    base_cid = get_base_id(int(cid))

    if base_cid in member_db:
        m = member_db[base_cid]
        ability_text = getattr(m, "ability_text", "")

        # Only reconstruct if no rich text is available
        if not ability_text and hasattr(m, "abilities") and m.abilities:
            ability_lines = []
            for ab in m.abilities:
                trigger_icon = {
                    TriggerType.ACTIVATED: "【起動】",
                    TriggerType.ON_PLAY: "【登場】",
                    TriggerType.CONSTANT: "【常時】",
                    TriggerType.ON_LIVE_START: "【ライブ開始】",
                    TriggerType.ON_LIVE_SUCCESS: "【ライブ成功時】",
                }.get(ab.trigger, "【自動】")
                ability_lines.append(f"{trigger_icon} {ab.raw_text}")
            ability_text = "\n".join(ability_lines)

        card_data = {
            "id": int(cid),  # Keep original ID (UID) for frontend tracking
            "card_no": m.card_no,
            "name": m.name,
            "type": "member",
            "cost": m.cost,
            "blade": m.blades,
            "img": m.img_path,
            "hearts": m.hearts.tolist() if hasattr(m.hearts, "tolist") else list(m.hearts),
            "blade_hearts": m.blade_hearts.tolist() if hasattr(m.blade_hearts, "tolist") else list(m.blade_hearts),
            "text": ability_text,
            "original_text": getattr(m, "original_text", ""),
        }
    elif base_cid in live_db:
        l = live_db[base_cid]
        ability_text = getattr(l, "ability_text", "")

        # Only reconstruct if no rich text is available
        if not ability_text and hasattr(l, "abilities") and l.abilities:
            ability_lines = []
            for ab in l.abilities:
                trigger_icon = {TriggerType.ON_LIVE_START: "【ライブ開始】"}.get(ab.trigger, "【自動】")
                ability_lines.append(f"{trigger_icon} {ab.raw_text}")
            ability_text = "\n".join(ability_lines)

        card_data = {
            "id": int(cid),
            "card_no": l.card_no,
            "name": l.name,
            "type": "live",
            "score": l.score,
            "img": l.img_path,
            "required_hearts": l.required_hearts.tolist()
            if hasattr(l.required_hearts, "tolist")
            else list(l.required_hearts),
            "text": ability_text,
            "original_text": getattr(l, "original_text", ""),
        }
    elif base_cid in energy_db:
        e = energy_db[base_cid]
        card_data = {
            "id": int(cid),
            "card_no": getattr(e, "card_no", "ENERGY"),
            "name": getattr(e, "name", "Energy"),
            "type": "energy",
            "img": getattr(e, "img_path", "assets/energy_card.png"),
        }
    else:
        return {"id": int(cid), "name": f"Card {cid}", "type": "unknown", "img": None}

    if not is_viewable and peek:
        card_data["hidden"] = True
        card_data["face_down"] = True

    return card_data


def serialize_player(p, game_state, player_idx, viewer_idx=0, is_viewable=True, lang="jp"):
    member_db = game_state.member_db
    live_db = game_state.live_db
    energy_db = getattr(game_state, "energy_db", {})
    legal_mask = game_state.get_legal_actions()

    expected_yells = 0
    for i, card_id in enumerate(p.stage):
        if card_id >= 0 and not p.tapped_members[i]:
            base_cid = get_base_id(int(card_id))
            if base_cid in member_db:
                expected_yells += member_db[base_cid].blades

    hand = []
    for i, cid in enumerate(p.hand):
        if is_viewable:
            c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
            is_new = False
            if hasattr(p, "hand_added_turn") and i < len(p.hand_added_turn):
                is_new = p.hand_added_turn[i] == game_state.turn_number
            c["is_new"] = is_new

            valid_actions = []
            for area in range(3):
                aid = 1 + i * 3 + area
                if aid < len(legal_mask) and legal_mask[aid]:
                    valid_actions.append(aid)
            for aid in [400 + i, 300 + i, 500 + i]:
                if aid < len(legal_mask) and legal_mask[aid]:
                    valid_actions.append(aid)
            c["valid_actions"] = valid_actions
            hand.append(c)
        else:
            hand.append(serialize_card(cid, member_db, live_db, energy_db, is_viewable=False, lang=lang))

    stage = []
    for i, _ in enumerate(range(3)):
        # Correctly access stage by index
        cid = int(p.stage[i])
        if cid >= 0:
            c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
            c["tapped"] = bool(p.tapped_members[i])
            c["energy"] = int(p.stage_energy_count[i])
            c["locked"] = bool(p.members_played_this_turn[i])

            # Add modifiers
            c["modifiers"] = get_card_modifiers(p, i, cid, member_db, live_db)

            stage.append(c)
        else:
            stage.append(None)

    discard = [serialize_card(cid, member_db, live_db, energy_db, is_viewable=True, lang=lang) for cid in p.discard]

    energy = []
    for i, cid in enumerate(p.energy_zone):
        energy.append(
            {
                "id": i,
                "tapped": bool(p.tapped_energy[i]),
                "card": serialize_card(cid, member_db, live_db, energy_db, is_viewable=False, lang=lang),
            }
        )

    # Calculate total hearts and blades for the player
    total_blades = p.get_total_blades(member_db)
    total_hearts = p.get_total_hearts(member_db)  # Returns np.array(7)

    # Track remaining hearts for live fulfillment calculation (Greedy allocation)
    temp_hearts = total_hearts.copy()

    live_zone = []
    for i, cid in enumerate(p.live_zone):
        is_revealed = bool(p.live_zone_revealed[i]) if i < len(p.live_zone_revealed) else False
        card_obj = serialize_card(
            cid, member_db, live_db, energy_db, is_viewable=is_revealed, peek=(player_idx == viewer_idx), lang=lang
        )

        # Calculate heart progress for this live card
        if cid in live_db:
            l = live_db[cid]
            req = l.required_hearts  # np.array
            filled = [0] * 7

            if is_revealed or (player_idx == viewer_idx):
                # Greedy fill logic matching PlayerState.get_performance_guide
                # Colors 0-5
                for c_idx in range(6):
                    have = temp_hearts[c_idx]
                    need = req[c_idx]
                    take = min(have, need)
                    filled[c_idx] = int(take)
                    temp_hearts[c_idx] -= take

                # Any Color (Index 6)
                req_any = req[6] if len(req) > 6 else 0
                remaining_total = sum(temp_hearts[:6]) + temp_hearts[6]
                take_any = min(remaining_total, req_any)
                filled[6] = int(take_any)
                # Note: We don't subtract from temp_hearts for 'any' because strict color matching is done,
                # and 'any' sucks from the pool of remaining.
                # But to be strictly correct for *subsequent* cards (if we supported multiple approvals at once),
                # we should decrement. But the game usually checks one at a time or order matters.
                # Use the logic from get_performance_guide:
                # It doesn't actually decrement 'any' from specific colors in temp_hearts
                # because 'any' is a wildcard check on the *sum*.
                # Wait, get_performance_guide does:
                # remaining_total = np.sum(temp_hearts[:6]) + temp_hearts[6]

                card_obj["required_hearts"] = req.tolist()
                card_obj["filled_hearts"] = filled

                # Determine passed status
                is_passed = True
                for c_idx in range(6):
                    if filled[c_idx] < req[c_idx]:
                        is_passed = False
                if filled[6] < req[6]:
                    is_passed = False

                card_obj["is_cleared"] = is_passed

            # Add modifiers for live card (e.g. requirement reduction)
            card_obj["modifiers"] = get_card_modifiers(p, -1, cid, member_db, live_db)

        live_zone.append(card_obj)

    score = sum(live_db[cid].score for cid in p.success_lives if cid in live_db)

    return {
        "player_id": p.player_id,
        "score": score,
        "is_active": (game_state.current_player == player_idx),
        "hand": hand,
        "hand_count": len(p.hand),
        "mulligan_selection": list(p.mulligan_selection) if is_viewable else [],
        "deck_count": len(p.main_deck),
        "energy_deck_count": len(p.energy_deck),
        "discard": discard,
        "discard_count": len(p.discard),
        "energy": energy,
        "energy_count": len(p.energy_zone),
        "energy_untapped": int(p.count_untapped_energy()),
        "live_zone": live_zone,
        "live_zone_count": len(p.live_zone),
        "stage": stage,
        "success_lives": [
            serialize_card(cid, member_db, live_db, energy_db, is_viewable, lang=lang) for cid in p.success_lives
        ],
        "restrictions": list(p.restrictions),
        "expected_yells": expected_yells,
        "total_hearts": total_hearts.tolist(),
        "total_blades": int(total_blades),
        "hand_costs": [p.get_member_cost(cid, member_db) if cid in member_db else 0 for cid in p.hand],
        "active_effects": [
            {
                "description": format_effect_description(ce["effect"]),
                "source": (
                    member_db[get_base_id(int(ce["source_card_id"]))].name
                    if ce.get("source_card_id") is not None and get_base_id(int(ce["source_card_id"])) in member_db
                    else live_db[get_base_id(int(ce["source_card_id"]))].name
                    if ce.get("source_card_id") is not None and get_base_id(int(ce["source_card_id"])) in live_db
                    else "Effect"
                ),
                "expiry": ce.get("expiry", "TURN_END"),
                "source_card_id": int(ce.get("source_card_id", -1)) if ce.get("source_card_id") is not None else -1,
            }
            for ce in p.continuous_effects
        ],
    }


def serialize_state(gs, viewer_idx=0, is_pvp=False, mode="pve", lang="jp"):
    active_idx = gs.current_player
    legal_mask = gs.get_legal_actions()
    legal_actions = []
    p = gs.active_player
    member_db = gs.member_db
    live_db = gs.live_db
    energy_db = getattr(gs, "energy_db", {})

    # Only populate legal actions if it is the viewer's turn, or if in PvP/Hotseat mode (show all)
    show_actions = is_pvp or (viewer_idx == active_idx)

    if show_actions:
        for i, v in enumerate(legal_mask):
            if v:
                desc = get_action_desc(i, gs, lang=lang)
                meta = {"id": i, "desc": desc, "name": desc, "description": desc}

                # Enrich with metadata for UI
                if 1 <= i <= 180:
                    meta["type"] = "PLAY"
                    meta["hand_idx"] = (i - 1) // 3
                    meta["area_idx"] = (i - 1) % 3
                    if meta["hand_idx"] < len(p.hand):
                        cid = p.hand[meta["hand_idx"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        hand_cost = p.get_member_cost(cid, member_db)
                        # Baton Touch Reduction (Rule 12)
                        net_cost = hand_cost
                        if p.stage[meta["area_idx"]] >= 0:
                            old_cid = get_base_id(int(p.stage[meta["area_idx"]]))
                            if old_cid in member_db:
                                net_cost = max(0, hand_cost - member_db[old_cid].cost)

                        meta.update(
                            {
                                "img": c["img"],
                                "name": c["name"],
                                "cost": int(net_cost),
                                "base_cost": int(hand_cost),
                                "card_no": c.get("card_no", "???"),
                                "text": c.get("text", ""),
                            }
                        )
                        if cid in member_db:
                            meta["triggers"] = [ab.trigger for ab in member_db[cid].abilities]
                elif 200 <= i <= 202:
                    meta["type"] = "ABILITY"
                    meta["area_idx"] = i - 200
                    cid = p.stage[meta["area_idx"]]
                    if cid >= 0:
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "source_card_id": int(cid)}
                        )
                elif 300 <= i <= 359:
                    meta["type"] = "MULLIGAN"
                    meta["hand_idx"] = i - 300
                elif 400 <= i <= 459:
                    meta["type"] = "LIVE_SET"
                    meta["hand_idx"] = i - 400
                elif 500 <= i <= 559:
                    meta["type"] = "SELECT_HAND"
                    meta["hand_idx"] = i - 500
                    target_p_idx = active_idx
                    if gs.pending_choices:
                        target_p_idx = gs.pending_choices[0][1].get("player_id", active_idx)
                    meta["player_id"] = target_p_idx
                    target_p = gs.players[target_p_idx]
                    if meta["hand_idx"] < len(target_p.hand):
                        cid = target_p.hand[meta["hand_idx"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "source_card_id": int(cid)}
                        )
                elif 560 <= i <= 562:
                    meta["type"] = "SELECT_STAGE"
                    meta["area_idx"] = i - 560
                    target_p_idx = active_idx
                    if gs.pending_choices:
                        target_p_idx = gs.pending_choices[0][1].get("player_id", active_idx)
                    meta["player_id"] = target_p_idx
                    target_p = gs.players[target_p_idx]
                    cid = target_p.stage[meta["area_idx"]]
                    if cid >= 0:
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "source_card_id": int(cid)}
                        )
                elif 590 <= i <= 599:
                    meta["type"] = "ABILITY_TRIGGER"
                    meta["index"] = i - 590
                elif 600 <= i <= 659:
                    meta["type"] = "SELECT"
                    meta["index"] = i - 600
                    if gs.pending_choices:
                        ctype, cparams = gs.pending_choices[0]
                        if ctype == "TARGET_OPPONENT_MEMBER":
                            opp = gs.inactive_player
                            meta["player_id"] = opp.player_id
                            if meta["index"] < 3:
                                cid = opp.stage[meta["index"]]
                                if cid >= 0:
                                    c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                                    meta.update(
                                        {
                                            "img": c["img"],
                                            "name": c["name"],
                                            "text": c.get("text", ""),
                                            "source_card_id": int(cid),
                                        }
                                    )
                        elif ctype == "SELECT_FROM_LIST" or ctype == "SELECT_SUCCESS_LIVE":
                            cards = cparams.get("cards", [])
                            if meta["index"] < len(cards):
                                cid = cards[meta["index"]]
                                c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                                meta.update(
                                    {
                                        "img": c["img"],
                                        "name": c["name"],
                                        "text": c.get("text", ""),
                                        "source_card_id": int(cid),
                                    }
                                )
                elif 660 <= i <= 719:
                    meta["type"] = "SELECT_DISCARD"
                    meta["index"] = i - 660
                    if gs.pending_choices:
                        ctype, cparams = gs.pending_choices[0]
                        if ctype == "SELECT_FROM_DISCARD":
                            cards = cparams.get("cards", [])
                            if meta["index"] < len(cards):
                                cid = cards[meta["index"]]
                                c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                                meta.update(
                                    {
                                        "img": c["img"],
                                        "name": c["name"],
                                        "text": c.get("text", ""),
                                        "source_card_id": int(cid),
                                    }
                                )

                elif 570 <= i <= 579:
                    meta["type"] = "SELECT_MODE"
                    meta["index"] = i - 570
                    if gs.pending_choices:
                        ctype, cparams = gs.pending_choices[0]
                        if ctype == "MODAL" or ctype == "SELECT_MODE":
                            options = cparams.get("options", [])
                            if meta["index"] < len(options):
                                opt = options[meta["index"]]
                                # Option can be string or list/dict
                                desc = str(opt)
                                if isinstance(opt, (list, tuple)) and len(opt) > 0:
                                    desc = str(opt[0])  # Crude fallback
                                meta["text"] = desc
                                meta["name"] = desc
                elif 580 <= i <= 589:
                    meta["type"] = "COLOR_SELECT"
                    meta["index"] = i - 580
                    colors = ["Pink", "Red", "Yellow", "Green", "Blue", "Purple", "All", "None"]
                    if meta["index"] < len(colors):
                        meta["color"] = colors[meta["index"]]
                        meta["name"] = colors[meta["index"]]
                elif 720 <= i <= 759:
                    meta["type"] = "SELECT_FORMATION"
                    meta["index"] = i - 720
                    if gs.pending_choices:
                        ctype, cparams = gs.pending_choices[0]
                        cards = cparams.get("cards", cparams.get("available_members", []))
                        if meta["index"] < len(cards):
                            cid = cards[meta["index"]]
                            c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                            meta.update(
                                {
                                    "img": c["img"],
                                    "name": c["name"],
                                    "text": c.get("text", ""),
                                    "source_card_id": int(cid),
                                }
                            )
                elif 760 <= i <= 819:
                    meta["type"] = "SELECT_SUCCESS_LIVE"
                    meta["index"] = i - 760
                    # Usually points to p.success_lives
                    target_p_idx = active_idx
                    if gs.pending_choices:
                        ctype, cparams = gs.pending_choices[0]
                        target_p_idx = cparams.get("player_id", active_idx)
                    target_p = gs.players[target_p_idx]

                    # If specific cards list provided in params, use that
                    cards = []
                    if gs.pending_choices:
                        _, cparams = gs.pending_choices[0]
                        cards = cparams.get("cards", [])

                    if not cards:
                        cards = target_p.success_lives

                    if meta["index"] < len(cards):
                        cid = cards[meta["index"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {
                                "img": c["img"],
                                "name": c["name"],
                                "text": c.get("text", ""),
                                "source_card_id": int(cid),
                            }
                        )
                elif 820 <= i <= 829:
                    meta["type"] = "TARGET_LIVE"
                    meta["index"] = i - 820
                    target_p_idx = active_idx
                    if gs.pending_choices:
                        _, cparams = gs.pending_choices[0]
                        target_p_idx = cparams.get("player_id", active_idx)
                    target_p = gs.players[target_p_idx]
                    if meta["index"] < len(target_p.live_zone):
                        cid = target_p.live_zone[meta["index"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {
                                "img": c["img"],
                                "name": c["name"],
                                "text": c.get("text", ""),
                                "source_card_id": int(cid),
                            }
                        )
                elif 830 <= i <= 849:
                    meta["type"] = "TARGET_ENERGY"
                    meta["index"] = i - 830
                    target_p_idx = active_idx
                    if gs.pending_choices:
                        _, cparams = gs.pending_choices[0]
                        target_p_idx = cparams.get("player_id", active_idx)
                    target_p = gs.players[target_p_idx]
                    if meta["index"] < len(target_p.energy_zone):
                        cid = target_p.energy_zone[meta["index"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {
                                "img": c["img"],
                                "name": c["name"],
                                "text": c.get("text", ""),
                                "source_card_id": int(cid),
                            }
                        )
                elif 850 <= i <= 909:
                    meta["type"] = "TARGET_REMOVED"
                    meta["index"] = i - 850
                    # Assuming removed_cards is on GameState
                    removed = getattr(gs, "removed_cards", [])
                    if meta["index"] < len(removed):
                        cid = removed[meta["index"]]
                        c = serialize_card(cid, member_db, live_db, energy_db, lang=lang)
                        meta.update(
                            {
                                "img": c["img"],
                                "name": c["name"],
                                "text": c.get("text", ""),
                                "source_card_id": int(cid),
                            }
                        )

                legal_actions.append(meta)

    pending_choice = None
    if gs.pending_choices:
        choice_type, params_raw = gs.pending_choices[0]
        try:
            params = json.loads(params_raw) if isinstance(params_raw, str) else params_raw
        except:
            params = {}

        # Resolve Source Card Details
        source_name = params.get("source_member", "Unknown")
        source_img = None
        source_id = params.get("source_card_id")

        if source_id is not None:
            if source_id in member_db:
                m = member_db[source_id]
                source_name = m.name
                source_img = m.img_path
            elif source_id in live_db:
                l = live_db[source_id]
                source_name = l.name
                source_img = l.img_path

        pending_choice = {
            "type": choice_type,
            "description": params.get("effect_description", ""),
            "source_ability": params.get("source_ability", ""),
            "source_member": source_name,
            "source_img": source_img,
            "source_card_id": int(source_id) if source_id is not None else -1,
            "is_optional": params.get("is_optional", False),
            "params": params,
        }

    # FINAL CHECK: Correctly indented return statement
    return {
        "turn": gs.turn_number,
        "phase": int(gs.phase),
        "active_player": int(active_idx),
        "game_over": gs.game_over,
        "winner": gs.winner,
        "mode": mode,
        "is_pvp": is_pvp,
        "players": [
            serialize_player(
                gs.players[0],
                gs,
                player_idx=0,
                viewer_idx=viewer_idx,
                is_viewable=(viewer_idx == 0 or is_pvp),
                lang=lang,
            ),
            serialize_player(
                gs.players[1],
                gs,
                player_idx=1,
                viewer_idx=viewer_idx,
                is_viewable=(viewer_idx == 1 or is_pvp),
                lang=lang,
            ),
        ],
        "legal_actions": legal_actions,
        "pending_choice": pending_choice,
        "rule_log": gs.rule_log[-200:],  # Truncate log for transport
        "performance_results": getattr(gs, "performance_results", {}),
        "last_performance_results": getattr(gs, "last_performance_results", {}),
        "performance_history": getattr(gs, "performance_history", []),
        "looked_cards": [
            serialize_card(cid, member_db, live_db, energy_db, lang=lang)
            for cid in getattr(gs.get_player(active_idx), "looked_cards", [])
        ],
        "my_player_id": viewer_idx,
        "needs_deck": gs.phase == 3,
    }
