"""
FAST CPU-Only Agent Tournament
Optimized for maximum throughput with heuristic agents.

Key Optimizations:
1. Mutable game state (no copy per step) - HUGE speedup
2. Disabled verbose logging
3. Disabled loop detection (saves tuple creation + hashing)
4. Larger chunksizes for reduced IPC overhead
5. Minimal object creation per turn
"""

import argparse
import os
import random
import subprocess
import sys
import time
from enum import IntEnum
from multiprocessing import Pool, cpu_count
from typing import Dict, List

import numpy as np

# Add parent dir to path
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root)
sys.path.append(os.path.join(root, "engine"))
sys.path.append(os.path.join(root, "ai"))

from game.data_loader import CardDataLoader

# ============================================================================
# INLINE MINIMAL GAME STATE (Optimized for Speed)
# ============================================================================


class Phase(IntEnum):
    SETUP = -2
    MULLIGAN_P1 = -1
    MULLIGAN_P2 = 0
    ACTIVE = 1
    ENERGY = 2
    DRAW = 3
    MAIN = 4
    LIVE_SET = 5
    PERFORMANCE_P1 = 6
    PERFORMANCE_P2 = 7
    LIVE_RESULT = 8


class FastPlayerState:
    """Minimal player state for fast simulation."""

    __slots__ = [
        "player_id",
        "hand",
        "main_deck",
        "energy_deck",
        "discard",
        "energy_zone",
        "success_lives",
        "live_zone",
        "stage",
        "stage_energy",
        "tapped_energy",
        "tapped_members",
        "members_played_this_turn",
        "mulligan_selection",
    ]

    def __init__(self, player_id: int):
        self.player_id = player_id
        self.hand: List[int] = []
        self.main_deck: List[int] = []
        self.energy_deck: List[int] = []
        self.discard: List[int] = []
        self.energy_zone: List[int] = []
        self.success_lives: List[int] = []
        self.live_zone: List[int] = []
        self.stage: np.ndarray = np.full(3, -1, dtype=np.int32)
        self.stage_energy: List[List[int]] = [[], [], []]
        self.tapped_energy: np.ndarray = np.zeros(50, dtype=bool)
        self.tapped_members: np.ndarray = np.zeros(3, dtype=bool)
        self.members_played_this_turn: np.ndarray = np.zeros(3, dtype=bool)
        self.mulligan_selection: set = set()

    def untap_all(self):
        self.tapped_energy[:] = False
        self.tapped_members[:] = False

    def count_untapped_energy(self) -> int:
        return len(self.energy_zone) - np.sum(self.tapped_energy[: len(self.energy_zone)])

    def get_total_hearts(self, member_db: Dict) -> np.ndarray:
        total = np.zeros(7, dtype=np.int32)
        for i, card_id in enumerate(self.stage):
            if card_id >= 0 and not self.tapped_members[i] and card_id in member_db:
                member = member_db[card_id]
                total[:6] += member.hearts
        return total

    def get_total_blades(self, member_db: Dict) -> int:
        total = 0
        for i, card_id in enumerate(self.stage):
            if card_id >= 0 and not self.tapped_members[i] and card_id in member_db:
                total += member_db[card_id].blades
        return total


