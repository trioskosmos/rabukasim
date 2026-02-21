import json
import os
import random
import sys
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import engine_rust
from ai.benchmark_decks import parse_deck
from ai.tournament import MCTSAgent, RandomAgent, ResNetAgent


def profile_agents(num_games=3):
    with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
        db_content = f.read()
    db_json = json.loads(db_content)

    # Load Decks
    deck_paths = [
        "ai/decks/aqours_cup.txt",
        "ai/decks/hasunosora_cup.txt",
        "ai/decks/liella_cup.txt",
        "ai/decks/muse_cup.txt",
        "ai/decks/nijigaku_cup.txt",
    ]
    decks = []
    for dp in deck_paths:
        if os.path.exists(dp):
            decks.append(parse_deck(dp, db_json["member_db"], db_json["live_db"], db_json.get("energy_db", {})))

    # Agents
    random_agent = RandomAgent()
    mcts_agent = MCTSAgent(sims=100)
    resnet_agent = ResNetAgent("ai/models/alphanet_best.pt")

    agent_names = ["Random", "MCTS-100", "ResNet-v1"]
    agents = [random_agent, mcts_agent, resnet_agent]

    print(f"Profiling Agents over {num_games} test games each...")

    stats = {name: {"calls": 0, "total_time": 0} for name in agent_names}

    db = engine_rust.PyCardDatabase(db_content)

    for name, agent in zip(agent_names, agents):
        print(f"Profiling {name}...")
        for _ in range(num_games):
            game = engine_rust.PyGameState(db)
            p0_deck, p0_lives = random.choice(decks)
            p1_deck, p1_lives = random.choice(decks)
            game.initialize_game(p0_deck, p1_deck, [0] * 10, [0] * 10, p0_lives, p1_lives)

            step = 0
            while not game.is_terminal() and step < 200:
                cp = game.current_player
                phase = game.phase

                if phase in [-1, 0, 4, 5]:
                    start = time.perf_counter()
                    action = agent.get_action(game, game.db)
                    end = time.perf_counter()

                    stats[name]["total_time"] += end - start
                    stats[name]["calls"] += 1

                    try:
                        game.step(action)
                    except:
                        legal = game.get_legal_action_ids()
                        if legal:
                            game.step(int(legal[0]))
                        else:
                            break
                else:
                    game.step(0)
                step += 1

    print("\nSpeed Results:")
    print(f"{'Agent':<12} | {'Avg Time/Move':<15} | {'Moves/Sec':<12}")
    print("-" * 50)
    for name, data in stats.items():
        if data["calls"] > 0:
            avg = data["total_time"] / data["calls"]
            m_sec = 1.0 / avg if avg > 0 else 0
            print(f"{name:<12} | {avg * 1000:>10.2f} ms | {m_sec:>10.1f}")
        else:
            print(f"{name:<12} | N/A")


if __name__ == "__main__":
    profile_agents()
