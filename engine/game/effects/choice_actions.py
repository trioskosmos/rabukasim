from __future__ import annotations

import random
from typing import Any, Dict

import numpy as np

from engine.game.effects.hand import discard_hand_card, move_hand_card_to_discard
from engine.game.effects.zone_actions import move_stage_card
from engine.models.ability import Effect, EffectType, ResolvingEffect


def resolve_target_hand_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(p.hand):
        return

    eff = params.get("effect")
    if eff == "discard":
        cid = move_hand_card_to_discard(p, idx)
        if cid is None:
            return
        if getattr(game, "verbose", False):
            print(f"DEBUG: TARGET_HAND discarded card {cid}. Discard size now {len(p.discard)}")
        return

    cid = discard_hand_card(p, idx)
    if cid is None:
        return

    if eff == "energy_charge":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False
    elif eff == "place_under":
        target = params.get("target_area", -1)
        if target >= 0:
            p.add_stage_energy(target, cid)
    elif eff == "place_member":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = cid
        else:
            p.discard.append(cid)
    elif eff == "place_live":
        p.live_zone.append(cid)
        p.live_zone_revealed.append(True)
    elif eff == "place_energy":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False
    elif eff in {"place_energy_to_stage_energy", "place_member_to_stage_energy", "place_live_to_stage_energy"}:
        target = params.get("target_area", 0)
        p.add_stage_energy(target, cid)
    elif eff in {"place_energy_to_discard", "place_member_to_discard", "place_live_to_discard"}:
        p.discard.append(cid)
    elif eff in {"place_energy_to_success", "place_member_to_success", "place_live_to_success"}:
        p.success_lives.append(cid)
    elif eff in {"place_energy_to_removed", "place_member_to_removed", "place_live_to_removed"}:
        game.removed_cards.append(cid)


def resolve_target_live_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(p.live_zone):
        return

    cid = p.live_zone.pop(idx)
    if idx < len(p.live_zone_revealed):
        p.live_zone_revealed.pop(idx)

    eff = params.get("effect")
    if eff == "discard":
        p.discard.append(cid)
    elif eff == "remove":
        game.removed_cards.append(cid)
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "return_to_deck":
        p.main_deck.append(cid)
        random.shuffle(p.main_deck)
    elif eff == "return_to_success":
        p.success_lives.append(cid)


def resolve_target_deck_choice(game: Any, p: Any, params: Dict[str, Any], idx: int, choice_type: str) -> None:
    cards = params.get("cards", p.main_deck)
    if choice_type == "SELECT_FROM_LIST":
        if not 0 <= idx < len(cards):
            return
        cid = cards[idx]
    else:
        if not 0 <= idx < len(p.main_deck):
            return
        cid = p.main_deck.pop(idx)

    eff = params.get("effect")
    if eff == "place_member":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = cid
        else:
            p.discard.append(cid)
    elif eff == "place_live":
        p.live_zone.append(cid)
        p.live_zone_revealed.append(True)
    elif eff == "place_energy":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "return_to_discard":
        p.discard.append(cid)
    elif eff == "return_to_success":
        p.success_lives.append(cid)
    elif eff == "return_to_removed":
        game.removed_cards.append(cid)

    if choice_type != "SELECT_FROM_LIST":
        random.shuffle(p.main_deck)


def resolve_target_removed_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(game.removed_cards):
        return

    cid = game.removed_cards.pop(idx)
    eff = params.get("effect")
    if eff == "return_to_deck":
        p.main_deck.append(cid)
        random.shuffle(p.main_deck)
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "return_to_discard":
        p.discard.append(cid)
    elif eff == "return_to_success":
        p.success_lives.append(cid)
    elif eff == "place_member":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = cid
        else:
            p.discard.append(cid)
    elif eff == "place_live":
        p.live_zone.append(cid)
        p.live_zone_revealed.append(True)
    elif eff == "place_energy":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False


def resolve_target_success_lives_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(p.success_lives):
        return

    cid = p.success_lives.pop(idx)
    eff = params.get("effect")
    if eff == "place_energy":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False
    elif eff == "discard":
        p.discard.append(cid)
    elif eff == "remove":
        game.removed_cards.append(cid)
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "return_to_deck":
        p.main_deck.append(cid)
        random.shuffle(p.main_deck)
    elif eff == "return_to_discard":
        p.discard.append(cid)
    elif eff == "place_member":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = cid
        else:
            p.discard.append(cid)
    elif eff == "place_live":
        p.live_zone.append(cid)
        p.live_zone_revealed.append(True)


