import json
import os
import sys

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import engine_rust

from engine.game.desc_utils import get_action_desc
from engine.game.enums import Phase

TRIGGER_ICONS = {
    "jp": {
        1: "【登場】",
        2: "【ライブ開始】",
        3: "【ライブ成功時】",
        6: "【常時】",
        7: "【起動】",
    },
    "en": {
        1: "[Play]",
        2: "[Live Start]",
        3: "[Live Success]",
        6: "[Constant]",
        7: "[Activate]",
    }
}

SERIALIZER_STRINGS = {
    "jp": {
        "ability_root": "アビリティ",
        "card_effect": "カードの効果",
        "make_selection": "選択してください",
        "select_color": "ピースの色を選択してください",
        "select_mode": "モードを選択してください",
        "select_success_live": "獲得するライブカードを1枚選んでください",
        "select_opp_member": "相手のメンバーを選択してください",
        "choose_option": "選択肢を選んでください",
        "select_discard": "控え室から選択してください",
        "select_stage": "メンバーを選択してください",
        "select_hand": "手札から選択してください",
        "order_deck": "デッキの順番を選んでください",
        "choose_turn_order": "じゃんけん勝利！ 先攻・後攻を選んでください",
        "rps_choice": "じゃんけん！ 手を選んでください",
        "color_names": ["赤", "青", "緑", "黄", "紫", "ピンク"],
        "select_discard_hand": "捨てるカードを選択してください",
        "select_hand_play": "プレイするカードを選択してください",
        "pay_energy": "エネルギーを選択してください",
        "rock": "グー",
        "paper": "パー",
        "scissors": "チョキ",
        "unknown": "???",
        "unknown_type": "不明",
        "card_types": {
            "メンバー": "メンバー",
            "ライブ": "ライブ",
            "エネルギー": "エネルギー"
        }
    },
    "en": {
        "ability_root": "Ability",
        "card_effect": "Card Effect",
        "make_selection": "Make a selection",
        "select_color": "Select a Color",
        "select_mode": "Select a Mode",
        "select_success_live": "Select a Live card to acquire",
        "select_opp_member": "Select an Opponent Member",
        "choose_option": "Choose an option",
        "select_discard": "Select from Discard",
        "select_stage": "Select a Member on Stage",
        "select_hand": "Select from Hand",
        "order_deck": "Choose deck order",
        "choose_turn_order": "RPS Win! Choose Turn Order",
        "rps_choice": "Rock Paper Scissors! Choose your sign",
        "color_names": ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"],
        "select_discard_hand": "Select card to discard",
        "select_hand_play": "Select card to play",
        "pay_energy": "Select Energy to Pay",
        "rock": "Rock",
        "paper": "Paper",
        "scissors": "Scissors",
        "unknown": "???",
        "unknown_type": "Unknown",
        "card_types": {
            "メンバー": "Member",
            "ライブ": "Live",
            "エネルギー": "Energy"
        }
    },
}


class RustCompatPlayer:
    def __init__(self, p):
        self._p = p
        self.player_id = p.player_id
        self.hand = p.hand
        self.discard = p.discard
        self.success_lives = p.success_lives
        self.stage = p.stage
        self.live_zone = p.live_zone
        # Convert bitmask to set for compatibility with 'idx in p.mulligan_selection'
        self.mulligan_selection = {i for i in range(len(p.hand)) if (p.mulligan_selection >> i) & 1}

    def __getattr__(self, name):
        return getattr(self._p, name)


class RustCompatGameState:
    def __init__(self, gs, py_member_db, py_live_db, py_energy_db=None):
        self._gs = gs
        self.member_db = py_member_db
        self.live_db = py_live_db
        self.energy_db = py_energy_db
        self.current_player = gs.current_player
        self.phase = gs.phase
        self.turn_number = gs.turn
        self.triggered_abilities = []

    @property
    def pending_choices(self):
        # Convert Rust Vec<(String, String)> to [(type, params_dict), ...]
        raw = self._gs.pending_choices
        result = []
        for t, p in raw:
            try:
                params = json.loads(p)
                result.append((t, params))
            except:
                result.append((t, {}))
        return result

    @property
    def pending_area_idx(self):
        return self._gs.pending_area_idx

    @property
    def pending_ab_idx(self):
        return self._gs.pending_ab_idx

    @property
    def active_player(self):
        return RustCompatPlayer(self._gs.get_player(self._gs.current_player))

    @property
    def inactive_player(self):
        return RustCompatPlayer(self._gs.get_player(1 - self._gs.current_player))

    @property
    def inactive_player_idx(self):
        return 1 - self._gs.current_player

    @property
    def players(self):
        return [RustCompatPlayer(self._gs.get_player(0)), RustCompatPlayer(self._gs.get_player(1))]

    def get_player(self, idx):
        return RustCompatPlayer(self._gs.get_player(idx))

    def get_legal_actions(self):
        return self._gs.get_legal_actions()


