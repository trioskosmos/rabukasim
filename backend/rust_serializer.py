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

FILTER_IS_OPTIONAL = 1 << 61

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
        "color_names": ["ピンク", "赤", "黄", "緑", "青", "紫"],
        "select_discard_hand": "捨てるカードを選択してください",
        "select_hand_play": "プレイするカードを選択してください",
        "pay_energy": "エネルギーを選択してください",
        "yes": "はい",
        "no": "いいえ",
        "done": "完了",
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
        "color_names": ["Pink", "Red", "Yellow", "Green", "Blue", "Purple"],
        "select_discard_hand": "Select card to discard",
        "select_hand_play": "Select card to play",
        "pay_energy": "Select Energy to Pay",
        "yes": "Yes",
        "no": "No",
        "done": "Done",
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

ACTION_BASE_PASS = 0
ACTION_BASE_MULLIGAN = 300
ACTION_BASE_LIVESET = 400
ACTION_BASE_MODE = 500
ACTION_BASE_COLOR = 580
ACTION_BASE_STAGE_SLOTS = 600
ACTION_BASE_HAND = 1000
ACTION_BASE_HAND_ACTIVATE = 1600
ACTION_BASE_HAND_CHOICE = 2200
ACTION_BASE_TURN_ORDER_FIRST = 5000
ACTION_BASE_HAND_SELECT = 8200
ACTION_BASE_STAGE = 8300
ACTION_BASE_STAGE_CHOICE = 8600
ACTION_BASE_DISCARD_ACTIVATE = 9300
ACTION_BASE_ENERGY = 10000
ACTION_BASE_CHOICE = 11000
ACTION_BASE_RPS = 20000
ACTION_BASE_RPS_P2 = 21000
CHOICE_DONE = 99