class FastGameState:
    """Minimal game state - MUTABLE (no copies) for speed."""

    def __init__(self, member_db: Dict, live_db: Dict):
        self.member_db = member_db
        self.live_db = live_db
        self.players = [FastPlayerState(0), FastPlayerState(1)]
        self.current_player = 0
        self.first_player = 0
        self.phase = Phase.ACTIVE
        self.turn_number = 1
        self.game_over = False
        self.winner = -1

    def get_legal_actions(self) -> np.ndarray:
        """Returns legal action mask - simplified for speed."""
        mask = np.zeros(500, dtype=bool)

        if self.game_over:
            return mask

        p = self.players[self.current_player]

        # MULLIGAN
        if self.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            mask[0] = True
            for i in range(min(len(p.hand), 60)):
                mask[300 + i] = True
            return mask

        # Auto-advance phases
        if self.phase in (
            Phase.ACTIVE,
            Phase.ENERGY,
            Phase.DRAW,
            Phase.PERFORMANCE_P1,
            Phase.PERFORMANCE_P2,
            Phase.LIVE_RESULT,
        ):
            mask[0] = True
            return mask

        # MAIN phase
        if self.phase == Phase.MAIN:
            mask[0] = True
            available_energy = p.count_untapped_energy()

            # Play members
            for i, card_id in enumerate(p.hand):
                if card_id not in self.member_db:
                    continue
                member = self.member_db[card_id]
                for area in range(3):
                    if p.members_played_this_turn[area]:
                        continue
                    active_cost = member.cost
                    if p.stage[area] >= 0 and p.stage[area] in self.member_db:
                        active_cost = max(0, active_cost - self.member_db[p.stage[area]].cost)
                    if active_cost <= available_energy:
                        mask[1 + i * 3 + area] = True
            return mask

        # LIVE_SET
        if self.phase == Phase.LIVE_SET:
            mask[0] = True
            if len(p.live_zone) < 3:
                for i, card_id in enumerate(p.hand):
                    if card_id in self.live_db:
                        mask[400 + i] = True
            return mask

        mask[0] = True
        return mask

    def step_inplace(self, action_id: int):
        """Execute action IN-PLACE (no copy) for speed."""
        p = self.players[self.current_player]

        # MULLIGAN
        if self.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            if 300 <= action_id < 360:
                idx = action_id - 300
                if idx < len(p.hand):
                    if idx in p.mulligan_selection:
                        p.mulligan_selection.discard(idx)
                    else:
                        p.mulligan_selection.add(idx)
            elif action_id == 0:
                # Execute mulligan
                if p.mulligan_selection:
                    to_return = sorted(p.mulligan_selection, reverse=True)
                    for idx in to_return:
                        if idx < len(p.hand):
                            card = p.hand.pop(idx)
                            p.main_deck.insert(0, card)
                    random.shuffle(p.main_deck)
                    draw_count = len(to_return)
                    for _ in range(draw_count):
                        if p.main_deck:
                            p.hand.append(p.main_deck.pop())
                    p.mulligan_selection.clear()

                # Advance phase
                if self.phase == Phase.MULLIGAN_P1:
                    self.phase = Phase.MULLIGAN_P2
                    self.current_player = 1
                else:
                    self.phase = Phase.ACTIVE
                    self.current_player = self.first_player
            return

        # Auto-advance phases
        if self.phase == Phase.ACTIVE:
            p.untap_all()
            p.members_played_this_turn[:] = False
            self.phase = Phase.ENERGY
            return

        if self.phase == Phase.ENERGY:
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))
            self.phase = Phase.DRAW
            return

        if self.phase == Phase.DRAW:
            for _ in range(2):
                if p.main_deck:
                    p.hand.append(p.main_deck.pop())
            self.phase = Phase.MAIN
            return

        # MAIN phase actions
        if self.phase == Phase.MAIN:
            if action_id == 0:
                self.phase = Phase.LIVE_SET
                return

            if 1 <= action_id <= 180:
                hand_idx = (action_id - 1) // 3
                area = (action_id - 1) % 3
                if hand_idx < len(p.hand):
                    card_id = p.hand[hand_idx]
                    if card_id in self.member_db:
                        member = self.member_db[card_id]
                        cost = member.cost

                        # Baton touch cost reduction
                        if p.stage[area] >= 0 and p.stage[area] in self.member_db:
                            old_cost = self.member_db[p.stage[area]].cost
                            cost = max(0, cost - old_cost)
                            # Send old member to discard
                            p.discard.append(p.stage[area])

                        # Pay cost
                        paid = 0
                        for i in range(len(p.energy_zone)):
                            if paid >= cost:
                                break
                            if not p.tapped_energy[i]:
                                p.tapped_energy[i] = True
                                paid += 1

                        # Place member
                        p.hand.pop(hand_idx)
                        p.stage[area] = card_id
                        p.members_played_this_turn[area] = True
            return

        # LIVE_SET
        if self.phase == Phase.LIVE_SET:
            if action_id == 0:
                self.phase = Phase.PERFORMANCE_P1
                self.current_player = self.first_player
                return

            if 400 <= action_id < 460:
                idx = action_id - 400
                if idx < len(p.hand) and p.hand[idx] in self.live_db:
                    card = p.hand.pop(idx)
                    p.live_zone.append(card)
            return

        # PERFORMANCE phases (simplified - just check and resolve)
        if self.phase == Phase.PERFORMANCE_P1:
            self._resolve_performance(self.first_player)
            self.phase = Phase.PERFORMANCE_P2
            self.current_player = 1 - self.first_player
            return

        if self.phase == Phase.PERFORMANCE_P2:
            self._resolve_performance(1 - self.first_player)
            self.phase = Phase.LIVE_RESULT
            return

        if self.phase == Phase.LIVE_RESULT:
            self._check_win()
            # Next turn
            self.turn_number += 1
            self.first_player = 1 - self.first_player
            self.current_player = self.first_player
            self.phase = Phase.ACTIVE
            return

    def _resolve_performance(self, pid: int):
        """Simplified performance resolution."""
        p = self.players[pid]
        if not p.live_zone:
            return

        hearts = p.get_total_hearts(self.member_db)

        passed = []
        failed = []
        for live_id in p.live_zone:
            if live_id not in self.live_db:
                failed.append(live_id)
                continue

            live = self.live_db[live_id]
            req = live.required_hearts
            have = hearts.copy()

            # Check colored hearts
            ok = True
            for c in range(6):
                if have[c] >= req[c]:
                    have[c] -= req[c]
                else:
                    ok = False
                    break

            # Check 'any' hearts
            if ok and np.sum(have) >= req[6]:
                passed.append(live_id)
            else:
                failed.append(live_id)

        p.success_lives.extend(passed)
        p.discard.extend(failed)
        p.live_zone = []

    def _check_win(self):
        if len(self.players[0].success_lives) >= 3:
            self.game_over = True
            self.winner = 0
        elif len(self.players[1].success_lives) >= 3:
            self.game_over = True
            self.winner = 1


