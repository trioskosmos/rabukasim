print("STARTING DEBUG SCRIPT")
import numpy as np

from engine.game.game_state import initialize_game
from engine.models.card import MemberCard
from engine.models.enums import Area, Group


def debug_ability_2():
    # {{live_start.png|ライブ開始時}}自分のステージの左サイドエリアにいる『Liella!』のメンバーが{{heart_02.png|heart02}}を3つ以上持つ場合、そのメンバーは、ライブ終了時まで、{{icon_blade.png|ブレード}}{{icon_blade.png|ブレード}}を得る。
    state = initialize_game(use_real_data=True)
    p0 = state.players[0]

    card_no = "PL!SP-bp4-024-L"
    card_id = -1
    for cid, c in state.live_db.items():
        if c.card_no == card_no:
            card_id = cid
            break

    print(f"Found card_id: {card_id}")

    # Setup Left Side Member (Area.LEFT = 0)
    left_id = 8888

    # Liella member, has Heart02 x3 (Red hearts)
    hearts = np.zeros(7, dtype=np.int32)
    hearts[1] = 3  # 3 Red Hearts

    left_member = MemberCard(
        card_id=left_id,
        card_no="test-left",
        name="Kekeru",
        cost=2,
        hearts=hearts,
        blade_hearts=np.zeros(7, dtype=np.int32),
        blades=1,
        groups=[Group.LIELLA],
    )
    state.member_db[left_id] = left_member
    p0.stage[Area.LEFT] = left_id

    p0.live_zone = [card_id]

    # Ability 2
    ability = state.live_db[card_id].abilities[1]
    print(f"Ability trigger: {ability.trigger}")

    # Execute
    print("DEBUG: Triggering Ability 2")
    state.triggered_abilities.append((0, ability, {"card_id": card_id}))
    state._process_rule_checks()  # This processes the ability queue
    print("DEBUG: Finished _process_rule_checks Ability 2")

    # Check Buff
    base_blades = left_member.blades
    breakdown = p0.get_blades_breakdown(Area.LEFT, state.member_db)
    current_blades = p0.get_effective_blades(Area.LEFT, state.member_db)

    import json

    def default_serializer(obj):
        return str(obj)

    print(f"Base blades: {base_blades}")
    print(f"Current blades: {current_blades}")
    print(f"Breakdown: {json.dumps(breakdown, indent=2, default=default_serializer)}")

    print(f"Continuous effects: {json.dumps(p0.continuous_effects, indent=2, default=default_serializer)}")

    if current_blades != base_blades + 2:
        print("FAILURE: Buff not applied correctly.")
    else:
        print("SUCCESS")


if __name__ == "__main__":
    try:
        debug_ability_2()
    except Exception:
        import traceback

        traceback.print_exc()
