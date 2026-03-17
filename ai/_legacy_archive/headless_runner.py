import argparse
import logging
import os
import random
import sys
import time

import numpy as np

# Add parent dir to path
# Add parent dir to path (for ai directory)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# Add engine directory
# Add project root directory
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from ai.agents.agent_base import Agent
from ai.agents.search_prob_agent import SearchProbAgent
from engine.game.data_loader import CardDataLoader
from engine.game.game_state import GameState, Phase


class TrueRandomAgent(Agent):
    """Completely random agent with no heuristics"""

    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0
        return int(np.random.choice(legal_indices))


class RandomAgent(Agent):
    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0

        # SMART HEURISTICS
        non_pass = [i for i in legal_indices if i != 0]

        # MULLIGAN: Sometimes confirm (action 0)
        if state.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            # 30% chance to confirm, 70% to toggle cards
            if random.random() < 0.3:
                return 0
            mulligan_actions = [i for i in legal_indices if 300 <= i <= 359]
            if mulligan_actions:
                return int(np.random.choice(mulligan_actions))
            return 0

        # Priority 1: In LIVE_SET, prioritize setting LIVE cards over passing
        if state.phase == Phase.LIVE_SET:
            live_set_actions = [i for i in legal_indices if 400 <= i <= 459]
            if live_set_actions:
                return int(np.random.choice(live_set_actions))

        # Priority 2: In MAIN phase, try to play members to stage
        if state.phase == Phase.MAIN:
            play_actions = [i for i in legal_indices if 1 <= i <= 180]
            if play_actions:
                # 80% chance to play instead of pass
                if random.random() < 0.8:
                    return int(np.random.choice(play_actions))

        # Priority 3: Never pass if ANY other action available
        if non_pass:
            return int(np.random.choice(non_pass))

        return 0


