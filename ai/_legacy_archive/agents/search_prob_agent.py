from typing import List

import numpy as np

from ai.agents.agent_base import Agent
from engine.game.enums import Phase as PhaseEnum
from engine.game.game_state import GameState

try:
    from numba import njit

    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    # Mock njit decorator if numba is missing
    def njit(f):
        return f


@njit
def _check_meet_jit(hearts, req):
    """Greedy heart requirement check matching engine logic - Optimized."""
    # 1. Match specific colors (0-5)
    needed_specific = req[:6]
    have_specific = hearts[:6]

    # Numba doesn't support np.minimum for arrays in all versions efficiently, doing manual element-wise
    used_specific = np.zeros(6, dtype=np.int32)
    for i in range(6):
        if needed_specific[i] < have_specific[i]:
            used_specific[i] = needed_specific[i]
        else:
            used_specific[i] = have_specific[i]

    remaining_req_0 = req[0] - used_specific[0]
    remaining_req_1 = req[1] - used_specific[1]
    remaining_req_2 = req[2] - used_specific[2]
    remaining_req_3 = req[3] - used_specific[3]
    remaining_req_4 = req[4] - used_specific[4]
    remaining_req_5 = req[5] - used_specific[5]

    temp_hearts_0 = hearts[0] - used_specific[0]
    temp_hearts_1 = hearts[1] - used_specific[1]
    temp_hearts_2 = hearts[2] - used_specific[2]
    temp_hearts_3 = hearts[3] - used_specific[3]
    temp_hearts_4 = hearts[4] - used_specific[4]
    temp_hearts_5 = hearts[5] - used_specific[5]

    # 2. Match Any requirement (index 6) with remaining specific hearts
    needed_any = req[6]
    have_any_from_specific = (
        temp_hearts_0 + temp_hearts_1 + temp_hearts_2 + temp_hearts_3 + temp_hearts_4 + temp_hearts_5
    )

    used_any_from_specific = needed_any
    if have_any_from_specific < needed_any:
        used_any_from_specific = have_any_from_specific

    # 3. Match remaining Any with Any (Wildcard) hearts (index 6)
    needed_any -= used_any_from_specific
    have_wild = hearts[6]

    used_wild = needed_any
    if have_wild < needed_any:
        used_wild = have_wild

    # Check if satisfied
    if remaining_req_0 > 0:
        return False
    if remaining_req_1 > 0:
        return False
    if remaining_req_2 > 0:
        return False
    if remaining_req_3 > 0:
        return False
    if remaining_req_4 > 0:
        return False
    if remaining_req_5 > 0:
        return False

    if (needed_any - used_wild) > 0:
        return False

    return True


@njit
def _run_sampling_jit(stage_hearts, deck_ids, global_matrix, num_yells, total_req, samples):
    # deck_ids: array of card Base IDs (ints)
    # global_matrix: (MAX_ID+1, 7) array of hearts

    success_count = 0
    deck_size = len(deck_ids)

    # Fix for empty deck case
    if deck_size == 0:
        if _check_meet_jit(stage_hearts, total_req):
            return float(samples)
        else:
            return 0.0

    sample_size = num_yells
    if sample_size > deck_size:
        sample_size = deck_size

    # Create an index array for shuffling
    indices = np.arange(deck_size)

    for _ in range(samples):
        # Fisher-Yates shuffle for first N elements
        # Reuse existing indices array logic
        for i in range(sample_size):
            j = np.random.randint(i, deck_size)
            # Swap
            temp = indices[i]
            indices[i] = indices[j]
            indices[j] = temp

        # Sum selected hearts using indirect lookup
        simulated_hearts = stage_hearts.copy()

        for k in range(sample_size):
            idx = indices[k]
            card_id = deck_ids[idx]

            # Simple bounds check if needed, but assuming valid IDs
            # Numba handles array access fast
            # Unrolling 7 heart types
            simulated_hearts[0] += global_matrix[card_id, 0]
            simulated_hearts[1] += global_matrix[card_id, 1]
            simulated_hearts[2] += global_matrix[card_id, 2]
            simulated_hearts[3] += global_matrix[card_id, 3]
            simulated_hearts[4] += global_matrix[card_id, 4]
            simulated_hearts[5] += global_matrix[card_id, 5]
            simulated_hearts[6] += global_matrix[card_id, 6]

        if _check_meet_jit(simulated_hearts, total_req):
            success_count += 1

    return success_count / samples


