from __future__ import annotations

import random
from typing import Any

import numpy as np

from engine.game.enums import Phase
from engine.models.ability import EffectType, TriggerType


def apply_system_rules(game: Any) -> bool:
    changed = False

    for player in game.players:
        player.meta_rules.clear()

        for cid in player.stage:
            if cid >= 0 and cid in game._meta_rule_cards:
                for ability in game.member_db[cid].abilities:
                    if ability.trigger == TriggerType.CONSTANT:
                        for effect in ability.effects:
                            if effect.effect_type == EffectType.META_RULE:
                                player.meta_rules.add(str(effect.params.get("type", "")))

        for zone in [player.live_zone, player.success_lives]:
            for cid in zone:
                if cid in game._meta_rule_cards:
                    for ability in game.live_db[cid].abilities:
                        if ability.trigger == TriggerType.CONSTANT:
                            for effect in ability.effects:
                                if effect.effect_type == EffectType.META_RULE:
                                    player.meta_rules.add(str(effect.params.get("type", "")))

        if not player.main_deck and player.discard:
            player.main_deck = player.discard[:]
            player.discard = []
            if game.fast_mode:
                np.random.shuffle(player.main_deck)
            else:
                random.shuffle(player.main_deck)
            changed = True

        for slot_idx in range(3):
            if player.stage[slot_idx] < 0 and player.stage_energy_count[slot_idx] > 0:
                if hasattr(game, "log_rule"):
                    game.log_rule(
                        "Rule 10.5.3",
                        f"Reclaiming energy from empty slot {slot_idx} for player {player.player_id}.",
                    )
                energy_count = player.stage_energy_count[slot_idx]
                if energy_count > 0:
                    player.energy_deck.extend(player.stage_energy_vec[slot_idx, :energy_count])
                    player.stage_energy_vec[slot_idx, :] = 0
                    player.stage_energy_count[slot_idx] = 0
                    changed = True

    if game.yell_cards and int(game.phase) not in (Phase.PERFORMANCE_P1, Phase.PERFORMANCE_P2):
        for cid in game.yell_cards:
            game.players[game.current_player].discard.append(cid)
        game.yell_cards = []
        changed = True

    old_game_over = game.game_over
    game.check_win_condition()
    if game.game_over and not old_game_over:
        changed = True

    return changed


__all__ = ["apply_system_rules"]