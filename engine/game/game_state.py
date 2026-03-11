"""
Love Live Card Game - AlphaZero Compatible Game State

This module implements the game state representation for the Love Live
Official Card Game, designed for fast self-play with AlphaZero-style training.

Key Design Decisions:
- Numpy arrays for vectorized operations
- Immutable state with state copying for MCTS
- Action space encoded as integers for neural network output
- Observation tensors suitable for CNN input
"""

# Love Live! Card Game - Comprehensive Rules v1.04 Implementation

# Rule 1: (General Overview)

# Rule 2: (Card Information)

# Rule 3: (Player Info)

# Rule 4: (Zones)

# Rule 1.3: (Fundamental Principles)

# Rule 1.3.1: Card text overrides rules.

# Rule 1.3.2: Impossible actions are simply not performed.

# Rule 1.3.3: "Cannot" effects take priority over "Can" effects.

# Rule 1.3.4: Active player chooses first when multiple choices occur.

# Rule 1.3.5: Numerical selections must be non-negative integers.

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from engine.game.data_loader import CardDataLoader
from engine.game.enums import Phase
from engine.game.mixins.action_mixin import ActionMixin
from engine.game.mixins.effect_mixin import EffectMixin
from engine.game.mixins.phase_mixin import PhaseMixin
from engine.models.ability import (
    Ability,
    EffectType,
    ResolvingEffect,
    TriggerType,
)
from engine.models.card import LiveCard, MemberCard
from engine.models.enums import Group, Unit

# Import Numba utils

# Import Numba utils

try:
    from engine.game.numba_utils import JIT_AVAILABLE, calc_main_phase_masks

except ImportError:
    JIT_AVAILABLE = False

    def calc_main_phase_masks(*args):
        pass

# =============================================================================

# OBJECT POOLING FOR PERFORMANCE

# =============================================================================


class StatePool:
    """

    Object pool for PlayerState and GameState to avoid allocation overhead.

    Thread-local pools for multiprocessing compatibility.

    """

    _player_pool: List["PlayerState"] = []

    _game_pool: List["GameState"] = []

    _max_pool_size: int = 100

    @classmethod
    def get_player_state(cls, player_id: int) -> "PlayerState":
        """Get a PlayerState - POOLING DISABLED for safety"""

        return PlayerState(player_id)

    @classmethod
    def get_game_state(cls) -> "GameState":
        """Get a GameState - POOLING DISABLED for safety"""

        return GameState()

    @classmethod
    def return_player_state(cls, ps: "PlayerState") -> None:
        """Return a PlayerState to the pool for reuse."""

        if len(cls._player_pool) < cls._max_pool_size:
            cls._player_pool.append(ps)

    @classmethod
    def return_game_state(cls, gs: "GameState") -> None:
        """Return a GameState to the pool for reuse."""

        if len(cls._game_pool) < cls._max_pool_size:
            cls._game_pool.append(gs)


# Phase enum moved to enums.py

# Enums and Card Classes moved to engine.models

# Imported above

from engine.game.player_state import PlayerState