class YellOddsCalculator:
    """
    Calculates the probability of completing a set of lives given a known (but unordered) deck.
    Optimized with Numba if available using Indirect Lookup.
    """

    def __init__(self, member_db, live_db):
        self.member_db = member_db
        self.live_db = live_db

        # Pre-compute global heart matrix for fast lookup
        if self.member_db:
            max_id = max(self.member_db.keys())
        else:
            max_id = 0

        # Shape: (MaxID + 1, 7)
        # We need to ensure it's contiguous and int32
        self.global_heart_matrix = np.zeros((max_id + 1, 7), dtype=np.int32)

        for mid, member in self.member_db.items():
            self.global_heart_matrix[mid] = member.blade_hearts.astype(np.int32)

        # Ensure it's ready for Numba
        if HAS_NUMBA:
            self.global_heart_matrix = np.ascontiguousarray(self.global_heart_matrix)

    def calculate_odds(
        self, deck_cards: List[int], stage_hearts: np.ndarray, live_ids: List[int], num_yells: int, samples: int = 150
    ) -> float:
        if not live_ids:
            return 1.0

        # Pre-calculate requirements
        total_req = np.zeros(7, dtype=np.int32)
        for live_id in live_ids:
            base_id = live_id & 0xFFFFF
            if base_id in self.live_db:
                total_req += self.live_db[base_id].required_hearts

        # Optimization: Just convert deck to IDs. No object lookups.
        # Mask out extra bits to get Base ID
        # Vectorized operation if deck_cards was numpy, but it's list.
        # List comprehension is reasonably fast for small N (~50).
        deck_ids_list = [c & 0xFFFFF for c in deck_cards]
        deck_ids = np.array(deck_ids_list, dtype=np.int32)

        # Use JITted function
        if HAS_NUMBA:
            # Ensure contiguous arrays
            stage_hearts_c = np.ascontiguousarray(stage_hearts, dtype=np.int32)
            return _run_sampling_jit(stage_hearts_c, deck_ids, self.global_heart_matrix, num_yells, total_req, samples)
        else:
            return _run_sampling_jit(stage_hearts, deck_ids, self.global_heart_matrix, num_yells, total_req, samples)

    def check_meet(self, hearts: np.ndarray, req: np.ndarray) -> bool:
        """Legacy wrapper for tests."""
        return _check_meet_jit(hearts, req)