class SmartHeuristicAgent(Agent):
    """Advanced AI with better winning strategies"""

    def __init__(self):
        self.last_turn_num = -1
        self.turn_action_counts = {}

    def choose_action(self, state: GameState, player_id: int) -> int:
        # --- Loop Protection ---
        if state.turn_number != self.last_turn_num:
            self.last_turn_num = state.turn_number
            self.turn_action_counts = {}

        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0

        p = state.players[player_id]

        # --- MULLIGAN PHASE ---
        if state.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            # Keep members with cost <= 3, discard others and all Live cards
            # 300-359: index i is toggled

            # Initialize mulligan_selection if not present
            if not hasattr(p, "mulligan_selection"):
                p.mulligan_selection = set()

            to_toggle = []
            for i, card_id in enumerate(p.hand):
                should_keep = False
                if card_id in state.member_db:
                    member = state.member_db[card_id]
                    if member.cost <= 3:
                        should_keep = True

                # Check if already marked for return (mulligan_selection is a set of indices)
                is_marked = i in p.mulligan_selection
                if should_keep and is_marked:
                    # Unmark keepable card
                    to_toggle.append(300 + i)
                elif not should_keep and not is_marked:
                    # Mark bad card
                    to_toggle.append(300 + i)

            if to_toggle:
                # Filter to only legal toggles
                legal_set = set(legal_indices.tolist())
                valid_toggles = [a for a in to_toggle if a in legal_set]
                if valid_toggles:
                    choice = np.random.choice(valid_toggles)
                    return int(choice) if np.isscalar(choice) else int(choice[0])
            return 0  # Confirm

        # --- LIVE SET PHASE ---
        if state.phase == Phase.LIVE_SET:
            live_actions = [i for i in legal_indices if 400 <= i <= 459]
            if not live_actions:
                return 0  # Pass

            current_hearts = p.get_total_hearts(state.member_db)

            # Calculate what we already need for pending live cards
            pending_req = np.zeros(7, dtype=np.int32)
            for live_id in p.live_zone:
                if live_id in state.live_db:
                    pending_req += state.live_db[live_id].required_hearts

            # --- Improved LIVE_SET Logic ---
            best_action = -1
            max_value = -1

            for action in live_actions:
                hand_idx = action - 400
                card_id = p.hand[hand_idx]
                if card_id not in state.live_db:
                    continue

                live = state.live_db[card_id]
                total_req = pending_req + live.required_hearts

                # Check feasibility
                needed = total_req.copy()
                have = current_hearts.copy()

                # 1. Colors
                possible = True
                for c in range(6):
                    if have[c] >= needed[c]:
                        have[c] -= needed[c]
                        needed[c] = 0
                    else:
                        possible = False
                        break

                if not possible:
                    continue

                # 2. Any hearts
                if np.sum(have) < needed[6]:
                    continue

                # If possible, calculate value
                value = live.score * 10
                # Prefer cards we have hearts for
                value += np.sum(have) - needed[6]

                if value > max_value:
                    max_value = value
                    best_action = action

            if best_action != -1:
                return int(best_action)
            return 0  # Pass if no safe plays

        # --- MAIN PHASE ---
        if state.phase == Phase.MAIN:
            # 1. Activate Abilities (Rule of thumb: Draw/Energy > Buff > Damage)
            activate_actions = [i for i in legal_indices if 200 <= i <= 202]
            best_ability_action = -1
            best_ability_score = -1

            for action in activate_actions:
                area = action - 200
                card_id = p.stage[area]
                if card_id in state.member_db:
                    # HEURISTIC: Use 1-step lookahead to detect no-ops or loops
                    try:
                        next_state = state.step(action)
                        next_p = next_state.players[player_id]

                        # Comparison metrics
                        hand_delta = len(next_p.hand) - len(p.hand)
                        energy_delta = len(next_p.energy_zone) - len(p.energy_zone)
                        tap_delta = np.sum(next_p.tapped_energy) - np.sum(p.tapped_energy)
                        stage_changed = not np.array_equal(next_p.stage, p.stage)
                        choice_pending = len(next_state.pending_choices) > 0

                        # Repeating action penalty
                        reps = self.turn_action_counts.get(action, 0)

                        if (
                            not any([hand_delta > 0, energy_delta > 0, stage_changed, choice_pending])
                            and tap_delta <= 0
                        ):
                            # State didn't meaningfully improve for the better (maybe it tapped something but didn't gain)
                            score = -10
                        else:
                            score = 15 if (hand_delta > 0 or energy_delta > 0) else 10

                        # Apply repetition penalty
                        score -= reps * 20

                    except Exception:
                        score = -100  # Crashes are bad

                    if score > best_ability_score:
                        best_ability_score = score
                        best_ability_action = action

            # 2. Play Members
            play_actions = [i for i in legal_indices if 1 <= i <= 180]
            best_play_action = -1
            best_play_score = -1

            if play_actions:
                # Find current requirements from all live cards in zone
                # Precise "Scanning" of what hearts are missing
                pending_req = np.zeros(7, dtype=np.int32)
                for live_id in p.live_zone:
                    if live_id in state.live_db:
                        pending_req += state.live_db[live_id].required_hearts

                # What we have (excluding hand)
                current_hearts = p.get_total_hearts(state.member_db)

                # Calculate simple missing vector (ignoring Any for a moment to prioritize colors)
                # We really want to find a card that reduces the "Distance" to completion

                for action in play_actions:
                    hand_idx = (action - 1) // 3
                    card_id = p.hand[hand_idx]
                    member = state.member_db[card_id]

                    score = 0

                    # A. Heart Contribution
                    # Does this member provide a heart provided in 'pending_req' that we don't have enough of?
                    prov = member.hearts  # Shape (6,)

                    for c in range(6):
                        if pending_req[c] > current_hearts[c]:
                            # We need this color
                            if prov[c] > 0:
                                score += 20  # HUGE bonus for matching a need

                    # A2. Total Heart Volume (Crucial for 'Any' requirements)
                    total_hearts = prov.sum()
                    score += total_hearts * 5

                    # B. Base Stats
                    score += member.blades  # Power is good
                    score += member.draw_icons * 5  # Drawing is good

                    # C. Cost Efficiency
                    # If we are low on energy, cheap cards are better
                    # But don't punish so hard we don't play at all!
                    untapped_energy = p.count_untapped_energy()
                    if untapped_energy < 1 and member.cost > 1:
                        score -= 2  # Small penalty

                    # D. Slot Efficiency
                    area = (action - 1) % 3
                    if p.stage[area] >= 0:
                        # Replacing a member.
                        prev = state.member_db[p.stage[area]]
                        if prev.hearts.sum() > member.hearts.sum():
                            score -= 5
                    else:
                        score += 5  # Filling empty slot is good

                    if score > best_play_score:
                        best_play_score = score
                        best_play_action = action

            # Decision
            if best_ability_score > 0:
                self.turn_action_counts[best_ability_action] = self.turn_action_counts.get(best_ability_action, 0) + 1
                return int(best_ability_action)

            if best_play_action != -1:
                return int(best_play_action)

            # Pass - but verify it's legal
            if 0 in legal_indices:
                return 0
            return int(legal_indices[0])  # Fallback to first legal

        # Default: pick random non-pass if available
        non_pass = [i for i in legal_indices if i != 0]
        if non_pass:
            return int(np.random.choice(non_pass))
        # Fallback
        return int(legal_indices[0]) if len(legal_indices) > 0 else 0