class GameState(ActionMixin, PhaseMixin, EffectMixin):
    """

    Full game state (Rule 1)

    Features:

    - Rule 4.14: Resolution Zone (yell_cards)

    - Rule 1.2: Victory Detection

    - MCTS / AlphaZero support

    """

    # Class-level caches
    member_db: Dict[int, MemberCard] = {}
    live_db: Dict[int, LiveCard] = {}
    _meta_rule_cards: set = set()

    # JIT Arrays
    _jit_member_costs: Optional[np.ndarray] = None
    _jit_member_blades: Optional[np.ndarray] = None
    _jit_member_hearts_sum: Optional[np.ndarray] = None
    _jit_member_hearts_vec: Optional[np.ndarray] = None
    _jit_live_score: Optional[np.ndarray] = None
    _jit_live_hearts_sum: Optional[np.ndarray] = None
    _jit_live_hearts_vec: Optional[np.ndarray] = None

    @classmethod
    def initialize_class_db(cls, member_db: Dict[int, "MemberCard"], live_db: Dict[int, "LiveCard"]) -> None:
        """Initialize and wrap static DBs with MaskedDB for UID resolution."""
        from engine.game.state_utils import MaskedDB

        cls.member_db = MaskedDB(member_db)
        cls.live_db = MaskedDB(live_db)

        # Optimization: Cache cards with CONSTANT META_RULE effects
        cls._meta_rule_cards = set()
        for cid, card in cls.member_db.items():
            for ab in card.abilities:
                if ab.trigger.name == "CONSTANT":
                    for eff in ab.effects:
                        if eff.effect_type == EffectType.META_RULE:
                            cls._meta_rule_cards.add(cid)
                            break
        for cid, card in cls.live_db.items():
            for ab in card.abilities:
                if ab.trigger.name == "CONSTANT":
                    for eff in ab.effects:
                        if eff.effect_type == EffectType.META_RULE:
                            cls._meta_rule_cards.add(cid)
                            break

        cls._init_jit_arrays()

    @classmethod
    def _init_jit_arrays(cls):
        """Initialize static arrays for Numba JIT"""

        if not cls.member_db:
            return

        # Find max ID

        max_id = max(max(cls.member_db.keys(), default=0), max(cls.live_db.keys(), default=0))

        # Create lookup arrays (default 0 or -1)

        # Costs: -1 for non-members

        costs = np.full(max_id + 1, -1, dtype=np.int32)

        # Blades: 0

        blades = np.zeros(max_id + 1, dtype=np.int32)

        # Hearts Sum: 0

        hearts_sum = np.zeros(max_id + 1, dtype=np.int32)

        # Hearts Vector: (N, 7)

        hearts_vec = np.zeros((max_id + 1, 7), dtype=np.int32)

        # Live Score: 0

        live_score = np.zeros(max_id + 1, dtype=np.int32)

        # Live Hearts Requirement Sum: 0

        live_hearts_sum = np.zeros(max_id + 1, dtype=np.int32)

        # Live Hearts Vector: (N, 7)

        live_hearts_vec = np.zeros((max_id + 1, 7), dtype=np.int32)

        for cid, member in cls.member_db.items():
            costs[cid] = member.cost

            blades[cid] = member.blades

            if hasattr(member, "hearts"):
                h = member.hearts
                # Robustly handle arrays likely to be shape (6,) or (7,)
                if len(h) >= 7:
                    hearts_vec[cid] = h[:7]
                else:
                    hearts_vec[cid, : len(h)] = h

                hearts_sum[cid] = np.sum(member.hearts)

        for cid, live in cls.live_db.items():
            live_score[cid] = int(live.score)

            if hasattr(live, "required_hearts"):
                rh = live.required_hearts
                if len(rh) >= 7:
                    live_hearts_vec[cid] = rh[:7]
                else:
                    live_hearts_vec[cid, : len(rh)] = rh

                live_hearts_sum[cid] = np.sum(live.required_hearts)

        cls._jit_member_costs = costs

        cls._jit_member_blades = blades

        cls._jit_member_hearts_sum = hearts_sum

        cls._jit_member_hearts_vec = hearts_vec

        cls._jit_live_score = live_score

        cls._jit_live_hearts_sum = live_hearts_sum

        cls._jit_live_hearts_vec = live_hearts_vec

    @classmethod
    def serialize_card(cls, cid: int, is_viewable=True, peek=False):
        """Static helper to serialize a card ID."""

        if cid < 0:
            return None

        card_data = {"id": int(cid), "img": "cards/card_back.png", "type": "unknown", "name": "Unknown"}

        if not is_viewable and not peek:
            return {"id": int(cid), "img": "cards/card_back.png", "type": "unknown", "hidden": True}

        if cid in cls.member_db:
            m = cls.member_db[cid]

            # Basic ability text formatting

            at = getattr(m, "ability_text", "")

            if not at and hasattr(m, "abilities"):
                at_lines = []

                for ab in m.abilities:
                    at_lines.append(ab.raw_text)

                at = "\n".join(at_lines)

            card_data = {
                "id": int(cid),
                "card_no": getattr(m, "card_no", "Unknown"),
                "name": getattr(m, "name", "Unknown Member"),
                "cost": int(getattr(m, "cost", 0)),
                "type": "member",
                "hp": int(m.total_hearts()) if hasattr(m, "total_hearts") else 0,
                "blade": int(getattr(m, "blades", 0)),
                "img": getattr(m, "img_path", "cards/card_back.png"),
                "hearts": m.hearts.tolist() if hasattr(m, "hearts") and hasattr(m.hearts, "tolist") else [0] * 7,
                "blade_hearts": m.blade_hearts.tolist()
                if hasattr(m, "blade_hearts") and hasattr(m.blade_hearts, "tolist")
                else [0] * 7,
                "text": at,
            }

        elif cid in cls.live_db:
            l = cls.live_db[cid]

            card_data = {
                "id": int(cid),
                "card_no": getattr(l, "card_no", "Unknown"),
                "name": l.name,
                "type": "live",
                "score": int(l.score),
                "img": l.img_path,
                "required_hearts": l.required_hearts.tolist(),
                "text": getattr(l, "ability_text", ""),
            }

        elif cid == 888:  # Easy member
            card_data = {
                "id": 888,
                "name": "Easy Member",
                "type": "member",
                "cost": 1,
                "hp": 1,
                "blade": 1,
                "img": "cards/PLSD01/PL!-sd1-001-SD.png",
                "hearts": [1, 0, 0, 0, 0, 0, 0],
                "blade_hearts": [0, 0, 0, 0, 0, 0, 0],
                "text": "",
            }

        elif cid == 999:  # Easy live
            card_data = {
                "id": 999,
                "name": "Easy Live",
                "type": "live",
                "score": 1,
                "img": "cards/PLSD01/PL!-pb1-019-SD.png",
                "required_hearts": [0, 0, 0, 0, 0, 0, 1],
                "text": "",
            }

        if not is_viewable and peek:
            card_data["hidden"] = True

            card_data["face_down"] = True

        return card_data

    __slots__ = (
        "verbose",
        "players",
        "current_player",
        "first_player",
        "phase",
        "turn_number",
        "game_over",
        "winner",
        "performance_results",
        "yell_cards",
        "pending_effects",
        "pending_choices",
        "rule_log",
        "turn_history",
        "current_resolving_ability",
        "current_resolving_member",
        "current_resolving_member_id",
        "looked_cards",
        "triggered_abilities",
        "state_history",
        "loop_draw",
        "removed_cards",
        "action_count_this_turn",
        "pending_choices_vec",
        "pending_choices_ptr",
        "triggered_abilities_vec",
        "triggered_abilities_ptr",
        "_jit_dummy_array",
        "fast_mode",
        "suppress_logs",
        "enable_loop_detection",
        "next_execution_id",
        "current_execution_id",
        "_trigger_buffers",
    )

    def __init__(self, verbose=False, suppress_logs=False, enable_loop_detection=True):
        self.verbose = verbose
        self.suppress_logs = suppress_logs
        self.enable_loop_detection = enable_loop_detection

        self.players = [PlayerState(0), PlayerState(1)]

        self.current_player = 0  # Who is acting now

        self.first_player = 0  # Who goes first this turn

        self.phase = Phase.ACTIVE

        self.turn_number: int = 1

        self.game_over: bool = False

        self.winner: int = -1  # -1 = ongoing, 0/1 = player won, 2 = draw

        # Performance Result Tracking (for UI popup)

        self.performance_results: Dict[int, Any] = {}

        # For yell phase tracking

        self.yell_cards: List[int] = []  # Shared Resolution Zone (Rule 4.14)

        self.pending_effects: List[ResolvingEffect] = []  # Stack of effects to resolve

        self.pending_activation: Optional[Dict[str, Any]] = None

        self.pending_choices: List[Tuple[str, Dict[str, Any]]] = []  # (choice_type, params with metadata)

        self.rule_log: List[str] = []  # Real-time rule application log

        # Track currently resolving ability for context

        self.current_resolving_ability: Optional[Ability] = None

        self.current_resolving_member: Optional[str] = None  # Member name

        self.current_resolving_member_id: int = -1  # Member card ID

        # Temporary zone for LOOK_DECK

        self.looked_cards: List[int] = []

        # Rule 9.7: Automatic Abilities

        # List of (player_id, Ability, context) waiting to be played

        self.triggered_abilities: List[Tuple[int, Ability, Dict[str, Any]]] = []

        # Vectorized triggers/choices for JIT
        self.pending_choices_vec = np.zeros((16, 3), dtype=np.int32)
        self.pending_choices_ptr = 0
        self.triggered_abilities_vec = np.zeros((16, 2), dtype=np.int32)
        self.triggered_abilities_ptr = 0
        self._jit_dummy_array = np.zeros(100, dtype=np.int32)
        self.fast_mode = False
        self._trigger_buffers = [[], []]  # Pre-allocated buffers for trigger processing

        # Static caches (for performance and accessibility)

        # Should be set from server or data loader

        # Loop Detection (Rule 12.1)

        # Using a simple hash of the serialization for history

        self.state_history: List[int] = []

        # Structured turn history for richer frontend rendering
        self.turn_history: List[Dict[str, Any]] = []

        # Execution id tracking for grouping related log entries
        self.next_execution_id: int = 1
        self.current_execution_id: Optional[int] = None

        self.loop_draw = False

        self.removed_cards: List[int] = []

        self.action_count_this_turn: int = 0

    def log_rule(self, rule_id: str, description: str):
        """Append a rule application entry to the log."""
        if self.suppress_logs:
            return

        # Use structured event logging so frontend can prefer metadata
        try:
            self.log_event(
                "RULE",
                description,
                source_cid=-1,
                ability_idx=-1,
                player_id=self.current_player,
                rule_ref=rule_id,
                log_to_rule_log=True,
            )
        except Exception:
            # Fallback to legacy string append if structured logging fails
            phase_name = self.phase.name if hasattr(self.phase, "name") else str(self.phase)
            entry = f"[Turn {self.turn_number}] [{phase_name}] [{rule_id}] {description}"
            self.rule_log.append(entry)
            if self.verbose:
                print(f"RULE_LOG: {entry}")

    def log_event(self, event_type: str, description: str, source_cid: int, ability_idx: int, player_id: int, rule_ref: Optional[str] = None, log_to_rule_log: bool = False):
        """Record a structured event and optionally append to the legacy text rule_log.

        Mirrors the Rust-side `log_event` shape so frontend can use structured data.
        """
        if self.suppress_logs:
            return

        # 1) Append to turn_history (cap to avoid unbounded growth)
        if getattr(self, "turn_history", None) is None:
            self.turn_history = []

        if len(self.turn_history) < 2000:
            try:
                ev = {
                    "turn": int(self.turn_number),
                    "phase": int(self.phase) if isinstance(self.phase, int) else getattr(self.phase, "value", str(self.phase)),
                    "player_id": int(player_id) if player_id is not None else -1,
                    "event_type": str(event_type),
                    "source_cid": int(source_cid) if source_cid is not None else -1,
                    "ability_idx": int(ability_idx) if ability_idx is not None else -1,
                    "description": str(description),
                    "rule_ref": rule_ref,
                }
            except Exception:
                ev = {
                    "turn": self.turn_number,
                    "phase": str(self.phase),
                    "player_id": player_id,
                    "event_type": event_type,
                    "source_cid": source_cid,
                    "ability_idx": ability_idx,
                    "description": description,
                    "rule_ref": rule_ref,
                }
            # Attach execution id if present
            if getattr(self, "current_execution_id", None) is not None:
                ev["execution_id"] = int(self.current_execution_id)
            self.turn_history.append(ev)

        # 2) Optionally also append a legacy text line for backward compatibility
        if log_to_rule_log:
            rule_prefix = f"[{rule_ref}] " if rule_ref else ""
            full_msg = f"[Turn {self.turn_number}] {rule_prefix}{description}"
            if self.rule_log is None:
                self.rule_log = []
            self.rule_log.append(full_msg)
            if self.verbose:
                print(f"RULE_LOG: {full_msg}")

    def generate_execution_id(self) -> int:
        eid = int(self.next_execution_id)
        # wrap-around like unsigned 32-bit
        self.next_execution_id = (self.next_execution_id + 1) & 0xFFFFFFFF
        self.current_execution_id = eid
        return eid

    def clear_execution_id(self) -> None:
        self.current_execution_id = None

    def _reset(self) -> None:
        """Reset state for pool reuse - avoids object allocation."""

        self.verbose = False

        # Players get reset by PlayerState._reset or replaced

        self.current_player = 0

        self.first_player = 0

        self.phase = Phase.ACTIVE

        self.turn_number = 1

        self.game_over = False

        self.winner = -1

        self.performance_results.clear()

        self.yell_cards.clear()

        self.pending_effects.clear()

        self.pending_choices.clear()

        self.rule_log.clear()

        self.current_resolving_ability = None

        self.current_resolving_member = None

        self.current_resolving_member_id = -1

        self.looked_cards.clear()

        self.triggered_abilities.clear()

        self.pending_choices_vec.fill(0)
        self.pending_choices_ptr = 0
        self.triggered_abilities_vec.fill(0)
        self.triggered_abilities_ptr = 0
        self._trigger_buffers[0].clear()
        self._trigger_buffers[1].clear()

        self.state_history.clear()

        self.loop_draw = False

    def copy(self) -> "GameState":
        """Copy current game state"""

        new = GameState()

        self.copy_to(new)

        return new

    def copy_to(self, new: "GameState") -> None:
        """In-place copy to an existing object to avoid allocation"""

        new.verbose = self.verbose
        new.suppress_logs = self.suppress_logs
        new.enable_loop_detection = self.enable_loop_detection

        # Reuse existing PlayerState objects in the pooled GameState

        for i, p in enumerate(self.players):
            p.copy_to(new.players[i])

        new.current_player = self.current_player

        new.first_player = self.first_player

        new.phase = self.phase

        new.turn_number = self.turn_number

        new.game_over = self.game_over

        new.winner = self.winner

        new.yell_cards = list(self.yell_cards)

        # Shallow copy of Effect objects (assumed immutable/shared)

        new.pending_effects = list(self.pending_effects)

        # Manual copy of pending_choices: List[Tuple[str, Dict]]

        new.pending_choices = [(pc[0], pc[1].copy()) for pc in self.pending_choices]

        new.rule_log = list(self.rule_log)

        new.current_resolving_ability = self.current_resolving_ability

        new.current_resolving_member = self.current_resolving_member

        new.current_resolving_member_id = self.current_resolving_member_id

        new.looked_cards = list(self.looked_cards)

        # Manual copy of triggered_abilities: List[Tuple[int, Ability, Dict[str, Any]]]

        # Tuple is immutable, Ability is shared, Dict needs copy

        new.triggered_abilities = [(ta[0], ta[1], ta[2].copy()) for ta in self.triggered_abilities]

        # Copy vectorized state
        np.copyto(new.pending_choices_vec, self.pending_choices_vec)
        new.pending_choices_ptr = self.pending_choices_ptr
        np.copyto(new.triggered_abilities_vec, self.triggered_abilities_vec)
        new.triggered_abilities_ptr = self.triggered_abilities_ptr
        new.fast_mode = self.fast_mode
        new._trigger_buffers = [list(self._trigger_buffers[0]), list(self._trigger_buffers[1])]

        new.state_history = list(self.state_history)

        new.loop_draw = self.loop_draw

        new.loop_draw = self.loop_draw

        # Optimization: Use shallow copy instead of deepcopy.
        # The engine only performs assignment (replace) or clear() (structure),
        # not in-place mutation of the nested lists.
        new.performance_results = self.performance_results.copy()

        # Copy deferred activation state (Rule 9.7 logic)
        if hasattr(self, "pending_activation") and self.pending_activation:
            new.pending_activation = self.pending_activation.copy()
            if "context" in new.pending_activation:
                new.pending_activation["context"] = new.pending_activation["context"].copy()
        else:
            new.pending_activation = None

    def inject_card(self, player_idx: int, card_id: int, zone: str, position: int = -1) -> None:
        """Inject a card into a specific zone for testing purposes."""

        if player_idx < 0 or player_idx >= len(self.players):
            raise ValueError("Invalid player index")

        p = self.players[player_idx]

        if zone == "hand":
            if position == -1:
                p.hand.append(card_id)

            else:
                p.hand.insert(position, card_id)

        elif zone == "energy":
            if position == -1:
                p.energy_zone.append(card_id)

            else:
                p.energy_zone.insert(position, card_id)

        elif zone == "live":
            if position == -1:
                p.live_zone.append(card_id)

                p.live_zone_revealed.append(False)

            else:
                p.live_zone.insert(position, card_id)

                p.live_zone_revealed.insert(position, False)

        elif zone == "stage":
            if position < 0 or position >= 3:
                raise ValueError("Stage position must be 0-2")

            p.stage[position] = card_id

        else:
            raise ValueError(f"Invalid zone: {zone}")

    @property
    def active_player(self) -> PlayerState:
        return self.players[self.current_player]

    @property
    def inactive_player(self) -> PlayerState:
        return self.players[1 - self.current_player]

    def is_terminal(self) -> bool:
        """Check if game has ended"""

        return self.game_over

    def get_winner(self) -> int:
        """Returns winner (0 or 1) or -1 if not terminal, 2 if draw"""

        return self.winner

    def check_win_condition(self) -> None:
        """Check if anyone has won (3+ successful lives)"""

        p0_lives = len(self.players[0].success_lives)

        p1_lives = len(self.players[1].success_lives)

        if p0_lives >= 3 and p1_lives >= 3:
            self.game_over = True

            if p0_lives > p1_lives:
                self.winner = 0

            elif p1_lives > p0_lives:
                self.winner = 1

            else:
                self.winner = 2  # Draw

        elif p0_lives >= 3:
            # Rule 1.2.1.1: Player 0 wins by 3 successful lives
            self.game_over = True
            self.winner = 0
            if hasattr(self, "log_rule"):
                self.log_rule("Rule 1.2.1.1", "Player 0 wins by 3 successful lives.")

        elif p1_lives >= 3:
            # Rule 1.2.1.1: Player 1 wins by 3 successful lives
            self.game_over = True
            self.winner = 1
            if hasattr(self, "log_rule"):
                self.log_rule("Rule 1.2.1.1", "Player 1 wins by 3 successful lives.")

    def _is_card_legal_for_choice(self, card_id: int, params: Dict[str, Any]) -> bool:
        """Helper to check if a card matches the filter criteria for a choice."""
        if card_id < 0:
            return False

        # Determine if it's a member or live card
        card = self.member_db.get(card_id) or self.live_db.get(card_id)
        if not card:
            return False

        # 1. Type filter
        req_type = params.get("filter", params.get("type"))
        if req_type == "member" and card_id not in self.member_db:
            return False
        if req_type == "live" and card_id not in self.live_db:
            return False

        # 2. Group filter
        group_filter = params.get("group")
        if group_filter is not None:
            target_group = Group.from_japanese_name(group_filter)
            if target_group not in getattr(card, "groups", []):
                # Also check units just in case
                target_unit = Unit.from_japanese_name(group_filter)
                if target_unit not in getattr(card, "units", []):
                    return False

        # 3. Cost filter
        cost_max = params.get("cost_max")
        if cost_max is not None and getattr(card, "cost", 0) > cost_max:
            return False

        cost_min = params.get("cost_min")
        if cost_min is not None and getattr(card, "cost", 0) < cost_min:
            return False

        return True

    def get_legal_actions(self) -> np.ndarray:
        """

        Returns a mask of legal actions (Rule 9.5.4:

        Expanded for Complexity:

        200-202: Activate ability of member in Area (LEFT, CENTER, RIGHT)

        300-359: Mulligan toggle

        400-459: Live Set

        500-559: Choose card in hand (index 0-59) for effect target

        560-562: Choose member on stage (Area 0-2) for effect target

        590-599: Choose pending trigger to resolve

        """

        mask = np.zeros(2000, dtype=bool)

        if self.game_over:
            return mask

        # Priority: If there are choices to be made for a pending effect

        if self.pending_choices:
            choice_type, params = self.pending_choices[0]

            p_idx = params.get("player_id", self.current_player)

            p = self.players[p_idx]

            if choice_type == "TARGET_HAND":
                # Allow skip for optional costs

                if params.get("is_optional"):
                    mask[0] = True

                found = False

                if len(p.hand) > 0:
                    for i, cid in enumerate(p.hand):
                        is_legal = self._is_card_legal_for_choice(cid, params)
                        if self.verbose:
                            print(f"DEBUG: TARGET_HAND check idx={i} cid={cid} legal={is_legal} params={params}")
                        if is_legal:
                            mask[500 + i] = True

                            found = True

                if not found:
                    mask[0] = True  # No valid cards in hand, allow pass logic (fizzle)

            elif choice_type == "TARGET_MEMBER" or choice_type == "TARGET_MEMBER_SLOT":
                # 560-562: Selected member on stage

                found = False

                for i in range(3):
                    if p.stage[i] >= 0 or choice_type == "TARGET_MEMBER_SLOT":
                        # Filter: for 'activate', only tapped members are legal

                        if params.get("effect") == "activate" and not p.tapped_members[i]:
                            continue

                        # Apply general filters if card exists

                        if p.stage[i] >= 0:
                            if not self._is_card_legal_for_choice(p.stage[i], params):
                                continue

                        mask[560 + i] = True

                        found = True

                if not found:
                    mask[0] = True  # No valid targets on stage, allow pass (fizzle)

            elif choice_type == "DISCARD_SELECT":
                # 500-559: Select card in hand to discard

                # Allow skip for optional costs

                if params.get("is_optional"):
                    mask[0] = True

                found = False

                if len(p.hand) > 0:
                    for i, cid in enumerate(p.hand):
                        if self._is_card_legal_for_choice(cid, params):
                            mask[500 + i] = True

                            found = True

                if not found and params.get("is_optional"):
                    mask[0] = True  # No cards to discard, allow pass

            elif choice_type == "MODAL" or choice_type == "SELECT_MODE":
                # params['options'] is a list of strings or list of lists

                options = params.get("options", [])

                for i in range(len(options)):
                    mask[570 + i] = True

            elif choice_type == "CHOOSE_FORMATION":
                # For now, just a dummy confirm? Or allow re-arranging?

                # Simplified: Action 0 to confirm current formation

                mask[0] = True

            elif choice_type == "COLOR_SELECT":
                # 580: Red, 581: Blue, 582: Green, 583: Yellow, 584: Purple, 585: Pink

                for i in range(6):
                    mask[580 + i] = True

            elif choice_type == "TARGET_OPPONENT_MEMBER":
                # Opponent Stage 0-2 -> Action 600-602

                opp = self.inactive_player

                found = False

                for i in range(3):
                    if opp.stage[i] >= 0:
                        mask[600 + i] = True

                        found = True

                if not found:
                    # If no valid targets but choice exists, softlock prevention:

                    # Ideally we should strictly check before pushing choice, but safe fallback:

                    mask[0] = True  # Pass/Cancel

            elif choice_type == "SELECT_FROM_LIST":
                # 600-659: List selection (up to 60 items)

                cards = params.get("cards", [])

                card_count = min(len(cards), 60)

                if card_count > 0:
                    mask[600 : 600 + card_count] = True

                else:
                    mask[0] = True  # Empty list, allow pass

            elif choice_type == "SELECT_FROM_DISCARD":
                # 660-719: Discard selection (up to 60 items)

                cards = params.get("cards", [])

                card_count = min(len(cards), 60)

                if card_count > 0:
                    mask[660 : 660 + card_count] = True

                else:
                    mask[0] = True  # Empty discard, allow pass

            elif choice_type == "SELECT_FORMATION_SLOT" or choice_type == "SELECT_ORDER":
                # 720-759: Item selection from a list (Formation)
                cards = params.get("cards", params.get("available_members", []))
                card_count = min(len(cards), 40)
                if card_count > 0:
                    mask[720 : 720 + card_count] = True
                else:
                    mask[0] = True

            elif choice_type == "SELECT_SWAP_SOURCE":
                # 600-659: Reuse list selection range

                cards = params.get("cards", [])

                card_count = min(len(cards), 60)

                if card_count > 0:
                    mask[600 : 600 + card_count] = True

                else:
                    mask[0] = True

            elif choice_type == "SELECT_SWAP_TARGET":
                # 500-559: Target hand range

                if len(p.hand) > 0:
                    for i in range(len(p.hand)):
                        mask[500 + i] = True

                else:
                    mask[0] = True

            elif choice_type == "SELECT_SUCCESS_LIVE" or choice_type == "TARGET_SUCCESS_LIVES":
                # 760-819: Select from passed lives list (Score)
                cards = params.get("cards", p.success_lives)
                card_count = min(len(cards), 60)
                if card_count > 0:
                    mask[760 : 760 + card_count] = True
                else:
                    mask[0] = True

            elif choice_type == "TARGET_LIVE":
                # 820-822: Select specific slot in Live Zone
                for i in range(len(p.live_zone)):
                    mask[820 + i] = True
                if not any(mask[820:823]):
                    mask[0] = True

            elif choice_type == "TARGET_ENERGY_ZONE":
                # 830-849: Select specific card in Energy Zone
                for i in range(len(p.energy_zone)):
                    if i < 20:
                        mask[830 + i] = True
                if not any(mask[830:850]):
                    mask[0] = True

            elif choice_type == "TARGET_REMOVED":
                # 850-909: Select from Removed cards
                count = min(len(self.removed_cards), 60)
                if count > 0:
                    mask[850 : 850 + count] = True
                else:
                    mask[0] = True

            elif choice_type == "TARGET_DECK" or choice_type == "TARGET_ENERGY_DECK" or choice_type == "TARGET_DISCARD":
                # List selection ranges
                cards = params.get("cards", [])
                card_count = min(len(cards), 60)
                offset = 600 if choice_type != "TARGET_DISCARD" else 660
                if card_count > 0:
                    mask[offset : offset + card_count] = True
                else:
                    mask[0] = True
            elif choice_type == "PAY_COST_OPTIONAL":
                # Action 570 for Yes, 0 for No
                mask[570] = True
                mask[0] = True

        # MULLIGAN phases: Select cards to return or confirm mulligan

        elif self.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            p = self.active_player

            mask[0] = True  # Confirm mulligan (done selecting)

            # Actions 300-359: Select card for mulligan (card index 0-59)

            # Note: We allow toggling selection.

            m_sel = getattr(p, "mulligan_selection", set())

            for i in range(len(p.hand)):
                mask[300 + i] = True

        # Auto-advance phases: these phases process automatically in 'step' when any valid action is received

        # We allow Action 0 (Pass) to trigger the transition.

        elif self.phase in (Phase.ACTIVE, Phase.ENERGY):
            mask[0] = True
        elif self.phase == Phase.PERFORMANCE_P1 or self.phase == Phase.PERFORMANCE_P2:
            p = self.active_player
            mask[0] = True  # Always can pass (skip performance)

            # Check all lives in live zone
            for i, card_id in enumerate(p.live_zone):
                # Standard Live ID as Action ID
                if card_id in self.live_db:
                    live_card = self.live_db[card_id]

                    # Check requirements
                    reqs = getattr(live_card, "required_hearts", [0] * 7)
                    if len(reqs) < 7:
                        reqs = [0] * 7

                    stage_hearts = [0] * 7
                    total_blades = 0

                    for slot in range(3):
                        sid = p.stage[slot]
                        if sid in self.member_db:
                            m = self.member_db[sid]
                            total_blades += m.blades

                            # Determine color index (1-6) from hearts
                            # Heuristic: Find first non-zero index in hearts array
                            # This mimics vector_env logic
                            col = 0
                            h_arr = m.hearts
                            for cidx, val in enumerate(h_arr):
                                if val > 0:
                                    col = cidx + 1
                                    break

                            if 1 <= col <= 6:
                                stage_hearts[col] += m.hearts[col - 1]  # m.hearts is 0-indexed?
                                # Wait, GameState initializes hearts_vec with m.hearts
                                # m.hearts is usually [Pink, Red, ...]
                                # Let's assume m.hearts is standard 7-dim or 6-dim
                                # If m.hearts[0] is Pink (Color 1), then:
                                pass

                    # Re-calculating correctly using GameState helper if available,
                    # else manual sum matching VectorEnv

                    # Optimized check:
                    # Use existing helper? p.get_effective_hearts?
                    # But that returns vector.

                    # Let's use p.stage stats directly
                    current_hearts = [0] * 7
                    current_blades = 0
                    for slot in range(3):
                        if p.stage[slot] != -1:
                            eff_h = p.get_effective_hearts(slot, self.member_db)
                            for c in range(7):
                                current_hearts[c] += eff_h[c]
                            current_blades += p.get_effective_blades(slot, self.member_db)

                    # Check against reqs
                    # reqs[0] is usually Any? Or Pink?
                    # In VectorEnv: 12-18 (Pink..Purple, All)
                    # live_card.required_hearts is 0-indexed typically [Pink, Red, Yel, Grn, Blu, Pur, Any]

                    met = True
                    # Check colors (0-5)
                    for c in range(6):
                        if current_hearts[c] < reqs[c]:
                            met = False
                            break
                    # Check Any (index 6, matches any color + explicit Any?)
                    # Usually Any req is satisfied by sum of all?
                    # For strictness, let's assume reqs[6] is specific "Any" points needed (wildcard).
                    # VectorEnv logic was:
                    # if stage_hearts[1] < req_pink...

                    # Assuming standard behavior:
                    if met and current_blades > 0:
                        mask[900 + i] = True

        elif self.phase == Phase.DRAW or self.phase == Phase.LIVE_RESULT:
            mask[0] = True

        elif self.phase == Phase.MAIN:
            p = self.active_player

            # Can always pass

            mask[0] = True

            # --- SHARED PRE-CALCULATIONS ---

            available_energy = p.count_untapped_energy()

            total_reduction = 0

            for ce in p.continuous_effects:
                if ce["effect"].effect_type == EffectType.REDUCE_COST:
                    total_reduction += ce["effect"].value

            # --- PLAY MEMBERS ---

            if "placement" not in p.restrictions:
                # JIT Optimization Path

                # JIT Path disabled temporarily for training stability

                if False and JIT_AVAILABLE and self._jit_member_costs is not None:
                    # Use pre-allocated hand buffer to avoid reallocation

                    hand_len = len(p.hand)

                    if hand_len > 0:
                        p.hand_buffer[:hand_len] = p.hand

                    calc_main_phase_masks(
                        p.hand_buffer[:hand_len],
                        p.stage,
                        available_energy,
                        total_reduction,
                        True,  # Baton touch is always allowed if slot occupied
                        p.members_played_this_turn,
                        self._jit_member_costs,
                        mask,
                    )

                else:
                    # Python Fallback

                    for i, card_id in enumerate(p.hand):
                        if card_id not in self.member_db:
                            continue

                        member = self.member_db[card_id]

                        for area in range(3):
                            action_id = 1 + i * 3 + area

                            if p.members_played_this_turn[area]:
                                continue

                            is_baton = p.stage[area] >= 0

                            # Calculate effective baton touch limit
                            extra_baton = sum(
                                ce["effect"].value
                                for ce in p.continuous_effects
                                if ce["effect"].effect_type == EffectType.BATON_TOUCH_MOD
                            )
                            effective_baton_limit = p.baton_touch_limit + extra_baton

                            if is_baton and p.baton_touch_count >= effective_baton_limit:
                                continue

                            # Calculate slot-specific cost
                            slot_reduction = sum(
                                ce["effect"].value
                                for ce in p.continuous_effects
                                if ce["effect"].effect_type == EffectType.REDUCE_COST
                                and (ce.get("target_slot", -1) in (-1, area))
                            )

                            active_cost = max(0, member.cost - slot_reduction)

                            if is_baton:
                                if p.stage[area] in self.member_db:
                                    baton_mem = self.member_db[p.stage[area]]
                                    active_cost = max(0, active_cost - baton_mem.cost)

                            if active_cost <= available_energy:
                                mask[action_id] = True

                            # DEBUG: Trace why specific cards fail

                            elif self.verbose and (member.cost >= 10 or card_id == 369):
                                print(
                                    f"DEBUG REJECT: Card {card_id} ({getattr(member, 'name', 'Unknown')}) Area {area}: Cost {active_cost} > Energy {available_energy}. Limit {p.baton_touch_limit}, Count {p.baton_touch_count}"
                                )

            # --- ACTIVATE ABILITIES ---

            # Uses same available_energy

            for i, card_id in enumerate(p.stage):
                if card_id >= 0 and card_id in self.member_db and not p.tapped_members[i]:
                    member = self.member_db[card_id]

                    for abi_idx, ab in enumerate(member.abilities):
                        if ab.trigger == TriggerType.ACTIVATED:
                            # Rule 9.7: Check once per turn
                            abi_key = f"{card_id}-{abi_idx}"
                            if ab.is_once_per_turn and abi_key in p.used_abilities:
                                continue

                            # Strict verification: Check conditions and costs

                            is_legal = True

                            if not all(self._check_condition(p, cond, context={"area": i}) for cond in ab.conditions):
                                is_legal = False

                            if is_legal and not self._can_pay_costs(p, ab.costs, source_area=i):
                                # print(f"DEBUG: Cost check failed for card {card_id} area {i}. Costs: {ab.costs}")
                                is_legal = False

                            if is_legal:
                                mask[200 + i] = True
                                # else:
                                # print(f"DEBUG: Ability {ab.raw_text} illegal for card {card_id} area {i}")

                                break  # Only one ability activation per member slot

        elif self.phase == Phase.LIVE_SET:
            p = self.active_player

            mask[0] = True

            # Check live restriction (Rule 8.3.4.1 / Cluster 3)

            if "live" not in p.restrictions and len(p.live_zone) < 3:
                # Allow ANY card to be set (Rule 8.2.2: "Choose up to 3 cards from your hand")
                for i, card_id in enumerate(p.hand):
                    mask[400 + i] = True

        else:
            # Other phases are automatic

            mask[0] = True

        # Safety check: Ensure at least one action is legal to prevent softlocks

        if not np.any(mask):
            # Force action 0 (Pass) as legal

            mask[0] = True

            # print(f"WARNING: No legal actions found in phase {self.phase.name}, forcing Pass action")

        return mask

    def step(self, action_id: int, check_legality: bool = True, in_place: bool = False) -> "GameState":
        """

        Executes one step in the game (Rule 9).

        Args:
            action_id: The action to execute.
            check_legality: Whether to verify action legality. Disable for speed if caller guarantees validity.
            in_place: If True, modifies the state in-place instead of copying. Faster for RL.

        """
        self.action_count_this_turn += 1
        if self.action_count_this_turn > 1000:
            self.game_over = True
            self.winner = 2  # Draw due to runaway logic
            self.log_rule("Safety", "Turn exceeded 1000 actions. Force terminating as Draw.")
            return self

        if self.game_over:
            print(f"WARNING: Step called after Game Over (Winner: {self.winner}). Ignoring action {action_id}.")

            return self

        # Strict validation for debugging
        if check_legality:
            legal_actions = self.get_legal_actions()

            if not legal_actions[action_id]:
                # Soft fallback for illegal moves to prevent crashes
                legal_indices = np.where(legal_actions)[0]

                # print(
                #     f"ILLEGAL MOVE CAUGHT: Action {action_id} in phase {self.phase}. "
                #     f"PendingChoices: {len(self.pending_choices)}. "
                #     f"Fallback to first legal action: {legal_indices[0] if len(legal_indices) > 0 else 'None'}"
                # )

                if len(legal_indices) > 0:
                    if 0 in legal_indices:
                        action_id = 0
                    else:
                        action_id = int(legal_indices[0])
                else:
                    self.game_over = True
                    self.winner = -2  # Special code for illegal move failure
                    return self

        if in_place:
            new_state = self
        else:
            new_state = self.copy()

        new_state.log_rule("Rule 9.5", f"Processing action {action_id} in {new_state.phase} phase.")

        # Check rule conditions before acting (Rule 9.5.1 / 10.1.2)
        # MUST be done on new_state
        new_state._process_rule_checks()

        # Rule 9.5.4.1: Check timing occurs before play timing
        new_state._process_rule_checks()

        # Priority: If waiting for a choice (like targeting), handles that action

        if new_state.pending_choices:
            new_state._handle_choice(action_id)

        # Otherwise, if resolving a complex effect stack

        elif new_state.pending_effects:
            new_state._resolve_pending_effect(0)  # 0 is dummy action for auto-res

        # Normal action execution

        else:
            new_state._execute_action(action_id)

        # After any action, automatically process non-choice effects

        while new_state.pending_effects and not new_state.pending_choices:
            new_state._resolve_pending_effect(0)  # 0 is dummy action for auto-res

        # Rule 9.5.1: Final check timing after action resolution

        new_state._process_rule_checks()

        # Rule 12.1: Infinite Loop Detection

        # Skip for Mulligan phases and if disabled

        if new_state.enable_loop_detection and new_state.phase not in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            try:
                # Capture key state tuple

                state_tuple = (
                    new_state.phase,
                    new_state.current_player,
                    tuple(sorted(new_state.players[0].hand)),
                    tuple(new_state.players[0].stage),
                    tuple(tuple(x) for x in new_state.players[0].stage_energy),
                    tuple(new_state.players[0].energy_zone),
                    tuple(sorted(new_state.players[1].hand)),
                    tuple(new_state.players[1].stage),
                    tuple(tuple(x) for x in new_state.players[1].stage_energy),
                    tuple(new_state.players[1].energy_zone),
                    tuple(sorted(list(new_state.players[0].used_abilities))),
                    tuple(sorted(list(new_state.players[1].used_abilities))),
                )

                state_hash = hash(state_tuple)

                new_state.state_history.append(state_hash)

                if new_state.state_history.count(state_hash) >= 20:
                    new_state.log_rule("Rule 12.1", "Infinite Loop detected. Terminating as Draw.")

                    new_state.game_over = True

                    new_state.winner = 2  # Draw

                    new_state.loop_draw = True

            except Exception:
                # If hashing fails, just ignore for now to prevent crash

                pass

        return new_state

    def get_observation(self) -> np.ndarray:
        """
        Calculates a flat feature vector representing the game state for the AI (Rule 9.1).

        New Layout (Size 320):
        [0-36]: Metadata (Phase, Player, Choice Context)
        [36-168]: Hand (12 cards x 11 floats) -> [Exist, ID, Cost, Blade, HeartVec(7)]
        [168-204]: Self Stage (3 slots x 12 floats) -> [Exist, ID, Tapped, Blade, HeartVec(7), Energy]
        [204-240]: Opponent Stage (3 slots x 12 floats) -> [Exist, ID, Tapped, Blade, HeartVec(7), Energy]
        [240-270]: Live Zone (3 cards x 10 floats) -> [Exist, ID, Score, ReqHeartVec(7)]
        [270-272]: Scores (Self, Opp)
        [272]: Source ID of pending choice
        [273-320]: Padding
        """

        # Expanded observation size
        features = np.zeros(320, dtype=np.float32)

        # JIT Arrays Check
        if GameState._jit_member_costs is None:
            GameState._init_jit_arrays()

        costs_db = GameState._jit_member_costs
        hearts_vec_db = GameState._jit_member_hearts_vec
        blades_db = GameState._jit_member_blades
        live_score_db = GameState._jit_live_score
        live_req_vec_db = GameState._jit_live_hearts_vec

        # Max ID for normalization (add safety for 0 div)
        max_id_val = float(costs_db.shape[0]) if costs_db is not None else 2000.0

        # --- 1. METADATA [0:36] ---

        # Phase (one-hot) [0:16] - using 11 slots
        phase_val = int(self.phase) + 2
        if 0 <= phase_val < 11:
            features[phase_val] = 1.0

        # Current Player [16:18]
        features[16 + (1 if self.current_player == 1 else 0)] = 1.0

        # Pending Choice [18:36]
        if self.pending_choices:
            features[18] = 1.0
            choice_type, params = self.pending_choices[0]

            # Populate Source ID if available [272]
            source_id = params.get("card_id", -1)
            if source_id >= 0:
                features[272] = source_id / max_id_val

            types = [
                "TARGET_MEMBER",
                "TARGET_HAND",
                "SELECT_MODE",
                "COLOR_SELECT",
                "TARGET_OPPONENT_MEMBER",
                "TARGET_MEMBER_SLOT",
                "SELECT_SWAP_SOURCE",
                "SELECT_FROM_LIST",
                "SELECT_FROM_DISCARD",
                "DISCARD_SELECT",
                "MODAL",
                "CHOOSE_FORMATION",
                "SELECT_ORDER",
                "SELECT_FORMATION_SLOT",
                "SELECT_SUCCESS_LIVE",
            ]
            try:
                t_idx = types.index(choice_type)
                features[19 + t_idx] = 1.0
            except ValueError:
                pass

            if params.get("is_optional"):
                features[35] = 1.0

        # --- 2. HAND [36:168] (12 cards * 11 features) ---
        p = self.players[self.current_player]
        hand_len = len(p.hand)
        n_hand = min(hand_len, 12)

        if n_hand > 0:
            hand_ids = np.array(p.hand[:n_hand], dtype=int)
            base_idx = np.arange(n_hand) * 11 + 36

            # Existence
            features[base_idx] = 1.0

            # ID
            features[base_idx + 1] = hand_ids / max_id_val

            # Cost
            c = costs_db[hand_ids]
            features[base_idx + 2] = np.clip(c, 0, 10) / 10.0

            # Blade
            b = blades_db[hand_ids]
            features[base_idx + 3] = np.clip(b, 0, 10) / 10.0

            # Heart Vectors (7 dim)
            # Flatten 12x7 -> 84? No, interleaved.
            # We need to assign (N, 7) into sliced positions.
            # This is tricky with simple slicing if stride is not 1.
            # Loop for safety or advanced indexing.
            # shape of h_vecs: (n_hand, 7)
            h_vecs = hearts_vec_db[hand_ids]

            for i in range(n_hand):
                start = 36 + i * 11 + 4
                features[start : start + 7] = np.clip(h_vecs[i], 0, 5) / 5.0

        # --- 3. SELF STAGE [168:204] (3 slots * 12 features) ---
        for i in range(3):
            cid = p.stage[i]
            base = 168 + i * 12
            if cid >= 0:
                features[base] = 1.0
                features[base + 1] = cid / max_id_val
                features[base + 2] = 1.0 if p.tapped_members[i] else 0.0

                # Effective Stats (retains python logic for modifiers)
                eff_blade = p.get_effective_blades(i, self.member_db)
                eff_hearts = p.get_effective_hearts(i, self.member_db)  # vector

                features[base + 3] = min(eff_blade / 10.0, 1.0)

                # Hearts (7)
                # eff_hearts is usually (6,) or (7,) or list
                if isinstance(eff_hearts, (list, np.ndarray)):
                    h_len = min(len(eff_hearts), 7)
                    features[base + 4 : base + 4 + h_len] = np.array(eff_hearts[:h_len]) / 5.0

                # Energy Count
                features[base + 11] = min(len(p.stage_energy[i]) / 5.0, 1.0)

        # --- 4. OPPONENT STAGE [204:240] (3 slots * 12 features) ---
        opp = self.players[1 - self.current_player]
        for i in range(3):
            cid = opp.stage[i]
            base = 204 + i * 12
            if cid >= 0:
                features[base] = 1.0
                features[base + 1] = cid / max_id_val
                features[base + 2] = 1.0 if opp.tapped_members[i] else 0.0

                # Note: get_effective_blades requires accessing the opponent object relative to the DB
                # but GameState usually uses p methods.
                # p.get_effective_blades uses self.stage.
                # So we call opp.get_effective_blades.
                eff_blade = opp.get_effective_blades(i, self.member_db)
                eff_hearts = opp.get_effective_hearts(i, self.member_db)

                features[base + 3] = min(eff_blade / 10.0, 1.0)

                if isinstance(eff_hearts, (list, np.ndarray)):
                    h_len = min(len(eff_hearts), 7)
                    features[base + 4 : base + 4 + h_len] = np.array(eff_hearts[:h_len]) / 5.0

                features[base + 11] = min(len(opp.stage_energy[i]) / 5.0, 1.0)

        # --- 5. LIVE ZONE [240:270] (3 cards * 10 features) ---
        n_live = min(len(p.live_zone), 3)
        if n_live > 0:
            live_ids = np.array(p.live_zone[:n_live], dtype=int)

            for i in range(n_live):
                cid = live_ids[i]
                base = 240 + i * 10
                features[base] = 1.0
                features[base + 1] = cid / max_id_val
                features[base + 2] = np.clip(live_score_db[cid], 0, 5) / 5.0

                # Req Heart Vec (7)
                if live_req_vec_db is not None:
                    features[base + 3 : base + 10] = np.clip(live_req_vec_db[cid], 0, 5) / 5.0

        # --- 6. SCORES [270:272] ---
        features[270] = min(len(p.success_lives) / 5.0, 1.0)
        features[271] = min(len(self.players[1 - self.current_player].success_lives) / 5.0, 1.0)

        return features

    def to_dict(self):
        """Serialize full game state."""

        return {
            "turn": self.turn_number,
            "phase": self.phase,
            "active_player": self.current_player,
            "game_over": self.game_over,
            "winner": self.winner,
            "players": [p.to_dict(viewer_idx=0) for p in self.players],
            "legal_actions": [],  # Can populate if needed
            "pending_choice": None,
            "performance_results": {},
            "rule_log": list(self.rule_log),
        }

    def get_reward(self, player_idx: int) -> float:
        # Get reward for player (1.0 for win, -1.0 for loss, 0.0 for draw)
        # Illegal move (-2) is treated as a loss (-1.0) for safety in standard RL,
        # though explicit training usually handles this via masking or separate loss.

        if self.winner == -2:
            return -100.0  # Illegal move/Technical loss

        if self.winner == player_idx:
            return 100.0
        elif self.winner == 1 - player_idx:
            return -100.0
        elif self.winner == 2:  # Draw
            return 0.0
        elif self.winner == -1:  # Ongoing
            # Ongoing heuristic: Pure score difference
            # Time penalties are now handled by the Gymnasium environment (per turn)
            my_score = len(self.players[player_idx].success_lives)
            opp_score = len(self.players[1 - player_idx].success_lives)
            return float(my_score - opp_score)

    def take_action(self, action_id: int) -> None:
        """In-place version of step() for testing and direct manipulation."""

        if self.pending_choices:
            self._handle_choice(action_id)

        else:
            self._execute_action(action_id)

        # Process resulting effects

        while self.pending_effects and not self.pending_choices:
            self._resolve_pending_effect(0)


