from __future__ import annotations

import copy
import random
from typing import Any, Dict

import numpy as np

from engine.models.ability import ConditionType, Effect, EffectType, TargetType
from engine.models.enums import Group, Unit
from engine.models.opcodes import Opcode


def resolve_effect_opcode(game: Any, opcode: Opcode, seg: Any, context: Dict[str, Any]) -> None:
    self = game
    """Execute a single quadruple from bytecode."""
    p = self.active_player
    opp_idx = 1 - p.player_id
    v = seg[1]
    a = seg[2]
    s_packed = seg[3]

    # Decode dynamic flag (Bit 6 of 'a')
    real_v = v
    if (a & 0x40) != 0:
        cond_type = ConditionType(v)
        if cond_type == ConditionType.COUNT_STAGE:
            raw_count = len([c for c in p.stage if c >= 0])
        elif cond_type == ConditionType.COUNT_HAND:
            raw_count = len(p.hand)
        elif cond_type == ConditionType.COUNT_DISCARD:
            raw_count = len(p.discard)
        elif cond_type == ConditionType.COUNT_ENERGY:
            raw_count = len(p.energy_zone)
        elif cond_type == ConditionType.COUNT_SUCCESS_LIVE:
            raw_count = len(p.success_lives)
        elif cond_type == ConditionType.COUNT_LIVE_ZONE:
            raw_count = len(p.live_zone)
        else:
            raw_count = 0

        # Decode scaling flag (Bit 5 of 'a')
        if (a & 0x20) != 0:
            # PER_X scaling: real_v = target_v * (raw_count // scaling_factor)
            scaling_factor = s_packed >> 4  # Top 4 bits of s_packed store scaling factor
            if scaling_factor > 0:
                real_v = (s_packed & 0x0F) * (raw_count // scaling_factor)
            else:
                real_v = 0
        else:
            real_v = raw_count

    # Decode slot/comparison
    s = s_packed & 0x0F

    # Condition Check Opcodes (Return/Jump logic usually handled in loop, but we need 'cond' state)
    # In this Python version, _resolve_pending_effect's loop needs to handle cond.
    # But for now, we only trigger effects.

    if self.verbose:
        print(f"DEBUG_OP: {opcode.name} v={v} a={a} s={s}")

    if opcode == Opcode.DRAW:
        self._draw_cards(p, real_v)
    elif opcode == Opcode.ADD_BLADES:
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.ADD_BLADES, real_v, TargetType.SELF),
                "target_slot": s if s < 3 else -1,
                "expiry": "TURN_END",
            }
        )
    elif opcode == Opcode.ADD_HEARTS:
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.ADD_HEARTS, real_v, TargetType.SELF, {"color": a & 0x3F}),
                "expiry": "TURN_END",
            }
        )
    elif opcode == Opcode.GRANT_ABILITY:
        # Granting an ability (Rule 1.3.1)
        # a: attribute of granted ability (trigger type)
        # v: Index into member_db if external, or reference to current
        # For Sumire: It's usually a predefined ID or a special payload.
        # In V2 compiler, GRANT_ABILITY often carries a whole Ability object or pre-compiled bytecode.
        # But here we handle the "Legacy" or "Simple" case for Starters.

        # If it's "SELF" (s == 0), we apply to current member.
        source_id = context.get("source_card_id", -1)
        target_p = p

        # In Sumire's case, the pseudocode is:
        # EFFECT: GRANT_ABILITY(SELF, TRIGGER="CONSTANT", CONDITION="IS_ON_STAGE", EFFECT="BOOST_SCORE(1)")
        # This is compiled into Opcode 60.

        # For simplicity in this engine version, we convert it to a Continuous Effect
        # that mimics the granted ability.
        target_slot = context.get("area", -1)
        if target_slot == -1 and source_id != -1:
            # Find where source_id is on stage
            for i, cid in enumerate(p.stage):
                if cid == source_id:
                    target_slot = i
                    break

        if target_slot != -1:
            # Create a pseudo-effect that matches the granted ability
            # Sumire grants BOOST_SCORE(1) while on stage.
            # In basic engine terms, this is just a Score Buff continuous effect.
            p.continuous_effects.append(
                {
                    "source_card_id": source_id,
                    "effect": Effect(EffectType.BOOST_SCORE, real_v, TargetType.SELF),
                    "target_slot": target_slot,
                    "expiry": "TURN_END",  # Usually until end of turn or permanent?
                    # Starter Sumire is "This turn".
                }
            )

    elif opcode == Opcode.LOOK_DECK:
        # Reveal top V cards (Target awareness)
        target_tp = self.players[opp_idx] if s == 2 else p  # s=2 is OPPONENT in TargetType
        if self.verbose:
            print(f"DEBUG: LOOK_DECK Target={target_tp.player_id} DeckLen={len(target_tp.main_deck)}")
        if not target_tp.main_deck:
            self._resolve_deck_refresh(target_tp)
        self.looked_cards = []
        for _ in range(v):
            if target_tp.main_deck:
                self.looked_cards.append(target_tp.main_deck.pop(0))
        if self.verbose:
            print(f"DEBUG: LOOK_DECK Result={self.looked_cards}")
    elif opcode == Opcode.LOOK_AND_CHOOSE:
        # Trigger SLIST choice
        if self.looked_cards:
            dest = "discard" if (a & 0x0F) == 1 else "hand"
            target_pid = opp_idx if s == 2 else p.player_id
            self.pending_choices.append(
                (
                    "SELECT_FROM_LIST",
                    {
                        "cards": self.looked_cards,
                        "count": real_v,
                        "reason": "look_and_choose",
                        "destination": dest,
                        "target_player_id": target_pid,
                        "player_id": p.player_id,
                        "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    },
                )
            )

    elif opcode == Opcode.TAP_OPPONENT:
        is_all = (a & 0x80) != 0
        requires_selection = (a & 0x20) != 0  # Bit 5 flag
        cost_max = v
        blades_max = a & 0x1F  # Mask out flags

        # Dynamic Resolution: If cost_max is 99, try to find context card cost
        if cost_max == 99:
            scid = context.get("source_card_id", context.get("card_id", -1))
            if scid != -1 and scid in self.member_db:
                cost_max = self.member_db[scid].cost

        def passes_filter(slot_id):
            cid = opp.stage[slot_id]
            if cid < 0:
                return False
            card = self.member_db[int(cid)]
            # Cost check
            if cost_max != 99 and card.cost > cost_max:
                return False
            # Blades check
            if blades_max != 99 and card.total_blades > blades_max:
                return False
            return True

        if is_all:
            for i in range(3):
                if passes_filter(i):
                    opp.tapped_members[i] = True
                    opp.members_tapped_by_opponent_this_turn.add(opp.stage[i])
        else:
            # Check for interactive selection
            if requires_selection or (s == 2 and v == 1):  # s=2 is OPPONENT, v=1 count
                choice = context.get("choice_index", -1)
                if choice == -1:
                    # Pause for selection
                    # Create a pending choice
                    # Valid targets
                    valid_slots = [i for i in range(3) if passes_filter(i) and not opp.tapped_members[i]]

                    if valid_slots:
                        self.pending_choices.append(
                            (
                                "TARGET_OPPONENT_MEMBER",
                                {
                                    "player_id": self.current_player,
                                    "valid_slots": valid_slots,
                                    "effect": "tap_opponent",
                                    "pending_context": context,  # Store context to resume
                                    # "resume_opcode": opcode, ... (Python engine handles resume differently usually)
                                    # Using standard pending_choices format
                                },
                            )
                        )
                        # In Python engine, pending_choices usually halts execution flow implicitly or explicitly?
                        # resolve_bytecode doesn't return status.
                        # We might need to ensure this halts.
                        # But standard python engine relies on pending_choices check in outer loop.
                        pass
                else:
                    # Apply to chosen slot
                    if 0 <= choice < 3 and passes_filter(choice):
                        opp.tapped_members[choice] = True
                        opp.members_tapped_by_opponent_this_turn.add(opp.stage[choice])
            elif s < 3:  # Fallback for directed target (if s is actually a fixed slot index)
                # Note: s=2 (Right Slot) vs s=2 (Opponent TargetType) is ambiguous without flags.
                # This is why we added the flag.
                # If flag is NOT set, and s < 3, assume fixed slot?
                # But previously s=2 tapped right slot.
                if passes_filter(s):
                    opp.tapped_members[s] = True
                    opp.members_tapped_by_opponent_this_turn.add(opp.stage[s])
    elif opcode == Opcode.ACTIVATE_MEMBER:
        if s < 3:
            p.tapped_members[s] = False
    elif opcode == Opcode.REVEAL_CARDS:
        # s=1 means reveal looking cards (usually for yel animation/trigger)
        pass
    elif opcode == Opcode.RECOVER_LIVE:
        # Trigger interactive selection instead of broken automatic recovery
        live_cards_in_discard = [cid for cid in p.discard if int(cid) in self.live_db]
        if live_cards_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        "source_card_id": context.get("source_card_id", -1),
                        "cards": live_cards_in_discard,
                        "count": real_v,
                        "filter": "live",
                        "effect": "return_to_hand",
                        "effect_description": "蝗槫庶縺吶ｋ繝ｩ繧､繝悶ｒ驕ｸ繧薙〒縺上□縺輔＞",
                    },
                )
            )
    elif opcode == Opcode.RECOVER_MEMBER:
        # Trigger interactive selection instead of broken automatic recovery
        member_cards_in_discard = [cid for cid in p.discard if int(cid) in self.member_db]
        if member_cards_in_discard:
            self.pending_choices.append(
                (
                    "SELECT_FROM_DISCARD",
                    {
                        "source_card_id": context.get("source_card_id", -1),
                        "cards": member_cards_in_discard,
                        "count": real_v,
                        "filter": "member",
                        "effect": "return_to_hand",
                        "effect_description": "蝗槫庶縺吶ｋ繝｡繝ｳ繝舌・繧帝∈繧薙〒縺上□縺輔＞",
                    },
                )
            )
    elif opcode == Opcode.SWAP_CARDS:
        # Discard v, then draw v
        for _ in range(v):
            if p.hand:
                cid = p.hand.pop(0)
                p.hand_added_turn.pop(0)
                p.discard.append(cid)
        self._draw_cards(p, v)
    elif opcode == Opcode.REDUCE_COST:
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.REDUCE_COST, v, TargetType.SELF),
                "target_slot": s if s < 3 else -1,
                "expiry": "TURN_END",
            }
        )
    elif opcode == Opcode.REDUCE_HEART_REQ:
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.REDUCE_HEART_REQ, v, TargetType.SELF),
                "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
            }
        )
    elif opcode == Opcode.BATON_TOUCH_MOD:
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.BATON_TOUCH_MOD, v, TargetType.SELF),
                "expiry": "TURN_END",
            }
        )
    elif opcode == Opcode.META_RULE:
        # Handle specific meta rules that have engine impact (cheer_mod, etc)
        rule_type = context.get("type", "")
        if rule_type == "cheer_mod":
            p.continuous_effects.append(
                {
                    "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                    "effect": Effect(EffectType.META_RULE, v, TargetType.SELF, {"type": "cheer_mod"}),
                    "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
                }
            )
        elif rule_type == "fragment_cleanup":
            pass  # Already handled by parser filter
        else:
            p.meta_rules.add(str(rule_type))
    elif opcode == Opcode.TRANSFORM_COLOR:
        target = context.get("target", "base_hearts")
        p.continuous_effects.append(
            {
                "source_card_id": context.get("source_card_id", context.get("card_id", -1)),
                "effect": Effect(EffectType.TRANSFORM_COLOR, v, TargetType.SELF, {"target": target, "color": a}),
                "expiry": "LIVE_END" if context.get("until") == "live_end" else "TURN_END",
            }
        )
    elif opcode == Opcode.PLAY_MEMBER_FROM_HAND:
        # v = count, a = source_attr (e.g. Group)
        # From hand is standard, but if context says discard:
        source_zone = context.get("from", "hand")
        self.pending_choices.append(
            (
                "TARGET_MEMBER_SLOT",
                {
                    **context,
                    "player_id": p.player_id,
                    "effect": "place_member",
                    "source_zone": source_zone,
                    "count": v,
                    "filter_group": a if a != 0 else None,
                },
            )
        )
    elif opcode == Opcode.FLAVOR_ACTION:
        # Trigger modal choice "What do you like?"
        self.pending_choices.append(
            (
                "MODAL_CHOICE",
                {
                    **context,
                    "player_id": opp_idx,
                    "title": "What do you like?",
                    "options": [
                        "Choco Mint",
                        "Strawberry Flavor",
                        "Cookies & Cream",
                        "You",
                        "Anything else",
                    ],
                    "reason": "flavor_action",
                },
            )
        )
    elif opcode == Opcode.ADD_TO_HAND:
        # v = count, a = source (0=looked, 1=discard, 2=deck)
        if a == 0 and self.looked_cards:
            for _ in range(v):
                if self.looked_cards:
                    cid = self.looked_cards.pop(0)
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
        elif a == 1:
            # Handled by RECOVER_LIVE/MEMBER usually, but for generic:
            for _ in range(v):
                if p.discard:
                    cid = p.discard.pop()
                    p.hand.append(cid)
                    p.hand_added_turn.append(self.turn_number)
        elif a == 2:
            self._draw_cards(p, v)
    elif opcode == Opcode.BOOST_SCORE:
        p.live_score_bonus += v
    elif opcode == Opcode.ENERGY_CHARGE:
        count = v
        for _ in range(count):
            if p.main_deck:
                cid = p.main_deck.pop(0)
                p.energy_zone.append(cid)
                p.tapped_energy[len(p.energy_zone) - 1] = False
            elif p.discard:
                self._resolve_deck_refresh(p)
                if p.main_deck:
                    cid = p.main_deck.pop(0)
                    p.energy_zone.append(cid)
                    p.tapped_energy[len(p.energy_zone) - 1] = False
    elif opcode == Opcode.MOVE_MEMBER:
        dest = context.get("target_slot", -1)
        if 0 <= s < 3 and 0 <= dest < 3:
            self._move_member(p, s, dest)
    elif opcode == Opcode.MOVE_TO_DISCARD:
        # v = count, a = source (1=deck_top, 2=hand, 3=energy), s = target_slot
        if a == 1:  # From Deck Top
            for _ in range(v):
                if not p.main_deck:
                    self._resolve_deck_refresh(p)
                if p.main_deck:
                    cid = p.main_deck.pop(0)
                    p.discard.append(cid)
        elif a == 2:  # From Hand
            for _ in range(v):
                if p.hand:
                    cid = p.hand.pop()
                    p.hand_added_turn.pop()
                    p.discard.append(cid)
        elif a == 3:  # From Energy
            for _ in range(v):
                if p.energy_zone:
                    cid = p.energy_zone.pop()
                    p.discard.append(cid)
        elif s == 0:  # Target SELF (Member on stage)
            scid = context.get("source_card_id", context.get("card_id", -1))
            for i in range(3):
                if p.stage[i] == scid:
                    p.stage[i] = -1
                    p.tapped_members[i] = False
                    p.discard.append(scid)
                    break
    elif opcode == Opcode.JUMP_IF_FALSE:
        # This requires a more complex loop in _resolve_pending_effect
        # For now, standard step() might not use jumps heavily in Python mode
        pass


__all__ = ["resolve_effect_opcode"]