class SearchProbAgent(Agent):
    """
    AI that uses Alpha-Beta search for decisions and sampling for probability.
    Optimizes for Expected Value (EV) = P(Success) * Score.
    """

    def __init__(self, depth=2, beam_width=5):
        self.depth = depth
        self.beam_width = beam_width
        self.calculator = None
        self._last_state_id = None
        self._action_cache = {}

    def get_calculator(self, state: GameState):
        if self.calculator is None:
            self.calculator = YellOddsCalculator(state.member_db, state.live_db)
        return self.calculator

    def evaluate_state(self, state: GameState, player_id: int) -> float:
        if state.game_over:
            if state.winner == player_id:
                return 10000.0
            if state.winner >= 0:
                return -10000.0
            return 0.0

        p = state.players[player_id]
        opp = state.players[1 - player_id]

        score = 0.0

        # 1. Guaranteed Score (Successful Lives)
        score += len(p.success_lives) * 1000.0
        score -= len(opp.success_lives) * 800.0

        # 2. Board Presence (Members on Stage) - HIGH PRIORITY
        stage_member_count = sum(1 for cid in p.stage if cid >= 0)
        score += stage_member_count * 150.0  # Big bonus for having members on stage

        # 3. Board Value (Hearts and Blades from members on stage)
        total_blades = 0
        total_hearts = np.zeros(7, dtype=np.int32)
        for i, cid in enumerate(p.stage):
            if cid >= 0:
                base_id = cid & 0xFFFFF
                if base_id in state.member_db:
                    member = state.member_db[base_id]
                    total_blades += member.blades
                    total_hearts += member.hearts

        score += total_blades * 80.0
        score += np.sum(total_hearts) * 40.0

        # 4. Expected Score from Pending Lives
        target_lives = list(p.live_zone)
        if target_lives and total_blades > 0:
            calc = self.get_calculator(state)
            prob = calc.calculate_odds(p.main_deck, total_hearts, target_lives, total_blades)
            potential_score = sum(
                state.live_db[lid & 0xFFFFF].score for lid in target_lives if (lid & 0xFFFFF) in state.live_db
            )
            score += prob * potential_score * 500.0
            if prob > 0.9:
                score += 500.0

        # 5. Resources
        # Diminishing returns for hand size to prevent hoarding
        hand_val = len(p.hand)
        if hand_val > 8:
            score += 80.0 + (hand_val - 8) * 1.0  # Very small bonus for cards beyond 8
        else:
            score += hand_val * 10.0

        score += p.count_untapped_energy() * 10.0
        score -= len(opp.hand) * 5.0

        return score

    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]

        if len(legal_indices) == 1:
            return int(legal_indices[0])

        # Skip search for simple phases
        if state.phase not in (PhaseEnum.MAIN, PhaseEnum.LIVE_SET):
            return int(np.random.choice(legal_indices))

        # Alpha-Beta Search for Main Phase
        best_action = legal_indices[0]
        best_val = -float("inf")
        alpha = -float("inf")
        beta = float("inf")

        # Limit branching factor for performance
        candidates = list(legal_indices)
        if len(candidates) > 15:
            # Better heuristic: prioritize Play/Live/Activate over others
            def action_priority(idx):
                if 1 <= idx <= 180:
                    return 0  # Play Card
                if 400 <= idx <= 459:
                    return 1  # Live Set
                if 200 <= idx <= 202:
                    return 2  # Activate Ability
                if idx == 0:
                    return 5  # Pass (End Phase)
                if 900 <= idx <= 902:
                    return -1  # Performance (High Priority)
                return 10  # Everything else (choices, target selection etc)

            candidates.sort(key=action_priority)
            candidates = candidates[:15]
            if 0 not in candidates and 0 in legal_indices:
                candidates.append(0)

        for action in candidates:
            try:
                ns = state.copy()
                ns = ns.step(action)

                while ns.pending_choices and ns.current_player == player_id:
                    ns = ns.step(self._greedy_choice(ns))

                val = self._minimax(ns, self.depth - 1, alpha, beta, False, player_id)

                if val > best_val:
                    best_val = val
                    best_action = action

                alpha = max(alpha, val)
            except Exception:
                continue

        return int(best_action)

    def _minimax(
        self, state: GameState, depth: int, alpha: float, beta: float, is_max: bool, original_player: int
    ) -> float:
        if depth == 0 or state.game_over:
            return self.evaluate_state(state, original_player)

        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if not legal_indices.any():
            return self.evaluate_state(state, original_player)

        # Optimization: Only search if it's still original player's turn or transition
        # If it's opponent's turn, we can either do a full minimax or just use a fixed heuristic
        # for their move. Let's do simple minimax.

        current_is_max = state.current_player == original_player

        candidates = list(legal_indices)
        if len(candidates) > 8:
            indices = np.random.choice(legal_indices, 8, replace=False)
            candidates = list(indices)
            if 0 in legal_indices and 0 not in candidates:
                candidates.append(0)

        if current_is_max:
            max_eval = -float("inf")
            for action in candidates:
                try:
                    ns = state.copy().step(action)
                    while ns.pending_choices and ns.current_player == state.current_player:
                        ns = ns.step(self._greedy_choice(ns))
                    eval = self._minimax(ns, depth - 1, alpha, beta, False, original_player)
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha:
                        break
                except:
                    continue
            return max_eval
        else:
            min_eval = float("inf")
            # For simplicity, if it's opponent's turn, maybe just assume they pass if we are deep enough
            # or use a very shallow search.
            for action in candidates:
                try:
                    ns = state.copy().step(action)
                    while ns.pending_choices and ns.current_player == state.current_player:
                        ns = ns.step(self._greedy_choice(ns))
                    eval = self._minimax(ns, depth - 1, alpha, beta, True, original_player)
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha:
                        break
                except:
                    continue
            return min_eval

    def _greedy_choice(self, state: GameState) -> int:
        """Fast greedy resolution for pending choices during search."""
        mask = state.get_legal_actions()
        indices = np.where(mask)[0]
        if not indices.any():
            return 0

        # Simple priority: 1. Keep high cost (if mulligan), 2. Target slot 1, etc.
        # For now, just pick the first valid action
        return int(indices[0])
