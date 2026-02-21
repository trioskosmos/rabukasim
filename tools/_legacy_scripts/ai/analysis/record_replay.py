import os
import sys

import numpy as np

# Ensure project root is in path
sys.path.append(os.getcwd())

from engine.game.game_state import initialize_game


def record_replay():
    print("Recording replay of a random game...")
    game = initialize_game(deck_type="training")

    # Enable verbose logging to capture rule details
    game.verbose = True

    log_file = "game_replay.txt"

    with open(log_file, "w", encoding="utf-8") as f:
        f.write("=== Love Live TCG Replay (Random Agent) ===\n")
        f.write("Deck: Training (60 cards)\n")
        f.write("===========================================\n\n")

        step_count = 0
        while not game.game_over:
            step_count += 1

            # snapshot state before action
            turn = game.turn_number
            phase = game.phase.name
            player = game.current_player

            f.write(f"--- Step {step_count} | Turn {turn} | {phase} | Player {player} ---\n")

            # Log basic state
            p = game.players[player]
            f.write(f"Hand: {[c for c in p.hand]}\n")
            f.write(f"Stage: {p.stage}\n")
            f.write(f"Lives: {p.success_lives}\n")

            # Get legal actions
            mask = game.get_legal_actions()
            legal_indices = np.where(mask)[0]

            if len(legal_indices) == 0:
                f.write("NO LEGAL ACTIONS! Force Pass.\n")
                action = 0
            else:
                action = int(np.random.choice(legal_indices))

            f.write(f">> Action Chosen: {action}\n")

            # Capture specific action details if possible
            if action == 0:
                f.write("   (Pass/Next)\n")
            elif 200 <= action <= 202:
                f.write(f"   (Activate Member Slot {action - 200})\n")
            elif 300 <= action <= 359:
                f.write(f"   (Mulligan Card {action - 300})\n")
            elif 400 <= action <= 459:
                f.write(f"   (Set Live {action - 400})\n")
            elif 1 <= action <= 180:
                f.write("   (Play Card)\n")

            # Execute
            if hasattr(game, "take_action"):
                game.take_action(action)
            else:
                # Fallback if take_action missing (shouldn't happen)
                game = game.step(action)

            # Flush rule log to file
            if game.rule_log:
                for entry in game.rule_log:
                    f.write(f"   [LOG] {entry}\n")
                game.rule_log.clear()  # Clear so we don't reprint

            f.write("\n")

        # End game summary
        f.write("===========================================\n")
        f.write(f"GAME OVER. Winner: {game.winner}\n")
        f.write(f"Total Steps: {step_count}\n")
        f.write(f"P0 Lives: {len(game.players[0].success_lives)}\n")
        f.write(f"P1 Lives: {len(game.players[1].success_lives)}\n")

    print(f"Replay saved to {log_file}")
    print("You can view it to see exactly what decisions were made.")


if __name__ == "__main__":
    record_replay()