def generate_random_decks(member_ids, live_ids):
    """Generate two random decks: 40 members + 10 lives in ONE main_deck each"""
    m_pool = list(member_ids)
    l_pool = list(live_ids)

    # Ensure pool is not empty
    if not m_pool:
        m_pool = [0]
    if not l_pool:
        l_pool = [0]

    # Mix members and lives in one deck
    deck1 = [random.choice(m_pool) for _ in range(40)] + [random.choice(l_pool) for _ in range(10)]
    deck2 = [random.choice(m_pool) for _ in range(40)] + [random.choice(l_pool) for _ in range(10)]

    random.shuffle(deck1)
    random.shuffle(deck2)

    return deck1, deck2


def initialize_game(use_real_data: bool = True, cards_path: str = "data/cards.json") -> GameState:
    """Initializes GameState with card data."""
    if use_real_data:
        try:
            loader = CardDataLoader(cards_path)
            m_db, l_db, e_db = loader.load()
            GameState.member_db = m_db
            GameState.live_db = l_db
        except Exception as e:
            print(f"Failed to load real data: {e}")
            GameState.member_db = {}
            GameState.live_db = {}
    else:
        # For testing, ensure dbs are empty or mocked if not loading real data
        GameState.member_db = {}
        GameState.live_db = {}
    return GameState()


def create_easy_cards():
    """Create custom easy cards for testing scoring"""
    import numpy as np
    from game.game_state import LiveCard, MemberCard

    # Easy Member: Cost 1, provides 1 of each heart + 1 blade
    m = MemberCard(
        card_id=888,
        card_no="PL!-sd1-001-SD",  # Correct field name
        name="Easy Member",
        cost=1,
        hearts=np.array([1, 1, 1, 1, 1, 1], dtype=np.int32),
        blade_hearts=np.array([0, 0, 0, 0, 0, 0], dtype=np.int32),
        blades=1,
        volume_icons=0,
        draw_icons=0,
        img_path="cards/PLSD01/PL!-sd1-001-SD.png",
        group="Easy",
    )

    # Easy Live: Score 1, Requires 1 Any Heart
    l = LiveCard(
        card_id=39999,
        card_no="PL!-pb1-019-SD",  # Correct field name
        name="Easy Live",
        score=1,
        required_hearts=np.array([0, 0, 0, 0, 0, 0, 1], dtype=np.int32),
        volume_icons=0,
        draw_icons=0,
        img_path="cards/PLSD01/PL!-pb1-019-SD.png",
        group="Easy",
    )

    return m, l