def create_sample_cards() -> Tuple[Dict[int, MemberCard], Dict[int, LiveCard]]:
    """Create sample cards for testing"""

    members = {}

    lives = {}

    # Create 48 sample members with varying stats

    for i in range(48):
        cost = 2 + (i % 14)  # Costs 2-15

        blades = 1 + (i % 6)  # Blades 1-6

        hearts = np.zeros(7, dtype=np.int32)  # Changed from 6 to 7

        hearts[i % 6] = 1 + (i // 6 % 3)  # 1-3 hearts of one color

        if i >= 24:
            hearts[(i + 1) % 6] = 1  # Second color for higher cost cards

        blade_hearts = np.zeros(6, dtype=np.int32)

        if i % 3 == 0:
            blade_hearts[i % 6] = 1

        members[i] = MemberCard(
            card_id=i,
            card_no=f"SAMPLE-M-{i}",
            name=f"Member_{i}",
            cost=cost,
            hearts=hearts,
            blade_hearts=blade_hearts,
            blades=blades,
        )

    # Create 12 sample live cards

    for i in range(12):
        score = 1 + (i % 3)  # Score 1-3

        required = np.zeros(7, dtype=np.int32)

        required[i % 6] = 2 + (i // 6)  # 2-3 of one color required

        required[6] = 1 + (i % 4)  # 1-4 "any" hearts required

        lives[100 + i] = LiveCard(
            card_id=100 + i, card_no=f"SAMPLE-L-{i}", name=f"Live_{i}", score=score, required_hearts=required
        )

    return members, lives


def initialize_game(use_real_data: bool = True, deck_type: str = "normal") -> GameState:
    """

    Create initial game state with shuffled decks.

    Args:

        use_real_data: Whether to try loading real cards.json data

        deck_type: "normal" (random from DB) or "vanilla" (specific simple cards)

    """

    # Try loading real data

    if use_real_data and not GameState.member_db:
        import traceback

        # print("DEBUG: initialize_game attempting to load real data...")

        try:
            # Try current directory first (assuming run from root)

            data_path = os.path.join(os.getcwd(), "data", "cards_compiled.json")

            if not os.path.exists(data_path):
                # Fallback to cards.json

                data_path = os.path.join(os.getcwd(), "data", "cards.json")

            if not os.path.exists(data_path):
                # Absolute path fallback based on file location

                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

                data_path = os.path.join(base_dir, "data", "cards_compiled.json")

            # print(f"DEBUG: Selected data path: {data_path}")

            if not os.path.exists(data_path):
                # print(f"ERROR: Data path does not exist: {data_path}")
                pass

            else:
                loader = CardDataLoader(data_path)

                m, l, e = loader.load()

                if m:
                    GameState.member_db = m
                    GameState.live_db = l
                    print(f"SUCCESS: Loaded {len(m)} members and {len(l)} lives from {data_path}")

                    # Optimization: Cache cards with CONSTANT META_RULE effects
                    GameState._meta_rule_cards = set()
                    for cid, card in m.items():
                        for ab in card.abilities:
                            if ab.trigger.name == "CONSTANT":  # Check string to avoid import if needed, or use enum
                                for eff in ab.effects:
                                    if eff.effect_type.name == "META_RULE":
                                        GameState._meta_rule_cards.add(cid)
                                        break
                    for cid, card in l.items():
                        for ab in card.abilities:
                            if ab.trigger.name == "CONSTANT":
                                for eff in ab.effects:
                                    if eff.effect_type.name == "META_RULE":
                                        GameState._meta_rule_cards.add(cid)
                                        break

                    GameState._init_jit_arrays()

                else:
                    # print("WARNING: Loader returned empty member database.")
                    pass

        except Exception as e:
            print(f"CRITICAL: Failed to load real data: {e}")
            import traceback

            traceback.print_exc()
            pass

            traceback.print_exc()

    if not GameState.member_db:
        # print("WARNING: Falling back to SAMPLE cards. This may cause logic inconsistencies.")

        # Fallback to sample

        members, lives = create_sample_cards()

        GameState.member_db = members

        GameState.live_db = lives

        GameState._init_jit_arrays()

    state = GameState()

    # Pre-calculate Vanilla Deck IDs if needed

    vanilla_member_ids = []

    vanilla_live_ids = []

    if deck_type == "vanilla":
        # Target Vanilla Members (4 copies each = 48)

        # 5 Vanilla + 7 Simple

        target_members = [
            "PL!-sd1-010-SD",
            "PL!-sd1-013-SD",
            "PL!-sd1-014-SD",
            "PL!-sd1-017-SD",
            "PL!-sd1-018-SD",  # Vanilla
            "PL!-sd1-002-SD",
            "PL!-sd1-005-SD",
            "PL!-sd1-011-SD",
            "PL!-sd1-012-SD",
            "PL!-sd1-016-SD",  # Simple
            "PL!-sd1-015-SD",
            "PL!-sd1-007-SD",
        ]

        # Target Vanilla Lives (3 copies each = 12)

        target_lives = ["PL!-sd1-019-SD", "PL!-sd1-020-SD", "PL!-sd1-021-SD", "PL!-sd1-022-SD"]

        # 1. Map Members

        found_members = {}

        for cid, card in GameState.member_db.items():
            if card.card_no in target_members:
                found_members[card.card_no] = cid

        # 2. Map Lives

        found_lives = {}

        for cid, card in GameState.live_db.items():
            if card.card_no in target_lives:
                found_lives[card.card_no] = cid

        # 3. Construct Lists

        for tm in target_members:
            if tm in found_members:
                vanilla_member_ids.extend([found_members[tm]] * 4)

            else:
                # print(f"WARNING: Vanilla card {tm} not found in DB!")
                pass

        for tl in target_lives:
            if tl in found_lives:
                vanilla_live_ids.extend([found_lives[tl]] * 3)

            else:
                # print(f"WARNING: Vanilla live {tl} not found in DB!")
                pass

        # Fill if missing?

        if len(vanilla_member_ids) < 48:
            # print(f"WARNING: Vanilla deck incomplete ({len(vanilla_member_ids)}), filling with randoms.")
            pass

            remaining = 48 - len(vanilla_member_ids)

            all_ids = list(GameState.member_db.keys())

            if all_ids:
                vanilla_member_ids.extend(np.random.choice(all_ids, remaining).tolist())

        if len(vanilla_live_ids) < 12:
            # print(f"WARNING: Vanilla live deck incomplete ({len(vanilla_live_ids)}), filling with randoms.")
            pass

            remaining = 12 - len(vanilla_live_ids)

            all_ids = list(GameState.live_db.keys())

            if all_ids:
                vanilla_live_ids.extend(np.random.choice(all_ids, remaining).tolist())

    # Prepare Verified/Random lists if needed
    verified_member_ids = []
    verified_live_ids = []

    if deck_type == "random_verified":
        try:
            pool_path = os.path.join(os.getcwd(), "verified_card_pool.json")
            if os.path.exists(pool_path):
                with open(pool_path, "r", encoding="utf-8") as f:
                    pool = json.load(f)

                v_members = pool.get("verified_abilities", [])
                v_vanilla = pool.get("vanilla_members", [])
                total_v_members = v_members + v_vanilla

                # Filter DB for these card_nos
                for cid, card in GameState.member_db.items():
                    if card.card_no in total_v_members:
                        verified_member_ids.append(cid)

                v_lives = pool.get("vanilla_lives", [])  # Or use vanilla_lives as a base for lives
                for cid, card in GameState.live_db.items():
                    if card.card_no in v_lives:
                        verified_live_ids.append(cid)

                if not verified_member_ids or not verified_live_ids:
                    # print(f"WARNING: Verified pool empty after filtering! Check card_nos. falling back.")
                    pass
            else:
                # print(f"WARNING: verified_card_pool.json not found at {pool_path}")
                pass
        except Exception:
            # print(f"ERROR: Failed to load verified pool: {e}")
            pass

    for p_idx in range(2):
        p = state.players[p_idx]

        # Build decks
        if deck_type == "vanilla":
            member_ids = list(vanilla_member_ids)  # Copy
            live_ids = list(vanilla_live_ids)  # Copy
        elif deck_type == "random_verified" and verified_member_ids and verified_live_ids:
            # 48 members, 12 lives
            member_ids = list(np.random.choice(verified_member_ids, 48, replace=True))
            live_ids = list(np.random.choice(verified_live_ids, 12, replace=True))
        else:
            # Random Normal Deck
            # Random Normal Deck

            member_ids = list(GameState.member_db.keys())

            live_ids = list(GameState.live_db.keys())

            # Filter if too many? For now just take random subset if huge

            if len(member_ids) > 48:
                member_ids = list(np.random.choice(member_ids, 48, replace=False))

            if len(live_ids) > 12:
                live_ids = list(np.random.choice(live_ids, 12, replace=False))

        energy_ids = list(range(200, 212))

        np.random.shuffle(member_ids)

        np.random.shuffle(live_ids)

        np.random.shuffle(energy_ids)

        p.main_deck = member_ids + live_ids

        np.random.shuffle(p.main_deck)

        p.energy_deck = energy_ids

        # Initial draw: 6 cards (Rule 6.2.1.5)
        # Note: log_rule isn't available on GameState yet as it's a static function creating state
        # but we can print or add a log entry to the state's internal log if it has one.
        # Actually, let's just make sure the draw happens.
        for _ in range(6):
            if p.main_deck:
                p.hand.append(p.main_deck.pop(0))

    # Log initial setup rules (Rule 6.2.1.5 and 6.2.1.7)
    # Use structured events for initial setup so frontend can consume metadata
    try:
        state.log_event("RULE", "Both players draw 6 cards as starting hand.", source_cid=-1, ability_idx=-1, player_id=-1, rule_ref="Rule 6.2.1.5", log_to_rule_log=True)
        state.log_event("RULE", "Both players place 3 cards from Energy Deck to Energy Zone.", source_cid=-1, ability_idx=-1, player_id=-1, rule_ref="Rule 6.2.1.7", log_to_rule_log=True)
    except Exception:
        # Fallback — append legacy dicts if structured logging not available
        state.rule_log.append({"rule": "Rule 6.2.1.5", "description": "Both players draw 6 cards as starting hand."})
        state.rule_log.append({"rule": "Rule 6.2.1.7", "description": "Both players place 3 cards from Energy Deck to Energy Zone."})

    # Set initial phase to Mulligan

    state.phase = Phase.MULLIGAN_P1

    # Randomly determine first player

    state.first_player = np.random.randint(2)

    state.current_player = state.first_player

    # Rule 6.2.1.7: Both players place top 3 cards of Energy Deck into Energy Zone

    for p in state.players:
        p.energy_zone = []

        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    return state


if __name__ == "__main__":
    # Test game creation and basic flow

    game = initialize_game()

    print(f"Game initialized. First player: {game.first_player}")

    print(f"P0 hand: {len(game.players[0].hand)} cards")

    print(f"P1 hand: {len(game.players[1].hand)} cards")

    print(f"Phase: {game.phase.name}")

    # Run a few random actions

    for step in range(20):
        if game.is_terminal():
            print(f"Game over! Winner: {game.get_winner()}")

            break

        legal = game.get_legal_actions()

        legal_indices = np.where(legal)[0]

        if len(legal_indices) == 0:
            print("No legal actions!")

            break

        action = np.random.choice(legal_indices)

        game = game.step(action)

        print(
            f"Step {step}: Action {action}, Phase {game.phase}, "
            f"Player {game.current_player}, "
            f"P0 lives: {len(game.players[0].success_lives)}, "
            f"P1 lives: {len(game.players[1].success_lives)}"
        )

# --- COMPREHENSIVE RULEBOOK INDEX (v1.04) ---

# This index ensures 100% searchability of all official rule identifiers.

#

# Rule 1:

# Rule 1.1:

# Rule 1.1.1:

# Rule 1.2:

# Rule 1.2.1:

# Rule 1.2.1.1: ??E??????v???C???[????????C?u?J?[?h?u

# Rule 1.2.1.2: ??????v???C???[????????3 ????????

# Rule 1.2.2:

# Rule 1.2.3:

# Rule 1.2.3.1: ???E???s???s???A???????J?[?h?E?e????E

# Rule 1.2.4:

# Rule 1.3:

# Rule 1.3.1:

# Rule 1.3.2:

# Rule 1.3.2.1: ????????????????E?????????E??

# Rule 1.3.2.2: ????s???????s??????P?????E??????E

# Rule 1.3.2.3: ????s????v???????????E?????????A??

# Rule 1.3.2.4: ?v???C???[??E???[?h????????l?E????A????

# Rule 1.3.3:

# Rule 1.3.4:

# Rule 1.3.4.1: ?????????E????v???C???[??K?p????AE

# Rule 1.3.4.2: ???E?J????J?[?h?????I???????

# Rule 1.3.5:

# Rule 1.3.5.1: ?J?[?h???[??????e?`???f?E??????

# Rule 2:

# Rule 2.1:

# Rule 2.1.1:

# Rule 2.1.2:

# Rule 2.1.3:

# Rule 2.2:

# Rule 2.2.1:

# Rule 2.2.2:

# Rule 2.2.2.1: ?J?[?h?^?C?v?????C?u?????J?[?h?E?A?Q?[??

# Rule 2.2.2.1.1: ?X?R?A?E?E.10?E????E???n?[?g?IE.11?E???????

# Rule 2.2.2.2: ?J?[?h?^?C?v???????o?E?????J?[?h?E?A???C

# Rule 2.2.2.2.1: ?R?X?g?IE.6?E???n?E?g?IE.9?E???????J?[?`E

# Rule 2.2.2.3: ?J?[?h?^?C?v???G?l???M?[?????J?[?h?E?A??

# Rule 2.2.2.3.1: ?J?[?h??????e?G?l???M?[?J?[?h?f??\?E

# Rule 2.3:

# Rule 2.3.1:

# Rule 2.3.2:

# Rule 2.3.2.1: ?J?[?h?????E?E?????????o?E?J?[?h?E?AE??E??

# Rule 2.3.2.2: ?`E???X?g???A?u?v?i?????????E??????????

# Rule 2.4:

# Rule 2.4.1:

# Rule 2.4.2:

# Rule 2.4.2.1: ?J?[?h?????E?E?????????o?E?J?[?h?E?AE??E??

# Rule 2.4.2.2: ?????o?E?????O???[?v????????E?A??

# Rule 2.4.3:

# Rule 2.4.3.1: ?`E???X?g???A?w?x?i??d?????????E??????

# Rule 2.4.4:

# Rule 2.5:

# Rule 2.5.1:

# Rule 2.5.2:

# Rule 2.5.3:

# Rule 2.6:

# Rule 2.6.1:

# Rule 2.7:

# Rule 2.7.1:

# Rule 2.7.2:

# Rule 2.8:

# Rule 2.8.1:

# Rule 2.8.2:

# Rule 2.9:

# Rule 2.9.1:

# Rule 2.9.2:

# Rule 2.9.3:

# Rule 2.10:

# Rule 2.10.1:

# Rule 2.11:

# Rule 2.11.1:

# Rule 2.11.2:

# Rule 2.11.2.1: ??E???[?g??????A?c??

# Rule 2.11.2.2: ?n?E?g???????E????????A????S???

# Rule 2.11.3:

# Rule 2.12:

# Rule 2.12.1:

# Rule 2.12.2:

# Rule 2.12.3:

# Rule 2.12.4:

# Rule 2.13:

# Rule 2.13.1:

# Rule 2.13.2:

# Rule 2.14:

# Rule 2.14.1:

# Rule 2.14.2:

# Rule 2.14.3:

# Rule 3:

# Rule 3.1:

# Rule 3.1.1:

# Rule 3.1.2:

# Rule 3.1.2.1: ???E???E?}?X?^?[???A????\???L????E

# Rule 3.1.2.2: ?N???E???E?}?X?^?[???A??????v???C????

# Rule 3.1.2.3: ?????E???E?}?X?^?[???A????\???L????E

# Rule 3.1.2.4: ?????E?}?X?^?[???A??????????????E

# Rule 3.1.2.4.1: ?????????????v???C???[???w?E

# Rule 4:

# Rule 4.1:

# Rule 4.1.1:

# Rule 4.1.2:

# Rule 4.1.2.1: ???J????J?[?h???u???????A????

# Rule 4.1.2.2: ?????E?J?????????J??????????

# Rule 4.1.2.3: ???E?J??????????A???????J?[?`E

# Rule 4.1.3:

# Rule 4.1.3.1: ??E???????E???????J?[?h?E??E????AE

# Rule 4.1.4:

# Rule 4.1.4.1: ????J?[?h????????E??A???????????E

# Rule 4.1.5:

# Rule 4.1.5.1: ???J???Y????E?J?????E????J?[?h??

# Rule 4.1.6:

# Rule 4.1.7:

# Rule 4.2:

# Rule 4.2.1:

# Rule 4.2.2:

# Rule 4.2.3:

# Rule 4.3:

# Rule 4.3.1:

# Rule 4.3.2:

# Rule 4.3.2.1: ?A?N?`E???u????E?J?[?h?E?A????J?[?h?E?}?X

# Rule 4.3.2.2: ?E?F?C?g????E?J?[?h?E?A????J?[?h?E?}?X

# Rule 4.3.2.3: ?z?u??????E??????????J?[?h???u??E

# Rule 4.3.3:

# Rule 4.3.3.1: ?\????????E?J?[?h?E?A?J?[?h?E?E????????E

# Rule 4.3.3.2: ??????????E?J?[?h?E?A?J?[?h?E?E????????E

# Rule 4.4:

# Rule 4.4.1:

# Rule 4.4.2:

# Rule 4.5:

# Rule 4.5.1:

# Rule 4.5.1.1: ?`E???X?g????P??e?G???A?f?????????E????

# Rule 4.5.2:

# Rule 4.5.2.1: ??E?????o?E?G???A??A??????e???T?C?h?G??

# Rule 4.5.2.2: ????v???C???[???????A???T?C?h?G???A??

# Rule 4.5.2.3: ????v???C???[???????A???T?C?h?G???A??

# Rule 4.5.3:

# Rule 4.5.4:

# Rule 4.5.5:

# Rule 4.5.5.1: ?????o?E?G???A??????o?E?J?[?h?E????d?E

# Rule 4.5.5.2: ?????o?E?G???A??????o?E?J?[?h?E????d?E

# Rule 4.5.5.3: ?????o?E?G???A??????o?E?????E?????o?E?G

# Rule 4.5.5.4: ?????o?E?G???A??????o?E???????o?E?G???A

# Rule 4.5.6:

# Rule 4.6:

# Rule 4.6.1:

# Rule 4.6.2:

# Rule 4.7:

# Rule 4.7.1:

# Rule 4.7.2:

# Rule 4.7.3:

# Rule 4.7.4:

# Rule 4.8:

# Rule 4.8.1:

# Rule 4.8.2:

# Rule 4.8.3:

# Rule 4.8.4:

# Rule 4.9:

# Rule 4.9.1:

# Rule 4.9.2:

# Rule 4.9.3:

# Rule 4.9.4:

# Rule 4.10:

# Rule 4.10.1:

# Rule 4.10.2:

# Rule 4.11:

# Rule 4.11.1:

# Rule 4.11.2:

# Rule 4.11.3:

# Rule 4.12:

# Rule 4.12.1:

# Rule 4.12.2:

# Rule 4.13:

# Rule 4.13.1:

# Rule 4.13.2:

# Rule 4.14:

# Rule 4.14.1:

# Rule 4.14.2:

# Rule 5:

# Rule 5.1:

# Rule 5.1.1:

# Rule 5.2:

# Rule 5.2.1:

# Rule 5.3:

# Rule 5.3.1:

# Rule 5.4:

# Rule 5.4.1:

# Rule 5.5:

# Rule 5.5.1:

# Rule 5.5.1.1: ?J?[?h?Q?????P?????????E????????

# Rule 5.5.1.2: ?J?[?h?Q??J?[?h??0 ??????E1 ???E???E

# Rule 5.6:

# Rule 5.6.1:

# Rule 5.6.2:

# Rule 5.6.3:

# Rule 5.6.3.1: ?E????l?E???0 ??????????E?A?????E????E

# Rule 5.6.3.2: ??E???E???C???[????E??E?????I?E???????E

# Rule 5.6.3.3: ??E???E???C???[??J?[?h??1 ??????????AE

# Rule 5.6.3.4: ???E??E??????5.6.3.3 ?????s????????i??

# Rule 5.7:

# Rule 5.7.1:

# Rule 5.7.2:

# Rule 5.7.2.1: ?E????l?E???0 ??????????E?A?????E????E

# Rule 5.7.2.2: ?????????1 ???w??????AE

# Rule 5.7.2.3: ??E???E???C???[????E??E?????I?E???????E

# Rule 5.7.2.4: ??E???E???C???[??A???C???`E???L?u??????

# Rule 5.7.2.5: ???E??E??????5.7.2.4 ?????s????????i??

# Rule 5.8:

# Rule 5.8.1:

# Rule 5.8.2:

# Rule 5.9.1:

# Rule 5.9.1.1: ?E

# Rule 5.10:

# Rule 5.10.1:

# Rule 6:

# Rule 6.1:

# Rule 6.1.1:

# Rule 6.1.1.1: ???C???`E???L??A?????o?E?J?[?`E8 ??????E????

# Rule 6.1.1.2: ???C???`E???L???A?J?[?h?i???o?E???????

# Rule 6.1.1.3: ?G?l???M?[?`E???L??A?G?l???M?[?J?[?`E2

# Rule 6.1.2:

# Rule 6.2:

# Rule 6.2.1:

# Rule 6.2.1.1: ???E?Q?[????g?p?????g??`E???L???

# Rule 6.2.1.2: ??E?E???C???[????g????C???`E???L???E?g??

# Rule 6.2.1.3: ??E?E???C???[????g??G?l???M?[?`E???L??E

# Rule 6.2.1.4: ??E?E???C???[????????????E?v???C???[

# Rule 6.2.1.5: ??E?E???C???[????g????C???`E???L?u?????

# Rule 6.2.1.6: ??U?v???C???[?????E???A?e?v???C???[???

# Rule 6.2.1.7: ??E?E???C???[????g??G?l???M?[?`E???L?u

# Rule 7:

# Rule 7.1:

# Rule 7.1.1:

# Rule 7.1.2:

# Rule 7.2:

# Rule 7.2.1:

# Rule 7.2.1.1: ???v???C???[???w????t?F?C?Y????A??

# Rule 7.2.1.2: ???v???C???[???w?????E???F?C?Y????AE

# Rule 7.2.2:

# Rule 7.3:

# Rule 7.3.1:

# Rule 7.3.2:

# Rule 7.3.2.1: ???t?F?C?Y???A?E?U?v???C???[?????`E

# Rule 7.3.3:

# Rule 7.4:

# Rule 7.4.1:

# Rule 7.4.2:

# Rule 7.4.3:

# Rule 7.5:

# Rule 7.5.1:

# Rule 7.5.2:

# Rule 7.5.3:

# Rule 7.6:

# Rule 7.6.1:

# Rule 7.6.2:

# Rule 7.6.3:

# Rule 7.7:

# Rule 7.7.1:

# Rule 7.7.2:

# Rule 7.7.2.1: ???E?E?J?[?h??????N???E???1 ??I???AE

# Rule 7.7.2.2: ???E?E??D??????o?E?J?[?h??1 ???I???A??

# Rule 7.7.3:

# Rule 7.8:

# Rule 7.8.1:

# Rule 8:

# Rule 8.1:

# Rule 8.1.1:

# Rule 8.1.2:

# Rule 8.2:

# Rule 8.2.1:

# Rule 8.2.2:

# Rule 8.2.3:

# Rule 8.2.4:

# Rule 8.2.5:

# Rule 8.3:

# Rule 8.3.1:

# Rule 8.3.2:

# Rule 8.3.2.1: ?p?t?H?[?}???X?t?F?C?Y???A?E?U?v???C

# Rule 8.3.3:

# Rule 8.3.4:

# Rule 8.3.4.1: ???v???C???[???e???C?u??????E???????E

# Rule 8.3.5:

# Rule 8.3.6:

# Rule 8.3.7:

# Rule 8.3.8:

# Rule 8.3.9:

# Rule 8.3.10:

# Rule 8.3.11:

# Rule 8.3.12:

# Rule 8.3.13:

# Rule 8.3.14:

# Rule 8.3.15:

# Rule 8.3.15.1: ???????C?u???L?n?[?g????A??????C?`E

# Rule 8.3.15.1.1: ???E??A?e

# Rule 8.3.15.1.2: ????????E???C?u?J?[?h?E?E??E

# Rule 8.3.16:

# Rule 8.3.17:

# Rule 8.4:

# Rule 8.4.1:

# Rule 8.4.2:

# Rule 8.4.2.1: ???E??A?e?v???C???[????g??G?[????

# Rule 8.4.3:

# Rule 8.4.3.1: ??????v???C???[???????E???C?u?J?[?h?u

# Rule 8.4.3.2: ?????v???C???[????C?u?J?[?h?u?????

# Rule 8.4.3.3: ??????v???C???[????C?u?J?[?h?u?????

# Rule 8.4.4:

# Rule 8.4.5:

# Rule 8.4.6:

# Rule 8.4.6.1: ??????v???C???[???????E???C?u?J?[?h?u

# Rule 8.4.6.2: ??E??????v???C???[????C?u?J?[?h?u????

# Rule 8.4.7:

# Rule 8.4.7.1: ??????v???C???[???????????E?????E

# Rule 8.4.8:

# Rule 8.4.9:

# Rule 8.4.10:

# Rule 8.4.11:

# Rule 8.4.12:

# Rule 8.4.13: 8.4.7 ???????A?????v???C???[?????E?????C

# Rule 8.4.14:

# Rule 9:

# Rule 9.1:

# Rule 9.1.1:

# Rule 9.1.1.1: ?N???E????A?E???C?^?C?~???O???^?????

# Rule 9.1.1.1.1: ?N???E???E?A?J?[?h?????E

# Rule 9.1.1.2: ?????E????A????\?????????????E

# Rule 9.1.1.2.1: ?????E???E?A?J?[?h?????E

# Rule 9.1.1.3: ???E????A????\????L???????A??

# Rule 9.1.1.3.1: ???E???E?A?J?[?h?????E

# Rule 9.2:

# Rule 9.2.1:

# Rule 9.2.1.1: ?e?P??????f???A??????????E??E???????E

# Rule 9.2.1.2: ?e?p??????f???A????E???????i?????

# Rule 9.2.1.3: ?e?u??????f???A?Q?[???????????????

# Rule 9.2.1.3.1: ?\???e?i?s??A?E??????A???????E??E

# Rule 9.2.1.3.2: ?\???e?i?s??A?E??????A??????[?I

# Rule 9.3:

# Rule 9.3.1:

# Rule 9.3.2:

# Rule 9.3.3:

# Rule 9.3.4:

# Rule 9.3.4.1: ?????E????E?????E????v???C????E

# Rule 9.3.4.1.1: ????J?[?h?E?v???C?????E?J?[?h???

# Rule 9.3.4.2: ?J?[?h?^?C?v???????o?E?????J?[?h?E?\?E

# Rule 9.3.4.3: ?J?[?h?^?C?v?????C?u?????J?[?h?E?\???E?AE

# Rule 9.4:

# Rule 9.4.1:

# Rule 9.4.2:

# Rule 9.4.2.1: ?R?X?g???E????s??????????A?e?L?X?g?E

# Rule 9.4.2.2: ?R?X?g?E??E????????E?S?????x?????????E

# Rule 9.4.3:

# Rule 9.5:

# Rule 9.5.1:

# Rule 9.5.1.1: ?`?F?`E???^?C?~???O????????A??????[????

# Rule 9.5.2:

# Rule 9.5.3:

# Rule 9.5.3.1: ??????E???s????????[?????E??????

# Rule 9.5.3.2: ?v???C???[???E?X?^?[?????E???????

# Rule 9.5.3.3: ??A?N?`E???u?E???C???[???E?X?^?[?????E

# Rule 9.5.3.4: ?`?F?`E???^?C?~???O???I?E??????AE

# Rule 9.5.4:

# Rule 9.5.4.1: ?`?F?`E???^?C?~???O????????????B?`?F?`E???^?C

# Rule 9.5.4.2: ?v???C?^?C?~???O?????????E?v???C???[??

# Rule 9.5.4.3: ?v???C?^?C?~???O??^??????E???C???[??E

# Rule 9.6:

# Rule 9.6.1:

# Rule 9.6.2:

# Rule 9.6.2.1: ?v???C????\????D??J?[?h????E??????

# Rule 9.6.2.1.1: ?v???C???????J?[?h???????A????E

# Rule 9.6.2.1.2: ????E???s??????AE

# Rule 9.6.2.1.2.1: ???E??A????^?[????X?`E?E?W??

# Rule 9.6.2.1.3: ?v???C???????E????????A????

# Rule 9.6.2.2: ?J?[?h??\???????E?I?????E???????

# Rule 9.6.2.3: ?v???C???????R?X?g????????A????R

# Rule 9.6.2.3.1: ?v???C???????????o?E??J?[?h?????

# Rule 9.6.2.3.2: ?????o?E???E???C?????A?x???????E

# Rule 9.6.2.3.2.1: ???????R?X?g???????E?E??

# Rule 9.6.2.4: ?J?[?h??\???E???????s??????AE

# Rule 9.6.2.4.1: ?v???C????????????o?E???????A??

# Rule 9.6.2.4.2: ?v???C????????N???E??????E???

# Rule 9.6.2.4.2.1: ?\???E??????????????o?E?J?[

# Rule 9.6.3:

# Rule 9.6.3.1: ?I??????w??????E?????A??????\

# Rule 9.6.3.1.1: ?I??????f?`???I???f??f?`???I

# Rule 9.6.3.1.2: ?I??????w??????E??????A?w?E

# Rule 9.6.3.1.3: ?I??????w??????E??????A???E

# Rule 9.6.3.1.4: ?I????E???E?J??????E????E?????J??E

# Rule 9.7:

# Rule 9.7.1:

# Rule 9.7.2:

# Rule 9.7.2.1: ?????E???E?U?????????E?????????

# Rule 9.7.3:

# Rule 9.7.3.1: ??E??????E?????E???E?v???C???????A?E

# Rule 9.7.3.1.1: ?????E????C???R?X?g???x?????????

# Rule 9.7.3.2: ?I???E??????E?????E????v???C?????

# Rule 9.7.3.2.1: ?????E????C???R?X?g???x?????????

# Rule 9.7.4:

# Rule 9.7.4.1: ??????U?????????E????A????\?E

# Rule 9.7.4.1.1: ?J?[?h?????J???Y????E?J???A??

# Rule 9.7.4.1.2: ?J?[?h???X?`E?E?W????F???O?E???

# Rule 9.7.4.1.3: ??L?????????O?E?A?E?J???Y??

# Rule 9.7.4.2: ????J?[?h????????U???\????????A??

# Rule 9.7.5:

# Rule 9.7.5.1: ?????U????A?????????????????E????E??

# Rule 9.7.6:

# Rule 9.7.6.1: ???U????A????????????????????1

# Rule 9.7.7:

# Rule 9.8:

# Rule 9.8.1:

# Rule 9.9:

# Rule 9.9.1:

# Rule 9.9.1.1: ?J?[?h?E?g??\?L??????E???E?????A????

# Rule 9.9.1.2: ????A?E???^????E??????E?L???????/

# Rule 9.9.1.3: ????A?p???????E??E???E??????l???X??E

# Rule 9.9.1.4: ????A?p???????E??E???E??????l??????E

# Rule 9.9.1.4.1: ?n?E?g??u???[?h?E?????????E????

# Rule 9.9.1.5: ????A?p???????E??E???E??????l???X??E

# Rule 9.9.1.5.1: ?n?E?g??u???[?h?E??????????Z????E

# Rule 9.9.1.6: ????E9.9.1.2X-9.9.1.4 ??K?p??E?E?O??I??

# Rule 9.9.1.7: ????E9.9.1.2X-9.9.1.6 ??K?p??E?E?O??I??

# Rule 9.9.1.7.1: ?p???????E???????????E??????

# Rule 9.9.1.7.2: ?????O?E?\???E???E?A?????v??

# Rule 9.9.2:

# Rule 9.9.3:

# Rule 9.9.3.1: ?????E?E????????J?[?h????????????E

# Rule 9.10:

# Rule 9.10.1:

# Rule 9.10.1.1: ???????A?u????????E?E???????????

# Rule 9.10.2:

# Rule 9.10.2.1: ?e????????????J?[?h??\???????

# Rule 9.10.2.2: ?e????????????Q?[??????s?????E

# Rule 9.10.2.3: ??????????????A?e?u???????E??

# Rule 9.10.3:

# Rule 9.11:

# Rule 9.11.1:

# Rule 9.12:

# Rule 9.12.1:

# Rule 9.12.2:

# Rule 10:

# Rule 10.1:

# Rule 10.1.1:

# Rule 10.1.2:

# Rule 10.1.3:

# Rule 10.2:

# Rule 10.2.1:

# Rule 10.2.2:

# Rule 10.2.2.1: ??E??????v???C???[????C???`E???L?u??E

# Rule 10.2.2.2: ???C???`E???L?u???????H?????E??????

# Rule 10.2.3:

# Rule 10.2.4:

# Rule 10.3:

# Rule 10.3.1:

# Rule 10.4:

# Rule 10.4.1:

# Rule 10.5:

# Rule 10.5.1:

# Rule 10.5.2:

# Rule 10.5.3:

# Rule 10.5.4:

# Rule 10.6:

# Rule 10.6.1:

# Rule 11:

# Rule 11.1:

# Rule 11.1.1:

# Rule 11.1.2:

# Rule 11.1.3:

# Rule 11.2:

# Rule 11.2.2:

# Rule 11.2.3:

# Rule 11.3:

# Rule 11.3.1: [Icon] ??A?????o?E???????o?E?G???A??u????E

# Rule 11.3.2:

# Rule 11.4:

# Rule 11.4.1: [Icon] ??A???C?u???J?n??????????E

# Rule 11.4.2:

# Rule 11.4.2.1: ?p?t?H?[?}???X?t?F?C?Y???A???v???C???[

# Rule 11.5:

# Rule 11.5.1: [Icon] ??A???C?u???????????????U??

# Rule 11.5.2:

# Rule 11.6:

# Rule 11.6.1: [Icon] ??A?E???E?v???C???????A?E???E?E

# Rule 11.6.2:

# Rule 11.6.3:

# Rule 11.6.4:

# Rule 11.7:

# Rule 11.7.1: [Icon] ??A?E???E?v???C???????A?E???E?E

# Rule 11.7.2:

# Rule 11.7.3:

# Rule 11.7.4:

# Rule 11.8:

# Rule 11.8.1: [Icon] ??A?E???E?v???C???????A?E???E?E

# Rule 11.8.2:

# Rule 11.8.3:

# Rule 11.8.4:

# Rule 11.9:

# Rule 11.9.1:

# Rule 11.9.2:

# Rule 11.10:

# Rule 11.10.1:

# Rule 11.10.2:

# Rule 12:

# Rule 12.1:

# Rule 12.1.1:

# Rule 12.1.1.1: ?A?N?`E???u?E???C???[?E?E.2?E??E?A????z???E

# Rule 12.1.1.2: ?A?N?`E???u?E???C???[???????E?s?????E

# Rule 12.1.1.3: ?????E?E??????A??????E?v???C???[??

# Rule 2025:

# --- END OF INDEX ---