def serialize_card_rust(card_id, db: engine_rust.PyCardDatabase, is_viewable=True):
    if card_id < 0:
        return None
    if not is_viewable:
        return {"id": int(card_id), "name": "???", "type": "unknown", "img": "cards/back.png", "hidden": True}

    # In Rust engine, card_id is already the index in DB for basic lookups?
    # Actually PyCardDatabase needs to expose card data.
    # If the Rust PyCardDatabase doesn't expose full card objects yet,
    # we might need to load the JSON DB in Python too just for metadata.

    # For now, let's assume we use the Python member_db/live_db as a dictionary of metadata
    # that matches the IDs in Rust.
    pass


class RustGameStateSerializer:
    def __init__(self, py_member_db, py_live_db, py_energy_db):
        from engine.game.state_utils import MaskedDB

        self.member_db = py_member_db if isinstance(py_member_db, MaskedDB) else MaskedDB(py_member_db)
        self.live_db = py_live_db if isinstance(py_live_db, MaskedDB) else MaskedDB(py_live_db)
        self.energy_db = py_energy_db if isinstance(py_energy_db, MaskedDB) else MaskedDB(py_energy_db)
        self._card_cache = {}  # Cache for base card metadata

    def serialize_card(self, cid, is_viewable=True, peek=False, lang="jp"):
        s = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])
        if cid < 0:
            return None
        if not is_viewable and not peek:
            return {
                "id": int(cid),
                "name": s["unknown"],
                "type": s["unknown_type"],
                "img": "icon_blade.png",
                "hidden": True,
            }

        # Fallback to icon_blade.png for unknown cards if no image path exists
        def fix_img(img):
            if not img:
                return "icon_blade.png"
            if img.startswith("assets/"):
                return img  # energy_card.png
            return img

        cid_int = int(cid)
        base_id = cid_int & 0xFFFFF  # Mask with BASE_ID_MASK (20 bits)

        if base_id in self._card_cache:
            res = self._card_cache[base_id].copy()
            res["id"] = cid_int
            return res

        res = None
        # Using the Python DB for metadata (names, images, text)
        bid_str = str(base_id)
        if bid_str in self.member_db:
            m = self.member_db[bid_str]
            # Fallback for ability text if not populated
            # Prioritize pseudocode (raw_text) for consistent frontend translation
            abilities = getattr(m, "abilities", [])
            at = "\n".join([getattr(ab, "raw_text", "") for ab in abilities if getattr(ab, "raw_text", "")])

            # Fallback to static ability text if no pseudocode available
            if not at:
                at = getattr(m, "ability_text", "")

            res = {
                "card_no": m.card_no,
                "name": m.name,
                "type": "member",
                "cost": m.cost,
                "blade": m.blades,
                "img": m.img_path,
                "hearts": list(m.hearts),
                "blade_hearts": list(m.blade_hearts),
                "text": at,
                "original_text": m.original_text,
                "original_text_en": getattr(m, "original_text_en", ""),
                "ability": m.original_text,
            }
        elif bid_str in self.live_db:
            l = self.live_db[bid_str]

            # Prioritize pseudocode for lives too
            abilities = getattr(l, "abilities", [])
            at = "\n".join([getattr(ab, "raw_text", "") for ab in abilities if getattr(ab, "raw_text", "")])
            if not at:
                at = getattr(l, "ability_text", "")

            res = {
                "card_no": l.card_no,
                "name": l.name,
                "type": "live",
                "score": l.score,
                "img": l.img_path,
                "required_hearts": list(l.required_hearts),
                "text": at,
                "original_text": l.original_text,
                "original_text_en": getattr(l, "original_text_en", ""),
                "ability": l.original_text,
            }
        elif bid_str in self.energy_db:
            e = self.energy_db[bid_str]
            res = {
                "card_no": e.card_no,
                "name": e.name,
                "type": "energy",
                "img": e.img_path,
                "text": e.ability_text,
                "original_text": e.original_text,
                "ability": e.original_text,
            }

        if res:
            self._card_cache[base_id] = res
            res_instance = res.copy()
            res_instance["id"] = cid_int
            return res_instance

        return {"id": cid_int, "name": f"Card {base_id}", "type": "unknown", "img": "icon_blade.png"}

    def serialize_player(
        self, p: engine_rust.PyPlayerState, gs: engine_rust.PyGameState, p_idx, viewer_idx=0, legal_mask=None, lang="jp"
    ):
        is_viewable = p_idx == viewer_idx

        hand = []
        # Use cached legal_mask if provided, otherwise fetch (fallback for direct calls)
        if legal_mask is None:
            legal_mask = gs.get_legal_actions() if gs.current_player == p_idx else []
        elif gs.current_player != p_idx:
            legal_mask = []  # Clear mask for non-active player

        for i, cid in enumerate(p.hand):
            c = self.serialize_card(cid, is_viewable=is_viewable, lang=lang)
            if is_viewable:
                c["is_new"] = (p.hand_added_turn[i] == gs.turn) if i < len(p.hand_added_turn) else False

                valid_actions = []
                if len(legal_mask) > 0:
                    # Mapping logic matching Python serializer
                    # Play Member: 1 + hand_idx * 3 + slot_idx
                    for area in range(3):
                        aid = 1 + i * 3 + area
                        if aid < len(legal_mask) and legal_mask[aid]:
                            valid_actions.append(aid)
                    # Other hand-related actions: Mulligan (300+), LiveSet (400+), SelectHand (500+)
                look_range = [300 + i, 400 + i, 500 + i]
                # If we are in a discard cost phase, the IDs follow the 550 + area*100 + ab*10 + hand_idx pattern
                if gs.pending_choice_type == "SELECT_HAND_DISCARD":
                    area = gs.pending_area_idx if gs.pending_area_idx >= 0 else 0
                    ab = gs.pending_ab_idx if gs.pending_ab_idx >= 0 else 0
                    base = 550 + (area * 100) + (ab * 10)
                    look_range.append(base + i)

                for aid in look_range:
                    if aid < len(legal_mask) and legal_mask[aid]:
                        valid_actions.append(aid)
                c["valid_actions"] = valid_actions
            hand.append(c)

        stage = []
        rust_stage = p.stage
        rust_tapped = p.tapped_members
        for i in range(3):
            cid = rust_stage[i]
            if cid >= 0:
                c = self.serialize_card(cid, is_viewable=True, lang=lang)
                c["tapped"] = bool(rust_tapped[i])
                c["energy"] = int(getattr(p, "stage_energy_count", [0, 0, 0])[i])
                c["locked"] = False  # Rust doesn't track locked members yet

                # Fetch effective stats from Rust
                eff_blade = gs.get_effective_blades(p_idx, i)
                eff_hearts = gs.get_effective_hearts(p_idx, i)

                # Update stats in card dict
                c["blade"] = int(eff_blade)
                c["hearts"] = [int(h) for h in eff_hearts]

                # Calculate modifiers for UI highlighting (Attack +1, etc.)
                modifiers = []
                base_m = self.member_db.get(int(cid))
                if base_m:
                    if c["blade"] > base_m.blades:
                        modifiers.append(
                            {
                                "type": "blade",
                                "value": c["blade"] - base_m.blades,
                                "label": f"Attack +{c['blade'] - base_m.blades}",
                            }
                        )
                    elif c["blade"] < base_m.blades:
                        modifiers.append(
                            {
                                "type": "blade",
                                "value": c["blade"] - base_m.blades,
                                "label": f"Attack {c['blade'] - base_m.blades}",
                            }
                        )

                    for j in range(len(c["hearts"])):
                        if j < len(base_m.hearts) and c["hearts"][j] > base_m.hearts[j]:
                            modifiers.append(
                                {"type": "heart", "color_idx": j, "value": c["hearts"][j] - base_m.hearts[j]}
                            )

                c["modifiers"] = modifiers

                # Add valid actions for stage highlighting
                valid_actions = []
                if len(legal_mask) > 0:
                    # ABILITY is 200 + slot_idx * 10 + ab_idx
                    for ab_idx in range(10):
                        aid = 200 + i * 10 + ab_idx
                        if aid < len(legal_mask) and legal_mask[aid]:
                            valid_actions.append(aid)
                    # SELECT_STAGE is 560 + slot_idx
                    aid = 560 + i
                    if aid < len(legal_mask) and legal_mask[aid]:
                        valid_actions.append(aid)
                c["valid_actions"] = valid_actions

                stage.append(c)
            else:
                stage.append(None)

        # Live Guide Logic
        total_hearts = gs.get_total_hearts(p_idx)  # [u32; 7]
        temp_hearts = list(total_hearts)

        live_zone = []
        rust_lives = p.live_zone
        rust_revealed = p.live_zone_revealed
        for i in range(3):
            cid = rust_lives[i]
            if cid >= 0:
                c = self.serialize_card(cid, is_viewable=rust_revealed[i], peek=is_viewable, lang=lang)

                # Fulfillment (Rule 8.4.1)
                if cid in self.live_db:
                    l = self.live_db[cid]
                    req = l.required_hearts
                    filled = [0] * 7
                    # Specific
                    for ci in range(6):
                        take = min(temp_hearts[ci], req[ci])
                        filled[ci] = int(take)
                        temp_hearts[ci] -= take
                    # Any
                    req_any = req[6] if len(req) > 6 else 0
                    rem_total = sum(temp_hearts[:6]) + temp_hearts[6]
                    take_any = min(rem_total, req_any)
                    filled[6] = int(take_any)
                    # Note: We don't decrement from temp_hearts for 'any' matching the Python serializer's logic

                    c["filled_hearts"] = filled
                    c["is_cleared"] = all(filled[ci] >= req[ci] for ci in range(6)) and (filled[6] >= req_any)
                    c["required_hearts"] = list(req)

                c["modifiers"] = []
                live_zone.append(c)
            else:
                live_zone.append(None)

        energy = []
        rust_energy = p.energy_zone
        rust_tapped_energy = p.tapped_energy
        for i, cid in enumerate(rust_energy):
            energy.append(
                {
                    "id": i,
                    "tapped": rust_tapped_energy[i],
                    "card": self.serialize_card(cid, is_viewable=False, lang=lang),
                }
            )

        # Convert bitmask to list of selected indices for frontend
        mulligan_selection_list = [i for i in range(len(p.hand)) if (p.mulligan_selection >> i) & 1]

        return {
            "player_id": p.player_id,
            "score": p.score,
            "is_active": (gs.current_player == p_idx),
            "hand": hand,
            "hand_count": len(hand),
            "deck_count": p.deck_count,
            "energy_deck_count": p.energy_deck_count,
            "discard": [self.serialize_card(cid, lang=lang) for cid in p.discard],
            "discard_count": len(p.discard),
            "energy": energy,
            "energy_count": len(energy),
            "energy_untapped": sum(1 for t in rust_tapped_energy if not t),
            "live_zone": live_zone,
            "live_zone_count": sum(1 for cid in rust_lives if cid >= 0),
            "stage": stage,
            "success_lives": [self.serialize_card(cid, lang=lang) for cid in p.success_lives],
            "restrictions": [],
            "total_hearts": [int(h) for h in total_hearts],
            "total_blades": int(gs.get_total_blades(p_idx)),
            "mulligan_selection": mulligan_selection_list,
            "looked_cards": [self.serialize_card(cid, lang=lang) for cid in getattr(p, "looked_cards", [])],
        }

    def serialize_state(self, gs: engine_rust.PyGameState, viewer_idx=0, mode="pve", is_pvp=False, lang="jp"):
        s = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])
        # Cache legal_mask once to avoid multiple expensive calls
        legal_mask = gs.get_legal_actions()

        players = [
            self.serialize_player(gs.get_player(0), gs, 0, viewer_idx, legal_mask, lang=lang),
            self.serialize_player(gs.get_player(1), gs, 1, viewer_idx, legal_mask, lang=lang),
        ]

        # Action Metadata - reuse cached legal_mask
        legal_actions = []

        # Compatibility wrapper for get_action_desc
        compat_gs = RustCompatGameState(gs, self.member_db, self.live_db, self.energy_db)

        # Only show actions if viewer is active (or in RPS phase where both act)
        if viewer_idx == gs.current_player or gs.phase == Phase.RPS or gs.phase == Phase.TurnChoice:
            for i, v in enumerate(legal_mask):
                if v:
                    desc = get_action_desc(i, compat_gs, lang=lang, text=gs.pending_choice_text)
                    meta = {"id": i, "desc": desc, "name": desc, "description": desc}

                    # Enrich with metadata for UI highlighting
                    phase = gs.phase  # Assumed int

                    if 5000 <= i <= 5001:
                        meta["type"] = "TURN_CHOICE"
                        meta["name"] = s["choose_turn_order"] if i == 5000 else s["choose_turn_order"]
                        meta["choice"] = i - 5000
                    elif 10000 <= i <= 12000:
                        meta["type"] = "RPS"
                        signs = [s["rock"], s["paper"], s["scissors"]]
                        choice_idx = (i - 10000) % 1000
                        if choice_idx < len(signs):
                            meta["name"] = f"【RPS】 {signs[choice_idx]}"
                            meta["choice"] = choice_idx
                    elif 1 <= i <= 180:
                        meta["type"] = "PLAY"
                        meta["hand_idx"] = (i - 1) // 3
                        meta["area_idx"] = (i - 1) % 3
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang)
                            hand_cost = gs.get_member_cost(gs.current_player, cid, -1)
                            net_cost = gs.get_member_cost(gs.current_player, cid, meta["area_idx"])
                            meta.update(
                                {
                                    "img": c["img"],
                                    "name": c["name"],
                                    "cost": int(net_cost),
                                    "base_cost": int(hand_cost),
                                    "text": c.get("text", ""),
                                    "source_card_id": int(cid),
                                }
                            )
                    elif 200 <= i <= 299:
                        meta["type"] = "ABILITY"
                        adj = i - 200
                        meta["area_idx"] = adj // 10
                        meta["ability_idx"] = adj % 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["area_idx"] < len(curr_p.stage):
                            cid = curr_p.stage[meta["area_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang)
                                # Extract specific ability trigger/text
                                base_id = int(cid) & 0xFFFFF
                                triggers = []
                                raw_text = ""
                                if base_id in self.member_db:
                                    m = self.member_db[base_id]
                                    if hasattr(m, "abilities") and len(m.abilities) > meta["ability_idx"]:
                                        ab = m.abilities[meta["ability_idx"]]
                                        triggers = [int(ab.trigger)]
                                        raw_text = ab.raw_text

                                meta.update(
                                    {
                                        "img": c["img"],
                                        "name": desc,
                                        "source_card_id": int(cid),
                                        "triggers": triggers,
                                        "raw_text": raw_text,
                                        "text": "",  # Delay ability text
                                        "ability_idx": meta["ability_idx"],
                                        "description": desc,
                                    }
                                )
                    elif 300 <= i <= 359:
                        meta["type"] = "MULLIGAN"
                        meta["hand_idx"] = i - 300
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang)
                            meta.update(
                                {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "description": desc}
                            )
                    elif 400 <= i <= 459:
                        meta["type"] = "LIVE_SET"
                        meta["hand_idx"] = i - 400
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang)
                            meta.update(
                                {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "description": desc}
                            )
                    elif 100 <= i <= 159 or 500 <= i <= 549:
                        meta["type"] = "SELECT_HAND"
                        meta["hand_idx"] = (i - 100) if (100 <= i <= 159) else (i - 500)
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang)
                            meta.update(
                                {"img": c["img"], "name": c["name"], "text": c.get("text", ""), "description": desc}
                            )
                    elif 560 <= i <= 562:
                        meta["type"] = "SELECT_STAGE"
                        meta["area_idx"] = i - 560
                        curr_p = gs.get_player(gs.current_player)
                        cid = curr_p.stage[meta["area_idx"]]
                        if cid >= 0:
                            c = self.serialize_card(cid, lang=lang)
                            meta.update({"img": c["img"], "name": c["name"], "text": "", "description": desc})

                        # Add pending context for UI grouping
                        if gs.pending_card_id >= 0:
                            meta["source_card_id"] = int(gs.pending_card_id)
                            c = self.serialize_card(gs.pending_card_id, lang=lang)
                            meta["source_name"] = c["name"]
                            meta["source_img"] = c["img"]
                    elif 570 <= i <= 579:
                        meta["type"] = "SELECT_MODE"
                        meta["index"] = i - 570
                    elif 580 <= i <= 585:
                        meta["type"] = "COLOR_SELECT"
                        meta["index"] = i - 580
                        colors = s["color_names"]
                        if meta["index"] < len(colors):
                            meta["color"] = ["Red", "Blue", "Green", "Yellow", "Purple", "Pink"][
                                meta["index"]
                            ]  # Internal ID
                            color_label = colors[meta["index"]]
                            meta["name"] = f"{s['select_color']}: {color_label}"
                            meta["description"] = meta["name"]
                    elif 900 <= i <= 902:
                        meta["type"] = "SELECT_LIVE"
                        meta["area_idx"] = i - 900
                        curr_p = gs.get_player(gs.current_player)
                        if meta["area_idx"] < len(curr_p.live_zone):
                            cid = curr_p.live_zone[meta["area_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang)
                                meta.update(
                                    {
                                        "img": c["img"],
                                        "name": c["name"],
                                        "source_card_id": int(cid),
                                        "raw_text": c.get("text", ""),
                                        "description": desc,
                                    }
                                )
                    elif 590 <= i <= 599:
                        meta["type"] = "ABILITY_TRIGGER"
                        idx = i - 590
                        if idx < len(gs.triggered_abilities):
                            t_obj = gs.triggered_abilities[idx]
                            # t_obj is [type, params, card_obj]
                            # PyTriggeredAbility has .card_id or .source_card_id?
                            # Based on desc_utils.py: cid = getattr(t_obj[2], "card_id", -1)
                            t_src = t_obj[2] if len(t_obj) > 2 else None
                            cid = getattr(t_src, "card_id", -1) if t_src else -1
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang)
                                meta.update(
                                    {
                                        "source_card_id": int(cid),
                                        "img": c["img"],
                                        "name": c["name"],
                                        "text": c.get("text", ""),
                                    }
                                )
                    elif 550 <= i <= 849:
                        # Shared range for Ability choices, Card selections, and Opponent targeting
                        meta["type"] = "ABILITY"
                        meta["area_idx"] = gs.pending_area_idx

                        # Enrich based on pending choice context
                        raw_choices = compat_gs.pending_choices
                        if raw_choices:
                            ctype, cparams = raw_choices[0]
                            # index within the 10-slot block for this ability
                            choice_idx = (i - 550) % 10

                            # 1. Selection from a list (e.g. Look at top 3, choose 1)
                            if ctype in (
                                "SELECT_FROM_LIST",
                                "SELECT_SUCCESS_LIVE",
                                "ORDER_DECK",
                                "SELECT_FROM_DISCARD",
                                "LOOK_AND_CHOOSE",
                            ):
                                cards = cparams.get("cards", [])
                                if choice_idx < len(cards):
                                    cid = cards[choice_idx]
                                    c = self.serialize_card(cid, lang=lang)
                                    meta.update(
                                        {
                                            "type": "SELECT",
                                            "img": c["img"],
                                            "name": c["name"],
                                            "text": c.get("text", ""),
                                            "ability": c.get("text", ""),
                                            "source_card_id": int(cid),
                                        }
                                    )
                                    if ctype == "ORDER_DECK":
                                        meta["type"] = "ORDER_DECK"
                                    if ctype == "SELECT_HAND_DISCARD":
                                        meta["type"] = "SELECT_HAND"
                                        meta["hand_idx"] = choice_idx

                            # 2. Target Opponent Member (600-602)
                            elif ctype == "TARGET_OPPONENT_MEMBER" and 600 <= i <= 602:
                                meta["type"] = "TARGET_OPPONENT"
                                meta["index"] = i - 600
                                opp = gs.get_player(1 - gs.current_player)
                                cid = opp.stage[meta["index"]]
                                if cid >= 0:
                                    c = self.serialize_card(cid, lang=lang)
                                    meta.update(
                                        {
                                            "img": c["img"],
                                            "name": c["name"],
                                            "text": c.get("text", ""),
                                            "ability": c.get("text", ""),
                                            "source_card_id": int(cid),
                                        }
                                    )

                            # 3. Fallback: Source card metadata
                            else:
                                cid = gs.pending_card_id
                                if cid >= 0:
                                    c = self.serialize_card(cid, lang=lang)
                                    meta.update(
                                        {"img": c["img"], "name": desc, "text": c.get("text", ""), "description": desc}
                                    )
                        else:
                            # Fallback if no pending choice context
                            cid = gs.pending_card_id
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang)
                                meta.update(
                                    {"img": c["img"], "name": desc, "text": c.get("text", ""), "description": desc}
                                )

                    elif 2000 <= i <= 2999:
                        meta["type"] = "ABILITY"
                        adj = i - 2000
                        discard_idx = adj // 10
                        ability_idx = adj % 10
                        curr_p = gs.get_player(gs.current_player)
                        if discard_idx < len(curr_p.discard):
                            cid = curr_p.discard[discard_idx]
                            c = self.serialize_card(cid, lang=lang)
                            meta.update(
                                {
                                    "img": c["img"],
                                    "name": desc,
                                    "source_card_id": int(cid),
                                    "ability_idx": ability_idx,
                                    "description": desc,
                                    "location": "discard",
                                }
                            )
                    elif 1000 <= i <= 1999:
                        # Range for OnPlay choices (Mode select, slot select context)
                        # We treat these as PLAY actions so they group with the placement grid
                        meta["type"] = "PLAY"
                        adj = i - 1000
                        meta["hand_idx"] = adj // 100
                        meta["area_idx"] = (adj % 100) // 10
                        meta["choice_idx"] = adj % 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang)
                            # Get costs for UI if applicable
                            hand_cost = gs.get_member_cost(gs.current_player, cid, -1)
                            net_cost = gs.get_member_cost(gs.current_player, cid, meta["area_idx"])
                            meta.update(
                                {
                                    "img": c["img"],
                                    "name": c["name"],
                                    "cost": int(net_cost),
                                    "base_cost": int(hand_cost),
                                    "text": c.get("text", ""),
                                    "source_card_id": int(cid),
                                }
                            )

                    legal_actions.append(meta)

        # Pending Choice Serialization
        pending_choice = None

        # 1. Try to get explicit pending_choices (Python/Compat engine)
        raw_choices = compat_gs.pending_choices

        if raw_choices:
            choice_type, params = raw_choices[0]
            if isinstance(params, str):
                try:
                    params = json.loads(params)
                except:
                    params = {}

            # Handle Custom Choice Types
            if choice_type == "SELECT_HAND_DISCARD":
                choice_type = "SELECT_FROM_LIST"
                curr_p = gs.get_player(gs.current_player)
                params = {"cards": list(curr_p.hand), "description": s["select_discard_hand"]}
            elif choice_type == "SELECT_HAND_PLAY":
                choice_type = "SELECT_FROM_LIST"
                curr_p = gs.get_player(gs.current_player)
                params = {"cards": list(curr_p.hand), "description": s.get("select_hand_play", "Select a card to play")}
            elif choice_type == "SELECT_MODE":
                # Don't overwrite params — preserve any options that are already in them.
                # Count available options from legal mask range 570-579
                if not params.get("options"):
                    num_options = sum(1 for i in range(570, 580) if i < len(legal_mask) and legal_mask[i])
                    params = {
                        **params,
                        "options": [f"Option {i + 1}" for i in range(num_options)],
                        "description": s["select_mode"],
                    }
                # Keep type as SELECT_MODE for frontend handler
                choice_type = "SELECT_MODE"

            source_name = params.get("source_member", s["card_effect"])
            source_img = None
            source_id = params.get("source_card_id", -1)

            if source_id != -1:
                c = self.serialize_card(source_id, lang=lang)
                source_name = c["name"]
                source_img = c["img"]
            elif "area" in params:
                curr_p = gs.get_player(gs.current_player)
                cid = curr_p.stage[params["area"]]
                if cid >= 0:
                    c = self.serialize_card(cid, lang=lang)
                    source_name = c["name"]
                    source_img = c["img"]
                    source_id = int(cid)

            pending_choice = {
                "type": choice_type,
                "description": params.get("effect_description", desc),
                "source_ability": params.get("source_ability", ""),
                "source_member": source_name,
                "source_img": source_img,
                "min": params.get("min", 1),
                "max": params.get("max", 1),
                "can_skip": params.get("can_skip", False),
                "params": params,
            }

        # 2. Fallback: Infer pending choice from legal action ranges (Rust Engine)
        elif not raw_choices and any(v for i, v in enumerate(legal_mask) if i >= 500):
            # Check ranges in priority order
            inferred_type = None
            inferred_desc = s["make_selection"]

            has_select_hand = any(legal_mask[i] for i in range(500, 560))
            has_select_stage = any(legal_mask[i] for i in range(560, 570))
            has_select_mode = any(legal_mask[i] for i in range(570, 580))
            has_select_color = any(legal_mask[i] for i in range(580, 586))
            has_ability_trigger = any(legal_mask[i] for i in range(590, 600))
            has_target_opp = any(legal_mask[i] for i in range(600, 603)) and (gs.phase == 4)  # MAIN only
            has_select_discard = any(legal_mask[i] for i in range(660, 720))
            # LIVE_RESULT choices (600+)
            has_select_success_live = any(legal_mask[i] for i in range(600, 720)) and gs.phase == 8  # Phase.LIVE_RESULT

            # Generic list/mode choices (600+) - catch all if not special
            has_generic_choice = (
                any(legal_mask[i] for i in range(600, 720)) and not has_target_opp and not has_select_success_live
            )

            has_rps = gs.phase == Phase.RPS
            has_turn_choice = gs.phase == Phase.TurnChoice

            # EXCLUDE 1000-1999 from triggering a generic modal if it's a placement choice
            # as these are handled in the board grid.
            has_select_list = any(legal_mask[i] for i in range(1000, 2000)) and gs.phase != 4  # Phase.MAIN

            inferred_params = {}

            if has_ability_trigger:
                # Triggers are top level, not usually a "choice" modal but a button
                pass
            elif has_rps:
                inferred_type = "RPS"
                inferred_desc = s["rps_choice"]
            elif has_turn_choice:
                inferred_type = "TURN_CHOICE"
                inferred_desc = s["choose_turn_order"]
            elif has_select_color:
                inferred_type = "SELECT_COLOR"
                inferred_desc = s["select_color"]
            elif has_select_mode:
                inferred_type = "SELECT_MODE"
                inferred_desc = s["select_mode"]
            elif has_select_success_live:
                inferred_type = "SELECT_SUCCESS_LIVE"
                inferred_desc = s["select_success_live"]
            elif has_target_opp:
                inferred_type = "TARGET_OPPONENT_MEMBER"
                inferred_desc = s["select_opp_member"]
            elif has_generic_choice:
                # Catch-all for Rust engine list choices
                inferred_type = "SELECT_FROM_LIST"
                inferred_desc = s["choose_option"]
            elif has_select_discard:
                inferred_type = "SELECT_FROM_DISCARD"
                inferred_desc = s["select_discard"]
                curr_p = gs.get_player(gs.current_player)
                inferred_params["available_members"] = list(curr_p.discard)
            elif has_select_stage:
                inferred_type = "SELECT_STAGE"
                inferred_desc = s["select_stage"]
            elif has_select_hand:
                inferred_type = "SELECT_FROM_HAND"
                inferred_desc = s["select_hand"]
            elif has_select_list:
                inferred_type = "SELECT_FROM_LIST"
                inferred_desc = s["choose_option"]

            if gs.pending_choice_text:
                inferred_desc = gs.pending_choice_text

            if inferred_type:
                # Try to resolve source info from gs.pending_card_id
                source_name = "Game"
                source_img = None
                source_id = int(gs.pending_card_id)
                if source_id >= 0:
                    c = self.serialize_card(source_id, lang=lang)
                    source_name = c["name"]
                    source_img = c["img"]

                pending_choice = {
                    "type": inferred_type,
                    "description": inferred_desc,
                    "source_member": source_name,
                    "source_img": source_img,
                    "source_id": source_id,
                    "min": 1,
                    "max": 1,
                    "can_skip": False,
                    "params": inferred_params,
                }

        # 3. New: Support Phase.RESPONSE (Choice postponing)
        elif gs.phase == Phase.RESPONSE:
            pending_card_id = gs.pending_card_id
            choice_type = gs.pending_choice_type or "PENDING_ABILITY"

            choice_desc = s["choose_option"]
            inferred_params = {}

            if choice_type == "ORDER_DECK":
                choice_desc = s["order_deck"]
                # Looking at p[gs.current_player].looked_cards
                curr_p = gs.get_player(gs.current_player)
                inferred_params["cards"] = list(curr_p.looked_cards)
            elif pending_card_id >= 0:
                c = self.serialize_card(pending_card_id, lang=lang)
                # Infer type from legal actions as fallback
                has_color = any(legal_mask[i] for i in range(1000, 2000) if i % 10 == 5) or any(
                    legal_mask[i] for i in range(550, 850) if i % 10 == 5
                )
                has_mode = any(legal_mask[i] for i in range(1000, 2000) if i % 10 == 1) or any(
                    legal_mask[i] for i in range(550, 850) if i % 10 == 1
                )

                if not gs.pending_choice_type:
                    if has_color:
                        choice_type = "SELECT_COLOR"
                        choice_desc = s["select_color"]
                    elif has_mode:
                        choice_type = "SELECT_MODE"
                        choice_desc = s["select_mode"]

                source_name = c["name"]
                source_img = c["img"]
            else:
                source_name = "Game"
                source_img = None

            pending_choice = {
                "type": choice_type,
                "description": choice_desc,
                "source_member": source_name,
                "source_img": source_img,
                "source_id": int(pending_card_id),
                "min": 1,
                "max": 1,
                "can_skip": False,
                "params": inferred_params,
            }

        return {
            "turn": gs.turn,
            "phase": gs.phase,
            "active_player": gs.current_player,
            "game_over": gs.is_terminal(),
            "winner": gs.get_winner(),
            "players": players,
            "legal_actions": legal_actions,
            "pending_choice": pending_choice,
            "rule_log": gs.rule_log,
            "performance_results": {int(k): v for k, v in json.loads(gs.last_performance_results).items()}
            if gs.phase in (6, 7, 8)
            else {},
            "last_performance_results": {int(k): v for k, v in json.loads(gs.last_performance_results).items()},
            "performance_history": json.loads(gs.performance_history),
            "mode": mode,
            "is_pvp": is_pvp,
            "my_player_id": viewer_idx,
            "needs_deck": gs.phase == Phase.DRAW,
        }