def setup_game(args):
    # Initialize game state
    use_easy = args.deck_type == "easy"

    state = initialize_game(use_real_data=(not use_easy), cards_path=args.cards_path)

    # Set seed
    np.random.seed(args.seed)
    random.seed(args.seed)

    if use_easy:
        # INJECT EASY CARDS
        m, l = create_easy_cards()
        state.member_db[888] = m
        state.live_db[39999] = l

        # Single main_deck with BOTH Members (40) and Lives (10), shuffled
        for p in state.players:
            m_list = [888] * 48
            l_list = [39999] * 12
            p.main_deck = m_list + l_list
            random.shuffle(p.main_deck)
            p.energy_deck = [40000] * 12
            p.hand = []
            p.energy_zone = []
            p.live_zone = []
            p.discard = []
            p.stage = np.array([-1, -1, -1], dtype=np.int32)
    else:
        # Normal Random Decks (Members + Lives mixed)
        member_keys = list(state.member_db.keys())

        if args.deck_type == "ability_only":
            # Filter for members with abilities
            member_keys = [mid for mid in member_keys if state.member_db[mid].abilities]
            if not member_keys:
                print("WARNING: No members with abilities found! Reverting to all members.")
                member_keys = list(state.member_db.keys())

        deck1, deck2 = generate_random_decks(member_keys, state.live_db.keys())
        state.players[0].main_deck = deck1
        state.players[0].energy_deck = [39999] * 10

        state.players[1].main_deck = deck2
        state.players[1].energy_deck = [39999] * 10

        # Clear hands/zones just in case
        for p in state.players:
            p.hand = []
            p.energy_zone = []

    # Initial Draw (5 cards from main_deck)
    for _ in range(5):
        if state.players[0].main_deck:
            state.players[0].hand.append(state.players[0].main_deck.pop())
        if state.players[1].main_deck:
            state.players[1].hand.append(state.players[1].main_deck.pop())

    # Setup Energy Decks (Rule 6.1.1.3: 12 cards)
    for p in state.players:
        p.energy_deck = [40000] * 12
        p.energy_zone = []
        # Initial Energy (Rule 6.2.1.7: Move 3 cards to energy zone)
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    return state


class AbilityFocusAgent(SmartHeuristicAgent):
    """
    Agent that prioritizes activating abilities and playing cards with abilities.
    Used for stress-testing ability implementations.
    """

    def choose_action(self, state: GameState, player_id: int) -> int:
        legal_mask = state.get_legal_actions()
        legal_indices = np.where(legal_mask)[0]
        if len(legal_indices) == 0:
            return 0

        # If we have pending choices, we MUST choose one of them (usually 500+)
        if state.pending_choices:
            non_zero = [i for i in legal_indices if i != 0]
            if non_zero:
                return int(np.random.choice(non_zero))
            return int(np.random.choice(legal_indices))

        p = state.players[player_id]

        # 1. (LIVE_SET is handled by superclass logic for smarter selection)

        # 2. MAIN Phase Priorities
        if state.phase == Phase.MAIN:
            priority_actions = []

            # Check Play Actions (1-180)
            play_actions = [i for i in legal_indices if 1 <= i <= 180]
            for action_id in play_actions:
                hand_idx = (action_id - 1) // 3
                if hand_idx < len(p.hand):
                    card_id = p.hand[hand_idx]
                    if card_id in state.member_db:
                        card = state.member_db[card_id]
                        if card.abilities:
                            # Massive priority for cards with ON_PLAY or ACTIVATED
                            has_prio = any(a.trigger in (1, 7) for a in card.abilities)  # 1=ON_PLAY, 7=ACTIVATED
                            if has_prio:
                                priority_actions.append(action_id)

            # Check Activated Ability Actions (200-202)
            ability_actions = [i for i in legal_indices if 200 <= i <= 202]
            priority_actions.extend(ability_actions)

            if priority_actions:
                return int(np.random.choice(priority_actions))

        # Fallback to SmartHeuristic if no high-priority ability action found
        return super().choose_action(state, player_id)


