import numpy as np
from ai.vector_env import VectorGameState


def visualize_game():
    print("--- 1v1 Game Visualization (Text Log) ---")
    env = VectorGameState(num_envs=1)
    env.reset()

    # Context Indices
    SC = 0
    HD = 3
    DK = 6
    PH = 8
    TR = 2

    print(f"Initial State | Agent Deck: {env.batch_global_ctx[0, DK]} | Opp Deck: {env.opp_global_ctx[0, DK]}")

    for term in range(300):  # Max turns
        # Get State
        phase = env.batch_global_ctx[0, PH]
        turn = env.batch_global_ctx[0, 54]  # Assuming 54 is turn count based on previous edits

        # Simple Random Action
        masks = env.get_action_masks()
        legal = np.where(masks[0])[0]
        if len(legal) > 0:
            action = np.random.choice(legal)
        else:
            action = 0

        # Step
        obs, rewards, dones, infos = env.step(np.array([action], dtype=np.int32))

        # Log Step
        a_score = env.batch_scores[0]
        o_score = env.opp_scores[0]
        a_hand = env.batch_global_ctx[0, HD]
        a_deck = env.batch_global_ctx[0, DK]
        a_trash = env.batch_global_ctx[0, TR]

        # Numeric Logging Style
        phase_map = {0: "START", 1: "ACTIVE", 2: "ENERGY", 3: "DRAW", 4: "MAIN", 8: "LIVE_RES"}
        ph_str = phase_map.get(phase, f"PH{phase}")

        log_line = f"[Step {term:3d}] Turn {turn:2d} | {ph_str:12s} | Action: {action:3d} | score: {a_score} vs Opp: {o_score} | Hand: {a_hand} | Deck: {a_deck} | Trash: {a_trash} | Energy: {env.batch_global_ctx[0, 5]}"

        # Add context details if action happens
        if action != 0:
            if 1 <= action <= 180:
                slot = (action - 1) % 3
                log_line += f"      -> Played Member to Slot {slot}"
            elif 400 <= action <= 459:
                log_line += "      -> Played LIVE CARD"

        print(log_line)
        with open("gameplay.log", "a", encoding="utf-8") as f:
            f.write(log_line + "\n")

        if dones[0]:
            inf = infos[0]
            final_a = inf.get("terminal_score_agent", a_score)
            final_o = inf.get("terminal_score_opp", o_score)
            res_line = (
                f"\n--- GAME OVER ---\nWINNER: {'AGENT' if final_a > final_o else 'OPPONENT'} ({final_a} - {final_o})\n"
            )
            print(res_line)
            with open("gameplay.log", "a", encoding="utf-8") as f:
                f.write(res_line)
            break

        # Small delay for "watching" effect if running interactive,
        # but for log dump we want instant.
        # time.sleep(0.05)


if __name__ == "__main__":
    # Clear log
    with open("gameplay.log", "w", encoding="utf-8") as f:
        f.write("--- 1v1 Gameplay Log (Numeric) ---\n")
    visualize_game()