def _safe_int(value, default=-1):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _first_text(*values) -> str:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def _normalize_choice_key(value) -> str:
    return str(value or "").strip().lower().replace("-", "_")


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

    def _lookup_card_record(self, cid):
        cid_int = _safe_int(cid, -1)
        if cid_int < 0:
            return None, None

        base_id = cid_int & 0xFFFFF
        bid_str = str(base_id)
        if bid_str in self.member_db:
            return self.member_db[bid_str], "member"
        if bid_str in self.live_db:
            return self.live_db[bid_str], "live"
        if bid_str in self.energy_db:
            return self.energy_db[bid_str], "energy"
        return None, None

    def _ability_details(self, cid, ability_idx, lang="jp"):
        idx = _safe_int(ability_idx, -1)
        record, _ = self._lookup_card_record(cid)
        abilities = getattr(record, "abilities", []) if record is not None else []
        if idx < 0 or idx >= len(abilities):
            return {"label": "", "text": "", "trigger_label": ""}

        ability = abilities[idx]
        raw_text = str(getattr(ability, "raw_text", "")).strip()
        trigger = _safe_int(getattr(ability, "trigger", 0), 0)
        trigger_label = TRIGGER_ICONS.get(lang, TRIGGER_ICONS["jp"]).get(trigger, "")
        first_line = raw_text.split("\n")[0].strip() if raw_text else ""
        label = " ".join(part for part in (trigger_label, first_line) if part).strip()
        return {"label": label, "text": raw_text, "trigger_label": trigger_label}

    def _serialize_card_ids(self, card_ids, lang="jp", is_vanilla=False):
        cards = []
        for cid in card_ids or []:
            cid_int = _safe_int(cid, -1)
            if cid_int < 0:
                continue
            card = self.serialize_card(cid_int, lang=lang, is_vanilla=is_vanilla)
            if card:
                cards.append(card)
        return cards

    def _serialize_selection_cards(self, card_ids, lang="jp", is_vanilla=False):
        cards = []
        for selection_idx, cid in enumerate(card_ids or []):
            cid_int = _safe_int(cid, -1)
            if cid_int < 0:
                continue
            card = self.serialize_card(cid_int, lang=lang, is_vanilla=is_vanilla)
            if card:
                selection_card = dict(card)
                selection_card["selection_idx"] = selection_idx
                cards.append(selection_card)
        return cards

    def _default_prompt_text(self, choice_type, lang="jp"):
        s = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])
        kind = _normalize_choice_key(choice_type)
        if "color" in kind:
            return s["select_color"]
        if "mode" in kind:
            return s["select_mode"]
        if "energy" in kind:
            return s["pay_energy"]
        if "discard" in kind:
            return s["select_discard"]
        if "hand" in kind:
            return s["select_hand"]
        if "opponent" in kind:
            return s["select_opp_member"]
        if "stage" in kind or "member" in kind:
            return s["select_stage"]
        if "order" in kind:
            return s["order_deck"]
        return s["make_selection"]

    def _pending_target_player(self, choice_type, params, current_player):
        if isinstance(params, dict):
            if "target_player" in params:
                return _safe_int(params.get("target_player"), current_player)
            if "player_id" in params:
                return _safe_int(params.get("player_id"), current_player)

        kind = _normalize_choice_key(choice_type)
        if "opponent" in kind:
            return 1 - current_player
        return current_player

    def _resolve_choice_name(self, choice_idx, pending_choice, lang="jp"):
        s = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])
        options = pending_choice.get("options") or []
        option_text = pending_choice.get("options_text") or []
        if 0 <= choice_idx < len(options):
            option = options[choice_idx]
            if isinstance(option, dict):
                text = _first_text(option.get("name"), option.get("text"), option.get("label"), option.get("value"))
                if text:
                    return text
            elif isinstance(option, (list, tuple)) and option:
                text = _first_text(option[0])
                if text:
                    return text
            else:
                text = _first_text(option)
                if text:
                    return text

        if 0 <= choice_idx < len(option_text):
            text = _first_text(option_text[choice_idx])
            if text:
                return text

        kind = _normalize_choice_key(pending_choice.get("choice_type") or pending_choice.get("type"))
        skip_label = "いいえ / スキップ" if lang == "jp" else "No / Skip"
        if "optional" in kind:
            if choice_idx == 0:
                return s["yes"]
            if choice_idx == 1:
                return skip_label
        if choice_idx == CHOICE_DONE and (
            "optional" in kind
            or (kind == "look_and_choose" and _safe_int(pending_choice.get("filter_attr"), 0) & FILTER_IS_OPTIONAL)
        ):
            return skip_label
        if choice_idx == CHOICE_DONE:
            return s["done"]

        return ""

    def _slot_name(self, slot_idx, lang="jp"):
        if lang == "jp":
            return f"メンバー{slot_idx + 1}"
        return f"Member {slot_idx + 1}"

    def _zone_card_id(self, player, zone, index):
        if player is None or index is None or index < 0:
            return -1

        zone_map = {
            "hand": getattr(player, "hand", []),
            "stage": getattr(player, "stage", []),
            "discard": getattr(player, "discard", []),
            "energy": getattr(player, "energy_zone", []),
            "live": getattr(player, "live_zone", []),
        }
        cards = zone_map.get(zone, [])
        if index >= len(cards):
            return -1
        return _safe_int(cards[index], -1)

    def _populate_card_fields(self, meta, cid, lang="jp", is_vanilla=False, source_card_id=None, ability_idx=None):
        cid_int = _safe_int(cid, -1)
        if cid_int < 0:
            return

        card = self.serialize_card(cid_int, lang=lang, is_vanilla=is_vanilla)
        meta.update({
            "img": card["img"],
            "card_id": int(cid_int),
            "name": card["name"],
        })
        if "text" in card and card.get("text"):
            meta["text"] = card.get("text", "")
        if source_card_id is not None:
            meta["source_card_id"] = int(source_card_id)
        else:
            meta["source_card_id"] = int(cid_int)

        if ability_idx is not None:
            ability_info = self._ability_details(cid_int, ability_idx, lang)
            if ability_info["label"]:
                meta["name"] = ability_info["label"]
            if ability_info["text"]:
                meta["text"] = ability_info["text"]

    def _populate_zone_card_fields(self, meta, gs, player_idx, zone, index, lang="jp", source_card_id=None, ability_idx=None):
        player = gs.get_player(player_idx)
        cid = self._zone_card_id(player, zone, index)
        if cid >= 0:
            self._populate_card_fields(
                meta,
                cid,
                lang=lang,
                is_vanilla=gs.db.is_vanilla,
                source_card_id=source_card_id,
                ability_idx=ability_idx,
            )
        return cid

    def _normalize_pending_choice(self, gs, raw_choice_type, params, lang="jp"):
        params = params if isinstance(params, dict) else {}
        choice_type = params.get("choice_type") or raw_choice_type
        source_id = _safe_int(params.get("source_card_id", gs.pending_card_id), -1)
        if source_id < 0:
            source_id = _safe_int(gs.pending_card_id, -1)

        source_card = self.serialize_card(source_id, lang=lang, is_vanilla=gs.db.is_vanilla) if source_id >= 0 else None
        source_name = source_card["name"] if source_card else "Game"
        source_img = source_card["img"] if source_card else None
        source_player = _safe_int(params.get("source_player"), gs.current_player)
        target_player = self._pending_target_player(choice_type, params, source_player)
        ability_index = _safe_int(params.get("ability_index"), -1)
        ability_info = self._ability_details(source_id, ability_index, lang)

        choice_text = _first_text(params.get("choice_text"), gs.pending_choice_text)
        text = _first_text(choice_text, params.get("effect_description"), self._default_prompt_text(choice_type, lang))
        actions = [_safe_int(action, -1) for action in params.get("actions", []) if _safe_int(action, -1) >= 0]
        options = params.get("options") if isinstance(params.get("options"), list) else []
        option_text = [self._resolve_choice_name(idx, {"options": options, "choice_type": choice_type, "type": raw_choice_type}, lang) for idx in range(len(options))]

        selection_ids = []
        if isinstance(params.get("cards"), list):
            selection_ids = [_safe_int(cid, -1) for cid in params.get("cards", [])]
        elif _normalize_choice_key(raw_choice_type) in {"select_from_list", "orderdeck", "order_deck"}:
            chooser = gs.get_player(source_player)
            selection_ids = [_safe_int(cid, -1) for cid in getattr(chooser, "looked_cards", [])]

        selection_cards = self._serialize_selection_cards(selection_ids, lang=lang, is_vanilla=gs.db.is_vanilla)
        v_remaining = _safe_int(params.get("v_remaining"), -1)
        choose_count = _safe_int(params.get("choose_count"), -1)
        if choose_count < 0 and v_remaining >= 0:
            choose_count = v_remaining + 1

        pending_choice = {
            "type": raw_choice_type,
            "choice_type": choice_type,
            "filter_attr": _safe_int(params.get("filter_attr"), 0),
            "description": _first_text(params.get("effect_description"), choice_text),
            "text": text,
            "title": text,
            "choice_text": choice_text,
            "source_member": source_name,
            "source_img": source_img,
            "source_card_id": int(source_id),
            "source_player": source_player,
            "source_area": _safe_int(params.get("source_area", params.get("area")), -1),
            "ability_index": ability_index,
            "opcode": _safe_int(params.get("effect_opcode"), -1),
            "target_slot": _safe_int(params.get("target_slot"), -1),
            "target_player": target_player,
            "source_ability": ability_info["text"],
            "trigger_label": ability_info["trigger_label"],
            "v_remaining": v_remaining,
            "choose_count": choose_count,
            "actions": actions,
            "options": options,
            "options_text": option_text,
            "selection_cards": selection_cards,
            "params": params,
        }
        return pending_choice

    def _attach_metadata(self, meta):
        metadata = {}
        for key in (
            "name",
            "description",
            "category",
            "type",
            "card_id",
            "source_card_id",
            "source_player",
            "target_player",
            "source_zone",
            "target_zone",
            "source_index",
            "target_index",
            "hand_idx",
            "slot_idx",
            "area_idx",
            "energy_idx",
            "ability_idx",
            "choice_idx",
            "selection_index",
            "location",
            "cost",
            "base_cost",
            "img",
            "text",
            "secondary_slot_idx",
            "areas_desc",
        ):
            if key in meta:
                metadata[key] = meta[key]
        meta["metadata"] = metadata
        return meta

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
                look_range = [300 + i, 400 + i, 8200 + i]
                for ab_idx in range(10):
                    look_range.append(1600 + i * 10 + ab_idx)
                    look_range.append(2200 + i * 10 + ab_idx)
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
                c["valid_actions"] = []
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
        pending_choice = None
        if raw_choices:
            choice_type, choice_params = raw_choices[0]
            pending_choice = self._normalize_pending_choice(gs, choice_type, choice_params, lang)

        pending_source_card_id = pending_choice["source_card_id"] if pending_choice else _safe_int(gs.pending_card_id, -1)
        pending_source_player = pending_choice["source_player"] if pending_choice else gs.current_player
        pending_target_player = pending_choice["target_player"] if pending_choice else gs.current_player
        pending_selection_cards = pending_choice.get("selection_cards", []) if pending_choice else []
        pending_selection_map = {
            _safe_int(card.get("selection_idx"), idx): _safe_int(card.get("id"), -1)
            for idx, card in enumerate(pending_selection_cards)
            if _safe_int(card.get("id"), -1) >= 0
        }

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

                    if ACTION_BASE_TURN_ORDER_FIRST <= i <= ACTION_BASE_TURN_ORDER_FIRST + 1:
                        meta["type"] = "TURN_CHOICE"
                        meta["category"] = "SYSTEM"
                        meta["choice"] = i - ACTION_BASE_TURN_ORDER_FIRST
                        meta["choice_idx"] = meta["choice"]
                        meta["name"] = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["choose_turn_order"]
                    elif ACTION_BASE_RPS <= i <= ACTION_BASE_RPS_P2 + 2:
                        meta["type"] = "RPS"
                        meta["category"] = "SYSTEM"
                        choice_idx = (i - ACTION_BASE_RPS) % 1000
                        meta["choice"] = choice_idx
                        meta["choice_idx"] = choice_idx
                        rps_names = {
                            0: SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["rock"],
                            1: SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["paper"],
                            2: SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["scissors"],
                        }
                        meta["name"] = rps_names.get(choice_idx, meta["name"])
                    elif i == ACTION_BASE_PASS:
                        meta["type"] = "SYSTEM"
                        meta["category"] = "SYSTEM"
                        if pending_choice:
                            meta["name"] = self._resolve_choice_name(CHOICE_DONE, pending_choice, lang)
                        elif gs.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
                            meta["name"] = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["done"]
                    elif ACTION_BASE_HAND <= i <= ACTION_BASE_HAND_ACTIVATE - 1:
                        meta["type"] = "PLAY"
                        meta["category"] = "PLAY"
                        meta["hand_idx"] = (i - ACTION_BASE_HAND) // 10
                        meta["area_idx"] = (i - ACTION_BASE_HAND) % 10
                        meta["slot_idx"] = meta["area_idx"]
                        meta["source_zone"] = "hand"
                        meta["source_index"] = meta["hand_idx"]
                        meta["target_zone"] = "stage"
                        meta["target_index"] = meta["area_idx"]
                        meta["source_player"] = gs.current_player
                        meta["target_player"] = gs.current_player
                        player = gs.get_player(gs.current_player)
                        if meta["hand_idx"] < len(player.hand):
                            cid = self._zone_card_id(player, "hand", meta["hand_idx"])
                            net_cost = gs.get_member_cost(gs.current_player, cid, meta["area_idx"])
                            self._populate_card_fields(meta, cid, lang=lang, is_vanilla=gs.db.is_vanilla)
                            meta["cost"] = int(net_cost)
                    elif ACTION_BASE_HAND_ACTIVATE <= i <= ACTION_BASE_HAND_CHOICE - 1:
                        adj = i - ACTION_BASE_HAND_ACTIVATE
                        meta["type"] = "HAND_ABILITY"
                        meta["category"] = "ABILITY"
                        meta["hand_idx"] = adj // 10
                        meta["ability_idx"] = adj % 10
                        meta["source_zone"] = "hand"
                        meta["source_index"] = meta["hand_idx"]
                        meta["source_player"] = gs.current_player
                        self._populate_zone_card_fields(meta, gs, gs.current_player, "hand", meta["hand_idx"], lang=lang, ability_idx=meta["ability_idx"])
                    elif ACTION_BASE_STAGE <= i <= ACTION_BASE_STAGE_CHOICE - 1:
                        meta["type"] = "ABILITY"
                        meta["category"] = "ABILITY"
                        adj = i - ACTION_BASE_STAGE
                        meta["slot_idx"] = adj // 100
                        meta["ability_idx"] = (adj % 100) // 10
                        meta["source_zone"] = "stage"
                        meta["source_index"] = meta["slot_idx"]
                        meta["source_player"] = gs.current_player
                        self._populate_zone_card_fields(meta, gs, gs.current_player, "stage", meta["slot_idx"], lang=lang, ability_idx=meta["ability_idx"])
                    elif ACTION_BASE_MULLIGAN <= i <= ACTION_BASE_MULLIGAN + 59:
                        meta["type"] = "MULLIGAN"
                        meta["category"] = "MULLIGAN"
                        meta["hand_idx"] = i - ACTION_BASE_MULLIGAN
                        meta["source_zone"] = "hand"
                        meta["source_index"] = meta["hand_idx"]
                        meta["target_zone"] = "hand"
                        meta["target_index"] = meta["hand_idx"]
                        meta["source_player"] = gs.current_player
                        meta["target_player"] = gs.current_player
                        self._populate_zone_card_fields(meta, gs, gs.current_player, "hand", meta["hand_idx"], lang=lang)
                    elif ACTION_BASE_LIVESET <= i <= ACTION_BASE_LIVESET + 99:
                        meta["type"] = "LIVE_SET"
                        meta["category"] = "LIVE_SET"
                        meta["hand_idx"] = i - ACTION_BASE_LIVESET
                        meta["source_zone"] = "hand"
                        meta["source_index"] = meta["hand_idx"]
                        meta["target_zone"] = "live"
                        meta["source_player"] = gs.current_player
                        meta["target_player"] = gs.current_player
                        self._populate_zone_card_fields(meta, gs, gs.current_player, "hand", meta["hand_idx"], lang=lang)
                    elif ACTION_BASE_MODE <= i <= ACTION_BASE_MODE + 59:
                        meta["type"] = "SELECT_MODE"
                        meta["category"] = "CHOICE"
                        meta["choice_idx"] = i - ACTION_BASE_MODE
                        meta["target_zone"] = "mode"
                        meta["name"] = self._resolve_choice_name(meta["choice_idx"], pending_choice or {}, lang)
                    elif ACTION_BASE_COLOR <= i <= ACTION_BASE_COLOR + 7:
                        meta["type"] = "COLOR_SELECT"
                        meta["category"] = "CHOICE"
                        meta["choice_idx"] = i - ACTION_BASE_COLOR
                        meta["target_zone"] = "color"
                        colors = SERIALIZER_STRINGS.get(lang, SERIALIZER_STRINGS["jp"])["color_names"]
                        if meta["choice_idx"] < len(colors):
                            meta["name"] = colors[meta["choice_idx"]]
                    elif ACTION_BASE_HAND_SELECT <= i <= ACTION_BASE_HAND_SELECT + 99:
                        meta["type"] = "SELECT_HAND"
                        meta["category"] = "SELECT_HAND"
                        meta["hand_idx"] = i - ACTION_BASE_HAND_SELECT
                        meta["target_zone"] = "hand"
                        meta["target_index"] = meta["hand_idx"]
                        meta["source_player"] = pending_source_player
                        meta["target_player"] = pending_target_player
                        self._populate_zone_card_fields(meta, gs, meta["target_player"], "hand", meta["hand_idx"], lang=lang, source_card_id=pending_source_card_id)
                    elif ACTION_BASE_STAGE_SLOTS <= i <= ACTION_BASE_STAGE_SLOTS + 2:
                        meta["type"] = "SELECT_STAGE"
                        meta["category"] = "SELECT_STAGE"
                        meta["slot_idx"] = i - ACTION_BASE_STAGE_SLOTS
                        meta["area_idx"] = meta["slot_idx"]
                        meta["target_zone"] = "stage"
                        meta["target_index"] = meta["slot_idx"]
                        meta["source_player"] = pending_source_player
                        meta["target_player"] = pending_target_player
                        cid = self._populate_zone_card_fields(meta, gs, meta["target_player"], "stage", meta["slot_idx"], lang=lang, source_card_id=pending_source_card_id)
                        if cid < 0:
                            meta["name"] = self._slot_name(meta["slot_idx"], lang)
                    elif ACTION_BASE_ENERGY <= i <= ACTION_BASE_ENERGY + 999:
                        meta["type"] = "ENERGY"
                        meta["category"] = "SELECT_ENERGY"
                        meta["energy_idx"] = i - ACTION_BASE_ENERGY
                        meta["target_zone"] = "energy"
                        meta["target_index"] = meta["energy_idx"]
                        meta["source_player"] = pending_source_player
                        meta["target_player"] = pending_target_player
                        self._populate_zone_card_fields(meta, gs, meta["target_player"], "energy", meta["energy_idx"], lang=lang, source_card_id=pending_source_card_id)
                    elif ACTION_BASE_CHOICE <= i <= 15999:
                        meta["type"] = "CHOICE"
                        meta["category"] = "CHOICE"
                        meta["choice_idx"] = i - ACTION_BASE_CHOICE
                        meta["source_player"] = pending_source_player
                        if meta["choice_idx"] == CHOICE_DONE:
                            meta["name"] = self._resolve_choice_name(CHOICE_DONE, pending_choice or {}, lang)
                        elif meta["choice_idx"] in pending_selection_map:
                            cid = pending_selection_map[meta["choice_idx"]]
                            self._populate_card_fields(meta, cid, lang=lang, is_vanilla=gs.db.is_vanilla, source_card_id=pending_source_card_id)
                            meta.update({
                                "target_zone": "selection",
                                "selection_index": meta["choice_idx"],
                                "target_index": meta["choice_idx"],
                            })
                        else:
                            meta["name"] = self._resolve_choice_name(meta["choice_idx"], pending_choice or {}, lang)
                    elif ACTION_BASE_HAND_CHOICE <= i <= ACTION_BASE_HAND_CHOICE + 599:
                        meta["type"] = "CHOICE"
                        meta["category"] = "CHOICE"
                        meta["hand_idx"] = (i - ACTION_BASE_HAND_CHOICE) // 10
                        meta["choice_idx"] = (i - ACTION_BASE_HAND_CHOICE) % 10
                        meta["target_zone"] = "hand"
                        meta["target_index"] = meta["hand_idx"]
                        meta["source_player"] = pending_source_player
                        meta["target_player"] = pending_target_player
                        self._populate_zone_card_fields(meta, gs, meta["target_player"], "hand", meta["hand_idx"], lang=lang, source_card_id=pending_source_card_id)
                    elif ACTION_BASE_STAGE_CHOICE <= i <= ACTION_BASE_STAGE_CHOICE + 299:
                        meta["type"] = "CHOICE"
                        meta["category"] = "CHOICE"
                        meta["slot_idx"] = (i - ACTION_BASE_STAGE_CHOICE) // 100
                        meta["choice_idx"] = (i - ACTION_BASE_STAGE_CHOICE) % 100
                        meta["area_idx"] = meta["slot_idx"]
                        meta["target_zone"] = "stage"
                        meta["target_index"] = meta["slot_idx"]
                        meta["source_player"] = pending_source_player
                        meta["target_player"] = pending_target_player
                        self._populate_zone_card_fields(meta, gs, meta["target_player"], "stage", meta["slot_idx"], lang=lang, source_card_id=pending_source_card_id)
                    elif ACTION_BASE_DISCARD_ACTIVATE <= i <= ACTION_BASE_DISCARD_ACTIVATE + 699:
                        adj = i - ACTION_BASE_DISCARD_ACTIVATE
                        meta["type"] = "DISCARD_ABILITY"
                        meta["category"] = "ABILITY"
                        meta["discard_idx"] = adj // 10
                        meta["ability_idx"] = adj % 10
                        meta["location"] = "discard"
                        meta["source_zone"] = "discard"
                        meta["source_index"] = meta["discard_idx"]
                        meta["source_player"] = gs.current_player
                        self._populate_zone_card_fields(meta, gs, gs.current_player, "discard", meta["discard_idx"], lang=lang, ability_idx=meta["ability_idx"])

                    if "source_card_id" not in meta and pending_source_card_id >= 0 and meta.get("type") in {
                        "SELECT_HAND",
                        "SELECT_STAGE",
                        "ENERGY",
                        "CHOICE",
                        "SELECT_MODE",
                        "COLOR_SELECT",
                    }:
                        meta["source_card_id"] = int(pending_source_card_id)

                    if "name" in meta and isinstance(meta["name"], str):
                        meta["name"] = meta["name"].strip() or desc

                    self._attach_metadata(meta)

                    legal_actions.append(meta)

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
