from __future__ import annotations

import copy
import random
from typing import Any

import numpy as np

from engine.game.effects.choices import (
    is_cost_payment_choice,
    normalize_choice_metadata,
    store_choice_answer,
)
from engine.game.effects.zone_actions import move_stage_card
from engine.game.enums import Phase
from engine.models.ability import Effect, EffectType, ResolvingEffect


def handle_choice(game: Any, action: int) -> None:
    self = game
    if not self.pending_choices:
        return
    choice_type, params = self.pending_choices.pop(0)
    is_cost_payment = is_cost_payment_choice(self, choice_type, params)
    if self.pending_activation:
        pass

    choice_metadata = normalize_choice_metadata(params)

    p_idx = params.get("player_id", self.current_player)
    p = self.players[p_idx]
    opp_idx = 1 - p_idx
    opp = self.players[opp_idx]
    cost_paid = False

    store_choice_answer(self, action)

    if choice_type == "TARGET_HAND":
        idx = action - 500
        if 0 <= idx < len(p.hand):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True

            cid = p.hand.pop(idx)
            if idx < len(p.hand_added_turn):
                p.hand_added_turn.pop(idx)

            eff = params.get("effect")
            if eff == "discard":
                p.discard.append(cid)
                if self.verbose:
                    print(f"DEBUG: TARGET_HAND discarded card {cid}. Discard size now {len(p.discard)}")
            elif eff == "energy_charge":
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
            elif eff in {
                "place_energy_to_stage_energy",
                "place_member_to_stage_energy",
                "place_live_to_stage_energy",
            }:
                target = params.get("target_area", 0)
                p.add_stage_energy(target, cid)
            elif eff in {"place_energy_to_discard", "place_member_to_discard", "place_live_to_discard"}:
                p.discard.append(cid)
            elif eff in {"place_energy_to_success", "place_member_to_success", "place_live_to_success"}:
                p.success_lives.append(cid)
            elif eff in {"place_energy_to_removed", "place_member_to_removed", "place_live_to_removed"}:
                self.removed_cards.append(cid)

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_HAND", params))

    elif choice_type == "TARGET_LIVE":
        idx = action - 820
        if 0 <= idx < len(p.live_zone):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            cid = p.live_zone.pop(idx)
            if idx < len(p.live_zone_revealed):
                p.live_zone_revealed.pop(idx)

            eff = params.get("effect")
            if eff == "discard":
                p.discard.append(cid)
            elif eff == "remove":
                self.removed_cards.append(cid)
            elif eff == "return_to_hand":
                p.hand.append(cid)
                p.hand_added_turn.append(self.turn_number)
            elif eff == "return_to_deck":
                p.main_deck.append(cid)
                random.shuffle(p.main_deck)
            elif eff == "return_to_success":
                p.success_lives.append(cid)

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_LIVE", params))

    elif choice_type in ("SELECT_FROM_DISCARD", "TARGET_DISCARD"):
        idx = action - 660
        source_list = params.get("cards", p.discard)
        if 0 <= idx < len(source_list):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True

            cid = source_list[idx]
            if cid in p.discard:
                p.discard.remove(cid)
            elif 0 <= idx < len(p.discard):
                cid = p.discard.pop(idx)

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
            elif eff == "return_to_deck":
                p.main_deck.append(cid)
                random.shuffle(p.main_deck)
            elif eff == "return_to_hand":
                p.hand.append(cid)
                p.hand_added_turn.append(self.turn_number)
            elif eff == "return_to_success":
                p.success_lives.append(cid)
            elif eff == "return_to_removed":
                self.removed_cards.append(cid)

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_DISCARD", params))

    elif choice_type in ("TARGET_DECK", "SELECT_FROM_LIST"):
        idx = action - 600
        if 0 <= idx < len(p.main_deck) or choice_type == "SELECT_FROM_LIST":
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True

            source_list = params.get("cards", p.main_deck)
            cid = None
            if 0 <= idx < len(source_list):
                cid = source_list.pop(idx) if choice_type != "SELECT_FROM_LIST" else source_list[idx]

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
                p.hand_added_turn.append(self.turn_number)
            elif eff == "return_to_discard":
                p.discard.append(cid)
            elif eff == "return_to_success":
                p.success_lives.append(cid)
            elif eff == "return_to_removed":
                self.removed_cards.append(cid)

            random.shuffle(p.main_deck)

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_DECK", params))

    elif choice_type == "TARGET_REMOVED":
        idx = action - 850
        if 0 <= idx < len(self.removed_cards):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            cid = self.removed_cards.pop(idx)

            eff = params.get("effect")
            if eff == "return_to_deck":
                p.main_deck.append(cid)
                random.shuffle(p.main_deck)
            elif eff == "return_to_hand":
                p.hand.append(cid)
                p.hand_added_turn.append(self.turn_number)
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

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_REMOVED", params))

    elif choice_type == "TARGET_SUCCESS_LIVES":
        idx = action - 760
        if 0 <= idx < len(p.success_lives):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            cid = p.success_lives.pop(idx)

            eff = params.get("effect")
            if eff == "place_energy":
                p.energy_zone.append(cid)
                p.tapped_energy[len(p.energy_zone) - 1] = False
            elif eff == "discard":
                p.discard.append(cid)
            elif eff == "remove":
                self.removed_cards.append(cid)
            elif eff == "return_to_hand":
                p.hand.append(cid)
                p.hand_added_turn.append(self.turn_number)
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

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_SUCCESS_LIVES", params))

    elif choice_type == "TARGET_ENERGY_ZONE":
        idx = action - 830
        if 0 <= idx < len(p.energy_zone):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
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
                p.hand_added_turn.append(self.turn_number)
            elif eff == "discard":
                p.discard.append(cid)
            elif eff == "remove":
                self.removed_cards.append(cid)
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

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_ENERGY_ZONE", params))

    elif choice_type == "TARGET_ENERGY_DECK":
        idx = action - 600
        if 0 <= idx < len(p.energy_deck):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            cid = p.energy_deck.pop(idx)

            eff = params.get("effect")
            if eff == "return_to_hand":
                p.hand.append(cid)
                p.hand_added_turn.append(self.turn_number)
            elif eff == "return_to_discard":
                p.discard.append(cid)
            elif eff == "return_to_success":
                p.success_lives.append(cid)
            elif eff == "return_to_removed":
                self.removed_cards.append(cid)
            elif eff == "place_energy":
                p.energy_zone.append(cid)
                p.tapped_energy[len(p.energy_zone) - 1] = False
            elif eff == "place_member":
                area = next((i for i in range(3) if p.stage[i] < 0), -1)
                if area >= 0:
                    p.stage[area] = cid
                else:
                    p.discard.append(cid)
            elif eff == "place_live":
                p.live_zone.append(cid)
                p.live_zone_revealed.append(True)

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_ENERGY_DECK", params))

    elif choice_type == "PAY_COST_OPTIONAL":
        if action == 570:
            cost_type = params.get("cost_type")
            amount = params.get("amount", 0)
            if cost_type == "discard":
                discard_params = {
                    **choice_metadata,
                    "reason": "cost",
                    "effect": "discard",
                    "is_optional": True,
                    "cost_index": params.get("cost_index", -1),
                    "count": amount,
                }
                self.pending_choices.append(("TARGET_HAND", discard_params))
                return False

            tapped = 0
            for i in range(len(p.energy_zone) - 1, -1, -1):
                if not p.tapped_energy[i]:
                    p.tapped_energy[i] = True
                    tapped += 1
                    if tapped >= amount:
                        break
            cost_paid = True
        else:
            cost_paid = False

    elif choice_type in ("TARGET_MEMBER", "TARGET_MEMBER_SLOT"):
        area = action - 560
        if 0 <= area < 3:
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
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
                    self.pending_choices.insert(
                        0,
                        (
                            "TARGET_MEMBER_SLOT",
                            {**choice_metadata, "reason": "position_change", "step": "dest", "source": area},
                        ),
                    )
                elif step == "dest":
                    src = params.get("source")
                    if src is not None and src != area:
                        self._move_member(p, src, area)
            elif params.get("effect") == "return_to_hand":
                move_stage_card(self, p, area, "hand")
            elif params.get("effect") == "discard_member":
                move_stage_card(self, p, area, "discard")
            elif params.get("effect") == "remove_member":
                move_stage_card(self, p, area, "removed")
            elif params.get("effect") == "return_to_deck":
                move_stage_card(self, p, area, "deck")
            elif params.get("effect") == "return_to_success":
                move_stage_card(self, p, area, "success")
            elif params.get("effect") == "return_to_discard":
                move_stage_card(self, p, area, "discard")
            elif params.get("effect") == "return_to_removed":
                move_stage_card(self, p, area, "removed")

    elif choice_type == "DISCARD_SELECT":
        idx = action - 500
        if 0 <= idx < len(p.hand):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            cid = p.hand.pop(idx)
            if idx < len(p.hand_added_turn):
                p.hand_added_turn.pop(idx)
            p.discard.append(cid)

            if params.get("draw_on_discard") and params.get("count", 1) <= 1:
                self._draw_cards(p, params.get("total_count", 1))

            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("DISCARD_SELECT", params))

    elif choice_type == "MODAL":
        opt = action - 570
        opts = params.get("options", [])
        if 0 <= opt < len(opts):
            if opt == 0:
                self.pending_choices.insert(
                    0, ("TARGET_HAND", {**choice_metadata, "effect": "discard", "player": "active"})
                )
            elif opt == 1:
                self._draw_cards(p, 1)
                self._draw_cards(opp, 1)
            elif opt == 2:
                self.pending_choices.append(("CHOOSE_FORMATION", {**choice_metadata}))

    elif choice_type == "TARGET_OPPONENT_MEMBER":
        area = action - 600
        if 0 <= area < 3 and opp.stage[area] >= 0 and params.get("effect") == "tap":
            opp.tapped_members[area] = True
            opp.members_tapped_by_opponent_this_turn.add(opp.stage[area])

    elif choice_type == "SELECT_MODE":
        opt = action - 570
        bytecodes = params.get("options_bytecode")
        if bytecodes and 0 <= opt < len(bytecodes):
            self.pending_effects.insert(0, bytecodes[opt])
            return

        opts = params.get("options", [])
        if 0 <= opt < len(opts):
            source_id = params.get("source_card_id", -1)
            opt_effects = opts[opt]
            total = len(opt_effects)
            for i, eff in enumerate(reversed(opt_effects)):
                self.pending_effects.insert(0, ResolvingEffect(copy.copy(eff), source_id, total - i, total))

    elif choice_type == "SELECT_FROM_LIST":
        cards = params.get("cards", [])
        idx = action - 600
        target_player_id = params.get("target_player_id", p.player_id)
        tp = self.players[target_player_id]

        if action == 0 and params.get("is_optional", False):
            reason = params.get("reason")
            if reason == "look_and_reorder":
                if self.looked_cards:
                    for c in self.looked_cards:
                        p.discard.append(c)
                    self.looked_cards = []

                if params.get("reorder") and hasattr(self, "_reorder_staged_cards") and self._reorder_staged_cards:
                    self.pending_choices.insert(
                        0,
                        (
                            "SELECT_ORDER",
                            {
                                "cards": self._reorder_staged_cards.copy(),
                                "ordered": [],
                                "position": "top",
                                "player_id": p.player_id,
                            },
                        ),
                    )
                    self._reorder_staged_cards = []
                elif hasattr(self, "_reorder_staged_cards") and self._reorder_staged_cards:
                    for c in reversed(self._reorder_staged_cards):
                        p.main_deck.insert(0, c)
                    self._reorder_staged_cards = []
                return

            if reason == "look_and_choose":
                if self.looked_cards:
                    if params.get("destination") == "discard":
                        for c in reversed(self.looked_cards):
                            tp.main_deck.insert(0, c)
                    else:
                        tp.discard.extend(self.looked_cards)
                    self.looked_cards = []
            return

        if 0 <= idx < len(cards):
            sel = cards.pop(idx)

            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True

            reason = params.get("reason")
            if reason in ("look_and_choose", "search_deck"):
                dest = params.get("destination", params.get("to", "hand"))
                if dest == "discard":
                    tp.discard.append(sel)
                else:
                    p.hand.append(sel)
                    p.hand_added_turn.append(self.turn_number)
                if reason == "look_and_choose" and sel in self.looked_cards:
                    self.looked_cards.remove(sel)
            elif reason == "look_and_reorder":
                if not hasattr(self, "_reorder_staged_cards"):
                    self._reorder_staged_cards = []
                self._reorder_staged_cards.append(sel)
                if sel in self.looked_cards:
                    self.looked_cards.remove(sel)

                any_number = params.get("any_number", False)
                reorder = params.get("reorder", False)
                if any_number and cards:
                    self.pending_choices.insert(0, ("SELECT_FROM_LIST", {**params, "cards": cards}))
                    return

                if self.looked_cards:
                    for c in self.looked_cards:
                        p.discard.append(c)
                    self.looked_cards = []

                if reorder and self._reorder_staged_cards:
                    self.pending_choices.insert(
                        0,
                        (
                            "SELECT_ORDER",
                            {
                                "cards": self._reorder_staged_cards.copy(),
                                "ordered": [],
                                "position": "top",
                                "player_id": p.player_id,
                            },
                        ),
                    )
                    self._reorder_staged_cards = []
                elif self._reorder_staged_cards:
                    for c in reversed(self._reorder_staged_cards):
                        p.main_deck.insert(0, c)
                    self._reorder_staged_cards = []
                return

            current_count = int(params.get("choose_count", params.get("count", 1)))
            rem_cards = cards
            if sel in rem_cards:
                rem_cards.remove(sel)

            looping = current_count > 1 and rem_cards
            if self.looked_cards and not looping:
                if reason == "look_and_choose":
                    if params.get("destination") == "discard":
                        for c in reversed(rem_cards):
                            tp.main_deck.insert(0, c)
                    else:
                        tp.discard.extend(rem_cards)
                self.looked_cards = []

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
                    params["choose_count"] = (
                        str(current_count - 1) if isinstance(params["choose_count"], str) else current_count - 1
                    )
                params["count"] = current_count - 1
                params["cards"] = rem_cards
                self.pending_choices.insert(0, ("SELECT_FROM_LIST", params))

    elif choice_type == "SELECT_FROM_DISCARD":
        cards = params.get("cards", [])
        idx = action - 660
        if 0 <= idx < len(cards):
            sel = int(cards[idx])
            if sel in p.discard:
                p.discard.remove(sel)
                dest = params.get("destination", "hand")
                if dest == "hand":
                    p.hand.append(sel)
                    p.hand_added_turn.append(self.turn_number)
                elif dest == "stage":
                    area = next((i for i in range(3) if p.stage[i] < 0), -1)
                    if area >= 0:
                        p.stage[area] = sel
                    else:
                        p.hand.append(sel)
                        p.hand_added_turn.append(self.turn_number)
                if params.get("count", 1) > 1:
                    rem = [c for c in cards if int(c) != sel and int(c) in p.discard]
                    if rem:
                        params.update({"cards": rem, "count": params["count"] - 1})
                        self.pending_choices.insert(0, ("SELECT_FROM_DISCARD", params))

    elif choice_type == "CHOOSE_FORMATION":
        mems = [(i, cid) for i, cid in enumerate(p.stage) if cid >= 0]
        if mems:
            self.pending_choices.append(
                (
                    "SELECT_FORMATION_SLOT",
                    {**choice_metadata, "slot_index": 0, "available_members": mems, "new_stage": [-1, -1, -1]},
                )
            )

    elif choice_type == "SELECT_FORMATION_SLOT":
        slot = params.get("slot_index", 0)
        avail = params.get("available_members", [])
        nstage = params.get("new_stage", [-1, -1, -1])
        idx = action - 700
        if 0 <= idx < len(avail):
            sel = avail.pop(idx)
            nstage[slot] = sel[1]
            if slot + 1 < 3 and avail:
                self.pending_choices.insert(
                    0,
                    (
                        "SELECT_FORMATION_SLOT",
                        {
                            **choice_metadata,
                            "slot_index": slot + 1,
                            "available_members": avail,
                            "new_stage": nstage,
                        },
                    ),
                )
            else:
                for k in range(slot + 1, 3):
                    nstage[k] = -1
                np.copyto(p.stage, nstage)

    elif choice_type == "COLOR_SELECT":
        color_idx = action - 580
        if 0 <= color_idx < 6:
            for i, pe in enumerate(self.pending_effects):
                eff = pe.effect if hasattr(pe, "effect") else pe
                if eff.effect_type == EffectType.ADD_HEARTS and eff.params.get("color") == "choice":
                    new_params = eff.params.copy()
                    new_params["color"] = color_idx
                    new_eff = Effect(EffectType.ADD_HEARTS, eff.value, eff.target, new_params)
                    if hasattr(pe, "effect"):
                        pe.effect = new_eff
                    else:
                        self.pending_effects[i] = new_eff
                    break

    elif choice_type == "SELECT_SWAP_SOURCE":
        idx = action - 600
        if 0 <= idx < len(params.get("cards", [])):
            self.pending_choices.insert(0, ("SELECT_SWAP_TARGET", {"card_to_hand": params["cards"][idx]}))

    elif choice_type == "SELECT_SWAP_TARGET":
        idx = action - 500
        if 0 <= idx < len(p.hand):
            clive = p.hand[idx]
            chand = params.get("card_to_hand")
            if chand in p.success_lives:
                p.success_lives.remove(chand)
                p.hand.append(chand)
                p.hand_added_turn.append(self.turn_number)
            if clive in p.hand:
                hidx = p.hand.index(clive)
                if hidx < len(p.hand_added_turn):
                    p.hand_added_turn.pop(hidx)
                p.hand.remove(clive)
                p.success_lives.append(clive)

    elif choice_type == "SELECT_SUCCESS_LIVE":
        print(f"DEBUG: SELECT_SUCCESS_LIVE resolution. Action: {action}")
        idx = action - 600
        cards = params.get("cards", [])
        print(f"DEBUG: cards in params: {cards}, calculated idx: {idx}")
        if 0 <= idx < len(cards):
            sel = cards[idx]
            tplayer = self.players[params.get("player_id", 0)]
            print(f"DEBUG: card selected: {sel}, player {tplayer.player_id}, passed_lives: {tplayer.passed_lives}")
            if sel in tplayer.passed_lives:
                tplayer.success_lives.append(sel)
                tplayer.passed_lives.remove(sel)
                print(f"DEBUG: card moved. success_lives now: {tplayer.success_lives}")
                if tplayer.passed_lives:
                    if hasattr(self, "log_rule"):
                        self.log_rule(
                            "Rule 8.4",
                            f"Player {tplayer.player_id} discarded other successful lives: {len(tplayer.passed_lives)} cards",
                        )
                    tplayer.discard.extend(tplayer.passed_lives)
                    tplayer.passed_lives = []
                print(f"DEBUG: passed_lives cleared: {tplayer.passed_lives}")
            else:
                print(f"DEBUG: card {sel} NOT found in passed_lives")
        else:
            print(f"DEBUG: idx {idx} out of range for cards")

    elif choice_type == "CONTINUE_LIVE_RESULT":
        if hasattr(self, "_finish_live_result"):
            self._finish_live_result()
        return

    elif choice_type == "CHOOSE_TRIGGER":
        tidx = action - 590
        ids = params.get("indices", [])
        if 0 <= tidx < len(ids):
            pid, ab, ctx = self.triggered_abilities.pop(ids[tidx])
            self._play_automatic_ability(pid, ab, ctx)

    elif choice_type == "SELECT_ORDER":
        idx = action - 700
        cards = params["cards"]
        if 0 <= idx < len(cards):
            params["ordered"].append(cards.pop(idx))
            if cards:
                self.pending_choices.insert(0, ("SELECT_ORDER", params))
            elif params["position"] == "top":
                for c in reversed(params["ordered"]):
                    p.main_deck.insert(0, c)
            else:
                p.main_deck.extend(params["ordered"])

    elif choice_type == "MODAL_CHOICE":
        pass

    if is_cost_payment and self.pending_activation:
        if cost_paid:
            pa = self.pending_activation
            ability = pa["ability"]
            ctx = pa["context"]
            abi_key = pa["abi_key"]

            paid_index = params.get("cost_index", -1)
            all_costs_paid = True
            if paid_index >= 0 and paid_index + 1 < len(ability.costs):
                p = self.active_player
                area = ctx.get("area", -1)
                if not self._pay_costs(p, ability.costs, source_area=area, start_index=paid_index + 1):
                    all_costs_paid = False

            if all_costs_paid:
                cid = ctx.get("source_card_id", ctx.get("card_id", -1))
                total = len(ability.effects)
                for i, phase_effect in enumerate(reversed(ability.effects)):
                    step = total - i
                    eff_copy = copy.copy(phase_effect)
                    self.pending_effects.insert(0, ResolvingEffect(eff_copy, cid, step, total))

                p = self.active_player
                if ability.is_once_per_turn:
                    p.used_abilities.add(abi_key)

                self.pending_activation = None

                while self.pending_effects and not self.pending_choices:
                    self._resolve_pending_effect(0, context=ctx)
        elif not self.pending_choices or self.pending_choices[0][1].get("reason") != "cost":
            self.pending_activation = None

    if self.pending_effects and not self.pending_choices:
        self._resolve_pending_effect(0, context=params)

    if not self.pending_choices and not self.pending_effects and self.phase == Phase.LIVE_RESULT:
        if hasattr(self, "_do_live_result"):
            self._do_live_result()


__all__ = ["handle_choice"]
