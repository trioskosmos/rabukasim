import json
import os
import sys

import numpy as np

# Ensure we can import ai modules
sys.path.append(os.getcwd())

from ai.vec_env_adapter import VectorEnvAdapter
from ai.vector_env import step_opponent_vectorized, step_vectorized
from sb3_contrib import MaskablePPO

from engine.game.fast_logic import check_deck_refresh


class AgentAnalyzer:
    def __init__(self, model_path):
        self.model_path = model_path
        self.card_db = {}
        self.load_card_db()
        self.env = VectorEnvAdapter(num_envs=1)
        self.model = MaskablePPO.load(model_path, env=self.env)

    def load_card_db(self):
        print("Loading Card Database...")
        with open("data/cards_compiled.json", "r", encoding="utf-8") as f:
            data = json.load(f)

        # Member DB
        for cid, card in data.get("member_db", {}).items():
            self.card_db[int(cid)] = {
                "name": card["name"],
                "type": "Member",
                "cost": card["cost"],
                "power": card.get("blades", 0),
                "hearts": card.get("hearts", 0),
                "color": card.get("color", 0),  # 1=Pink, 2=Red, 3=Yel, 4=Grn, 5=Blu, 6=Pur
                "text": card.get("ability_text", ""),
            }

        # Live DB
        for cid, card in data.get("live_db", {}).items():
            self.card_db[int(cid)] = {
                "name": card["name"],
                "type": "Live",
                "score": card.get("score", 0),
                "req": card.get("live_b", []),  # [p, r, y, g, b, pu]
                "text": card.get("abilities", [{}])[0].get("raw_text", "") if card.get("abilities") else "Vanilla",
            }

    def get_card_name(self, card_id):
        if card_id == 0:
            return "Empty"
        if card_id in self.card_db:
            c = self.card_db[card_id]
            return f"{c['name']} ({c['type'][0]})"
        return f"Unknown_{card_id}"

    def decode_action(self, action_id, hand_ids, stage_ids):
        if action_id == 0:
            return "PASS"

        # Play Member: 1..180
        # Formula: (HandIdx * 3) + Slot + 1
        if 1 <= action_id <= 180:
            val = action_id - 1
            hand_idx = val // 3
            slot = val % 3

            card_id = 0
            if hand_idx < len(hand_ids):
                card_id = hand_ids[hand_idx]

            card_name = self.get_card_name(card_id)
            return f"PLAY {card_name} [ID {card_id}] from Hand[{hand_idx}] to Slot {slot}"

        # Activate Ability: 200..202
        if 200 <= action_id <= 202:
            slot = action_id - 200
            card_id = stage_ids[slot]
            card_name = self.get_card_name(card_id)
            return f"ACTIVATE {card_name} [ID {card_id}] at Slot {slot}"

        # Set Live: 400..459
        if 400 <= action_id <= 459:
            hand_idx = action_id - 400
            card_id = 0
            if hand_idx < len(hand_ids):
                card_id = hand_ids[hand_idx]
            card_name = self.get_card_name(card_id)
            return f"SET LIVE {card_name} [ID {card_id}] from Hand[{hand_idx}]"

        return f"UNKNOWN ACTION {action_id}"

    def manual_phase_step(self):
        """Advance simple phases (0->4) logic"""
        i = 0  # Env 0
        g_ctx = self.env.game_state.batch_global_ctx
        deck = self.env.game_state.batch_deck
        hand = self.env.game_state.batch_hand
        tapped = self.env.game_state.batch_tapped
        trash = self.env.game_state.batch_trash
        trash = self.env.game_state.batch_trash

        # Limit loops
        for _ in range(10):
            ph = int(g_ctx[i, 8])

            if ph == 4:  # Main Phase
                return

            # Phase 0/8 -> 1 (Start)
            if ph == 0 or ph == 8:
                # Reset Tapped
                tapped[i, 0:16] = 0
                # Reset "Play Per Turn" flags (51-53)
                g_ctx[i, 51:54] = 0
                # Inc Energy
                ec = g_ctx[i, 5]
                if ec == 0:
                    g_ctx[i, 5] = 3
                elif ec < 12:
                    g_ctx[i, 5] = ec + 1

                g_ctx[i, 54] += 1  # Turn Inc usually happens here
                g_ctx[i, 8] = 1
                print(f"      [System] Turn {g_ctx[i, 54]} Start. Energy: {g_ctx[i, 5]}")
                continue

            # 1 -> 2 (Energy)
            if ph == 1:
                g_ctx[i, 8] = 2
                continue

            # 2 -> 3 (Draw)
            if ph == 2:
                g_ctx[i, 8] = 3
                continue

            # 3 -> 4 (Draw Action)
            if ph == 3:
                # Rule 10.2: Refresh if needed
                check_deck_refresh(i, deck, trash, g_ctx, 6, 2)

                # Draw Card
                top_card = 0
                deck_idx = -1
                for d_idx in range(60):
                    if deck[i, d_idx] > 0:
                        top_card = deck[i, d_idx]
                        deck_idx = d_idx
                        break

                if top_card > 0:
                    for h_idx in range(60):
                        if hand[i, h_idx] == 0:
                            hand[i, h_idx] = top_card
                            deck[i, deck_idx] = 0
                            # Update Counts
                            hc = 0
                            for k in range(60):
                                if hand[i, k] > 0:
                                    hc += 1
                            g_ctx[i, 3] = hc
                            g_ctx[i, 6] -= 1
                            print(f"      [System] Drew Card: {self.get_card_name(top_card)}")
                            break

                g_ctx[i, 8] = 4  # To Main
                continue

    def run_game(self, max_turns=1000):
        # Redirect stdout to a file
        original_stdout = sys.stdout
        with open("gameplay.log", "w", encoding="utf-8") as log_file:
            sys.stdout = log_file

            try:
                print("\n=== STARTING AGENT GAMEPLAY ANALYSIS ===")
                self.env.reset()

                # Check Phase 0
                if self.env.game_state.batch_global_ctx[0, 8] == 0:
                    print(
                        f"[System] Game Start: Phase 0 (Mulligan). Energy: {self.env.game_state.batch_global_ctx[0, 5]}"
                    )

                # Initial Phase resolution
                self.manual_phase_step()

                total_steps = 0

                while total_steps < 10000:
                    env_state = self.env.game_state

                    # 1. Get State
                    turn = env_state.batch_global_ctx[0, 54]
                    phase = env_state.batch_global_ctx[0, 8]
                    score = env_state.batch_scores[0]

                    if turn > max_turns:
                        print("Max turns reached.")
                        break

                    # Win Condition (Rule 7.1)
                    if score >= 3:
                        print(f"Game End: Score reached {score}!")
                        break

                    # Conservation of Mass Check
                    deck_audit = env_state.batch_global_ctx[0, 6]
                    trash_audit = len([c for c in env_state.batch_trash[0] if c > 0])
                    hand_audit = len([c for c in env_state.batch_hand[0] if c > 0])
                    stage_audit = len([c for c in env_state.batch_stage[0] if c > 0])
                    energy_audit = np.sum(env_state.batch_energy_count[0])
                    live_audit = len([c for c in env_state.batch_live[0] if c > 0])
                    total_audit = deck_audit + trash_audit + hand_audit + stage_audit + energy_audit + live_audit

                    if total_audit != 60:
                        print(
                            f"   [WARNING] INTEGRITY FAIL: Total Cards {total_audit} != 60 (D{deck_audit} H{hand_audit} S{stage_audit} T{trash_audit} E{energy_audit} L{live_audit})"
                        )

                    # Hand
                    hand_ids = [c for c in env_state.batch_hand[0] if c > 0]
                    # Stage
                    stage_ids = env_state.batch_stage[0]
                    stage_str = []
                    for slot, cid in enumerate(stage_ids):
                        if cid > 0:
                            name = self.get_card_name(cid)
                            stats = self.card_db.get(cid, {})
                            power = stats.get("power", 0)
                            hearts = stats.get("hearts", 0)
                            col = stats.get("color", 0)
                            col_map = ["?", "Pn", "Rd", "Yl", "Gr", "Bl", "Pu"]
                            c_str = col_map[col] if 0 <= col <= 6 else "?"
                            stage_str.append(f"S{slot}: {name} (P{power}, {hearts}H {c_str})")
                        else:
                            stage_str.append(f"S{slot}: [Empty]")

                    # Opponent Stage
                    opp_stage_ids = env_state.opp_stage[0]
                    opp_stage_str = []
                    for slot, cid in enumerate(opp_stage_ids):
                        if cid > 0:
                            name = self.get_card_name(cid)
                            power = env_state.card_stats[cid, 1]
                            opp_stage_str.append(f"S{slot}: {name} (P{power})")
                        else:
                            opp_stage_str.append(f"S{slot}: [Empty]")

                    energy = env_state.batch_global_ctx[0, 5]
                    trash = env_state.batch_global_ctx[0, 2]
                    deck_count = env_state.batch_global_ctx[0, 6]

                    opp_trash = env_state.batch_global_ctx[0, 7]
                    opp_deck_count = env_state.opp_global_ctx[0, 6]
                    opp_energy = env_state.opp_global_ctx[0, 5]

                    print(
                        f"\n[Turn {turn}] Phase {phase} | Score: {score} | My Energy: {energy} | My Deck: {deck_count} | My Trash: {trash}"
                    )
                    print(f"   My Stage : {' | '.join(stage_str)}")
                    print(f"   Opp Stage: {' | '.join(opp_stage_str)}")
                    print(
                        f"   My Hand ({len(hand_ids)}): "
                        + ", ".join([str(x) for x in hand_ids[:10]])
                        + ("..." if len(hand_ids) > 10 else "")
                    )
                    print(
                        f"   Opp Hand : {env_state.opp_global_ctx[0, 3]} cards | Opp Deck: {opp_deck_count} | Opp Energy: {opp_energy} | Opp Trash: {opp_trash}"
                    )

                    # 2. Agent Act
                    masks = self.env.game_state.get_action_masks()
                    total_actions = np.sum(masks[0])
                    print(f"   Total Legal Actions: {total_actions}")
                    obs = self.env.game_state.get_observations()

                    # Diagnostic: Check if any Live actions are legal
                    live_action_indices = [idx for idx in range(400, 460) if masks[0, idx]]
                    if live_action_indices:
                        print(
                            f"   Available Live Actions ({len(live_action_indices)}): "
                            + ", ".join(
                                [self.decode_action(lx, env_state.batch_hand[0], []) for lx in live_action_indices[:3]]
                            )
                        )
                    else:
                        print("   [WARNING] No Legal Live Actions!")
                        # Debug why: Check held lives and stats
                        for hid, cid in enumerate(env_state.batch_hand[0]):
                            if cid > 0 and cid < 2000 and env_state.card_stats[cid, 10] == 2:
                                # It is a live card. why masks false?
                                req_p = env_state.card_stats[cid, 12]
                                req_r = env_state.card_stats[cid, 13]
                                print(f"      Held Live (Slot {hid}, ID {cid}): Req Pink {req_p}, Red {req_r}...")

                    action, _ = self.model.predict(obs, action_masks=masks)
                    action_id = action[0]

                    action_desc = self.decode_action(action_id, env_state.batch_hand[0], env_state.batch_stage[0])
                    print(f"   >> ACTION: {action_desc}")

                    # 3. Step Env
                    step_vectorized(
                        action,
                        env_state.batch_stage,
                        env_state.batch_energy_vec,
                        env_state.batch_energy_count,
                        env_state.batch_continuous_vec,
                        env_state.batch_continuous_ptr,
                        env_state.batch_tapped,
                        env_state.batch_live,
                        env_state.batch_opp_tapped,
                        env_state.batch_scores,
                        env_state.batch_flat_ctx,
                        env_state.batch_global_ctx,
                        env_state.batch_hand,
                        env_state.batch_deck,
                        env_state.bytecode_map,
                        env_state.bytecode_index,
                        env_state.card_stats,
                        env_state.batch_trash,
                    )

                    # Opponent
                    step_opponent_vectorized(
                        env_state.opp_hand,
                        env_state.opp_deck,
                        env_state.opp_stage,
                        env_state.opp_energy_vec,
                        env_state.opp_energy_count,
                        env_state.opp_tapped,
                        env_state.opp_scores,
                        env_state.batch_tapped,
                        env_state.opp_global_ctx,
                        env_state.bytecode_map,
                        env_state.bytecode_index,
                        env_state.opp_trash,
                    )

                    # If Pass was chosen:
                    if action_id == 0:
                        print("      [System] Agent Passed. Performance Phase resolved internally.")
                        env_state.batch_global_ctx[0, 8] = 0  # Force End Turn

                    # manual phase step
                    self.manual_phase_step()

                    total_steps += 1

                print("\n=== GAME OVER ===")
                print(f"Final Score: {env_state.batch_scores[0]}")

            finally:
                sys.stdout = original_stdout
                print("Gameplay log saved to gameplay.log")


if __name__ == "__main__":
    # Path from user request
    model = r"C:\Users\trios\.gemini\antigravity\vscode\loveca-copy\historiccheckpoints\20260119_194930_4718592_steps\model.zip"

    analyzer = AgentAnalyzer(model)
    analyzer.run_game()
