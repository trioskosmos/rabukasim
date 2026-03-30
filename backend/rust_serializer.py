from __future__ import annotations

import json
import os
import sys

# --- PATH SETUP ---
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


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


def _derived_card_text(abilities, fallback: str) -> str:
    if fallback and str(fallback).strip():
        return str(fallback)
    parts = []
    for ab in abilities or []:
        raw = str(getattr(ab, "raw_text", "")).strip()
        if raw:
            parts.append(raw)
    return "\n".join(parts)


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

    def step_opponent_turnseq(self):
        """Execute opponent's turn using TurnSequencer heuristic (vanilla mode AI)."""
        return self._gs.step_opponent_turnseq()

    def step_opponent_greedy(self, config=None):
        """Execute opponent's turn using greedy heuristic."""
        return self._gs.step_opponent_greedy(config)

    def step_opponent_mcts(self, sims, config=None):
        """Execute opponent's turn using MCTS."""
        return self._gs.step_opponent_mcts(sims, config)

    def __getattr__(self, name):
        """Delegate any other attribute/method access to self._gs."""
        return getattr(self._gs, name)


def serialize_card_rust(card_id, db=None, is_viewable=True):
    """Serialize a single card (legacy function for compatibility)."""
    if card_id < 0:
        return None
    if not is_viewable:
        return {"id": int(card_id), "name": "???", "type": "unknown", "img": "cards/back.png", "hidden": True}
    # This function is not actively used; the serializer class method is preferred
    return None


