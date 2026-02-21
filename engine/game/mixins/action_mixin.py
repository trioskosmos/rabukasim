import random
from typing import TYPE_CHECKING, Any

import numpy as np

from engine.game.enums import Phase
from engine.models.ability import EffectType, TriggerType

if TYPE_CHECKING:
    pass


class ActionMixin:
    """
    Mixin for GameState that handles player actions and core mechanics.
    """

    def _resolve_deck_refresh(self, player: Any) -> None:
        """Rule 10.2: If deck is empty, shuffle waiting room to make new deck."""
        if not player.main_deck and player.discard:
            # Shuffle discard into deck
            player.main_deck = list(player.discard)
            player.discard = []
            random.shuffle(player.main_deck)
            player.deck_refreshed_this_turn = True
            if hasattr(self, "log_rule"):
                self.log_rule(
                    "Rule 10.2",
                    f"Player {player.player_id} Refreshed Deck from Discard ({len(player.main_deck)} cards).",
                )

    def _draw_cards(self, player: Any, count: int) -> None:
        for _ in range(count):
            if hasattr(self, "_process_rule_checks"):
                self._process_rule_checks()

            # Check for refresh before drawing
            if not player.main_deck:
                self._resolve_deck_refresh(player)

            if player.main_deck:
                player.hand.append(player.main_deck.pop(0))
                player.hand_added_turn.append(self.turn_number)
            else:
                # Deck still empty after attempt to refresh (Rule 10.2.1.2: If both empty, cannot draw)
                pass

            if hasattr(self, "_process_rule_checks"):
                self._process_rule_checks()

    def _play_member(self, hand_idx: int, area_idx: int) -> None:
        p = self.active_player
        if "placement" in p.restrictions:
            return
        card_id = p.hand.pop(hand_idx)
        if hand_idx < len(p.hand_added_turn):
            added_turn = p.hand_added_turn.pop(hand_idx)
        else:
            # Fallback if list is desynced (shouldn't happen but prevented crash)
            added_turn = 0

        # Safety check: verify card exists in database before accessing
        card_id_int = int(card_id)
        if card_id_int not in self.member_db:
            # Put the card back in hand and return to prevent crash
            p.hand.insert(hand_idx, card_id)
            p.hand_added_turn.insert(hand_idx, added_turn if hand_idx < len(p.hand_added_turn) else 0)
            return

        card = self.member_db[card_id_int]
        if hasattr(self, "log_rule"):
            self.log_rule("Rule 7.7.2.2", f"Player {p.player_id} plays {card.name} to Slot {area_idx}.")
        # Calculate slot-specific cost reduction
        slot_reduction = sum(
            ce["effect"].value
            for ce in p.continuous_effects
            if ce["effect"].effect_type == EffectType.REDUCE_COST and (ce.get("target_slot", -1) in (-1, area_idx))
        )
        base_cost = max(0, card.cost - slot_reduction)
        cost = base_cost

        is_baton = p.stage[area_idx] >= 0
        if is_baton:
            extra_baton = sum(
                ce["effect"].value
                for ce in p.continuous_effects
                if ce["effect"].effect_type == EffectType.BATON_TOUCH_MOD
            )
            effective_baton_limit = p.baton_touch_limit + extra_baton

            if p.baton_touch_count >= effective_baton_limit:
                # Should be caught by get_legal_actions, but safety first
                p.hand.insert(hand_idx, card_id)
                p.hand_added_turn.insert(hand_idx, added_turn)
                return

            prev_card_id = int(p.stage[area_idx])
            if prev_card_id in self.member_db:
                prev_card = self.member_db[prev_card_id]
            else:
                prev_card = None

            if prev_card:
                if hasattr(self, "log_rule"):
                    self.log_rule("Rule 9.6.2.3.2", f"Baton Touch! Cost reduced by {prev_card.cost}.")
                cost = max(0, cost - prev_card.cost)
                p.baton_touch_count += 1

                # Rule 9.9.1.2: Check for ON_LEAVES triggers before/as card leaves stage
                for ability in prev_card.abilities:
                    trig = getattr(ability, "trigger", "NO_TRIGGER")
                    if trig == TriggerType.ON_LEAVES:
                        self.triggered_abilities.append(
                            (
                                p.player_id,
                                ability,
                                {"area": area_idx, "card_id": p.stage[area_idx], "from_zone": "stage"},
                            )
                        )
            else:
                # If prev_card is None, just increment baton touch count without cost adjustment
                p.baton_touch_count += 1

            p.discard.append(p.stage[area_idx])
            if p.stage_energy_count[area_idx] > 0:
                p.energy_deck.extend(p.stage_energy[area_idx])
                p.clear_stage_energy(area_idx)
        untapped = [i for i, tapped in enumerate(p.tapped_energy) if not tapped]
        if len(untapped) < cost:
            p.hand.insert(hand_idx, card_id)
            p.hand_added_turn.insert(hand_idx, added_turn)
            return
        for i in range(cost):
            p.tapped_energy[untapped[i]] = True
        p.stage[area_idx] = card_id
        self.prev_cid = prev_card_id if "prev_card_id" in locals() else -1
        p.members_played_this_turn[area_idx] = True  # Rule 9.6.2.1.2.1: Cannot play into this slot again this turn
        for ability in card.abilities:
            if ability.trigger == TriggerType.ON_PLAY:
                if hasattr(self, "log_rule"):
                    self.log_rule("Rule 11.3", f"Triggering [登場] (On Play) abilities for {card.name}.")
                # print(f"DEBUG: Queuing ON_PLAY trigger for {card.name}")
                self.triggered_abilities.append((p.player_id, ability, {"area": area_idx, "card_id": card_id}))
        if hasattr(self, "_check_remote_triggers"):
            self._check_remote_triggers(TriggerType.ON_PLAY, {"card_id": card_id, "area": area_idx})

        if hasattr(self, "_process_rule_checks"):
            self._process_rule_checks()

    def _activate_member_ability(self, area: int) -> None:
        p = self.active_player
        card_id = int(p.stage[area])
        if card_id < 0 or card_id not in self.member_db:
            return
        member = self.member_db[card_id]
        ability = None
        ability_idx = -1
        for abi_idx, ab in enumerate(member.abilities):
            if ab.trigger == TriggerType.ACTIVATED:
                abi_key = f"{card_id}-{abi_idx}"
                if ab.is_once_per_turn and abi_key in p.used_abilities:
                    continue
                ability = ab
                ability_idx = abi_idx
                break
        if not ability:
            return

        if hasattr(self, "log_rule"):
            self.log_rule("Rule 7.7.2.1", f"Player {p.player_id} activates ability of {member.name} (Slot {area}).")

        # Set resolution context for metadata tracking
        self.current_resolving_ability = ability
        self.current_resolving_member = member.name
        self.current_resolving_member_id = card_id

        if not self._pay_costs(p, ability.costs, source_area=area):
            # Defer execution until cost paid (via choice)
            abi_key = f"{card_id}-{ability_idx}"
            self.pending_activation = {
                "ability": ability,
                "context": {"area": area, "card_id": card_id, "source_card_id": card_id},
                "abi_key": abi_key,
            }
            return
        total = len(ability.effects)
        from engine.models.ability import ResolvingEffect

        for i, effect in enumerate(reversed(ability.effects)):
            step = total - i
            self.pending_effects.insert(0, ResolvingEffect(effect, card_id, step, total))

        if ability.is_once_per_turn:
            p.used_abilities.add(f"{card_id}-{ability_idx}")
        while self.pending_effects and not self.pending_choices:
            self._resolve_pending_effect(0, context={"area": area, "card_id": card_id, "source_card_id": card_id})

    def _execute_mulligan(self) -> None:
        p = self.active_player
        if hasattr(self, "log_rule"):
            count = len(p.mulligan_selection) if hasattr(p, "mulligan_selection") else 0
            self.log_rule("Rule 6.2.1.6", f"Player {p.player_id} finished mulligan ({count} cards).")
        if hasattr(p, "mulligan_selection") and p.mulligan_selection:
            cards_to_return = []
            for idx in sorted(p.mulligan_selection, reverse=True):
                if idx < len(p.hand):
                    cards_to_return.append(p.hand.pop(idx))
                    if idx < len(p.hand_added_turn):
                        p.hand_added_turn.pop(idx)
            for _ in range(len(cards_to_return)):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop(0))
                    p.hand_added_turn.append(self.turn_number)
            p.main_deck.extend(cards_to_return)
            random.shuffle(p.main_deck)

        if hasattr(p, "mulligan_selection"):
            p.mulligan_selection.clear()

        # Phase transition: P1 -> P2 -> ACTIVE
        if self.phase == Phase.MULLIGAN_P1:
            self.current_player = 1 - self.first_player
            self.phase = Phase.MULLIGAN_P2
        else:
            self.current_player = self.first_player
            self.phase = Phase.ACTIVE

    def _check_hearts_meet_requirement(self, have: np.ndarray, need: np.ndarray) -> bool:
        """
        Check if 'have' hearts satisfy 'need' requirements.
        have/need: shape (7,) [Pink, Green, Yellow, Purple, Red, Blue, Any/Wildcard]
        index 6 in 'have' is Wildcard (can be any color).
        index 6 in 'need' is 'Any' requirement (can be satisfied by any color).
        """
        # 1. Check specific color requirements (0-5)
        # Calculate deficit for each color
        deficits = np.maximum(0, need[:6] - have[:6])
        total_deficit = np.sum(deficits)

        # Check if we have enough Wildcards to cover the deficit
        wildcards_have = have[6] if len(have) > 6 else 0
        if wildcards_have < total_deficit:
            return False

        # 2. Check 'Any' requirement (index 6)
        any_need = need[6] if len(need) > 6 else 0
        if any_need <= 0:
            return True

        # Remaining Wildcards after covering deficit
        remaining_wildcards = wildcards_have - total_deficit

        # Surplus specific hearts (those not used for specific requirements)
        surplus_specific = np.sum(np.maximum(0, have[:6] - need[:6]))

        total_available_for_any = remaining_wildcards + surplus_specific

        return total_available_for_any >= any_need

    def _consume_hearts(self, have: np.ndarray, need: np.ndarray) -> None:
        """
        Consume 'need' from 'have' in-place.
        Assumes _check_hearts_meet_requirement returned True.
        """
        # 1. Consume for specific requirements
        for i in range(6):
            n = need[i] if i < len(need) else 0
            if n > 0:
                # Use specific color first
                take_specific = min(have[i], n)
                have[i] -= take_specific
                remaining_need = n - take_specific

                # Use Wildcards for remainder
                if remaining_need > 0 and len(have) > 6:
                    take_wild = min(have[6], remaining_need)
                    have[6] -= take_wild

        # 2. Consume for 'Any' requirement
        any_need = need[6] if len(need) > 6 else 0
        if any_need > 0:
            # First consume surplus specific colors
            for i in range(6):
                if any_need <= 0:
                    break
                if have[i] > 0:
                    take = min(have[i], any_need)
                    have[i] -= take
                    any_need -= take

            # Then consume Wildcards
            if any_need > 0 and len(have) > 6:
                take = min(have[6], any_need)
                have[6] -= take

    def _set_live_card(self, hand_idx: int) -> None:
        """Set a card face-down in live zone"""
        p = self.active_player
        if hand_idx < 0 or hand_idx >= len(p.hand) or len(p.live_zone) >= 3:
            return

        card_id = p.hand[hand_idx]  # Look before pop for logging context
        from engine.game.state_utils import get_base_id

        base_id = get_base_id(card_id)

        if base_id in self.live_db:
            card_desc = f"{self.live_db[base_id].name} ({self.live_db[base_id].card_no})"
        elif base_id in self.member_db:
            card_desc = f"手札[{hand_idx}] ({self.member_db[base_id].card_no})"
        else:
            card_desc = f"Card #{card_id}"

        if hasattr(self, "log_rule"):
            self.log_rule("Rule 8.2.2", f"Player {p.player_id} sets {card_desc} to Live Zone.")

        p.hand.pop(hand_idx)
        if hand_idx < len(p.hand_added_turn):
            p.hand_added_turn.pop(hand_idx)
        p.live_zone.append(card_id)
        p.live_zone_revealed.append(False)
        # Rule 8.2.2 modification: Draw happens at end of Live Set phase, not immediately
        # self._draw_cards(p, 1)
        p.live_cards_set_this_turn += 1

    def _execute_action(self, action: int) -> None:
        """Internal: execute action on this state (mutates self)"""
        p = self.active_player
        if self.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            if action == 0:
                self._execute_mulligan()
            elif 300 <= action <= 359:
                card_idx = action - 300
                if card_idx < len(p.hand):
                    if not hasattr(p, "mulligan_selection"):
                        p.mulligan_selection = set()
                    if card_idx in p.mulligan_selection:
                        p.mulligan_selection.remove(card_idx)
                    else:
                        p.mulligan_selection.add(card_idx)
            return

        if getattr(self, "pending_choices", []):
            if action == 0:
                choice_type, params = self.pending_choices[0]
                if choice_type == "CONTINUE_LIVE_RESULT":
                    self.pending_choices.pop(0)
                    self._finish_live_result()
                    return
                if choice_type.startswith("CONTINUE"):
                    self.pending_choices.pop(0)
                    return
                if True:  # Handle action 0 as cancel/fail for both optional and mandatory (if forced)
                    self.pending_choices.pop(0)

                    # If look_and_choose declined, move looked cards to discard if on_fail is set
                    if params.get("reason") == "look_and_choose" and getattr(self, "looked_cards", []):
                        if params.get("on_fail") == "discard":
                            p.discard.extend(self.looked_cards)
                        self.looked_cards = []

                    if params.get("reason") in ("cost", "effect"):
                        self.pending_effects.clear()
                        # If we had chained choices (rare for cost), they are now invalid ideally
                        # But pending_choices might contain next steps?
                        # For "cost", the whole ability aborts, so safe to clear.
                        self.pending_choices.clear()
                        # Clear resolution state
                        self.looked_cards = []
                        self.current_resolving_member = None
                        self.current_resolving_member_id = -1
                    return
            if action >= 500:
                self._handle_choice(action)
                return

        if self.phase == Phase.ACTIVE:
            self._do_active_phase()
        elif self.phase == Phase.ENERGY:
            self._do_energy_phase()
        elif self.phase == Phase.DRAW:
            self._do_draw_phase()
        elif self.phase == Phase.MAIN:
            if action == 0:
                self._end_main_phase()
            elif 1 <= action <= 180:
                adj = action - 1
                self._play_member(adj // 3, adj % 3)
            elif 200 <= action <= 202:
                self._activate_member_ability(action - 200)
        elif self.phase == Phase.LIVE_SET:
            if action == 0:
                self._end_live_set()
            elif 400 <= action <= 459:
                self._set_live_card(action - 400)
        elif self.phase == Phase.PERFORMANCE_P1:
            if 900 <= action <= 902:
                self._do_performance(0, live_idx=action - 900)
            else:
                self._do_performance(0)
        elif self.phase == Phase.PERFORMANCE_P2:
            if 900 <= action <= 902:
                self._do_performance(1, live_idx=action - 900)
            else:
                self._do_performance(1)
        elif self.phase == Phase.LIVE_RESULT:
            self._do_live_result()