# ============================================================================
# FAST AGENTS (Simplified for Speed)
# ============================================================================


class FastTrueRandomAgent:
    def choose_action(self, state: FastGameState, pid: int) -> int:
        mask = state.get_legal_actions()
        legal = np.where(mask)[0]
        return int(np.random.choice(legal)) if len(legal) > 0 else 0


class FastRandomAgent:
    def choose_action(self, state: FastGameState, pid: int) -> int:
        mask = state.get_legal_actions()
        legal = np.where(mask)[0]
        if len(legal) == 0:
            return 0
        non_pass = [i for i in legal if i != 0]
        if non_pass and random.random() < 0.8:
            return int(random.choice(non_pass))
        return int(np.random.choice(legal))


class FastSmartAgent:
    def choose_action(self, state: FastGameState, pid: int) -> int:
        mask = state.get_legal_actions()
        legal = np.where(mask)[0]
        if len(legal) == 0:
            return 0

        p = state.players[pid]

        # MULLIGAN: Keep low cost members
        if state.phase in (Phase.MULLIGAN_P1, Phase.MULLIGAN_P2):
            for i, card_id in enumerate(p.hand):
                should_keep = card_id in state.member_db and state.member_db[card_id].cost <= 3
                is_marked = i in p.mulligan_selection
                if should_keep and is_marked:
                    return 300 + i
                if not should_keep and not is_marked:
                    return 300 + i
            return 0

        # LIVE_SET: Set viable lives
        if state.phase == Phase.LIVE_SET:
            live_actions = [i for i in legal if 400 <= i < 460]
            if live_actions:
                hearts = p.get_total_hearts(state.member_db)
                for action in live_actions:
                    idx = action - 400
                    if idx < len(p.hand):
                        live_id = p.hand[idx]
                        if live_id in state.live_db:
                            req = state.live_db[live_id].required_hearts
                            have = hearts.copy()
                            ok = True
                            for c in range(6):
                                if have[c] >= req[c]:
                                    have[c] -= req[c]
                                else:
                                    ok = False
                                    break
                            if ok and np.sum(have) >= req[6]:
                                return action
            return 0

        # MAIN: Play members
        if state.phase == Phase.MAIN:
            play_actions = [i for i in legal if 1 <= i <= 180]
            if play_actions:
                return int(random.choice(play_actions))

        # Default: non-pass if available
        non_pass = [i for i in legal if i != 0]
        if non_pass:
            return int(random.choice(non_pass))
        return 0