class RustGameStateSerializer:
    def __init__(self, py_member_db, py_live_db, py_energy_db):
        from engine.game.state_utils import MaskedDB

        self.member_db = py_member_db if isinstance(py_member_db, MaskedDB) else MaskedDB(py_member_db)
        self.live_db = py_live_db if isinstance(py_live_db, MaskedDB) else MaskedDB(py_live_db)
        self.energy_db = py_energy_db if isinstance(py_energy_db, MaskedDB) else MaskedDB(py_energy_db)
        self._card_cache = {}  # Cache for base card metadata

    def serialize_card(self, cid, is_viewable=True, peek=False, lang="jp", is_vanilla=False):
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

        cid_int = int(cid)
        base_id = cid_int & 0xFFFFF  # Mask with BASE_ID_MASK (20 bits)

        cache_key = (base_id, is_vanilla)
        if cache_key in self._card_cache:
            res = self._card_cache[cache_key].copy()
            res["id"] = cid_int
            return res

        res = None
        bid_str = str(base_id)
        if bid_str in self.member_db:
            m = self.member_db[bid_str]
            abilities = getattr(m, "abilities", [])
            at = _derived_card_text(abilities, getattr(m, "ability_text", "") or getattr(m, "original_text", ""))

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
                "original_text": at or m.original_text,
                "original_text_en": getattr(m, "original_text_en", ""),
                "ability": at or m.original_text,
            }
        elif bid_str in self.live_db:
            l = self.live_db[bid_str]
            abilities = getattr(l, "abilities", [])
            at = _derived_card_text(abilities, getattr(l, "ability_text", "") or getattr(l, "original_text", ""))

            res = {
                "card_no": l.card_no,
                "name": l.name,
                "type": "live",
                "score": l.score,
                "img": l.img_path,
                "required_hearts": list(l.required_hearts),
                "text": at,
                "original_text": at or l.original_text,
                "original_text_en": getattr(l, "original_text_en", ""),
                "ability": at or l.original_text,
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
            if is_vanilla:
                res["text"] = ""
                res["ability"] = ""
                res["original_text"] = ""
                res["original_text_en"] = ""
            self._card_cache[cache_key] = res
            res_instance = res.copy()
            res_instance["id"] = cid_int
            return res_instance

        return {"id": cid_int, "name": f"Card {base_id}", "type": "unknown", "img": "icon_blade.png"}

    def serialize_player(self, p, gs, p_idx, viewer_idx=0, legal_mask=None, lang="jp"):
        is_viewable = p_idx == viewer_idx
        is_vanilla = gs.db.is_vanilla

        hand = []
        if legal_mask is None:
            legal_mask = gs.get_legal_actions() if gs.current_player == p_idx else []
        elif gs.current_player != p_idx:
            legal_mask = []

        for i, cid in enumerate(p.hand):
            c = self.serialize_card(cid, is_viewable=is_viewable, lang=lang, is_vanilla=is_vanilla)
            if is_viewable:
                c["is_new"] = (p.hand_added_turn[i] == gs.turn) if i < len(p.hand_added_turn) else False
                valid_actions = []
                if len(legal_mask) > 0:
                    # PLAY base 1000
                    for area in range(3):
                        aid = 1000 + i * 10 + area
                        if aid < len(legal_mask) and legal_mask[aid]:
                            valid_actions.append(aid)
                look_range = [300 + i, 400 + i, 500 + i, 100 + i, 8200 + i, 1600 + i, 2200 + i]
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
                c = self.serialize_card(cid, is_viewable=True, lang=lang, is_vanilla=is_vanilla)
                c["tapped"] = bool(rust_tapped[i])
                c["energy"] = int(getattr(p, "stage_energy_count", [0, 0, 0])[i])
                eff_blade = gs.get_effective_blades(p_idx, i)
                eff_hearts = gs.get_effective_hearts(p_idx, i)
                c["blade"] = int(eff_blade)
                c["hearts"] = [int(h) for h in eff_hearts]
                modifiers = []
                base_m = self.member_db.get(int(cid))
                if base_m:
                    if c["blade"] > base_m.blades:
                        modifiers.append({"type": "blade", "value": c["blade"] - base_m.blades, "label": f"Attack +{c['blade'] - base_m.blades}"})
                    elif c["blade"] < base_m.blades:
                        modifiers.append({"type": "blade", "value": c["blade"] - base_m.blades, "label": f"Attack {c['blade'] - base_m.blades}"})
                    for j in range(len(c["hearts"])):
                        if j < len(base_m.hearts) and c["hearts"][j] > base_m.hearts[j]:
                            modifiers.append({"type": "heart", "color_idx": j, "value": c["hearts"][j] - base_m.hearts[j]})
                c["modifiers"] = modifiers
                valid_actions = []
                if len(legal_mask) > 0:
                    # STAGE Activate base 8300
                    for ab_idx in range(10):
                        aid = 8300 + i * 100 + ab_idx * 10
                        if aid < len(legal_mask) and legal_mask[aid]:
                            valid_actions.append(aid)
                        # Stage Choice base 8600
                        aid_choice = 8600 + i * 100 + ab_idx * 10
                        if aid_choice < len(legal_mask) and legal_mask[aid_choice]:
                            valid_actions.append(aid_choice)
                    # SELECT_STAGE base 600
                    aid = 600 + i
                    if aid < len(legal_mask) and legal_mask[aid]:
                        valid_actions.append(aid)
                c["valid_actions"] = valid_actions
                stage.append(c)
            else:
                stage.append(None)

        total_hearts = gs.get_total_hearts(p_idx)
        member_hearts = gs.get_total_member_hearts(p_idx)
        temp_hearts = list(total_hearts)
        live_zone = []
        rust_lives = p.live_zone
        rust_revealed = p.live_zone_revealed
        for i in range(3):
            cid = rust_lives[i]
            if cid >= 0:
                c = self.serialize_card(cid, is_viewable=rust_revealed[i], peek=is_viewable, lang=lang, is_vanilla=is_vanilla)
                if cid in self.live_db:
                    l = self.live_db[cid]
                    req = l.required_hearts
                    filled = [0] * 7
                    for ci in range(6):
                        take = min(temp_hearts[ci], req[ci])
                        filled[ci] = int(take)
                        temp_hearts[ci] -= take
                    req_any = req[6] if len(req) > 6 else 0
                    take_any_wild = min(temp_hearts[6], req_any)
                    filled[6] = int(take_any_wild)
                    temp_hearts[6] -= take_any_wild
                    req_any -= take_any_wild
                    if req_any > 0:
                        for ci in range(6):
                            if req_any <= 0: break
                            take = min(temp_hearts[ci], req_any)
                            filled[6] += int(take)
                            temp_hearts[ci] -= take
                            req_any -= take
                    c["filled_hearts"] = filled
                    c["is_cleared"] = all(filled[ci] >= req[ci] for ci in range(6)) and (filled[6] >= req[6])
                    c["required_hearts"] = list(req)
                c["modifiers"] = []
                valid_actions = []
                if len(legal_mask) > 0:
                    # SELECT_LIVE base 900
                    aid = 900 + i
                    if aid < len(legal_mask) and legal_mask[aid]:
                        valid_actions.append(aid)
                c["valid_actions"] = valid_actions
                live_zone.append(c)
            else:
                live_zone.append(None)

        energy = []
        rust_energy = p.energy_zone
        rust_tapped_energy = p.tapped_energy
        for i, cid in enumerate(rust_energy):
            e_card = {"id": i, "tapped": rust_tapped_energy[i], "card": self.serialize_card(cid, is_viewable=False, lang=lang, is_vanilla=is_vanilla)}
            valid_actions = []
            if len(legal_mask) > 0:
                # ENERGY Select base 10000
                aid = 10000 + i
                if aid < len(legal_mask) and legal_mask[aid]:
                    valid_actions.append(aid)
            e_card["valid_actions"] = valid_actions
            energy.append(e_card)

        mulligan_selection_list = [i for i in range(len(p.hand)) if (p.mulligan_selection >> i) & 1]
        initial_deck = [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in getattr(p, "initial_deck", [])] if is_viewable else []
        full_deck = [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in getattr(p, "deck", [])] if is_viewable else []
        energy_deck = [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in getattr(p, "energy_deck", [])] if is_viewable else []

        return {
            "player_id": p.player_id,
            "score": p.score,
            "is_active": (gs.current_player == p_idx),
            "hand": hand,
            "hand_count": len(hand),
            "deck_count": p.deck_count,
            "energy_deck_count": p.energy_deck_count,
            "initial_deck": initial_deck,
            "full_deck": full_deck,
            "energy_deck": energy_deck,
            "discard": [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in p.discard],
            "discard_count": len(p.discard),
            "energy": energy,
            "energy_count": len(energy),
            "energy_untapped": sum(1 for t in rust_tapped_energy if not t),
            "live_zone": live_zone,
            "live_zone_count": sum(1 for cid in rust_lives if cid >= 0),
            "stage": stage,
            "success_lives": [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in p.success_lives],
            "restrictions": [],
            "total_hearts": [int(h) for h in member_hearts],
            "total_blades": int(gs.get_total_blades(p_idx)),
            "mulligan_selection": mulligan_selection_list,
            "looked_cards": [self.serialize_card(cid, lang=lang, is_vanilla=is_vanilla) for cid in getattr(p, "looked_cards", [])],
        }

    def serialize_state(self, gs, viewer_idx=0, mode="pve", is_pvp=False, lang="jp"):
        SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])
        legal_mask = gs.get_legal_actions()
        compat_gs = RustCompatGameState(gs, self.member_db, self.live_db, self.energy_db)

        raw_choices = compat_gs.pending_choices
        pending_choice_type = None
        pending_choice_params = {}
        if raw_choices:
            pending_choice_type, pending_choice_params = raw_choices[0]

        pending_source_card_id = pending_choice_params.get("source_card_id", -1)
        if pending_source_card_id is None:
            pending_source_card_id = gs.pending_card_id
        else:
            pending_source_card_id = int(pending_source_card_id)
            if pending_source_card_id < 0:
                pending_source_card_id = gs.pending_card_id

        players = [
            self.serialize_player(gs.get_player(0), gs, 0, viewer_idx, legal_mask, lang=lang),
            self.serialize_player(gs.get_player(1), gs, 1, viewer_idx, legal_mask, lang=lang),
        ]

        legal_actions = []
        if viewer_idx == gs.current_player or gs.phase == Phase.RPS or gs.phase == Phase.TurnChoice:
            for i, v in enumerate(legal_mask):
                if v:
                    desc = get_action_desc(i, compat_gs, lang=lang, text=gs.pending_choice_text)
                    meta = {"id": i, "desc": desc, "name": desc, "description": desc}
                    
                    if 5000 <= i <= 5001:
                        meta["type"] = "TURN_CHOICE"
                        meta["choice"] = i - 5000
                    elif 20000 <= i <= 22000:
                        meta["type"] = "RPS"
                        choice_idx = (i - 20000) % 1000
                        meta["choice"] = choice_idx
                    elif 1000 <= i <= 1599:
                        meta["type"] = "PLAY"
                        meta["hand_idx"] = (i - 1000) // 10
                        meta["area_idx"] = (i - 1000) % 10 # Usually < 3
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            net_cost = gs.get_member_cost(gs.current_player, cid, meta["area_idx"])
                            meta.update({"img": c["img"], "name": c["name"], "cost": int(net_cost), "source_card_id": int(cid)})
                    elif 1600 <= i <= 2199:
                        # Hand Activate: abilities from hand (not yet played)
                        adj = i - 1600
                        meta["type"] = "HAND_ABILITY"
                        meta["hand_idx"] = adj // 10
                        meta["ability_idx"] = adj % 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "ability_idx": meta["ability_idx"]})
                    elif 8300 <= i <= 8599:
                        meta["type"] = "ABILITY"
                        adj = i - 8300
                        meta["slot_idx"] = adj // 100
                        meta["ability_idx"] = (adj % 100) // 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["slot_idx"] < len(curr_p.stage):
                            cid = curr_p.stage[meta["slot_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                                meta.update({"img": c["img"], "source_card_id": int(cid), "ability_idx": meta["ability_idx"]})
                    elif 300 <= i <= 359:
                        meta["type"] = "MULLIGAN"
                        meta["hand_idx"] = i - 300
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 400 <= i <= 459:
                        meta["type"] = "LIVE_SET"
                        meta["hand_idx"] = i - 400
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 100 <= i <= 159 or 500 <= i <= 559 or 8200 <= i <= 8259:
                        meta["type"] = "SELECT_HAND"
                        if 100 <= i <= 159: meta["hand_idx"] = i - 100
                        elif 500 <= i <= 559: meta["hand_idx"] = i - 500
                        else: meta["hand_idx"] = i - 8200
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 600 <= i <= 602:
                        meta["type"] = "SELECT_STAGE"
                        meta["slot_idx"] = i - 600
                        curr_p = gs.get_player(gs.current_player)
                        if meta["slot_idx"] < len(curr_p.stage):
                            cid = curr_p.stage[meta["slot_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                                meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 900 <= i <= 929:
                        meta["type"] = "SELECT_LIVE"
                        meta["slot_idx"] = i - 900
                        curr_p = gs.get_player(gs.current_player)
                        if meta["slot_idx"] < len(curr_p.live_zone):
                            cid = curr_p.live_zone[meta["slot_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                                meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 10000 <= i <= 10999:
                        meta["type"] = "ENERGY"
                        meta["energy_idx"] = i - 10000
                        curr_p = gs.get_player(gs.current_player)
                        if meta["energy_idx"] < len(curr_p.energy_zone):
                            cid = curr_p.energy_zone[meta["energy_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "name": c["name"]})
                    elif 11000 <= i <= 15999:
                        meta["type"] = "CHOICE"
                        meta["choice_idx"] = i - 11000
                    elif 2200 <= i <= 2799:
                        meta["type"] = "CHOICE"
                        meta["hand_idx"] = (i - 2200) // 10
                        meta["choice_idx"] = (i - 2200) % 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(curr_p.hand):
                            cid = curr_p.hand[meta["hand_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid)})
                    elif 8600 <= i <= 8899:
                        meta["type"] = "CHOICE"
                        meta["slot_idx"] = (i - 8600) // 100
                        meta["choice_idx"] = (i - 8600) % 100
                        curr_p = gs.get_player(gs.current_player)
                        if meta["slot_idx"] < len(curr_p.stage):
                            cid = curr_p.stage[meta["slot_idx"]]
                            if cid >= 0:
                                c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                                meta.update({"img": c["img"], "source_card_id": int(cid)})
                    elif 9300 <= i <= 9999:
                        # Discard Activate: abilities from discard pile
                        adj = i - 9300
                        meta["type"] = "DISCARD_ABILITY"
                        meta["discard_idx"] = adj // 10
                        meta["ability_idx"] = adj % 10
                        curr_p = gs.get_player(gs.current_player)
                        if meta["discard_idx"] < len(curr_p.discard):
                            cid = curr_p.discard[meta["discard_idx"]]
                            c = self.serialize_card(cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta.update({"img": c["img"], "source_card_id": int(cid), "ability_idx": meta["ability_idx"]})

                    legal_actions.append(meta)

        pending_choice = None
        if raw_choices:
            choice_type, params = raw_choices[0]
            if isinstance(params, str):
                try: params = json.loads(params)
                except: params = {}
            
            source_id = params.get("source_card_id", -1)
            source_name = "Game"
            source_img = None
            if source_id != -1:
                c = self.serialize_card(source_id, lang=lang, is_vanilla=gs.db.is_vanilla)
                source_name = c["name"]
                source_img = c["img"]

            pending_choice = {
                "type": choice_type,
                "description": params.get("effect_description", ""),
                "source_member": source_name,
                "source_img": source_img,
                "source_card_id": int(source_id),
                "params": params,
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
            "performance_results": json.loads(gs.last_performance_results) if gs.phase in (6, 7, 8) else {},
            "mode": mode,
            "is_pvp": is_pvp,
            "my_player_id": viewer_idx,
            "needs_deck": gs.phase == Phase.DRAW,
        }
