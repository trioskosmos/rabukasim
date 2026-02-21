import numpy as np

from engine.game.fast_logic import C_OPPONENT_CHOICE, O_BLADES, O_JUMP_F, resolve_bytecode
from engine.game.game_state import GameState
from engine.models.ability import Ability, Condition, ConditionType, Effect, EffectType
from engine.models.card import MemberCard

# Mock Card Data
# MemberCard(card_id: int, card_no: str, name: str, cost: int, hearts: numpy.ndarray, blade_hearts: numpy.ndarray, blades: int, groups: List[engine.models.enums.Group] = <factory>, units: List[engine.models.enums.Unit] = <factory>, abilities: List[engine.models.ability.Ability] = <factory>, img_path: str = '', rare: str = 'N', ability_text: str = '', volume_icons: int = 0, draw_icons: int = 0)
CARD_647 = MemberCard(
    card_id=647,
    card_no="647",
    name="Onizuka Tomari",
    cost=3,
    hearts=np.zeros(7, dtype=np.int32),
    blade_hearts=np.zeros(7, dtype=np.int32),
    blades=3000,
    groups=[],
    units=[],
    rare="R",
    abilities=[
        Ability(
            effects=[Effect(EffectType.ADD_BLADES, 1000, None, {})],
            conditions=[Condition(ConditionType.OPPONENT_CHOICE, {}, [])],
            raw_text="Test",
            trigger=0,
        )
    ],
    ability_text="If opponent chose...",
)


def test_python_logic():
    gs = GameState()
    p1 = gs.players[0]
    p1.members_tapped_by_opponent_this_turn.add(123)  # Simulate tap

    # Check condition manually
    cond = Condition(ConditionType.OPPONENT_CHOICE, {}, [])
    # Pass context with card_id 123
    met = gs._check_condition(p1, cond, {"card_id": 123})
    assert met == True, "Should be true if ID in set"

    met_fail = gs._check_condition(p1, cond, {"card_id": 999})
    assert met_fail == False, "Should be false if ID not in set"
    print("Python Logic OK")


def test_numba_logic():
    # Bytecode: [C_OPPONENT_CHOICE, 0, 0], [O_JUMP_F, 3, 0], [O_BLADES, 1000, 0, 0]
    bytecode = np.array(
        [
            [C_OPPONENT_CHOICE, 0, 0, 0],
            [O_JUMP_F, 2, 0, 0],  # Skip next if false
            [O_BLADES, 1000, 0, 0],  # Exec if true
            [0, 0, 0, 0],  # Sentinel
        ],
        dtype=np.int32,
    )

    # Contexts
    flat_ctx = np.zeros(32, dtype=np.int32)
    global_ctx = np.zeros(32, dtype=np.int32)

    # Opponent Tapped Array (3 slots)
    opp_tapped_true = np.array([0, 1, 0], dtype=np.int32)  # Slot 1 tapped
    opp_tapped_false = np.array([0, 0, 0], dtype=np.int32)

    # Other args (dummies)
    p_hand = np.zeros(60, dtype=np.int32)
    p_deck = np.zeros(60, dtype=np.int32)
    p_stage = np.zeros(3, dtype=np.int32)
    p_ev = np.zeros((3, 32), dtype=np.int32)
    p_ec = np.zeros(3, dtype=np.int32)
    p_cv = np.zeros((32, 10), dtype=np.int32)
    cptr = np.zeros(1, dtype=np.int32)
    p_tap = np.zeros(3, dtype=np.int32)
    p_live = np.zeros(9, dtype=np.int32)
    p_trash = np.zeros((1, 60), dtype=np.int32)  # Needs 2D for batch but resolve_bytecode takes 1D usually?
    # Wait, resolve_bytecode signature takes p_trash. In code it takes 1D for single.
    # In batch_resolve it slices.
    # Let's check signature call in resolve_bytecode implementation.
    # It passes p_tr[i] which is 1D.
    p_trash = np.zeros(60, dtype=np.int32)

    b_map = np.zeros((1, 1, 4), dtype=np.int32)
    b_idx = np.zeros((1, 4), dtype=np.int32)
    out_bonus = np.zeros(1, dtype=np.int32)

    # Test TRUE case
    resolve_bytecode(
        bytecode,
        flat_ctx,
        global_ctx,
        1,
        p_hand,
        p_deck,
        p_stage,
        p_ev,
        p_ec,
        p_cv,
        cptr,
        p_tap,
        p_live,
        opp_tapped_true,  # PASSED AS TRUE
        p_trash,
        b_map,
        b_idx,
        out_bonus,
    )

    # Check result: O_BLADES should add to p_cv
    assert p_cv[0, 0] == 1, "Should have executed O_BLADES (Op 1)"
    assert p_cv[0, 1] == 1000, "Should have value 1000"

    print("Numba Logic TRUE case OK")

    # Test FALSE case
    p_cv.fill(0)
    cptr[0] = 0

    resolve_bytecode(
        bytecode,
        flat_ctx,
        global_ctx,
        1,
        p_hand,
        p_deck,
        p_stage,
        p_ev,
        p_ec,
        p_cv,
        cptr,
        p_tap,
        p_live,
        opp_tapped_false,  # PASSED AS FALSE
        p_trash,
        b_map,
        b_idx,
        out_bonus,
    )

    assert p_cv[0, 0] == 0, "Should NOT have executed O_BLADES"
    print("Numba Logic FALSE case OK")


if __name__ == "__main__":
    test_python_logic()
    test_numba_logic()