# ============================================================================
# TOURNAMENT LOGIC
# ============================================================================


class EloRating:
    def __init__(self, k_factor=32):
        self.k_factor = k_factor
        self.ratings = {}
        self.matches = {}
        self.wins = {}
        self.draws = {}

    def init_agent(self, name):
        if name not in self.ratings:
            self.ratings[name] = 1000
            self.matches[name] = 0
            self.wins[name] = 0
            self.draws[name] = 0

    def update(self, agent_a, agent_b, score_a):
        self.init_agent(agent_a)
        self.init_agent(agent_b)
        self.matches[agent_a] += 1
        self.matches[agent_b] += 1
        if score_a == 1:
            self.wins[agent_a] += 1
        elif score_a == 0:
            self.wins[agent_b] += 1
        else:
            self.draws[agent_a] += 1
            self.draws[agent_b] += 1

        ra, rb = self.ratings[agent_a], self.ratings[agent_b]
        ea = 1 / (1 + 10 ** ((rb - ra) / 400))
        eb = 1 - ea
        k = self.k_factor * 2 if self.matches[agent_a] <= 20 else self.k_factor
        self.ratings[agent_a] = ra + k * (score_a - ea)
        self.ratings[agent_b] = rb + k * ((1 - score_a) - eb)


def get_free_ram() -> int:
    try:
        output = subprocess.check_output(["wmic", "OS", "get", "FreePhysicalMemory", "/Value"], encoding="utf-8")
        for line in output.splitlines():
            if "FreePhysicalMemory" in line:
                return int(line.split("=")[1].strip()) // 1024
        return 4096
    except:
        return 4096


# Global for workers
G_MEMBER_DB = {}
G_LIVE_DB = {}
G_AGENTS = {}


def init_worker(member_db, live_db):
    global G_MEMBER_DB, G_LIVE_DB, G_AGENTS
    G_MEMBER_DB = member_db
    G_LIVE_DB = live_db
    G_AGENTS = {
        "TrueRandom": FastTrueRandomAgent(),
        "Random": FastRandomAgent(),
        "Smart": FastSmartAgent(),
    }


