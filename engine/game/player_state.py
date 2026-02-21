from typing import Any, Dict, List

import numpy as np

from engine.game.state_utils import StateMixin
from engine.models.ability import Condition, ConditionType, EffectType, TargetType, TriggerType
from engine.models.card import MemberCard


class PlayerState(StateMixin):
    """
    Player state (Rule 3)
    Contains areas, zones, and tracking for a single player.
    """

    __slots__ = (
        "player_id",
        "hand",
        "main_deck",
        "energy_deck",
        "discard",
        "energy_zone",
        "success_lives",
        "live_zone",
        "live_zone_revealed",
        "stage",
        "stage_energy_vec",
        "stage_energy_count",
        "tapped_energy",
        "tapped_members",
        "members_played_this_turn",
        "mulligan_selection",
        "baton_touch_limit",
        "baton_touch_count",
        "negate_next_effect",
        "restrictions",
        "live_score_bonus",
        "passed_lives",
        "cannot_live",
        "used_abilities",
        "meta_rules",
        "continuous_effects",
        "continuous_effects_vec",
        "continuous_effects_ptr",
        "hand_buffer",
        "moved_members_this_turn",
        "hand_added_turn",
        "deck_refreshed_this_turn",
        "performance_abilities_processed",
        "rested_members",
        "revealed_hand",
        "yell_score_count",
        "fast_mode",
        "members_tapped_by_opponent_this_turn",
        "live_cards_set_this_turn",
        "live_success_triggered",
    )

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand: List[int] = []
        self.hand_added_turn: List[int] = []
        self.main_deck: List[int] = []
        self.energy_deck: List[int] = []
        self.discard: List[int] = []
        self.energy_zone: List[int] = []
        self.success_lives: List[int] = []
        self.live_zone: List[int] = []
        self.live_zone_revealed: List[bool] = []
        self.stage: np.ndarray = np.full(3, -1, dtype=np.int32)
        self.stage_energy_vec: np.ndarray = np.zeros((3, 32), dtype=np.int32)
        self.stage_energy_count: np.ndarray = np.zeros(3, dtype=np.int32)
        self.tapped_energy: np.ndarray = np.zeros(100, dtype=bool)
        self.tapped_members: np.ndarray = np.zeros(3, dtype=bool)
        self.members_played_this_turn: np.ndarray = np.zeros(3, dtype=bool)
        self.mulligan_selection: set = set()
        self.baton_touch_limit: int = 1
        self.baton_touch_count: int = 0
        self.negate_next_effect: bool = False
        self.restrictions: set[str] = set()
        self.live_score_bonus: int = 0
        self.passed_lives: List[int] = []
        self.cannot_live: bool = False
        self.used_abilities: set[str] = set()
        self.moved_members_this_turn: set[int] = set()
        self.continuous_effects: List[Dict[str, Any]] = []
        self.continuous_effects_vec: np.ndarray = np.zeros((32, 10), dtype=np.int32)
        self.continuous_effects_ptr: int = 0
        self.meta_rules: set[str] = set()
        self.fast_mode: bool = False
        self.hand_buffer: np.ndarray = np.zeros(100, dtype=np.int32)
        self.deck_refreshed_this_turn: bool = False
        self.performance_abilities_processed: bool = False
        self.rested_members: np.ndarray = np.zeros(3, dtype=bool)
        self.revealed_hand: bool = False
        self.yell_score_count: int = 0
        self.live_cards_set_this_turn: int = 0
        self.live_success_triggered: bool = False
        self.members_tapped_by_opponent_this_turn: set[int] = set()

    @property
    def score(self) -> int:
        """
        Game Score (Rule 1.2 / 8.4.7)
        - This is the number of cards in the success_lives zone.
        - Points are obtained during Rule 8.4 Live Judgment phase.
        - Only 1 success live card can be added per judgment turn.
        """
        return len(self.success_lives)

    @property
    def energy_count(self) -> int:
        return len(self.energy_zone)

    @energy_count.setter
    def energy_count(self, value: int):
        current = len(self.energy_zone)
        if value < current:
            # Assume cost payment: Move from Energy Zone to Discard
            diff = current - value
            for _ in range(diff):
                if self.energy_zone:
                    card_id = self.energy_zone.pop()
                    self.discard.append(card_id)
        elif value > current:
            # Cannot magically add empty energy without cards
            pass

    @property
    def stage_energy(self) -> List[List[int]]:
        """Legacy compatibility property. Returns a copy of the energy state."""
        res = []
        for i in range(3):
            count = self.stage_energy_count[i]
            res.append(list(self.stage_energy_vec[i, :count]))
        return res

    def add_stage_energy(self, slot_idx: int, card_id: int) -> None:
        """Add energy to a slot using flat arrays."""
        count = self.stage_energy_count[slot_idx]
        if count < 32:
            self.stage_energy_vec[slot_idx, count] = card_id
            self.stage_energy_count[slot_idx] = count + 1

    def clear_stage_energy(self, slot_idx: int) -> None:
        """Clear energy from a slot."""
        self.stage_energy_count[slot_idx] = 0

    def _reset(self, player_id: int) -> None:
        """Reset state for pool reuse."""
        self.player_id = player_id
        self.hand.clear()
        self.main_deck.clear()
        self.energy_deck.clear()
        self.discard.clear()
        self.energy_zone.clear()
        self.success_lives.clear()
        self.live_zone.clear()
        self.live_zone_revealed.clear()
        self.stage.fill(-1)
        self.stage_energy_vec.fill(0)
        self.stage_energy_count.fill(0)
        self.tapped_energy.fill(False)
        self.tapped_members.fill(False)
        self.members_played_this_turn.fill(False)
        self.mulligan_selection.clear()
        self.baton_touch_limit = 1
        self.baton_touch_count = 0
        self.negate_next_effect = False
        self.restrictions.clear()
        self.live_score_bonus = 0
        self.passed_lives.clear()
        self.cannot_live = False
        self.used_abilities.clear()
        self.continuous_effects.clear()
        self.continuous_effects_vec.fill(0)
        self.continuous_effects_ptr = 0
        self.meta_rules.clear()
        self.hand_added_turn.clear()
        self.deck_refreshed_this_turn = False
        self.performance_abilities_processed = False
        self.rested_members.fill(False)
        self.revealed_hand = False
        self.revealed_hand = False
        self.moved_members_this_turn.clear()
        self.members_tapped_by_opponent_this_turn.clear()
        self.live_cards_set_this_turn = 0
        self.live_success_triggered = False

    def copy_slots_to(self, target: "PlayerState") -> None:
        """Hardcoded field copy for maximum performance."""
        target.player_id = self.player_id
        target.hand = self.hand[:]
        target.hand_added_turn = self.hand_added_turn[:]
        target.main_deck = self.main_deck[:]
        target.energy_deck = self.energy_deck[:]
        target.discard = self.discard[:]
        target.energy_zone = self.energy_zone[:]
        target.success_lives = self.success_lives[:]
        target.live_zone = self.live_zone[:]
        target.live_zone_revealed = self.live_zone_revealed[:]
        target.baton_touch_limit = self.baton_touch_limit
        target.baton_touch_count = self.baton_touch_count
        target.negate_next_effect = self.negate_next_effect
        target.live_score_bonus = self.live_score_bonus
        target.cannot_live = self.cannot_live
        target.deck_refreshed_this_turn = self.deck_refreshed_this_turn
        target.performance_abilities_processed = self.performance_abilities_processed
        target.revealed_hand = self.revealed_hand
        target.continuous_effects_ptr = self.continuous_effects_ptr
        target.live_cards_set_this_turn = self.live_cards_set_this_turn
        target.live_success_triggered = self.live_success_triggered

    def copy(self) -> "PlayerState":
        new = PlayerState(self.player_id)
        self.copy_to(new)
        return new

    def copy_to(self, new: "PlayerState") -> None:
        # 1. Scalar/List fields
        self.copy_slots_to(new)
        # 2. NumPy arrays (memcpy speed)
        np.copyto(new.stage, self.stage)
        np.copyto(new.stage_energy_vec, self.stage_energy_vec)
        np.copyto(new.stage_energy_count, self.stage_energy_count)
        np.copyto(new.tapped_energy, self.tapped_energy)
        np.copyto(new.tapped_members, self.tapped_members)
        np.copyto(new.rested_members, self.rested_members)
        np.copyto(new.continuous_effects_vec, self.continuous_effects_vec)

        # 3. Sets and complex structures (slowest)
        np.copyto(new.members_played_this_turn, self.members_played_this_turn)
        new.used_abilities = set(self.used_abilities)
        new.restrictions = set(self.restrictions)
        new.mulligan_selection = set(self.mulligan_selection)
        new.meta_rules = set(self.meta_rules)
        new.meta_rules = set(self.meta_rules)
        new.moved_members_this_turn = set(self.moved_members_this_turn)
        new.members_tapped_by_opponent_this_turn = set(self.members_tapped_by_opponent_this_turn)
        new.passed_lives = list(self.passed_lives)

        # Legacy continuous_effects (only copy if needed or for AI skip)
        if hasattr(self, "fast_mode") and self.fast_mode:
            new.continuous_effects = []
        else:
            new.continuous_effects = [dict(e) for e in self.continuous_effects]

    def untap_all(self) -> None:
        self.tapped_energy[:] = False
        self.tapped_members[:] = False
        self.live_cards_set_this_turn = 0

    def count_untapped_energy(self) -> int:
        return int(np.count_nonzero(~self.tapped_energy[: len(self.energy_zone)]))

        return breakdown

    def get_blades_breakdown(self, slot_idx: int, card_db: Dict[int, MemberCard]) -> List[Dict[str, Any]]:
        """Calculate blades breakdown for a slot (Rule 9.9)."""
        card_id = self.stage[slot_idx]
        if card_id < 0:
            return [{"source": f"Slot {slot_idx + 1}", "value": 0, "type": "empty", "source_id": -1}]

        # Check if member is tapped (inactive)
        if self.tapped_members[slot_idx]:
            from engine.game.state_utils import get_base_id

            base_id = get_base_id(int(card_id))
            name = card_db[base_id].name if base_id in card_db else "Unknown"
            return [{"source": f"{name} (Resting)", "value": 0, "type": "inactive", "source_id": int(card_id)}]

        from engine.game.state_utils import get_base_id

        base_id = get_base_id(int(card_id))
        if base_id not in card_db:
            return [{"source": "Unknown Card", "value": 0, "type": "error"}]

        member = card_db[base_id]
        breakdown = [{"source": member.name, "value": int(member.blades), "type": "base", "source_id": int(card_id)}]

        # Collect effects
        applied_effects = []  # List of (source_name, effect)
        for ce in self.continuous_effects:
            # ONLY include effects targeting this specific slot.
            # Global effects (target_slot == -1) are handled at the Player level to avoid overcounting.
            if ce.get("target_slot") == slot_idx:
                src = ce.get("source_name", "Effect")
                if "condition_text" in ce:
                    src += f" ({ce['condition_text']})"
                applied_effects.append((src, ce["effect"]))

        for ab in member.abilities:
            if ab.trigger == TriggerType.CONSTANT:
                if all(self._check_condition_for_constant(ab_cond, slot_idx, card_db) for ab_cond in ab.conditions):
                    for eff in ab.effects:
                        # Construct a helpful source string
                        src = member.name
                        if ab.conditions:
                            cond_texts = []
                            for c in ab.conditions:
                                if c.type == ConditionType.TURN_1:
                                    cond_texts.append("Turn 1")
                                elif c.type == ConditionType.COUNT_STAGE:
                                    cond_texts.append(f"Stage {c.params.get('value', 0)}+")
                                elif c.type == ConditionType.COUNT_HAND:
                                    cond_texts.append(f"Hand {c.params.get('value', 0)}+")
                                elif c.type == ConditionType.LIFE_LEAD:
                                    cond_texts.append("Life Lead")
                                else:
                                    cond_texts.append("Cond")
                            src += f" ({', '.join(cond_texts)})"
                        else:
                            src += " (Constant)"
                        applied_effects.append((src, eff))

        # Layer 4: SET
        for source, eff in applied_effects:
            if eff.effect_type == EffectType.SET_BLADES:
                breakdown = [
                    {"source": source, "value": int(eff.value), "type": "set", "source_id": ce.get("source_id", -1)}
                ]

        # Layer 4: ADD / BUFF
        for source, eff in applied_effects:
            if eff.effect_type in (EffectType.ADD_BLADES, EffectType.BUFF_POWER):
                val = eff.value
                val_desc = ""
                if eff.params.get("multiplier"):
                    if eff.params.get("per_live"):
                        val *= len(self.success_lives)
                        val_desc = f" ({len(self.success_lives)} Lives)"
                    elif eff.params.get("per_energy"):
                        val *= len(self.energy_zone)
                        val_desc = f" ({len(self.energy_zone)} Energy)"
                    elif eff.params.get("per_member"):
                        val *= np.sum(self.stage >= 0)
                        val_desc = f" ({np.sum(self.stage >= 0)} Members)"

                final_source = source + val_desc
                breakdown.append(
                    {
                        "source": final_source,
                        "value": int(val),
                        "type": "mod",
                        "source_id": ce.get("source_id", -1) if "ce" in locals() else int(card_id),
                    }
                )

        return breakdown

    def get_global_blades_breakdown(self) -> List[Dict[str, Any]]:
        """Calculate breakdown for global (player-wide) blade effects."""
        breakdown = []
        applied_effects = []
        for ce in self.continuous_effects:
            if ce.get("target_slot") == -1:
                src = ce.get("source_name", "Effect")
                if "condition_text" in ce:
                    src += f" ({ce['condition_text']})"
                applied_effects.append((ce, src, ce["effect"]))

        for ce, source, eff in applied_effects:
            if eff.effect_type in (EffectType.ADD_BLADES, EffectType.BUFF_POWER):
                val = eff.value
                val_desc = ""
                if eff.params.get("multiplier"):
                    if eff.params.get("per_live"):
                        val *= len(self.success_lives)
                        val_desc = f" ({len(self.success_lives)} Lives)"
                    elif eff.params.get("per_energy"):
                        val *= len(self.energy_zone)
                        val_desc = f" ({len(self.energy_zone)} Energy)"
                    elif eff.params.get("per_member"):
                        val *= np.sum(self.stage >= 0)
                        val_desc = f" ({np.sum(self.stage >= 0)} Members)"

                final_source = source + val_desc
                breakdown.append(
                    {
                        "source": final_source,
                        "value": int(val),
                        "type": "mod",
                        "source_id": ce.get("source_id", -1),
                    }
                )
        return breakdown

    def get_effective_blades(self, slot_idx: int, card_db: Dict[int, MemberCard]) -> int:
        breakdown = self.get_blades_breakdown(slot_idx, card_db)
        total = sum(item["value"] for item in breakdown)
        return max(0, total)

    def _check_condition_for_constant(
        self, cond: Condition, slot_idx: int, card_db: Dict[int, MemberCard] = None
    ) -> bool:
        """
        Check if a condition is met for a constant ability.
        slot_idx < 0 implies the card is not on stage (e.g. in hand for cost reduction).
        """
        if cond.type == ConditionType.NONE:
            return True

        # Conditions that require being on stage
        if slot_idx < 0:
            if cond.type in (ConditionType.HAS_MOVED, ConditionType.IS_CENTER, ConditionType.GROUP_FILTER):
                # For GROUP_FILTER, if it's checking SELF, we might need the card ID context which is not passed here properly.
                # But for cost reduction, usually it's just Hand/Stage counts.
                return False

        if cond.type == ConditionType.HAS_MOVED:
            # Check if this card moved this turn.
            current_card_id = self.stage[slot_idx]
            if current_card_id >= 0:
                return current_card_id in self.moved_members_this_turn
            return False
        elif cond.type == ConditionType.TURN_1:
            # This would require access to game state to check turn number
            # For now, return True as a placeholder
            return True
        elif cond.type == ConditionType.IS_CENTER:
            # Check if the slot is the center position (index 1 in 3-slot system)
            return slot_idx == 1
        elif cond.type == ConditionType.GROUP_FILTER:
            # Check if the member belongs to the specified group
            current_card_id = self.stage[slot_idx]
            if current_card_id >= 0 and card_db:
                from engine.game.state_utils import get_base_id

                base_id = get_base_id(int(current_card_id))
                if base_id in card_db:
                    member = card_db[base_id]
                group_name = cond.params.get("group", "")
                # This would need to compare member's group with the condition's group
                # For now, return True as a placeholder
                return True
            return False
        elif cond.type == ConditionType.COUNT_GROUP:
            # Count members of a specific group in the stage
            group_name = cond.params.get("group", "")
            min_count = cond.params.get("min", 1)
            zone = cond.params.get("zone", "STAGE")

            count = 0
            if zone == "STAGE" or zone == "OPPONENT_STAGE":
                from engine.game.state_utils import get_base_id

                for i in range(3):
                    card_id = self.stage[i]
                    if card_id >= 0 and card_db:
                        base_id = get_base_id(int(card_id))
                        if base_id in card_db:
                            member = card_db[base_id]
                            # Compare member's group with the condition's group
                            # For now, return True as a placeholder
                            count += 1

            return count >= min_count
        elif cond.type == ConditionType.OPPONENT_HAS:
            # Placeholder for opponent has condition
            return True
        elif cond.type == ConditionType.COUNT_ENERGY:
            min_energy = cond.params.get("min", 1)
            return len(self.energy_zone) >= min_energy
        else:
            # Default lenient for other conditions
            return True

    def get_hearts_breakdown(self, slot_idx: int, card_db: Dict[int, MemberCard]) -> List[Dict[str, Any]]:
        """Calculate hearts breakdown for a slot, including continuous effects."""
        card_id = self.stage[slot_idx]
        if card_id < 0:
            return [{"source": f"Slot {slot_idx + 1}", "value": [0] * 7, "type": "empty", "source_id": -1}]

        # Check if member is tapped (inactive)
        if self.tapped_members[slot_idx]:
            from engine.game.state_utils import get_base_id

            base_id = get_base_id(int(card_id))
            name = card_db[base_id].name if base_id in card_db else "Unknown"
            return [{"source": f"{name} (Resting)", "value": [0] * 7, "type": "inactive", "source_id": int(card_id)}]

        from engine.game.state_utils import get_base_id

        base_id = get_base_id(int(card_id))
        if base_id not in card_db:
            return [{"source": "Unknown Card", "value": [0] * 7, "type": "error"}]

        member = card_db[base_id]

        # Ensure base hearts are 7-dim
        base_hearts = np.zeros(7, dtype=np.int32)
        base_hearts[: len(member.hearts)] = member.hearts

        breakdown = [{"source": member.name, "value": base_hearts.tolist(), "type": "base", "source_id": int(card_id)}]

        # Collect effects
        applied_effects = []
        for ce in self.continuous_effects:
            if ce.get("target_slot") in (-1, slot_idx):
                src = ce.get("source_name", "Effect")
                if "condition_text" in ce:
                    src += f" ({ce['condition_text']})"
                applied_effects.append((src, ce["effect"]))

        for ab in member.abilities:
            if ab.trigger == TriggerType.CONSTANT:
                if all(self._check_condition_for_constant(ab_cond, slot_idx, card_db) for ab_cond in ab.conditions):
                    for eff in ab.effects:
                        # Construct a helpful source string
                        src = member.name
                        if ab.conditions:
                            cond_texts = []
                            for c in ab.conditions:
                                if c.type == ConditionType.TURN_1:
                                    cond_texts.append("Turn 1")
                                elif c.type == ConditionType.COUNT_STAGE:
                                    cond_texts.append(f"Stage {c.params.get('value', 0)}+")
                                elif c.type == ConditionType.COUNT_HAND:
                                    cond_texts.append(f"Hand {c.params.get('value', 0)}+")
                                elif c.type == ConditionType.LIFE_LEAD:
                                    cond_texts.append("Life Lead")
                                elif c.type == ConditionType.HAS_MEMBER:
                                    cond_texts.append("Has Member")
                                elif c.type == ConditionType.HAS_COLOR:
                                    cond_texts.append("Has Color")
                                else:
                                    cond_texts.append("Cond")
                            src += f" ({', '.join(cond_texts)})"
                        else:
                            src += " (Constant)"
                        applied_effects.append((src, eff))

        # Apply Heart Modifications
        for source, eff in applied_effects:
            eff_val = np.zeros(7, dtype=np.int32)

            if eff.effect_type == EffectType.SET_HEARTS:
                breakdown = [
                    {
                        "source": source,
                        "value": [int(eff.value)] * 7,
                        "type": "set",
                        "source_id": ce.get("source_id", -1),
                    }
                ]
                # Reset others? For SET, usually yes.
                continue

            if eff.effect_type == EffectType.ADD_HEARTS:
                color_map = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5}  # P,R,Y,G,B,P
                target_colors = []
                if eff.params.get("color"):
                    c = eff.params["color"]
                    if c in color_map:
                        target_colors.append(color_map[c])
                elif eff.params.get("all"):
                    target_colors = list(range(6))

                amount = eff.value
                # Multipliers
                if eff.params.get("multiplier"):
                    if eff.params.get("per_live"):
                        amount *= len(self.success_lives)
                    elif eff.params.get("per_energy"):
                        amount *= len(self.energy_zone)

                for c_idx in target_colors:
                    eff_val[c_idx] += amount

                if not target_colors:
                    pass

                # Only append if non-zero
                if np.any(eff_val):
                    breakdown.append(
                        {
                            "source": source,
                            "value": eff_val.tolist(),
                            "type": "mod",
                            "source_id": ce.get("source_id", -1) if "ce" in locals() else int(card_id),
                        }
                    )

        return breakdown

    def get_effective_hearts(self, slot_idx: int, card_db: Dict[int, MemberCard]) -> np.ndarray:
        breakdown = self.get_hearts_breakdown(slot_idx, card_db)
        total = np.zeros(7, dtype=np.int32)
        for item in breakdown:
            total += np.array(item["value"], dtype=np.int32)
        return np.maximum(0, total)

    def get_total_blades(self, card_db: Dict[int, MemberCard]) -> int:
        total = 0
        # 1. Base + Slot-specific modifiers
        for i, card_id in enumerate(self.stage):
            if card_id >= 0 and not self.tapped_members[i]:
                total += self.get_effective_blades(i, card_db)

        # 2. Global modifiers
        global_mods = self.get_global_blades_breakdown()
        for mod in global_mods:
            total += mod["value"]

        return max(0, total)

    def get_total_hearts(self, card_db: Dict[int, Any]) -> np.ndarray:
        total = np.zeros(7, dtype=np.int32)
        for i, card_id in enumerate(self.stage):
            if card_id >= 0 and not self.tapped_members[i]:
                total += self.get_effective_hearts(i, card_db)

        # Rank 5: Blades as Hearts
        # Condition A: Card 30030 in Live Zone (Revealed)
        has_rank_5 = False
        for i, l_id in enumerate(self.live_zone):
            if l_id == 30030 and (i < len(self.live_zone_revealed) and self.live_zone_revealed[i]):
                has_rank_5 = True
                break

        # Condition B: Card 414 on Stage (Active)
        if not has_rank_5:
            for i, m_id in enumerate(self.stage):
                if m_id == 414 and not self.tapped_members[i]:
                    has_rank_5 = True
                    break

        if has_rank_5:
            blades = self.get_total_blades(card_db)
            total[6] += blades

        return total

    def get_performance_guide(self, live_db: Dict[int, Any], member_db: Dict[int, Any]) -> Dict[str, Any]:
        """
        Calculate projected performance outcome for the user guide.
        Now comprehensive: includes breakdown for all slots (active, resting, empty)
        and requirement modifications.
        """
        if not self.live_zone:
            return {"can_perform": False, "reason": "No live cards"}

        from engine.game.state_utils import get_base_id

        # 1. Total Blades & Blade Breakdown
        total_blades = 0
        blade_breakdown = []
        # Always iterate 0-2 to show all slots
        for i in range(3):
            # Breakdown method handles empty/inactive cases now
            bd = self.get_blades_breakdown(i, member_db)
            blade_breakdown.extend(bd)
            if self.stage[i] >= 0 and not self.tapped_members[i]:
                # Sum up effective blades from breakdown for Active members
                slot_total = sum(item["value"] for item in bd if item.get("type") in ("base", "mod", "set"))
                total_blades += max(0, slot_total)

        # Apply cheer_mod
        extra_reveals = sum(
            ce["effect"].value
            for ce in self.continuous_effects
            if ce["effect"].effect_type == EffectType.META_RULE and ce["effect"].params.get("type") == "cheer_mod"
        )
        total_blades = max(0, total_blades + extra_reveals)

        # 2. Total Hearts & Heart Breakdown
        total_hearts = np.zeros(7, dtype=np.int32)
        heart_breakdown = []
        for i in range(3):
            bd = self.get_hearts_breakdown(i, member_db)
            heart_breakdown.extend(bd)
            if self.stage[i] >= 0 and not self.tapped_members[i]:
                # Sum up effective hearts from breakdown for Active members
                for item in bd:
                    if item.get("type") in ("base", "mod", "set"):
                        total_hearts += np.array(item["value"], dtype=np.int32)

        # Rank 5: Blades as Hearts
        has_rank_5 = False
        rank_5_source = ""
        rank_5_id = -1
        for i, l_id in enumerate(self.live_zone):
            if l_id == 30030 and (i < len(self.live_zone_revealed) and self.live_zone_revealed[i]):
                has_rank_5 = True
                rank_5_source = "Reflection in the mirror"
                rank_5_id = 30030
                break
        if not has_rank_5:
            for i, m_id in enumerate(self.stage):
                if m_id == 414 and not self.tapped_members[i]:
                    has_rank_5 = True
                    rank_5_source = member_db[414].name if 414 in member_db else "Megumi"
                    rank_5_id = 414
                    break

        if has_rank_5:
            blades = self.get_total_blades(member_db)
            if blades > 0:
                val_arr = [0] * 7
                val_arr[6] = blades
                heart_breakdown.append(
                    {
                        "source": f"Rank 5: {rank_5_source} (Blades as Hearts)",
                        "value": val_arr,
                        "type": "mod",
                        "source_id": rank_5_id,
                    }
                )
                total_hearts[6] += blades

        # 3. Apply TRANSFORM_COLOR (Global)
        transform_log = []
        for ce in self.continuous_effects:
            if ce["effect"].effect_type == EffectType.TRANSFORM_COLOR:
                eff = ce["effect"]
                src_color = eff.params.get("from_color", eff.params.get("color"))  # 1-based
                dest_color = eff.params.get("to_color")  # 1-based
                if src_color and dest_color:
                    try:
                        # Handle possibly float/string values
                        s_idx = int(src_color) - 1
                        d_idx = int(dest_color) - 1
                        if 0 <= s_idx < 6 and 0 <= d_idx < 6:
                            amount_moved = total_hearts[s_idx]
                            total_hearts[d_idx] += amount_moved
                            total_hearts[s_idx] = 0
                            transform_log.append(
                                {
                                    "source": ce.get("source_name", "Effect"),
                                    "desc": f"Color Transform (Type {src_color} -> Type {dest_color})",
                                    "type": "transform",
                                    "source_id": ce.get("source_id", -1),
                                }
                            )
                    except:
                        pass

        # 4. Process Lives & Requirements
        lives = []
        req_breakdown = []  # Log for requirement reductions

        for live_id in self.live_zone:
            l_base = get_base_id(live_id)
            if l_base not in live_db:
                continue
            live_card = live_db[l_base]

            # Base Requirement
            req_breakdown.append(
                {"source": live_card.name, "value": live_card.required_hearts.tolist(), "type": "base_req"}
            )

            # Copy requirement to modify
            req = live_card.required_hearts.copy()  # (7,)

            # Apply REDUCE_HEART_REQ
            for ce in self.continuous_effects:
                eff = ce["effect"]
                if eff.effect_type == EffectType.REDUCE_HEART_REQ:
                    reduction_val = np.zeros(7, dtype=np.int32)
                    target_color = eff.params.get("color")
                    val = eff.value

                    if target_color and target_color != "any":
                        try:
                            c_idx = int(target_color) - 1
                            if 0 <= c_idx < 6:
                                reduction_val[c_idx] = val
                        except:
                            pass
                    else:
                        # Any color reduction (index 6) matches "any" param or default
                        reduction_val[6] = val

                    # Log reduction
                    if np.any(reduction_val > 0):
                        req_breakdown.append(
                            {
                                "source": ce.get("source_name", "Effect"),
                                "value": (-reduction_val).tolist(),
                                "type": "req_mod",
                                "source_id": ce.get("source_id", -1),
                            }
                        )
                        req = np.maximum(0, req - reduction_val)

            # Calculate Success (Greedy)
            temp_hearts = total_hearts.copy()

            # 1. Match specific colors
            needed_specific = req[:6]
            have_specific = temp_hearts[:6]
            used_specific = np.minimum(needed_specific, have_specific)

            temp_hearts[:6] -= used_specific
            remaining_req = req.copy()
            remaining_req[:6] -= used_specific

            # 2. Match Any with remaining specific
            needed_any = remaining_req[6]
            have_any_from_specific = np.sum(temp_hearts[:6])
            used_any_from_specific = min(needed_any, have_any_from_specific)

            # 3. Match Any with Any
            needed_any -= used_any_from_specific
            have_wild = temp_hearts[6]
            used_wild = min(needed_any, have_wild)

            met = np.all(remaining_req[:6] == 0) and (needed_any - used_wild <= 0)

            lives.append(
                {
                    "name": live_card.name,
                    "img": live_card.img_path,
                    "score": int(live_card.score),
                    "req": req.tolist(),
                    "passed": bool(met),
                    "reason": "" if met else "Not met",
                    "base_score": int(live_card.score),
                    "bonus_score": self.live_score_bonus,
                }
            )

        return {
            "can_perform": True,
            "total_blades": int(total_blades),
            "total_hearts": total_hearts.tolist(),
            "lives": lives,
            "breakdown": {
                "blades": blade_breakdown,
                "hearts": heart_breakdown,
                "requirements": req_breakdown,
                "transforms": transform_log,
            },
        }

    def get_member_cost(self, card_id: int, card_db: Dict[int, MemberCard]) -> int:
        """
        Calculate effective cost of a member card in hand.
        """
        from engine.game.state_utils import get_base_id

        base_id = get_base_id(card_id)
        if base_id not in card_db:
            return 0

        member = card_db[base_id]
        cost = member.cost

        # Apply global cost reduction effects
        total_reduction = 0
        for ce in self.continuous_effects:
            if ce["effect"].effect_type == EffectType.REDUCE_COST:
                total_reduction += ce["effect"].value

        # Q129: Apply card's OWN constant abilities if they reduce cost in hand.
        for ab in member.abilities:
            if ab.trigger == TriggerType.CONSTANT:
                for eff in ab.effects:
                    if eff.effect_type == EffectType.REDUCE_COST and eff.target == TargetType.SELF:
                        conditions_met = True
                        for cond in ab.conditions:
                            if not self._check_condition_for_constant(cond, slot_idx=-1, card_db=card_db):
                                conditions_met = False
                                break

                        if conditions_met:
                            val = eff.value
                            if eff.params.get("multiplier") and eff.params.get("per_hand_other"):
                                count = max(0, len(self.hand) - 1)
                                val *= count
                            total_reduction += val

        return max(0, cost - total_reduction)

    def to_dict(self, viewer_idx=0):
        # We now have StateMixin.to_dict() but we might want this custom one for the UI.
        # Actually, let's just use StateMixin.to_dict and enrich it if needed in serializer.py.
        # This keeps PlayerState purely about state.
        return super().to_dict()