class ConservativeAgent(SmartHeuristicAgent):
    """
    Very safe AI. Only sets Live cards if it has strictly sufficient hearts
    available on stage right now (untapped members). Never gambles on future draws.
    """

    def choose_action(self, state: GameState, player_id: int) -> int:
        # Override LIVE_SET phase with ultra-conservative logic
        if state.phase == Phase.LIVE_SET:
            p = state.players[player_id]
            legal_indices = np.where(state.get_legal_actions())[0]
            live_actions = [i for i in legal_indices if 400 <= i <= 459]
            if not live_actions:
                return 0  # Pass

            # ONLY count hearts on stage (no assumptions about future)
            stage_hearts = p.get_total_hearts(state.member_db)

            # Calculate what we already need for pending live cards
            pending_req = np.zeros(7, dtype=np.int32)
            for live_id in p.live_zone:
                if live_id in state.live_db:
                    pending_req += state.live_db[live_id].required_hearts

            best_action = -1
            max_value = -1

            for action in live_actions:
                hand_idx = action - 400
                card_id = p.hand[hand_idx]
                if card_id not in state.live_db:
                    continue

                live = state.live_db[card_id]
                total_req = pending_req + live.required_hearts

                # Ultra-strict feasibility check: need EXACT hearts available
                needed = total_req.copy()
                have = stage_hearts.copy()

                # 1. Check colored hearts (must have exact matches)
                possible = True
                for c in range(6):
                    if have[c] < needed[c]:
                        possible = False
                        break
                    have[c] -= needed[c]
                    needed[c] = 0

                if not possible:
                    continue

                # 2. Check "Any" hearts (must have enough remaining)
                if np.sum(have) < needed[6]:
                    continue

                # If strictly possible, calculate conservative value
                value = live.score * 10
                # Small bonus for having extra hearts (prefer safer plays)
                value += np.sum(have) - needed[6]

                if value > max_value:
                    max_value = value
                    best_action = action

            if best_action != -1:
                return int(best_action)
            return 0  # Pass if no 100% safe plays

        # For all other phases, use SmartHeuristicAgent logic
        return super().choose_action(state, player_id)


class GambleAgent(SmartHeuristicAgent):
    """
    Risk-taking AI. Sets Live cards if it has enough hearts OR if it has
    enough blades on stage to likely get the hearts from yell cards.
    """

    def choose_action(self, state: GameState, player_id: int) -> int:
        if state.phase == Phase.LIVE_SET:
            p = state.players[player_id]
            legal_indices = np.where(state.get_legal_actions())[0]
            live_actions = [i for i in legal_indices if 400 <= i <= 459]
            if not live_actions:
                return 0

            # Current hearts on stage
            stage_hearts = p.get_total_hearts(state.member_db)
            # Total blades on stage (potential yells)
            total_blades = p.get_total_blades(state.member_db)

            # Estimated hearts from yells: Roughly 0.5 hearts per blade?
            # Or simplified: consider blades as "Any" hearts for feasibility check
            est_extra_hearts = total_blades // 2

            best_action = -1
            max_value = -1

            # Pending req
            pending_req = np.zeros(7, dtype=np.int32)
            for live_id in p.live_zone:
                if live_id in state.live_db:
                    pending_req += state.live_db[live_id].required_hearts

            for action in live_actions:
                hand_idx = action - 400
                card_id = p.hand[hand_idx]
                if card_id not in state.live_db:
                    continue

                live = state.live_db[card_id]
                total_req = pending_req + live.required_hearts

                # Feasibility check with "Gamble" factor
                needed = total_req.copy()
                have = stage_hearts.copy()

                # satisfy colors
                possible = True
                for c in range(6):
                    if have[c] < needed[c]:
                        # Can we gamble on this color?
                        # Maybe if we have a lot of blades.
                        # For simplicity, let's say we can only gamble on 'Any'
                        possible = False
                        break
                    have[c] -= needed[c]

                if not possible:
                    continue

                # Any hearts check with gamble
                total_have = np.sum(have) + est_extra_hearts
                if total_have >= needed[6]:
                    value = live.score * 10 + (total_have - needed[6])
                    if value > max_value:
                        max_value = value
                        best_action = action

            if best_action != -1:
                return int(best_action)
            return 0

        return super().choose_action(state, player_id)


