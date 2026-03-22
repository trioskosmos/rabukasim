from typing import Any, Dict, Optional

from engine.models.ability import ConditionType
from engine.models.enums import Group, Unit


def check_condition(game: Any, player: Any, cond: Any, context: Optional[Dict[str, Any]] = None) -> bool:
    self = game
    if context is None:
        context = {}
    met = False
    if self.verbose:
        print(f"DEBUG: Checking condition {cond.type} Params: {cond.params} CTX: {context}")
    if cond.type == ConditionType.NONE:
        met = True
    elif cond.type == ConditionType.SCORE_COMPARE:
        if cond.params.get("type") == "score":
            val = sum(self.live_db[cid].score for cid in player.success_lives if cid in self.live_db)
            req = cond.params.get("value", 0)
            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = val >= req
            elif comp == "GT":
                met = val > req
            elif comp == "LE":
                met = val <= req
            elif comp == "LT":
                met = val < req
            else:
                met = val == req
        elif cond.params.get("type") == "cost":
            opp = self.players[1 - player.player_id]
            target_zone = cond.params.get("zone", "STAGE")

            def get_cost_in_zone(p, z):
                if z == "CENTER_STAGE" or z == "OPPONENT_CENTER_STAGE":
                    cid = p.stage[1]
                    return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                elif z == "LEFT_STAGE" or z == "OPPONENT_LEFT_STAGE":
                    cid = p.stage[0]
                    return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                elif z == "RIGHT_STAGE" or z == "OPPONENT_RIGHT_STAGE":
                    cid = p.stage[2]
                    return self.member_db[cid].cost if (cid >= 0 and cid in self.member_db) else 0
                return sum(self.member_db[cid].cost for cid in p.stage if cid >= 0 and cid in self.member_db)

            my_cost = get_cost_in_zone(player, target_zone)
            opp_cost = get_cost_in_zone(
                opp, "OPPONENT_" + target_zone if "OPPONENT_" not in target_zone else target_zone
            )

            # Default to comparing vs opponent if no fixed value
            req = cond.params.get("value", opp_cost)
            val = my_cost

            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = val >= req
            elif comp == "GT":
                met = val > req
            elif comp == "LE":
                met = val <= req
            elif comp == "LT":
                met = val < req
            else:
                met = val == req
    elif cond.type == ConditionType.AREA_CHECK:
        req_area = cond.params.get("value")
        current_area = context.get("area")
        # Infer area from card_id if missing
        if current_area is None and "card_id" in context:
            cid = context["card_id"]
            for i, c in enumerate(player.stage):
                if c == cid:
                    current_area = i
                    break
        met = current_area == req_area
    elif cond.type == ConditionType.TURN_1:
        met = self.turn_number == 1
    elif cond.type == ConditionType.IS_CENTER:
        met = context.get("area") == 1
    elif cond.type == ConditionType.HAS_MEMBER:
        name = cond.params.get("name")
        area = cond.params.get("area")
        found = False
        for i, cid in enumerate(player.stage):
            if cid >= 0 and cid in self.member_db:
                m = self.member_db[cid]
                if name and name in m.name:
                    if area == "CENTER_STAGE" and i != 1:
                        continue
                    if area == "LEFT_STAGE" and i != 0:
                        continue
                    if area == "RIGHT_STAGE" and i != 2:
                        continue
                    found = True
                    break
        met = found
    elif cond.type == ConditionType.COUNT_STAGE:
        met = sum(1 for cid in player.stage if cid >= 0) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.LIFE_LEAD:
        met = len(player.success_lives) > len(self.players[1 - player.player_id].success_lives)
    elif cond.type == ConditionType.COUNT_GROUP:
        group_str = cond.params.get("group", "").strip("「」、 　")
        zone = cond.params.get("zone", "STAGE")
        min_count = cond.params.get("count", cond.params.get("min", 0))
        if not group_str:
            return False
        target_group = Group.from_japanese_name(group_str)
        target_unit = Unit.from_japanese_name(group_str)
        count = 0
        cards = []
        if cond.params.get("context") == "revealed":
            cards = self.looked_cards
        elif "OPPONENT_" in zone:
            opp = self.players[1 - player.player_id]
            oz = zone.replace("OPPONENT_", "")
            if oz == "STAGE":
                cards = [c for c in opp.stage if c >= 0]
            elif oz == "DISCARD":
                cards = opp.discard
            elif oz == "HAND":
                cards = opp.hand
            elif oz == "DECK":
                cards = opp.main_deck
            elif oz == "LIVE_ZONE":
                cards = opp.live_zone
            elif oz == "CENTER_STAGE":
                cards = [opp.stage[1]] if opp.stage[1] >= 0 else []
            elif oz == "LEFT_STAGE":
                cards = [opp.stage[0]] if opp.stage[0] >= 0 else []
            elif oz == "RIGHT_STAGE":
                cards = [opp.stage[2]] if opp.stage[2] >= 0 else []
        elif zone == "STAGE":
            cards = [c for c in player.stage if c >= 0]
        elif zone == "DISCARD":
            cards = player.discard
        elif zone == "HAND":
            cards = player.hand
        elif zone == "DECK":
            cards = player.main_deck
        elif zone == "LIVE_ZONE":
            cards = player.live_zone
        elif zone == "CENTER_STAGE":
            cards = [player.stage[1]] if player.stage[1] >= 0 else []
        elif zone == "LEFT_STAGE":
            cards = [player.stage[0]] if player.stage[0] >= 0 else []
        elif zone == "RIGHT_STAGE":
            cards = [player.stage[2]] if player.stage[2] >= 0 else []
        for cid in cards:
            try:
                cid_int = int(cid)
            except ValueError:
                continue
            card = self.member_db.get(cid_int) or self.live_db.get(cid_int)
            if card:
                groups = getattr(card, "groups", [])
                units = getattr(card, "units", [])
                is_match = target_group in groups or target_unit in units
                if is_match:
                    count += 1
        met = count >= min_count
    elif cond.type == ConditionType.HAS_COLOR:
        active_hearts = player.get_total_hearts(self.member_db)
        color_map = {"ピンク": 0, "赤": 1, "黄": 2, "緑": 3, "青": 4, "紫": 5}
        idx = color_map.get(str(cond.params.get("color", "")))
        met = active_hearts[idx] > 0 if idx is not None else False
    elif cond.type == ConditionType.OPPONENT_HAND_DIFF:
        diff_val = len(self.players[1 - player.player_id].hand) - len(player.hand)
        req_diff = cond.params.get("diff", 0)
        comp = cond.params.get("comparison", "GT")
        if comp == "GT":
            met = diff_val >= req_diff
        elif comp == "LT":
            met = (
                diff_val <= req_diff
            )  # Or strictly less? Usually "Less than X" means < X or <= X depending on wording. Usually existing logic uses inclusive.
        else:
            met = diff_val == req_diff
    elif cond.type == ConditionType.HAND_INCREASED:
        # Check how many cards added to hand this turn
        # hand_added_turn tracks timestamps (turn numbers) of additions
        count = sum(1 for t in player.hand_added_turn if t == self.turn_number)
        met = count >= cond.params.get("min", 1)
    elif cond.type == ConditionType.COUNT_ENERGY:
        target_raw = str(cond.params.get("target", "self")).lower()
        target_player = self.players[1 - player.player_id] if target_raw in {"opponent", "opp", "1"} else player
        met = len(target_player.energy_zone) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.HAS_LIVE_CARD:
        # Check if looked_cards (milled/revealed) contains a live card
        if self.looked_cards:
            met = any(cid in self.live_db for cid in self.looked_cards)
        else:
            met = len(player.live_zone) > 0

    elif cond.type == ConditionType.COUNT_HAND:
        target_raw = str(cond.params.get("target", "self")).lower()
        target_player = self.players[1 - player.player_id] if target_raw in {"opponent", "opp", "1"} else player
        met = len(target_player.hand) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.COUNT_DISCARD:
        target_raw = str(cond.params.get("target", "self")).lower()
        target_player = self.players[1 - player.player_id] if target_raw in {"opponent", "opp", "1"} else player
        met = len(target_player.discard) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.SELF_IS_GROUP:
        cid = context.get("card_id")
        req_group = Group.from_japanese_name(cond.params.get("group", ""))
        card = self.member_db.get(cid) or self.live_db.get(cid)
        met = req_group in getattr(card, "groups", []) if card else False
    elif cond.type == ConditionType.MODAL_ANSWER:
        met = context.get("answer") == cond.params.get("answer")
    elif cond.type == ConditionType.HAND_HAS_NO_LIVE:
        met = not any(cid in self.live_db for cid in player.hand)
    elif cond.type == ConditionType.COUNT_SUCCESS_LIVE:
        target_raw = str(cond.params.get("target", "self")).lower()
        target_player = self.players[1 - player.player_id] if target_raw in {"opponent", "opp", "1"} else player
        met = len(target_player.success_lives) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.GROUP_FILTER:
        group_str = cond.params.get("group", "")
        if not group_str:
            met = False
        else:
            target_group = Group.from_japanese_name(group_str)
            target_unit = Unit.from_japanese_name(group_str)
            cards = []
            if cond.params.get("context") == "revealed":
                cards = self.looked_cards
            elif cond.params.get("context") == "live_zone":
                cards = player.live_zone
            elif "zone" in cond.params:
                z = cond.params["zone"]
                if "OPPONENT_" in z:
                    opp = self.players[1 - player.player_id]
                    oz = z.replace("OPPONENT_", "")
                    if oz == "STAGE":
                        cards = [c for c in opp.stage if c >= 0]
                    elif oz == "DISCARD":
                        cards = opp.discard
                    elif oz == "HAND":
                        cards = opp.hand
                    elif oz == "DECK":
                        cards = opp.main_deck
                    elif oz == "LIVE_ZONE":
                        cards = opp.live_zone
                    elif oz == "CENTER_STAGE":
                        cards = [opp.stage[1]] if opp.stage[1] >= 0 else []
                    elif oz == "LEFT_STAGE":
                        cards = [opp.stage[0]] if opp.stage[0] >= 0 else []
                    elif oz == "RIGHT_STAGE":
                        cards = [opp.stage[2]] if opp.stage[2] >= 0 else []
                elif z == "STAGE":
                    cards = [c for c in player.stage if c >= 0]
                elif z == "DISCARD":
                    cards = player.discard
                elif z == "HAND":
                    cards = player.hand
                elif z == "DECK":
                    cards = player.main_deck
                elif z == "LIVE_ZONE":
                    cards = player.live_zone
                elif z == "CENTER_STAGE":
                    cards = [player.stage[1]] if player.stage[1] >= 0 else []
                elif z == "LEFT_STAGE":
                    cards = [player.stage[0]] if player.stage[0] >= 0 else []
                elif z == "RIGHT_STAGE":
                    cards = [player.stage[2]] if player.stage[2] >= 0 else []
            elif context.get("card_id") is not None:
                cards = [context["card_id"]]
            else:
                cards = [c for c in player.stage if c >= 0]

            # Filter out self if requested
            if cond.params.get("exclude_self") and context.get("card_id") is not None:
                cards = [c for c in cards if c != context["card_id"]]

            match_count = 0
            for cid in cards:
                card = self.member_db.get(cid) or self.live_db.get(cid)
                if card and (
                    target_group in getattr(card, "groups", []) or target_unit in getattr(card, "units", [])
                ):
                    match_count += 1
            met = match_count >= cond.params.get("min", cond.params.get("count", 1))

    elif cond.type == ConditionType.COST_CHECK:
        # If we have a target card in context, check its cost
        target_cid = context.get("target_card_id")
        if target_cid is not None:
            val = (self.member_db.get(target_cid) or self.live_db.get(target_cid)).cost
            req = cond.params.get("value", 0)
            comp = cond.params.get("comparison", "GE")
            if comp == "GE":
                met = val >= req
            elif comp == "GT":
                met = val > req
            elif comp == "LE":
                met = val <= req
            elif comp == "LT":
                met = val < req
            else:
                met = val == req
        else:
            # Fallback: check source card or stage
            target_ids = []
            if context.get("card_id") is not None:
                target_ids = [context["card_id"]]
            else:
                target_ids = [c for c in player.stage if c >= 0]

            req = cond.params.get("value", 0)
            comp = cond.params.get("comparison", "LE")
            for cid in target_ids:
                card = self.member_db.get(cid) or self.live_db.get(cid)
                if not card:
                    continue
                val = card.cost
                is_match = val <= req if comp == "LE" else val >= req
                if is_match:
                    met = True
                    break

    elif cond.type == ConditionType.OPPONENT_CHOICE or cond.type == ConditionType.HAS_CHOICE:
        met = True

    elif cond.type == ConditionType.OPPONENT_HAS:
        opp = self.players[1 - player.player_id]
        req_name = cond.params.get("name")
        if req_name:
            met = any(
                req_name in (self.member_db[cid].name if cid in self.member_db else "")
                for cid in opp.stage
                if cid >= 0
            )
        else:
            met = any(cid >= 0 for cid in opp.stage)
    elif cond.type == ConditionType.DECK_REFRESHED:
        met = player.deck_refreshed_this_turn
    elif cond.type == ConditionType.HAS_KEYWORD:
        cid = context.get("card_id")
        keyword = cond.params.get("keyword")
        card = self.member_db.get(cid) or self.live_db.get(cid)
        if not card:
            met = False
        elif keyword == "Blade Heart":
            # Special handling for Blade Heart icon check
            met = getattr(card, "total_blade_hearts", lambda: 0)() > 0
        else:
            met = keyword in getattr(card, "keywords", [])
    elif cond.type == ConditionType.HAS_MOVED:
        tid = context.get("card_id", player.stage[context.get("area", -1)] if context.get("area", -1) >= 0 else -1)
        met = tid in player.moved_members_this_turn if tid >= 0 else False
    elif cond.type == ConditionType.OPPONENT_ENERGY_DIFF:
        diff_val = len(self.players[1 - player.player_id].energy_zone) - len(player.energy_zone)
        req_diff = cond.params.get("diff", 0)
        comp = cond.params.get("comparison", "GE")
        if comp == "GE":
            met = diff_val >= req_diff
        elif comp == "GT":
            met = diff_val > req_diff
        elif comp == "LE":
            met = diff_val <= req_diff
        elif comp == "LT":
            met = diff_val < req_diff
        else:
            met = diff_val == req_diff
    elif cond.type == ConditionType.RARITY_CHECK:
        cid = context.get("card_id")
        card = self.member_db.get(cid) or self.live_db.get(cid)
        # Rarity is likely stored in 'rare' or 'rarity' attribute, possibly extra field
        rarity = getattr(card, "rare", getattr(card, "rarity", ""))
        met = rarity == cond.params.get("rare")
    elif cond.type == ConditionType.COUNT_LIVE_ZONE:
        met = len(player.live_zone) >= cond.params.get("min", 0)
    elif cond.type == ConditionType.COUNT_BLADES:
        req = cond.params.get("min", cond.params.get("count", 1))
        val = player.get_total_blades(self.member_db)
        comp = cond.params.get("comparison", "GE")
        if comp == "GE":
            met = val >= req
        elif comp == "GT":
            met = val > req
        elif comp == "LE":
            met = val <= req
        elif comp == "LT":
            met = val < req
        else:
            met = val == req
    elif cond.type == ConditionType.COUNT_HEARTS:
        req = cond.params.get("min", cond.params.get("count", 1))
        # Determine color index
        c_idx = -1
        c_name = cond.params.get("color")
        color_map = {"pink": 0, "red": 1, "yellow": 2, "green": 3, "blue": 4, "purple": 5}
        jp_map = {"ピンク": 0, "赤": 1, "黄": 2, "緑": 3, "青": 4, "紫": 5}

        if c_name is not None:
            if isinstance(c_name, int):
                c_idx = c_name
            elif c_name in color_map:
                c_idx = color_map[c_name]
            elif c_name in jp_map:
                c_idx = jp_map[c_name]

        # Fallback: Infer from source card
        if c_idx == -1:
            scid = context.get("source_card_id", -1)
            if scid != -1:
                scard = self.member_db.get(int(scid)) or self.live_db.get(int(scid))
                if scard and hasattr(scard, "hearts"):
                    # Find first non-zero heart
                    for i, h in enumerate(scard.hearts):
                        if i < 6 and h > 0:
                            c_idx = i
                            break

        val = 0
        target_cid = context.get("target_card_id")
        if target_cid is not None:
            print(f"DEBUG: Checking Heart Filter. Target={target_cid} ColorIdx={c_idx} Req={req}")
            # Filter Mode: Check Candidate Card
            card = self.member_db.get(int(target_cid)) or self.live_db.get(int(target_cid))
            if card:
                # Check hearts (Member) or required_hearts (Live)
                check_hearts = getattr(card, "hearts", getattr(card, "required_hearts", None))
                if check_hearts is not None:
                    if c_idx != -1 and c_idx < len(check_hearts):
                        val = check_hearts[c_idx]
                    elif c_idx == -1:
                        val = sum(check_hearts[:6])
        else:
            # Activation Mode: Check Player Stage
            active_hearts = player.get_total_hearts(self.member_db)
            if c_idx != -1:
                val = active_hearts[c_idx]
            else:
                val = sum(active_hearts)

        comp = cond.params.get("comparison", "GE")
        if comp == "GE":
            met = val >= req
        elif comp == "GT":
            met = val > req
        elif comp == "LE":
            met = val <= req
        elif comp == "LT":
            met = val < req
        else:
            met = val == req

    elif cond.type == ConditionType.HAS_CHOICE:
        met = True
    elif cond.type == ConditionType.OPPONENT_CHOICE:
        # Check if this card specifically was tapped/chosen by opponent this turn
        cid = context.get("card_id")
        if cid is not None:
            met = cid in player.members_tapped_by_opponent_this_turn
        else:
            met = False
    elif cond.type == ConditionType.TYPE_CHECK:
        # Check if a card is of a specific type (member/live)
        card_type = cond.params.get("card_type", "member")
        zone = cond.params.get("zone", "")

        # Determine which cards to check based on zone
        cards_to_check = []
        if zone == "DISCARDED_THIS":
            cards_to_check = context.get("discarded_cards", [])
        elif zone == "REVEALED_THIS":
            cards_to_check = self.looked_cards
        elif context.get("target_card_id") is not None:
            cards_to_check = [context["target_card_id"]]
        elif context.get("card_id") is not None:
            cards_to_check = [context["card_id"]]

        if card_type == "member":
            met = any(cid in self.member_db for cid in cards_to_check)
        elif card_type == "live":
            met = any(cid in self.live_db for cid in cards_to_check)
        else:
            met = len(cards_to_check) > 0
    elif cond.type == ConditionType.BATON:
        # Baton Pass: Check if current card replaced a specific unit/group member
        prev_cid = context.get("prev_cid", getattr(self, "prev_cid", -1))
        unit_filter = cond.params.get("unit", "")
        cost_filter = cond.params.get("filter", "")

        if prev_cid >= 0 and prev_cid in self.member_db:
            prev_card = self.member_db[prev_cid]

            # Check unit filter
            if unit_filter:
                target_unit = Unit.from_japanese_name(unit_filter)
                unit_match = target_unit in getattr(prev_card, "units", [])
            else:
                unit_match = True

            # Check cost filter (e.g., COST_LT_SELF)
            if cost_filter == "COST_LT_SELF":
                source_cid = context.get("card_id", -1)
                if source_cid >= 0 and source_cid in self.member_db:
                    source_cost = self.member_db[source_cid].cost
                    cost_match = prev_card.cost < source_cost
                else:
                    cost_match = False
            else:
                cost_match = True

            met = unit_match and cost_match
        else:
            met = False
    else:
        met = True

    return met



__all__ = ["check_condition"]
