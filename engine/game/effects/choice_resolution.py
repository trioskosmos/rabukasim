from __future__ import annotations

import copy
from typing import Any

import numpy as np

from engine.game.effects.choice_actions import (
    handle_optional_select_from_list,
    resolve_select_from_discard_choice,
    resolve_select_from_list_choice,
    resolve_target_deck_choice,
    resolve_target_energy_deck_choice,
    resolve_target_energy_zone_choice,
    resolve_target_hand_choice,
    resolve_target_live_choice,
    resolve_target_member_choice,
    resolve_target_removed_choice,
    resolve_target_success_lives_choice,
)
from engine.game.effects.choices import (
    is_cost_payment_choice,
    normalize_choice_metadata,
    store_choice_answer,
)
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
    original_phase = None
    if getattr(self, "pending_activation", None):
        original_phase = self.pending_activation.get("context", {}).get("original_phase")
    if original_phase is None:
        original_phase = choice_metadata.get("original_phase")

    store_choice_answer(self, action)

    if choice_type == "TARGET_HAND":
        idx = action - 500
        if 0 <= idx < len(p.hand):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_hand_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_HAND", params))

    elif choice_type == "TARGET_LIVE":
        idx = action - 820
        if 0 <= idx < len(p.live_zone):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_live_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_LIVE", params))

    elif choice_type in ("SELECT_FROM_DISCARD", "TARGET_DISCARD"):
        idx = action - 660
        if 0 <= idx < len(params.get("cards", p.discard)):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_select_from_discard_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_DISCARD", params))

    elif choice_type in ("TARGET_DECK", "SELECT_FROM_LIST"):
        idx = action - 600
        if 0 <= idx < len(p.main_deck) or choice_type == "SELECT_FROM_LIST":
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_deck_choice(self, p, params, idx, choice_type)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_DECK", params))

    elif choice_type == "TARGET_REMOVED":
        idx = action - 850
        if 0 <= idx < len(self.removed_cards):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_removed_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_REMOVED", params))

    elif choice_type == "TARGET_SUCCESS_LIVES":
        idx = action - 760
        if 0 <= idx < len(p.success_lives):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_success_lives_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_SUCCESS_LIVES", params))

    elif choice_type == "TARGET_ENERGY_ZONE":
        idx = action - 830
        if 0 <= idx < len(p.energy_zone):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_energy_zone_choice(self, p, params, idx)
            if params.get("count", 1) > 1:
                params["count"] -= 1
                self.pending_choices.insert(0, ("TARGET_ENERGY_ZONE", params))

    elif choice_type == "TARGET_ENERGY_DECK":
        idx = action - 600
        if 0 <= idx < len(p.energy_deck):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_target_energy_deck_choice(self, p, params, idx)
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
            if cost_type == "place_energy_deck":
                energy_params = {
                    **choice_metadata,
                    "cards": p.energy_deck.copy(),
                    "reason": "cost",
                    "effect": "place_energy",
                    "is_optional": True,
                    "cost_index": params.get("cost_index", -1),
                    "count": amount,
                }
                self.pending_choices.append(("TARGET_ENERGY_DECK", energy_params))
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
            resolve_target_member_choice(self, p, params, area)

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
        if params.get("cost_type_name") == "SELECT_SELF_OR_DISCARD":
            if opt == 0:
                area = params.get("source_area", params.get("area", -1))
                if 0 <= area < 3:
                    p.tapped_members[area] = True
                cost_paid = True
            elif opt == 1:
                discard_params = {
                    **choice_metadata,
                    "reason": "cost",
                    "effect": "discard",
                    "is_optional": False,
                    "cost_index": params.get("cost_index", -1),
                    "count": 1,
                }
                self.pending_choices.append(("TARGET_HAND", discard_params))
                return False

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
        idx = action - 600
        if action == 0 and params.get("is_optional", False):
            if handle_optional_select_from_list(self, p, params):
                return

        if 0 <= idx < len(params.get("cards", [])):
            if params.get("reason") == "cost" and params.get("count", 1) <= 1:
                cost_paid = True
            resolve_select_from_list_choice(self, p, params, idx)

    elif choice_type == "SELECT_FROM_DISCARD":
        idx = action - 660
        if 0 <= idx < len(params.get("cards", [])):
            resolve_select_from_discard_choice(self, p, params, idx)

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

    if not self.pending_choices and not self.pending_effects and not self.pending_activation and original_phase is not None:
        self.phase = original_phase

    if self.pending_effects and not self.pending_choices:
        self._resolve_pending_effect(0, context=params)

    if not self.pending_choices and not self.pending_effects and self.phase == Phase.LIVE_RESULT:
        if hasattr(self, "_do_live_result"):
            self._do_live_result()


__all__ = ["handle_choice"]