class NNAgent(Agent):
    """
    Agent backed by a Neural Network (PyTorch), running on GPU if available.
    """

    def __init__(self, device=None, model_path=None):
        try:
            # Lazy import to avoid hard dependency if not used
            # import torch
            from game.network import NetworkConfig
            from game.network_torch import TorchNetworkWrapper

            self.config = NetworkConfig()
            self.net = TorchNetworkWrapper(self.config, device=device)
            self.device = self.net.device

            if model_path:
                print(f"Loading model from {model_path}...")
                self.net.load(model_path)
            # print(f"NNAgent initialized on device: {self.device}")

        except ImportError as e:
            print(f"WARNING: PyTorch or network modules not found. NNAgent falling back to Random. Error: {e}")
            self.net = None
        except Exception as e:
            print(f"WARNING: Failed to initialize NNAgent: {e}")
            self.net = None

    def choose_action(self, state: GameState, player_id: int) -> int:
        if self.net is None:
            # Fallback to random if failed to load
            legal_mask = state.get_legal_actions()
            legal_indices = np.where(legal_mask)[0]
            return int(np.random.choice(legal_indices)) if len(legal_indices) > 0 else 0

        # Predict policy (this runs on GPU if available)
        policy, value = self.net.predict(state)

        # Choose action based on policy probabilities
        # Direct policy sampling (fastest way to use the network without MCTS)

        # Ensure probabilities sum to 1 (handling float errors)
        policy_sum = policy.sum()
        if policy_sum > 0:
            policy = policy / policy_sum
            return int(np.random.choice(len(policy), p=policy))
        else:
            # Fallback if policy is all zeros (shouldn't happen with proper masking)
            legal_mask = state.get_legal_actions()
            legal_indices = np.where(legal_mask)[0]
            return int(np.random.choice(legal_indices)) if len(legal_indices) > 0 else 0


