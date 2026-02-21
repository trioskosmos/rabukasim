import random
from typing import TYPE_CHECKING

import numpy as np

from engine.game.enums import Phase
from engine.models.ability import EffectType, TriggerType

if TYPE_CHECKING:
    pass


class PhaseMixin:
    """
    Mixin for GameState that handles turn and phase transitions.

    Phase State Machine (Rule 7):
        MULLIGAN_P1 -> MULLIGAN_P2 -> ACTIVE -> ENERGY -> DRAW -> MAIN
        -> LIVE_SET (both players) -> PERFORMANCE_P1 -> PERFORMANCE_P2
        -> LIVE_RESULT -> ACTIVE (next turn)

    Each phase handler (e.g. _do_active_phase) advances self.phase to the next
    phase before returning. Do not manually set self.phase after calling a handler.
    """

    def _do_active_phase(self) -> None:
        p = self.active_player
        if hasattr(self, "log_rule"):
            self.log_rule("Rule 7.4.1", f"Active Phase: Untapping all members and energy for Player {p.player_id}.")
        if isinstance(p.members_played_this_turn, list):
            p.members_played_this_turn.clear()
        else:
            p.members_played_this_turn.fill(False)
        p.untap_all()
        self.phase = Phase.ENERGY

    def _do_energy_phase(self) -> None:
        p = self.active_player
        if hasattr(self, "log_rule"):
            self.log_rule(
                "Rule 7.5.2", f"Energy Phase: Player {p.player_id} moves 1 card from Energy Deck to Energy Zone."
            )
        if p.energy_deck:
            p.energy_zone.append(p.energy_deck.pop(0))
        self.phase = Phase.DRAW

    def _do_draw_phase(self) -> None:
        p = self.active_player
        if hasattr(self, "log_rule"):
            self.log_rule("Rule 7.6.2", f"Draw Phase: Player {p.player_id} draws 1 card.")
        self._draw_cards(p, 1)
        self.phase = Phase.MAIN

    def _advance_performance(self) -> None:
        if self.first_player == 0:
            if self.phase == Phase.PERFORMANCE_P1:
                self.phase = Phase.PERFORMANCE_P2
                self.current_player = 1
            else:
                self.phase = Phase.LIVE_RESULT
        else:
            if self.phase == Phase.PERFORMANCE_P2:
                self.phase = Phase.PERFORMANCE_P1
                self.current_player = 0
            else:
                self.phase = Phase.LIVE_RESULT

    def _end_main_phase(self) -> None:
        """End player's main phase. If first player, switch to second player's turn.
        If second player, advance to LIVE_SET phase."""
        if hasattr(self, "log_rule"):
            self.log_rule("Rule 7.7.3", f"Main Phase End: Player {self.current_player} ends Main Phase.")
        if self.current_player == self.first_player:
            # Switch to Player 2's turn: untap their cards and run their phases
            p2 = 1 - self.first_player
            self.players[p2].tapped_energy[:] = False
            self.players[p2].tapped_members[:] = False
            self.players[p2].members_played_this_turn[:] = False
            self.current_player = p2
            # Clear any stale looked_cards from ability resolution (safety)
            self.looked_cards = []
            # Chain through ACTIVE -> ENERGY -> DRAW -> MAIN
            # Each handler sets self.phase to the next phase before returning
            self.phase = Phase.ACTIVE
            self._do_active_phase()  # Sets phase to ENERGY
            self._do_energy_phase()  # Sets phase to DRAW
            self._do_draw_phase()  # Sets phase to MAIN
        else:
            # Both players have had their main phase, move to LIVE_SET
            self.phase = Phase.LIVE_SET
            self.current_player = self.first_player
            # Clear any stale looked_cards from ability resolution
            self.looked_cards = []

    def _end_live_set(self) -> None:
        """End player's live set phase. First player sets first, then second player.
        After both, advance to performance phase (first player performs first)."""
        p = self.active_player
        # Draw cards equal to the number of cards set this turn (Rule 8.2.2 modified timing)
        if p.live_cards_set_this_turn > 0:
            if hasattr(self, "log_rule"):
                self.log_rule(
                    "Rule 8.2.2", f"Live Set End: Player {p.player_id} draws {p.live_cards_set_this_turn} cards."
                )
            self._draw_cards(p, p.live_cards_set_this_turn)
            p.live_cards_set_this_turn = 0

        if self.current_player == self.first_player:
            # Switch to second player for their live set
            self.current_player = 1 - self.first_player
        else:
            # Both players have set lives, begin performance
            # Performance order matches first_player: P1 performs first if first_player=0
            self.performance_results = {}
            if self.first_player == 0:
                self.phase = Phase.PERFORMANCE_P1
                self.current_player = 0
            else:
                self.phase = Phase.PERFORMANCE_P2
                self.current_player = 1

    def _do_performance(self, player_idx: int, live_idx: int = -1) -> None:
        """Execute performance phase for a player.
        If live_idx >= 0, only that specific live card is performed.
        Otherwise (default -1), all cards in the live zone are performed (all-or-nothing).
        """
        p = self.players[player_idx]

        # Phase 1: Ability Trigger (Run once)
        if not p.performance_abilities_processed:
            p.performance_abilities_processed = True

            p.live_zone_revealed = [True] * len(p.live_zone)

            # Rule 8.3.4: "puts all cards that are not Live Cards into their Waiting Room"
            # Filter live_zone: Keep only if in live_db
            new_live_zone = []
            for cid in p.live_zone:
                if cid in self.live_db:
                    new_live_zone.append(cid)
                else:
                    if hasattr(self, "log_rule"):
                        self.log_rule("Rule 8.3.4", f"Discarding non-live card {cid} from Live Zone.")
                    p.discard.append(cid)
            p.live_zone = new_live_zone

            triggers_found = False
            for card_id in p.live_zone:
                for ab in self.live_db[card_id].abilities:
                    if ab.trigger == TriggerType.ON_LIVE_START:
                        if hasattr(self, "log_rule"):
                            self.log_rule(
                                "Rule 11.4",
                                f"Triggering [ライブ開始時] (Live Start) abilities for {self.live_db[card_id].name}.",
                            )
                        self.triggered_abilities.append((player_idx, ab, {"card_id": card_id}))
                        triggers_found = True

            for i, card_id in enumerate(p.stage):
                if card_id >= 0 and not p.tapped_members[i] and card_id in self.member_db:
                    for ab in self.member_db[card_id].abilities:
                        if ab.trigger == TriggerType.ON_LIVE_START:
                            self.triggered_abilities.append((player_idx, ab, {"area": i}))
                            triggers_found = True

            # If abilities triggered, return to main loop to process them
            if triggers_found:
                return

        # Phase 2: Wait for resolution
        if self.triggered_abilities or self.pending_choices or self.pending_effects:
            return

        # Phase 3: Calculation checks
        if p.cannot_live:
            for card_id in p.live_zone:
                p.discard.append(card_id)
            p.live_zone = []
            p.performance_abilities_processed = False
            self._advance_performance()
            return

        if not p.live_zone:
            # Create empty performance result for consistency
            self.performance_results[player_idx] = {
                "success": False,
                "member_contributions": [],
                "yell_cards": [],
                "total_hearts": [0] * 7,
                "lives": [],
            }
            p.performance_abilities_processed = False
            self._advance_performance()
            return

        total_blades = p.get_total_blades(self.member_db)

        # Apply cheer_mod (RE_CHEER or cheer_mod rule)
        extra_reveals = sum(
            ce["effect"].value
            for ce in p.continuous_effects
            if ce["effect"].effect_type == EffectType.META_RULE and ce["effect"].params.get("type") == "cheer_mod"
        )
        total_blades = max(0, total_blades + extra_reveals)

        print(f"DEBUG: Total Blades (cheer reveal count): {total_blades}")

        # Collect blade breakdown for result
        blade_breakdown = []
        for i in range(3):
            if p.stage[i] >= 0:
                blade_breakdown.extend(p.get_blades_breakdown(i, self.member_db))
        blade_breakdown.extend(p.get_global_blades_breakdown())

        if hasattr(self, "log_rule"):
            self.log_rule("Rule 8.3.11", f"Player {player_idx} performs Yell ({total_blades} blades).")
        self.yell_cards = []
        for _ in range(total_blades):
            if not p.main_deck and p.discard:
                random.shuffle(p.discard)
                p.main_deck, p.discard = p.discard, []
            if p.main_deck:
                self.yell_cards.append(p.main_deck.pop(0))
        draw_bonus, yell_score_bonus = 0, 0
        total_hearts = np.zeros(7, dtype=np.int32)
        member_contributions = []
        heart_breakdown = []
        for i in range(3):
            cid = p.stage[i]
            if cid >= 0:
                hraw = p.get_effective_hearts(i, self.member_db)
                total_hearts[: len(hraw)] += hraw
                heart_breakdown.extend(p.get_hearts_breakdown(i, self.member_db))
                card = self.member_db[cid]

                # Rule 8.4.1: Include Stage Member volume icons
                vol = getattr(card, "volume_icons", 0)
                yell_score_bonus += vol

                member_contributions.append(
                    {
                        "source_id": cid,
                        "source": card.name,
                        "img": card.img_path,
                        "hearts": hraw.tolist(),
                        "blades": int(p.get_effective_blades(i, self.member_db)),
                        "volume_icons": vol,
                        "draw_icons": getattr(card, "draw_icons", 0),
                    }
                )

        yell_card_details = []
        for card_id in self.yell_cards:
            card = self.member_db.get(card_id) or self.live_db.get(card_id)
            if card:
                draw_bonus += getattr(card, "draw_icons", 0)
                vol = getattr(card, "volume_icons", 0)
                yell_score_bonus += vol

                details = {
                    "id": card_id,
                    "name": card.name,
                    "img": card.img_path,
                    "blade_hearts": [0] * 7,
                    "volume_icons": vol,
                    "draw_icons": getattr(card, "draw_icons", 0),
                }
                # Rule 8.4.1: Include Blade Hearts (including ALL Blade) from revealed cards
                bh = getattr(card, "blade_hearts", None)
                if bh is not None:
                    bh_padded = np.zeros(7, dtype=np.int32)
                    bh_padded[: len(bh)] = bh[:7]
                    total_hearts[: len(bh_padded)] += bh_padded
                    details["blade_hearts"] = bh_padded.tolist()
                yell_card_details.append(details)

        # Apply global TRANSFORM_COLOR to the final heart pool
        transform_logs = []
        for ce in p.continuous_effects:
            eff = ce["effect"]
            if eff.effect_type == EffectType.TRANSFORM_COLOR:
                # Value v is the amount or filter? Usually it's "all of type X become Y"
                # Params: from_color (int 1-6), to_color (int 1-6)
                src = eff.params.get("from_color", eff.params.get("color"))
                dest = eff.params.get("to_color")
                if src and dest:
                    try:
                        s_idx, d_idx = int(src) - 1, int(dest) - 1
                        if 0 <= s_idx < 6 and 0 <= d_idx < 6:
                            transfer = total_hearts[s_idx]
                            total_hearts[d_idx] += transfer
                            total_hearts[s_idx] = 0
                            heart_breakdown.append(
                                {
                                    "source": ce.get("source_name", "Effect"),
                                    "type": "transform",
                                    "text": f"Transform {src} Yells to {dest}",
                                }
                            )
                            transform_logs.append(
                                {
                                    "source": ce.get("source_name", "Effect"),
                                    "desc": f"Transform {src} Yells to {dest}",
                                    "type": "transform",
                                    "source_id": ce.get("source_id", -1),
                                }
                            )
                    except:
                        pass

        self._draw_cards(p, draw_bonus)

        # Save pre-consumption hearts for display
        display_hearts = total_hearts.copy()

        # --- ALL-OR-NOTHING CHECK ---
        total_req = np.zeros(7, dtype=np.int32)
        live_reqs = []  # Store individual reqs for UI and logic
        requirement_logs = []

        # Determine target lives
        target_lives = []
        if 0 <= live_idx < len(p.live_zone):
            target_lives = [p.live_zone[live_idx]]
        else:
            target_lives = p.live_zone

        for card_id in target_lives:
            live = self.live_db[card_id]
            req = live.required_hearts.copy()
            for ce in p.continuous_effects:
                if ce["effect"].effect_type == EffectType.REDUCE_HEART_REQ:
                    val = ce["effect"].value
                    color = ce["effect"].params.get("color")
                    if color == "any" or not color:
                        req[6] = max(0, req[6] - val)
                    else:
                        try:
                            # color param might be 1-6
                            c_idx = int(color) - 1
                            if 0 <= c_idx < 6:
                                req[c_idx] = max(0, req[c_idx] - val)
                        except:
                            pass

                    # Log requirement reduction
                    red_vec = np.zeros(7, dtype=np.int32)
                    if color == "any" or not color:
                        red_vec[6] = val
                    else:
                        try:
                            c_idx = int(color) - 1
                            if 0 <= c_idx < 6:
                                red_vec[c_idx] = val
                        except:
                            pass

                    if np.any(red_vec > 0):
                        requirement_logs.append(
                            {
                                "source": ce.get("source_name", "Effect"),
                                "value": (-red_vec).tolist(),
                                "type": "req_mod",
                                "source_id": ce.get("source_id", -1),
                            }
                        )

            # Pad to 7 just in case
            req_padded = np.zeros(7, dtype=np.int32)
            req_padded[: len(req)] = req[:7]

            total_req += req_padded
            live_reqs.append((card_id, req_padded))

        temp_hearts = total_hearts.copy()
        live_details = []
        passed_lives_acc = []
        any_failed = False

        for card_id, req in live_reqs:
            l_passed = self._check_hearts_meet_requirement(temp_hearts, req)
            status_text = "PASSED" if l_passed else "FAILED"
            if hasattr(self, "log_rule"):
                card_name = self.live_db[card_id].name if card_id in self.live_db else f"Card {card_id}"
                self.log_rule("Rule 8.3.15", f"P{player_idx} Live Card '{card_name}': {status_text}")

            if not any_failed and l_passed:
                # SUCCESS for this card
                before = temp_hearts.copy()
                self._consume_hearts(temp_hearts, req)
                filled = before - temp_hearts

                live_details.append(
                    {
                        "id": card_id,
                        "name": self.live_db[card_id].name,
                        "img": self.live_db[card_id].img_path,
                        "required": req.tolist(),
                        "filled": filled.tolist(),
                        "passed": True,
                        "score": self.live_db[card_id].score,
                    }
                )
                passed_lives_acc.append(card_id)
            else:
                # FAILED for this card or previous card failed
                any_failed = True
                live_details.append(
                    {
                        "id": card_id,
                        "name": self.live_db[card_id].name,
                        "img": self.live_db[card_id].img_path,
                        "required": req.tolist(),
                        "filled": [0] * 7,
                        "passed": False,
                        "score": self.live_db[card_id].score,
                    }
                )

        all_passed = not any_failed and len(passed_lives_acc) == len(live_reqs)

        # Log results
        if hasattr(self, "log_rule"):
            res_str = "PASSED" if all_passed else "FAILED"
            self.log_rule(
                "Rule 8.3.15",
                f"Performance P{player_idx} {res_str} - Lives Passed: {len(passed_lives_acc)}/{len(live_reqs)}",
            )

        # Rule 8.3.16: If ANY failed, ALL go to discard.
        if all_passed:
            p.passed_lives = passed_lives_acc
            p.live_zone = []  # All moved to passed_lives
        else:
            p.passed_lives = []
            if hasattr(self, "log_rule"):
                self.log_rule(
                    "Rule 8.3.16", f"P{player_idx} Performance Failure: Discarding {len(p.live_zone)} live cards."
                )
            p.discard.extend(p.live_zone)
            p.live_zone = []

        p.live_score_bonus += yell_score_bonus
        p.yell_score_count = yell_score_bonus

        self.performance_results[player_idx] = {
            "success": all_passed,
            "lives_passed_count": len(passed_lives_acc) if all_passed else 0,
            "member_contributions": member_contributions,
            "yell_cards": yell_card_details,
            "total_hearts": display_hearts.tolist(),
            "lives": live_details,
            "breakdown": {
                "blades": blade_breakdown,
                "hearts": heart_breakdown,
                "requirements": requirement_logs,
                "transforms": transform_logs,
                "score_modifiers": [],  # Will be populated in _do_live_result
            },
            "yell_score_bonus": yell_score_bonus,
        }

        # Store in history
        if not hasattr(self, "performance_history"):
            self.performance_history = []
        hist_entry = self.performance_results[player_idx].copy()
        hist_entry["player_id"] = player_idx
        hist_entry["turn"] = self.turn_number
        self.performance_history.append(hist_entry)

        p.performance_abilities_processed = False
        self._advance_performance()

    def _clear_expired_effects(self, expiry_type: str) -> None:
        for p in self.players:
            p.continuous_effects = [e for e in p.continuous_effects if e.get("expiry") != expiry_type]
            if expiry_type == "LIVE_END":
                p.cannot_live = False
                p.live_score_bonus = 0
                p.live_success_triggered = False

    def _do_live_result(self) -> None:
        """
        Rule 8.4: Determine live winner and handle success.
        """
        if hasattr(self, "performance_results"):
            self.last_performance_results = self.performance_results.copy()

        p0, p1 = self.players[0], self.players[1]

        # Rule 8.4.4: Success event triggers before winner determination
        # Trigger ON_LIVE_SUCCESS for both Stage Members and performed Live Cards
        for pid, p in enumerate(self.players):
            if p.passed_lives and not p.live_success_triggered:
                p.live_success_triggered = True
                if hasattr(self, "log_rule"):
                    self.log_rule("Rule 11.5", f"P{pid} Live Success Event: Triggering [ライブ成功時] abilities.")
                # Stage Members
                for i, cid in enumerate(p.stage):
                    if cid >= 0 and cid in self.member_db:
                        for ab in self.member_db[cid].abilities:
                            if ab.trigger == TriggerType.ON_LIVE_SUCCESS:
                                self.triggered_abilities.append((pid, ab, {"area": i}))
                # Live Cards (Rule 11.5 explicitly mentions both can have success abilities)
                for cid in p.passed_lives:
                    if cid in self.live_db:
                        for ab in self.live_db[cid].abilities:
                            if ab.trigger == TriggerType.ON_LIVE_SUCCESS:
                                self.triggered_abilities.append((pid, ab, {"card_id": cid}))

        # If abilities triggered, return to process them (allowing score mods to apply)
        if self.triggered_abilities:
            return

        # Calculate base score from passed_lives (Rule 8.4.1)
        p0_base = sum(self.live_db[c].score for c in p0.passed_lives if c in self.live_db)
        p1_base = sum(self.live_db[c].score for c in p1.passed_lives if c in self.live_db)

        # Apply score modifiers (Rule 11)
        for pid, p in enumerate([p0, p1]):
            player_score_mods = []
            for ce in p.continuous_effects:
                if ce["effect"].effect_type == EffectType.MODIFY_SCORE_RULE:
                    val = ce["effect"].value
                    if ce["effect"].params and ce["effect"].params.get("multiplier_source") == "yell_score_icon":
                        val *= p.yell_score_count
                    p.live_score_bonus += val

                    # Capture for breakdown
                    if pid in self.performance_results:
                        self.performance_results[pid]["breakdown"]["score_modifiers"].append(
                            {
                                "source": ce.get("source_name", "Effect"),
                                "value": val,
                                "desc": f"Score modifier from {ce.get('source_name', 'Effect')}",
                                "source_id": ce.get("source_id", -1),
                            }
                        )

        p0_total, p1_total = p0_base + p0.live_score_bonus, p1_base + p1.live_score_bonus
        if hasattr(self, "log_rule"):
            self.log_rule("Rule 8.4.6", f"Live Judgment: P0={p0_total}, P1={p1_total}")

        # Determine Winners (Rule 8.4.6)
        winners = []
        if p0_total > 0 or p1_total > 0:
            if p0_total > p1_total:
                winners = [0]
            elif p1_total > p0_total:
                winners = [1]
            else:
                winners = [0, 1]

        choices = []
        is_tie = len(winners) == 2

        for w in winners:
            p = self.players[w]
            if p.passed_lives:
                # Rule 8.4.7.1: Penalty for ties with multiple cards
                if is_tie and len(p.passed_lives) >= 2:
                    if hasattr(self, "log_rule"):
                        self.log_rule(
                            "Rule 8.4.7.1", f"Player {w} Tie Penalty: {len(p.passed_lives)} cards; 0 points awarded."
                        )
                    continue

                # Rule 8.4.7.2 / 8.4.7.3: Move exactly one card to success lives
                if len(p.passed_lives) == 1:
                    cid = p.passed_lives[0]
                    if hasattr(self, "log_rule"):
                        self.log_rule(
                            "Rule 11.5",
                            f"Triggering [ライブ成功時] (Live Success) abilities for {self.live_db[cid].name}.",
                        )
                    p.success_lives.append(cid)
                    p.passed_lives.pop(0)
                    if hasattr(self, "log_rule"):
                        self.log_rule("Rule 8.4.7.2", f"Player {w} obtained 1 Success Live: {self.live_db[cid].name}")
                else:
                    # Multi-card success (when not a tie): must choose one (Rule 8.4.7.3)
                    choices.append(
                        (
                            "SELECT_SUCCESS_LIVE",
                            {
                                "cards": p.passed_lives.copy(),
                                "player_id": w,
                                "source_card_id": p.passed_lives[0],
                                # Simplified choice text
                                "effect_description": "獲得するライブカードを1枚選んでください",
                                "source_member": "ライブ判定",
                            },
                        )
                    )

        for c in reversed(choices):
            if c not in self.pending_choices:
                self.pending_choices.insert(0, c)

        if self.pending_choices:
            choice_player = self.pending_choices[0][1].get("player_id")
            self.current_player = choice_player
            return

        # Cleanup (Rule 8.4.8)
        for w, p in enumerate(self.players):
            if p.passed_lives:
                if hasattr(self, "log_rule"):
                    self.log_rule(
                        "Rule 8.4.8",
                        f"P{w} Live Result Cleanup: Discarding {len(p.passed_lives)} surplus passed cards.",
                    )
                p.discard.extend(p.passed_lives)
                p.passed_lives = []
            p.live_score_bonus = 0

        # Determine who goes first next turn (Rule 8.4.10)
        # Winner goes first. If both won (tie), host/active or specified logic.
        if len(winners) == 1:
            self.first_player = winners[0]

        # Reset turn effects
        for p in self.players:
            p.continuous_effects = [e for e in p.continuous_effects if e.get("expiry") != "TURN_END"]
            p.cannot_live = False
            p.used_abilities.clear()
            p.moved_members_this_turn.clear()

        # Advance turn
        self._finish_live_result()

    def _finish_live_result(self) -> None:
        """Advance to the next turn after live results are finalized."""
        # Q171: "Until end of live" effects expire at the end of the Live Result phase.
        self._clear_expired_effects("LIVE_END")

        self.turn_number += 1
        self.action_count_this_turn = 0
        self.first_player = (self.first_player + 1) % len(self.players)
        self.current_player = self.first_player
        self.phase = Phase.ACTIVE

        if hasattr(self, "performance_results"):
            self.performance_results.clear()

        for p in self.players:
            # Rule 8.4.11: Move any unperformed live cards to discard
            p.discard.extend(p.live_zone)
            p.live_zone = []
            p.live_zone_revealed = []
            p.performance_abilities_processed = False

        self.check_win_condition()
        self._do_active_phase()