def resolve_target_energy_zone_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(p.energy_zone):
        return

    cid = p.energy_zone.pop(idx)
    if idx < len(p.tapped_energy):
        p.tapped_energy = np.delete(p.tapped_energy, idx)
        p.tapped_energy = np.pad(p.tapped_energy, (0, 64 - len(p.tapped_energy)), "constant")

    eff = params.get("effect")
    if eff == "return_to_deck":
        p.main_deck.append(cid)
        random.shuffle(p.main_deck)
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "discard":
        p.discard.append(cid)
    elif eff == "remove":
        game.removed_cards.append(cid)
    elif eff == "return_to_success":
        p.success_lives.append(cid)
    elif eff == "place_member":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = cid
        else:
            p.discard.append(cid)
    elif eff == "place_live":
        p.live_zone.append(cid)
        p.live_zone_revealed.append(True)


def resolve_target_energy_deck_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    if not 0 <= idx < len(p.energy_deck):
        return

    cid = p.energy_deck.pop(idx)
    eff = params.get("effect")
    if eff == "place_energy":
        p.energy_zone.append(cid)
        p.tapped_energy[len(p.energy_zone) - 1] = False
    elif eff == "discard":
        p.discard.append(cid)
    elif eff == "remove":
        game.removed_cards.append(cid)
    elif eff == "return_to_hand":
        p.hand.append(cid)
        p.hand_added_turn.append(game.turn_number)
    elif eff == "return_to_deck":
        p.main_deck.append(cid)
        random.shuffle(p.main_deck)
    elif eff == "return_to_success":
        p.success_lives.append(cid)
    elif eff == "return_to_discard":
        p.discard.append(cid)


def resolve_select_from_discard_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    cards = params.get("cards", [])
    if not 0 <= idx < len(cards):
        return

    sel = int(cards[idx])
    if sel not in p.discard:
        return
    p.discard.remove(sel)

    dest = params.get("destination", "hand")
    if dest == "hand":
        p.hand.append(sel)
        p.hand_added_turn.append(game.turn_number)
    elif dest == "stage":
        area = next((i for i in range(3) if p.stage[i] < 0), -1)
        if area >= 0:
            p.stage[area] = sel
        else:
            p.hand.append(sel)
            p.hand_added_turn.append(game.turn_number)


def resolve_select_from_list_choice(game: Any, p: Any, params: Dict[str, Any], idx: int) -> None:
    cards = params.get("cards", [])
    if not 0 <= idx < len(cards):
        return

    sel = cards.pop(idx)
    reason = params.get("reason")
    tp = game.players[params.get("target_player_id", p.player_id)]

    if reason in ("look_and_choose", "search_deck"):
        dest = params.get("destination", params.get("to", "hand"))
        if dest == "discard":
            tp.discard.append(sel)
        else:
            p.hand.append(sel)
            p.hand_added_turn.append(game.turn_number)
        if reason == "look_and_choose" and sel in game.looked_cards:
            game.looked_cards.remove(sel)
        return

    if reason == "look_and_reorder":
        if not hasattr(game, "_reorder_staged_cards"):
            game._reorder_staged_cards = []
        game._reorder_staged_cards.append(sel)
        if sel in game.looked_cards:
            game.looked_cards.remove(sel)

        any_number = params.get("any_number", False)
        reorder = params.get("reorder", False)
        if any_number and cards:
            game.pending_choices.insert(0, ("SELECT_FROM_LIST", {**params, "cards": cards}))
            return

        if game.looked_cards:
            for c in game.looked_cards:
                p.discard.append(c)
            game.looked_cards = []

        if reorder and game._reorder_staged_cards:
            game.pending_choices.insert(
                0,
                (
                    "SELECT_ORDER",
                    {
                        "cards": game._reorder_staged_cards.copy(),
                        "ordered": [],
                        "position": "top",
                        "player_id": p.player_id,
                    },
                ),
            )
            game._reorder_staged_cards = []
        elif game._reorder_staged_cards:
            for c in reversed(game._reorder_staged_cards):
                p.main_deck.insert(0, c)
            game._reorder_staged_cards = []
        return

    current_count = int(params.get("choose_count", params.get("count", 1)))
    rem_cards = cards
    if sel in rem_cards:
        rem_cards.remove(sel)

    looping = current_count > 1 and rem_cards
    if game.looked_cards and not looping and reason == "look_and_choose":
        if params.get("destination") == "discard":
            for c in reversed(rem_cards):
                tp.main_deck.insert(0, c)
        else:
            tp.discard.extend(rem_cards)
        game.looked_cards = []

    if reason == "search_deck":
        if sel in p.main_deck:
            p.main_deck.remove(sel)
        if not looping and params.get("shuffle"):
            random.shuffle(p.main_deck)
    elif reason == "activate_energy":
        found_idx = -1
        for i, ecid in enumerate(p.energy_zone):
            if ecid == sel and p.tapped_energy[i]:
                found_idx = i
                break
        if found_idx >= 0:
            p.tapped_energy[found_idx] = False
    elif reason == "place_under_from_energy":
        target = params.get("target_area", -1)
        if target >= 0:
            if isinstance(p.tapped_energy, (list, np.ndarray)):
                if isinstance(p.tapped_energy, np.ndarray):
                    p.tapped_energy[idx : len(p.energy_zone)] = p.tapped_energy[idx + 1 : len(p.energy_zone) + 1]
                else:
                    p.tapped_energy.pop(idx)
            p.add_stage_energy(target, sel)

    if looping:
        if "choose_count" in params:
            params["choose_count"] = str(current_count - 1) if isinstance(params["choose_count"], str) else current_count - 1
        params["count"] = current_count - 1
        params["cards"] = rem_cards
        game.pending_choices.insert(0, ("SELECT_FROM_LIST", params))