def run_simulation(args):
    import io

    # We will manage logging manually per game
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Console handler for high-level info
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)  # Only show warnings/errors to console during run
    root_logger.addHandler(console)

    best_combined_score = -1
    best_log_content = ""
    best_game_idx = -1
    best_winner = -1

    results = []

    start_total = time.time()

    for game_idx in range(args.num_games):
        # Capture logs for this game
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.INFO)
        # Use a simple format for game logs
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)

        root_logger.handlers = [console, handler]  # Replace handlers (keep console)

        # Log Header
        logging.info(f"=== Game {game_idx + 1} ===")

        # Setup Game
        try:
            state = setup_game(args)
            current_seed = args.seed + game_idx
            random.seed(current_seed)
            np.random.seed(current_seed)

            # Agent Selection
            if args.agent == "random":
                p0_agent = RandomAgent()
            elif args.agent == "ability_focus":
                p0_agent = AbilityFocusAgent()
            elif args.agent == "conservative":
                p0_agent = ConservativeAgent()
            elif args.agent == "gamble":
                p0_agent = GambleAgent()
            elif args.agent == "nn":
                p0_agent = NNAgent()
            elif args.agent == "search":
                p0_agent = SearchProbAgent(depth=args.depth)
            else:
                p0_agent = SmartHeuristicAgent()

            # Agent Selection P1
            if args.agent_p2 == "ability_focus":
                p1_agent = AbilityFocusAgent()
            elif args.agent_p2 == "search":
                p1_agent = SearchProbAgent(depth=args.depth)
            elif args.agent_p2 == "smart":
                p1_agent = SmartHeuristicAgent()
            else:
                p1_agent = RandomAgent()

            agents = [p0_agent, p1_agent]

            action_count = 0
            while not state.game_over:
                # Limit safety
                if action_count > args.max_turns:
                    break
                state.check_win_condition()
                if state.game_over:
                    break

                active_pid = state.current_player

                # Detailed Log
                logging.info("-" * 40)
                logging.info(f"Turn {state.turn_number} | Phase {state.phase.name} | Active: P{active_pid}")
                p0 = state.players[0]
                p1 = state.players[1]
                logging.info(f"Score: P0({len(p0.success_lives)}) - P1({len(p1.success_lives)})")
                logging.info(f"Hand: P0({len(p0.hand)}) - P1({len(p1.hand)})")

                # Agent Act
                action = agents[active_pid].choose_action(state, active_pid)
                logging.info(f"Action: P{active_pid} chooses {action}")

                state = state.step(action)
                action_count += 1

            # Game End
            p0_score = len(state.players[0].success_lives)
            p1_score = len(state.players[1].success_lives)
            combined_score = p0_score + p1_score
            winner = state.winner

            logging.info("=" * 40)
            logging.info(f"Game Over. Winner: {winner}. Score: {p0_score}-{p1_score}")

            res = {
                "id": game_idx,
                "winner": winner,
                "score_total": combined_score,
                "p0_score": p0_score,
                "p1_score": p1_score,
                "actions": action_count,
                "game_turns": state.turn_number,
            }
            results.append(res)
            print(f"DEBUG: Game {game_idx} Winner: {winner}")

            # Check if this is the "best" game
            is_win = winner == 0 or winner == 1
            if is_win or combined_score > best_combined_score:
                if is_win and best_winner == -1:
                    print(f"Found a Winner in Game {game_idx + 1}! (Winner: P{winner})")

                best_log_content = log_capture.getvalue()
                best_combined_score = combined_score
                best_winner = winner
                best_game_idx = game_idx  # Added this line to update best_game_idx

            if (game_idx + 1) % 100 == 0:
                print(f"Simulated {game_idx + 1} games... Best Score: {best_combined_score}")

        except Exception as e:
            msg = f"Error in game {game_idx}: {e}"
            print(msg, file=sys.stderr)
            import traceback

            traceback.print_exc()

        finally:
            log_capture.close()

    total_time = time.time() - start_total

    # Write best log
    with open(args.log_file, "w", encoding="utf-8") as f:
        f.write(best_log_content)

    print("\n=== Simulation Complete ===")
    print(f"Total Games Ran: {len(results)}")
    print(f"Total Time: {total_time:.2f}s")

    wins0 = sum(1 for r in results if r["winner"] == 0)
    wins1 = sum(1 for r in results if r["winner"] == 1)
    draws = sum(1 for r in results if r["winner"] == 2)

    print(f"Wins: P0={wins0}, P1={wins1}, Draws={draws}")

    total_actions = sum(r["actions"] for r in results)
    total_game_turns = sum(r["game_turns"] for r in results)

    if total_time > 0:
        print(f"APS (Actions Per Second): {total_actions / total_time:.2f}")
        print(f"TPS (Turns Per Second): {total_game_turns / total_time:.2f}")

    print(
        f"Best Game was Game {best_game_idx + 1} with Score Total {best_combined_score if best_combined_score >= 0 else 0}"
    )
    print(f"Log for best game saved to {args.log_file}")
    import json

    if results:
        print(f"Last Game Summary: {json.dumps(results[-1], indent=2)}")


if __name__ == "__main__":
    # Default path relative to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_cards_path = os.path.join(script_dir, "..", "engine", "data", "cards.json")

    parser = argparse.ArgumentParser()
    parser.add_argument("--cards_path", default=default_cards_path, help="Path to cards.json")
    parser.add_argument(
        "--deck_type",
        default="normal",
        choices=["normal", "easy", "ability_only"],
        help="Deck type: normal, easy, or ability_only",
    )
    parser.add_argument("--max_turns", type=int, default=1000, help="Max steps/turns to run")
    parser.add_argument("--log_file", default="game_log.txt", help="Output log file")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--num_games", type=int, default=1, help="Number of games to run")
    parser.add_argument(
        "--agent",
        default="smart",
        choices=["random", "smart", "ability_focus", "conservative", "gamble", "nn", "search"],
        help="Agent type to control P0",
    )
    parser.add_argument(
        "--agent_p2",
        default="random",
        choices=["random", "smart", "ability_focus", "conservative", "gamble", "nn", "search"],
        help="Agent type to control P1",
    )
    parser.add_argument("--depth", type=int, default=2, help="Search depth for SearchProbAgent")

    args = parser.parse_args()

    run_simulation(args)