def run_single_game(args_tuple):
    agent_name_a, agent_name_b, game_seed = args_tuple

    random.seed(game_seed)
    np.random.seed(game_seed)

    state = FastGameState(G_MEMBER_DB, G_LIVE_DB)
    agent_a = G_AGENTS[agent_name_a]
    agent_b = G_AGENTS[agent_name_b]

    # Setup decks
    m_ids = list(G_MEMBER_DB.keys())
    l_ids = list(G_LIVE_DB.keys())
    for p in state.players:
        p.energy_deck = [2000] * 12
        p.main_deck = [random.choice(m_ids) for _ in range(40)] + [random.choice(l_ids) for _ in range(10)]
        random.shuffle(p.main_deck)
        for _ in range(5):
            if p.main_deck:
                p.hand.append(p.main_deck.pop())
        for _ in range(3):
            if p.energy_deck:
                p.energy_zone.append(p.energy_deck.pop(0))

    first_player = random.randint(0, 1)
    state.first_player = first_player
    state.current_player = first_player
    state.phase = Phase.MULLIGAN_P1

    # Run game
    for _ in range(2000):
        if state.game_over:
            break

        mask = state.get_legal_actions()
        if not np.any(mask):
            state.game_over = True
            state.winner = 2
            break

        pid = state.current_player
        active_agent = agent_a if (first_player == 0 and pid == 0) or (first_player == 1 and pid == 1) else agent_b
        if first_player == 0:
            active_agent = agent_a if pid == 0 else agent_b
        else:
            active_agent = agent_b if pid == 0 else agent_a

        action = active_agent.choose_action(state, pid)
        state.step_inplace(action)

    # Result
    if not state.game_over:
        s0 = len(state.players[0].success_lives)
        s1 = len(state.players[1].success_lives)
        winner = 0 if s0 > s1 else (1 if s1 > s0 else 2)
    else:
        winner = state.winner

    if winner == 2:
        return 0.5
    if first_player == 0:
        return 1.0 if winner == 0 else 0.0
    else:
        return 0.0 if winner == 0 else 1.0


def main():
    parser = argparse.ArgumentParser(description="FAST CPU-Only Agent Tournament")
    parser.add_argument("--games_per_pair", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--workers", type=int, default=0)
    args = parser.parse_args()

    random.seed(args.seed)
    np.random.seed(args.seed)

    # Only 3 fast agents for now
    agent_names = ["TrueRandom", "Random", "Smart"]

    elo = EloRating()
    for name in agent_names:
        elo.init_agent(name)

    matchups = {}
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            matchups[(agent_names[i], agent_names[j])] = [0, 0, 0]

    loader = CardDataLoader("data/cards.json")
    m, l, e = loader.load()

    # Workers
    cores = cpu_count()
    ram = get_free_ram()
    max_workers = min(ram // 50, cores - 1)
    num_workers = args.workers if args.workers > 0 else max(1, max_workers)

    print(f"FAST Tournament: {cores} cores, {ram}MB RAM, {num_workers} workers")

    # Build tasks
    tasks = []
    meta = []
    for i in range(len(agent_names)):
        for j in range(i + 1, len(agent_names)):
            for g in range(args.games_per_pair):
                tasks.append((agent_names[i], agent_names[j], args.seed + len(tasks)))
                meta.append((agent_names[i], agent_names[j]))

    print(f"Running {len(tasks)} games...")
    start = time.time()

    with Pool(num_workers, init_worker, (m, l)) as pool:
        results = list(pool.imap(run_single_game, tasks, chunksize=8))

    elapsed = time.time() - start

    for result, (a, b) in zip(results, meta):
        elo.update(a, b, result)
        if result == 1.0:
            matchups[(a, b)][0] += 1
        elif result == 0.0:
            matchups[(a, b)][1] += 1
        else:
            matchups[(a, b)][2] += 1

    print(f"\nCompleted in {elapsed:.2f}s ({elapsed / len(tasks) * 1000:.1f}ms/game)")
    print(f"Throughput: {len(tasks) / elapsed:.1f} games/sec")

    print("\n" + "=" * 50)
    print(f"{'Agent':<12} | {'ELO':<6} | {'Wins':<5} | {'Win%'}")
    print("-" * 50)
    for name in sorted(agent_names, key=lambda x: elo.ratings[x], reverse=True):
        e_score = int(elo.ratings[name])
        w = elo.wins[name]
        m_count = elo.matches[name]
        wr = f"{w / m_count * 100:.1f}%" if m_count > 0 else "N/A"
        print(f"{name:<12} | {e_score:<6} | {w:<5} | {wr}")
    print("=" * 50)


if __name__ == "__main__":
    main()