def handle_optional_select_from_list(game: Any, p: Any, params: Dict[str, Any]) -> bool:
    """Handle pass/finish behavior for optional SELECT_FROM_LIST choices."""
    reason = params.get("reason")
    if reason == "look_and_reorder":
        if game.looked_cards:
            for c in game.looked_cards:
                p.discard.append(c)
            game.looked_cards = []

        if params.get("reorder") and hasattr(game, "_reorder_staged_cards") and game._reorder_staged_cards:
            game.pending_choices.insert(
                0,
                (
                    "SELECT_ORDER",
                    {
                        "cards": game._reorder_staged_cards.copy(),
                        "ordered": [],
                        "position": "top",
                        "player_id": p.player_id,
                    },
                ),
            )
            game._reorder_staged_cards = []
        elif hasattr(game, "_reorder_staged_cards") and game._reorder_staged_cards:
            for c in reversed(game._reorder_staged_cards):
                p.main_deck.insert(0, c)
            game._reorder_staged_cards = []
        return True

    if reason == "look_and_choose" and game.looked_cards:
        target_player = game.players[params.get("target_player_id", p.player_id)]
        if params.get("destination") == "discard":
            for c in reversed(game.looked_cards):
                target_player.main_deck.insert(0, c)
        else:
            target_player.discard.extend(game.looked_cards)
        game.looked_cards = []
        return True

    return False


def resolve_target_member_choice(game: Any, p: Any, params: Dict[str, Any], area: int) -> None:
    if params.get("effect") == "buff":
        teff = params.get("target_effect")
        if teff:
            p.continuous_effects.append({"effect": teff, "target_slot": area, "expiry": "TURN_END"})
    elif params.get("effect") == "activate":
        p.tapped_members[area] = False
    elif params.get("effect") == "tap":
        p.tapped_members[area] = True
    elif params.get("effect") == "tap_self_chosen":
        p.tapped_members[area] = True
        p.members_tapped_by_opponent_this_turn.add(p.stage[area])
    elif params.get("effect") == "rest":
        p.rested_members[area] = True
    elif params.get("reason") == "position_change":
        step = params.get("step", "source")
        if step == "source" and p.stage[area] >= 0:
            game.pending_choices.insert(
                0,
                (
                    "TARGET_MEMBER_SLOT",
                    {**params, "reason": "position_change", "step": "dest", "source": area},
                ),
            )
        elif step == "dest":
            src = params.get("source")
            if src is not None and src != area:
                game._move_member(p, src, area)
    elif params.get("effect") == "return_to_hand":
        move_stage_card(game, p, area, "hand")
    elif params.get("effect") == "discard_member":
        move_stage_card(game, p, area, "discard")
    elif params.get("effect") == "remove_member":
        move_stage_card(game, p, area, "removed")
    elif params.get("effect") == "return_to_deck":
        move_stage_card(game, p, area, "deck")
    elif params.get("effect") == "return_to_success":
        move_stage_card(game, p, area, "success")
    elif params.get("effect") == "return_to_discard":
        move_stage_card(game, p, area, "discard")
    elif params.get("effect") == "return_to_removed":
        move_stage_card(game, p, area, "removed")
