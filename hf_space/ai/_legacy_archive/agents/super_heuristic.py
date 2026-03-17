import random

import numpy as np

from ai.headless_runner import Agent
from engine.game.game_state import GameState, Phase


class SuperHeuristicAgent(Agent):
    """
    "Really Smart" heuristic AI that uses Beam Search and a comprehensive
    evaluation function to look ahead and maximize advantage.
    """

    def __init__(self, depth=2, beam_width=3):
        self.depth = depth
        self.beam_width = beam_width
        self.last_turn_num = -1

    def evaluate_state(self, state: GameState, player_id: int) -> float:
        """
        Global evaluation function for a game state state from player_id's perspective.
        Higher is better.
        """
        if state.game_over:
            if state.winner == player_id:
                return 100000.0
            elif state.winner >= 0:
                return -100000.0
            else:
                return 0.0  # Draw

        p = state.players[player_id]
        opp = state.players[1 - player_id]

        score = 0.0

        # --- 1. Score Advantage ---
        my_score = len(p.success_lives)
        opp_score = len(opp.success_lives)
        # Drastically increase score weight to prioritize winning
        score += my_score * 50000.0
        score -= opp_score * 40000.0  # Slightly less penalty (aggressive play)

        # --- 2. Live Progress (The "Closeness" to performing a live) ---
        # Analyze lives in Live Zone
        stage_hearts = p.get_total_hearts(state.member_db)

        # Calculate pending requirement for existing lives
        pending_req = np.zeros(7, dtype=np.int32)
        for live_id in p.live_zone:
            if live_id in state.live_db:
                pending_req += state.live_db[live_id].required_hearts

        # Calculate how "fulfilled" the pending requirement is
        fulfilled_val = 0

        # Colors
        rem_hearts = stage_hearts.copy()
        rem_req = pending_req.copy()

        for c in range(6):
            matched = min(rem_hearts[c], rem_req[c])
            fulfilled_val += matched * 300  # VERY High value for matching needed colors
            rem_hearts[c] -= matched
            rem_req[c] -= matched

        # Any
        needed_any = rem_req[6] if len(rem_req) > 6 else 0
        avail_any = np.sum(rem_hearts)
        matched_any = min(avail_any, needed_any)
        fulfilled_val += matched_any * 200

        score += fulfilled_val

        # Penalize unmet requirements (Distance to goal)
        unmet_hearts = np.sum(rem_req[:6]) + max(0, needed_any - avail_any)
        score -= unmet_hearts * 100  # Penalize distance

        # Bonus: Can complete a live THIS turn?
        # If unmet is 0 and we have lives in zone, HUGE bonus
        if unmet_hearts == 0 and len(p.live_zone) > 0:
            score += 5000.0

        # --- 3. Board Strength (Secondary) ---
        stage_blades = 0
        stage_draws = 0
        stage_raw_hearts = 0

        for cid in p.stage:
            if cid in state.member_db:
                m = state.member_db[cid]
                stage_blades += m.blades
                stage_draws += m.draw_icons
                stage_raw_hearts += np.sum(m.hearts)

        score += stage_blades * 5  # Reduced from 10
        score += stage_draws * 10  # Reduced from 15
        score += stage_raw_hearts * 2  # Reduced from 5 (fulfilled matters more)

        # --- 4. Resources ---
        score += len(p.hand) * 10  # Reduced from 20
        # Untapped Energy value
        untapped_energy = p.count_untapped_energy()
        score += untapped_energy * 5  # Reduced from 10

        # --- 5. Opponent Denial (Simple) ---
        # We want opponent to have fewer cards/resources
        score -= len(opp.hand) * 5

        return score

    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0
        if len(legal_indices) == 1:
            return int(legal_indices[0])

        chosen_action = None  # Will be set by phase logic

        # --- PHASE SPECIFIC LOGIC ---

        # 1. Mulligan: Keep Low Cost Cards
        if state.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            p = state.players[player_id]
            if not hasattr(p, "mulligan_selection"):
                p.mulligan_selection = set()

            to_toggle = []
            for i, card_id in enumerate(p.hand):
                should_keep = False
                if card_id in state.member_db:
                    member = state.member_db[card_id]
                    if member.cost <= 3:
                        should_keep = True

                is_marked = i in p.mulligan_selection
                if should_keep and is_marked:
                    to_toggle.append(300 + i)
                elif not should_keep and not is_marked:
                    to_toggle.append(300 + i)

            # Filter to only legal toggles
            valid_toggles = [a for a in to_toggle if a in legal_indices]
            if valid_toggles:
                chosen_action = int(np.random.choice(valid_toggles))
            else:
                chosen_action = 0  # Confirm

        # 2. Live Set: Greedy Value Check
        elif state.phase == Phase.LIVE_SET:
            live_actions = [i for i in legal_indices if 400 <= i <= 459]
            if not live_actions:
                chosen_action = 0
            else:
                p = state.players[player_id]
                stage_hearts = p.get_total_hearts(state.member_db)

                pending_req = np.zeros(7, dtype=np.int32)
                for live_id in p.live_zone:
                    if live_id in state.live_db:
                        pending_req += state.live_db[live_id].required_hearts

                best_action = 0
                max_val = -100

                for action in live_actions:
                    hand_idx = action - 400
                    if hand_idx >= len(p.hand):
                        continue
                    card_id = p.hand[hand_idx]
                    if card_id not in state.live_db:
                        continue

                    live = state.live_db[card_id]
                    total_req = pending_req + live.required_hearts

                    missing = 0
                    temp_hearts = stage_hearts.copy()
                    for c in range(6):
                        needed = total_req[c]
                        have = temp_hearts[c]
                        if have < needed:
                            missing += needed - have
                            temp_hearts[c] = 0
                        else:
                            temp_hearts[c] -= needed

                    needed_any = total_req[6] if len(total_req) > 6 else 0
                    avail_any = np.sum(temp_hearts)
                    if avail_any < needed_any:
                        missing += needed_any - avail_any

                    score_val = live.score * 10
                    score_val -= missing * 5

                    if score_val > 0 and score_val > max_val:
                        max_val = score_val
                        best_action = action

                chosen_action = best_action if max_val > 0 else 0

        # 3. Main Phase: MINIMAX SEARCH
        elif state.phase == Phase.MAIN:
            # Limit depth to 2 (Me -> Opponent -> Eval) for performance
            # Ideally 3 to see my own follow-up response
            best_action = 0
            best_val = -float("inf")

            # Alpha-Beta Pruning
            alpha = -float("inf")
            beta = float("inf")

            legal_mask = state.get_legal_actions()
            legal_indices = np.where(legal_mask)[0]

            # Order moves by simple heuristic to improve pruning?
            # For now, simplistic ordering: Live/Play > Trade > Toggle > Pass
            # Actually, just random shuffle to avoid bias, or strict ordering.
            # Let's shuffle to keep variety.
            candidates = list(legal_indices)
            random.shuffle(candidates)

            # Pruning top-level candidates if too many
            if len(candidates) > 8:
                candidates = candidates[:8]
                if 0 not in candidates and 0 in legal_indices:
                    candidates.append(0)  # Always consider passing

            for action in candidates:
                try:
                    # MAX NODE (Me)
                    ns = state.step(action)
                    val = self._minimax(ns, self.depth - 1, alpha, beta, player_id)

                    if val > best_val:
                        best_val = val
                        best_action = action

                    alpha = max(alpha, val)
                    if beta <= alpha:
                        break  # Prune
                except Exception:
                    # If simulation fails, treat as bad move
                    pass

            chosen_action = int(best_action)

        # Fallback for other phases (ENERGY, DRAW, PERFORMANCE - usually auto)
        else:
            chosen_action = int(legal_indices[0])

        # --- FINAL VALIDATION ---
        # Ensure chosen_action is actually legal
        legal_set = set(legal_indices.tolist())
        if chosen_action is None or chosen_action not in legal_set:
            chosen_action = int(legal_indices[0])

        return chosen_action

    def _minimax(self, state: GameState, depth: int, alpha: float, beta: float, maximize_player: int) -> float:
        if depth <= 0 or state.game_over:
            return self.evaluate_state(state, maximize_player)

        current_player = state.current_player
        is_maximizing = current_player == maximize_player

        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]

        if len(legal_indices) == 0:
            return self.evaluate_state(state, maximize_player)

        # Move Ordering / Filtering for speed
        candidates = list(legal_indices)
        if len(candidates) > 5:
            indices = np.random.choice(legal_indices, 5, replace=False)
            candidates = list(indices)
            # Ensure pass is included if legal (often safe fallback)
            if 0 in legal_indices and 0 not in candidates:
                candidates.append(0)

        if is_maximizing:
            max_eval = -float("inf")
            for action in candidates:
                try:
                    ns = state.step(action)
                    eval_val = self._minimax(ns, depth - 1, alpha, beta, maximize_player)
                    max_eval = max(max_eval, eval_val)
                    alpha = max(alpha, eval_val)
                    if beta <= alpha:
                        break
                except:
                    pass
            return max_eval
        else:
            min_eval = float("inf")
            for action in candidates:
                try:
                    ns = state.step(action)
                    eval_val = self._minimax(ns, depth - 1, alpha, beta, maximize_player)
                    min_eval = min(min_eval, eval_val)
                    beta = min(beta, eval_val)
                    if beta <= alpha:
                        break
                except:
                    pass
            return min_eval
